from ..core.control import Control


class Switch(Control):
    def __init__(
        self, label: str = "", value: bool = False, on_change=None, active_color=None
    ):
        super().__init__()
        self.label = label
        self.value = value
        self.on_change = on_change
        self.active_color = active_color

    def build(self):
        import flet as ft

        return ft.Switch(
            label=self.label,
            value=self.value,
            on_change=self._handle_change,
            active_color=self.active_color,
        )

    def _handle_change(self, event):
        if callable(self.on_change):
            self.on_change(event)
