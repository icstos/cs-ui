import flet as ft
from typing import Optional
from .core.control import Control


class Page:
    def __init__(self, page: ft.Page):
        self._page = page

    def add(self, *controls):
        built = [
            control.build() if isinstance(control, Control) else control
            for control in controls
        ]
        self._page.add(*built)

    def clear(self):
        self._page.controls.clear()
        self._page.update()

    def update(self):
        self._page.update()


class App:
    def __init__(
        self, title: str = "CS UI App", on_start=None, bgcolor: str = "#f5f5f5"
    ):
        self.title = title
        self.on_start = on_start
        self.bgcolor = bgcolor
        self.page: Optional[Page] = None

    def run(self):
        def main(page: ft.Page):
            page.title = self.title
            page.bgcolor = self.bgcolor
            page.padding = 20
            page.scroll = "auto"
            page.vertical_alignment = ft.MainAxisAlignment.START
            self.page = Page(page)
            if callable(self.on_start):
                self.on_start(self.page)

        ft.app(target=main)
