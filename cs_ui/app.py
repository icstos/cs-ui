import flet as ft
from collections.abc import Callable


class Page:
    """对 ft.Page 的轻量封装，提供更简洁的 API"""

    def __init__(self, page: ft.Page):
        self._page = page

    def __getattr__(self, name):
        return getattr(self._page, name)

    def add(self, *controls):
        self._page.add(*controls)

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
        self._title = title
        self._on_start = on_start
        self._bgcolor = bgcolor
        self.page: Page | None = None

    def run(self):
        def main(page: ft.Page):
            page.title = self._title
            page.bgcolor = self._bgcolor
            page.padding = 20
            page.scroll = ft.ScrollMode.AUTO
            self.page = Page(page)
            if callable(self._on_start):
                self._on_start(self.page)

        ft.app(target=main)
