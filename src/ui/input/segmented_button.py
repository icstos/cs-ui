"""分段控件 (SegmentedButton) —— 2-5 个互斥选项，像一排连在一起的按钮。

它解决的是「在几个短选项之间立刻切一下」：日 / 周 / 月、列表 / 网格、简洁 / 详细。
选项全部摊在一条上，比 Radio 省纵向空间，比下拉框少一次点击。默认单选：
点新的、旧的自动取消 —— 多选是显式打开的另一种模式，不该是默认行为。

选项有两种写法：``options`` 收字符串（值即文案，最省事），``segments`` 收
:class:`Segment`（要图标、要「值 ≠ 文案」时用）。两者只需要给一个。

用法::

    view = SegmentedButton(options=["日", "周", "月"], selected=["月"])
    Column([view])
    print(view.selected)
"""

from __future__ import annotations

import flet as ft

from ui.core.doc import Api, Example, Spec, info, run, warn
from ui.core.tokens import FONT_SIZE, RADIUS, SPACE

__all__ = ["Segment", "SegmentedButton"]

#: 选中段的图标与描边；未选中段交给主题的默认外观（不铺底色）
SELECTED_FG = ft.Colors.ON_PRIMARY
SELECTED_BG = ft.Colors.PRIMARY
MUTED = ft.Colors.ON_SURFACE_VARIANT

#: 分段圆角：与输入框同一档，工具栏里不会显得比旁边的按钮更圆
RADIUS_PX = RADIUS["md"]


@ft.control
class Segment(ft.Segment):
    """一个分段。``value`` 是唯一标识，``label`` 缺省时直接显示 ``value``。"""

    def init(self):
        if self.label is None:
            self.label = ft.Text(value=self.value, size=FONT_SIZE["body"])


@ft.control
class SegmentedButton(ft.SegmentedButton):
    """分段控件：一排互斥按钮，值落在 ``selected`` 上。

    Args:
        options: 简写选项，字符串的值与文案相同。
        segments: 完整选项，需要图标或「值 ≠ 文案」时用它。
        selected: 已选中的 value 列表；单选时只放一个。
        allow_multiple_selection: 是否允许多选，默认 False（互斥）。
        allow_empty_selection: 是否允许一个都不选，默认 True。
        disabled: 禁用：整组降灰、不响应点击，``selected`` 仍可读。
        on_change: 选择变化回调，入参是事件对象；选中值读 ``e.data`` 或 ``selected``。
    """

    segments: list[Segment] | None = None
    options: list[str | Segment] | None = None
    selected_icon: ft.IconData | ft.Control | None = None
    allow_multiple_selection: bool = False
    allow_empty_selection: bool = True

    def init(self):
        # 每个按钮各建一个图标：把它写成字段默认值会让所有实例共用同一个 Control
        if self.selected_icon is None:
            self.selected_icon = ft.Icon(
                icon=ft.Icons.CHECK,
                size=18,
                color=SELECTED_FG,
            )

        if self.options is not None:
            self.segments = [
                option if isinstance(option, Segment) else Segment(str(option))
                for option in self.options
            ]
        if not self.segments:
            raise ValueError("SegmentedButton 需要 options 或 segments 至少一项")

        # allow_empty_selection=False 时 selected 不能为空，否则 flet 校验直接报错
        if not self.allow_empty_selection and not self.selected:
            self.selected = [self.segments[0].value]

        # 禁用就断开回调：客户端即使把点击发上来，也不该产生一次「选择变化」
        if self.disabled:
            self.on_change = None

        # 调用方传了 style 就用它，别覆盖自定义样式
        if self.style is None:
            self.style = ft.ButtonStyle(
                color={ft.ControlState.SELECTED: SELECTED_FG},
                bgcolor={ft.ControlState.SELECTED: SELECTED_BG},
                side={ft.ControlState.SELECTED: ft.BorderSide(1, SELECTED_BG)},
                shape={
                    ft.ControlState.DEFAULT: ft.RoundedRectangleBorder(
                        radius=RADIUS_PX
                    ),
                    ft.ControlState.SELECTED: ft.RoundedRectangleBorder(
                        radius=RADIUS_PX
                    ),
                },
            )


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
def _caption(text: str) -> ft.Control:
    return ft.Text(text, size=FONT_SIZE["small"], color=MUTED)


