import flet as ft

from cs_ui.core import BaseControl


@ft.control("Divider")
class Divider(BaseControl):
    def __init__(self, height=1, color="#e5e7eb", thickness=1, indent=0, end_indent=0):
        super().__init__()
        self.height = height
        self.color = color
        self.thickness = thickness
        self.indent = indent
        self.end_indent = end_indent

    def build(self):
        return ft.Divider(
            height=self.height,
            color=self.color,
            thickness=self.thickness,
            indent=self.indent,
            end_indent=self.end_indent,
        )