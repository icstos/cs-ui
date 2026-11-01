"""把已安装的 ``ui`` 包内省成一份可 JSON 序列化的 API 索引。

**为什么用运行时内省，而不是像 flet-mcp 那样做 griffe 静态扫描？**

cs-ui 的控件是 ``@ft.control`` 装饰出来的 dataclass，构造器由基类
**拍平生成**；表单类组件是 ``@ft.observable`` 数据对象 + ``ui()`` 方法。
真正决定"能传什么参数"的是 ``dataclasses.fields()`` 与
``inspect.signature()`` 在**当前安装版本**上的结果 —— 静态扫描只能看到
源码里写着的那几个注解，看不到 flet 拍平后的构造器和继承链。

这个索引只在 ``ui-mcp build`` 时生成一次，产物是
``ui_mcp/data/api.json``；**服务期不 import ui**。
"""

from __future__ import annotations

import dataclasses
import enum
import importlib
import inspect
import pkgutil
import re
import sys
import textwrap
import types
import typing
from datetime import datetime
from typing import Any

# 事件字段：flet 1.x 用 EventHandler[Event] / ControlEventHandler[Control] 标注
_EVENT_TYPE_RE = re.compile(r"(Control)?EventHandler\s*\[")
_INLINE_COMMENT_RE = re.compile(r"^\s{4,}([A-Za-z_]\w*)\s*:\s*.+?#\s*(.+)$")
_CLASS_REPR_RE = re.compile(r"<class '([\w.]+)'>")
_FORWARD_REF_RE = re.compile(r"ForwardRef\('([^']+)'\)")
_RST_ROLE_RE = re.compile(r":\w+(?::\w+)?:`~?([^`]+)`")
# 类型串里的模块限定名：`a.b.C` → `C`（只吃"点分隔 + 首字母大写"的类名）
_MODULE_PREFIX_RE = re.compile(r"\b(?:[A-Za-z_]\w*\.)+([A-Za-z_]\w*)")
# dataclass/Enum 自动生成的 docstring，没有信息量
_BOILERPLATE_DOCS = (
    "Create a collection of name/value pairs.",
    "An enumeration.",
)

# 库里各模块自带的示例入口（`def App()` / `main()` / 模板页），不是公共 API
_DEMO_ENTRY_NAMES = {
    "App",
    "main",
    "set_app",
    "Home",
    "About",
    "Contact",
    "Template",
    "NotFoundView",
}

# 生成构造器签名时忽略的 flet 基础设施字段（它们永远有默认值，列出来只是噪音）
_PLUMBING = {
    "data",
    "key",
    "ref",
    "visible",
    "disabled",
    "expand",
    "opacity",
    "tooltip",
    "rtl",
    "adaptive",
}

SUMMARY_CHARS = 150


# ---------------------------------------------------------------------------
# 文本 / 类型格式化
# ---------------------------------------------------------------------------


def first_sentence(text: str | None, limit: int = SUMMARY_CHARS) -> str:
    """docstring 的第一段第一句（中文句号也认），超长截断。"""
    if not text:
        return ""
    text = _RST_ROLE_RE.sub(r"`\1`", text.strip())
    head = text.split("\n\n", 1)[0].strip()
    # 一句结束：中文句号 / 英文句点+空格
    for sep in ("。", ". "):
        idx = head.find(sep)
        if 0 < idx < limit:
            head = head[: idx + 1]
            break
    head = " ".join(head.split())
    return head if len(head) <= limit else head[: limit - 1].rstrip() + "…"


def full_doc(text: str | None) -> str:
    """去掉 RST 角色标记，保留全文。"""
    if not text:
        return ""
    return _RST_ROLE_RE.sub(r"`\1`", text).strip()


