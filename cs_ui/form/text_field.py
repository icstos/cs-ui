import flet as ft

from cs_ui.core import BaseControl


@ft.control("TextField")
class TextField(BaseControl):
    def __init__(
        self,
        value: str = "",
        label: str | None = None,
        hint_text: str | None = None,
        width=None,
        password: bool = False,
        on_change=None,
        on_submit=None,
    ):
        super().__init__()
        self.value = value
        self.label = label
        self.hint_text = hint_text
        self.password = password
        self.width = width
        self.on_change = on_change
        self.on_submit = on_submit

    def build(self):
        return ft.TextField(
            value=self.value,
            label=self.label,
            hint_text=self.hint_text,
            password=self.password,
            on_change=self.on_change,
            on_submit=self.on_submit,
            width=self.width,
        )