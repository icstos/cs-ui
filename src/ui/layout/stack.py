"""层叠 (Stack) —— 把子项按 Z 轴叠起来，并允许逐个子项贴边定位。

Stack 的排版只有「叠」这一条：controls 里越靠后越在上层。它真正的用处是分层 ——
底层铺背景、画布或占位块，上层放浮层、角标、悬浮按钮。定位靠**子项自己**的
left / top / right / bottom；不定位的子项由 alignment 统一摆放。

用法::

    Stack(
        width=320,
        height=180,
        controls=[
            Container(bgcolor=...),                     # 底层
            Container(right=16, bottom=16, ...),        # 右下角浮层
        ],
    )
"""

from __future__ import annotations

import flet as ft

from ui.core.doc import Api, Example, Spec, info, run, tip, warn
from ui.core.tokens import FONT_SIZE, FONT_WEIGHT, RADIUS, SPACE

__all__ = ["Stack"]

_MUTED = ft.Colors.ON_SURFACE_VARIANT
_LINE = ft.Colors.OUTLINE_VARIANT


@ft.control
class Stack(ft.Stack):
    """层叠容器：不做流式排版，只决定谁压在谁上面、谁贴在哪个角。

    叠放的代价是「不占位」：两个子项会重叠而不是互相推开，所以每一项的尺寸和
    位置都得自己想清楚 —— 要么给宽高，要么用 left / top / right / bottom 贴边。
    """


# ---------------------------------------------------------------------------
# 示例零件
# ---------------------------------------------------------------------------
def _caption(text: str) -> ft.Control:
    return ft.Text(text, size=FONT_SIZE["small"], color=_MUTED)


def _hero() -> ft.Control:
    """底层：铺满 Stack 的渐变画布。没有子项的 Container 会撑到最大可用尺寸。"""
    return ft.Container(
        border_radius=RADIUS["lg"],
        gradient=ft.LinearGradient(
            begin=ft.Alignment.TOP_LEFT,
            end=ft.Alignment.BOTTOM_RIGHT,
            colors=[ft.Colors.PRIMARY_CONTAINER, ft.Colors.SECONDARY_CONTAINER],
        ),
    )


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
@ft.component
def _overlay() -> ft.Control:
    """底层渐变 + 左下角前景卡片：两层各干一件事，谁也不推谁。"""
    return ft.Column(
        spacing=SPACE["3"],
        controls=[
            Stack(
                width=560,
                height=200,
                controls=[
                    _hero(),
                    ft.Container(
                        left=SPACE["5"],
                        bottom=SPACE["5"],
                        width=300,
                        padding=SPACE["4"],
                        border_radius=RADIUS["md"],
                        bgcolor=ft.Colors.SURFACE,
                        border=ft.Border.all(1, _LINE),
                        content=ft.Column(
                            spacing=SPACE["1"],
                            controls=[
                                ft.Text(
                                    "季度回顾",
                                    size=FONT_SIZE["title"],
                                    weight=FONT_WEIGHT["semibold"],
                                ),
                                ft.Text(
                                    "3 个目标已完成，1 个延期到下周。",
                                    size=FONT_SIZE["body"],
                                    color=_MUTED,
                                ),
                            ],
                        ),
                    ),
                ],
            ),
            _caption(
                "前景卡片给了 left / bottom，就脱离了 alignment 自己贴角；"
                "它不占位，所以背景仍然铺满整块。"
            ),
        ],
    )


