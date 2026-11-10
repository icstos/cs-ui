"""滑块 (Slider / RangeSlider) —— 拖动取值：连续、分段，或一整段区间。

滑块适合「大致范围」而不是「精确数字」：用户看轨道长短就能判断 60% 在哪，
不需要先算。要填精确到分的金额时它反而难用，那是 NumberInput 的活。

值始终回写在 ``value``（区间是 ``start_value`` / ``end_value``）上；给了
``divisions`` 就吸附到刻度，否则 0.1 步长的滑块会吐出 ``0.30000000000000004``，
存进业务字段后到处都要 round。

用法::

    volume = Slider(label="音量", value=30, min=0, max=100, divisions=100)
    Column([volume.ui()])
    print(volume.value)

``slider_label`` 只在拖动时浮在滑块上方，要让当前值一直可见，请在下面另放一行读数
（示例里就是这么做的）—— 一个永远挂着的气泡会盖住轨道。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import flet as ft

from ui.core.constants import LayoutType
from ui.core.doc import Api, Example, Spec, info, run, tip, warn
from ui.core.tokens import FONT_SIZE, SPACE
from ui.input.input import Label

__all__ = ["RangeSlider", "Slider"]

#: 说明行：与正文拉开一档灰，不跟数值抢注意力
MUTED = ft.Colors.ON_SURFACE_VARIANT


@ft.observable
@dataclass
class Slider(Label):
    """单值滑块：一条轨道 + 一个滑块，外加可选的标签与当前值气泡。

    Args:
        value: 当前值，必须落在 ``min`` / ``max`` 之间。
        min: 最小值。与 ``max`` 相等时原生滑块自动变成禁用态。
        max: 最大值。
        divisions: 分段数；``None`` 为连续滑块，给整数则切成等距刻度。
        slider_label: 拖动时浮在滑块上方的气泡文案，支持 ``{value}`` 占位。
        round: 气泡里保留几位小数；默认 0，即四舍五入到整数。
        disabled: 禁用：降灰、拖不动，读 ``value`` 仍是最新值。
        on_value_change: 值变化回调，入参是吸附后的浮点值；联动别的控件时用它。
    """

    value: ft.Number = 0.0
    min: ft.Number = 0.0
    max: ft.Number = 1.0
    divisions: int | None = None
    slider_label: str | None = None
    round: int = 0
    active_color: str | None = None
    inactive_color: str | None = None
    thumb_color: str | None = None
    slider_layout_type: LayoutType = LayoutType.HORIZONTAL
    disabled: bool = False
    on_value_change: Callable[[float], None] | None = None

    def _snap(self, raw: float) -> float:
        """把原始值夹进范围，并按 ``divisions`` 吸附到最近的刻度。

        连续滑块保留原始精度；分段滑块返回 ``min + k * step``，再抹掉浮点尾数，
        免得同一个刻度在两次拖动里得到 0.30000000000000004 和 0.3 两个值。
        """
        low, high = float(self.min), float(self.max)
        value = min(max(raw, low), high)
        if self.divisions:
            step = (high - low) / self.divisions
            if step > 0:
                value = low + round((value - low) / step) * step
                value = round(value, 6)
        return value

    def on_change(self, e: ft.ControlEvent) -> None:
        """滑块值变更：吸附后写回 ``value``，再通知回调。

        ``e.data`` 是字符串（``"30.0"``），直接当数字用会参与字符串比较；
        个别版本把它放在 ``control.value`` 上，两处都取一次更稳。
        """
        raw = e.data if e.data is not None else getattr(e.control, "value", None)
        try:
            value = float(raw)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return
        self.value = self._snap(value)
        if self.on_value_change is not None:
            self.on_value_change(float(self.value))

    def ui(self) -> ft.Control:
        """构建「标签 + 滑块」。

        ``ui()`` 是普通方法，不是 ``@ft.component``：它不订阅、也不自我重绘，
        拖动时不会把整块滑块重建一次。读数交给 ``on_value_change`` 更新到别处，
        滑块本身只跟着自己的原生手势走。
        """
        v_slider = ft.Slider(
            value=self.value,
            min=self.min,
            max=self.max,
            divisions=self.divisions,
            label=self.slider_label,
            round=self.round,
            active_color=self.active_color,
            inactive_color=self.inactive_color,
            thumb_color=self.thumb_color,
            disabled=self.disabled,
            # 禁用就断开回调：即使客户端仍然派发事件，服务端的值也不会动
            on_change=None if self.disabled else self.on_change,
        )

        if self.v_label is not None:
            if self.slider_layout_type == LayoutType.VERTICAL or self.is_vertical:
                return ft.Column(
                    controls=[self.v_label, v_slider],
                    spacing=SPACE["1"],
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                )
            # 滑块吃掉标签之外的宽度：摆在表单里才是一条完整的轨道，
            # 而不是挤在左边一小截（原生滑块没有「自然宽度」）
            v_slider.expand = True
            return ft.Row(
                controls=[self.v_label, v_slider],
                spacing=SPACE["2"],
                # 标签是文字、滑块是 48 高的控件，靠中线对齐才不显得浮着
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        return v_slider


@ft.observable
@dataclass
class RangeSlider(Label):
    """区间滑块：两个滑块，一次选一段范围。

    Args:
        start_value: 左端值；``None`` 表示取范围的前 20%。
        end_value: 右端值；``None`` 表示取范围的后 80%。
        min: 最小值。
        max: 最大值。
        divisions: 分段数；``None`` 为连续滑块（此时气泡标签不显示）。
        slider_label: 拖动时气泡文案，支持 ``{value}``。
        round: 气泡里保留几位小数。
        disabled: 禁用：降灰、拖不动，两端值仍可读。
        on_value_change: 区间变化回调，入参是 ``(start, end)``。
    """

    start_value: ft.Number | None = None
    end_value: ft.Number | None = None
    min: ft.Number = 0.0
    max: ft.Number = 1.0
    divisions: int | None = None
    slider_label: str | None = None
    round: int = 0
    active_color: str | None = None
    inactive_color: str | None = None
    slider_layout_type: LayoutType = LayoutType.HORIZONTAL
    disabled: bool = False
    on_value_change: Callable[[float, float], None] | None = None

    def __post_init__(self) -> None:
        """夹紧两端、保证 ``start <= end``。

        只有 ``None`` 才套用「两端各让 20%」的默认值。用 ``== min`` / ``== max``
        判断「没传」的话，``start_value=0`` 这种合法值会被悄悄改成 20% ——
        用户根本选不了从 0 开始的区间。
        """
        span = float(self.max) - float(self.min)
        if span <= 0:
            self.start_value = self.end_value = self.min
            return

        low = float(self.min)
        start = (
            low + span * 0.2 if self.start_value is None else float(self.start_value)
        )
        end = low + span * 0.8 if self.end_value is None else float(self.end_value)
        start, end = self._snap(start), self._snap(end)
        if start > end:
            start, end = end, start
        self.start_value, self.end_value = start, end

    def _snap(self, raw: float) -> float:
        """夹进范围并吸附到刻度（与 :meth:`Slider._snap` 同一套规则）。"""
        low, high = float(self.min), float(self.max)
        value = min(max(float(raw), low), high)
        if self.divisions:
            step = (high - low) / self.divisions
            if step > 0:
                value = low + round((value - low) / step) * step
                value = round(value, 6)
        return value

    def _on_change(self, e: ft.ControlEvent) -> None:
        """区间变更：两端一起吸附后写回，再通知回调。

        读 ``e.control.start_value`` / ``end_value`` 而不是拆 ``e.data``：
        data 在不同版本里可能是 ``"20,80"`` 这样的拼接串，解析失败就会把拖动卡住。
        """
        start = self._snap(float(e.control.start_value))
        end = self._snap(float(e.control.end_value))
        if start > end:
            start, end = end, start
        self.start_value, self.end_value = start, end
        if self.on_value_change is not None:
            self.on_value_change(start, end)

    def ui(self) -> ft.Control:
        """构建「标签 + 双滑块」，布局规则与 :class:`Slider` 一致。"""
        v_slider = ft.RangeSlider(
            start_value=self.start_value if self.start_value is not None else self.min,
            end_value=self.end_value if self.end_value is not None else self.max,
            min=self.min,
            max=self.max,
            divisions=self.divisions,
            label=self.slider_label,
            round=self.round,
            active_color=self.active_color,
            inactive_color=self.inactive_color,
            disabled=self.disabled,
            on_change=None if self.disabled else self._on_change,
        )

        if self.v_label is not None:
            if self.slider_layout_type == LayoutType.VERTICAL or self.is_vertical:
                return ft.Column(
                    controls=[self.v_label, v_slider],
                    spacing=SPACE["1"],
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                )
            v_slider.expand = True
            return ft.Row(
                controls=[self.v_label, v_slider],
                spacing=SPACE["2"],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        return v_slider


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
def _caption(text: str) -> ft.Control:
    return ft.Text(text, size=FONT_SIZE["small"], color=MUTED)


@ft.component
def _basic() -> ft.Control:
    """连续滑块 + 单位回显：拖动时气泡显示百分比，下面一行常驻读数。"""
    volume, set_volume = ft.use_state(30.0)
    slider = Slider(
        label="音量",
        value=volume,
        min=0,
        max=100,
        divisions=100,
        slider_label="{value}%",
        label_width=64,
        on_value_change=set_volume,
    )
    return ft.Column(
        spacing=10,
        controls=[
            slider.ui(),
            _caption(f"当前音量 {volume:.0f}%"),
        ],
    )


@ft.component
def _steps() -> ft.Control:
    """分段滑块：刻度点 + 档位气泡；下面一条演示禁用态。"""
    level, set_level = ft.use_state(3.0)
    stepped = Slider(
        label="档位",
        value=level,
        min=0,
        max=5,
        divisions=5,
        slider_label="第 {value} 档",
        label_width=64,
        on_value_change=set_level,
    )
    locked = Slider(
        label="亮度",
        value=40,
        min=0,
        max=100,
        divisions=10,
        slider_label="{value}%",
        label_width=64,
        disabled=True,
    )
    return ft.Column(
        spacing=12,
        controls=[
            stepped.ui(),
            _caption(f"当前第 {level:.0f} 档（divisions=5，拖动会吸附到整数档）"),
            locked.ui(),
            _caption("亮度按策略锁定：降灰、拖不动，值仍然是 40%"),
        ],
    )


@ft.component
def _range() -> ft.Control:
    """区间滑块：两端各自拖动，读数实时合并成一个价格区间。"""
    start, set_start = ft.use_state(200.0)
    end, set_end = ft.use_state(800.0)

    def handle_change(low: float, high: float) -> None:
        set_start(low)
        set_end(high)

    price = RangeSlider(
        label="价格区间",
        min=0,
        max=1000,
        start_value=start,
        end_value=end,
        divisions=20,
        slider_label="{value}",
        label_width=64,
        on_value_change=handle_change,
    )
    return ft.Column(
        spacing=10,
        controls=[
            price.ui(),
            _caption(f"¥{start:.0f} — ¥{end:.0f}（两端不会交叉）"),
        ],
    )


_BASIC_CODE = """volume = Slider(
    label="音量",
    value=30,
    min=0,
    max=100,
    divisions=100,          # 切成 100 个刻度
    slider_label="{value}%",  # 拖动时气泡上显示的单位
    on_value_change=lambda v: print(f"{v:.0f}%"),
)

