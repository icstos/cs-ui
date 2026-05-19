import flet as ft

from cs_ui.core import BaseControl


@ft.control("Column")
class Column(BaseControl):
    def __init__(self, *children, alignment=None, spacing=10):
        super().__init__()
        self.children = list(children)
        self.alignment = alignment
        self.spacing = spacing

    def add(self, *controls):
        self.children.extend(controls)

    def build(self):
        return ft.Column(
            controls=self._build_controls(self.children),
            alignment=self.alignment,
            spacing=self.spacing,
        )