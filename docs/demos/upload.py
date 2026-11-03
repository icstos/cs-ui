"""文件与目录选择演示。"""

from __future__ import annotations

import flet as ft

from docs.core.assets import LOGO_FILE
from docs.demos._helpers import use_stable
from docs.kit import cell, demo_card, demo_grid, doc_page
from ui import (
    Button,
    DirPicker,
    FilePicker,
    FileSaver,
    ImagePicker,
    toast_info,
    use_t,
)


@ft.component
def upload_page() -> ft.Control:
    tr = use_t()
    page = ft.context.page

    file_picker = use_stable(
        lambda: FilePicker(allowed_extensions=["png", "jpg", "pdf"])
    )
    dir_picker = use_stable(lambda: DirPicker())
    file_saver = use_stable(lambda: FileSaver())
    image_picker = use_stable(
        lambda: ImagePicker(
            label=tr("upload.image.label"),
            value=str(LOGO_FILE),
            width=320,
        )
    )

    def read_values(_: ft.Event[Button]) -> None:
        toast_info(
            tr(
                "upload.dump",
                file=file_picker.value,
                dir=dir_picker.value,
                save=file_saver.value,
                image=image_picker.value,
            ),
            page=page,
        )

    file_card = demo_card(
        title=tr("upload.file.title"),
        hint=tr("upload.file.hint"),
        icon=ft.Icons.ATTACH_FILE,
        stretch=True,
        body=[file_picker.ui()],
    )
    dir_card = demo_card(
        title=tr("upload.dir.title"),
        hint=tr("upload.dir.hint"),
        icon=ft.Icons.FOLDER_OPEN,
        stretch=True,
        body=[dir_picker.ui()],
    )
    save_card = demo_card(
        title=tr("upload.save.title"),
        hint=tr("upload.save.hint"),
        icon=ft.Icons.SAVE_OUTLINED,
        stretch=True,
        body=[file_saver.ui()],
    )
    image_card = demo_card(
        title=tr("upload.image.title"),
        hint=tr("upload.image.hint"),
        icon=ft.Icons.IMAGE_OUTLINED,
        stretch=True,
        body=[image_picker.ui()],
    )

    return doc_page(
        "upload",
        [
            demo_grid(
                cell(file_card, span=6),
                cell(dir_card, span=6),
                cell(save_card, span=6),
                cell(image_card, span=6),
            )
        ],
        badges=[
            Button(
                tr("common.read_values"),
                is_primary=True,
                on_click=read_values,
            )
        ],
    )
