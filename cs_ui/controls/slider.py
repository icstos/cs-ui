from cs_ui.core.control import Control


class Slider(Control):
    def __init__(
        self,
        value: float = 0.0,
        min_value: float = 0.0,
        max_value: float = 1.0,
        divisions: int | None = None,
        label: str | None = None,
        width=None,
        on_change=None,
    ):
        super().__init__(width=width)
        self.value = value
        self.min_value = min_value
        self.max_value = max_value
        self.divisions = divisions
        self.label = label
        self.on_change = on_change

    def _create(self):
        import flet as ft

        return ft.Slider(
            value=self.value,
            min=self.min_value,
            max=self.max_value,
            divisions=self.divisions,
            label=self.label,
            on_change=self._handle_change,
        )

    def _handle_change(self, event):
        if callable(self.on_change):
            self.on_change(event)
