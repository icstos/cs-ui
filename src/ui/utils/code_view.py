import flet as ft
from ui.layout.expander import Expander
from ui.display.text import Code


@ft.control
class CodeView(ft.Column):
    code: str = ""
    component: ft.Control | None = None

    def init(self):
        self.controls.append(
            Expander(title="查看代码", controls=[Code(value=self.code)], dense=True)
        )

    def did_mount(self):
        if self.component is not None:
            self.controls.insert(0, self.component)
