import flet as ft
from dataclasses import dataclass, field

from ui.core.constants import LayoutType
from ui.input.input import Label

ICON_SIZE = 16
BORDER_RADIUS = 8
DEFAULT_FORM_HEIGHT = 36


@ft.observable
@dataclass
class Checkbox(Label):
    """Single checkbox component."""

    value: bool = False

    def on_change(self, e):
        self.value = e.data if e.data else False

    @ft.component
    def ui(self):
        def _on_change(e):
            self.on_change(e)
            self.notify()  # type: ignore[attr-defined]

        v_ui = ft.Checkbox(
            value=self.value,
            on_change=_on_change,
            check_color=ft.Colors.WHITE,
            active_color=ft.Colors.BLUE,
            border_side=ft.BorderSide(width=1.0, color=ft.Colors.GREY),
        )

        if self.v_label is not None:
            if self.is_vertical:
                return ft.Column(
                    controls=[self.v_label, v_ui],
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                )
            else:
                return ft.Row(controls=[self.v_label, v_ui])
        else:
            return v_ui


@ft.observable
@dataclass
class CheckboxGroup(Label):
    """Multi-select checkbox group with select-all support."""

    value: list[str] = field(default_factory=list)
    options: list[str] = field(default_factory=list)
    checkbox_layout_type: LayoutType = LayoutType.VERTICAL

    def on_change(self, option: str, checked: bool):
        if checked:
            if option not in self.value:
                self.value = [*self.value, option]
        else:
            if option in self.value:
                self.value = [v for v in self.value if v != option]

    def select_all(self, select: bool):
        if select:
            self.value = self.options.copy()
        else:
            self.value = []

    @ft.component
    def ui(self):
        all_selected: bool = (
            len(self.value) == len(self.options) and len(self.options) > 0
        )

        def _on_select_all(e):
            self.select_all(bool(e.data))
            self.notify()  # type: ignore[attr-defined]

        check_all: ft.Checkbox = ft.Checkbox(
            label="全选",
            value=all_selected,
            on_change=_on_select_all,
            check_color=ft.Colors.WHITE,
            active_color=ft.Colors.BLUE,
            border_side=ft.BorderSide(width=1.0, color=ft.Colors.GREY),
        )

        def make_on_change(opt: str):
            def _on_change(e):
                self.on_change(opt, bool(e.data))
                self.notify()  # type: ignore[attr-defined]

            return _on_change

        checkbox_controls: list[ft.Control] = [check_all]

        if self.checkbox_layout_type == LayoutType.HORIZONTAL:
            checkbox_controls.append(ft.Container(width=2, bgcolor=ft.Colors.BLACK))
        else:
            checkbox_controls.append(ft.Divider())

        for option in self.options:
            checkbox_controls.append(
                ft.Checkbox(
                    label=option,
                    value=option in self.value,
                    on_change=make_on_change(option),
                    check_color=ft.Colors.WHITE,
                    active_color=ft.Colors.BLUE,
                    border_side=ft.BorderSide(width=1.0, color=ft.Colors.GREY),
                )
            )

        if self.checkbox_layout_type == LayoutType.HORIZONTAL:
            group_content = ft.Row(
                controls=checkbox_controls,
                spacing=6,
                alignment=ft.MainAxisAlignment.START,
            )
        else:
            group_content = ft.Column(
                controls=checkbox_controls,
                spacing=0,
                alignment=ft.MainAxisAlignment.START,
            )

        v_ui = ft.Container(
            content=group_content,
            padding=ft.Padding.all(0),
        )

        if self.v_label is not None:
            if self.is_vertical:
                return ft.Column(
                    controls=[self.v_label, v_ui],
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                )
            else:
                return ft.Row(controls=[self.v_label, v_ui])
        else:
            return v_ui


@ft.component
def App():
    single = Checkbox(label="同意协议", is_required=True)

    group = CheckboxGroup(
        label="选择兴趣",
        options=["多选1", "多选2", "多选3", "多选4", "多选5"],
        is_required=True,
    )

    group_horizontal = CheckboxGroup(
        label="水平布局",
        options=["选项A", "选项B", "选项C"],
        checkbox_layout_type=LayoutType.HORIZONTAL,
        is_vertical=True,
    )

    return ft.Column(
        controls=[
            single.ui(),
            ft.Divider(),
            group.ui(),
            ft.Divider(),
            group_horizontal.ui(),
            ft.Divider(),
            ft.Button(
                content=ft.Text("打印值"),
                on_click=lambda _: print(
                    f"同意协议: {single.value}, "
                    f"兴趣: {group.value}, "
                    f"布局: {group_horizontal.value}"
                ),
            ),
        ]
    )


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
