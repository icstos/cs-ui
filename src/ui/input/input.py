import flet as ft
from decimal import Decimal
from pathlib import Path
import math
from dataclasses import field
from enum import Enum

from ui.core.constants import FormValueType, DEFAULT_FORM_HEIGHT

ICON_SIZE = 16


@ft.control
class Input(ft.TextField):
    value: int | float | Decimal | str | None = ''
    theme_mode = ft.ThemeMode.LIGHT
    keyboard_type: ft.KeyboardType = ft.KeyboardType.TEXT
    cursor_color: ft.Colors = ft.Colors.BLUE
    focused_border_color: ft.Colors = ft.Colors.BLUE
    selection_color: ft.Colors = ft.Colors.GREY_400
    hover_color: ft.Colors = ft.Colors.BLUE_50
    border_radius: ft.BorderRadius = field(
        default_factory=lambda: ft.BorderRadius.all(7)
    )
    border: ft.InputBorder = ft.InputBorder.OUTLINE
    border_width: int = 1
    cursor_width: int = 1
    filled: bool = True
    height: int = DEFAULT_FORM_HEIGHT
    form_value_type: FormValueType = FormValueType.STR
    # text_align: ft.TextAlign = ft.TextAlign.CENTER

    def init(self):
        if self.prefix and not self.suffix:
            self.content_padding = ft.Padding.only(left=10, right=5)
        elif self.suffix and not self.prefix:
            self.content_padding = ft.Padding.only(left=5, right=10)
        elif self.prefix and self.suffix:
            self.content_padding = ft.Padding.symmetric(horizontal=10)
        else:
            self.content_padding = ft.Padding.all(1)

        self.default_value = self.value

    @property
    def path(self) -> Path | None:
        if self.value is None or len(str(self.value).strip()) == 0:
            return None
        else:
            return Path(str(self.value).strip().strip('"').strip("'"))


@ft.control
class NumberInput(Input):
    value: int | float | Decimal | str = 0
    min_value: ft.Number = -math.inf
    max_value: ft.Number = math.inf
    step: ft.Number = 0.01
    is_int: bool = False
    text_align: ft.TextAlign = ft.TextAlign.CENTER
    form_value_type: FormValueType = FormValueType.FLOAT

    def init(self):
        if isinstance(self.value, int) or self.is_int:
            self.step = 1
            self.is_int = True
            self.form_value_type = FormValueType.INT
        elif isinstance(self.value, float):
            self.step = 0.01
            self.is_int = False
        else:
            raise ValueError('value must be int or float')

        self.v_decrease = ft.Container(
            content=ft.Icon(icon=ft.Icons.REMOVE, size=ICON_SIZE),
            border_radius=ft.BorderRadius(
                top_left=0, top_right=0, bottom_left=0, bottom_right=0
            ),
            on_click=self.handle_decrease_click,
            on_hover=self.handle_hover,
            height=self.height,
            width=30,
            alignment=ft.Alignment.CENTER,
        )
        self.v_increase_icon = ft.Icon(icon=ft.Icons.ADD, size=ICON_SIZE)
        self.v_increase = ft.Container(
            content=self.v_increase_icon,
            border_radius=ft.BorderRadius(
                top_left=0, top_right=8, bottom_left=0, bottom_right=8
            ),
            on_click=self.handle_increase_click,
            on_hover=self.handle_hover,
            height=self.height,
            width=30,
            alignment=ft.Alignment.CENTER,
        )
        self.suffix = ft.Container(
            content=ft.Row(
                controls=[self.v_decrease, self.v_increase],
                alignment=ft.MainAxisAlignment.END,
                vertical_alignment=ft.CrossAxisAlignment.START,
                spacing=0,
                run_spacing=0,
            ),
            width=60,
            alignment=ft.Alignment.CENTER_RIGHT,
            height=self.height,
            # TODO: 不加这个的话背景颜色会偏移
            offset=ft.Offset(x=0.1, y=0.03),
        )
        self.last_value = self.value
        self.content_padding = ft.Padding.only(left=5, right=0, top=0, bottom=10)
        self.text_vertical_align = ft.VerticalAlignment.START

        self.on_change = self._on_change

    def handle_hover(self, e):
        if e.data:
            e.control.content.color = ft.Colors.WHITE
            e.control.bgcolor = ft.Colors.BLUE
        else:
            e.control.content.color = None
            e.control.bgcolor = None
        e.control.update()

    def _on_change(self, e):
        try:
            if isinstance(self.value, str) and self.value.strip() != "":
                __value = float(self.value)
        except ValueError:
            print("NumberInputValueError", self.value, self.last_value)
            self.value = self.last_value
        else:
            self.last_value = self.value
        self.update()
        return super().on_change

    def handle_decrease_click(self, e):
        _value = float(Decimal(str(self.value)) - Decimal(str(self.step)))
        if self.is_int:
            self.value = int(_value)
        else:
            self.value = float(_value)

    def handle_increase_click(self, e):
        _value = float(Decimal(str(self.value)) + Decimal(str(self.step)))
        if self.is_int:
            self.value = int(_value)
        else:
            self.value = float(_value)


@ft.control
class IconContainer(ft.Container):
    width: int = 30
    padding: ft.Padding = field(default_factory=lambda: ft.Padding.all(0))

    def init(self):
        self.on_hover = self.handle_hover
        self.border_radius = ft.BorderRadius(
            top_left=6, top_right=0, bottom_left=6, bottom_right=0
        )

    def handle_hover(self, e):
        if e.data:
            e.control.content.color = ft.Colors.WHITE
            e.control.bgcolor = ft.Colors.BLUE
        else:
            e.control.content.color = None
            e.control.bgcolor = None
        e.control.update()


@ft.control
class FileInput(Input):
    value: str | Path | None = None
    form_value_type: FormValueType = FormValueType.FILE
    content_padding: ft.Padding = field(
        default_factory=lambda: ft.Padding.only(left=5, right=10, top=0, bottom=0)
    )

    def init(self):
        self.v_file_picker = ft.FilePicker()
        self.prefix_icon = IconContainer(
            content=ft.Icon(icon=ft.Icons.FILE_OPEN_OUTLINED, size=ICON_SIZE),
            on_click=self.handle_file_picker,
        )

    async def handle_file_picker(self, e):
        self.selected_files = await self.v_file_picker.pick_files(allow_multiple=False)
        if self.selected_files is not None and len(self.selected_files) > 0:
            self.value = str(self.selected_files[0].path)
            if self.on_change:
                self.on_change(e)


@ft.control
class DirInput(FileInput):
    value: str | Path | None = None
    form_value_type: FormValueType = FormValueType.DIR

    def init(self):
        self.v_file_picker = ft.FilePicker()
        self.prefix_icon = IconContainer(
            content=ft.Icon(icon=ft.Icons.FOLDER_OPEN_OUTLINED, size=ICON_SIZE),
            on_click=self.handle_file_picker,
            alignment=ft.Alignment.CENTER,
        )

    async def handle_file_picker(self, e):
        self.seleted_dir = await self.v_file_picker.get_directory_path()
        if self.seleted_dir is not None:
            self.value = str(self.seleted_dir)
            if self.on_change:
                self.on_change(e)


def main(page: ft.Page):
    page.add(Input(value="123"))
    page.add(NumberInput(value=123))
    page.add(FileInput())
    dir_input = DirInput()
    page.add(dir_input)
    print(isinstance(dir_input, Input))
    print(isinstance(dir_input, FileInput))
    print(isinstance(dir_input, DirInput))


if __name__ == "__main__":
    ft.run(main)
