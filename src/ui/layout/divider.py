"""分隔线 (Divider) —— 横线分节、竖线分栏。

:class:`Divider` 与 :class:`VerticalDivider` 都是 flet 同名控件的薄封装，
默认取主题的 ``outline_variant``：明暗主题下都不抢内容。

用法::

    Divider()                                  # 横线
    Divider(thickness=2, leading_indent=24)    # 加粗 + 左缩进
    VerticalDivider(width=24)                  # 竖线，放在 Row 里；高度由 Row 决定
"""

from __future__ import annotations

import flet as ft

from ui.core.doc import Api, Example, Spec, info, run, warn
from ui.core.tokens import FONT_SIZE

__all__ = ["Divider", "VerticalDivider"]


@ft.control
class Divider(ft.Divider):
    """横向分隔线，详见 :class:`flet.Divider`。"""


@ft.control
class VerticalDivider(ft.VerticalDivider):
    """纵向分隔线，放在 :class:`flet.Row` 里分栏。"""


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
def _caption(text: str) -> ft.Control:
    return ft.Text(text, size=12, color=ft.Colors.ON_SURFACE_VARIANT)


@ft.component
def _horizontal() -> ft.Control:
    """三种横线：默认、两端缩进、加粗强调。"""
    return ft.Column(
        spacing=10,
        controls=[
            _caption("默认：1px 线，上下各留 16px"),
            Divider(),
            _caption("两端缩进 24px：线和正文左边缘对齐"),
            Divider(leading_indent=24, trailing_indent=24),
            _caption("2px + 圆角：只在需要强调分段时用"),
            Divider(thickness=2, radius=2),
        ],
    )


@ft.component
def _vertical() -> ft.Control:
    """竖线没有 height 参数：高度由所在的 Row 决定，所以先给 Row 定高。"""
    return ft.Row(
        height=44,
        spacing=16,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Text("09:30", size=FONT_SIZE["body"]),
            VerticalDivider(width=24, thickness=1),
            ft.Text("已同步", size=FONT_SIZE["body"]),
            VerticalDivider(width=24, thickness=1),
            ft.Text("3 条记录", size=FONT_SIZE["body"], color=ft.Colors.ON_SURFACE_VARIANT),
        ],
    )


@ft.component
def _labeled() -> ft.Control:
    """带文字的分隔：两个可伸缩的 Divider 夹一段文字。"""
    return ft.Column(
        spacing=14,
        controls=[
            ft.Row(
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    Divider(expand=1),
                    ft.Text("今日", size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                    Divider(expand=1),
                ],
            ),
            _caption("两侧各 expand=1，文字自然落在中间；换语言、换字号都不用重算。"),
        ],
    )


_HORIZONTAL_CODE = """Divider()                                        # 默认：1px + 上下 16px
Divider(leading_indent=24, trailing_indent=24)    # 两端缩进，和正文对齐
Divider(thickness=2, radius=2)                    # 加粗强调，少用"""

_VERTICAL_CODE = """Row(
    height=44,                              # 竖线没有 height 参数，靠 Row 定高
    vertical_alignment=ft.CrossAxisAlignment.CENTER,
    controls=[
        Text("09:30"),
        VerticalDivider(width=24),          # width 含左右留白
        Text("已同步"),
    ],
)"""

_LABELED_CODE = """Row(
    spacing=12,
    vertical_alignment=ft.CrossAxisAlignment.CENTER,
    controls=[
        Divider(expand=1),        # 左边吃掉一半空档
        Text("今日", size=12, color=ft.Colors.ON_SURFACE_VARIANT),
        Divider(expand=1),        # 右边吃掉另一半
    ],
)"""


SPEC = Spec(
    name="Divider",
    summary="用一条发丝线把内容分组：横线分节、竖线分栏。",
    definition=(
        "分隔线是排版里的标点：它不传递信息，只负责断开。横线用于上下两段内容的"
        "换气，竖线用于同一行里并排的两组；线本身取主题的 outline_variant，"
        "明暗主题下都不会比正文更抢眼。要做「今日」这种小节标题，用两个 Divider "
        "夹一段文字即可，不必再引入一个标题组件。"
    ),
    anatomy=[
        ("线", "默认 1px 的 outline_variant；thickness 加粗只用于强调。"),
        (
            "留白",
            "height（横线）/ width（竖线）是线占的空间，不是粗细 —— 断开感主要来自它。",
        ),
        (
            "缩进",
            "leading_indent / trailing_indent 让线两端对齐文字，而不是顶到容器边缘。",
        ),
        (
            "竖线",
            "同文件的 VerticalDivider，放在 Row 里分栏；它没有 height，高度由 Row 或外层容器决定。",
        ),
    ],
    when=[
        "表单分成「基本信息 / 联系方式」两组",
        "列表项之间需要弱分隔，比卡片更轻",
        "同一行并排两组信息（时间 | 状态）需要隔开",
    ],
    avoid=[
        "每个列表项之间都画线：改用间距或斑马纹，满屏横线会盖过内容",
        "当作边框：容器的 border 才是边框，Divider 只负责分隔",
        "需要强调层级：用标题或卡片，线的视觉重量撑不起层级",
    ],
    examples=[
        Example(
            "横线",
            _horizontal,
            hint="默认、两端缩进、加粗三种；线的粗细与留白是两件事。",
            code=_HORIZONTAL_CODE,
        ),
        Example(
            "竖线",
            _vertical,
            hint="在 Row 里分栏；显式给 height，避免高度跟着最高的子项乱跑。",
            code=_VERTICAL_CODE,
        ),
        Example(
            "带文字",
            _labeled,
            hint="两个 expand=1 的 Divider 夹一个 Text —— 组件本身不画文字。",
            code=_LABELED_CODE,
        ),
    ],
    api=[
        Api("color", "ColorValue | None", "None", "线的颜色；默认取 outline_variant"),
        Api("thickness", "int | float | None", "None", "线的粗细（px），默认 1"),
        Api("height", "int | float | None", "None", "横线占用的纵向空间，默认 16"),
        Api("leading_indent", "int | float | None", "None", "左端缩进，让线对齐文字"),
        Api("trailing_indent", "int | float | None", "None", "右端缩进"),
        Api("radius", "int | BorderRadius | None", "None", "线端的圆角"),
    ],
    notes=[
        info(
            "Divider 本身不画文字。带文字的分隔是组合出来的：Row 里放两个 "
            "expand=1 的 Divider，中间夹一个 Text。"
        ),
        warn(
            "VerticalDivider 没有 height 参数（传了会抛 TypeError）。高度取所在 Row / "
            "Container 的约束：Row 没定高时它只能贴到最高的子项，要稳定就先给 Row 定高。"
        ),
        info(
            "颜色默认取主题的 outline_variant，不需要也不应该传十六进制灰 —— "
            "写死的灰在深色主题下会变成一道亮线。"
        ),
    ],
    tags=("分割线", "divider", "分隔", "竖线"),
)


if __name__ == "__main__":
    run(SPEC)
