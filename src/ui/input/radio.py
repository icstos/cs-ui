import flet as ft
from dataclasses import dataclass, field
from ui.core.constants import LayoutType
from ui.input.input import Label

ICON_SIZE = 16
BORDER_RADIUS = 8
DEFAULT_FORM_HEIGHT = 36


@ft.observable
@dataclass
class Radio(Label):
    value: str | None = None
    options: list[str | ft.Radio] = field(default_factory=list)
    radio_layout_type: LayoutType = LayoutType.HORIZONTAL

    def on_change(self, e):
        self.value = e.data if e.data else None

    @ft.component
    def ui(self):
        radio_controls = []
        for option in self.options:
            if isinstance(option, str):
                radio_controls.append(
                    ft.Radio(
                        label=option,
                        value=option,
                        label_position=ft.LabelPosition.RIGHT,
                        active_color=ft.Colors.BLUE,
                    )
                )
            else:
                radio_controls.append(option)

        if self.radio_layout_type == LayoutType.HORIZONTAL:
            radio_content = ft.Row(
                controls=radio_controls,
                spacing=self.spacing,
                run_spacing=self.run_spacing,
            )
        else:
            radio_content = ft.Column(
                controls=radio_controls,
                spacing=2,
                run_spacing=10,
            )

        def _on_change(e):
            self.on_change(e)
            self.notify()

        v_ui = ft.RadioGroup(
            value=self.value,
            content=radio_content,
            on_change=_on_change,
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
    radio = Radio(
        label="选择选项",
        options=["aa", "bb", "cc"],
        is_required=True,
    )

    return ft.Column(
        controls=[
            radio.ui(),
            Radio(
                label="布局方向",
                options=["水平", "垂直"],
                radio_layout_type=LayoutType.VERTICAL,
                is_vertical=True,
            ).ui(),
            ft.Button(
                content=ft.Text("打印值"),
                on_click=lambda _: print(f"当前值: {radio.value}"),
            ),
        ]
    )


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
