import flet as ft

from cs_ui.containers.container import Container


@ft.control("Container")
class Card(Container):
    def __init__(
        self,
        content=None,
        width=None,
        height=None,
        padding=20,
        bgcolor="#ffffff",
        border_radius=16,
        elevation: int = 2,
        alignment=None,
        expand=False,
    ):
        super().__init__(
            content=content,
            width=width,
            height=height,
            padding=padding,
            bgcolor=bgcolor,
            border_radius=border_radius,
            alignment=alignment,
            expand=expand,
        )
        self.elevation = elevation

    def build(self):
        return ft.Container(
            content=super().build().content,
            alignment=self.alignment,
            padding=self.padding,
            border_radius=self.border_radius,
            width=self.width,
            height=self.height,
            bgcolor=self.bgcolor,
        )


def main(page: ft.Page):
    page.title = "Card Demo"
    page.add(
        Card(
            content=ft.Text("Card 组件示例", size=16),
            width=320,
            padding=24,
            bgcolor="#ffffff",
            border_radius=16,
            elevation=4,
        )
    )


if __name__ == "__main__":
    ft.run(main)
