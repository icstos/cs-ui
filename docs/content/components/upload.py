"""文件选择：文件、目录、保存与图片。"""

from __future__ import annotations

import flet as ft

from docs import kit
from docs.blocks import Doc, demo, h2, note, p, tip
from docs.site import LOGO_FILE
from ui import (
    Button,
    DirPicker,
    FilePicker,
    FileSaver,
    ImagePicker,
    Message,
    use_t,
)

_PICKER_CODE = '''files = FilePicker(allowed_extensions=["png", "pdf"])
folder = DirPicker()
saver = FileSaver()

Column(controls=[files.ui(), folder.ui(), saver.ui()])

# 选择结果直接读 value
print([path.name for path in files.value])'''


@ft.component
def _pickers() -> ft.Control:
    tr = use_t()
    page = ft.context.page

    files = kit.use_stable(lambda: FilePicker(allowed_extensions=["png", "jpg", "pdf"]))
    folder = kit.use_stable(DirPicker)
    saver = kit.use_stable(FileSaver)

    def dump(_: ft.Event[Button]) -> None:
        Message.info(
            tr(
                "cat.upload.dump",
                files=len(files.value or []),
                folder=folder.value or "—",
                save=saver.value or "—",
            ),
            page=page,
        )

    return ft.Column(
        spacing=18,
        controls=[
            ft.Row(
                spacing=16,
                wrap=True,
                run_spacing=14,
                controls=[files.ui(), folder.ui(), saver.ui()],
            ),
            Button(
                tr("cat.upload.read"),
                is_primary=True,
                icon=ft.Icons.FACT_CHECK,
                on_click=dump,
            ),
        ],
    )


@ft.component
def _image_picker() -> ft.Control:
    tr = use_t()
    picker = kit.use_stable(
        lambda: ImagePicker(
            label=tr("cat.upload.image.label"),
            value=str(LOGO_FILE),
            width=340,
        )
    )
    return picker.ui()


UPLOAD: Doc = (
    p("cat.upload.intro"),
    h2("cat.upload.picker.title"),
    demo(_pickers, hint_key="cat.upload.picker.hint", code=_PICKER_CODE),
    h2("cat.upload.image.title"),
    demo(_image_picker, hint_key="cat.upload.image.hint"),
    tip("cat.upload.tip", "cat.upload.tip_title"),
    note("cat.upload.tip2", "cat.upload.tip2_title"),
)
