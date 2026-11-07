"""横向排列 (Row) —— 把子项排成一行，并决定间距、对齐、换行与伸缩。

Row 只做两件事：主轴（横向）上怎么摆，交叉轴（纵向）上怎么对齐。空间不够时
它默认既不换行也不滚动，而是让子项溢出，所以在窄容器里必须先选定策略：
``wrap`` 换行、``scroll`` 横向滚动，还是让某一项 ``expand`` 吃掉剩余空间。

用法::

    Row(
        spacing=8,                                   # 相邻子项间距
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[Icon(ft.Icons.CHECK), Text("已同步")],
    )
"""

from __future__ import annotations

import flet as ft

from ui.core.doc import Api, Example, Spec, info, run, tip, warn
from ui.core.tokens import FONT_SIZE, RADIUS, SPACE

__all__ = ["Row"]

_MUTED = ft.Colors.ON_SURFACE_VARIANT
_LINE = ft.Colors.OUTLINE_VARIANT


@ft.control
class Row(ft.Row):
    """横向排列子项。默认间距取 4px 网格上的 8（flet 原生是 10）。

    纵向堆叠用 :class:`flet.Column`，参数一一对应；两者可以互相嵌套，但别为了
    对齐反复加层 —— 先把 spacing 和 alignment 用对。
    """

    spacing: int = SPACE["2"]
    run_spacing: int = SPACE["2"]


# ---------------------------------------------------------------------------
# 示例零件
# ---------------------------------------------------------------------------
def _caption(text: str) -> ft.Control:
    return ft.Text(text, size=FONT_SIZE["small"], color=_MUTED)


def _block(width: int, height: int, text: str = "") -> ft.Control:
    return ft.Container(
        width=width,
        height=height,
        alignment=ft.Alignment.CENTER,
        bgcolor=ft.Colors.PRIMARY_CONTAINER,
        border_radius=RADIUS["sm"],
        content=ft.Text(
            text,
            size=FONT_SIZE["caption"],
            color=ft.Colors.ON_PRIMARY_CONTAINER,
        ),
    )


def _frame(
    content: ft.Control, *, width: int = 760, height: int | None = None
) -> ft.Control:
    """给演示加一层描边底座，方便看出 Row 占了多宽。"""
    return ft.Container(
        width=width,
        height=height,
        padding=SPACE["3"],
        border=ft.Border.all(1, _LINE),
        border_radius=RADIUS["md"],
        content=content,
    )


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
@ft.component
def _spacing() -> ft.Control:
    """同样的四个块，只改 spacing：0 / 8 / 16 / 24 的疏密差别一眼可辨。"""
    rows: list[ft.Control] = []
    for gap in (0, SPACE["2"], SPACE["4"], SPACE["6"]):
        rows.append(
            ft.Row(
                spacing=SPACE["3"],
                controls=[
                    ft.Text(
                        f"spacing {gap}",
                        size=FONT_SIZE["small"],
                        color=_MUTED,
                        width=78,
                    ),
                    Row(spacing=gap, controls=[_block(52, 32) for _ in range(4)]),
                ],
            )
        )

    return ft.Column(
        spacing=SPACE["3"],
        controls=[
            *rows,
            _caption("间距属于父级，不属于子项：不要在块上挂 margin 去凑距离。"),
        ],
    )


@ft.component
def _alignment() -> ft.Control:
    """主轴管横向分布，交叉轴管纵向对齐 —— 两个参数各管一个方向。"""

    def cross_strip(align: ft.CrossAxisAlignment, label: str) -> ft.Control:
        return ft.Row(
            spacing=SPACE["3"],
            controls=[
                ft.Text(label, size=FONT_SIZE["small"], color=_MUTED, width=96),
                ft.Container(
                    expand=True,
                    height=56,
                    padding=ft.Padding.symmetric(horizontal=SPACE["3"]),
                    border=ft.Border.all(1, _LINE),
                    border_radius=RADIUS["sm"],
                    content=Row(
                        spacing=SPACE["2"],
                        vertical_alignment=align,
                        controls=[_block(56, 24), _block(56, 40)],
                    ),
                ),
            ],
        )

    return ft.Column(
        spacing=SPACE["2"],
        controls=[
            cross_strip(ft.CrossAxisAlignment.START, "START"),
            cross_strip(ft.CrossAxisAlignment.CENTER, "CENTER（默认）"),
            cross_strip(ft.CrossAxisAlignment.END, "END"),
            ft.Container(height=SPACE["2"]),
            _caption("主轴：SPACE_BETWEEN 把首尾顶到两端，中间空档自动均分。"),
            _frame(
                Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        _block(72, 32, "A"),
                        _block(72, 32, "B"),
                        _block(72, 32, "C"),
                    ],
                ),
                height=64,
            ),
        ],
    )


