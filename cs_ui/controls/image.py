import flet as ft


@ft.control("Image")
class Image(ft.BaseControl):
    def __init__(self, src: str, width=None, height=None, fit=None, border_radius=0):
        super().__init__()
        self.src = src
        self.width = width
        self.height = height
        self.fit = fit
        self.border_radius = border_radius

    def build(self):
        return ft.Image(
            src=self.src,
            width=self.width,
            height=self.height,
            fit=self.fit,
            border_radius=self.border_radius,
        )


def main(page: ft.Page):
    page.title = "Image Demo"
    page.add(
        Image(
            src="https://via.placeholder.com/240",
            width=240,
            height=240,
            border_radius=12,
        )
    )


if __name__ == "__main__":
    ft.run(main)
