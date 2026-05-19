from cs_ui.core.control import Control


class Column(Control):
    def __init__(self, *children, alignment=None, spacing=10):
        super().__init__()
        self.children = list(children)
        self.alignment = alignment
        self.spacing = spacing

    def add(self, *controls):
        self.children.extend(controls)

    def _create(self):
        import flet as ft

        return ft.Column(
            controls=[Control._build_child(child) for child in self.children],
            alignment=self.alignment,
            spacing=self.spacing,
        )
