import flet as ft

from cs_ui.core import BaseControl


@ft.control("Tooltip")
class Tooltip(BaseControl):
    def __init__(self, content, message, position="bottom"):
        super().__init__()
        self.content = content
        self.message = message
        self.position = position

    def build(self):
        position_map = {
            "top": ft.TooltipPosition.TOP,
            "bottom": ft.TooltipPosition.BOTTOM,
            "left": ft.TooltipPosition.LEFT,
            "right": ft.TooltipPosition.RIGHT,
        }
        
        return ft.Tooltip(
            content=self._build_control(self.content),
            message=self.message,
            position=position_map.get(self.position, ft.TooltipPosition.BOTTOM),
        )