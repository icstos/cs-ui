from collections.abc import Sequence
from typing import Any

from cs_ui.core.control import Control


class RadioGroup(Control):
    def __init__(
        self,
        label: str | None = None,
        options: Sequence[Any] | None = None,
        value: Any = None,
        on_change=None,
    ):
        super().__init__()
        self.label = label
        self.options = options or []
        self.value = value
        self.on_change = on_change

    def _create(self):
        import flet as ft

        radios = [
            ft.Radio(value=val, label=text)
            if isinstance(option, tuple)
            else ft.Radio(value=option, label=str(option))
            for option in self.options
        ]

        controls = []
        if self.label:
            controls.append(ft.Text(self.label, weight="bold", size=14))
        controls.append(
            ft.RadioGroup(
                content=radios, value=self.value, on_change=self._handle_change
            )
        )

        return ft.Column(controls=controls, spacing=4)

    def _handle_change(self, event):
        if callable(self.on_change):
            self.on_change(event)
