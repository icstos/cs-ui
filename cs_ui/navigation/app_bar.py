import flet as ft


class AppBar(ft.AppBar):
    def __init__(self, title_text: str = "", **kwargs):
        super().__init__(**kwargs)
        if title_text:
            self.title = ft.Text(title_text, size=20, weight="bold")
