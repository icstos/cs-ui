import flet as ft


@ft.control("ProgressBar")
class ProgressBar(ft.BaseControl):
    def __init__(
        self, value: float = 0.0, width=None, bgcolor=None, color=None, height=None
    ):
        super().__init__()
        self.value = value
        self.width = width
        self.bgcolor = bgcolor
        self.color = color
        self.height = height

    def build(self):
        value = min(self.value / 100.0, 1.0) if self.value > 1 else self.value
        return ft.ProgressBar(
            value=value,
            width=self.width,
            bgcolor=self.bgcolor,
            color=self.color,
            height=self.height,
        )


def main(page: ft.Page):
    page.title = "ProgressBar Demo"
    page.add(
        ProgressBar(value=45, width=320, color="#4caf50", bgcolor="#e0e0e0", height=16)
    )


if __name__ == "__main__":
    ft.run(main)
