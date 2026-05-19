import flet as ft


class Badge(ft.Badge):
    def __init__(self, badge_value: int | None = None, max_value: int = 99,
                 badge_color: str = "#f53f3f", badge_text_color: str = "white", **kwargs):
        super().__init__(bgcolor=badge_color, **kwargs)
        if badge_value is not None:
            display = f"{max_value}+" if badge_value > max_value else str(badge_value)
            self.label = ft.Text(display, size=11, color=badge_text_color)
