import flet as ft

from cs_ui.core import BaseControl


@ft.control("GridView")
class GridView(BaseControl):
    def __init__(
        self,
        *children,
        runs_count=4,
        spacing=10,
        run_spacing=10,
        padding=10,
        alignment=None,
    ):
        super().__init__()
        self.children = list(children)
        self.runs_count = runs_count
        self.spacing = spacing
        self.run_spacing = run_spacing
        self.padding = padding
        self.alignment = alignment

    def add(self, *controls):
        self.children.extend(controls)

    def build(self):
        return ft.GridView(
            controls=self._build_controls(self.children),
            runs_count=self.runs_count,
            spacing=self.spacing,
            run_spacing=self.run_spacing,
            padding=self.padding,
            alignment=self.alignment,
        )