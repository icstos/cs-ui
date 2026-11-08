"""组件文档套件 —— 让每个实现文件自带「介绍 + 演示 + API」。

设计目标是**一份内容，两个出口**：

* 直接运行实现文件（``python src/ui/navigation/pagination.py``）→ 一个独立窗口，
  左边不用切、上下滚一屏就能读完这个组件；
* 文档站（``docs/``）把同一份 :class:`Spec` 渲染进
  ``/components/navigation/pagination``，一个字都不用重写。

所以这个模块只依赖 ``flet`` 本身（代码面板在渲染时才导入
``flet_code_editor``），放进 ``ui.core`` 不会拖慢任何组件的导入。

写法（放在实现文件末尾，组件代码之后）::

    SPEC = Spec(
        name="Pagination",
        summary="把长列表切成可控的页：总数、页码、跳页、每页条数。",
        definition="分页器解决的是「一屏放不下」。……",
        anatomy=[("总数", "左边那句「共 1,286 项」，随语言变。"), ...],
        when=["数据量超过一屏", "需要让用户直达某一页"],
        avoid=["十几行数据：一屏能看完，分页只添了一次点击"],
        examples=[
            Example("基础用法", _demo_basic, code=_BASIC_CODE, hint="……"),
        ],
        target=PaginationState,          # API 表从这里内省
        notes=[tip("……"), warn("……")],
    )

    if __name__ == "__main__":
        run(SPEC)

``group`` / ``key`` 不用写：``run()`` 从**调用方文件路径**推出来
（``src/ui/navigation/pagination.py`` → 导航 / ``pagination``），文档站则用
``ui.core.catalog`` 里的登记表 —— 两处推导出同一个键，靠
``scripts/_doc_logic.py`` 校验。
"""

from __future__ import annotations

import asyncio
import dataclasses
import inspect
import sys
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import flet as ft

from ui.core.tokens import FONT_SIZE, FONT_WEIGHT, ICON_SIZE, RADIUS, semantic_text

# 代码块配色：**故意不跟随明暗主题**。代码高亮有自己的色板，浅色主题下把
# 代码块也刷白，行内高亮的对比度会全线崩掉 —— VS Code / GitHub 也一样：
# 主题变，代码块底色保持深色。命名成常量，是为了让"刻意"和"随手写死"可区分。
_CODE_BG = "#0E1117"
_CODE_BG_BAR = "#151A22"
_CODE_BORDER = "#232A35"

__all__ = [
    "Api",
    "Doc",
    "Example",
    "Note",
    "Spec",
    "action",
    "api_rows",
    "callout",
    "danger",
    "info",
    "outline",
    "page",
    "run",
    "sections",
    "tip",
    "warn",
]

# ---------------------------------------------------------------------------
# 尺寸与配色：只走角色色，明暗主题自动跟随
# ---------------------------------------------------------------------------
_MAX_W = 960  # 正文最大宽度：再宽一行字就长到读不下去
_GUTTER = 32  # 小窗时的左右留白
_MUTED = ft.Colors.ON_SURFACE_VARIANT
_LINE = ft.Colors.OUTLINE_VARIANT
_MONO = ft.TextStyle(letter_spacing=-0.1)

#: 分类键 → 中文名。文档站有完整的三语导航，这里只服务独立窗口的眉标。
_GROUP_LABEL: dict[str, str] = {
    "general": "通用",
    "layout": "布局",
    "navigation": "导航",
    "form": "表单",
    "feedback": "反馈",
    "display": "展示",
    "charts": "图表",
    "media": "媒体",
    "upload": "文件",
    "core": "核心",
}


# ---------------------------------------------------------------------------
# 数据
# ---------------------------------------------------------------------------
@dataclass(frozen=True, slots=True)
class Api:
    """API 表的一行。

    Args:
        name: 参数 / 属性名。
        type: 类型串（``"int"`` / ``"Callable[[int], None] | None"``）。
        default: 默认值文本；没有默认值留空。
        desc: 一句话说明。
    """

    name: str
    type: str = ""
    default: str = ""
    desc: str = ""


@dataclass(frozen=True, slots=True)
class Example:
    """一个可交互的示例。

    Args:
        title: 示例标题（「基础用法」「受控选页」…）。
        view: 零参工厂，返回真正要展示的控件。用 ``@ft.component`` 函数或普通
            函数都可以 —— 后者每次重绘重建，适合无状态演示。
        hint: 标题下方的一句话说明：这个例子**演示了什么**。
        code: 「查看代码」里的源码。留空则不出现代码开关。
        padded: 舞台是否留 20px 内边距。贴边控件（表格、轮播）传 ``False``。
        height: 固定舞台高度。轮播、滚动列表这类"需要边界"的演示才用。
    """

    title: str
    view: Callable[[], ft.Control]
    hint: str = ""
    code: str = ""
    padded: bool = True
    height: int | None = None


type NoteKind = Literal["tip", "info", "warning", "danger"]


@dataclass(frozen=True, slots=True)
class Note:
    """页尾的一条备注。``kind`` 决定图标与语义色。"""

    kind: NoteKind
    text: str


