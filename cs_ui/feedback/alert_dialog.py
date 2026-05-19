import flet as ft

from cs_ui.core import BaseControl


@ft.control("AlertDialog")
class AlertDialog(BaseControl):
    def __init__(
        self,
        title=None,
        content=None,
        actions=None,
        actions_alignment="end",
        on_dismiss=None,
        modal=True,
    ):
        super().__init__()
        self.title = title
        self.content = content
        self.actions = actions or []
        self.actions_alignment = actions_alignment
        self.on_dismiss = on_dismiss
        self.modal = modal

    def build(self):
        title_control = ft.Text(self.title, size=20, weight="bold") if isinstance(self.title, str) else self._build_control(self.title)
        content_control = ft.Text(self.content) if isinstance(self.content, str) else self._build_control(self.content)
        actions_controls = [self._build_control(action) for action in self.actions]

        alignment_map = {
            "start": ft.MainAxisAlignment.START,
            "center": ft.MainAxisAlignment.CENTER,
            "end": ft.MainAxisAlignment.END,
        }

        return ft.AlertDialog(
            title=title_control,
            content=content_control,
            actions=actions_controls,
            actions_alignment=alignment_map.get(self.actions_alignment, ft.MainAxisAlignment.END),
            on_dismiss=self.on_dismiss,
            modal=self.modal,
        )