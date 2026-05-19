import flet as ft


class SnackBar(ft.SnackBar):
    def __init__(self, message: str = "", **kwargs):
        super().__init__(**kwargs)
        if message:
            self.content = ft.Text(message)