def type_str(annotation: Any, limit: int = 96) -> str:
    """把注解规约成可读短串。

    ``<class 'pathlib.Path'>`` → ``Path``；``Optional[X]`` → ``X | None``；
    ``typing.`` / ``ForwardRef()`` 一律去掉。超过 ``limit`` 截断。
    """
    if annotation is inspect.Parameter.empty or annotation is inspect.Signature.empty:
        return ""
    if annotation is None or annotation is type(None):
        return "None"

    if isinstance(annotation, str):
        text = annotation
    elif isinstance(annotation, type):
        text = annotation.__name__
    else:
        text = str(annotation)

    text = _CLASS_REPR_RE.sub(lambda m: m.group(1).rsplit(".", 1)[-1], text)
    text = _FORWARD_REF_RE.sub(r"\1", text)
    text = re.sub(r"\btyping\.", "", text)
    text = re.sub(r"\btypes\.NoneType\b", "None", text)
    text = text.replace("NoneType", "None")
    # 去掉类型里的模块前缀：flet.controls.colors.Colors → Colors。
    # 不这样做，flet 事件类型会长成
    # `Callable[[flet.controls.control_event.Event[Button]] | Any] | None`，
    # 一行 90+ 字符还没说到点子上。
    text = _MODULE_PREFIX_RE.sub(r"\1", text)
    optional = re.fullmatch(r"Optional\[(.+)\]", text)
    if optional:
        text = f"{optional.group(1)} | None"
    union = re.fullmatch(r"Union\[(.+)\]", text)
    if union:
        text = union.group(1).replace(", ", " | ")
    text = _squash_long_unions(text)
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _squash_long_unions(text: str, keep: int = 4) -> str:
    """``A | B | C | D | E | None`` 这种超长联合类型只留前几个，标 ``…``。"""
    if " | " not in text:
        return text
    parts = [p.strip() for p in text.split(" | ")]
    if len(parts) <= keep + 1:
        return text
    return " | ".join(parts[:keep] + ["…"])


def default_str(value: Any, limit: int = 48) -> str | None:
    """字段默认值 → 短串；``field(...)`` 之类声明式默认值解出真实值。"""
    if value is dataclasses.MISSING:
        return None
    if isinstance(value, enum.Enum):
        return f"{type(value).__name__}.{value.name}"
    if isinstance(value, (list, tuple)) and len(value) > 2:
        return f"{type(value).__name__}({len(value)} 项)"
    text = " ".join(repr(value).split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _enum_value(value: Any, limit: int = 5) -> str:
    """枚举值 → 可读串。StyleType 这类成员值是一串颜色元组，别只报"4 项"。"""
    if isinstance(value, (tuple, list)):
        items = [default_str(v, 24) or "?" for v in value[:limit]]
        text = "(" + ", ".join(items)
        if len(value) > limit:
            text += ", …"
        return text + ")"
    return default_str(value, 60) or str(value)


def _short_module(module: str) -> str:
    return module.rsplit(".", 1)[-1] if module else ""


# ---------------------------------------------------------------------------
# 类内省
# ---------------------------------------------------------------------------


def _ui_module_names() -> list[str]:
    import ui

    names = [ui.__name__]
    for info in pkgutil.walk_packages(ui.__path__, ui.__name__ + "."):
        names.append(info.name)
    return names


def _import(path: str) -> types.ModuleType | None:
    try:
        return importlib.import_module(path)
    except Exception:  # 单个模块的导入失败不该毁掉整份索引
        return None


def _own_annotation_names(cls: type) -> set[str]:
    """本类**自己声明**的字段名。

    只看 ``cls.__dict__['__annotations__']``。这是唯一可靠的判据：
    ``@ft.observable`` 会把原类塞进 mro 造一个同名代理，而
    ``@ft.control`` 的字段全部拍平进 dataclass —— 用"和基类字段做差集"
    算 own 会在代理链上把真实字段误删（Label 曾因此变成 0 个字段）。
    """
    own = set(getattr(cls, "__dict__", {}).get("__annotations__", {}) or {})
    if own:
        return own
    for base in cls.__mro__[1:]:
        if base.__name__ == cls.__name__ and base.__module__ == cls.__module__:
            return set(getattr(base, "__dict__", {}).get("__annotations__", {}) or {})
    return set()


def _own_dataclass_fields(cls: type) -> list[dataclasses.Field]:
    """只取**本类新增**的 dataclass 字段（继承来的由 ancestors 负责）。"""
    if not dataclasses.is_dataclass(cls):
        return []
    own = _own_annotation_names(cls)
    return [
        f
        for f in dataclasses.fields(cls)
        if f.name in own and not f.name.startswith("_")
    ]


def _inline_comments(cls: type) -> dict[str, str]:
    """从源码里捞出字段行尾注释。

    cs-ui 大量使用中文行尾注释表达字段含义（``plain: bool = False  # 中心是否镂空``），
    这是运行时拿不到的信息，但对读索引的人价值极高。
    """
    try:
        source = inspect.getsource(cls)
    except (OSError, TypeError):
        return {}
    comments: dict[str, str] = {}
    for line in source.splitlines():
        match = _INLINE_COMMENT_RE.match(line)
        if match:
            comments.setdefault(match.group(1), match.group(2).strip())
    return comments


def _is_event_field(entry: dict[str, Any]) -> bool:
    return entry["name"].startswith("on_") or bool(
        _EVENT_TYPE_RE.search(entry.get("type") or "")
    )


def _field_entry(field: dataclasses.Field, comments: dict[str, str]) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "name": field.name,
        "type": type_str(field.type),
        "default": default_str(field.default),
    }
    if field.default is dataclasses.MISSING and field.default_factory is not dataclasses.MISSING:  # type: ignore[misc]
        factory = getattr(field.default_factory, "__name__", "")
        entry["default"] = {"list": "[]", "dict": "{}", "set": "set()"}.get(
            factory, f"{factory}()" if factory else "…"
        )
    note = comments.get(field.name)
    if note:
        entry["doc"] = note
    return entry


