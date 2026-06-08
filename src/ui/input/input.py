import flet as ft
from decimal import Decimal
from pathlib import Path
from dataclasses import dataclass

ICON_SIZE = 16
FONT_SIZE = 16
BORDER_RADIUS = 8
DEFAULT_FORM_HEIGHT = 36


@ft.observable
@dataclass
class Label:
    label: str | None = None
    label_width: int | None = None
    is_vertical: bool = False
    is_required: bool = False
    spacing: ft.Number = 10
    run_spacing: ft.Number = 10

    @property
    def v_label(self):
        if self.label is not None:
            if self.is_required:
                spans = [
                    ft.TextSpan(text="*", style=ft.TextStyle(color=ft.Colors.RED)),
                    ft.TextSpan(self.label),
                ]
            else:
                spans = [ft.TextSpan(text=self.label)]
            if self.label.endswith(":") or self.label.endswith("："):
                pass
            else:
                #     self.label = self.label + ": " # NOTE, 在前面走这处，程序就死机了
                spans.append(ft.TextSpan(text=': '))
            return ft.Text(
                spans=spans,
                text_align=ft.TextAlign.START if self.is_vertical else ft.TextAlign.END,
                width=self.label_width,
                size=FONT_SIZE,
            )
        else:
            return None


@ft.observable
@dataclass
class Input(Label):
    value: int | float | Decimal | str | Path | None = None
    last_value: int | float | Decimal | str | Path | None = None
    hint_text: str | None = None
    multiline: bool = False
    data_type: str = 'str'
    step: int | float = 0.01

    def __post_init__(self):
        self.last_value = self.value

    # min_value: ft.Number = -math.inf
    # max_value: ft.Number = math.inf
    @property
    def path(self) -> Path | None:
        if self.value is None or len(str(self.value).strip()) == 0:
            return None
        else:
            return Path(str(self.value).strip().strip('"').strip("'"))

    def on_change(self, e):
        print('before', self.last_value, self.value)
        if self.data_type == 'int' or self.data_type == 'float':
            try:
                if isinstance(e.data, str) and e.data.strip() != "":
                    float(e.data)  # 验证数值合法性
            except ValueError:
                self.last_value = self.value
                self.value = self.last_value
            else:
                self.last_value = self.value
                self.value = e.data
        else:
            self.value = e.data
        # await asyncio.sleep(1)
        print('after', self.last_value, self.value)

    def handle_decrease_click(self, e):
        _value = float(Decimal(str(self.value)) - Decimal(str(self.step)))
        if self.data_type == 'int':
            self.value = int(_value)
        else:
            self.value = float(_value)
        self.last_value = self.value

    def handle_increase_click(self, e):
        print(self.value, self.step)
        _value = float(Decimal(str(self.value)) + Decimal(str(self.step)))
        if self.data_type == 'int':
            self.value = int(_value)
        else:
            self.value = float(_value)
        self.last_value = self.value

    async def handle_file_picker(self, e):
        self.selected_files = await e.control.pick_files(allow_multiple=False)
        if self.selected_files is not None and len(self.selected_files) > 0:
            self.value = str(self.selected_files[0].path)

    @ft.component
    def ui(
        self,
        prefix: ft.Control | None = None,
        suffix: ft.Control | None = None,
        prefix_icon: ft.Control | None = None,
    ):
        is_decrese_hover, set_decrese_hover = ft.use_state(False)
        is_increase_hover, set_increase_hover = ft.use_state(False)
        text_align: ft.TextAlign = ft.TextAlign.START
        keyboard_type: ft.KeyboardType = ft.KeyboardType.TEXT
        if self.data_type == 'int' or self.data_type == 'float':
            text_align: ft.TextAlign = ft.TextAlign.CENTER
            if self.data_type == 'int':
                self.step = 1
            elif self.data_type == 'float':
                self.step = 0.01
            v_decrease = ft.Container(
                content=ft.Icon(
                    icon=ft.Icons.REMOVE,
                    size=ICON_SIZE,
                    color=ft.Colors.WHITE if is_decrese_hover else None,
                ),
                border_radius=ft.BorderRadius(
                    top_left=0, top_right=0, bottom_left=0, bottom_right=0
                ),
                on_click=self.handle_decrease_click,
                width=30,
                alignment=ft.Alignment.CENTER,
                bgcolor=ft.Colors.BLUE if is_decrese_hover else None,
                on_hover=lambda e: set_decrese_hover(e.data),
            )
            v_increase = ft.Container(
                content=ft.Icon(
                    icon=ft.Icons.ADD,
                    size=ICON_SIZE,
                    color=ft.Colors.WHITE if is_increase_hover else None,
                ),
                border_radius=ft.BorderRadius(
                    top_left=0,
                    top_right=BORDER_RADIUS,
                    bottom_left=0,
                    bottom_right=BORDER_RADIUS,
                ),
                on_click=self.handle_increase_click,
                width=30,
                alignment=ft.Alignment.CENTER,
                bgcolor=ft.Colors.BLUE if is_increase_hover else None,
                on_hover=lambda e: set_increase_hover(e.data),
            )
            suffix = ft.Container(
                content=ft.Row(
                    controls=[v_decrease, v_increase],
                    alignment=ft.MainAxisAlignment.END,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    spacing=0,
                    run_spacing=0,
                ),
                width=60,
                alignment=ft.Alignment.CENTER_RIGHT,
                # TODO: 不加这个的话背景颜色会偏移
                offset=ft.Offset(x=0.1, y=-0.05),
            )
            content_padding = ft.Padding.only(left=5, right=0, top=0, bottom=10)
            keyboard_type: ft.KeyboardType = ft.KeyboardType.NUMBER
        elif self.data_type == 'file' or self.data_type == 'dir':
            is_pick, set_is_pick = ft.use_state(False)
            content_padding: ft.Padding = ft.Padding.only(
                left=5, right=10, top=0, bottom=0
            )

            async def handle_file_picker(e):
                selected_files = await v_file_picker.pick_files(allow_multiple=False)
                if selected_files is not None and len(selected_files) > 0:
                    self.value = str(selected_files[0].path)

            async def handle_dir_picker(e):
                seleted_dir = await v_file_picker.get_directory_path()
                if seleted_dir is not None:
                    self.value = str(seleted_dir)

            v_file_picker = ft.FilePicker()
            # NOTE: prefix的话，需要移到上面才会显示
            prefix_icon = ft.Container(
                content=ft.Icon(
                    icon=ft.Icons.FILE_OPEN_OUTLINED
                    if self.data_type == 'file'
                    else ft.Icons.FOLDER_OPEN_OUTLINED,
                    size=ICON_SIZE,
                    color=ft.Colors.WHITE if is_pick else None,
                ),
                on_click=handle_file_picker
                if self.data_type == 'file'
                else handle_dir_picker,
                bgcolor=ft.Colors.BLUE if is_pick else None,
                on_hover=lambda e: set_is_pick(e.data),
                border_radius=ft.BorderRadius(
                    top_left=BORDER_RADIUS,
                    top_right=0,
                    bottom_left=BORDER_RADIUS,
                    bottom_right=0,
                ),
            )

        else:
            if prefix and not suffix:
                content_padding = ft.Padding.only(left=10, right=5)
            elif suffix and not prefix:
                content_padding = ft.Padding.only(left=5, right=10)
            elif prefix and suffix:
                content_padding = ft.Padding.symmetric(horizontal=10)
            else:
                content_padding = ft.Padding.all(1)

        def _on_change(e):
            self.on_change(e)
            self.notify()

        v_ui = ft.TextField(
            value=str(self.value),
            cursor_color=ft.Colors.BLUE,
            focused_border_color=ft.Colors.BLUE,
            selection_color=ft.Colors.GREY_400,
            fill_color=ft.Colors.WHITE,
            hover_color=ft.Colors.BLUE_50,
            border_radius=ft.BorderRadius.all(BORDER_RADIUS),
            border=ft.InputBorder.OUTLINE,
            border_color=ft.Colors.GREY_300,
            border_width=1,
            cursor_width=1,
            hint_text=self.hint_text,
            multiline=self.multiline,
            filled=True,
            height=DEFAULT_FORM_HEIGHT,
            text_align=text_align,
            keyboard_type=keyboard_type,
            content_padding=content_padding,
            suffix=suffix,
            prefix=prefix,
            prefix_icon=prefix_icon,
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
    name = Input(label='name', value="shawn")
    age = Input(label='age', value="123", data_type='int')
    file = Input(
        label='file',
        value="",
        label_width=300,
        is_vertical=True,
        data_type='file',
    )
    _dir = Input(label='dir', value="", data_type='dir')
    return ft.Column(
        controls=[
            name.ui(),
            age.ui(),
            Input(label='age', value="123", data_type='int', is_required=True).ui(),
            Input(label='file', value="", data_type='file').ui(),
            Input(value="", data_type='file').ui(),
            Input(label='file', value="", label_width=300, data_type='file').ui(),
            file.ui(),
            _dir.ui(),
            ft.Button(
                content='print',
                on_click=lambda _: print(
                    f'???{name.value}，{age.value},{file.value},{_dir.value}'
                ),
            ),
        ]
    )


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