@dataclass(frozen=True, slots=True)
class Spec:
    """一个组件的完整说明。

    Args:
        name: 组件名，与导入名一致（``"Pagination"``）。
        summary: 一句话定义，出现在标题下方与文档站卡片里。**唯一的必填项**。
        definition: 展开的「定义」：它是什么、解决什么问题。留空则用 ``summary``。
        anatomy: 组件构成 ``[(部件, 作用), ...]``。写的是"看得见的那几块"，
            不是内部类名 —— 读者要能对着截图一一对上。
        when: 什么时候用它。
        avoid: 什么时候**不要**用它（写清替代方案）。
        examples: 示例，按从简到繁排。
        api: 手写的 API 行。留空则从 ``target`` 内省。
        target: 内省对象（组件类 / 表单状态 dataclass）。``api`` 非空时忽略。
        notes: 备注、坑与设计取舍。
        tags: 检索别名（``("分页", "pager")``），进文档站搜索。
        key: 路由键。留空由调用方推断。
        group: 分类键。留空由调用方推断。
        since: 引入版本。
    """

    name: str
    summary: str
    definition: str = ""
    anatomy: tuple[tuple[str, str], ...] = ()
    when: tuple[str, ...] = ()
    avoid: tuple[str, ...] = ()
    examples: tuple[Example, ...] = ()
    #: 手写 API 行；元素可以是 :class:`Api`，也可以直接写 ``(name, type, default, desc)``
    api: tuple[Api | tuple[str, str, str, str], ...] = ()
    target: Any = None
    #: 备注；元素可以是 :class:`Note`、``(kind, text)`` 或一句纯文本
    notes: tuple[Note | tuple[str, str] | str, ...] = ()
    tags: tuple[str, ...] = ()
    key: str = ""
    group: str = ""
    since: str = "0.1.0"
    source: str = field(default="", compare=False)

    # -- 归一：把"没写的"补齐，渲染层就不用到处判空 ------------------------
    def bound(self, *, key: str = "", group: str = "", source: str = "") -> Spec:
        """返回填好 key / group / source 的副本（原对象不可变）。

        顺手把作者写下的 list 归一成 tuple：``Spec`` 是 frozen dataclass，
        把可变容器留在里面迟早有人在渲染期改它。
        """
        return dataclasses.replace(
            self,
            key=self.key or key or _slug(self.name),
            group=self.group or group or "general",
            source=self.source or source,
            anatomy=tuple((part, desc) for part, desc in self.anatomy),
            when=tuple(self.when),
            avoid=tuple(self.avoid),
            examples=tuple(self.examples),
            # 允许把 API 行与备注写成裸元组 / 裸字符串：实现文件里少两个 import，
            # 表格也还能一行写完（``("size", "int", "40", "行高")``）。
            api=tuple(
                row if isinstance(row, Api) else Api(*row) for row in self.api
            ),
            notes=tuple(
                note
                if isinstance(note, Note)
                else (Note("info", note) if isinstance(note, str) else Note(*note))
                for note in self.notes
            ),
            tags=tuple(self.tags),
        )

    @property
    def definition_text(self) -> str:
        return self.definition or self.summary

    @property
    def rows(self) -> tuple[Api, ...]:
        """API 行：手写优先，否则从 :attr:`target` 内省。"""
        if self.api:
            return tuple(
                (row if isinstance(row, Api) else Api(*row)) for row in self.api
            )
        return api_rows(self.target) if self.target is not None else ()

    @property
    def notes_norm(self) -> tuple[Note, ...]:
        """备注归一：``str`` 当 info，``(kind, text)`` 当元组构造。"""
        out: list[Note] = []
        for note in self.notes:
            if isinstance(note, Note):
                out.append(note)
            elif isinstance(note, str):
                out.append(Note("info", note))
            else:
                out.append(Note(*note))  # type: ignore[arg-type]
        return tuple(out)


type Doc = Spec


# ---------------------------------------------------------------------------
# 书写糖
# ---------------------------------------------------------------------------
def tip(text: str) -> Note:
    return Note("tip", text)


def info(text: str) -> Note:
    return Note("info", text)


def warn(text: str) -> Note:
    return Note("warning", text)


def danger(text: str) -> Note:
    return Note("danger", text)


def action(name: str, type: str = "", default: str = "", desc: str = "") -> Api:
    """一行 API。位置参数顺序即表格列序，写起来像表格。"""
    return Api(name, type, default, desc)


def _slug(name: str) -> str:
    """``DateInput`` → ``date_input``（与模块名、路由键一致）。"""
    out: list[str] = []
    for index, char in enumerate(name):
        if char.isupper() and index and not name[index - 1].isupper():
            out.append("_")
        out.append(char.lower())
    return "".join(out)


# ---------------------------------------------------------------------------
# 内省：把构造参数变成 API 表
# ---------------------------------------------------------------------------
#: flet 的基础设施字段：每个控件都有，列在表里只是噪音
_PLUMBING: frozenset[str] = frozenset(
    {
        "key",
        "ref",
        "data",
        "expand",
        "visible",
        "disabled",
        "opacity",
        "tooltip",
        "adaptive",
        "rtl",
        "col",
        "bottom",
        "left",
        "right",
        "top",
        "width",
        "height",
    }
)

_GOOGLE_HEADS = {"args:", "arguments:", "params:", "parameters:"}