def _instance_entries(cls: type) -> list[dict[str, Any]]:
    """dataclass 字段（控件/数据对象的主参数表）。"""
    comments = _inline_comments(cls)
    return [_field_entry(f, comments) for f in _own_dataclass_fields(cls)]


def _namedtuple_entries(cls: type) -> list[dict[str, Any]]:
    names = list(getattr(cls, "_fields", []) or [])
    defaults = list(getattr(cls, "_field_defaults", {}) or {})
    hints = typing.get_type_hints(cls) if names else {}
    entries = []
    for name in names:
        entries.append(
            {
                "name": name,
                "type": type_str(hints.get(name, "")),
                "default": default_str(defaults.get(name, dataclasses.MISSING))
                if name in defaults
                else None,
            }
        )
    return entries


def _method_entries(cls: type) -> list[dict[str, Any]]:
    """本类（含 ui 包内的基类）声明的公开方法。"""
    seen: set[str] = set()
    entries: list[dict[str, Any]] = []
    for base in cls.__mro__:
        module = getattr(base, "__module__", "") or ""
        if base is not cls and not module.startswith("ui"):
            continue
        for name, raw in base.__dict__.items():
            if name.startswith("_") or name in seen:
                continue
            func = raw
            if isinstance(raw, (staticmethod, classmethod)):
                func = raw.__func__  # type: ignore[attr-defined]
            if not inspect.isfunction(func):
                continue
            seen.add(name)
            entries.append(_describe_callable(name, func, is_method=True))
    return entries


def _describe_callable(name: str, func: Any, is_method: bool = False) -> dict[str, Any]:
    try:
        sig = inspect.signature(func)
        params = list(sig.parameters.values())
        if is_method and params and params[0].name in ("self", "cls"):
            params = params[1:]
        args = [
            {
                "name": p.name,
                "type": type_str(p.annotation),
                "default": default_str(p.default) if p.default is not inspect.Parameter.empty else None,
                "kind": p.kind.name.lower(),
            }
            for p in params
        ]
        rendered = ", ".join(
            p.name
            + (f": {type_str(p.annotation)}" if p.annotation is not inspect.Parameter.empty else "")
            + (
                f" = {default_str(p.default)}"
                if p.default is not inspect.Parameter.empty
                else ""
            )
            for p in params
        )
    except (ValueError, TypeError):
        args, rendered = [], ""
    entry: dict[str, Any] = {
        "name": name,
        "args": args,
        "signature": f"{name}({rendered})",
        "doc": full_doc(inspect.getdoc(func)),
    }
    if inspect.iscoroutinefunction(func):
        entry["async"] = True
    return entry


def _base_key(base: type, ui_class_names: set[str]) -> str:
    """基类键：ui 内部用裸类名，外部用 ``包名.类名``。

    不能只按"类名是否出现在 ui 里"判断 —— cs-ui 的 ``Button`` 与
    ``flet.Button`` 同名，只看名字会把外部基类误认成自家兄弟类。
    """
    module = base.__module__ or ""
    if module.split(".")[0] == "ui":
        return base.__name__
    return f"{module.split('.')[0]}.{base.__name__}"


