"""Chip 选择组件

提供标签式的单选/多选功能，参考 Radio 的 observable + dataclass + component 模式实现。
"""

import flet as ft
from dataclasses import dataclass, field
from ui.core.constants import LayoutType
from ui.input.input import Label

ICON_SIZE = 16
BORDER_RADIUS = 8
DEFAULT_FORM_HEIGHT = 36


@ft.observable
@dataclass
class Chip(Label):
    """Chip 选择组件，支持单选和多选模式。

    Attributes:
        value: 单选模式下存储选中的选项值，多选模式下存储选中的选项值列表。
        options: 可选项列表，每个元素为选项的文本标签。
        multi_select: 是否为多选模式，默认 False（单选）。
        chip_layout_type: 布局方向，水平或垂直，默认水平。
    """

    value: str | None = None
    selected_values: list[str] = field(default_factory=list)
    options: list[str] = field(default_factory=list)
    multi_select: bool = False
    chip_layout_type: LayoutType = LayoutType.HORIZONTAL

    def on_change(self, option: str, selected: bool) -> None:
        """芯片选择状态变化时的回调。

        子类可重写此方法以处理自定义逻辑。

        Args:
            option: 被点击的选项文本。
            selected: 该选项被点击后的选中状态。
        """
        pass

    @ft.component
    def ui(self):
        """构建 Chip 组件的 UI。

        Returns:
            ft.Control: 包含所有 Chip 控件的行或列布局。
        """
        chips: list[ft.Control] = []

        for option in self.options:
            is_selected: bool
            if self.multi_select:
                is_selected = option in self.selected_values
            else:
                is_selected = self.value == option

            def make_on_click(opt: str):
                """为每个 chip 创建闭包捕获当前选项值。"""

                def _on_click(e=None) -> None:
                    """芯片点击事件处理。

                    Args:
                        e: flet 事件对象（可选）。
                    """
                    if self.multi_select:
                        if opt in self.selected_values:
                            self.selected_values = [
                                v for v in self.selected_values if v != opt
                            ]
                        else:
                            self.selected_values = self.selected_values + [opt]
                    else:
                        if self.value == opt:
                            self.value = None
                        else:
                            self.value = opt
                    self.on_change(
                        opt,
                        opt
                        in (
                            self.selected_values
                            if self.multi_select
                            else [self.value]
                            if self.value
                            else []
                        ),
                    )
                    self.notify()

                return _on_click

            chip = ft.Chip(
                label=ft.Text(
                    option,
                    color=ft.Colors.WHITE if is_selected else ft.Colors.BLACK,
                ),
                selected=is_selected,
                selected_color=ft.Colors.GREEN,
                check_color=ft.Colors.WHITE,
                on_click=make_on_click(option),
            )
            chips.append(chip)

        if self.chip_layout_type == LayoutType.HORIZONTAL:
            chip_content = ft.Row(
                controls=chips,
                spacing=self.spacing,
                run_spacing=self.run_spacing,
                wrap=True,
            )
        else:
            chip_content = ft.Column(
                controls=chips,
                spacing=2,
                run_spacing=10,
            )

        if self.v_label is not None:
            if self.is_vertical:
                return ft.Column(
                    controls=[self.v_label, chip_content],
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                )
            else:
                return ft.Row(controls=[self.v_label, chip_content])
        else:
            return chip_content


@ft.component
def App():
    single_chip = Chip(
        label="单选 Chip",
        options=["选项 A", "选项 B", "选项 C"],
    )
    multi_chip = Chip(
        label="多选 Chip",
        options=["标签 1", "标签 2", "标签 3", "标签 4"],
        multi_select=True,
        is_vertical=True,
    )

    return ft.Column(
        controls=[
            single_chip.ui(),
            multi_chip.ui(),
            ft.Button(
                content=ft.Text("打印值"),
                on_click=lambda _: print(
                    f"单选值: {single_chip.value}\n多选值: {multi_chip.value}"
                ),
            ),
        ]
    )


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