@ft.component
def _pinned() -> ft.Control:
    """绝对定位的悬浮按钮：贴在右下角，点一下计数，位置不随内容高度变化。"""
    liked, set_liked = ft.use_state(0)

    def bump(_event: ft.Event[ft.Container]) -> None:
        set_liked(liked + 1)

    return ft.Column(
        spacing=SPACE["3"],
        controls=[
            Stack(
                width=420,
                height=180,
                controls=[
                    ft.Container(
                        width=420,
                        height=180,
                        padding=SPACE["4"],
                        border_radius=RADIUS["lg"],
                        bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
                        content=ft.Column(
                            spacing=SPACE["2"],
                            controls=[
                                ft.Text(
                                    "发布检查",
                                    size=FONT_SIZE["title"],
                                    weight=FONT_WEIGHT["semibold"],
                                ),
                                ft.Text(
                                    "3 个页面、1 个组件有改动，发布后 5 分钟内生效。",
                                    size=FONT_SIZE["body"],
                                    color=_MUTED,
                                ),
                            ],
                        ),
                    ),
                    ft.Container(
                        right=SPACE["4"],
                        bottom=SPACE["4"],
                        width=44,
                        height=44,
                        border_radius=RADIUS["full"],
                        bgcolor=ft.Colors.PRIMARY,
                        alignment=ft.Alignment.CENTER,
                        on_click=bump,
                        content=ft.Icon(
                            ft.Icons.FAVORITE,
                            size=20,
                            color=ft.Colors.ON_PRIMARY,
                        ),
                    ),
                ],
            ),
            ft.Text(
                f"被点了 {liked} 次 —— 按钮只挪动自己的位置，正文排版完全不受影响。",
                size=FONT_SIZE["small"],
                color=_MUTED,
            ),
        ],
    )


def _avatar(with_clip: bool) -> ft.Control:
    """同一个角标，只差 clip_behavior：默认值会把伸出边界的部分切掉。"""
    return Stack(
        width=60,
        height=60,
        clip_behavior=(
            ft.ClipBehavior.HARD_EDGE if with_clip else ft.ClipBehavior.NONE
        ),
        controls=[
            ft.CircleAvatar(
                radius=30,
                bgcolor=ft.Colors.PRIMARY_CONTAINER,
                content=ft.Text(
                    "林",
                    size=FONT_SIZE["headline"],
                    color=ft.Colors.ON_PRIMARY_CONTAINER,
                ),
            ),
            ft.Container(
                right=-4,
                top=-4,
                width=20,
                height=20,
                border_radius=RADIUS["full"],
                bgcolor=ft.Colors.ERROR,
                alignment=ft.Alignment.CENTER,
                content=ft.Text(
                    "3",
                    size=FONT_SIZE["caption"],
                    color=ft.Colors.ON_ERROR,
                    weight=FONT_WEIGHT["semibold"],
                ),
            ),
        ],
    )


@ft.component
def _badge() -> ft.Control:
    """角标压在头像右上角，故意探出 4px：左右一对比就知道该不该改 clip。"""
    return ft.Row(
        spacing=SPACE["8"],
        vertical_alignment=ft.CrossAxisAlignment.START,
        controls=[
            ft.Column(
                spacing=SPACE["2"],
                controls=[
                    _caption("clip_behavior = NONE"),
                    _avatar(with_clip=False),
                    _caption("角标完整"),
                ],
            ),
            ft.Column(
                spacing=SPACE["2"],
                controls=[
                    _caption("默认 HARD_EDGE"),
                    _avatar(with_clip=True),
                    _caption("探出的那一角被切平"),
                ],
            ),
        ],
    )


_OVERLAY_CODE = """Stack(
    height=200,                              # 叠放要先有尺寸
    controls=[
        Container(                           # 底层：铺满的渐变背景
            border_radius=8,
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_LEFT,
                end=ft.Alignment.BOTTOM_RIGHT,
                colors=[ft.Colors.PRIMARY_CONTAINER, ft.Colors.SECONDARY_CONTAINER],
            ),
        ),
        Container(                           # 上层：贴左下角的前景卡片
            left=24,
            bottom=24,
            padding=16,
            bgcolor=ft.Colors.SURFACE,
            border_radius=6,
            content=Text("季度回顾"),
        ),
    ],
)"""

_BADGE_CODE = """Stack(
    width=60,
    height=60,
    clip_behavior=ft.ClipBehavior.NONE,      # 默认 HARD_EDGE 会切掉探出的角标
    controls=[
        CircleAvatar(radius=30, content=Text("林")),
        Container(
            right=-4,                        # 负值：故意压在边界外
            top=-4,
            width=20,
            height=20,
            border_radius=999,
            bgcolor=ft.Colors.ERROR,
            content=Text("3", size=11, color=ft.Colors.ON_ERROR),
        ),
    ],
)"""


