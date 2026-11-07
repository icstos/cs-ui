"""纵向排列 (Column) —— 把子项排成一列，并决定间距、对齐、滚动与伸缩。

Column 只做两件事：主轴（纵向）上怎么分布，交叉轴（横向）上怎么对齐。它默认
按内容高度撑开、既不滚动也不压缩子项，所以内容超出可用高度时必须先选一条路：
给 Column 一个有界高度并开 ``scroll``，或让某一项 ``expand`` 吃掉剩余高度。

用法::

    Column(
        spacing=8,                                  # 相邻子项间距
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        controls=[Text("标题"), Text("副标题")],
    )
"""

from __future__ import annotations

import flet as ft

from ui.core.doc import Api, Example, Spec, info, run, tip, warn
from ui.core.tokens import FONT_SIZE, RADIUS, SPACE

__all__ = ["Column"]

_MUTED = ft.Colors.ON_SURFACE_VARIANT
_LINE = ft.Colors.OUTLINE_VARIANT


@ft.control
class Column(ft.Column):
    """纵向排列子项。默认间距取 4px 网格上的 8（flet 原生是 10）。

    横向并排用 :class:`ui.layout.row.Row`，参数一一对应；两者可以互相嵌套，
    但别为了对齐反复加层 —— 先把 spacing 和 alignment 用对。
    """

    spacing: int = SPACE["2"]
    run_spacing: int = SPACE["2"]


# ---------------------------------------------------------------------------
# 示例零件
# ---------------------------------------------------------------------------
def _caption(text: str) -> ft.Control:
    return ft.Text(text, size=FONT_SIZE["small"], color=_MUTED)


def _block(height: int = 26) -> ft.Control:
    return ft.Container(
        width=84,
        height=height,
        border_radius=RADIUS["sm"],
        bgcolor=ft.Colors.PRIMARY_CONTAINER,
    )


def _bar(text: str) -> ft.Control:
    """宽度交给父级的 STRETCH —— 自己不给 width，才看得出「撑满」。"""
    return ft.Container(
        height=24,
        padding=ft.Padding.symmetric(horizontal=SPACE["2"]),
        alignment=ft.Alignment.CENTER_LEFT,
        border_radius=RADIUS["sm"],
        bgcolor=ft.Colors.SECONDARY_CONTAINER,
        content=ft.Text(
            text,
            size=FONT_SIZE["caption"],
            color=ft.Colors.ON_SECONDARY_CONTAINER,
        ),
    )


def _grow(weight: int) -> ft.Control:
    return ft.Container(
        expand=weight,
        alignment=ft.Alignment.CENTER,
        border_radius=RADIUS["sm"],
        bgcolor=ft.Colors.PRIMARY_CONTAINER,
        content=ft.Text(
            str(weight),
            size=FONT_SIZE["caption"],
            color=ft.Colors.ON_PRIMARY_CONTAINER,
        ),
    )


def _frame(
    content: ft.Control, *, label: str, width: int = 216, height: int = 140
) -> ft.Control:
    """给演示加一层描边的定高底座，主轴分布才看得出来。"""
    return ft.Column(
        spacing=SPACE["2"],
        controls=[
            _caption(label),
            ft.Container(
                width=width,
                height=height,
                padding=SPACE["3"],
                border=ft.Border.all(1, _LINE),
                border_radius=RADIUS["md"],
                content=content,
            ),
        ],
    )


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
@ft.component
def _spacing() -> ft.Control:
    """同样三个块，只改 spacing：0 / 8 / 16 / 24 的疏密差别一眼可辨。"""
    strips: list[ft.Control] = []
    for gap in (0, SPACE["2"], SPACE["4"], SPACE["6"]):
        strips.append(
            ft.Column(
                spacing=SPACE["2"],
                controls=[
                    _caption(f"spacing {gap}"),
                    Column(spacing=gap, controls=[_block() for _ in range(3)]),
                ],
            )
        )

    return ft.Column(
        spacing=SPACE["3"],
        controls=[
            ft.Row(
                spacing=SPACE["6"],
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=strips,
            ),
            _caption("间距属于父级，不属于子项：不要在块上挂 margin 去凑距离。"),
        ],
    )


