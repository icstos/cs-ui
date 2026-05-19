import flet as ft

from cs_ui.core import BaseControl


@ft.control("Checkbox")
class Checkbox(BaseControl):
    def __init__(
        self,
        label: str = "",
        value: bool = False,
        on_change=None,
        disabled: bool = False,
    ):
        super().__init__()
        self.label = label
        self.value = value
        self.on_change = on_change
        self.disabled = disabled

    def build(self):
        return ft.Checkbox(
            label=self.label,
            value=self.value,
            on_change=self.on_change,
            disabled=self.disabled,
        )