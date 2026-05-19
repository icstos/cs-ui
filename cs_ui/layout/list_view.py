import flet as ft

from cs_ui.core import BaseControl


@ft.control("ListView")
class ListView(BaseControl):
    def __init__(
        self,
        *children,
        spacing=10,
        padding=10,
        auto_scroll=False,
        reverse=False,
        expand=False,
    ):
        super().__init__()
        self.children = list(children)
        self.spacing = spacing
        self.padding = padding
        self.auto_scroll = auto_scroll
        self.reverse = reverse
        self.expand = expand

    def add(self, *controls):
        self.children.extend(controls)

    def build(self):
        return ft.ListView(
            controls=self._build_controls(self.children),
            spacing=self.spacing,
            padding=self.padding,
            auto_scroll=self.auto_scroll,
            reverse=self.reverse,
            expand=self.expand,
        )