def _clean_type(annotation: Any) -> str:
    """注解 → 短串：去掉 ``typing.`` / ``<class '...'>`` / 引号。"""
    if annotation is inspect.Parameter.empty or annotation is inspect.Signature.empty:
        return ""
    text = annotation if isinstance(annotation, str) else getattr(annotation, "__name__", "")
    if not text:
        text = str(annotation)
    for junk in ("typing.", "<class '", "'>", "'", '"'):
        text = text.replace(junk, "")
    text = text.replace("NoneType", "None")
    return " ".join(text.split())


def _clean_default(value: Any) -> str:
    if value is inspect.Parameter.empty or value is dataclasses.MISSING:
        return ""
    if getattr(value, "__class__", None).__name__ in ("_MISSING_TYPE", "Factory"):
        return ""
    text = repr(value)
    if len(text) > 34:
        text = text[:31] + "…"
    return text


def _parse_args(doc: str | None) -> dict[str, str]:
    """从 docstring 里抠出 ``参数 → 说明``。

    两种主流写法都认：

    * Google —— ``Args:`` 段里的 ``name: 说明``，续行按缩进收；
    * NumPy —— ``Parameters`` + ``----------`` 下的 ``name : 类型``，说明在下一行。

    认不出来就返回空表：API 表退化成"只有名字和类型"，也不会报错。
    """
    if not doc:
        return {}

    lines = doc.expandtabs(4).splitlines()
    out: dict[str, str] = {}
    mode: str | None = None
    indent = 0
    name = ""

    def flush(text: list[str]) -> None:
        if name and text:
            out.setdefault(name, " ".join(" ".join(text).split()))

    buffer: list[str] = []
    for index, raw in enumerate(lines):
        stripped = raw.strip()
        pad = len(raw) - len(raw.lstrip())

        if stripped.lower() in _GOOGLE_HEADS:
            flush(buffer)
            buffer, name, mode = [], "", "google"
            continue
        if stripped.lower() == "parameters" and mode is None:
            if index + 1 < len(lines) and set(lines[index + 1].strip()) == {"-"}:
                flush(buffer)
                buffer, name, mode = [], "", "numpy"
            continue
        if set(stripped) == {"-"} and mode == "numpy" and not name:
            continue
        if mode is None:
            continue

        # 段落结束：出现新的顶层小节（Returns / Raises / Notes …）
        if stripped.endswith(":") and pad <= 4 and not stripped.endswith("::"):
            head = stripped[:-1].lower()
            if head in {"returns", "yields", "raises", "notes", "examples", "see also"}:
                flush(buffer)
                buffer, name, mode = [], "", None
                continue

        entry_indent = indent or 4
        if pad <= entry_indent and stripped and ":" in stripped:
            key_part, _, rest = stripped.partition(":")
            candidate = key_part.split("(")[0].split(" ")[0].strip()
            if candidate.isidentifier():
                flush(buffer)
                buffer, name, indent = [], candidate, pad
                rest = rest.strip()
                if mode == "google" and rest and not rest.startswith("..."):
                    buffer = [rest]
                continue
        if name and stripped:
            buffer.append(stripped)

    flush(buffer)
    return out


def api_rows(target: Any) -> tuple[Api, ...]:
    """把组件类 / 表单状态 / 普通函数内省成 API 行。

    * ``@ft.control`` 组件与 ``@ft.observable`` 状态都是 dataclass —— 只看**本类
      自己声明**的字段，继承来的 60 个 flet 属性是噪音；
    * 普通函数看签名，``self`` / ``*args`` / ``**kwargs`` 跳过。

    说明文字来自 docstring 的 ``Args:`` 段；没有就留空，表格照常能用。
    """
    if target is None:
        return ()

    docs = _parse_args(getattr(target, "__doc__", None))
    rows: list[Api] = []

    if dataclasses.is_dataclass(target):
        own = set(getattr(target, "__annotations__", {}))
        for item in dataclasses.fields(target):
            if item.name not in own or item.name in _PLUMBING:
                continue
            if item.name.startswith("_"):
                continue
            default = ""
            if item.default is not dataclasses.MISSING:
                default = _clean_default(item.default)
            elif item.default_factory is not dataclasses.MISSING:  # type: ignore[misc]
                default = "…"
            if item.default is False and "bool" in _clean_type(item.type):
                default = "False"
            rows.append(
                Api(
                    name=item.name,
                    type=_clean_type(item.type),
                    default=default,
                    desc=docs.get(item.name, ""),
                )
            )
        return tuple(rows)

    if callable(target):
        try:
            signature = inspect.signature(target)
        except (TypeError, ValueError):
            return ()
        for name, param in signature.parameters.items():
            if name == "self" or param.kind in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            ):
                continue
            rows.append(
                Api(
                    name=name,
                    type=_clean_type(param.annotation),
                    default=_clean_default(param.default),
                    desc=docs.get(name, ""),
                )
            )
    return tuple(rows)


# ---------------------------------------------------------------------------
# 渲染片段
# ---------------------------------------------------------------------------
def _hairline(*, color: ft.ColorValue = _LINE) -> ft.Control:
    return ft.Container(height=1, bgcolor=color)


