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


def main(page: ft.Page):
    page.title = "Column Demo"
    page.add(
        Column(
            ft.Text("Column 布局示例", size=20, weight="bold"),
            ft.Text("第一项"),
            ft.Text("第二项"),
            spacing=12,
        )
    )


if __name__ == "__main__":
    ft.run(main)
