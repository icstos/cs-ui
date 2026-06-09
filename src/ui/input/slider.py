import flet as ft
from dataclasses import dataclass

from ui.core.constants import LayoutType
from ui.input.input import Label


@ft.observable
@dataclass
class Slider(Label):
    """单值滑块组件，封装 ft.Slider，配合 Label 提供标签与布局能力。"""

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

    def on_change(self, e: ft.ControlEvent) -> None:
        """滑块值变更回调，将原生事件数据写入 value 字段。"""
        self.value = float(e.data) if e.data else self.min

    def ui(self) -> ft.Control:
        """构建包含标签与滑块控件的 UI 组件。

        注意: ui() 为普通方法（非 @ft.component），仅在初始构建时调用一次，
        之后滑块状态由 flet 原生控件自行管理，拖动时不会触发重建。
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
            on_change=self.on_change,
        )

        if self.v_label is not None:
            controls: list[ft.Control] = [self.v_label, v_slider]
            if self.slider_layout_type == LayoutType.VERTICAL or self.is_vertical:
                return ft.Column(
                    controls=controls,
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                )
            else:
                return ft.Row(controls=controls)
        else:
            return v_slider


@ft.observable
@dataclass
class RangeSlider(Label):
    """范围滑块组件，封装 ft.RangeSlider，配合 Label 提供标签与布局能力。"""

    start_value: ft.Number = 0.0
    end_value: ft.Number = 1.0
    min: ft.Number = 0.0
    max: ft.Number = 1.0
    divisions: int | None = None
    slider_label: str | None = None
    round: int = 0
    active_color: str | None = None
    inactive_color: str | None = None
    slider_layout_type: LayoutType = LayoutType.HORIZONTAL

    def __post_init__(self) -> None:
        """确保 start_value 和 end_value 在 [min, max] 内且 start_value <= end_value。"""
        span = self.max - self.min
        if span <= 0:
            self.start_value = self.end_value = self.min
            return

        # 将值钳制到 [min, max] 范围内
        self.start_value = max(self.min, min(self.max, self.start_value))
        self.end_value = max(self.min, min(self.max, self.end_value))

        # 处理未显式设置的默认值场景
        if self.start_value == self.min:
            self.start_value = self.min + span * 0.2
        if self.end_value == self.max:
            self.end_value = self.min + span * 0.8

        # 最终确保 start_value < end_value
        if self.start_value >= self.end_value:
            self.start_value = self.min + span * 0.2
            self.end_value = self.min + span * 0.8

    def _on_change(self, e: ft.ControlEvent) -> None:
        """范围变更回调，解析 e.data 字符串写入 start_value / end_value。"""
        # print(dir(e), e.control.start_value, '....')
        # if e.data:
        #     parts = e.data.split(",")
        self.start_value = e.control.start_value
        self.end_value = e.control.end_value
        self.notify()

    def ui(self) -> ft.Control:
        """构建包含标签与范围滑块控件的 UI 组件。

        注意: ui() 为普通方法（非 @ft.component），仅在初始构建时调用一次，
        之后滑块状态由 flet 原生控件自行管理，拖动时不会触发重建。
        """

        v_range_slider = ft.RangeSlider(
            start_value=self.start_value,
            end_value=self.end_value,
            min=self.min,
            max=self.max,
            divisions=self.divisions,
            label=self.slider_label,
            round=self.round,
            active_color=self.active_color,
            inactive_color=self.inactive_color,
            on_change=self._on_change,
        )

        if self.v_label is not None:
            controls: list[ft.Control] = [self.v_label, v_range_slider]
            if self.slider_layout_type == LayoutType.VERTICAL or self.is_vertical:
                return ft.Column(
                    controls=controls,
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                )
            else:
                return ft.Row(controls=controls)
        else:
            return v_range_slider


@ft.component
def App() -> ft.Control:
    """测试用入口，展示 Slider 与 RangeSlider 组件。"""

    slider = Slider(
        label="音量",
        value=0.3,
        slider_label="{value}",
        is_required=True,
    )

    range_slider = RangeSlider(
        label="价格范围",
        min=0,
        max=1000,
        slider_label="{value}",
        is_required=True,
    )

    return ft.Column(
        controls=[
            slider.ui(),
            Slider(
                label="亮度",
                value=0.7,
                slider_layout_type=LayoutType.VERTICAL,
                is_vertical=True,
            ).ui(),
            range_slider.ui(),
            RangeSlider(
                label="年龄范围",
                min=0,
                max=120,
                slider_layout_type=LayoutType.VERTICAL,
                is_vertical=True,
            ).ui(),
            ft.Button(
                content=ft.Text("打印值"),
                on_click=lambda _: print(
                    f"Slider: {slider.value}, "
                    f"RangeSlider: {range_slider.start_value} - {range_slider.end_value}"
                ),
            ),
        ]
    )


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