def _marker() -> ft.Control:
    """小节标题左侧那枚 3×14 的主色小方块 —— 让标题"挂"在正文上，而不是浮着。"""
    return ft.Container(
        width=3,
        height=15,
        border_radius=2,
        bgcolor=ft.Colors.PRIMARY,
        margin=ft.Margin.only(top=4),
    )


def _section(anchor: str, title: str, body: Sequence[ft.Control]) -> ft.Control:
    return ft.Column(
        key=anchor,
        spacing=14,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        controls=[
            ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    _marker(),
                    ft.Text(title, size=FONT_SIZE["title"], weight=FONT_WEIGHT["bold"]),
                ],
            ),
            *body,
        ],
    )


def _prose(text: str) -> ft.Control:
    return ft.Text(
        text,
        size=14,
        color=ft.Colors.ON_SURFACE,
        style=ft.TextStyle(height=1.85),
    )


def _muted(text: str, *, size: float = 12.5) -> ft.Control:
    return ft.Text(text, size=size, color=_MUTED, style=ft.TextStyle(height=1.65))


# -- 头部 -------------------------------------------------------------------
@ft.component
def header(doc: Spec) -> ft.Control:
    """标题区：分类眉标 + 组件名 + 一句话定义 + 别名。"""
    badges: list[ft.Control] = []
    for tag in doc.tags:
        badges.append(_chip(tag, tone=_MUTED))

    return ft.Column(
        spacing=12,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        controls=[
            ft.Text(
                f"{_GROUP_LABEL.get(doc.group, doc.group)} / {doc.key}",
                size=FONT_SIZE["caption"],
                color=ft.Colors.PRIMARY,
                weight=ft.FontWeight.W_600,
                style=ft.TextStyle(letter_spacing=0.6),
            ),
            ft.Text(
                doc.name,
                size=FONT_SIZE["display_lg"],
                weight=ft.FontWeight.W_800,
                style=ft.TextStyle(letter_spacing=-0.8, height=1.15),
            ),
            ft.Container(
                padding=ft.Padding.only(right=40),
                content=ft.Text(
                    doc.summary,
                    size=FONT_SIZE["title"],
                    color=_MUTED,
                    style=ft.TextStyle(height=1.7),
                ),
            ),
            *(
                [
                    ft.Row(
                        spacing=6,
                        wrap=True,
                        run_spacing=6,
                        controls=badges,
                    )
                ]
                if badges
                else []
            ),
        ],
    )


def _chip(text: str, *, tone: ft.ColorValue | None = None) -> ft.Control:
    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=8, vertical=2),
        border_radius=999,
        bgcolor=ft.Colors.with_opacity(0.07, tone or ft.Colors.PRIMARY),
        content=ft.Text(
            text,
            size=FONT_SIZE["caption"],
            color=tone or ft.Colors.PRIMARY,
            weight=ft.FontWeight.W_600,
        ),
    )


# -- 组件构成 ---------------------------------------------------------------
def _anatomy(doc: Spec) -> ft.Control:
    rows: list[ft.Control] = []
    for index, (part, desc) in enumerate(doc.anatomy, start=1):
        rows.append(
            ft.Row(
                spacing=14,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.Container(
                        width=22,
                        content=ft.Text(
                            f"{index:02d}",
                            size=11,
                            color=ft.Colors.PRIMARY,
                            weight=ft.FontWeight.W_700,
                            style=_MONO,
                        ),
                    ),
                    ft.Container(
                        width=132,
                        content=ft.Text(
                            part,
                            size=FONT_SIZE["body"],
                            weight=ft.FontWeight.W_600,
                            no_wrap=True,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                    ),
                    ft.Container(
                        expand=True,
                        content=ft.Text(
                            desc,
                            size=FONT_SIZE["body"],
                            color=_MUTED,
                            style=ft.TextStyle(height=1.75),
                        ),
                    ),
                ],
            )
        )
    return ft.Container(
        padding=ft.Padding.only(left=2, top=4),
        content=ft.Column(spacing=12, controls=rows),
    )


# -- 何时使用 ---------------------------------------------------------------
def _checklist(
    items: Iterable[str],
    *,
    icon: ft.IconData,
    color: ft.ColorValue,
    title: str,
) -> ft.Control:
    lines = [
        ft.Row(
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                ft.Icon(icon, size=ICON_SIZE["md"], color=color),
                ft.Container(
                    expand=True,
                    content=ft.Text(
                        text,
                        size=FONT_SIZE["body"],
                        color=ft.Colors.ON_SURFACE_VARIANT,
                        style=ft.TextStyle(height=1.7),
                    ),
                ),
            ],
        )
        for text in items
    ]
    return ft.Container(
        expand=True,
        padding=ft.Padding.symmetric(horizontal=16, vertical=14),
        border_radius=12,
        bgcolor=ft.Colors.with_opacity(0.04, color),
        border=ft.Border.all(1, ft.Colors.with_opacity(0.16, color)),
        content=ft.Column(
            spacing=8,
            controls=[
                ft.Text(
                    title,
                    size=12,
                    weight=ft.FontWeight.W_700,
                    color=color,
                    style=ft.TextStyle(letter_spacing=0.3),
                ),
                *lines,
            ],
        ),
    )


