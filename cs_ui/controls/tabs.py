import flet as ft
from collections.abc import Sequence
from typing import Any


@ft.control("Tabs")
class Tabs(ft.BaseControl):
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


def main(page: ft.Page):
    page.title = "Tabs Demo"
    page.add(
        Tabs(
            tabs=["首页", "设置", "关于"],
            value="首页",
            width=320,
            on_change=lambda e: page.add(
                ft.Text(f"当前标签索引：{e.control.selected_index}", color="green")
            ),
        )
    )


if __name__ == "__main__":
    ft.run(main)

    def _selected_index(self):
        if self.value is None:
            return 0
        for index, tab in enumerate(self.tabs):
            val = tab[0] if isinstance(tab, tuple) else tab
            if val == self.value:
                return index
        return 0
