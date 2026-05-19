import flet as ft
from collections.abc import Sequence
from typing import Any

from cs_ui.core import BaseControl


@ft.control("Dropdown")
class Dropdown(BaseControl):
    def __init__(
        self,
        label: str | None = None,
        options: Sequence[Any] | None = None,
        value: Any = None,
        width=None,
        hint_text: str | None = None,
        on_change=None,
    ):
        super().__init__()
        self.label = label
        self.options = options or []
        self.value = value
        self.width = width
        self.hint_text = hint_text
        self.on_change = on_change

    def build(self):
        ft_options = []
        for option in self.options:
            if isinstance(option, tuple):
                val, text = option
            else:
                val, text = option, str(option)
            ft_options.append(ft.dropdown.Option(text, val))
        return ft.Dropdown(
            text=self.label,
            options=ft_options,
            value=self.value,
            hint_text=self.hint_text,
            on_select=self.on_change,
            width=self.width,
        )