_TAGS = ("全部", "进行中", "已完成", "我负责的", "本周到期", "已归档", "草稿")


@ft.component
def _wrap_and_expand() -> ft.Control:
    """放不下时两条路：换行（wrap）或让子项按份数分剩余空间（expand）。"""
    chips = [
        ft.Container(
            padding=ft.Padding.symmetric(horizontal=SPACE["2"], vertical=SPACE["1"]),
            border_radius=RADIUS["full"],
            bgcolor=ft.Colors.SECONDARY_CONTAINER,
            content=ft.Text(
                tag,
                size=FONT_SIZE["small"],
                color=ft.Colors.ON_SECONDARY_CONTAINER,
            ),
        )
        for tag in _TAGS
    ]

    return ft.Column(
        spacing=SPACE["3"],
        controls=[
            _caption(
                "wrap=True，宽度 340：一行放不下就折行，行距由 run_spacing 决定。"
            ),
            ft.Container(
                width=360,
                padding=SPACE["3"],
                border=ft.Border.all(1, _LINE),
                border_radius=RADIUS["md"],
                content=Row(
                    wrap=True,
                    spacing=SPACE["2"],
                    run_spacing=SPACE["2"],
                    controls=chips,
                ),
            ),
            _caption("expand 1 : 2 : 1，固定宽的项先占 80，剩下的才按份数分。"),
            _frame(
                Row(
                    spacing=SPACE["2"],
                    controls=[
                        ft.Container(
                            expand=1,
                            height=40,
                            alignment=ft.Alignment.CENTER,
                            bgcolor=ft.Colors.PRIMARY_CONTAINER,
                            border_radius=RADIUS["sm"],
                            content=ft.Text("1", size=FONT_SIZE["small"]),
                        ),
                        ft.Container(
                            expand=2,
                            height=40,
                            alignment=ft.Alignment.CENTER,
                            bgcolor=ft.Colors.PRIMARY_CONTAINER,
                            border_radius=RADIUS["sm"],
                            content=ft.Text("2", size=FONT_SIZE["small"]),
                        ),
                        ft.Container(
                            expand=1,
                            height=40,
                            alignment=ft.Alignment.CENTER,
                            bgcolor=ft.Colors.PRIMARY_CONTAINER,
                            border_radius=RADIUS["sm"],
                            content=ft.Text("1", size=FONT_SIZE["small"]),
                        ),
                        ft.Container(
                            width=80,
                            height=40,
                            alignment=ft.Alignment.CENTER,
                            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                            border_radius=RADIUS["sm"],
                            content=ft.Text("固定 80", size=FONT_SIZE["caption"]),
                        ),
                    ],
                )
            ),
        ],
    )


_SPACING_CODE = """Row(
    spacing=8,                       # 相邻子项之间；默认 8（4px 网格）
    controls=[
        Icon(ft.Icons.CHECK_CIRCLE, size=16),
        Text("已同步"),
        Container(expand=1),         # 吃掉中间空档，把后面推到右边
        Text("刚刚", color=ft.Colors.ON_SURFACE_VARIANT),
    ],
)"""

_WRAP_CODE = """Container(
    width=360,                       # 必须给宽度，否则 Row 不知道自己该在哪折
    content=Row(
        wrap=True,                   # 放不下就换行，而不是溢出
        spacing=8,                   # 同一行内
        run_spacing=8,               # 行与行之间
        controls=[Chip(t) for t in tags],
    ),
)"""


