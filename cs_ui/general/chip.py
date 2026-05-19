import flet as ft


class Chip(ft.Chip):
    def __init__(self, label_text: str = "", **kwargs):
        super().__init__(label=ft.Text(label_text) if label_text else ft.Text(""), **kwargs)
