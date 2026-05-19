import flet as ft


@ft.control("Row")
class Row(ft.BaseControl):
    def __init__(self, *children, alignment=None, spacing=10):
        super().__init__()
        self.children = list(children)
        self.alignment = alignment
        self.spacing = spacing

    def add(self, *controls):
        self.children.extend(controls)

    def build(self):
        return ft.Row(
            controls=[child for child in self.children],
            alignment=self.alignment,
            spacing=self.spacing,
        )


def main(page: ft.Page):
    page.title = "Row Demo"
    page.add(Row(ft.Text("第一项"), ft.Text("第二项"), ft.Text("第三项"), spacing=20))


if __name__ == "__main__":
    ft.run(main)
