import flet as ft
from typing import Any

from cs_ui.core import BaseControl


@ft.control("Chip")
class Chip(BaseControl):
    def __init__(
        self,
        label: str = "",
        icon: Any | None = None,
        on_delete=None,
        on_tap=None,
        selected: bool = False,
        disabled: bool = False,
        bgcolor="#f3f4f6",
        selected_color="#1f6feb",
    ):
        super().__init__()
        self.label = label
        self.icon = icon
        self.on_delete = on_delete
        self.on_tap = on_tap
        self.selected = selected
        self.disabled = disabled
        self.bgcolor = bgcolor
        self.selected_color = selected_color

    def build(self):
        icon_arg = None
        if isinstance(self.icon, str):
            icon_arg = getattr(ft.icons, self.icon.upper(), None)
            if icon_arg is None:
                icon_arg = ft.Icon(self.icon)
        else:
            icon_arg = self.icon

        return ft.Chip(
            label=ft.Text(self.label),
            icon=icon_arg,
            on_delete=self.on_delete,
            on_tap=self.on_tap,
            selected=self.selected,
            disabled=self.disabled,
            bgcolor=self.bgcolor,
            selected_color=self.selected_color,
        )