import flet as ft
from dataclasses import dataclass, field
from pathlib import Path
from collections.abc import Callable

import os
import copy


def get_size(file_path):
    return round(os.stat(file_path).st_size, 2)


def get_human_file_size(file_size: float) -> str:
    if file_size < 1024:
        return f"{file_size:.2f} byte"
    elif file_size < 1024 * 1024:
        return f"{file_size / 1024:.2f} KB"
    elif file_size < 1024 * 1024 * 1024:
        return f"{file_size / (1024 * 1024):.2f} MB"
    else:
        return f"{file_size / (1024 * 1024 * 1024):.2f} GB"


@ft.observable
@dataclass
class FilePicker:
    value: list | None = field(default_factory=list)
    allowed_extensions: list = field(default_factory=list)
    allow_multiple: bool = True
    on_change: Callable | None = None

    def __post_init__(self):
        if self.value is None:
            self.value = []
        file: Path
        for idx, file in enumerate(copy.deepcopy(self.value)):
            self.value.append(
                ft.FilePickerFile(
                    id=idx,
                    name=file.name,
                    path=str(file.absolute()),
                    size=file.stat().st_size,
                )
            )

    @ft.component
    def ui(self):
        self._v_file_picker = ft.FilePicker()

        async def handle_files_pick(e):
            result = await self._v_file_picker.pick_files(
                allow_multiple=self.allow_multiple,
                allowed_extensions=self.allowed_extensions,
            )
            if result is not None:
                self.value = result
            self.notify()
            if self.on_change:
                self.on_change(self.value)

        def click_delete_item(file):
            self.value = [f for f in self.value if f.name != file.name]
            self.notify()

        v_choose_btn = ft.Button(
            content=ft.Text("选择文件"),
            icon=ft.Icons.INSERT_DRIVE_FILE_OUTLINED,
            on_click=handle_files_pick,
        )

        v_selected_files = ft.ListView(
            spacing=-2,
            padding=ft.Padding.only(left=3),
            controls=[
                ft.Container(
                    ft.Row(
                        controls=[
                            ft.ProgressRing(
                                value=0, bgcolor="#eeeeee", width=20, height=20
                            ),
                            ft.Text(value=file.name),
                            ft.Text(value=get_human_file_size(file.size)),
                            ft.IconButton(
                                icon=ft.Icons.DELETE,
                                on_click=lambda e, f=file: click_delete_item(f),
                                key=file.name,
                            ),
                        ]
                    ),
                    key=file.name,
                    tooltip=file.path,
                )
                for file in self.value
            ],
        )
        v_selected_files_ctn = ft.Container(
            content=v_selected_files,
            border=ft.Border.all(1, ft.Colors.BLUE) if len(self.value) > 0 else None,
        )

        return ft.Column(controls=[v_choose_btn, v_selected_files_ctn])


@ft.observable
@dataclass
class DirPicker:
    value: Path | None = None
    on_change: Callable | None = None

    @ft.component
    def ui(self):
        file_picker = ft.FilePicker()
        v_dir_path = ft.Text(value=str(self.value) if self.value else "")

        async def handle_dir_picker(e):
            selected_dir = await file_picker.get_directory_path()
            if selected_dir is not None:
                self.value = Path(selected_dir)
                self.notify()
                if self.on_change:
                    self.on_change(self.value)

        return ft.Row(
            controls=[
                ft.Button(
                    content=ft.Text("选择文件夹"),
                    icon=ft.Icons.FOLDER_OPEN,
                    on_click=handle_dir_picker,
                ),
                v_dir_path,
            ]
        )


@ft.observable
@dataclass
class FileSaver:
    value: Path | None = None
    on_change: Callable | None = None

    @ft.component
    def ui(self):
        v_file_picker = ft.FilePicker()
        v_file_path = ft.Text(value=str(self.value) if self.value else "")

        async def handle_save_file(e):
            selected_path = await v_file_picker.save_file()
            if selected_path is not None:
                self.value = Path(selected_path)
                self.notify()
                if self.on_change:
                    self.on_change(self.value)

        return ft.Row(
            controls=[
                ft.Button(
                    content=ft.Text("保存文件"),
                    icon=ft.Icons.SAVE,
                    on_click=handle_save_file,
                ),
                v_file_path,
            ]
        )

    def save_file(self, data: str | bytes):
        if not self.value:
            return
        if isinstance(data, str):
            with open(self.value, "w", encoding="utf-8") as f:
                f.write(data)
        elif isinstance(data, bytes):
            with open(self.value, "wb") as f:
                f.write(data)


@ft.component
def App():
    now_file_uploader = FilePicker()
    now_dir_picker = DirPicker()
    now_file_saver = FileSaver()

    def test(_):
        print("FilePicker: ", now_file_uploader.value)

    def test_dir_picker(_):
        print("DirPicker: ", now_dir_picker.value)

    def test_file_saver(_):
        now_file_saver.save_file("测试内容")
        print("FileSaver: ", now_file_saver.value)

    test_btn = ft.Button(content=ft.Text("测试当前选择文件"), on_click=test)
    test_dir_picker_btn = ft.Button(
        content=ft.Text("测试当前选择文件夹"), on_click=test_dir_picker
    )
    test_file_saver_btn = ft.Button(
        content=ft.Text("测试当前保存文件"), on_click=test_file_saver
    )
    return ft.Column(
        controls=[
            now_file_uploader.ui(),
            test_btn,
            now_dir_picker.ui(),
            test_dir_picker_btn,
            now_file_saver.ui(),
            test_file_saver_btn,
        ]
    )


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
