from typing import Optional, Any

from cs_ui.core.control import Control


class IconButton(Control):
    def __init__(
        self,
        icon: Optional[Any] = None,
        content: Optional[Any] = None,
        on_click=None,
        tooltip: Optional[str] = None,
        width=None,
        height=None,
    ):
        super().__init__(width=width, height=height)
        self.icon = icon
        self.content = content
        self.on_click = on_click
        self.tooltip = tooltip

    def _create(self):
        import flet as ft

        icon_arg = None
        # normalize string icon names to ft.icons constants or ft.Icon
        if isinstance(self.icon, str):
            try:
                icon_arg = getattr(ft.icons, self.icon.upper())
            except Exception:
                icon_arg = ft.Icon(self.icon)
        else:
            icon_arg = self.icon

        kwargs = {
            "tooltip": self.tooltip,
            "on_click": self._handle_click,
            "width": self.width,
            "height": self.height,
        }

        if icon_arg is not None:
            kwargs["icon"] = icon_arg
        elif self.content is not None:
            # IconButton doesn't accept a `content` kwarg; map visible content
            # into the `icon` parameter as a control so it's displayed.
            if isinstance(self.content, str):
                kwargs["icon"] = ft.Text(self.content)
            else:
                kwargs["icon"] = self.content

        return ft.IconButton(**kwargs)

    def _handle_click(self, event):
        if callable(self.on_click):
            self.on_click(event)
