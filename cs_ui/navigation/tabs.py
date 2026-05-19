import flet as ft
from collections.abc import Sequence
from typing import Any


class Tabs(ft.Tabs):
    def __init__(self, tab_labels: Sequence[Any] | None = None, **kwargs):
        super().__init__(**kwargs)
        for tab in (tab_labels or []):
            val, label = tab if isinstance(tab, tuple) else (tab, str(tab))
            self.tabs.append(ft.Tab(label=label, data=val))
