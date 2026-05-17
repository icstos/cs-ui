from typing import Any, Optional, Sequence, Tuple

from ..core.control import Control


class Tabs(Control):
    def __init__(
        self,
        tabs: Optional[Sequence[Any]] = None,
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
