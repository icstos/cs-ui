import flet as ft
from collections.abc import Callable


class Page:
    def __init__(self, page: ft.Page):
        self._page = page

    def add(self, *controls):
        processed_controls = []
        for control in controls:
            if hasattr(control, 'build') and callable(control.build):
                processed_controls.append(control.build())
            else:
                processed_controls.append(control)
        self._page.add(*processed_controls)

    def clear(self):
        self._page.controls.clear()
        self._page.update()

    def update(self):
        self._page.update()


class App:
    def __init__(
        self,
        title: str = "CS UI App",
        on_start: Callable[[Page], object] | None = None,
        bgcolor: str = "#f5f5f5",
    ):
        self.title = title
        self.on_start = on_start
        self.bgcolor = bgcolor
        self.page: Page | None = None

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

        ft.run(main)
