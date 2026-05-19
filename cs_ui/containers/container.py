import flet as ft


@ft.control("Container")
class Container(ft.BaseControl):
    def __init__(
        self,
        content=None,
        width=None,
        height=None,
        padding=10,
        bgcolor=None,
        border_radius=0,
        alignment=None,
        expand=False,
    ):
        super().__init__()
        self.content = content
        self.children: list[object] = []
        self.width = width
        self.height = height
        self.padding = padding
        self.bgcolor = bgcolor
        self.border_radius = border_radius
        self.alignment = alignment
        self.expand = expand

    def add(self, *controls):
        self.children.extend(controls)

    def build(self):
        if self.content is not None and self.children:
            raise ValueError("Container can hold either content or children, not both")

        content = None
        if self.content is not None:
            content = self.content
        elif self.children:
            content = ft.Column(
                controls=[child for child in self.children],
                spacing=10,
                alignment=self.alignment,
            )

        return ft.Container(
            content=content,
            alignment=self.alignment,
            padding=self.padding,
            border_radius=self.border_radius,
            width=self.width,
            height=self.height,
            bgcolor=self.bgcolor,
        )


def main(page: ft.Page):
    page.title = "Container Demo"
    page.add(
        Container(
            content=ft.Text("这是一个容器", size=16),
            width=320,
            padding=24,
            bgcolor="#ffffff",
            border_radius=12,
        )
    )


if __name__ == "__main__":
    ft.run(main)