def _bases_of(cls: type, ui_class_names: set[str]) -> list[str]:
    keys = []
    for base in cls.__bases__:
        if base is object:
            continue
        # `@ft.observable` 生成的代理类会把原类当基类（同名同模块），跳过自引用；
        # Observable 是框架底座，列出来只会误导。
        if base.__name__ == cls.__name__ and base.__module__ == cls.__module__:
            continue
        if base.__name__ in ("Observable", "BaseControl", "object"):
            continue
        keys.append(_base_key(base, ui_class_names))
    return keys


def _classify(cls: type) -> tuple[str, str]:
    """→ (kind, pattern)。

    kind:    enum / control / component / type / mixin / helper
    pattern: 静态控件 static / 有状态组件 observable / 混入 mixin /
             纯数据 dataclass / 枚举 enum / 普通类 class
    """
    import flet as ft

    if isinstance(cls, type) and issubclass(cls, enum.Enum):
        return "enum", "enum"
    if isinstance(cls, type) and issubclass(cls, ft.BaseControl):
        return "control", "static"
    if dataclasses.is_dataclass(cls) and callable(getattr(cls, "ui", None)):
        return "component", "observable"
    if dataclasses.is_dataclass(cls):
        return "type", "dataclass"
    if callable(getattr(cls, "ui", None)):
        # 非 dataclass 但有 ui() —— 例如 CalendarPanel(混入+渲染方法)
        return "component", "observable"
    if any("PanelField" in b.__name__ for b in cls.__mro__):
        return "mixin", "mixin"
    return "helper", "class"


def _pattern_note(kind: str, name: str) -> str | None:
    if kind == "component":
        return (
            f"有状态组件：`{name}(...)` 返回的是数据对象，**必须**调用 `.ui()` "
            "拿到控件再放进控件树；且只能在 @ft.component 渲染上下文里调用，"
            "实例要用 state()/use_ref 固定，否则父组件重渲染会重建对象、丢状态。"
        )
    if kind == "control":
        return "静态控件：构造即用，直接放进 controls。"
    if kind == "type":
        return "纯数据对象：不是控件，不能直接放进 controls。"
    if kind == "mixin":
        return "混入/基类：不要直接实例化，用它的子类。"
    return None


def describe_class(
    cls: type,
    *,
    module: str,
    ui_class_names: set[str],
    exported: bool,
    category: list[str],
) -> dict[str, Any]:
    kind, pattern = _classify(cls)
    docstring = full_doc(inspect.getdoc(cls))
    # dataclass 会给没有 docstring 的类塞一个"签名式 docstring"，
    # Enum 会继承 "Create a collection of name/value pairs." —— 都丢掉
    if docstring.startswith(f"{cls.__name__}(") or docstring.startswith(_BOILERPLATE_DOCS):
        docstring = ""

    if kind == "enum":
        members = [
            {"name": m.name, "value": _enum_value(m.value)}
            for m in cls  # type: ignore[attr-defined]
        ]
        return {
            "name": cls.__name__,
            "module": module,
            "kind": "enum",
            "pattern": "enum",
            "summary": first_sentence(docstring),
            "docstring": docstring,
            "exported": exported,
            "categories": category,
            # 与类条目保持同构：消费方不用为枚举写分支
            "bases": [],
            "properties": [],
            "events": [],
            "methods": [],
            "members": members,
        }

    if dataclasses.is_dataclass(cls):
        instance_fields = _instance_entries(cls)
    elif hasattr(cls, "_fields"):
        instance_fields = _namedtuple_entries(cls)
    else:
        instance_fields = []

    properties = [e for e in instance_fields if not _is_event_field(e)]
    events = [e for e in instance_fields if _is_event_field(e)]

    bases = _bases_of(cls, ui_class_names)

    notes = []
    pattern_note = _pattern_note(kind, cls.__name__)
    if pattern_note:
        notes.append(pattern_note)
    if any(b.endswith("PanelField") for b in [x.__name__ for x in cls.__mro__]):
        notes.append(
            "选择器外壳家族（PanelField）：折叠态输入框 + 页面浮层面板，"
            "详情见 get_api('PanelField')。"
        )

    entry: dict[str, Any] = {
        "name": cls.__name__,
        "module": module,
        "kind": kind,
        "pattern": pattern,
        "summary": first_sentence(docstring),
        "docstring": docstring,
        "exported": exported,
        "categories": category,
        "bases": bases,
        "properties": properties,
        "events": events,
        "methods": _method_entries(cls),
        "notes": notes,
    }
    module_obj = sys.modules.get(module)
    if module_obj is not None:
        module_doc = full_doc(inspect.getdoc(module_obj))
        if module_doc and module_doc != docstring:
            entry["module_doc"] = module_doc
    if "用法" in docstring or "Usage" in docstring:
        entry["usage"] = _usage_block(docstring)
    return entry


