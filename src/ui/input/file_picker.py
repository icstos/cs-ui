from dataclasses import field
from pathlib import Path
from collections.abc import Callable

import flet as ft

import os
import copy


def get_size(file_path):
    return round(os.stat(file_path).st_size, 2)


def get_human_file_size(file_size: float) -> str:
    if file_size < 1024:
        return f'{file_size:.2f} byte'
    elif file_size < 1024 * 1024:
        return f'{file_size / 1024:.2f} KB'
    elif file_size < 1024 * 1024 * 1024:
        return f'{file_size / (1024 * 1024):.2f} MB'
    else:
        return f'{file_size / (1024 * 1024 * 1024):.2f} GB'


@ft.control
class FilePicker(ft.Container):
    label: str = '选择文件'
    suffix_list: list = field(default_factory=list)
    allow_multiple: bool = True
    help: str = ''
    selected_file_list: list = field(default_factory=list)
    on_change: Callable | None = None

    def init(self):
        file: Path
        for idx, file in enumerate(copy.deepcopy(self.selected_file_list)):
            self.selected_file_list.append(
                ft.FilePickerFile(
                    id=idx,
                    name=file.name,
                    path=str(file.absolute()),
                    size=file.stat().st_size,
                )
            )

        self.v_file_picker = ft.FilePicker()
        self.v_choose_btn = ft.Button(
            content=self.label,
            # style_type=ft.StyleType.PRIMARY,
            icon=ft.Icons.INSERT_DRIVE_FILE_OUTLINED,
            on_click=self.handle_files_pick,
        )
        self.v_selected_file_list = ft.ListView(
            spacing=-2, padding=ft.Padding.only(left=3)
        )
        self.v_selected_file_list_ctn = ft.Container(content=self.v_selected_file_list)
        self.content = ft.Column(
            controls=[self.v_choose_btn, self.v_selected_file_list_ctn]
        )
        self.update_v_selected_file_list()

    def update_v_selected_file_list(self):
        self.v_selected_file_list.controls = [
            ft.Container(
                ft.Row(
                    controls=[
                        ft.ProgressRing(
                            value=0, bgcolor='#eeeeee', width=20, height=20
                        ),
                        ft.Text(value=file.name),
                        ft.Text(value=get_human_file_size(file.size)),
                        ft.IconButton(
                            icon=ft.Icons.DELETE,
                            on_click=self.click_delete_item,
                            key=file.name,
                        ),
                    ]
                ),
                key=file.name,
                tooltip=file.path,
            )
            for file in self.selected_file_list
        ]

    async def handle_files_pick(self, e):
        self.selected_file_list = await self.v_file_picker.pick_files(
            allow_multiple=self.allow_multiple
        )
        self.update_v_selected_file_list()
        self.update_ctn_border()
        if self.on_change:
            self.on_change(self.selected_file_list)

    def click_delete_item(self, e):
        """
        删除已选文件。
        """
        for item in self.v_selected_file_list.controls:
            if item.key == e.control.key:
                self.v_selected_file_list.controls.remove(item)
        self.update_ctn_border()

    def update_ctn_border(self):
        """
        根据文件列表是否为空设置边框。
        """
        if len(self.v_selected_file_list.controls) > 0:
            self.v_selected_file_list_ctn.border = ft.Border.all(1, ft.Colors.BLUE)
        else:
            self.v_selected_file_list_ctn.border = None


@ft.control
class DirPicker(ft.Container):
    """
    文件夹选择控件，支持获取所选文件夹路径。
    """

    label: str = '选择文件夹'
    help: str = ''
    on_change: Callable | None = None

    def init(self):

        self.file_picker = ft.FilePicker()
        self.v_dir_path = ft.Text()
        self.rst_dir_path = Path()

        self.content = ft.Row(
            controls=[
                ft.Button(
                    content=self.label,
                    # style_type=ft.StyleType.PRIMARY,
                    icon=ft.Icons.FOLDER_OPEN,
                    on_click=self.handle_dir_picker,
                    # lambda _: self.v_file_picker.get_directory_path(),
                ),
                self.v_dir_path,
            ]
        )

    async def handle_dir_picker(self, event):
        self.seleted_dir = await self.file_picker.get_directory_path(
            dialog_title=self.label
        )
        self.v_dir_path.value = self.seleted_dir if self.seleted_dir else 'CANCELADO'
        self.rst_dir_path = Path(self.v_dir_path.value)
        self.v_dir_path.update()
        if self.on_change:
            self.on_change(self.rst_dir_path)


@ft.control
class FileSaver(ft.Container):
    """
    文件保存控件，支持保存文本或二进制数据到指定路径。
    """

    label: str = '保存文件'
    help: str = ''
    on_change: Callable | None = None

    def init(self):
        self.v_file_picker = ft.FilePicker()
        self.v_file_path = ft.Text()
        self.rst_file_path: Path | None = None

        self.content = ft.Row(
            controls=[
                ft.Button(
                    content=self.label,
                    # style_type=ft.StyleType.PRIMARY,
                    icon=ft.Icons.SAVE,
                    on_click=self.handle_save_file,
                    # lambda _: self.v_file_picker.save_file(),
                ),
                self.v_file_path,
            ]
        )

    async def handle_save_file(self, e):
        self.seleted_dir = await self.v_file_picker.save_file()
        if self.seleted_dir is not None:
            self.v_file_path.value = self.seleted_dir
            self.rst_file_path = Path(self.v_file_path.value)
            self.v_file_path.update()
            if self.on_change:
                self.on_change(self.rst_file_path)

    def save_file(self, data: str | bytes):
        """
        保存数据到选定文件路径。
        """
        if not self.rst_file_path:
            return
        if isinstance(data, str):
            with open(self.rst_file_path, 'w', encoding='utf-8') as f:
                f.write(data)
        elif isinstance(data, bytes):
            with open(self.rst_file_path, 'wb') as f:
                f.write(data)


def main(page: ft.Page):
    now_file_uploader = FilePicker()
    now_dir_picker = DirPicker()
    now_file_saver = FileSaver()

    def test(_):
        print('FilePicker: ', now_file_uploader.selected_file_list)

    def test_dir_picker(_):
        print('DirPicker: ', now_dir_picker.rst_dir_path)

    def test_file_saver(_):
        now_file_saver.save_file('测试内容')
        print('FileSaver: ', now_file_saver.rst_file_path)

    test_btn = ft.Button(content='测试当前选择文件', on_click=test)
    test_dir_picker_btn = ft.Button(
        content='测试当前选择文件夹', on_click=test_dir_picker
    )
    test_file_saver_btn = ft.Button(
        content='测试当前保存文件', on_click=test_file_saver
    )
    page.add(
        ft.Column(
            controls=[
                now_file_uploader,
                test_btn,
                now_dir_picker,
                test_dir_picker_btn,
                now_file_saver,
                test_file_saver_btn,
            ]
        )
    )


if __name__ == '__main__':
    ft.run(main)
