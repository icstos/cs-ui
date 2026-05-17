from typing import Any, Optional, Sequence, Tuple

from ..core.control import Control


class Dropdown(Control):
    def __init__(
        self,
        label: Optional[str] = None,
        options: Optional[Sequence[Any]] = None,
        value: Any = None,
        width=None,
        hint_text: Optional[str] = None,
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
            on_select=self._handle_change,
        )

    def _handle_change(self, event):
        if callable(self.on_change):
            self.on_change(event)