@ft.component
def _axes() -> ft.Control:
    """主轴管纵向分布，交叉轴管横向对齐；expand 决定谁分剩余高度。"""
    return ft.Column(
        spacing=SPACE["4"],
        controls=[
            ft.Row(
                spacing=SPACE["4"],
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    _frame(
                        Column(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            spacing=SPACE["2"],
                            controls=[_block(22) for _ in range(3)],
                        ),
                        label="alignment = SPACE_BETWEEN",
                    ),
                    _frame(
                        Column(
                            alignment=ft.MainAxisAlignment.END,
                            spacing=SPACE["2"],
                            controls=[_block(22) for _ in range(3)],
                        ),
                        label="alignment = END",
                    ),
                    _frame(
                        Column(
                            spacing=SPACE["2"],
                            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                            controls=[_bar("STRETCH 撑满宽度") for _ in range(3)],
                        ),
                        label="horizontal = STRETCH",
                    ),
                ],
            ),
            ft.Row(
                spacing=SPACE["5"],
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.Container(
                        width=300,
                        height=140,
                        padding=SPACE["3"],
                        border=ft.Border.all(1, _LINE),
                        border_radius=RADIUS["md"],
                        content=Column(
                            spacing=SPACE["2"],
                            controls=[_grow(1), _grow(2), _grow(1)],
                        ),
                    ),
                    ft.Container(
                        width=340,
                        content=_caption(
                            "expand 是子项自己的属性，不是 Column 的参数："
                            "剩余高度按 1:2:1 分完，固定高度的子项先拿走自己那份。"
                        ),
                    ),
                ],
            ),
        ],
    )


@ft.component
def _scroll() -> ft.Control:
    """30 行塞进 240 高的框里：Column 自己有界高度，滚动条才出现。"""
    rows = [
        ft.Container(
            height=32,
            padding=ft.Padding.symmetric(horizontal=SPACE["3"]),
            border_radius=RADIUS["sm"],
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            alignment=ft.Alignment.CENTER_LEFT,
            content=ft.Text(
                f"第 {index:02d} 行", size=FONT_SIZE["small"], color=_MUTED
            ),
        )
        for index in range(1, 31)
    ]

    return ft.Column(
        spacing=SPACE["3"],
        controls=[
            ft.Container(
                width=440,
                height=240,
                padding=SPACE["2"],
                border=ft.Border.all(1, _LINE),
                border_radius=RADIUS["md"],
                content=Column(
                    scroll=ft.ScrollMode.AUTO,
                    spacing=SPACE["2"],
                    controls=rows,
                ),
            ),
            _caption(
                "滚动要有个「框」：高度写死、由父级约束，或用 expand 占满剩余空间。"
            ),
        ],
    )


_SPACING_CODE = """Column(
    spacing=8,                                   # 相邻子项间距（默认 8）
    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    controls=[
        Text("通知设置"),
        Container(height=1, bgcolor=ft.Colors.OUTLINE_VARIANT),
        Text("只接收与账号相关的提醒", color=ft.Colors.ON_SURFACE_VARIANT),
    ],
)"""

_SCROLL_CODE = """Container(
    height=240,                                  # 必须先有界，滚动才有参照
    content=Column(
        scroll=ft.ScrollMode.AUTO,               # 超出部分自己滚
        spacing=8,
        controls=[Text(f"第 {i} 行") for i in range(30)],
    ),
)"""


