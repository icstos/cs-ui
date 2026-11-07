"""容器 (Container) —— 一块能自己定留白、底色、描边与对齐的基础盒子。

它只管「这一块」的盒子模型：占地多大、里面留多少白、底色和边什么样、唯一的
内容摆在盒内哪个位置。子项怎么排列不归它管 —— 那是 :class:`flet.Row` /
:class:`flet.Column` / :class:`flet.Stack` 的事。

用法::

    Container(
        padding=16,                       # 盒内留白
        bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        border_radius=8,
        content=Text("今日新增 128 条"),
    )
"""

from __future__ import annotations

import flet as ft

from ui.core.doc import Api, Example, Spec, info, run, tip, warn
from ui.core.tokens import FONT_SIZE, RADIUS, SPACE

__all__ = ["Container"]

_MUTED = ft.Colors.ON_SURFACE_VARIANT
_LINE = ft.Colors.OUTLINE_VARIANT


@ft.control
class Container(ft.Container):
    """通用盒子：留白、底色、边框、圆角、对齐、点击都在同一个控件上给。

    需要阴影 + 卡片语义时改用 :class:`ui.layout.card.Card`；需要排列多个子项时
    改用 ``Row`` / ``Column``。
    """


# ---------------------------------------------------------------------------
# 示例零件
# ---------------------------------------------------------------------------
def _caption(text: str) -> ft.Control:
    return ft.Text(text, size=FONT_SIZE["small"], color=_MUTED)


def _label(text: str) -> ft.Control:
    return ft.Text(text, size=FONT_SIZE["body"], color=ft.Colors.ON_PRIMARY_CONTAINER)


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
_PADDINGS = (SPACE["2"], SPACE["4"], SPACE["6"])


@ft.component
def _padding() -> ft.Control:
    """同一块 190×110 的盒子，只改 padding：里面那块主色区域就是「内容能用的地方」。"""
    boxes: list[ft.Control] = []
    for pad in _PADDINGS:
        boxes.append(
            ft.Column(
                spacing=SPACE["2"],
                controls=[
                    _caption(f"padding = {pad}"),
                    ft.Container(
                        width=190,
                        height=110,
                        padding=pad,
                        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                        border_radius=RADIUS["md"],
                        content=ft.Container(
                            alignment=ft.Alignment.CENTER,
                            bgcolor=ft.Colors.PRIMARY_CONTAINER,
                            border_radius=RADIUS["xs"],
                            content=_label(f"{pad}"),
                        ),
                    ),
                ],
            )
        )

    return ft.Column(
        spacing=SPACE["3"],
        controls=[
            ft.Row(spacing=SPACE["4"], controls=boxes),
            _caption(
                "外框尺寸不变，内边距越大可用面积越小。8 用于紧凑的行内块，"
                "16 是面板默认，24 只给需要「喘气」的独立区块。"
            ),
        ],
    )


@ft.component
def _surface() -> ft.Control:
    """底色、圆角、描边是三个独立开关：只给底色最轻，加描边最明确。"""
    tiles: list[ft.Control] = [
        Container(
            width=172,
            height=84,
            padding=SPACE["3"],
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            content=ft.Text("底色", size=FONT_SIZE["body"]),
        ),
        Container(
            width=172,
            height=84,
            padding=SPACE["3"],
            bgcolor=ft.Colors.PRIMARY_CONTAINER,
            border_radius=RADIUS["lg"],
            content=ft.Text(
                "底色 + 圆角",
                size=FONT_SIZE["body"],
                color=ft.Colors.ON_PRIMARY_CONTAINER,
            ),
        ),
        Container(
            width=172,
            height=84,
            padding=SPACE["3"],
            border=ft.Border.all(1, _LINE),
            border_radius=RADIUS["sm"],
            content=ft.Text("只描边", size=FONT_SIZE["body"]),
        ),
        Container(
            width=172,
            height=84,
            padding=SPACE["3"],
            bgcolor=ft.Colors.SECONDARY_CONTAINER,
            border=ft.Border.all(1, ft.Colors.SECONDARY),
            border_radius=RADIUS["xl"],
            content=ft.Text(
                "描边 + 大圆角",
                size=FONT_SIZE["body"],
                color=ft.Colors.ON_SECONDARY_CONTAINER,
            ),
        ),
    ]
    return ft.Column(
        spacing=SPACE["3"],
        controls=[
            ft.Row(spacing=SPACE["3"], controls=tiles),
            _caption(
                "底色用角色色（SURFACE_CONTAINER_* / PRIMARY_CONTAINER），不要写十六进制 —— "
                "同一个值在深色主题下会失去对比。"
            ),
        ],
    )


@ft.component
def _aligned() -> ft.Control:
    """alignment 摆的是盒内的内容；盒子本身在页面里居中，靠外层 Column。"""

    def box(align: ft.Alignment, text: str) -> ft.Control:
        return Container(
            width=280,
            height=120,
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border=ft.Border.all(1, _LINE),
            border_radius=RADIUS["md"],
            alignment=align,
            content=ft.Text(text, size=FONT_SIZE["body"], color=_MUTED),
        )

    return ft.Column(
        spacing=SPACE["4"],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Row(
                spacing=SPACE["4"],
                controls=[
                    box(ft.Alignment.CENTER, "alignment = CENTER"),
                    box(ft.Alignment.TOP_LEFT, "alignment = TOP_LEFT"),
                ],
            ),
            Container(
                width=340,
                padding=SPACE["4"],
                bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
                border=ft.Border.all(1, _LINE),
                border_radius=RADIUS["lg"],
                content=ft.Column(
                    spacing=SPACE["1"],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text("固定宽 340", size=FONT_SIZE["title"]),
                        _caption("由外层 Column 的 horizontal_alignment 居中"),
                    ],
                ),
            ),
        ],
    )


