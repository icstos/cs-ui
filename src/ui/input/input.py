import flet as ft
from decimal import Decimal
from pathlib import Path
from dataclasses import field, dataclass
from ui.core.constants import DEFAULT_FORM_HEIGHT

ICON_SIZE = 16
BORDER_RADIUS = 8


@ft.observable
@dataclass
class InputState:
    value: int | float | Decimal | str | Path = ''
    last_value: int | float | Decimal | str = ''
    is_int: bool = False
    is_float: bool = False
    step: int | float = 0.01
    is_file: bool = False
    is_dir: bool = False

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
        if self.is_int or self.is_float:
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
        if self.is_int:
            self.value = int(_value)
        else:
            self.value = float(_value)
        self.last_value = self.value

    def handle_increase_click(self, e):
        print(self.value, self.step)
        _value = float(Decimal(str(self.value)) + Decimal(str(self.step)))
        if self.is_int:
            self.value = int(_value)
        else:
            self.value = float(_value)
        self.last_value = self.value

    async def handle_file_picker(self, e):
        self.selected_files = await e.control.pick_files(allow_multiple=False)
        if self.selected_files is not None and len(self.selected_files) > 0:
            self.value = str(self.selected_files[0].path)


@ft.component
def Input(
    state: InputState,
    prefix: ft.Control | None = None,
    suffix: ft.Control | None = None,
    prefix_icon: ft.Control | None = None,
):
    is_decrese_hover, set_decrese_hover = ft.use_state(False)
    is_increase_hover, set_increase_hover = ft.use_state(False)
    text_align: ft.TextAlign = ft.TextAlign.START
    keyboard_type: ft.KeyboardType = ft.KeyboardType.TEXT
    if state.is_int or state.is_float:
        text_align: ft.TextAlign = ft.TextAlign.CENTER
        if state.is_int:
            state.step = 1
        elif state.is_float:
            state.step = 0.01
        v_decrease = ft.Container(
            content=ft.Icon(
                icon=ft.Icons.REMOVE,
                size=ICON_SIZE,
                color=ft.Colors.WHITE if is_decrese_hover else None,
            ),
            border_radius=ft.BorderRadius(
                top_left=0, top_right=0, bottom_left=0, bottom_right=0
            ),
            on_click=state.handle_decrease_click,
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
            on_click=state.handle_increase_click,
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
    elif state.is_file or state.is_dir:
        is_pick, set_is_pick = ft.use_state(False)
        content_padding: ft.Padding = ft.Padding.only(left=5, right=10, top=0, bottom=0)

        async def handle_file_picker(e):
            selected_files = await v_file_picker.pick_files(allow_multiple=False)
            if selected_files is not None and len(selected_files) > 0:
                state.value = str(selected_files[0].path)

        async def handle_dir_picker(e):
            seleted_dir = await v_file_picker.get_directory_path()
            if seleted_dir is not None:
                state.value = str(seleted_dir)

        v_file_picker = ft.FilePicker()
        # NOTE: prefix的话，需要移到上面才会显示
        prefix_icon = ft.Container(
            content=ft.Icon(
                icon=ft.Icons.FILE_OPEN_OUTLINED
                if state.is_file
                else ft.Icons.FOLDER_OPEN_OUTLINED,
                size=ICON_SIZE,
                color=ft.Colors.WHITE if is_pick else None,
            ),
            on_click=handle_file_picker if state.is_file else handle_dir_picker,
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
        state.on_change(e)
        state.notify()

    return ft.TextField(
        value=str(state.value),
        cursor_color=ft.Colors.BLUE,
        focused_border_color=ft.Colors.BLUE,
        selection_color=ft.Colors.GREY_400,
        hover_color=ft.Colors.BLUE_50,
        border_radius=ft.BorderRadius.all(BORDER_RADIUS),
        border=ft.InputBorder.OUTLINE,
        border_width=1,
        cursor_width=1,
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


@ft.component
def App():

    return ft.Column(
        controls=[
            Input(InputState(value="123")),
            Input(InputState(value="123", is_int=True)),
            Input(InputState(value="", is_file=True)),
            Input(dir_input := InputState(value="", is_dir=True)),
            ft.Button(content='print', on_click=lambda _: print(dir_input.value)),
            # FileInput(),
            # DirInput(),
        ]
    )


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
