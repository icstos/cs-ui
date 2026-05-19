import flet as ft

from .container import Container


@ft.control("Card")
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
        return ft.Card(
            content=super().build(),
            elevation=self.elevation,
        )