def _when(doc: Spec) -> ft.Control:
    cards: list[ft.Control] = []
    if doc.when:
        cards.append(
            _checklist(
                doc.when,
                icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
                color=ft.Colors.PRIMARY,
                title="适合",
            )
        )
    if doc.avoid:
        cards.append(
            _checklist(
                doc.avoid,
                icon=ft.Icons.REMOVE_CIRCLE_OUTLINE,
                color=_MUTED,
                title="不适合",
            )
        )
    return ft.Row(
        spacing=12,
        vertical_alignment=ft.CrossAxisAlignment.START,
        controls=cards,
    )


# -- 代码面板 ---------------------------------------------------------------
@ft.component
def code_panel(source: str, *, filename: str | None = None) -> ft.Control:
    """只读代码面板：深色底、可复制。刻意不跟随明暗主题（"纸与墨"）。"""
    copied, set_copied = ft.use_state(False)
    try:
        import flet_code_editor as fce
    except ImportError:  # pragma: no cover - 可选依赖
        return ft.Container(
            padding=14,
            border_radius=RADIUS["lg"],
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            content=ft.Text(source, size=12, selectable=True),
        )

    longest = max((len(line) for line in source.splitlines()), default=0)
    size = 12.5 if longest <= 72 else (11.6 if longest <= 92 else 10.8)
    height = min(460, (source.count("\n") + 1) * round(size * 1.72) + 14)

    async def copy(_event: ft.Event[ft.IconButton]) -> None:
        """图标换成对勾再换回来。复制本身是客户端 action，不经过后端。"""
        set_copied(True)
        await asyncio.sleep(1.4)
        set_copied(False)

    return ft.Container(
        border_radius=RADIUS["lg"],
        bgcolor=_CODE_BG,
        border=ft.Border.all(1, _CODE_BORDER),
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        content=ft.Column(
            spacing=0,
            controls=[
                ft.Container(
                    padding=ft.Padding.only(left=12, right=4, top=4, bottom=4),
                    bgcolor=_CODE_BG_BAR,
                    border=ft.Border(bottom=ft.BorderSide(1, _CODE_BORDER)),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text(
                                filename or "python",
                                size=FONT_SIZE["caption"],
                                color=ft.Colors.with_opacity(0.6, ft.Colors.WHITE),
                                weight=ft.FontWeight.W_500,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.CHECK_ROUNDED
                                if copied
                                else ft.Icons.CONTENT_COPY,
                                icon_size=ICON_SIZE["sm"],
                                icon_color=(
                                    ft.Colors.GREEN_ACCENT_200
                                    if copied
                                    else ft.Colors.with_opacity(0.55, ft.Colors.WHITE)
                                ),
                                tooltip="已复制" if copied else "复制",
                                padding=5,
                                action=ft.CopyToClipboard(source),
                                on_click=copy,
                            ),
                        ],
                    ),
                ),
                fce.CodeEditor(
                    value=source,
                    language=fce.CodeLanguage.PYTHON,
                    code_theme=fce.CodeTheme.ATOM_ONE_DARK,
                    read_only=True,
                    height=height,
                    text_style=ft.TextStyle(size=size, height=1.55),
                ),
            ],
        ),
    )


# -- 示例卡 -----------------------------------------------------------------
@ft.component
def _example_card(item: Example) -> ft.Control:
    show_code, set_show_code = ft.use_state(False)

    head: list[ft.Control] = [
        ft.Column(
            expand=True,
            spacing=4,
            controls=[
                ft.Text(item.title, size=FONT_SIZE["body"], weight=ft.FontWeight.W_700),
                *([_muted(item.hint)] if item.hint else []),
            ],
        )
    ]
    if item.code:
        head.append(
            _toggle(
                ft.Icons.CODE,
                "代码" if not show_code else "收起",
                active=show_code,
                on_click=lambda _e: set_show_code(not show_code),
            )
        )

    stage = ft.Container(
        padding=ft.Padding.all(20) if item.padded else None,
        height=item.height,
        content=item.view(),
    )

    return ft.Container(
        border_radius=12,
        bgcolor=ft.Colors.SURFACE,
        border=ft.Border.all(1, _LINE),
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        content=ft.Column(
            spacing=0,
            controls=[
                ft.Container(
                    padding=ft.Padding.only(left=16, right=10, top=8, bottom=8),
                    content=ft.Row(
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=head,
                    ),
                ),
                _hairline(),
                stage,
                *(
                    [
                        _hairline(),
                        ft.Container(
                            padding=ft.Padding.all(12),
                            content=code_panel(item.code, filename=f"{item.title}"),
                        ),
                    ]
                    if show_code and item.code
                    else []
                ),
            ],
        ),
    )


def _toggle(
    icon: ft.IconData, label: str, *, active: bool, on_click: Callable
) -> ft.Control:
    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=8, vertical=4),
        border_radius=RADIUS["md"],
        bgcolor=ft.Colors.SURFACE_CONTAINER_LOW if active else None,
        border=ft.Border.all(1, _LINE if active else ft.Colors.TRANSPARENT),
        ink=True,
        on_click=on_click,
        content=ft.Row(
            spacing=4,
            tight=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(icon, size=ICON_SIZE["sm"], color=ft.Colors.ON_SURFACE if active else _MUTED),
                ft.Text(
                    label,
                    size=FONT_SIZE["caption"],
                    color=ft.Colors.ON_SURFACE if active else _MUTED,
                    weight=ft.FontWeight.W_600 if active else None,
                ),
            ],
        ),
    )