def _picked(e: ft.ControlEvent) -> list[str]:
    """取选中值：``e.data`` 优先，拿不到再读控件自己的 ``selected``。

    两个来源都试一次，是因为不同版本里 data 可能是列表、也可能为空；
    只认其中一个，升级后就会出现「点了没反应」。
    """
    data = e.data
    if isinstance(data, list):
        return [str(item) for item in data]
    selected = getattr(e.control, "selected", None)
    return [str(item) for item in (selected or [])]


@ft.component
def _basic() -> ft.Control:
    """三段切换视图：选中的段立刻反映到下面的内容区。"""
    period, set_period = ft.use_state("月")
    summary = {
        "日": "今天 · 12 条记录",
        "周": "本周 · 86 条记录",
        "月": "本月 · 342 条记录",
    }

    def handle_change(e: ft.ControlEvent) -> None:
        picked = _picked(e)
        if picked:
            set_period(picked[0])

    button = SegmentedButton(
        options=["日", "周", "月"],
        selected=[period],
        allow_empty_selection=False,
        on_change=handle_change,
    )
    return ft.Column(
        spacing=SPACE["3"],
        controls=[
            button,
            ft.Container(
                padding=ft.Padding.symmetric(
                    horizontal=SPACE["3"], vertical=SPACE["2"]
                ),
                border_radius=RADIUS["lg"],
                bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
                content=ft.Text(summary[period], size=FONT_SIZE["body"]),
            ),
        ],
    )


@ft.component
def _icons_multi() -> ft.Control:
    """带图标 + 多选：图标保留在选中段上（不换成对勾），选中值可以有多个。"""
    days, set_days = ft.use_state(["周一", "周三"])

    def handle_change(e: ft.ControlEvent) -> None:
        set_days(_picked(e))

    return ft.Column(
        spacing=SPACE["3"],
        controls=[
            SegmentedButton(
                segments=[
                    Segment(value="周一", label="周一", icon=ft.Icons.LOOKS_ONE),
                    Segment(value="周三", label="周三", icon=ft.Icons.LOOKS_3),
                    Segment(value="周五", label="周五", icon=ft.Icons.LOOKS_5),
                ],
                selected=days,
                allow_multiple_selection=True,
                allow_empty_selection=True,
                # 选中时保留分段自己的图标，而不是换成默认的对勾
                show_selected_icon=False,
                on_change=handle_change,
            ),
            _caption(
                f"提醒日：{'、'.join(days) or '未选择'}（allow_multiple_selection=True）"
            ),
        ],
    )


@ft.component
def _disabled() -> ft.Control:
    """禁用：整组降灰、点了不动，但选中的「中」仍然看得出来。"""
    return ft.Column(
        spacing=SPACE["2"],
        controls=[
            SegmentedButton(
                options=["小", "中", "大"],
                selected=["中"],
                allow_empty_selection=False,
                disabled=True,
            ),
            _caption("当前档位是「中」，由上级设置锁定，不能在这里改"),
        ],
    )


_BASIC_CODE = """period = SegmentedButton(
    options=["日", "周", "月"],
    selected=["月"],
    allow_empty_selection=False,   # 必须始终有一段选中
    on_change=lambda e: print(e.control.selected),
)

Column([period])"""

_ICON_CODE = """SegmentedButton(
    segments=[
        Segment(value="周一", label="周一", icon=ft.Icons.LOOKS_ONE),
        Segment(value="周三", label="周三", icon=ft.Icons.LOOKS_3),
    ],
    selected=["周一"],
    allow_multiple_selection=True,   # 显式打开多选
    show_selected_icon=False,        # 保留分段自己的图标
)"""


