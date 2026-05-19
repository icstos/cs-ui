import flet as ft
from typing import Any

from cs_ui.core import BaseControl


@ft.control("IconButton")
class IconButton(BaseControl):
    def __init__(
        self,
        icon: Any | None = None,
        content: Any | None = None,
        on_click=None,
        tooltip: str | None = None,
        width=None,
        height=None,
    ):
        super().__init__()
        self.icon = icon
        self.content = content
        self.on_click = on_click
        self.tooltip = tooltip
        self.width = width
        self.height = height

    def build(self):
        icon_arg = None
        if isinstance(self.icon, str):
            icon_arg = getattr(ft.icons, self.icon.upper(), None)
            if icon_arg is None:
                icon_arg = ft.Icon(self.icon)
        else:
            icon_arg = self.icon

        if icon_arg is None and self.content is not None:
            icon_arg = (
                ft.Text(self.content) if isinstance(self.content, str) else self.content
            )

        kwargs = {
            "tooltip": self.tooltip,
            "on_click": self.on_click,
            "width": self.width,
            "height": self.height,
        }
        if icon_arg is not None:
            kwargs["icon"] = icon_arg

        return ft.IconButton(**kwargs)