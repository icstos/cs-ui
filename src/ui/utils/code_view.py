import flet as ft
from ui.layout.expander import Expander
from ui.display.text import Code


@ft.control
class CodeView(ft.Column):
    def init(self, code: str, **kwargs):
        self.code = code
        self.controls.append(eval(self.code))
        self.controls.append(
            Expander(title="查看代码", controls=[Code(value=self.code)], dense=True)
        )