SPEC = Spec(
    name="Column",
    summary="把子项纵向排开：间距、主轴与交叉轴对齐、滚动，以及按份分高度。",
    definition=(
        "Column 是纵向的一维布局：子项从上到下排开，主轴（纵向）决定它们靠上、居中、"
        "靠下还是两端/均分，交叉轴（横向）决定左对齐、居中、右对齐还是把每项拉满宽度。"
        "它默认按内容高度撑开，不会自动滚动，也不会压缩子项 —— 内容超出可用高度时，"
        "要么给高度开滚动，要么让某一项 expand 吃掉剩余空间，没有第三条路。"
    ),
    anatomy=[
        ("子项", "controls 按顺序从上到下排；高度由内容、height 或 expand 决定。"),
        (
            "间距",
            "spacing 是相邻两项的距离，默认 8（flet 原生是 10，这里收到 4px 网格上）。",
        ),
        (
            "主轴",
            "alignment 决定整列在纵向上怎么分布：START / CENTER / END / SPACE_BETWEEN / SPACE_AROUND。",
        ),
        (
            "交叉轴",
            "horizontal_alignment 决定子项在横向上怎么对齐，默认 START；STRETCH 会把每项拉到与列同宽。",
        ),
        (
            "滚动",
            "scroll=ScrollMode.AUTO 让超出部分可滚，前提是 Column 自己有界高度（height 或父级约束）。",
        ),
        (
            "伸缩",
            "expand 是子项自己的属性：剩余高度按份数瓜分，固定高度的子项先占位再分。",
        ),
    ],
    when=[
        "一屏内容自上而下排列：表单字段、详情信息、设置项",
        "需要一组控件等分或按比例分高度：写 expand=1 / 2 / 1",
        "内容可能很长但仍要留在同一块区域里：配一个有界高度加 scroll",
    ],
    avoid=[
        "子项要横向并排：用 Row，别把每个子项都包成一整行",
        "一屏只有一个控件：直接放进父级，少一层嵌套",
        "超长且逐项加载的数据：用 ListView，Column 会一次性构建全部子项",
    ],
    examples=[
        Example(
            "间距对比",
            _spacing,
            hint="同样三个块，spacing 取 0 / 8 / 16 / 24 的疏密差别。",
            code=_SPACING_CODE,
        ),
        Example(
            "主轴、交叉轴与伸缩",
            _axes,
            hint="SPACE_BETWEEN / END 拉开纵向分布，STRETCH 拉满宽度，expand 按 1:2:1 分剩余高度。",
        ),
        Example(
            "可滚动列",
            _scroll,
            hint="30 行放进 240 高的框：有界高度是滚动条的开关。",
            code=_SCROLL_CODE,
        ),
    ],
    api=[
        Api("controls", "list[Control]", "", "子项，按顺序从上到下"),
        Api("spacing", "int", "8", "相邻子项间距；本组件默认 8，flet 原生为 10"),
        Api(
            "alignment",
            "MainAxisAlignment",
            "START",
            "主轴分布：start / center / end / spaceBetween …",
        ),
        Api(
            "horizontal_alignment",
            "CrossAxisAlignment",
            "START",
            "交叉轴对齐；STRETCH 会把子项拉满宽度",
        ),
        Api(
            "scroll", "ScrollMode | None", "None", "纵向滚动；需要 Column 自身有界高度"
        ),
        Api("auto_scroll", "bool", "False", "新内容追加后自动滚到底，日志面板常用"),
        Api("tight", "bool", "False", "收窄到内容高度，而不是撑满父级高度"),
        Api(
            "on_scroll",
            "Callable | None",
            "None",
            "滚动回调；做吸顶、触底加载时从这里接",
        ),
    ],
    notes=[
        tip(
            "默认 spacing 从 flet 的 10 收到 8，与 tokens 的 4px 网格、Row 的默认值对齐。"
            "要贴紧就 spacing=0，而不是给子项挂负 margin。"
        ),
        warn(
            "scroll 只在 Column 自己有界高度时才生效：给 height、让父级有界，或用 expand "
            "占满剩余空间。放在无界高度里滚动条不会出现，内容被直接裁掉。"
        ),
        info(
            "horizontal_alignment=STRETCH 会把每个子项拉到与列同宽，子项自己的 width "
            "随之失效；需要「一部分撑满、一部分固定宽」时，把固定宽的项包进一层 Row 再居中。"
        ),
    ],
    tags=("列", "column", "纵向", "排列", "flex", "滚动"),
)


if __name__ == "__main__":
    run(SPEC)
