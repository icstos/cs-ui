from collections.abc import Sequence
from typing import Any

from cs_ui.core.control import Control


class Tabs(Control):
    def __init__(
        self,
        tabs: Sequence[Any] | None = None,
        value=None,
        on_change=None,
        width=None,
        height=None,
    ):
        super().__init__(width=width, height=height)
        self.tabs = tabs or []
        self.value = value
        self.on_change = on_change

    def _create(self):
        import flet as ft

        ft_tabs = [
            ft.Tab(label=label, data=val)
            if isinstance(tab, tuple)
            else ft.Tab(label=str(tab), data=tab)
            for tab in self.tabs
        ]

        return ft.Tabs(
            content=ft_tabs,
            length=len(ft_tabs),
            selected_index=self._selected_index(),
            on_change=self._handle_change,
            width=self.width,
            height=self.height,
        )

    def _selected_index(self):
        if self.value is None:
            return 0
        for index, tab in enumerate(self.tabs):
            val = tab[0] if isinstance(tab, tuple) else tab
            if val == self.value:
                return index
        return 0

    def _handle_change(self, event):
        if callable(self.on_change):
            self.on_change(event)
