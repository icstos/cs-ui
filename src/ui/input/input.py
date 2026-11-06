from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import flet as ft

from ui.core.styles import outline_input
from ui.core.tokens import FONT_SIZE as TYPE_SCALE

ICON_SIZE = 16
#: 标签字号：比正文大一档（正文 13），标签仍然略重，但不至于压过输入内容。
#: 以前写死 16，比输入文字大一号，两行挤在一起时读起来像两个标题。
LABEL_SIZE = TYPE_SCALE["subtitle"]
BORDER_RADIUS = 8
DEFAULT_FORM_HEIGHT = 36
SPACING = 10  # Column或ROW的controls之间的间隔


@ft.observable
@dataclass
class Label:
    label: str | None = None
    label_width: int = 150
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
                spans.append(ft.TextSpan(text=": "))
            return ft.Text(
                spans=spans,
                text_align=ft.TextAlign.START if self.is_vertical else ft.TextAlign.END,
                width=self.label_width,
                size=LABEL_SIZE,
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
    data_type: str = "str"
    step: int | float = 0.01
    width: int = 500

    def __post_init__(self):
        self.last_value = self.value
        # 数字类型（int / float）的实现在 NumberInput 里，这里只持有实例并桥接取值。
        self._num = None

    # min_value: ft.Number = -math.inf
    # max_value: ft.Number = math.inf
    @property
    def path(self) -> Path | None:
        if self.value is None or len(str(self.value).strip()) == 0:
            return None
        else:
            return Path(str(self.value).strip().strip('"').strip("'"))

    def on_change(self, e):
        """文本类输入的回写（数字类型走 :meth:`_on_number_change`）。"""
        self.value = e.data

    def _on_number_change(self, value: float | None) -> None:
        """NumberInput 的值回写到 ``Input.value``，外部读到的始终是最新值。"""
        self.value = value
        self.last_value = value
        self.notify()

    def _number_ui(self) -> ft.Control:
        """数字类型：渲染交给 :class:`~ui.input.number_input.NumberInput`。

        步进 / 精度 / 范围 / 单位都在那边实现，这里只做「标签参数 + 值」的搬运，
        避免两套数值处理逻辑各自漂移。

        ``NumberInput`` 继承自本模块的 :class:`Label`，所以在函数内延迟导入，
        避免模块级循环依赖。
        """
        from ui.input.number_input import NumberInput

        if self._num is None:
            self._num = NumberInput(
                label=self.label,
                label_width=self.label_width,
                is_vertical=self.is_vertical,
                is_required=self.is_required,
                spacing=self.spacing,
                run_spacing=self.run_spacing,
                value=self.value,
                step=1 if self.data_type == "int" else (self.step or 0.01),
                precision=0 if self.data_type == "int" else None,
                width=self.width,
                hint_text=self.hint_text,
                on_change=self._on_number_change,
            )
        # 外部改了 Input.value 时同步下来；值没变时 set_value 内部直接返回
        self._num.set_value(self.value)
        return self._num.ui()

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
        """构建输入控件。

        数字类型（``data_type="int"/"float"``）直接交给
        :class:`~ui.input.number_input.NumberInput`，``prefix`` / ``suffix`` /
        ``prefix_icon`` 只对文本与文件类型生效 —— 数字框的单位请用
        ``NumberInput`` 的 ``prefix`` / ``suffix`` 字符串参数。
        """
        if self.data_type == "int" or self.data_type == "float":
            return self._number_ui()

        text_align: ft.TextAlign = ft.TextAlign.START
        keyboard_type: ft.KeyboardType = ft.KeyboardType.TEXT
        if self.data_type == "file" or self.data_type == "dir":
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
                    if self.data_type == "file"
                    else ft.Icons.FOLDER_OPEN_OUTLINED,
                    size=ICON_SIZE,
                    color=ft.Colors.WHITE if is_pick else None,
                ),
                on_click=handle_file_picker
                if self.data_type == "file"
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
            value=str(self.value) if self.value is not None else "",
            cursor_color=ft.Colors.PRIMARY,
            selection_color=ft.Colors.with_opacity(0.24, ft.Colors.PRIMARY),
            hover_color=ft.Colors.with_opacity(0.08, ft.Colors.PRIMARY),
            border=outline_input(
                BORDER_RADIUS, ft.Colors.OUTLINE_VARIANT, ft.Colors.PRIMARY
            ),
            cursor_width=1,
            hint_text=self.hint_text,
            multiline=self.multiline,
            # 描边 + 透明底。以前铺 ``SURFACE_CONTAINER_HIGHEST``：那是 M3 里
            # 最重的一档容器色，在 1.1 的中性表面下就成了一块灰 —— 和卡片底、
            # 和旁边的只读框全糊在一起，边界只剩一圈比它更淡的线。
            filled=False,
            height=DEFAULT_FORM_HEIGHT,
            text_align=text_align,
            keyboard_type=keyboard_type,
            content_padding=content_padding,
            suffix=suffix,
            prefix=prefix,
            prefix_icon=prefix_icon,
            on_change=_on_change,
            width=self.width,
        )
        if self.v_label is not None:
            if self.is_vertical:
                return ft.Column(
                    controls=[self.v_label, v_ui],
                    width=self.width + 10,
                )
            else:
                return ft.Row(
                    controls=[self.v_label, v_ui],
                    width=self.label_width + self.width + SPACING,
                )
        else:
            return v_ui


@ft.component
def App():
    name = Input(label="name", value="shawn")
    age = Input(label="age", value="123", data_type="int", width=180)
    file = Input(
        label="file",
        value="",
        label_width=300,
        is_vertical=True,
        data_type="file",
    )
    _dir = Input(label="dir", value="", data_type="dir")
    return ft.Column(
        controls=[
            name.ui(),
            age.ui(),
            Input(
                label="age", value="123", data_type="int", is_required=True, width=180
            ).ui(),
            Input(label="file", value="", data_type="file").ui(),
            Input(value="", data_type="file").ui(),
            Input(label="file", value="", label_width=300, data_type="file").ui(),
            file.ui(),
            _dir.ui(),
            ft.Button(
                content="print",
                on_click=lambda _: print(
                    f"???{name.value}，{age.value},{file.value},{_dir.value}"
                ),
            ),
        ]
    )


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
