import flet as ft
from dataclasses import field

from rich import color

from ui.core.constants import LayoutType


@ft.control
class Checkbox(ft.Checkbox):
    check_color: ft.Colors = ft.Colors.WHITE
    active_color: ft.Colors = ft.Colors.BLUE
    border_side: ft.BorderSide = field(
        default_factory=lambda: ft.BorderSide(width=1.0, color=ft.Colors.GREY)
    )


@ft.control
class CheckboxGroup(ft.Container):
    options: list[str] = field(default_factory=list)
    layout_type: LayoutType = LayoutType.VERTICAL

    def init(self):
        self.selected = []
        self.check_all = Checkbox(label='全选', on_change=self.select_all)
        self.v_controls: list[ft.Control] = [self.check_all]

        if self.layout_type == LayoutType.VERTICAL:
            self.v_controls.append(ft.Divider())
            self.content = ft.Column(
                self.v_controls, spacing=0, alignment=ft.MainAxisAlignment.START
            )
        else:
            self.height = 32
            self.v_controls.append(ft.Container(width=2, bgcolor=ft.Colors.BLACK))
            self.content = ft.Row(
                self.v_controls, spacing=6, alignment=ft.MainAxisAlignment.START
            )
        for option in self.options:
            self.v_controls.append(Checkbox(label=option, on_change=self.change_single))
        self.tight = True
        self.padding = ft.Padding.all(0)

    @property
    def value(self) -> list[str]:
        return self.selected

    def change_single(self, e):
        val = e.control.label
        if e.data:
            if val not in self.selected:
                self.selected.append(val)
        else:
            if val in self.selected:
                self.selected.remove(val)
        self.check_all.value = len(self.selected) == len(self.options)

    def select_all(self, e):
        self.check_all.tristate = False
        val = self.check_all.value
        for i in range(2, len(self.v_controls)):
            self.v_controls[i].value = val
        self.selected = self.options.copy() if val else []


def main(page: ft.Page):
    aa = Checkbox()
    page.add(aa)
    print(isinstance(aa, ft.Checkbox))
    page.add(CheckboxGroup(options=['多选1', '多选2', '多选3', '多选4', '多选5']))
    page.add(
        CheckboxGroup(
            options=['多选1', '多选2', '多选3', '多选4', '多选5'],
            layout_type=LayoutType.HORIZONTAL,
        )
    )


if __name__ == "__main__":
    ft.run(main)
