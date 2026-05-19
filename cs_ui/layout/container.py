import flet as ft

from cs_ui.core import BaseControl


@ft.control("Container")
class Container(BaseControl):
    def __init__(
        self,
        content=None,
        width=None,
        height=None,
        padding=10,
        bgcolor=None,
        border_radius=0,
        alignment=None,
        expand=False,
    ):
        super().__init__()
        self.content = content
        self.children: list[object] = []
        self.width = width
        self.height = height
        self.padding = padding
        self.bgcolor = bgcolor
        self.border_radius = border_radius
        self.alignment = alignment
        self.expand = expand

    def add(self, *controls):
        self.children.extend(controls)

    def build(self):
        if self.content is not None and self.children:
            raise ValueError("Container can hold either content or children, not both")

        content = None
        if self.content is not None:
            content = self._build_control(self.content)
        elif self.children:
            content = ft.Column(
                controls=self._build_controls(self.children),
                spacing=10,
                alignment=self.alignment,
            )

        return ft.Container(
            content=content,
            alignment=self.alignment,
            padding=self.padding,
            border_radius=self.border_radius,
            width=self.width,
            height=self.height,
            bgcolor=self.bgcolor,
        )