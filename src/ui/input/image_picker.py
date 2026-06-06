import flet as ft
from dataclasses import dataclass
from pathlib import Path
from ui.input.input import Input


@ft.observable
@dataclass
class ImagePicker(Input):
    @ft.component
    def ui(self):
        def image_picked(e):
            if not e.files:
                return
            file = e.files[0]
            self.value = file.path

        file_picker = ft.FilePicker(on_upload=image_picked)

        async def on_click(_):
            selected_file = await file_picker.pick_files(
                allow_multiple=False, file_type=ft.FilePickerFileType.IMAGE
            )
            if selected_file is not None and len(selected_file) > 0:
                self.value = selected_file[0].path
                # v_ctn.content = ft.Image(src=selected_file[0].path)

        content_1 = ft.Placeholder()
        content_2 = ft.Image(
            width=150,
            height=150,
            border_radius=10,
            fit=ft.BoxFit.COVER,
            src=str(self.value),
        )
        if self.value is None or not Path(self.value).exists():
            content = content_1
        else:
            content = content_2

        return ft.Container(
            content=content,
            height=200,
            width=150,
            alignment=ft.Alignment.CENTER,
            on_click=on_click,
            bgcolor=ft.Colors.GREY_200,
        )


@ft.component
def App():

    return ft.Column(controls=[ImagePicker(value='data/images/test.png').ui()])


if __name__ == '__main__':
    ft.run(lambda page: page.render(App))
