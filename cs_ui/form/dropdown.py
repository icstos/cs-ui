import flet as ft
from collections.abc import Sequence
from typing import Any


class Dropdown(ft.Dropdown):
    def __init__(self, options_list: Sequence[Any] | None = None, **kwargs):
        super().__init__(**kwargs)
        for opt in (options_list or []):
            val, text = opt if isinstance(opt, tuple) else (opt, str(opt))
            self.options.append(ft.dropdown.Option(text, val))
