from collections.abc import Sequence
from typing import Any

from cs_ui.core.control import Control


class Dropdown(Control):
    def __init__(
        self,
        label: str | None = None,
        options: Sequence[Any] | None = None,
        value: Any = None,
        width=None,
        hint_text: str | None = None,
        on_change=None,
    ):
        super().__init__(width=width)
        self.label = label
        self.options = options or []
        self.value = value
        self.hint_text = hint_text
        self.on_change = on_change

    def _create(self):
        import flet as ft

        ft_options = [
            ft.dropdown.Option(text, val)
            if isinstance(option, tuple)
            else ft.dropdown.Option(str(option), option)
            for option in self.options
        ]

        return ft.Dropdown(
            text=self.label,
            options=ft_options,
            value=self.value,
            hint_text=self.hint_text,
            on_select=self._handle_change,
        )

    def _handle_change(self, event):
        if callable(self.on_change):
            self.on_change(event)
