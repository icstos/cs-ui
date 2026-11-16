"""行内搜索输入框 (SearchField) —— 圆角填底、聚焦换色、紧凑行高。

和 :class:`ui.SearchBar` 不是一回事：``SearchBar`` 打开的是 Flutter 的**搜索视图**
（盖在页面上的一层路由），适合全局搜索、命令面板；``SearchField`` 是一个能塞进
侧栏、工具栏、表格上方甚至 30px 高过滤条的普通输入框。

设计约定（来自 cs-markdown-editor 的实机经验，别改坏这三条）
------------------------------------------------------------
1. **单一着色来源**：底色、1px 描边、圆角、聚焦环都由外壳 ``Container`` 给；
   内层 ``TextField`` 必须 ``filled=False`` + ``NoInputBorder()``。让 Material
   自己画描边，会和外层圆角差半圈，浅色底上尤其明显。
2. **行首内缩由外壳统一给**：``filled=True`` 会自带约 4 逻辑 px 的 Material
   内缩，两条输入框并排时文字对不齐。
3. **聚焦三件套同时变**：底色提亮、描边换强调色、图标换强调色，再加一圈
   ``focus_ring``（实心外扩，不用模糊光晕）。只换描边在浅色面板里读不出来。

``SearchField`` 是 ``@ft.component`` 函数组件：聚焦态用 ``use_state`` 管理，
所以构造后直接放进控件树即可，不需要 ``.ui()``。

用法::

    query, set_query = ft.use_state("")
    SearchField(value=query, on_change=set_query, placeholder="在文件夹中查找…")
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import flet as ft

from ui.core.doc import Api, Example, Spec, info, run, tip, warn
from ui.core.tokens import FONT_SIZE, RADIUS, SPACE, focus_ring

__all__ = ["SearchField", "SearchFieldPalette"]


@dataclass(frozen=True, slots=True)
class SearchFieldPalette:
    """一套配色，六个性格。

    默认全部走 M3 角色色（主题感知，切明暗零重渲染）。应用若已有自己的
    设计令牌，整套覆盖即可，不必改组件、也不会丢聚焦态的语义。
    """

    fill: str = ft.Colors.SURFACE_CONTAINER_LOW
    focused_fill: str = ft.Colors.SURFACE
    border: str = ft.Colors.OUTLINE_VARIANT
    accent: str = ft.Colors.PRIMARY
    text: str = ft.Colors.ON_SURFACE
    hint: str = ft.Colors.ON_SURFACE_VARIANT


@ft.component
def SearchField(
    value: str = "",
    *,
    on_change: Callable[[str], None] | None = None,
    on_submit: Callable[[], None] | None = None,
    on_focus: Callable[[ft.ControlEvent], None] | None = None,
    on_blur: Callable[[ft.ControlEvent], None] | None = None,
    placeholder: str = "搜索",
    icon: str | None = ft.Icons.SEARCH,
    height: int = 30,
    radius: float = RADIUS["md"],
    palette: SearchFieldPalette | None = None,
    field_ref: ft.Ref | None = None,
    focus_shadow: list[ft.BoxShadow] | None = None,
    padding: ft.Padding | None = None,
    content_padding: ft.Padding | None = None,
    text_size: float = FONT_SIZE["small"],
    icon_size: float = 14,
    gap: float = SPACE["2"],
    font_family: str | None = None,
    width: float | None = None,
) -> ft.Control:
    """行内搜索/过滤输入框。

    Args:
        value: 当前文本（受控）。
        on_change: 文本变化，收到纯字符串，不用自己拆事件。
        on_submit: 回车提交，无参数。
        on_focus / on_blur: 焦点进出；除了驱动聚焦态，也原样转给外部回调。
        placeholder: 占位文案。
        icon: 左侧图标；``None`` 表示不要（替换框放放大镜会误导成「再搜一次」）。
        height: 外壳高度。同一面板里的搜索框与替换框给同一个值才对得齐。
        palette: 六色配色；``None`` 走 M3 角色色。
        field_ref: 外部持有输入框引用，供快捷键把光标送进来。
        focus_shadow: 聚焦环；默认用 ``ui.core.tokens.focus_ring`` 生成。
        padding: 外壳内边距；``None`` 取 4px 网格上的标准横向留白。
        content_padding: ``TextField`` 的内边距；默认只给上下，横向交给外壳。
        text_size / icon_size / gap: 紧凑尺寸，默认按 4px 网格排。
        font_family: 字体族；``None`` 跟随页面主题。
    """
    focused, set_focused = ft.use_state(False)
    p = palette or SearchFieldPalette()

    def _focus(e=None) -> None:
        set_focused(True)
        if on_focus is not None:
            on_focus(e)

    def _blur(e=None) -> None:
        set_focused(False)
        if on_blur is not None:
            on_blur(e)

    field = ft.TextField(
        value=value,
        hint_text=placeholder,
        hint_style=ft.TextStyle(size=text_size, color=p.hint, font_family=font_family),
        dense=True,
        border=ft.NoInputBorder(),
        filled=False,
        text_size=text_size,
        text_style=ft.TextStyle(size=text_size, color=p.text, font_family=font_family),
        content_padding=content_padding
        or ft.Padding.symmetric(horizontal=0, vertical=SPACE["1"]),
        cursor_color=p.accent,
        on_change=(lambda e: on_change(e.control.value or "")) if on_change else None,
        on_focus=_focus,
        on_blur=_blur,
        on_submit=(lambda e: on_submit()) if on_submit else None,
        ref=field_ref,
        expand=True,
    )

    controls: list[ft.Control] = []
    if icon is not None:
        controls.append(ft.Icon(icon, size=icon_size, color=p.accent if focused else p.hint))
    controls.append(field)

    return ft.Container(
        width=width,
        height=height,
        bgcolor=p.focused_fill if focused else p.fill,
        border=ft.Border.all(1, p.accent if focused else p.border),
        border_radius=radius,
        padding=padding or ft.Padding.symmetric(horizontal=SPACE["3"]),
        shadow=(focus_shadow if focus_shadow is not None else [focus_ring(p.accent)])
        if focused
        else None,
        alignment=ft.Alignment.CENTER_LEFT,
        content=ft.Row(
            controls=controls,
            spacing=gap,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )


# ---------------------------------------------------------------------------
# 文档演示
# ---------------------------------------------------------------------------
@ft.component
def _basic() -> ft.Control:
    query, set_query = ft.use_state("")
    return ft.Column(
        spacing=SPACE["3"],
        controls=[
            SearchField(value=query, on_change=set_query, placeholder="在文档中查找…"),
            ft.Text(f"当前：{query or '（空）'}", size=FONT_SIZE["small"]),
        ],
    )


@ft.component
def _palette_demo() -> ft.Control:
    own = SearchFieldPalette(
        fill=ft.Colors.SECONDARY_CONTAINER,
        focused_fill=ft.Colors.SURFACE,
        border=ft.Colors.OUTLINE,
        accent=ft.Colors.TERTIARY,
        text=ft.Colors.ON_SECONDARY_CONTAINER,
        hint=ft.Colors.ON_SURFACE_VARIANT,
    )
    return ft.Column(
        spacing=SPACE["3"],
        controls=[
            SearchField(placeholder="整套换成自己的色板", palette=own),
            SearchField(placeholder="不要放大镜，用作替换框", icon=None),
        ],
    )


_BASIC_CODE = '''\
query, set_query = ft.use_state("")

SearchField(
    value=query,
    on_change=set_query,
    placeholder="在文档中查找…",
)
'''

SPEC = Spec(
    name="SearchField",
    summary="行内搜索/过滤输入框：圆角填底，聚焦时底色、描边、图标一起换强调色。",
    definition=(
        "搜索框要解决两件事：让用户在密集的界面里一眼认出哪里能输入，以及输入时"
        "明确知道焦点在哪。SearchField 把两者交给同一层外壳 Container：填底加 1px "
        "描边负责「认得出」，聚焦时的三件套换色负责「在哪儿」。它是普通控件，"
        "能放进 30px 高的工具栏，不像 SearchBar 那样展开一层覆盖全页的搜索视图。"
    ),
    anatomy=[
        ("外壳 Container", "底色、1px 描边、圆角、聚焦环的唯一着色来源。"),
        ("前置图标", "可选；聚焦时从弱化色切到强调色，替换框可传 icon=None。"),
        ("内层 TextField", "filled=False + NoInputBorder，只负责文字，不画自己的框。"),
        ("focus_ring", "实心外扩 1.5~2px 的描边环，比模糊光晕更清晰。"),
    ],
    when=[
        "侧栏、工具栏、表格上方需要一条常驻的过滤/搜索输入框",
        "同一面板里并排放两条输入（搜索 + 替换），要求文字起点与行高完全对齐",
        "应用已有自己的设计令牌，需要一个能整套换色但不改结构的输入框",
    ],
    avoid=[
        "要做全局搜索 / 命令面板，且需要候选列表浮层：用 SearchBar",
        "多行文本、带校验的表单字段：用 Input",
        "窄到放不下占位文案的格子：优先缩短文案，别把 height 压到文字行高以下",
    ],
    examples=[
        Example(
            "基础用法",
            _basic,
            hint="受控 value + on_change；输入时下面一行同步显示当前文本。",
            code=_BASIC_CODE,
        ),
        Example(
            "换色板 / 去图标",
            _palette_demo,
            hint="上面一条整套换成自己的六色；下面一条去掉放大镜，用作替换框。",
        ),
    ],
    api=[
        Api("value", "str", "''", "受控文本"),
        Api("on_change", "Callable[[str], None] | None", "None", "文本变化，收到纯字符串"),
        Api("on_submit", "Callable[[], None] | None", "None", "回车提交"),
        Api("on_focus / on_blur", "Callable | None", "None", "焦点进出，原样转给外部"),
        Api("placeholder", "str", "'搜索'", "占位文案"),
        Api("icon", "str | None", "ft.Icons.SEARCH", "左侧图标；None 不显示"),
        Api("height", "int", "30", "外壳高度"),
        Api("radius", "float", "RADIUS['md']", "圆角"),
        Api("palette", "SearchFieldPalette | None", "None", "六色配色；None 走 M3 角色色"),
        Api("field_ref", "ft.Ref | None", "None", "输入框引用，供快捷键聚焦"),
        Api("focus_shadow", "list[BoxShadow] | None", "None", "聚焦环；None 用 tokens.focus_ring"),
        Api("padding", "ft.Padding | None", "None", "外壳内边距"),
        Api("content_padding", "ft.Padding | None", "None", "TextField 内边距"),
        Api("text_size / icon_size / gap", "float", "12 / 14 / 8", "紧凑尺寸"),
        Api("font_family", "str | None", "None", "字体族；None 跟随主题"),
    ],
    notes=[
        tip(
            "底色与描边只给外壳。若把 TextField 设成 filled=True，Material 会自带约 "
            "4 逻辑 px 的行首内缩，并画一圈和外层圆角对不上的描边。"
        ),
        info(
            "SearchFieldPalette 是 frozen dataclass：改配色就换一个新实例，不要在回调里"
            "改字段 —— 渲染出来的控件是冻结的，赋值不会上屏。"
        ),
        warn(
            "聚焦环默认是实心外扩（spread_radius），不是模糊阴影。模糊光晕在浅色面板上"
            "会糊成一团灰，读起来像脏了而不是聚焦了。"
        ),
    ],
    tags=("搜索", "搜索框", "过滤", "输入框", "search", "filter", "input"),
)


if __name__ == "__main__":
    run(SPEC)
