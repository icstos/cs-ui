import flet as ft


class AlertDialog(ft.AlertDialog):
    def __init__(self, title_text: str | None = None, content_text: str | None = None,
                 modal: bool = True, **kwargs):
        super().__init__(modal=modal, **kwargs)
        if title_text:
            self.title = ft.Text(title_text, size=20, weight="bold")
        if content_text:
            self.content = ft.Text(content_text)
