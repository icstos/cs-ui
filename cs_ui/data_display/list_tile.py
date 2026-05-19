import flet as ft
from typing import Any

from cs_ui.core import BaseControl


@ft.control("ListTile")
class ListTile(BaseControl):
    def __init__(
        self,
        title=None,
        subtitle=None,
        leading=None,
        trailing=None,
        on_click=None,
        selected=False,
        selected_color="#1f6feb",
    ):
        super().__init__()
        self.title = title
        self.subtitle = subtitle
        self.leading = leading
        self.trailing = trailing
        self.on_click = on_click
        self.selected = selected
        self.selected_color = selected_color

    def build(self):
        title_control = ft.Text(self.title, weight="bold") if isinstance(self.title, str) else self._build_control(self.title)
        subtitle_control = ft.Text(self.subtitle, size=12, color="#6b7280") if isinstance(self.subtitle, str) else self._build_control(self.subtitle)
        
        leading_control = None
        if self.leading:
            leading_control = self._build_control(self.leading)
        
        trailing_control = None
        if self.trailing:
            trailing_control = self._build_control(self.trailing)

        return ft.ListTile(
            title=title_control,
            subtitle=subtitle_control,
            leading=leading_control,
            trailing=trailing_control,
            on_click=self.on_click,
            selected=self.selected,
            selected_color=self.selected_color,
        )