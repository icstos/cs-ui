import flet as ft
from collections.abc import Sequence
from typing import Any

from cs_ui.core import BaseControl


@ft.control("NavigationBar")
class NavigationBar(BaseControl):
    def __init__(
        self,
        destinations=None,
        selected_index=0,
        on_change=None,
        bgcolor="#ffffff",
        height=60,
        elevation=4,
    ):
        super().__init__()
        self.destinations = destinations or []
        self.selected_index = selected_index
        self.on_change = on_change
        self.bgcolor = bgcolor
        self.height = height
        self.elevation = elevation

    def build(self):
        ft_destinations = []
        for dest in self.destinations:
            if isinstance(dest, tuple):
                icon, label = dest
            else:
                icon, label = dest, str(dest)
            
            icon_arg = None
            if isinstance(icon, str):
                icon_arg = getattr(ft.icons, icon.upper(), None)
                if icon_arg is None:
                    icon_arg = ft.Icon(icon)
            else:
                icon_arg = icon
            
            ft_destinations.append(ft.NavigationDestination(icon=icon_arg, label=label))

        return ft.NavigationBar(
            destinations=ft_destinations,
            selected_index=self.selected_index,
            on_change=self.on_change,
            bgcolor=self.bgcolor,
            height=self.height,
            elevation=self.elevation,
        )