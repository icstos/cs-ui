import flet as ft

from cs_ui.core import BaseControl


@ft.control("SnackBar")
class SnackBar(BaseControl):
    def __init__(
        self,
        content,
        action=None,
        action_color="#1f6feb",
        bgcolor="#1f2937",
        duration=3000,
    ):
        super().__init__()
        self.content = content
        self.action = action
        self.action_color = action_color
        self.bgcolor = bgcolor
        self.duration = duration

    def build(self):
        content_control = ft.Text(self.content) if isinstance(self.content, str) else self._build_control(self.content)
        
        return ft.SnackBar(
            content=content_control,
            action=self.action,
            action_color=self.action_color,
            bgcolor=self.bgcolor,
            duration=self.duration,
        )