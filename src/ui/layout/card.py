import flet as ft


@ft.control
class Card(ft.Card):
    def init(self):
        self.container = ft.Container(
            width=self.width,
            height=self.height,
            bgcolor=ft.Colors.WHITE,
            on_hover=lambda e: self.on_content_hover(e),
            animate=ft.Animation(600, ft.AnimationCurve.EASE),
            border=ft.Border.all(2, ft.Colors.WHITE_24),
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.START,
                spacing=0,
                controls=[self.content],
            ),
            border_radius=ft.BorderRadius.all(8),
        )
        self.content = ft.Container(
            content=ft.Column(
                spacing=0,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[self.container],
            )
        )

    def on_content_hover(self, e):
        if e.data:
            if self.elevation is not None:
                self.elevation = self.elevation + 20

            self.container.border = ft.Border.all(2, ft.Colors.BLUE)
            self.container.update()
        else:
            if self.elevation is not None:
                self.elevation = self.elevation - 20

            self.container.border = ft.Border.all(2, ft.Colors.WHITE_24)
            self.container.update()
        self.update()


def main(page: ft.Page):
    page.add(Card(width=200, height=100, content=ft.Text("Hello, Card!")))


if __name__ == "__main__":
    ft.run(main)
