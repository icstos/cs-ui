import flet as ft
from typing import Any

from cs_ui.core import BaseControl


@ft.control("AppBar")
class AppBar(BaseControl):
    def __init__(
        self,
        title=None,
        leading=None,
        leading_width=56,
        actions=None,
        bgcolor="#ffffff",
        color="#1f2937",
        elevation=4,
    ):
        super().__init__()
        self.title = title
        self.leading = leading
        self.leading_width = leading_width
        self.actions = actions or []
        self.bgcolor = bgcolor
        self.color = color
        self.elevation = elevation

    def build(self):
        title_control = None
        if isinstance(self.title, str):
            title_control = ft.Text(self.title, size=20, weight="bold", color=self.color)
        elif self.title:
            title_control = self._build_control(self.title)

        leading_control = None
        if self.leading:
            leading_control = self._build_control(self.leading)

        actions_controls = [self._build_control(action) for action in self.actions]

        return ft.AppBar(
            title=title_control,
            leading=leading_control,
            leading_width=self.leading_width,
            actions=actions_controls,
            bgcolor=self.bgcolor,
            color=self.color,
            elevation=self.elevation,
        )