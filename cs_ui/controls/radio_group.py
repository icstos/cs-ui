import flet as ft
from collections.abc import Sequence
from typing import Any


@ft.control("RadioGroup")
class RadioGroup(ft.BaseControl):
    def __init__(
        self,
        label: str | None = None,
        options: Sequence[Any] | None = None,
        value: Any = None,
        on_change=None,
    ):
        super().__init__()
        self.label = label
        self.options = options or []
        self.value = value
        self.on_change = on_change

    def build(self):
        radios = []
        for option in self.options:
            if isinstance(option, tuple):
                val, text = option
            else:
                val, text = option, str(option)
            radios.append(ft.Radio(value=val, label=text))

        controls = []
        if self.label:
            controls.append(ft.Text(self.label, weight="bold", size=14))
        controls.append(
            ft.RadioGroup(content=radios, value=self.value, on_change=self.on_change)
        )
        return ft.Column(controls=controls, spacing=4)


def main(page: ft.Page):
    page.title = "RadioGroup Demo"
    page.add(
        RadioGroup(
            label="请选择",
            options=["选项一", "选项二", "选项三"],
            value="选项一",
            on_change=lambda e: page.add(
                ft.Text(f"选择：{e.control.value}", color="green")
            ),
        )
    )


if __name__ == "__main__":
    ft.run(main)
