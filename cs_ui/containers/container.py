from ..core.control import Control


class Container(Control):
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
        super().__init__(width=width, height=height, expand=expand, bgcolor=bgcolor)
        self.content = content
        self.children = []
        self.padding = padding
        self.border_radius = border_radius
        self.alignment = alignment

    def add(self, *controls):
        self.children.extend(controls)

    def _create(self):
        import flet as ft

        if self.content is not None and self.children:
            raise ValueError("Container can hold either content or children, not both")

        content = None
        if self.content is not None:
            content = (
                self.content.build() if hasattr(self.content, "build") else self.content
            )
        elif self.children:
            content = ft.Column(
                controls=[
                    child.build() if hasattr(child, "build") else child
                    for child in self.children
                ],
                spacing=10,
                alignment=self.alignment,
            )

        return ft.Container(
            content=content,
            alignment=self.alignment,
            padding=self.padding,
            border_radius=self.border_radius,
        )