SPEC = Spec(
    name="Stack",
    summary="把子项按 Z 轴叠起来：一层铺底、一层浮在上面，并各自贴边定位。",
    definition=(
        "Stack 是二维布局里唯一允许「重叠」的容器：子项不再互相推开，而是从下往上"
        "叠。它适合表达层次关系 —— 背景与前景、面板与悬浮按钮、头像与角标。定位靠"
        "子项自己的 left / top / right / bottom，不定位的才交给 alignment。代价是浮层"
        "不参与排版，占多大、贴哪儿都得自己说清楚。"
    ),
    anatomy=[
        (
            "叠放顺序",
            "controls 越靠后越在上层；第一项通常铺底，最后一项是浮层或角标。",
        ),
        (
            "尺寸",
            "宽高由 Stack 自己给，或取最大那个未定位子项；定位过的子项不撑大 Stack。",
        ),
        (
            "定位",
            "子项给 left / top / right / bottom 就脱离 alignment 按边贴住；同一根轴给两条会拉成弹性尺寸。",
        ),
        ("对齐", "没定位的子项由 alignment 统一摆放；不写就是左上角。"),
        (
            "裁剪",
            "clip_behavior 默认 HARD_EDGE：探出边界的角标会被切掉，要放出去得显式改 NONE。",
        ),
        (
            "贴合",
            "fit 决定未定位子项是否撑满：LOOSE 按内容、EXPAND 撑满、PASS_THROUGH 原样交给子项。",
        ),
    ],
    when=[
        "背景图或渐变上要压文字、卡片、播放控件",
        "浮动按钮、关闭按钮这类固定贴在某个角的控件",
        "头像角标、未读红点、徽章这种「压在上面」的小标记",
    ],
    avoid=[
        "子项要按顺序排开并互相推挤：用 Column / Row，在 Stack 里它们只会重叠",
        "只是给内容加一层底色：用 Container 的 bgcolor，不必叠两层",
        "布局要随窗口宽度重排：用 Row / Column 的弹性，绝对定位不会跟着动",
    ],
    examples=[
        Example(
            "背景与前景",
            _overlay,
            hint="底层渐变铺满，前景卡片贴左下角 —— 两层各管一件事。",
            code=_OVERLAY_CODE,
        ),
        Example(
            "右下角悬浮按钮",
            _pinned,
            hint="按钮用 right / bottom 定位，点一下计数；正文排版不受影响。",
        ),
        Example(
            "角标与裁剪",
            _badge,
            hint="角标故意探出 4px：左图 clip_behavior=NONE 完整，右图默认值被切平。",
            code=_BADGE_CODE,
        ),
    ],
    api=[
        Api("controls", "list[Control]", "", "叠放顺序：列表越靠后越在上层"),
        Api("alignment", "Alignment | None", "None", "未定位子项的对齐基点，默认左上"),
        Api(
            "fit",
            "StackFit",
            "LOOSE",
            "未定位子项的尺寸策略：LOOSE / EXPAND / PASS_THROUGH",
        ),
        Api(
            "clip_behavior",
            "ClipBehavior",
            "HARD_EDGE",
            "超出边界是否裁剪；角标要探出去就改 NONE",
        ),
        Api(
            "left / top / right / bottom",
            "Number | None",
            "None",
            "子项属性：给了就脱离 alignment 按边定位",
        ),
    ],
    notes=[
        warn(
            "默认 clip_behavior 是 HARD_EDGE：角标用负的 right / top 探出边界时会被切平。"
            "要么改成 ClipBehavior.NONE，要么把角标收进 Stack 的宽高范围内。"
        ),
        info(
            "未定位的子项走 alignment 与 fit，定位过的子项完全按边算：同一条轴同时给 "
            "left 和 right（或 top 和 bottom）会被拉成弹性尺寸，而不是只认左边。"
        ),
        tip(
            "Stack 里没有「流」：浮层既不占位也不撑大容器。所以外层最好显式给宽高，"
            "否则 Stack 只会长到最大那个未定位子项的尺寸，浮层可能落在预期之外。"
        ),
    ],
    tags=("层叠", "stack", "叠放", "定位", "浮层", "角标", "overlay"),
)


if __name__ == "__main__":
    run(SPEC)
