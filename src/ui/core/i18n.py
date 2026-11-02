"""国际化 (i18n)：语言注册、翻译查表、声明式切换。

和 :mod:`ui.core.theme` 是同一套架构：**模块级 observable 单例 + context + hook**，
所以切语言和切明暗的手感完全一致 —— 只重绘订阅过的组件，不重建整棵控件树。

四条设计约束（都是被真实问题逼出来的）：

1. **键是扁平点号串**（``"app.title"``）。嵌套 dict 在**装表时**拍平一次，
   查表就是一次 ``dict.get`` —— 不在每次调用里 ``split`` 再逐层下钻。
   一个界面几百个文案，每次重绘都要查一遍，逐层下钻是纯浪费。
2. **缺翻译不抛异常**。UI 不该因为一句文案漏翻就白屏，返回键名本身
   （Qt / Flutter 都是这个取舍），同时**每个键只警告一次**；CI 里把
   ``configure(strict=True)`` 一开就变成立即报错。
3. **回退是有链路的**：``zh_Hant → zh_Hans → en``。繁体只翻了一部分时，
   剩下的自动落到简体；简体缺了再落英文。语言之间的关系由
   :attr:`Language.fallback` 声明，没声明就按「同语言的其他字形」猜。
4. **首帧就是正确语言**。持久化的选择在第一次渲染**之前**读进来
   （同步 JSON 文件，不需要挂 Service、不需要 await），所以不会先闪一下
   默认语言再跳。用户显式切过就记住，没切过就跟随系统语言。

用法（应用入口）::

    from ui import I18nProvider, Language, load_catalogs, register_language

    register_language(Language("zh_Hans", "简体中文", "Simplified Chinese",
                               fallback="en"))
    register_language(Language("en", "English"))
    load_catalogs("assets/i18n")        # zh_Hans.json / en.json ...

    @ft.component
    def App():
        return I18nProvider(build=MainShell)

用法（组件内，**必须**用 hook 才会跟随切换重绘）::

    @ft.component
    def Toolbar():
        tr = use_t()
        return ft.Text(tr("app.title"))          # 复数：tr.n("files", 3)

组件外的普通代码（日志、菜单构造）用全局函数 ``t()`` / ``tn()`` ——
它们读的是当前状态，但**不订阅**，切语言时不会自己重绘。
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

import flet as ft

from ui.core.config import logger
from ui.core.tokens import FONT_SIZE, RADIUS, SPACE

__all__ = [
    "FileStore",
    "I18nProvider",
    "I18nState",
    "Language",
    "LanguageRegistry",
    "LanguageSwitcher",
    "LocaleStore",
    "MemoryStore",
    "Translator",
    "available_languages",
    "canonical",
    "configure",
    "current_language",
    "current_locale",
    "flatten",
    "i18n_context",
    "i18n_registry",
    "i18n_state",
    "load_catalogs",
    "missing_keys",
    "plural_category",
    "register_language",
    "register_messages",
    "register_plural_rule",
    "reset_registry",
    "set_locale",
    "system_locale",
    "t",
    "tn",
    "use_i18n",
    "use_t",
    "validate",
]

# ---------------------------------------------------------------------------
# 语言标签：zh-CN / zh_CN / zh-Hant-TW / en-US 都要能认
# ---------------------------------------------------------------------------
_SPLIT_TAG = re.compile(r"[-_]")

#: 地区 → 文字。中日韩这类"一种语言多种字形"必须靠 script 区分，
#: 否则 ``zh-CN`` 与 ``zh-TW`` 会被当成同一种语言，繁体用户会看到简体文案。
_SCRIPT_BY_REGION: dict[str, dict[str, str]] = {
    "zh": {
        "CN": "Hans",
        "SG": "Hans",
        "MY": "Hans",
        "TW": "Hant",
        "HK": "Hant",
        "MO": "Hant",
    },
}


def _parse(tag: str) -> tuple[str, str | None, str | None]:
    """把语言标签拆成 ``(语言, 文字, 地区)``，全部归一。

    ``zh-Hant-TW`` → ``("zh", "Hant", "TW")``；``zh-CN`` → ``("zh", "Hans", "CN")``
    （``CN`` 的 ``Hans`` 来自 :data:`_SCRIPT_BY_REGION`）。
    """
    parts = [p for p in _SPLIT_TAG.split(str(tag or "").strip()) if p]
    if not parts:
        return "", None, None
    language = parts[0].lower()
    script: str | None = None
    region: str | None = None
    for part in parts[1:]:
        if len(part) == 4 and part.isalpha():
            script = part.title()  # 四字母 = 文字（Hans / Hant / Latn）
        elif len(part) in (2, 3) and part.isalpha():
            region = part.upper()
    if script is None and region:
        script = _SCRIPT_BY_REGION.get(language, {}).get(region)
    return language, script, region


def canonical(tag: str) -> str:
    """归一语言标签：有文字就用 ``语言_文字``，否则 ``语言_地区``，再否则 ``语言``。

    ``zh-CN`` → ``zh_Hans``、``zh-Hant-TW`` → ``zh_Hant``、``en-US`` → ``en_US``。
    **注册表里的 code 都用这个形式**，查询时再按语言/文字宽松匹配（见
    :meth:`LanguageRegistry.resolve`），所以只注册了 ``en`` 也能接住 ``en-US``。
    """
    language, script, region = _parse(tag)
    if not language:
        return ""
    if script:
        return f"{language}_{script}"
    if region:
        return f"{language}_{region}"
    return language


# ---------------------------------------------------------------------------
# 消息表拍平
# ---------------------------------------------------------------------------
def flatten(messages: Mapping[str, Any], prefix: str = "") -> dict[str, str]:
    """把嵌套消息表拍成 ``{"app.title": "..."}``。

    允许任意层级嵌套；数字/布尔按字面量转字符串（写 ``"count": 3`` 的稿子也能用），
    其他类型（列表、None）视为笔误直接报错 —— 装表阶段就炸，比运行到某页才炸好。
    """
    flat: dict[str, str] = {}
    for key, value in messages.items():
        path = f"{prefix}{key}"
        if isinstance(value, Mapping):
            flat.update(flatten(value, f"{path}."))
        elif isinstance(value, str):
            flat[path] = value
        elif isinstance(value, (int, float, bool)):
            flat[path] = str(value)
        else:
            raise TypeError(
                f"翻译值必须是字符串或嵌套字典：{path} -> {type(value).__name__}"
            )
    return flat


# ---------------------------------------------------------------------------
# 复数：只有 one / other 两档，够中英繁用；需要俄语/阿拉伯语时注册自己的规则
# ---------------------------------------------------------------------------
_PluralRule = Callable[[float], str]

_PLURAL_RULES: dict[str, _PluralRule] = {
    # 中文没有单复数形态变化：永远走 other（文案里写 "…{n} 项" 即可）
    "zh": lambda _n: "other",
    "ja": lambda _n: "other",
    "ko": lambda _n: "other",
    "en": lambda n: "one" if n == 1 else "other",
    "fr": lambda n: "one" if n in (0, 1) else "other",
}


def register_plural_rule(language: str, rule: _PluralRule) -> None:
    """给某种语言注册复数规则（入参是数量，返回 ``"one"`` / ``"other"``）。"""
    _PLURAL_RULES[str(language).lower()] = rule


def plural_category(tag: str, count: float) -> str:
    """取该语言下数量对应的复数档位（未注册的语言按 ``n == 1`` 二分）。"""
    rule = _PLURAL_RULES.get(_parse(tag)[0])
    return rule(count) if rule else ("one" if count == 1 else "other")


# ---------------------------------------------------------------------------
# 语言元数据
# ---------------------------------------------------------------------------
@dataclass(frozen=True, slots=True)
class Language:
    """一种语言：编码 + 母语名 + 英文名 + 回退目标。

    ``native_name`` 是菜单里给用户看的**母语写法**（简体中文 / 繁體中文 / English）——
    这是桌面软件的通行做法：用户在自己的语言列表里永远认得出自己的语言，
    哪怕界面已经是看不懂的外语。

    Args:
        code: 语言标签，``zh_CN`` / ``zh-Hant`` / ``en`` 都能写，构造时统一归一。
        native_name: 母语名，显示在语言菜单里。
        english_name: 英文名，次要显示（母语名与英文名相同时可省）。
        fallback: 回退语言（``zh_Hant`` 一般回退 ``zh_Hans``）。不填则按
            「同语言的其他字形」自动推断。
        direction: ``ltr`` / ``rtl``；RTL 语言会被同步到 ``page.rtl``。
    """

    code: str
    native_name: str = ""
    english_name: str = ""
    fallback: str | None = None
    direction: str = "ltr"

    def __post_init__(self) -> None:
        object.__setattr__(self, "code", canonical(self.code) or str(self.code))
        if self.fallback:
            object.__setattr__(self, "fallback", canonical(self.fallback))
        if not self.native_name:
            object.__setattr__(self, "native_name", self.code)

    @property
    def is_rtl(self) -> bool:
        return self.direction.lower() == "rtl"

    @property
    def label(self) -> str:
        """菜单里显示的主标题（母语名）。"""
        return self.native_name or self.code

    def __str__(self) -> str:
        return f"{self.label} ({self.code})"


# ---------------------------------------------------------------------------
# 注册表：语言 + 各自的扁平消息表
# ---------------------------------------------------------------------------
class LanguageRegistry:
    """语言与消息表的注册中心（进程内单例 :data:`i18n_registry`）。

    注册顺序 = 语言菜单的显示顺序，所以顺序本身有意义：把常用语言放前面。
    """

    def __init__(self) -> None:
        self._languages: dict[str, Language] = {}
        self._catalogs: dict[str, dict[str, str]] = {}

    # ---- 语言 ----

    def add_language(
        self,
        language: Language | str,
        *,
        native_name: str = "",
        english_name: str = "",
        fallback: str | None = None,
        direction: str = "ltr",
    ) -> Language:
        """注册（或覆盖）一种语言。传 str 时其余字段用关键字补。"""
        item = (
            language
            if isinstance(language, Language)
            else Language(
                code=str(language),
                native_name=native_name,
                english_name=english_name,
                fallback=fallback,
                direction=direction,
            )
        )
        self._languages[item.code] = item
        self._catalogs.setdefault(item.code, {})
        return item

    def languages(self) -> tuple[Language, ...]:
        """已注册语言，按注册顺序。"""
        return tuple(self._languages.values())

    def get(self, code: str) -> Language | None:
        return self._languages.get(code)

    def resolve(self, tag: str) -> str | None:
        """把任意语言标签解析成**已注册的** code（认不出就返回 ``None``）。

        三级命中：精确 → 同语言同文字 → 同语言。所以只注册了 ``en`` 时，
        ``en-US`` / ``en_GB`` 都会落到 ``en``；注册了 ``zh_Hans`` / ``zh_Hant``
        时，``zh-CN`` 落简体、``zh-TW`` 落繁体。
        """
        if not tag:
            return None
        code = canonical(tag)
        if code in self._languages:
            return code
        language, script, _ = _parse(code)
        same = [c for c in self._languages if _parse(c)[0] == language]
        if not same:
            return None
        for candidate in same:
            if _parse(candidate)[1] == script:
                return candidate
        for candidate in same:
            if _parse(candidate)[1] is None:  # 没有字形偏好的基础档
                return candidate
        return same[0]

    def fallback_of(self, code: str) -> str | None:
        """``code`` 的下一个回退目标：先看声明的 fallback，再看同语言的其他字形。"""
        language = self._languages.get(code)
        if language and language.fallback:
            return self.resolve(language.fallback)
        base, _, _ = _parse(code)
        for candidate in self._languages:
            if candidate != code and _parse(candidate)[0] == base:
                return candidate
        return None

    # ---- 消息表 ----

    def add_messages(
        self, code: str, messages: Mapping[str, Any], *, create: bool = True
    ) -> int:
        """合并一份消息表，返回本次写入的键数量（同键以后写的为准）。"""
        target = self.resolve(code) or canonical(code)
        if not target:
            raise ValueError("语言编码不能为空")
        if target not in self._languages:
            if not create:
                raise KeyError(f"语言未注册：{code}")
            self.add_language(target)
        flat = flatten(messages)
        self._catalogs[target].update(flat)
        return len(flat)

    def messages(self, code: str) -> Mapping[str, str]:
        """取某种语言的扁平消息表（只读，不要改）。"""
        return self._catalogs.get(code, {})

    def has_key(self, code: str, key: str) -> bool:
        return key in self._catalogs.get(code, {})

    # ---- 文件 ----

    def load_file(self, path: str | Path) -> int:
        """载入一个 JSON 语言包，返回写入的键数量。

        两种写法都支持（``_meta`` 可省，语言编码默认取文件名）::

            {"_meta": {"native_name": "Français", "fallback": "en"},
             "messages": {"app": {"title": "Mon App"}}}

            {"app.title": "Mon App"}
        """
        file = Path(path)
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            logger.error(f"语言包读取失败 {file}：{exc}")
            return 0
        if not isinstance(data, dict):
            logger.error(f"语言包必须是 JSON 对象：{file}")
            return 0

        meta = data.get("_meta") or data.get("meta") or {}
        if not isinstance(meta, Mapping):
            meta = {}
        body = data.get("messages")
        if not isinstance(body, Mapping):
            body = {k: v for k, v in data.items() if k not in ("_meta", "meta")}

        code = str(meta.get("code") or file.stem)
        if self.resolve(code) is None:
            self.add_language(
                code,
                native_name=str(meta.get("native_name") or ""),
                english_name=str(meta.get("english_name") or ""),
                fallback=meta.get("fallback"),
                direction=str(meta.get("direction") or "ltr"),
            )
        return self.add_messages(code, body)

    def load_dir(self, path: str | Path, pattern: str = "*.json") -> int:
        """载入目录下所有语言包（``zh_Hans.json`` / ``en.json`` …），返回总键数。"""
        folder = Path(path)
        if not folder.is_dir():
            logger.warning(f"语言包目录不存在：{folder}")
            return 0
        total = 0
        for file in sorted(folder.glob(pattern)):
            total += self.load_file(file)
        return total

    def clear(self) -> None:
        """清空全部注册（测试用；框架内置的三份语言包也会被清掉）。"""
        self._languages.clear()
        self._catalogs.clear()


#: 进程级注册表
i18n_registry = LanguageRegistry()


# ---------------------------------------------------------------------------
# 框架自用文案：语言切换器要说人话，而且必须自己走一遍 i18n
# ---------------------------------------------------------------------------
_BUILTIN_LANGUAGES: tuple[Language, ...] = (
    Language("zh_Hans", "简体中文", "Simplified Chinese", fallback="en"),
    Language("zh_Hant", "繁體中文", "Traditional Chinese", fallback="zh_Hans"),
    Language("en", "English", "English"),
)

_BUILTIN_MESSAGES: dict[str, dict[str, str]] = {
    "zh_Hans": {"ui.language.tooltip": "界面语言"},
    "zh_Hant": {"ui.language.tooltip": "介面語言"},
    "en": {"ui.language.tooltip": "Interface language"},
}


def _install_builtins() -> None:
    for language in _BUILTIN_LANGUAGES:
        i18n_registry.add_language(language)
    for code, messages in _BUILTIN_MESSAGES.items():
        i18n_registry.add_messages(code, messages)


_install_builtins()


# 模块级便捷函数：注册表的主入口（比直接操作 i18n_registry 读起来短）
def register_language(language: Language | str, **kwargs: Any) -> Language:
    """注册一种语言（等价于 :meth:`LanguageRegistry.add_language`）。"""
    return i18n_registry.add_language(language, **kwargs)


def register_messages(code: str, messages: Mapping[str, Any]) -> int:
    """给某种语言注册/合并一份消息表，返回键数量。

    运行期调用也会生效：这里会把状态的 ``revision`` 推进一格，订阅了
    ``use_t()`` 的组件随即重绘 —— 语言包热更新、插件式加载文案都靠它。
    """
    count = i18n_registry.add_messages(code, messages)
    _bump_revision()
    return count


def load_catalogs(path: str | Path) -> int:
    """载入语言包：传目录就批量载入，传文件就单个载入。"""
    source = Path(path)
    count = (
        i18n_registry.load_dir(source)
        if source.is_dir()
        else i18n_registry.load_file(source)
    )
    _bump_revision()
    return count


def available_languages() -> tuple[Language, ...]:
    """已注册语言（按注册顺序，直接可喂给语言菜单）。"""
    return i18n_registry.languages()


def reset_registry() -> None:
    """清空并恢复框架内置语言包（测试用）。"""
    i18n_registry.clear()
    _install_builtins()
    if "_state" in globals():
        _bump_revision()


def _bump_revision() -> None:
    """通知订阅者"文案变了"。

    在模块导入阶段（注册内置语言包、应用启动时注册文案）状态可能还没建好，
    而那时也**不可能有订阅者**，所以静默跳过。
    """
    state = globals().get("_state")
    if state is not None:
        state.revision += 1


# ---------------------------------------------------------------------------
# 持久化：桌面端一个 JSON 文件就够，同步读写，不需要挂 Service、不需要 await
# ---------------------------------------------------------------------------
class LocaleStore(Protocol):
    """语言选择的存取接口（想接数据库 / 配置中心时实现这两个方法即可）。"""

    def read(self) -> str | None: ...

    def write(self, code: str) -> None: ...


class MemoryStore:
    """不落盘（单元测试 / 临时会话）。"""

    def __init__(self, code: str | None = None) -> None:
        self.code = code

    def read(self) -> str | None:
        return self.code

    def write(self, code: str) -> None:
        self.code = code


class FileStore:
    """小 JSON 文件，默认落在系统配置目录。

    ``FLET_APP_STORAGE_DATA`` 存在时（flet 打包的桌面应用会设）就写在应用数据目录，
    否则按平台惯例：Windows ``%LOCALAPPDATA%\\cs-ui``、macOS ``Application Support``、
    Linux ``$XDG_CONFIG_HOME``。写临时文件再 ``os.replace``，断电也不会留半个坏文件。
    """

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else default_config_path()

    def read(self) -> str | None:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        code = data.get("locale") if isinstance(data, dict) else None
        return code if isinstance(code, str) and code else None

    def write(self, code: str) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temp = self.path.with_suffix(".tmp")
            temp.write_text(
                json.dumps({"locale": code}, ensure_ascii=False), encoding="utf-8"
            )
            os.replace(temp, self.path)
        except OSError as exc:  # 只读盘 / 权限不足：记住选择失败不该影响使用
            logger.warning(f"语言选择写入失败 {self.path}：{exc}")


def config_dir() -> Path:
    """配置文件目录（跟随平台惯例）。"""
    env = os.getenv("FLET_APP_STORAGE_DATA")
    if env:
        return Path(env)
    if sys.platform == "win32":
        base = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA")
        return Path(base or Path.home(), "cs-ui")
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "cs-ui"
    return Path(os.getenv("XDG_CONFIG_HOME") or Path.home() / ".config") / "cs-ui"


def default_config_path() -> Path:
    return config_dir() / "i18n.json"


def system_locale() -> str | None:
    """系统界面语言（``zh_CN`` / ``en_US`` / ``fr_FR`` …），取不到返回 ``None``。

    Windows 走 ``GetUserDefaultUILanguage``（比环境变量准，中文用户常见
    ``LANG`` 缺失）；其他平台读 ``LC_ALL`` / ``LC_MESSAGES`` / ``LANG``。
    **只用于首次启动的默认值**，用户切过之后以持久化选择为准。
    """
    if sys.platform == "win32":
        try:
            import ctypes
            import locale as _locale

            tag = _locale.windows_locale.get(
                ctypes.windll.kernel32.GetUserDefaultUILanguage()  # type: ignore[attr-defined]
            )
            if tag:
                return tag
        except Exception:  # noqa: BLE001 - 探测失败就退回环境变量，不该让启动失败
            logger.debug("GetUserDefaultUILanguage 探测失败，改用环境变量")
    for name in ("LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.getenv(name)
        if value:
            return value.split(".")[0].split("@")[0]
    return None


# ---------------------------------------------------------------------------
# 状态
# ---------------------------------------------------------------------------
def _number(value: float) -> int | float:
    """整数就还整数，别把 3 显示成 3.0。"""
    return int(value) if float(value).is_integer() else value


class _SafeParams(dict):
    """缺参数时保留占位符原文（``{name}``），而不是抛 KeyError。"""

    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def _format(
    state: I18nState, template: str, params: Mapping[str, Any], key: str
) -> str:
    """插值。先走 ``str.format`` 快路径，出错才退到「保留占位符」的安全路径。

    正常情况零额外开销（不建临时 dict、不做异常分支判断）；写错参数名时
    界面显示 ``你好，{name}`` 而不是整页崩掉，同时日志里点名是哪个键。
    """
    try:
        return template.format(**params)
    except (KeyError, IndexError, ValueError, AttributeError):
        pass
    try:
        return template.format_map(_SafeParams(params))
    except Exception:  # noqa: BLE001 - 译文里的大括号自己写错了
        _warn_once(
            state, f"fmt:{key}", f"翻译插值失败，原样输出：{key} -> {template!r}"
        )
        return template


def _warn_once(state: I18nState, tag: str, message: str) -> None:
    """同一个问题只警告一次（几百个组件同时缺一个键时别刷屏）。"""
    if tag in state._warned:
        return
    state._warned.add(tag)
    logger.warning(message)


@ft.observable
@dataclass
class I18nState:
    """全局多语言状态。

    模块级单例（:func:`i18n_state`），由 :func:`I18nProvider` 写进 ``page``。
    和 :class:`ui.core.theme.ThemeState` 一样选单例而不是每处 new 一个：
    语言本来就是应用级全局设置，再造一层"这个文案跟谁走"只会更难查。
    """

    locale: str = "en"  # 当前语言（注册表里的 code）
    fallback: str = "en"  # 兜底语言：所有回退链的终点
    strict: bool = False  # True = 缺键立即抛 KeyError（CI / 单测）
    revision: int = 0  # 消息表热更新后 +1，用来强制订阅者重绘

    # 下面都是内部字段：以 "_" 开头，Observable 不会因此触发重绘
    _chain: tuple[str, ...] = field(default_factory=tuple, repr=False)
    _missing: dict[str, int] = field(default_factory=dict, repr=False)
    _warned: set[str] = field(default_factory=set, repr=False)
    _store: LocaleStore | None = field(default=None, repr=False)
    _dirty: bool = field(default=False, repr=False)
    _bound: bool = field(default=False, repr=False)

    def __post_init__(self) -> None:
        self._refresh()

    # ---- 当前语言 ----

    @property
    def language(self) -> Language:
        """当前语言的元数据（母语名 / 方向）。"""
        found = i18n_registry.get(self.locale)
        return found or Language(self.locale or "und")

    @property
    def is_rtl(self) -> bool:
        return self.language.is_rtl

    def languages(self) -> tuple[Language, ...]:
        return i18n_registry.languages()

    def set_locale(self, code: str, *, persist: bool = True) -> bool:
        """切换语言。返回 ``False`` 表示该语言未注册（不做任何改动）。

        语言没变就直接返回，**不触发重绘** —— 语言菜单里点当前项不该让整个界面
        抖一下。``persist=False`` 用于临时预览（不写盘）。
        """
        resolved = i18n_registry.resolve(code)
        if resolved is None:
            logger.warning(
                f"未注册的语言：{code!r}（可选：{', '.join(self._codes())}）"
            )
            return False
        if resolved != self.locale:
            self.locale = resolved
            self._refresh()
        self._dirty = self._dirty or persist
        return True

    def _codes(self) -> list[str]:
        return [item.code for item in i18n_registry.languages()]

    def _refresh(self) -> None:
        """重建回退链。只在切语言 / 改兜底语言时调用。"""
        self._chain = self._build_chain(self.locale, self.fallback)

    @staticmethod
    def _build_chain(locale: str, fallback: str) -> tuple[str, ...]:
        chain: list[str] = []
        for start in (locale, fallback):
            code = i18n_registry.resolve(start) if start else None
            hops = 0
            while code and hops < 8 and code not in chain:
                chain.append(code)
                code = i18n_registry.fallback_of(code)
                hops += 1
        return tuple(chain)

    # ---- 查表 ----

    def has(self, key: str) -> bool:
        """当前语言（含回退）能否翻出这个键。"""
        return self._lookup(key) is not None

    def _lookup(self, key: str) -> str | None:
        catalogs = i18n_registry._catalogs
        for code in self._chain:
            bucket = catalogs.get(code)
            if bucket is not None:
                message = bucket.get(key)
                if message is not None:
                    return message
        return None

    def t(self, key: str, /, **params: Any) -> str:
        """取译文：``t("app.title")`` / ``t("hello", name="Shawn")``。

        没有参数时**不做插值**（直接返回原文），这是最高频的路径。
        """
        message = self._lookup(key)
        if message is None:
            return self._miss(key)
        return _format(self, message, params, key) if params else message

    def tn(self, key: str, count: float, /, **params: Any) -> str:
        """取复数译文：``tn("files", 3)`` → 命中 ``files.one`` / ``files.other``。

        ``n`` 和 ``count`` 会自动注入插值参数（模板里写 ``{n}`` 即可），
        想加千分位就用 ``{n:,}``。没有分档键时退回 ``key`` 本身。
        """
        category = plural_category(self.locale, count)
        message = None
        for candidate in (f"{key}.{category}", f"{key}.other", key):
            message = self._lookup(candidate)
            if message is not None:
                break
        if message is None:
            return self._miss(key)
        number = _number(count)
        params.setdefault("n", number)
        params.setdefault("count", number)
        return _format(self, message, params, key)

    def _miss(self, key: str) -> str:
        """缺键：记一次数、警告一次，然后**返回键名**（不白屏）。"""
        if self.strict:
            raise KeyError(f"缺少翻译：{key}（{self.locale}）")
        self._missing[key] = self._missing.get(key, 0) + 1
        _warn_once(
            self,
            f"miss:{key}",
            f"缺少翻译：{key}（语言 {self.locale}，回退链 {' -> '.join(self._chain)}）",
        )
        return key

    # ---- 诊断 ----

    def missing(self) -> dict[str, int]:
        """运行期缺过的键及次数（按次数降序）。"""
        return dict(sorted(self._missing.items(), key=lambda kv: -kv[1]))

    def reset_diagnostics(self) -> None:
        """清空缺键统计与"只警告一次"的记录（热更新语言包后用）。"""
        self._missing.clear()
        self._warned.clear()


#: 进程级单例
_state = I18nState(fallback=canonical("en") or "en")

#: 语言 context。默认值就是这个单例，所以**不挂 Provider 也能用**；
#: 真正的作用是 :func:`ft.use_context` 会替组件挂上 observable 订阅 ——
#: 直接在组件体里读单例字段**不会**订阅，切语言时会静默不更新。
i18n_context = ft.create_context(default_value=_state)


def i18n_state() -> I18nState:
    """拿全局状态单例（给组件外用；组件里请用 :func:`use_i18n`）。"""
    return _state


def configure(*, fallback: str | None = None, strict: bool | None = None) -> None:
    """调全局配置。``strict=True`` 会让缺键立即报错（CI 用）。"""
    if fallback is not None:
        resolved = i18n_registry.resolve(fallback)
        _state.fallback = resolved or canonical(fallback)
        _state._refresh()
    if strict is not None:
        _state.strict = bool(strict)


def set_locale(code: str, *, persist: bool = True) -> bool:
    """切语言（组件外调用；组件里直接 ``use_i18n().set_locale(...)``）。"""
    return _state.set_locale(code, persist=persist)


def current_locale() -> str:
    return _state.locale


def current_language() -> Language:
    return _state.language


def t(key: str, /, **params: Any) -> str:
    """取当前语言的译文（**不订阅**，适合日志、菜单构造等非渲染场景）。

    组件里要跟着切语言重绘，请用 :func:`use_t`。
    """
    return _state.t(key, **params)


def tn(key: str, count: float, /, **params: Any) -> str:
    """取复数译文（不订阅）。组件里用 ``use_t().n(key, count)``。"""
    return _state.tn(key, count, **params)


class Translator:
    """绑定到某次渲染的翻译器：``tr = use_t()``，然后 ``tr("key")``。

    订阅发生在 :func:`use_t` 里，所以这个对象只负责把调用转给状态；
    它读的是 ``locale`` 的**当前值**，不存在"缓存了旧语言"的问题。
    """

    __slots__ = ("_state",)

    def __init__(self, state: I18nState) -> None:
        self._state = state

    def __call__(self, key: str, /, **params: Any) -> str:
        return self._state.t(key, **params)

    def n(self, key: str, count: float, /, **params: Any) -> str:
        """复数形式：``tr.n("files", 3)``。"""
        return self._state.tn(key, count, **params)

    def has(self, key: str) -> bool:
        return self._state.has(key)

    @property
    def locale(self) -> str:
        return self._state.locale

    @property
    def language(self) -> Language:
        return self._state.language


def use_i18n() -> I18nState:
    """订阅全局多语言状态。**必须在组件体内调用**。"""
    return ft.use_context(i18n_context)


def use_t() -> Translator:
    """订阅语言并拿到翻译器 —— 组件里就用它。**必须在组件体内调用**。"""
    return Translator(use_i18n())


# ---------------------------------------------------------------------------
# Provider：首帧确定语言 + 变更时落到 page / 磁盘
# ---------------------------------------------------------------------------
def _to_ft_locale(language: Language) -> ft.Locale:
    base, script, region = _parse(language.code)
    return ft.Locale(language_code=base, script_code=script, country_code=region)


def _bind(
    page: ft.Page,
    state: I18nState,
    *,
    initial: str | None,
    store: LocaleStore | None,
    detect: bool,
) -> None:
    """首次渲染前解析出该用哪种语言：**存过的 > 应用指定的 > 系统语言 > 兜底**。

    顺序是刻意排的：用户显式切过的选择必须压过应用默认值，否则"我上次选了英文，
    这次打开又是中文"。``initial`` 只是没存过时的默认值。
    """
    state._store = store or FileStore()
    rescued = False
    try:
        saved = state._store.read()
    except Exception:  # noqa: BLE001 - 自定义 store 出错不该拖垮启动
        saved = None

    for candidate in (saved, initial, system_locale() if detect else None):
        if not candidate:
            continue
        resolved = i18n_registry.resolve(candidate)
        if resolved:
            if resolved != state.locale:
                # 首帧、尚无订阅者，跳过通知（否则在渲染期触发一次多余重绘）
                object.__setattr__(state, "locale", resolved)
            rescued = True
            break

    if not rescued:
        fallback = i18n_registry.resolve(state.fallback)
        codes = state._codes()
        if fallback or codes:
            object.__setattr__(state, "locale", fallback or codes[0])
    state._refresh()


def _apply(page: ft.Page, state: I18nState) -> None:
    """把语言同步到 Flutter 侧（内置控件跟着翻译 / RTL），并落盘。"""
    language = state.language
    try:
        page.rtl = language.is_rtl
    except Exception:  # noqa: BLE001 - 个别渲染后端没有 rtl
        logger.debug("当前后端不支持 page.rtl，跳过")
    try:
        # 让 Flutter 自带的 Material 组件（日期选择器、文本选择菜单…）也用同一种语言，
        # 否则自绘文案是英文、系统控件还是中文，看着像半成品。
        page.locale_configuration = ft.LocaleConfiguration(
            supported_locales=[_to_ft_locale(item) for item in state.languages()],
            current_locale=_to_ft_locale(language),
        )
    except Exception:  # noqa: BLE001 - 老版本 flet 没有这个字段，只影响系统控件
        logger.debug("page.locale_configuration 不可用，跳过系统控件语言同步")

    if state._dirty:
        state._dirty = False
        if state._store is not None:
            try:
                state._store.write(state.locale)
            except Exception as exc:  # noqa: BLE001 - 只读盘 / 权限不足
                logger.warning(f"语言选择持久化失败：{exc}")


@ft.component
def I18nProvider(
    *,
    build: Callable[[], ft.Control],
    locale: str | None = None,
    store: LocaleStore | None = None,
    detect: bool = True,
) -> ft.Control:
    """把多语言挂到页面。放在**根视图**里（与 :func:`ui.core.theme.ThemeProvider` 并列）。

    Args:
        build: **工厂函数**，返回应用主体。必须是函数：本组件用 ``use_memo`` 缓存它的
            结果，切语言时只让订阅了 ``use_t()`` 的组件重绘，**不重建整棵控件树** ——
            否则用户在表单里填了一半的内容会被语言切换清空。
        locale: 没存过选择时的默认语言（可写 ``zh-CN`` / ``zh_TW`` / ``en``）。
            不传就跟随系统。
        store: 自定义持久化（默认 :class:`FileStore`）。测试传 :class:`MemoryStore`。
        detect: 是否读系统语言作为首次启动的默认值。

    注意：``build`` 里如果直接写 ``t("key")`` 而不是用 ``use_t()``，切语言时
    那段文案不会更新 —— 这是 flet 订阅模型的固有行为（只有读 observable 的
    组件才会重绘），``use_t()`` 就是为此存在的一行订阅。
    """
    return _I18nBridge(build=build, initial=locale, store=store, detect=detect)


@ft.component
def _I18nBridge(
    *,
    build: Callable[[], ft.Control],
    initial: str | None,
    store: LocaleStore | None,
    detect: bool,
) -> ft.Control:
    """订阅状态 → 首帧绑定 → 同步 page / 写盘 → 返回缓存好的子树。"""
    page = ft.context.page
    state = use_i18n()

    if not state._bound:
        state._bound = True
        _bind(page, state, initial=initial, store=store, detect=detect)

    # 语言或消息表变了才重新下发；子树本身复用（不重建、不丢状态）
    ft.use_effect(lambda: _apply(page, state), [state.locale, state.revision])
    return ft.use_memo(build, [])


# ---------------------------------------------------------------------------
# 语言切换器（桌面端惯用形态：当前语言名 + 下拉勾选）
# ---------------------------------------------------------------------------
@ft.component
def LanguageSwitcher(*, compact: bool = False) -> ft.Control:
    """语言下拉菜单，直接放进顶栏。

    菜单项显示**母语名**（简体中文 / 繁體中文 / English）：用户就算已经切到看不懂的
    语言，也总能认出自己那一项；当前项打勾，英文名作为次要信息跟在后面。
    切换立即生效并落盘，界面上不需要"确定/应用"按钮。
    """
    state = use_i18n()
    tr = use_t()

    items: list[ft.Control] = []
    for language in state.languages():
        selected = language.code == state.locale
        items.append(
            ft.PopupMenuItem(
                content=ft.Row(
                    spacing=SPACE["2"],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        (
                            ft.Icon(
                                ft.Icons.CHECK,
                                size=FONT_SIZE["body"],
                                color=ft.Colors.PRIMARY,
                            )
                            if selected
                            else ft.Container(width=FONT_SIZE["body"])
                        ),
                        ft.Text(
                            language.native_name,
                            size=FONT_SIZE["body"],
                            weight=(
                                ft.FontWeight.W_600 if selected else ft.FontWeight.W_400
                            ),
                        ),
                        *(
                            [
                                ft.Text(
                                    language.english_name,
                                    size=FONT_SIZE["caption"],
                                    color=ft.Colors.ON_SURFACE_VARIANT,
                                )
                            ]
                            if language.english_name
                            and language.english_name != language.native_name
                            else []
                        ),
                    ],
                ),
                on_click=lambda _e, code=language.code: state.set_locale(code),
            )
        )

    if compact:
        return ft.PopupMenuButton(
            icon=ft.Icons.LANGUAGE,
            icon_color=ft.Colors.ON_SURFACE_VARIANT,
            tooltip=tr("ui.language.tooltip"),
            items=items,
        )

    return ft.PopupMenuButton(
        padding=0,
        tooltip=tr("ui.language.tooltip"),
        items=items,
        content=ft.Container(
            padding=ft.Padding.symmetric(horizontal=SPACE["2"], vertical=SPACE["1"]),
            border_radius=RADIUS["md"],
            content=ft.Row(
                spacing=SPACE["1"],
                tight=True,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(
                        ft.Icons.LANGUAGE,
                        size=FONT_SIZE["subtitle"],
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                    ft.Text(state.language.native_name, size=FONT_SIZE["body"]),
                    ft.Icon(
                        ft.Icons.ARROW_DROP_DOWN,
                        size=FONT_SIZE["title"],
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                ],
            ),
        ),
    )


# ---------------------------------------------------------------------------
# 翻译完整性体检（CI / 提测前跑一次）
# ---------------------------------------------------------------------------
def validate(reference: str | None = None) -> dict[str, list[str]]:
    """以基准语言为准，列出每种语言缺哪些键。

    Args:
        reference: 基准语言（默认取 ``state.fallback``）。基准语言自己不参与比较。

    Returns:
        ``{语言 code: [缺失的键]}``；全部齐全时返回 ``{code: []}``。
    """
    base = i18n_registry.resolve(reference or _state.fallback) or ""
    base_keys = set(i18n_registry.messages(base))
    report: dict[str, list[str]] = {}
    for language in i18n_registry.languages():
        if language.code == base:
            continue
        report[language.code] = sorted(
            base_keys - set(i18n_registry.messages(language.code))
        )
    return report


def missing_keys() -> dict[str, int]:
    """运行期缺过的键及次数（读的是全局状态）。"""
    return _state.missing()
