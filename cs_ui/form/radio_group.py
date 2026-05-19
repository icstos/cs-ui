import flet as ft
from collections.abc import Sequence
from typing import Any

from cs_ui.core import BaseControl


@ft.control("RadioGroup")
class RadioGroup(BaseControl):
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

    def build(self):
        radios = []
        for option in self.options:
            if isinstance(option, tuple):
                val, text = option
            else:
                val, text = option, str(option)
            radios.append(ft.Radio(value=val, label=text))

        controls = []
        if self.label:
            controls.append(ft.Text(self.label, weight="bold", size=14))
        controls.append(
            ft.RadioGroup(content=radios, value=self.value, on_change=self.on_change)
        )
        return ft.Column(controls=controls, spacing=4)