# -- API 表 -----------------------------------------------------------------
_COLS: tuple[tuple[str, int | None], ...] = (
    ("参数", 176),
    ("类型", 168),
    ("默认", 108),
)


def _api_row(cells: Sequence[ft.Control], *, head: bool = False) -> ft.Control:
    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=14, vertical=10 if not head else 8),
        bgcolor=ft.Colors.SURFACE_CONTAINER_LOW if head else None,
        content=ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=list(cells),
        ),
    )


def _cell(text: str, width: int | None, *, mono: bool = False, muted: bool = False) -> ft.Control:
    control = ft.Text(
        text,
        size=FONT_SIZE["small"],
        color=_MUTED if muted else ft.Colors.ON_SURFACE,
        no_wrap=True,
        overflow=ft.TextOverflow.ELLIPSIS,
        style=_MONO if mono else None,
    )
    if width is None:
        return ft.Container(expand=True, content=control)
    return ft.Container(width=width, content=control)


def _api_table(rows: Sequence[Api]) -> ft.Control:
    body: list[ft.Control] = [
        _api_row(
            [
                *(
                    _cell(label, width)
                    for label, width in _COLS
                ),
                _cell("说明", None),
            ],
            head=True,
        )
    ]
    for item in rows:
        body.append(
            _api_row(
                [
                    _cell(item.name, _COLS[0][1], mono=True),
                    _cell(item.type or "—", _COLS[1][1], muted=True),
                    _cell(item.default or "—", _COLS[2][1], muted=True),
                    ft.Container(
                        expand=True,
                        content=ft.Text(
                            item.desc or "—",
                            size=FONT_SIZE["small"],
                            color=ft.Colors.ON_SURFACE_VARIANT if item.desc else _MUTED,
                            style=ft.TextStyle(height=1.6),
                        ),
                    ),
                ]
            )
        )
    return ft.Container(
        border_radius=12,
        border=ft.Border.all(1, _LINE),
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        content=ft.Column(spacing=0, controls=body),
    )


# -- 备注 -------------------------------------------------------------------
#: 备注的图标是固定的，颜色却有两种来源，必须分开：
#:
#: * ``tip`` / ``info`` / ``danger`` 用 M3 的**主题角色**（``PRIMARY`` /
#:   ``ON_SURFACE_VARIANT`` / ``ERROR``），交给 Flutter 按当前色板解析；
#: * ``warning`` 在 M3 里**没有对应角色**，只能用框架的语义色，而语义色是
#:   具体十六进制值、随明暗切换 —— 所以它**不能在导入期求值**。
#:
#: 曾经把 ``"#B26A00"`` 直接写进这张表：字典在 import 时就固化了，切到深色
#: 主题后这行备注仍然是浅色的深琥珀，对比度掉到 2:1 出头。
_NOTE_ICON: dict[str, ft.IconData] = {
    "tip": ft.Icons.LIGHTBULB_OUTLINE_ROUNDED,
    "info": ft.Icons.INFO_OUTLINE_ROUNDED,
    "warning": ft.Icons.WARNING_AMBER_ROUNDED,
    "danger": ft.Icons.ERROR_OUTLINE_ROUNDED,
}

_NOTE_ROLE: dict[str, ft.ColorValue] = {
    "tip": ft.Colors.PRIMARY,
    "info": ft.Colors.ON_SURFACE_VARIANT,
    "danger": ft.Colors.ERROR,
}


def _note_color(kind: str) -> ft.ColorValue:
    """渲染期取备注颜色（``warning`` 走语义色，其余走主题角色）。"""
    if kind == "warning":
        return semantic_text("warning")
    return _NOTE_ROLE.get(kind, ft.Colors.ON_SURFACE_VARIANT)


def callout(note: Note) -> ft.Control:
    kind = note.kind if note.kind in _NOTE_ICON else "info"
    icon = _NOTE_ICON[kind]
    color = _note_color(kind)
    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=14, vertical=12),
        border_radius=RADIUS["lg"],
        bgcolor=ft.Colors.with_opacity(0.05, color),
        border=ft.Border(
            left=ft.BorderSide(3, color),
            top=ft.BorderSide(1, ft.Colors.with_opacity(0.12, color)),
            right=ft.BorderSide(1, ft.Colors.with_opacity(0.12, color)),
            bottom=ft.BorderSide(1, ft.Colors.with_opacity(0.12, color)),
        ),
        content=ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                ft.Icon(icon, size=16, color=color, margin=ft.Margin.only(top=1)),
                ft.Container(
                    expand=True,
                    content=ft.Text(
                        note.text,
                        size=FONT_SIZE["small"],
                        color=ft.Colors.ON_SURFACE_VARIANT,
                        style=ft.TextStyle(height=1.7),
                    ),
                ),
            ],
        ),
    )


# ---------------------------------------------------------------------------
# 页面装配
# ---------------------------------------------------------------------------
_TITLES = {
    "definition": "定义",
    "anatomy": "组件构成",
    "when": "何时使用",
    "examples": "示例",
    "api": "API",
    "notes": "备注",
}


