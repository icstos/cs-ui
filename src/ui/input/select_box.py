from collections.abc import Callable
from dataclasses import dataclass, field

import flet as ft

from ui.core.styles import INPUT_RADIUS, outline_input
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
    #: 是否铺底色。默认 False —— 与 :class:`~ui.input.input.Input`、
    #: ``MultiSelect`` 一样走"描边 + 透明底"，一排表单里不会出现一个灰块。
    filled: bool = False
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
            # 以前是 bgcolor=GREY_200 + 同色描边：固定色值不跟主题，暗色下
            # 直接变成一块亮灰。描边走角色，明暗都由 Flutter 解析。
            border=outline_input(
                INPUT_RADIUS, ft.Colors.OUTLINE_VARIANT, ft.Colors.PRIMARY
            ),
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
        options=["Option 1", "Option 2", "Option 3"],
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