SPEC = Spec(
    name="Row",
    summary="把子项排成一行：间距、主轴与交叉轴对齐、换行和按份分空间。",
    definition=(
        "Row 是横向的一维布局：子项从左到右排开，主轴（横向）决定它们靠左、居中、"
        "两端还是均分，交叉轴（纵向）决定它们顶端对齐、居中还是底端对齐。它不会自动"
        "适应窄容器 —— 放不下时默认溢出 —— 所以用之前先想清楚这一行是换行、滚动，"
        "还是让某一项 expand 吃掉剩余空间。纵向堆叠用 Column，参数几乎一一对应。"
    ),
    anatomy=[
        ("子项", "controls 按顺序从左到右排；想控制宽度就给子项 width 或 expand。"),
        (
            "间距",
            "spacing 是相邻两项的距离，默认 8（本组件统一到 4px 网格，flet 原生是 10）。",
        ),
        (
            "主轴",
            "alignment 决定整排在横向上怎么分布：start / center / end / SPACE_BETWEEN / SPACE_AROUND。",
        ),
        (
            "交叉轴",
            "vertical_alignment 决定子项在纵向上怎么对齐，默认 CENTER；高度由最高的子项撑开。",
        ),
        (
            "换行",
            "wrap=True 时放不下折到下一行，行距是 run_spacing（默认 8），行内分布是 run_alignment。",
        ),
        (
            "伸缩",
            "expand 是子项自己的属性：按份数瓜分剩余宽度，固定宽的项先占位再分。",
        ),
    ],
    when=[
        "一组控件横向并排：图标 + 文字、按钮组、工具条",
        "左右两端对齐：左边标题、右边操作，用 alignment=SPACE_BETWEEN",
        "需要按比例分宽：三栏 1:2:1，写 expand=1 / 2 / 1 即可",
    ],
    avoid=[
        "子项要纵向堆叠：用 Column，别靠 wrap 硬折成多行",
        "一行只有一两个控件且不需要对齐：直接放进父级，少一层嵌套",
        "内容会无限增长（标签云、筛选条件）：一定要配 wrap 或 scroll，否则必然溢出",
    ],
    examples=[
        Example(
            "间距对比",
            _spacing,
            hint="同一个四块组合，spacing 取 0 / 8 / 16 / 24 的疏密差别。",
            code=_SPACING_CODE,
        ),
        Example(
            "主轴与交叉轴",
            _alignment,
            hint="纵向三档交叉轴对齐，加一条 SPACE_BETWEEN 的主轴分布。",
        ),
        Example(
            "换行与伸缩",
            _wrap_and_expand,
            hint="窄容器里 wrap 折行；宽容器里 expand 按 1:2:1 分掉剩余空间。",
            code=_WRAP_CODE,
        ),
    ],
    api=[
        Api("controls", "list[Control]", "", "子项，按顺序从左到右"),
        Api("spacing", "int", "8", "相邻子项间距；本组件默认 8，flet 原生为 10"),
        Api(
            "alignment",
            "MainAxisAlignment",
            "START",
            "主轴分布：start / center / end / spaceBetween …",
        ),
        Api(
            "vertical_alignment", "CrossAxisAlignment", "CENTER", "交叉轴对齐，默认居中"
        ),
        Api("wrap", "bool", "False", "放不下时是否折行；配合一个有宽度的父级"),
        Api("run_spacing", "int", "8", "折行后行与行的距离"),
        Api(
            "run_alignment", "MainAxisAlignment", "START", "折行后每一行内部的主轴分布"
        ),
        Api("tight", "bool", "False", "收窄到内容宽度，而不是撑满父级"),
        Api("scroll", "ScrollMode | None", "None", "横向滚动；与 wrap 二选一"),
    ],
    notes=[
        tip(
            "默认 spacing 从 flet 的 10 收到 8，和 tokens 的 4px 网格对齐；需要贴紧就用 "
            "spacing=0，而不是给每项挂负 margin。"
        ),
        warn(
            "Row 放不下时既不会换行也不会滚动，默认直接溢出（调试期是黄黑条纹，发布后被裁）。"
            "窄容器里先决定 wrap / scroll / expand 三者之一，别等它挤爆再补。"
        ),
        info(
            "expand 是子项自己的属性，不是 Row 的参数；固定宽的子项先拿走自己的宽度，"
            "剩下的空间才按 expand 的份数分 —— 1:2:1 里夹一个 width=80 时，比例说的是"
            "扣掉 80 之后的部分。"
        ),
    ],
    tags=("行", "row", "横向", "排列", "flex", "换行"),
)


if __name__ == "__main__":
    run(SPEC)