def outline(doc: Spec) -> tuple[tuple[str, str], ...]:
    """本页锚点 ``(anchor, 标题)`` —— 文档站右侧"本页内容"用它。"""
    found: list[tuple[str, str]] = [("definition", _TITLES["definition"])]
    if doc.anatomy:
        found.append(("anatomy", _TITLES["anatomy"]))
    if doc.when or doc.avoid:
        found.append(("when", _TITLES["when"]))
    if doc.examples:
        found.append(("examples", _TITLES["examples"]))
    if doc.rows:
        found.append(("api", _TITLES["api"]))
    if doc.notes:
        found.append(("notes", _TITLES["notes"]))
    return tuple(found)


def sections(doc: Spec) -> list[ft.Control]:
    """从「定义」到「备注」的全部分节（文档站复用这一段，标题自己出）。"""
    doc = doc.bound()
    out: list[ft.Control] = [
        _section("definition", _TITLES["definition"], [_prose(doc.definition_text)])
    ]
    if doc.anatomy:
        out.append(_section("anatomy", _TITLES["anatomy"], [_anatomy(doc)]))
    if doc.when or doc.avoid:
        out.append(_section("when", _TITLES["when"], [_when(doc)]))
    if doc.examples:
        out.append(
            _section(
                "examples",
                _TITLES["examples"],
                [
                    ft.Column(
                        spacing=12,
                        controls=[_example_card(item) for item in doc.examples],
                    )
                ],
            )
        )
    rows = doc.rows
    if rows:
        out.append(_section("api", _TITLES["api"], [_api_table(rows)]))
    notes = doc.notes_norm
    if notes:
        out.append(
            _section(
                "notes",
                _TITLES["notes"],
                [callout(note) for note in notes],
            )
        )
    return out


def _footer(doc: Spec) -> ft.Control:
    return ft.Container(
        margin=ft.Margin.only(top=8),
        padding=ft.Padding.only(top=14),
        border=ft.Border(top=ft.BorderSide(1, _LINE)),
        content=ft.Row(
            spacing=8,
            wrap=True,
            run_spacing=6,
            controls=[
                ft.Icon(ft.Icons.TERMINAL, size=ICON_SIZE["sm"], color=_MUTED),
                ft.Text(
                    "直接运行本文件即可看到这一页",
                    size=FONT_SIZE["caption"],
                    color=_MUTED,
                ),
                *(
                    [
                        ft.Text("·", size=FONT_SIZE["caption"], color=_MUTED),
                        ft.Text(
                            doc.source,
                            size=FONT_SIZE["caption"],
                            color=_MUTED,
                            style=_MONO,
                            selectable=True,
                        ),
                    ]
                    if doc.source
                    else []
                ),
            ],
        ),
    )


@ft.component
def page(doc: Spec) -> ft.Control:
    """整页：标题 + 分节 + 页脚（独立窗口用）。"""
    return ft.Column(
        spacing=30,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        controls=[
            header(doc),
            *sections(doc),
            _footer(doc),
        ],
    )


# ---------------------------------------------------------------------------
# 独立运行
# ---------------------------------------------------------------------------
def _caller_globals(depth: int = 3) -> dict[str, Any]:
    try:
        return sys._getframe(depth).f_globals
    except ValueError:  # pragma: no cover - 极深的调用栈
        return {}


def _derive(module_globals: dict[str, Any]) -> tuple[str, str, str]:
    """从调用方文件路径推出 ``(key, group, 源码路径)``。

    路径即约定：``src/ui/navigation/pagination.py`` → ``pagination`` / ``navigation``。
    这样每个实现文件都不用重复声明自己在哪一组 —— 挪文件时自动跟着走。
    """
    raw = module_globals.get("__file__")
    if not raw:
        return "", "", ""
    path = Path(str(raw)).resolve()
    parts = path.parts
    group = ""
    source = ""
    if "ui" in parts:
        index = len(parts) - 1 - parts[::-1].index("ui")
        tail = parts[index + 1 :]
        if len(tail) >= 2:
            group = tail[-2]
        source = "/".join(("src", "ui", *tail))
    return path.stem, group, source


