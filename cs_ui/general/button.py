import flet as ft


class Button(ft.Button):
    def __init__(self, label: str = "", bgcolor: str = "#1f6feb", **kwargs):
        super().__init__(bgcolor=bgcolor, **kwargs)
        if label:
            self.content = ft.Text(label, color="white")
