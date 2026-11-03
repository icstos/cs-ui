"""反馈与浮层组件演示。"""

from __future__ import annotations

import asyncio

import flet as ft

from docs.kit import cell, demo_card, demo_grid, doc_page
from ui import (
    AlertDialog,
    Button,
    Loading,
    Message,
    ProgressBar,
    StyleType,
    Toast,
    toast_error,
    toast_info,
    toast_success,
    toast_warning,
    use_t,
)


@ft.component
def feedback_page() -> ft.Control:
    tr = use_t()
    page = ft.context.page

    def make_toast(style_type: StyleType, text: str):
        def show(_: ft.Event[Button]) -> None:
            Toast(content=text, style_type=style_type).show(page=page)

        return show

    def show_message(_: ft.Event[Button]) -> None:
        Message(content=tr("feedback.message.body"), style_type=StyleType.INFO).show()

    def show_dialog(_: ft.Event[Button]) -> None:
        AlertDialog(
            title=tr("feedback.dialog.delete_title"),
            msg=tr("feedback.dialog.delete_msg"),
            style_type=StyleType.WARNING,
            on_yes_click=lambda _: toast_success(
                tr("feedback.dialog.deleted"), page=page
            ),
            on_no_click=lambda _: toast_info(
                tr("feedback.dialog.canceled"), page=page
            ),
        ).show(page)

    progress, set_progress = ft.use_state(0.35)

    def animate_progress(_: ft.Event[Button]) -> None:
        async def pump() -> None:
            value = progress
            while value < 1.0:
                value = min(1.0, value + 0.02)
                set_progress(value)
                await asyncio.sleep(0.02)

        page.run_task(pump)

    toast_rows = [
        (tr("feedback.toast.default"), StyleType.DEFAULT, tr("feedback.toast.msg_default")),
        (tr("feedback.toast.primary"), StyleType.PRIMARY, tr("feedback.toast.msg_primary")),
        (tr("feedback.toast.info"), StyleType.INFO, tr("feedback.toast.msg_info")),
        (tr("feedback.toast.success"), StyleType.SUCCESS, tr("feedback.toast.msg_success")),
        (tr("feedback.toast.warning"), StyleType.WARNING, tr("feedback.toast.msg_warning")),
        (tr("feedback.toast.error"), StyleType.ERROR, tr("feedback.toast.msg_error")),
    ]

    toasts = demo_card(
        title=tr("feedback.toast.title"),
        hint=tr("feedback.toast.hint"),
        icon=ft.Icons.NOTIFICATIONS_OUTLINED,
        stretch=True,
        body=[
            ft.Row(
                wrap=True,
                spacing=10,
                run_spacing=10,
                controls=[
                    Button(label, on_click=make_toast(style, text))
                    for label, style, text in toast_rows
                ],
            ),
            ft.Row(
                wrap=True,
                spacing=10,
                run_spacing=10,
                controls=[
                    Button(
                        tr("feedback.toast.quick", name=tr("feedback.toast.success")),
                        on_click=lambda _: toast_success(
                            tr("feedback.toast.quick_success"), page=page
                        ),
                    ),
                    Button(
                        tr("feedback.toast.quick", name=tr("feedback.toast.error")),
                        on_click=lambda _: toast_error(
                            tr("feedback.toast.quick_error"), page=page
                        ),
                    ),
                    Button(
                        tr("feedback.toast.quick", name=tr("feedback.toast.warning")),
                        on_click=lambda _: toast_warning(
                            tr("feedback.toast.quick_warning"), page=page
                        ),
                    ),
                    Button(
                        tr("feedback.toast.quick", name=tr("feedback.toast.info")),
                        on_click=lambda _: toast_info(
                            tr("feedback.toast.quick_info"), page=page
                        ),
                    ),
                ],
            ),
        ],
    )

    message = demo_card(
        title=tr("feedback.message.title"),
        hint=tr("feedback.message.hint"),
        icon=ft.Icons.CHAT_BUBBLE_OUTLINE,
        body=[
            Button(tr("feedback.message.show"), on_click=show_message),
            Button(
                tr("feedback.dialog.confirm"),
                is_primary=True,
                on_click=show_dialog,
            ),
        ],
    )

    dialogs = demo_card(
        title=tr("feedback.dialog.title"),
        hint=tr("feedback.dialog.hint"),
        icon=ft.Icons.WEB_ASSET_OUTLINED,
        body=[
            ft.Row(
                wrap=True,
                spacing=10,
                run_spacing=10,
                controls=[
                    Button(
                        style.name,
                        on_click=lambda _, selected=style: AlertDialog(
                            title=tr("feedback.dialog.title_n", name=selected.name),
                            msg=tr("feedback.dialog.body"),
                            style_type=selected,
                            on_yes_click=lambda _: None,
                            on_no_click=lambda _: None,
                        ).show(page),
                    )
                    for style in StyleType
                ],
            )
        ],
    )

    bars = demo_card(
        title=tr("feedback.progress.title"),
        hint=tr("feedback.progress.hint"),
        icon=ft.Icons.LINEAR_SCALE,
        stretch=True,
        body=[
            ProgressBar(value=0.35, color=ft.Colors.PRIMARY),
            ProgressBar(value=0.72, color=ft.Colors.TERTIARY),
            ProgressBar(value=None, color=ft.Colors.SECONDARY),
        ],
    )

    loaders = demo_card(
        title=tr("feedback.loading.title"),
        hint=tr("feedback.loading.hint"),
        icon=ft.Icons.HOURGLASS_EMPTY,
        body=[
            ft.Row(
                spacing=32,
                controls=[
                    ft.Column(
                        spacing=4,
                        controls=[
                            ft.Text(
                                "small",
                                size=11,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                            Loading(size_name="small"),
                        ],
                    ),
                    ft.Column(
                        spacing=4,
                        controls=[
                            ft.Text(
                                "normal",
                                size=11,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                            Loading(size_name="normal"),
                        ],
                    ),
                    ft.Column(
                        spacing=4,
                        controls=[
                            ft.Text(
                                "large",
                                size=11,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                            Loading(size_name="large"),
                        ],
                    ),
                ],
            )
        ],
    )

    hooks = demo_card(
        title=tr("feedback.hooks.title"),
        hint=tr("feedback.hooks.hint"),
        icon=ft.Icons.AUTO_GRAPH,
        stretch=True,
        body=[
            ProgressBar(value=progress, color=ft.Colors.PRIMARY),
            ft.Text(
                tr("feedback.hooks.current", percent=f"{progress * 100:.0f}"),
                size=12,
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
            Button(tr("feedback.hooks.run"), on_click=animate_progress),
        ],
    )

    return doc_page(
        "feedback",
        [
            demo_grid(
                cell(toasts, span=12),
                cell(message, span=6),
                cell(dialogs, span=6),
                cell(bars, span=6),
                cell(loaders, span=6),
                cell(hooks, span=12),
            )
        ],
    )