Column([volume.ui()])"""

_RANGE_CODE = """price = RangeSlider(
    label="价格区间",
    min=0,
    max=1000,
    start_value=200,
    end_value=800,
    divisions=20,
    on_value_change=lambda low, high: print(f"¥{low:.0f} - ¥{high:.0f}"),
)

Column([price.ui()])"""


SPEC = Spec(
    name="Slider",
    summary="拖动取值：连续、按刻度分段，或用双滑块一次选一段区间。",
    definition=(
        "滑块把数值空间画成一条轨道，让用户用位置而不是数字来表达「大概多少」。"
        "它把标签排版、分段吸附和值回写一起收进组件：拖动过程中值就落在 ``value`` 上，"
        "调用方不需要解析事件对象。适合音视频进度、亮度、筛选区间这类改动频繁、"
        "又不必精确到个位的参数；需要输入确切金额或编号时，滑块反而不如输入框。"
    ),
    anatomy=[
        (
            "标签",
            "左侧或上方，冒号自动补；一列表单项靠 label_width 对齐，宽度不随文案抖动。",
        ),
        (
            "轨道与滑块",
            "轨道已走过的一段用主色、未走过用中性色，滑块是唯一的可拖点；颜色都走主题角色。",
        ),
        (
            "当前值气泡",
            "只在该滑块被拖动时浮在上方，``{value}`` 换成格式化后的数值；静止时不占视线。",
        ),
        (
            "刻度",
            "``divisions`` 把轨道切成等距小点，拖动会吸附到最近一档，不会停在两档之间。",
        ),
        (
            "双滑块（RangeSlider）",
            "同一根轨道上两个滑块，左端不低于右端；拖到交叉时会自动交换，不会出现反向区间。",
        ),
        (
            "禁用态",
            "整体降灰、不响应拖动，值仍然可读 —— 用于无权限或条件未满足的参数。",
        ),
    ],
    when=[
        "音量、亮度、缩放这类没有绝对正确值、靠试听试看决定的参数",
        "价格、年龄、时间段的筛选区间：用户先拖个大概，再看结果收窄",
        "需要即时反馈的调整（拖动立即可见效果），而不是填完再提交",
    ],
    avoid=[
        "必须精确到个位或小数（金额、库存）：用 NumberInput，滑块很难拖到准确值",
        "只有三五个离散选项：用 Radio / SegmentedButton，比在轨道上找刻度快",
        "选项需要一句解释或需要校验：用单选组或下拉，滑块放不下说明文字",
    ],
    examples=[
        Example(
            "连续与单位回显",
            _basic,
            hint="0-100 的音量，气泡显示百分比；拖动时 value 已回写，下面一行读数实时跟随。",
            code=_BASIC_CODE,
        ),
        Example(
            "分段与禁用",
            _steps,
            hint="divisions=5 把轨道切成 6 个整数档；下面一条演示禁用后仍保留可读的值。",
        ),
        Example(
            "区间选择",
            _range,
            hint="RangeSlider 两端各自拖动，读数合并成「¥200 — ¥800」；两端不会交叉。",
            code=_RANGE_CODE,
        ),
    ],
    api=[
        Api("value", "ft.Number", "0.0", "当前值；拖动即回写，读它就是最新值"),
        Api(
            "min / max",
            "ft.Number",
            "0.0 / 1.0",
            "取值范围；两者相等时原生控件自动禁用",
        ),
        Api(
            "divisions",
            "int | None",
            "None",
            "分段数；None 为连续滑块，整数则按等距刻度吸附",
        ),
        Api(
            "slider_label",
            "str | None",
            "None",
            "拖动时气泡文案，支持 {value} 占位（如「{value}%」）",
        ),
        Api("round", "int", "0", "气泡里保留的小数位；默认四舍五入到整数"),
        Api("label", "str | None", "None", "外置标签文案；冒号自动补"),
        Api("disabled", "bool", "False", "禁用：降灰、拖不动，值仍可读"),
        Api(
            "on_value_change",
            "Callable[[float], None] | None",
            "None",
            "值变化回调，入参是吸附后的值；联动或回显时用它",
        ),
        Api(
            "start_value",
            "ft.Number | None",
            "None",
            "RangeSlider 左端值；None 取前 20%，显式传 0 不会被改写",
        ),
        Api(
            "end_value",
            "ft.Number | None",
            "None",
            "RangeSlider 右端值；None 取后 80%，保证左右不交叉",
        ),
    ],
    notes=[
        tip(
            "给了 ``divisions`` 时值会吸附到刻度并抹掉浮点尾数：同一个刻度不会这帧是 "
            "0.3、下帧变成 0.30000000000000004，存库与去重都省心。"
        ),
        info(
            "RangeSlider 的默认值只在参数为 None 时套用（两端各留 20%）。此前按 "
            "「等于 min / max」判断，导致 start_value=0 或 end_value=max 被悄悄改掉，"
            "从 0 开始的区间根本选不出来。"
        ),
        warn(
            "禁用是靠「不挂 on_change」实现的：客户端即使派发事件，服务端的 value 也"
            "不会动。写自定义封装时别只把颜色改灰就当成禁用。"
        ),
    ],
    tags=("滑块", "slider", "range", "区间", "表单"),
)


if __name__ == "__main__":
    run(SPEC)