_PADDING_CODE = """Row(
    spacing=16,
    controls=[
        Container(
            width=190,
            height=110,
            padding=8,                          # 留白：内容可用面积随之变小
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
            border_radius=6,
            content=Container(bgcolor=ft.Colors.PRIMARY_CONTAINER),
        ),
        # padding=16 / 24 同上
    ],
)"""

_SURFACE_CODE = """Container(
    padding=12,
    bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,     # 角色色，跟随明暗主题
    border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
    border_radius=8,
    content=Text("今日新增 128 条"),
)"""

_ALIGN_CODE = """Column(
    horizontal_alignment=ft.CrossAxisAlignment.CENTER,   # 让固定宽的盒子居中
    controls=[
        Container(
            width=340,
            padding=16,
            alignment=ft.Alignment.CENTER,               # 让盒内内容居中
            content=Text("两块都居中，但管的是不同的事"),
        ),
    ],
)"""


SPEC = Spec(
    name="Container",
    summary="一块能自定留白、底色、描边和对齐的基础盒子。",
    definition=(
        "Container 是布局的地基：宽高、内边距、外边距、背景、圆角、描边、对齐、点击，"
        "全都能在同一个控件上给。它不排列子项 —— 只处理「这一块」自身的盒子模型，"
        "子项怎么排交给 Row / Column / Stack。也正因为什么都能塞，它最容易被当成"
        "万能胶：明明给父级 spacing 就能解决的 8px，不该再套一层带 padding 的盒子。"
    ),
    anatomy=[
        (
            "盒子",
            "width / height 定占地，padding 定内部留白，margin 定与邻居的距离 —— 三者不是一回事。",
        ),
        (
            "外观",
            "bgcolor / border / border_radius 决定这块区域长什么样，全部走主题角色色。",
        ),
        (
            "对齐",
            "alignment 把唯一的 content 摆到盒内九宫格的某个位置；盒子本身在页面里的位置由父级决定。",
        ),
        (
            "约束",
            "固定宽 + 居中的短写法是「外层 Column 居中 + 自身 width」；不要靠外层再包一个 Row 硬撑。",
        ),
        (
            "交互",
            "on_click 让整块可点，ink=True 加涟漪；它比给内容里每个子项挂事件更省事。",
        ),
    ],
    when=[
        "需要一块有底色或描边的区域（提示条、统计块、代码底座）",
        "一组面板要统一内边距（都 16），把留白收在一个地方",
        "需要固定宽并居中，或给内容一个明确的高度边界",
    ],
    avoid=[
        "只是想让子项横向或纵向排开：用 Row / Column，Container 不负责排列",
        "只是要加间距：给父级 padding / spacing，别为 8px 再套一层盒子",
        "需要阴影 + 卡片语义：用 Card，省得自己拼 elevation 与轮廓",
    ],
    examples=[
        Example(
            "内边距对比",
            _padding,
            hint="同一块 190×110，padding 8 / 16 / 24 之下可用面积肉眼可辨。",
            code=_PADDING_CODE,
        ),
        Example(
            "背景、圆角与描边",
            _surface,
            hint="底色最轻、加圆角变软、只描边最明确；三个开关各管一件事。",
            code=_SURFACE_CODE,
        ),
        Example(
            "对齐与约束",
            _aligned,
            hint="盒内对齐与盒子居中容易混：前者是 alignment，后者是父级的事。",
            code=_ALIGN_CODE,
        ),
    ],
    api=[
        Api(
            "content", "Control | None", "None", "唯一的子项；多个子项先包 Column / Row"
        ),
        Api("padding", "Padding | int | None", "None", "盒内留白；内容贴边时最先补它"),
        Api(
            "margin", "Margin | int | None", "None", "盒外留白；优先用父级 spacing 代替"
        ),
        Api(
            "bgcolor",
            "ColorValue | None",
            "None",
            "底色；不传是透明，要底色请显式给角色色",
        ),
        Api("border", "Border | None", "None", "四边描边，通常 1px 的 OUTLINE_VARIANT"),
        Api(
            "border_radius",
            "int | BorderRadius | None",
            "None",
            "圆角；有底色时再给，否则看不出",
        ),
        Api(
            "alignment", "Alignment | None", "None", "content 在盒内的位置，需先有宽高"
        ),
        Api("width", "Number | None", "None", "固定宽度；配合父级居中就是「约束宽度」"),
        Api(
            "on_click",
            "Callable | None",
            "None",
            "整块可点；命中区域比逐个控件挂事件大",
        ),
        Api("ink", "bool", "False", "点击涟漪；只在 on_click 存在时有意义"),
    ],
    notes=[
        info(
            "Container 只有一个 content 槽，不会替你排列多个子项。要放标题、正文、按钮，"
            "先包一个 Column —— 它负责排，Container 负责这一块长什么样。"
        ),
        tip(
            "「居中」有两种：Container.alignment 摆的是盒内的内容，盒子自己在页面里居中"
            "得靠外层 Column(horizontal_alignment=CENTER)。只写 alignment 而盒子宽度"
            "又是自动的，看不出任何变化。"
        ),
        warn(
            "父级已经用 spacing 排列时，别再给每个子项加 margin —— 组间距用 spacing、"
            "盒内留白用 padding，两种距离分开算，改版时才不会互相打架。"
        ),
    ],
    tags=("容器", "container", "盒子", "留白", "背景"),
)


if __name__ == "__main__":
    run(SPEC)
