import flet as ft
from collections.abc import Sequence
from typing import Any


class RadioGroup(ft.Column):
    def __init__(self, label: str | None = None, options: Sequence[Any] | None = None,
                 value: Any = None, on_change: Any = None, **kwargs):
        super().__init__(**kwargs)
        radios = []
        for opt in (options or []):
            val, text = opt if isinstance(opt, tuple) else (opt, str(opt))
            radios.append(ft.Radio(value=val, label=text))

        controls = []
        if label:
            controls.append(ft.Text(label, weight="bold", size=14))
        controls.append(
            ft.RadioGroup(content=radios, value=value, on_change=on_change)
        )
        self.controls = controls
        self.spacing = 4
