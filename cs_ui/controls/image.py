from ..core.control import Control


class Image(Control):
    def __init__(self, src: str, width=None, height=None, fit=None, border_radius=0):
        super().__init__()
        self.src = src
        self.width = width
        self.height = height
        self.fit = fit
        self.border_radius = border_radius

    def build(self):
        import flet as ft

        return ft.Image(
            src=self.src,
            width=self.width,
            height=self.height,
            fit=self.fit,
            border_radius=self.border_radius,
        )
