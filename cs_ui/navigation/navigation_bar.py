import flet as ft
from typing import Any

from cs_ui.core import resolve_icon


class NavigationBar(ft.NavigationBar):
    def __init__(self, destinations_config: list | None = None, **kwargs):
        super().__init__(**kwargs)
        for dest in (destinations_config or []):
            icon, label = dest if isinstance(dest, tuple) else (dest, str(dest))
            self.destinations.append(
                ft.NavigationDestination(icon=resolve_icon(icon), label=label)
            )
