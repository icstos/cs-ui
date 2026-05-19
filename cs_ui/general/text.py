import flet as ft


class Text(ft.Text):
    def __init__(self, value: str = "", size: int = 16, color: str = "#0f172a", **kwargs):
        super().__init__(value=value, size=size, color=color, **kwargs)