@ft.component
def _host(docs: tuple[Spec, ...]) -> ft.Control:
    """独立窗口的骨架：顶栏（分类 + 明暗切换）+ 居中正文。

    一个文件里写了多个组件（``display/text.py`` 就同时是 Text / Heading /
    Quote …）时，顶栏下面多一排名字，就地切换 —— 跑一次脚本能看完全家。
    """
    from ui.core.theme import use_theme

    theme = use_theme()
    dark = theme.is_dark
    current, set_current = ft.use_state(0)
    doc = docs[min(current, len(docs) - 1)]

    top = ft.Container(
        height=52,
        padding=ft.Padding.symmetric(horizontal=20),
        border=ft.Border(bottom=ft.BorderSide(1, _LINE)),
        bgcolor=ft.Colors.SURFACE,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(
                            width=6,
                            height=6,
                            border_radius=RADIUS["full"],
                            bgcolor=ft.Colors.PRIMARY,
                        ),
                        ft.Text("cs-ui", size=FONT_SIZE["body"], weight=ft.FontWeight.W_800),
                        ft.Text(
                            f"{_GROUP_LABEL.get(doc.group, doc.group)} · {doc.name}",
                            size=FONT_SIZE["small"],
                            color=_MUTED,
                        ),
                    ],
                ),
                ft.Row(
                    spacing=2,
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.LIGHT_MODE_OUTLINED
                            if dark
                            else ft.Icons.DARK_MODE_OUTLINED,
                            icon_size=18,
                            icon_color=_MUTED,
                            tooltip="切到浅色" if dark else "切到深色",
                            on_click=lambda _e: theme.toggle_mode(),
                        )
                    ],
                ),
            ],
        ),
    )

    switcher = (
        ft.Container(
            padding=ft.Padding.only(left=_GUTTER, right=_GUTTER, top=14),
            content=ft.Row(
                spacing=6,
                wrap=True,
                run_spacing=6,
                controls=[
                    ft.Container(
                        padding=ft.Padding.symmetric(horizontal=12, vertical=4),
                        border_radius=999,
                        bgcolor=(
                            ft.Colors.PRIMARY if index == current else ft.Colors.SURFACE
                        ),
                        border=ft.Border.all(
                            1, ft.Colors.PRIMARY if index == current else _LINE
                        ),
                        on_click=lambda _e, _i=index: set_current(_i),
                        content=ft.Text(
                            item.name,
                            size=12,
                            weight=ft.FontWeight.W_600,
                            color=(
                                ft.Colors.ON_PRIMARY
                                if index == current
                                else ft.Colors.ON_SURFACE_VARIANT
                            ),
                        ),
                    )
                    for index, item in enumerate(docs)
                ],
            ),
        )
        if len(docs) > 1
        else None
    )

    return ft.Container(
        expand=True,
        bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
        content=ft.Column(
            expand=True,
            spacing=0,
            controls=[
                top,
                *([switcher] if switcher is not None else []),
                ft.Container(
                    expand=True,
                    padding=ft.Padding.symmetric(horizontal=_GUTTER, vertical=34),
                    content=ft.Column(
                        expand=True,
                        scroll=ft.ScrollMode.AUTO,
                        controls=[
                            # 用 Row 居中而不是给 Column 设 CENTER：可滚动的 Column
                            # 在 Flutter 侧是 ListView，子项会被拉满整行宽度，
                            # 正文就失去「最大 960」这道约束了。
                            ft.Row(
                                alignment=ft.MainAxisAlignment.CENTER,
                                vertical_alignment=ft.CrossAxisAlignment.START,
                                controls=[
                                    ft.Container(width=_MAX_W, content=page(doc))
                                ],
                            )
                        ],
                    ),
                ),
            ],
        ),
    )


def _font() -> Path | None:
    path = Path(__file__).resolve().parents[1] / "data" / "fonts" / (
        "AlibabaPuHuiTi-3-55-Regular.otf"
    )
    return path if path.exists() else None


def run(
    *docs: Spec,
    dark: bool = False,
    width: int = 1120,
    height: int = 900,
) -> None:
    """把一份（或一个文件里的多份）:class:`Spec` 跑成独立窗口。

    ``group`` / ``key`` / ``source`` 由调用方文件路径补全；主题、字体、窗口尺寸
    都在这里定一次，实现文件里不必重复。传多份时窗口顶部多一排名字可切换 ——
    ``display/text.py`` 这类「一个文件多个组件」的模块用得上。

    Args:
        docs: 组件说明。多于一份时按 ``Spec.name`` 生成切换条。
        dark: 首帧就用深色（默认跟随浅色）。
        width: 初始窗口宽。
        height: 初始窗口高。
    """
    from ui.core.theme import theme_state

    if not docs:
        raise ValueError("run() 至少要一份 Spec")

    key, group, source = _derive(_caller_globals(2))
    # 单份时用文件名当 key（路径即约定）；多份时各自按类名推导，否则全撞一个键。
    single = len(docs) == 1
    specs = tuple(
        doc.bound(key=key if single else "", group=group, source=source) for doc in docs
    )
    font = _font()

    def boot(target: ft.Page) -> None:
        target.title = (
            f"{specs[0].name} · cs-ui"
            if single
            else f"{' / '.join(item.name for item in specs)} · cs-ui"
        )
        target.padding = 0
        target.window.width = width
        target.window.height = height
        target.window.min_width = 720
        target.window.min_height = 560
        if font is not None:
            # 字体与 ThemeState 必须指向同一个族名，否则首帧与重绘之间会来回跳。
            target.fonts = {"AlibabaPuHuiTi": str(font)}
            theme_state().font_family = "AlibabaPuHuiTi"
        if dark:
            theme_state().set_mode("dark")
        target.render(_app(specs))

    ft.run(boot)


def _app(specs: tuple[Spec, ...]) -> Callable[[], ft.Control]:
    """组装 「I18n → Theme → 页面」三层 Provider。

    顺序不能反：语言的默认文案要在首帧就位，主题其次（否则切换时会闪一帧旧配色）。
    """
    from ui.core.i18n import I18nProvider
    from ui.core.theme import ThemeProvider

    @ft.component
    def body() -> ft.Control:
        return _host(specs)

    @ft.component
    def themed() -> ft.Control:
        return ThemeProvider(build=body)

    @ft.component
    def app() -> ft.Control:
        return I18nProvider(locale="zh-CN", detect=False, build=themed)

    return app
