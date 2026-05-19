import flet as ft
from typing import Any


class ListTile(ft.ListTile):
    def __init__(self, title_text: str | None = None, subtitle_text: str | None = None, **kwargs):
        super().__init__(**kwargs)
        if title_text:
            self.title = ft.Text(title_text, weight="bold")
        if subtitle_text:
            self.subtitle = ft.Text(subtitle_text, size=12, color="#6b7280")
