import flet as ft


@ft.control("Column")
class Column(ft.BaseControl):
    def __init__(self, *children, alignment=None, spacing=10):
        super().__init__()
        self.children = list(children)
        self.alignment = alignment
        self.spacing = spacing

    def add(self, *controls):
        self.children.extend(controls)

    def build(self):
        return ft.Column(
            controls=[child for child in self.children],
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
