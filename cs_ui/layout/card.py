import flet as ft


class Card(ft.Card):
    def __init__(self, bgcolor: str = "#ffffff", elevation: int = 2, **kwargs):
        super().__init__(bgcolor=bgcolor, elevation=elevation, **kwargs)
