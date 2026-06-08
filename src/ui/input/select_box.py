import flet as ft
from dataclasses import dataclass, field
from collections.abc import Callable
from ui.input.input import Label

ICON_SIZE = 18
TEXT_SIZE = 14
PADDING = 10
INPUT_HEIGHT = 42


@ft.control
class SelectOption(ft.dropdownm2.Option):
    pass


@ft.observable
@dataclass
class SelectBox(Label):
    value: str | None = None
    options: list[str | ft.dropdownm2.Option] = field(default_factory=list)
    dense: bool = True
    filled: bool = True
    editable: bool = True
    on_change: Callable | None = None

    def _on_change(self, e):
        self.value = e.data if e.data else None

    @ft.component
    def ui(self):
        dropdown_options: list[ft.dropdownm2.Option] = []
        for option in self.options:
            if isinstance(option, str):
                dropdown_options.append(ft.dropdownm2.Option(text=option))
            elif isinstance(option, ft.dropdownm2.Option):
                dropdown_options.append(option)
            else:
                # fallback: coerce to string
                dropdown_options.append(ft.dropdownm2.Option(text=str(option)))

        def _on_select(e):
            self._on_change(e)
            if self.on_change:
                self.on_change(e)
            self.notify()

        v_ui = ft.DropdownM2(
            value=self.value,
            options=dropdown_options,
            # dense=True,
            filled=self.filled,
            # editable=self.editable,
            content_padding=ft.Padding.only(left=PADDING),
            border_color=ft.Colors.GREY_200,
            bgcolor=ft.Colors.GREY_200,
            border_width=1,
            border_radius=6,
            focused_border_color=ft.Colors.BLUE,
            on_change=_on_select,
            height=INPUT_HEIGHT,
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

    select = SelectBox(
        label="选择选项",
        options=['Option 1', 'Option 2', 'Option 3'],
        is_required=True,
    )

    return ft.Column(
        controls=[
            select.ui(),
            SelectBox(
                label="布局方向",
                options=["水平", "垂直"],
                is_vertical=True,
            ).ui(),
            ft.Button(
                content=ft.Text("打印值"),
                on_click=lambda _: print(f"当前值: {select.value}"),
            ),
        ]
    )


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
