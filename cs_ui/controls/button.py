import flet as ft
from typing import Any


@ft.control("Button")
class Button(ft.BaseControl):
    def __init__(
        self,
        label: str,
        on_click=None,
        width=None,
        bgcolor: str = "#1f6feb",
        text_color: str = "white",
        disabled: bool = False,
        icon: Any | None = None,
        tooltip: str | None = None,
    ):
        super().__init__()
        self.label = label
        self.on_click = on_click
        self.width = width
        self.bgcolor = bgcolor
        self.text_color = text_color
        self.disabled = disabled
        self.icon = icon
        self.tooltip = tooltip

    def build(self):
        return ft.Button(
            content=ft.Text(self.label, color=self.text_color),
            on_click=self.on_click,
            bgcolor=self.bgcolor,
            disabled=self.disabled,
            icon=self.icon,
            tooltip=self.tooltip,
            width=self.width,
        )


def main(page: ft.Page):
    page.title = "Button Demo"
    page.add(
        Button(
            "点击我",
            width=200,
            on_click=lambda e: page.add(ft.Text("按钮已点击!", color="green")),
        )
    )


if __name__ == "__main__":
    ft.run(main)
