from cs_ui.core.control import Control


class Checkbox(Control):
    def __init__(
        self,
        label: str = "",
        value: bool = False,
        on_change=None,
        disabled: bool = False,
    ):
        super().__init__()
        self.label = label
        self.value = value
        self.on_change = on_change
        self.disabled = disabled

    def build(self):
        import flet as ft

        return ft.Checkbox(
            label=self.label,
            value=self.value,
            on_change=self._handle_change,
            disabled=self.disabled,
        )

    def _handle_change(self, event):
        if callable(self.on_change):
            self.on_change(event)
