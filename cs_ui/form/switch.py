import flet as ft

from cs_ui.core import BaseControl


@ft.control("Switch")
class Switch(BaseControl):
    def __init__(
        self, label: str = "", value: bool = False, on_change=None, active_color=None
    ):
        super().__init__()
        self.label = label
        self.value = value
        self.on_change = on_change
        self.active_color = active_color

    def build(self):
        return ft.Switch(
            label=self.label,
            value=self.value,
            on_change=self.on_change,
            active_color=self.active_color,
        )