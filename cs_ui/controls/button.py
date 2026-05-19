from cs_ui.core.control import Control


class Button(Control):
    def __init__(
        self,
        label: str,
        on_click=None,
        width=None,
        bgcolor: str = "#1f6feb",
        text_color: str = "white",
        disabled: bool = False,
        icon=None,
        tooltip=None,
    ):
        super().__init__(width=width, bgcolor=bgcolor)
        self.label = label
        self.on_click = on_click
        self.text_color = text_color
        self.disabled = disabled
        self.icon = icon
        self.tooltip = tooltip

    def _create(self):
        import flet as ft

        return ft.ElevatedButton(
            content=ft.Text(self.label, color=self.text_color),
            on_click=self._handle_click,
            bgcolor=self.bgcolor,
            disabled=self.disabled,
            icon=self.icon,
            tooltip=self.tooltip,
            width=self.width,
        )

    def _handle_click(self, event):
        if callable(self.on_click):
            self.on_click(event)
