import flet as ft


@ft.control
class ImagePicker(ft.Stack):
    is_file_field: bool = True
    file_changed: bool = False
    value: str | None = None

    def init(self):
        self.image = ft.Image(
            width=150,
            height=150,
            border_radius=10,
            fit=ft.BoxFit.COVER,
            src='data/images/test.png',
        )
        self.v_ctn = ft.Container(
            height=200,
            width=150,
            content=ft.Column([ft.Placeholder(height=200), self.image]),
            on_click=self.on_click,
            alignment=ft.Alignment.CENTER,
            bgcolor=ft.Colors.GREY,
        )
        self.controls = [self.v_ctn]

        self.file_picker = ft.FilePicker(on_upload=self.image_picked)

    def image_picked(self, e):
        if not e.files:
            return
        file = e.files[0]
        self.value = file.path
        self.file_changed = True

    async def on_click(self, _):
        self.selected_file = await self.file_picker.pick_files(
            allow_multiple=False, file_type=ft.FilePickerFileType.IMAGE
        )
        if self.selected_file is not None and len(self.selected_file) > 0:
            self.v_ctn.content = ft.Image(src=self.selected_file[0].path)


def main(page: ft.Page):
    page.add(ImagePicker())


if __name__ == '__main__':
    ft.run(main)
