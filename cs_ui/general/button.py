import flet as ft
from typing import Any

from cs_ui.core import BaseControl


@ft.control("Button")
class Button(BaseControl):
    def __init__(
        self,
        label: str,
        on_click=None,
        width=None,
        bgcolor: str = "#1f6feb",
        text_color: str = "white",
        disabled: bool = False,
        icon: Any | None = None,
        tooltip: str | None = None,
    ):
        super().__init__()
        self.label = label
        self.on_click = on_click
        self.width = width
        self.bgcolor = bgcolor
        self.text_color = text_color
        self.disabled = disabled
        self.icon = icon
        self.tooltip = tooltip

    def build(self):
        return ft.Button(
            content=ft.Text(self.label, color=self.text_color),
            on_click=self.on_click,
            bgcolor=self.bgcolor,
            disabled=self.disabled,
            icon=self.icon,
            tooltip=self.tooltip,
            width=self.width,
        )