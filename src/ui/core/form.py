from dataclasses import field
from pathlib import Path

import flet as ft
from ui.core.constants import LayoutType, FormValueType, DEFAULT_FORM_HEIGHT


@ft.control
class Label(ft.Text):
    is_required: bool = False
    height: int = DEFAULT_FORM_HEIGHT
    size: int = 16
    spacing: int = 0
    alignment: ft.MainAxisAlignment = ft.MainAxisAlignment.END

    def init(self):
        if (
            self.value is not None
            and (not self.value.endswith(":"))
            and (not self.value.endswith("："))
        ):
            self.value = self.value + "："
        if self.is_required:
            self.spans = [
                ft.TextSpan(text="*", style=ft.TextStyle(color=ft.Colors.RED)),
                ft.TextSpan(self.value),
            ]
        else:
            self.spans = [ft.TextSpan(text=self.value)]
        # TODO: value 与 spans 同时存在时，都会显示
        self.value = ""


@ft.control
class FormField(ft.Row):
    label: str = ""
    label_width: int | None = None
    content: ft.Control = field(default=ft.Text("占位内容"))
    is_required: bool = False
    spacing: ft.Number = 10
    run_spacing: ft.Number = 10
    tight: bool = False
    wrap: bool = False
    layout_type: LayoutType = LayoutType.HORIZONTAL
    run_alignment: ft.MainAxisAlignment = ft.MainAxisAlignment.START
    alignment: ft.MainAxisAlignment = ft.MainAxisAlignment.START
    vertical_alignment: ft.CrossAxisAlignment = ft.CrossAxisAlignment.CENTER

    def init(self):
        self.v_label = Label(
            value=self.label, is_required=self.is_required, width=self.label_width
        )
        if self.layout_type == LayoutType.HORIZONTAL:
            self.v_label.text_align = ft.TextAlign.END
            self.controls = [self.v_label, self.content]
        elif self.layout_type == LayoutType.VERTICAL:
            self.v_label.text_align = ft.TextAlign.START
            self.controls = [
                ft.Column(
                    controls=[self.v_label, self.content],
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                )
            ]

    @property
    def value(self):
        tmp_value = self.content.__dict__.get("_values", {}).get("value", None)
        if hasattr(self.content, "form_value_type") and tmp_value is not None:
            if self.content.form_value_type == FormValueType.INT:
                return int(tmp_value)
            elif self.content.form_value_type == FormValueType.FLOAT:
                return float(tmp_value)
            elif (
                self.content.form_value_type == FormValueType.FILE
                or self.content.form_value_type == FormValueType.DIR
            ):
                return Path(tmp_value.strip().strip('"').strip("'"))
            elif self.content.form_value_type == FormValueType.STR:
                return str(tmp_value)
            elif self.content.form_value_type == FormValueType.BOOL:
                return bool(tmp_value)
            else:
                return tmp_value
        else:
            return tmp_value

    @value.setter
    def value(self, value):
        self.content.value = value

    @property
    def path(self) -> Path | None:
        try:
            path_str = self.content.value.strip().strip('"').strip("'")
            if len(path_str) == 0:
                return None
            return Path(path_str)
        except Exception:
            return None


def main(page: ft.Page):
    import ui

    form_field_1 = FormField(
        label="Hello, world!",
        content=ui.Input(value="Hello, world!"),
        width=200,
        is_required=True,
    )
    form_field = FormField(
        label="Hello, world!",
        content=ui.Input(value="Hello, world!"),
        width=200,
        layout_type=LayoutType.VERTICAL,
    )
    page.add(form_field_1)
    page.add(form_field)
    page.add(ui.Button(content='查看值', on_click=lambda e: print(form_field.value)))


if __name__ == "__main__":
    ft.run(main)