def _usage_block(docstring: str) -> str | None:
    """从 docstring 里抠出 ``用法::`` / ``Usage::`` 后的缩进代码块。"""
    lines = docstring.splitlines()
    for idx, line in enumerate(lines):
        if "用法" in line or line.strip().lower().startswith("usage"):
            block = textwrap.dedent("\n".join(lines[idx + 1 :])).strip("\n")
            if block:
                return block
    return None


# ---------------------------------------------------------------------------
# 扫描整个包
# ---------------------------------------------------------------------------


def _category_of(module: str, packages: set[str]) -> list[str]:
    parts = module.split(".")
    if len(parts) < 2:
        return []
    category = [parts[1]]
    if len(parts) > 2:
        sub = ".".join(parts[:3])
        leaf = parts[2]
        if sub in packages and leaf != parts[1]:
            category.append(leaf)
    return category


def _module_packages(modules: list[types.ModuleType]) -> set[str]:
    return {m.__name__ for m in modules if hasattr(m, "__path__")}


def build_meta(module_count: int, counts: dict[str, int]) -> dict[str, Any]:
    try:
        import flet as ft

        flet_version = getattr(ft, "__version__", "")
    except Exception:
        flet_version = ""
    import ui

    return {
        "package": "ui",
        "product": "cs-ui",
        "version": getattr(ui, "__version__", ""),
        "python": sys.version.split()[0],
        "flet": flet_version,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "modules": module_count,
        "counts": counts,
    }


