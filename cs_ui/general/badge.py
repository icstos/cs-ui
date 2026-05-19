import flet as ft

from cs_ui.core import BaseControl


@ft.control("Badge")
class Badge(BaseControl):
    def __init__(
        self,
        content=None,
        value=None,
        max_value=99,
        color="#f53f3f",
        text_color="white",
        size="small",
    ):
        super().__init__()
        self.content = content
        self.value = value
        self.max_value = max_value
        self.color = color
        self.text_color = text_color
        self.size = size

    def build(self):
        badge_content = None
        if self.value is not None:
            display_value = f"{self.max_value}+" if self.value > self.max_value else str(self.value)
            badge_content = ft.Text(
                display_value,
                size=11 if self.size == "small" else 12,
                color=self.text_color,
            )

        return ft.Badge(
            content=self._build_control(self.content) if self.content else None,
            badge_content=badge_content,
            color=self.color,
        )