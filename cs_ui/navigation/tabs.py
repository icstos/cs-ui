import flet as ft
from collections.abc import Sequence
from typing import Any

from cs_ui.core import BaseControl


@ft.control("Tabs")
class Tabs(BaseControl):
    def __init__(
        self,
        tabs: Sequence[Any] | None = None,
        value=None,
        on_change=None,
        width=None,
        height=None,
    ):
        super().__init__()
        self.tabs = tabs or []
        self.value = value
        self.on_change = on_change
        self.width = width
        self.height = height

    def build(self):
        ft_tabs = []
        for tab in self.tabs:
            if isinstance(tab, tuple):
                val, label = tab
            else:
                val, label = tab, str(tab)
            ft_tabs.append(ft.Tab(label=label, data=val))

        return ft.Tabs(
            content=ft_tabs,
            length=len(ft_tabs),
            selected_index=self._selected_index(),
            on_change=self.on_change,
            width=self.width,
            height=self.height,
        )

    def _selected_index(self) -> int:
        if self.value is None:
            return 0
        for index, tab in enumerate(self.tabs):
            val = tab[0] if isinstance(tab, tuple) else tab
            if val == self.value:
                return index
        return 0