def scan() -> dict[str, Any]:
    """扫描 ``ui`` 包，返回完整索引字典。"""
    import ui
    import flet as ft  # noqa: F401  (确保 ft 已导入，供 _classify 使用)

    module_names = _ui_module_names()
    modules = [m for m in (_import(n) for n in module_names) if m is not None]
    packages = _module_packages(modules)
    exported_names = set(dir(ui))

    # 先收集 ui 自己声明的类名，供基类键解析用
    ui_class_names: set[str] = set()
    for mod in modules:
        for name, obj in vars(mod).items():
            if inspect.isclass(obj) and getattr(obj, "__module__", "") == mod.__name__:
                ui_class_names.add(name)

    components: list[dict[str, Any]] = []
    types_: list[dict[str, Any]] = []
    functions: list[dict[str, Any]] = []
    enums: list[dict[str, Any]] = []
    seen_objects: dict[int, dict[str, Any]] = {}
    ancestor_classes: dict[str, type] = {}

    for mod in modules:
        is_public_module = not any(p.startswith("_") for p in mod.__name__.split("."))
        category = _category_of(mod.__name__, packages)
        for name, obj in vars(mod).items():
            if name.startswith("_"):
                continue
            if getattr(obj, "__module__", "") != mod.__name__:
                continue  # 别把 re-export 进来的 flet 符号算成自研组件

            # 同一个对象绑了多个名字（`Title = Header_1`、`SubHeader = Header_2`、
            # `RadioGroup = Radio`）时，只留一条，其余记为别名 —— 否则一次扫描
            # 会产出三份 Header_1，搜出来还以为有三个不同的组件。
            existing = seen_objects.get(id(obj))
            if existing is not None:
                if name != existing["name"] and name not in existing.setdefault("aliases", []):
                    existing["aliases"].append(name)
                continue

            if inspect.isclass(obj):
                entry = describe_class(
                    obj,
                    module=mod.__name__,
                    ui_class_names=ui_class_names,
                    exported=name in exported_names,
                    category=category,
                )
                if entry["kind"] == "enum":
                    enums.append(entry)
                elif entry["kind"] == "type":
                    types_.append(entry)
                else:
                    components.append(entry)
                if not is_public_module:
                    entry["internal"] = True
                seen_objects[id(obj)] = entry
                # 收集非 ui 祖先，供继承成员查询
                for base in obj.__mro__[1:]:
                    if base is object:
                        continue
                    if (base.__module__ or "").startswith("ui"):
                        continue
                    ancestor_classes[f"{base.__module__.split('.')[0]}.{base.__name__}"] = base
            elif inspect.isfunction(obj) or inspect.ismethod(obj):
                if name in _DEMO_ENTRY_NAMES:
                    # 库里各模块末尾的 `def App()` / `main()` 是自带示例入口，
                    # 不是给使用者调的 API；索引进来只会把 functions 撑成噪音。
                    continue
                func = obj
                is_component = bool(getattr(func, "__is_component__", False))
                described = _describe_callable(name, func)
                entry = {
                    "name": name,
                    "module": mod.__name__,
                    "kind": "component" if is_component else (
                        "hook" if name.startswith("use_") else "function"
                    ),
                    "pattern": "function",
                    "summary": first_sentence(described["doc"]),
                    "docstring": described["doc"],
                    "exported": name in exported_names,
                    "categories": category,
                    "args": described["args"],
                    "signature": described["signature"],
                }
                if described.get("async"):
                    entry["async"] = True
                if not is_public_module:
                    entry["internal"] = True
                if is_component:
                    entry["notes"] = [
                        "函数组件：直接当控件用（返回 Control），内部可用 hooks，"
                        "但必须在渲染上下文中执行。"
                    ]
                functions.append(entry)
                seen_objects[id(obj)] = entry

    ancestors = []
    for key, cls in sorted(ancestor_classes.items()):
        ancestors.append(_describe_ancestor(key, cls))

    # 继承块：把 bases 翻译成"有多少成员可以查"，让 agent 决定要不要下钻。
    by_key = {a["key"]: a for a in ancestors}
    by_name = {c["name"]: c for c in components + types_}
    for entry in components + types_:
        blocks = []
        for base in entry.get("bases") or []:
            target = by_name.get(base) or by_key.get(base)
            if target is None:
                continue
            blocks.append(
                {
                    "from": base,
                    "properties": len(target.get("properties") or []),
                    "events": len(target.get("events") or []),
                    "methods": len(target.get("methods") or []),
                }
            )
        if blocks:
            entry["inherited"] = blocks

    counts = {
        "components": len(components),
        "types": len(types_),
        "functions": len(functions),
        "enums": len(enums),
        "ancestors": len(ancestors),
    }
    return {
        "meta": build_meta(len(modules), counts),
        "categories": _category_counts(components + types_ + functions + enums),
        "components": components,
        "types": types_,
        "functions": functions,
        "enums": enums,
        "ancestors": ancestors,
    }


def _describe_ancestor(key: str, cls: type) -> dict[str, Any]:
    """flet / flet_* 里的祖先类：只留成员表，供"继承属性"查询。"""
    kind = "control"
    try:
        import flet as ft

        if not (isinstance(cls, type) and issubclass(cls, ft.BaseControl)):
            kind = "service" if "Service" in cls.__name__ else "type"
    except Exception:
        pass

    if dataclasses.is_dataclass(cls):
        fields = [
            _field_entry(f, {})
            for f in _own_dataclass_fields(cls)
            if f.name not in _PLUMBING
        ]
    else:
        fields = []

    docstring = full_doc(inspect.getdoc(cls))
    if docstring.startswith(f"{cls.__name__}("):
        docstring = ""
    return {
        "name": cls.__name__,
        "key": key,
        "module": cls.__module__,
        "package": key.split(".")[0],
        "kind": kind,
        "summary": first_sentence(docstring),
        "properties": [e for e in fields if not _is_event_field(e)],
        "events": [e for e in fields if _is_event_field(e)],
        "bases": [
            f"{b.__module__.split('.')[0]}.{b.__name__}"
            for b in cls.__bases__
            if b is not object and not (b.__module__ or "").startswith("ui")
        ],
    }


def _category_counts(entries: list[dict[str, Any]]) -> dict[str, list[str]]:
    buckets: dict[str, list[str]] = {}
    for entry in entries:
        for cat in entry.get("categories") or ["uncategorized"]:
            buckets.setdefault(cat, [])
            if entry["name"] not in buckets[cat]:
                buckets[cat].append(entry["name"])
    return {k: sorted(v) for k, v in sorted(buckets.items())}
