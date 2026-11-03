"""反馈组件：轻提示、消息条、对话框、进度与加载。"""

from __future__ import annotations

import flet as ft

from docs import kit
from docs.blocks import Doc, demo, h2, note, p, tip, ul
from docs.content.components._shared import caption
from ui import (
    AlertDialog,
    Button,
    Column,
    Loading,
    Message,
    ProgressBar,
    StyleType,
    Toast,
    toast_info,
    toast_success,
    use_t,
)

_TOAST_CODE = '''Toast(content="Saved", style_type=StyleType.SUCCESS).show(page=page)

# 快捷函数
toast_success("Saved", page=page)
toast_error("Upload failed", page=page)'''

_DIALOG_CODE = '''AlertDialog(
    title="Delete this file?",
    msg="This action cannot be undone.",
    style_type=StyleType.WARNING,
    on_yes_click=lambda _: toast_success("Deleted", page=page),
).show(page)'''


@ft.component
def _toasts() -> ft.Control:
    tr = use_t()
    page = ft.context.page
    styles = (
        ("default", StyleType.DEFAULT),
        ("primary", StyleType.PRIMARY),
        ("info", StyleType.INFO),
        ("success", StyleType.SUCCESS),
        ("warning", StyleType.WARNING),
        ("error", StyleType.ERROR),
    )
    return ft.Column(
        spacing=12,
        controls=[
            ft.Text(tr("cat.feedback.toast.hint"), size=12.5, color=kit.MUTED),
            ft.Row(
                wrap=True,
                spacing=10,
                run_spacing=10,
                controls=[
                    Button(
                        tr(f"cat.feedback.style.{name}"),
                        on_click=lambda _e, style=style, name=name: Toast(
                            content=tr("cat.feedback.toast.msg", kind=tr(f"cat.feedback.style.{name}")),
                            style_type=style,
                        ).show(page=page),
                    )
                    for name, style in styles
                ],
            ),
        ],
    )


@ft.component
def _dialog() -> ft.Control:
    tr = use_t()
    page = ft.context.page

    def confirm(_: ft.Event[Button]) -> None:
        AlertDialog(
            title=tr("cat.feedback.dialog.title2"),
            msg=tr("cat.feedback.dialog.msg"),
            style_type=StyleType.WARNING,
            on_yes_click=lambda _e: toast_success(
                tr("cat.feedback.dialog.done"), page=page
            ),
            on_no_click=lambda _e: toast_info(tr("cat.feedback.dialog.cancel"), page=page),
        ).show(page)

    def message(_: ft.Event[Button]) -> None:
        Message(
            content=tr("cat.feedback.message.body"),
            style_type=StyleType.INFO,
        ).show(page)

    return ft.Row(
        spacing=10,
        controls=[
            Button(
                tr("cat.feedback.dialog.open"),
                is_primary=True,
                icon=ft.Icons.CHAT_BUBBLE_OUTLINE,
                on_click=confirm,
            ),
            Button(
                tr("cat.feedback.message.open"),
                icon=ft.Icons.SUBJECT,
                on_click=message,
            ),
        ],
    )


@ft.component
def _progress() -> ft.Control:
    tr = use_t()
    return Column(
        spacing=14,
        controls=[
            Column(
                spacing=5,
                controls=[
                    caption(tr("cat.feedback.progress.download")),
                    ProgressBar(progress=0.72),
                ],
            ),
            Column(
                spacing=5,
                controls=[
                    caption(tr("cat.feedback.progress.index")),
                    ProgressBar(progress=35, color=ft.Colors.TERTIARY),
                ],
            ),
            ft.Row(
                spacing=22,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    Loading(),
                    Loading(size_name="small"),
                    Loading(size_name="large"),
                    ft.Text(tr("cat.feedback.progress.loading"), size=12, color=kit.MUTED),
                ],
            ),
        ],
    )


FEEDBACK: Doc = (
    p("cat.feedback.intro"),
    h2("cat.feedback.toast.title"),
    demo(_toasts, hint_key="cat.feedback.toast.hint", code=_TOAST_CODE),
    h2("cat.feedback.dialog.title"),
    demo(_dialog, hint_key="cat.feedback.dialog.hint", code=_DIALOG_CODE),
    h2("cat.feedback.progress.title"),
    demo(_progress, hint_key="cat.feedback.progress.hint"),
    ul("cat.feedback.note1", "cat.feedback.note2", "cat.feedback.note3"),
    tip("cat.feedback.tip", "cat.feedback.tip_title"),
    note("cat.feedback.tip2", "cat.feedback.tip2_title"),
)
