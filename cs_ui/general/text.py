import flet as ft

from cs_ui.core import BaseControl


@ft.control("Text")
class Text(BaseControl):
    def __init__(
        self,
        value: str,
        size: int = 16,
        color: str = "#0f172a",
        weight=None,
        text_align=None,
        italic: bool = False,
        selectable: bool = False,
        max_lines: int | None = None,
    ):
        super().__init__()
        self.value = value
        self.size = size
        self.color = color
        self.weight = weight
        self.text_align = text_align
        self.italic = italic
        self.selectable = selectable
        self.max_lines = max_lines

    def build(self):
        return ft.Text(
            self.value,
            size=self.size,
            color=self.color,
            weight=self.weight,
            italic=self.italic,
            text_align=self.text_align,
            selectable=self.selectable,
            max_lines=self.max_lines,
        )