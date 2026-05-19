from cs_ui.core.control import Control


class ProgressBar(Control):
    def __init__(
        self, value: float = 0.0, width=None, bgcolor=None, color=None, height=None
    ):
        super().__init__()
        self.value = value
        self.width = width
        self.bgcolor = bgcolor
        self.color = color
        self.height = height

    def build(self):
        import flet as ft

        value = min(self.value / 100.0, 1.0) if self.value > 1 else self.value

        return ft.ProgressBar(
            value=value,
            width=self.width,
            bgcolor=self.bgcolor,
            color=self.color,
            height=self.height,
        )
