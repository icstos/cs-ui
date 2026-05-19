from cs_ui.core.control import Control
from typing import Optional


class TextField(Control):
    def __init__(
        self,
        value: str = "",
        label: Optional[str] = None,
        hint_text: Optional[str] = None,
        width=None,
        password: bool = False,
        on_change=None,
        on_submit=None,
    ):
        super().__init__(width=width)
        self.value = value
        self.label = label
        self.hint_text = hint_text
        self.password = password
        self.on_change = on_change
        self.on_submit = on_submit

    def _create(self):
        import flet as ft

        return ft.TextField(
            value=self.value,
            label=self.label,
            hint_text=self.hint_text,
            password=self.password,
            on_change=self._handle_change,
            on_submit=self._handle_submit,
        )

    def _handle_change(self, event):
        if callable(self.on_change):
            self.on_change(event)

    def _handle_submit(self, event):
        if callable(self.on_submit):
            self.on_submit(event)