SPEC = Spec(
    name="SegmentedButton",
    summary="2-5 个互斥选项排成一条按钮组：选中项实心，切换即换内容。",
    definition=(
        "分段控件把一组短选项并排成一条，选中哪一段就点亮哪一段，用来切换同一位置的"
        "内容（日 / 周 / 月、列表 / 网格）。它比单选组省纵向空间，比下拉框少一次展开，"
        "代价是每一段都必须很短 —— 文案一长就会挤成一行小字。默认单选且可以一个都不选；"
        "要给一段加上图标或让值与文案不同，用 Segment 而不是字符串。"
    ),
    anatomy=[
        (
            "分段条",
            "一条横向按钮组，段与段之间共享描边；整条高度跟随主题，不与旁边的按钮错位。",
        ),
        (
            "选中段",
            "主色实底 + 反白文字，未选中段保持透明底 —— 让「当前在哪一档」一眼可见。",
        ),
        (
            "选中图标",
            (
                "默认在选中段文字前加一枚对勾；分段本身已有图标时关掉 "
                "show_selected_icon，否则图标会被对勾顶掉。"
            ),
        ),
        (
            "分段图标",
            "Segment 的 icon 放在文案前，给「列表 / 网格」这类选项一个可扫读的锚点。",
        ),
        ("禁用态", "整组降灰、不响应点击；已选中的那一段仍然保留选中样式，值可读。"),
    ],
    when=[
        "两到四个短选项之间切换，且切换后同一块区域的内容随之变化",
        "选项要一眼看全，不想为一次选择展开下拉或弹层",
        "工具栏里需要一个紧凑的视图切换（日 / 周 / 月、列表 / 卡片）",
    ],
    avoid=[
        "选项多到要换行或文案很长：用 Radio，分段条会把文字压成一排省略号",
        "选项需要各自一句说明、需要逐项禁用或校验：用 Radio（支持说明与独占禁用）",
        (
            "切换的是页面级导航（地址会变、可前进后退）：用 Tabs，分段按钮的语义是"
            "「取值」而不是「换页」"
        ),
    ],
    examples=[
        Example(
            "切换视图",
            _basic,
            hint="日 / 周 / 月三段互斥，选中即换下面的内容；点已选段不会清空。",
            code=_BASIC_CODE,
        ),
        Example(
            "图标与多选",
            _icons_multi,
            hint="Segment 给每段加图标并关掉对勾；显式打开多选后可以同时选中多个。",
            code=_ICON_CODE,
        ),
        Example(
            "禁用",
            _disabled,
            hint="整组禁用后仍然看得出选的是「中」，只是点不动。",
        ),
    ],
    api=[
        Api(
            "options",
            "list[str | Segment] | None",
            "None",
            "简写选项：字符串的值与文案相同，顺序即渲染顺序",
        ),
        Api(
            "segments",
            "list[Segment] | None",
            "None",
            "完整选项：需要图标或「值 ≠ 文案」时用；与 options 二选一",
        ),
        Api("selected", "list[str]", "[]", "已选中的 value 列表；单选时只放一个"),
        Api(
            "allow_multiple_selection",
            "bool",
            "False",
            "是否允许多选；默认互斥，点新的旧的自然取消",
        ),
        Api(
            "allow_empty_selection",
            "bool",
            "True",
            "是否允许一个都不选；设为 False 时会自动补上第一段",
        ),
        Api("show_selected_icon", "bool", "True", "选中时是否在文字前显示对勾"),
        Api(
            "selected_icon",
            "IconData | Control | None",
            "None",
            "选中标记；留空用 CHECK 图标（反白），配合 show_selected_icon 控制是否显示",
        ),
        Api(
            "on_change",
            "Callable[[ft.ControlEvent], None] | None",
            "None",
            "选择变化回调；选中值读 e.data 或 e.control.selected",
        ),
        Api("disabled", "bool", "False", "整组禁用：降灰、不响应点击，值仍可读"),
    ],
    notes=[
        info(
            "默认值从「允许多选」改成互斥（allow_multiple_selection=False）：分段控件的"
            "语义就是在几档里选一档，默认多选会让用户点第二下时才发现行为不对。要多选"
            "就显式打开，示例「图标与多选」就是这么做的。"
        ),
        info(
            "配色从写死的 WHITE / BLUE 换成 ON_PRIMARY / PRIMARY，并且不再给未选中段铺"
            "白底 —— 深色主题里那块白会变成一条刺眼的亮条。选中图标也是每个实例各建一个，"
            "不再共享同一个 Control。"
        ),
        warn(
            "allow_empty_selection=False 时 selected 不能为空，否则 flet 在挂载时校验失败。"
            "组件会在 init 里自动补第一段；自己改 selected 时别把它清空。"
        ),
    ],
    tags=("分段", "segmented", "切换", "互斥", "表单"),
)


if __name__ == "__main__":
    run(SPEC)
