"""反馈组件：消息提示、通知、对话框、进度与加载。"""

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
    Notification,
    ProgressBar,
    StyleType,
    use_t,
)

_MESSAGE_CODE = '''# 一句话的回执：顶部居中，3 秒后自己走开
Message.success("已保存")
Message.error("请求失败，请重试", duration=5000)

# 连点三次只留一条，带 ×3 计数
Message("已保存", grouping=True).show(page=page)

# 常驻 + 手动关
Message("正在同步…", duration=0, show_close=True).show(page=page)'''

_NOTIFY_CODE = '''# 系统级通报：默认贴右上角，带标题
Notification.success("同步完成", "3 个组件已更新到最新版本")

# 常驻，等用户处理完再关
Notification(
    title="连接中断",
    content="正在重试…",
    style_type=StyleType.ERROR,
    duration=0,
    position="bottom-right",
)'''

_DIALOG_CODE = '''AlertDialog(
    title="Delete this file?",
    msg="This action cannot be undone.",
    style_type=StyleType.WARNING,
    on_yes_click=lambda _: Message.success("Deleted"),
).show(page)'''


@ft.component
def _messages() -> ft.Control:
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

    def show(style: StyleType, name: str):
        def _handler(_e: ft.Event[Button]) -> None:
            Message(
                tr("cat.feedback.msg.body", kind=tr(f"cat.feedback.style.{name}")),
                style_type=style,
            ).show(page)

        return _handler

    return Column(
        spacing=12,
        controls=[
            ft.Row(
                wrap=True,
                spacing=10,
                run_spacing=10,
                controls=[
                    Button(tr(f"cat.feedback.style.{name}"), on_click=show(style, name))
                    for name, style in styles
                ],
            ),
            ft.Row(
                wrap=True,
                spacing=10,
                run_spacing=10,
                controls=[
                    Button(
                        tr("cat.feedback.msg.closable"),
                        icon=ft.Icons.CLOSE_ROUNDED,
                        on_click=lambda _e: Message(
                            tr("cat.feedback.msg.closablebody"),
                            duration=0,
                            show_close=True,
                        ).show(page),
                    ),
                    Button(
                        tr("cat.feedback.msg.grouping"),
                        on_click=lambda _e: Message(
                            tr("cat.feedback.msg.groupbody"),
                            style_type=StyleType.SUCCESS,
                            grouping=True,
                        ).show(page),
                    ),
                    Button(
                        tr("cat.feedback.msg.long"),
                        on_click=lambda _e: Message(
                            tr("cat.feedback.msg.longbody"),
                            style_type=StyleType.WARNING,
                        ).show(page),
                    ),
                    Button(
                        tr("cat.feedback.msg.closeall"),
                        on_click=lambda _e: Message.close_all(page),
                    ),
                ],
            ),
        ],
    )


@ft.component
def _notifications() -> ft.Control:
    tr = use_t()
    page = ft.context.page
    styles = (
        ("default", StyleType.DEFAULT),
        ("info", StyleType.INFO),
        ("success", StyleType.SUCCESS),
        ("warning", StyleType.WARNING),
        ("error", StyleType.ERROR),
    )
    corners = (
        ("tl", "top-left"),
        ("tr", "top-right"),
        ("bl", "bottom-left"),
        ("br", "bottom-right"),
    )

    def send(style: StyleType, name: str):
        def _handler(_e: ft.Event[Button]) -> None:
            Notification(
                tr("cat.feedback.notify.body"),
                title=tr(f"cat.feedback.style.{name}"),
                style_type=style,
            ).show(page)

        return _handler

    def corner(position: str, name: str):
        def _handler(_e: ft.Event[Button]) -> None:
            Notification(
                tr("cat.feedback.notify.posbody", pos=tr(f"cat.feedback.notify.pos.{name}")),
                title=tr("cat.feedback.notify.head"),
                style_type=StyleType.INFO,
                position=position,
            ).show(page)

        return _handler

    return Column(
        spacing=12,
        controls=[
            ft.Row(
                wrap=True,
                spacing=10,
                run_spacing=10,
                controls=[
                    Button(tr(f"cat.feedback.style.{name}"), on_click=send(style, name))
                    for name, style in styles
                ],
            ),
            ft.Row(
                wrap=True,
                spacing=10,
                run_spacing=10,
                controls=[
                    *[
                        Button(
                            tr(f"cat.feedback.notify.pos.{name}"),
                            on_click=corner(position, name),
                        )
                        for name, position in corners
                    ],
                    Button(
                        tr("cat.feedback.notify.sticky"),
                        icon=ft.Icons.PUSH_PIN_OUTLINED,
                        on_click=lambda _e: Notification(
                            tr("cat.feedback.notify.stickyBody"),
                            title=tr("cat.feedback.notify.stickyTitle"),
                            style_type=StyleType.WARNING,
                            duration=0,
                        ).show(page),
                    ),
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
            on_yes_click=lambda _e: Message.success(
                tr("cat.feedback.dialog.done")
            ).show(page),
            on_no_click=lambda _e: Message.info(tr("cat.feedback.dialog.cancel")).show(page),
        ).show(page)

    def notify(_: ft.Event[Button]) -> None:
        Notification(
            tr("cat.feedback.notify.body"),
            title=tr("cat.feedback.notify.head"),
            style_type=StyleType.SUCCESS,
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
                tr("cat.feedback.dialog.notify"),
                icon=ft.Icons.NOTIFICATIONS_OUTLINED,
                on_click=notify,
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
    h2("cat.feedback.msg.title"),
    demo(_messages, hint_key="cat.feedback.msg.hint", code=_MESSAGE_CODE),
    h2("cat.feedback.notify.title"),
    demo(_notifications, hint_key="cat.feedback.notify.hint", code=_NOTIFY_CODE),
    h2("cat.feedback.dialog.title"),
    demo(_dialog, hint_key="cat.feedback.dialog.hint", code=_DIALOG_CODE),
    h2("cat.feedback.progress.title"),
    demo(_progress, hint_key="cat.feedback.progress.hint"),
    ul("cat.feedback.note1", "cat.feedback.note2", "cat.feedback.note3"),
    tip("cat.feedback.tip", "cat.feedback.tip_title"),
    note("cat.feedback.tip2", "cat.feedback.tip2_title"),
)
