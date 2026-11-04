"""Notification 通知。

用于**系统级**的被动提醒：后台同步完了、有新版本、连接断了。它从窗口角落
浮出来，有标题和正文，可以一直挂着等用户处理。

与 :class:`~ui.feedback.message.Message` 的分界
------------------------------------------------
``Notification`` 是"系统发生了什么"的通报，``Message`` 是"我做了什么"的回执。
前者带标题、贴角、默认不抢焦点；后者一行字、居中、转瞬即逝。

用法::

    Notification.success("同步完成", "3 个组件已更新到最新版本")
    Notification(title="连接中断", content="正在重试…", duration=0)

    n = Notification(title="构建完成", content="耗时 12s", show_close=False)
    n.show(page=page)

设计取舍
--------
- **四角可选**：``position`` 取 ``top-right``（默认）/ ``top-left`` /
  ``bottom-right`` / ``bottom-left``；贴底的两个位置，新通知从下面长出来。
- **常驻**：``duration=0`` 时不自动关闭——系统级问题不该"没看见就走了"。
- **点整卡可触发回调**：``on_click`` 用来跳到详情页；关闭按钮不会触发它。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import flet as ft

from ui.core.constants import StyleType
from ui.core.i18n import t
from ui.core.tokens import (
    FONT_SIZE,
    FONT_WEIGHT,
    RADIUS,
    SPACE,
    elevation,
    overlay,
)

from ._look import icon_chip
from ._overlay import SLOTS, Card, host_for, peek_host

__all__ = ["Notification"]

GAP = 12
WIDTH = 360
#: 图标底色块的边长，正文缩进要按它对齐
ICON = 24
DEFAULT_DURATION = 4500


class Notification:
    """角落里的一张通知卡。

    Args:
        content: 正文文本，或任意控件。
        title: 标题。空标题时只显示正文（图标与正文同一行）。
        style_type: 语义类型，决定图标与强调色。
        duration: 自动关闭的毫秒数；``0`` 表示常驻。
        position: 弹出位置，见 :data:`ui.feedback._overlay.SLOTS`。
        show_close: 是否显示关闭按钮，默认显示。
        width: 卡片宽度，默认 340。
        offset: 距窗口边缘的距离，默认 24。**同位置的卡片共用第一次的取值**。
        on_click: 点击卡片的回调（关闭按钮不触发）。
        on_close: 消失后的回调。
    """

    def __init__(
        self,
        content: ft.StrOrControl = "",
        *,
        title: ft.StrOrControl = "",
        style_type: StyleType = StyleType.INFO,
        duration: int = DEFAULT_DURATION,
        position: str = "top-right",
        show_close: bool = True,
        width: float = WIDTH,
        offset: int | None = None,
        on_click: Callable[[], None] | None = None,
        on_close: Callable[[], None] | None = None,
    ) -> None:
        if position not in SLOTS:
            raise ValueError(
                f"position 只支持 {', '.join(SLOTS)}，收到 {position!r}"
            )
        self.content = content
        self.title = title
        self.style_type = style_type
        self.duration = duration
        self.position = position
        self.show_close = show_close
        self.width = width
        self.offset = offset
        self.on_click = on_click
        self.on_close = on_close
        self._card: Card | None = None
        self._host: Any = None

    # ------------------------------------------------------------------
    # 便捷入口
    # ------------------------------------------------------------------

    @classmethod
    def open(
        cls, title: ft.StrOrControl = "", content: ft.StrOrControl = "", *,
        page: ft.Page | None = None, **kw: Any,
    ) -> Notification:
        """显示一条通知（默认信息类型）。"""
        return cls(content, title=title, **kw).show(page=page)

    @classmethod
    def success(
        cls, title: ft.StrOrControl = "", content: ft.StrOrControl = "", *,
        page: ft.Page | None = None, **kw: Any,
    ) -> Notification:
        """显示一条成功通知。"""
        return cls(content, title=title, style_type=StyleType.SUCCESS, **kw).show(page=page)

    @classmethod
    def info(
        cls, title: ft.StrOrControl = "", content: ft.StrOrControl = "", *,
        page: ft.Page | None = None, **kw: Any,
    ) -> Notification:
        """显示一条信息通知。"""
        return cls(content, title=title, style_type=StyleType.INFO, **kw).show(page=page)

    @classmethod
    def warning(
        cls, title: ft.StrOrControl = "", content: ft.StrOrControl = "", *,
        page: ft.Page | None = None, **kw: Any,
    ) -> Notification:
        """显示一条警告通知。"""
        return cls(content, title=title, style_type=StyleType.WARNING, **kw).show(page=page)

    @classmethod
    def error(
        cls, title: ft.StrOrControl = "", content: ft.StrOrControl = "", *,
        page: ft.Page | None = None, **kw: Any,
    ) -> Notification:
        """显示一条错误通知。"""
        return cls(content, title=title, style_type=StyleType.ERROR, **kw).show(page=page)

    @classmethod
    def close_all(cls, page: ft.Page | None = None) -> None:
        """关掉当前页四个角上的所有通知。"""
        page = page or ft.context.page
        for position in SLOTS:
            host = peek_host(page, position)
            if host is not None:
                host.clear()

    # ------------------------------------------------------------------
    # 生命周期
    # ------------------------------------------------------------------

    def show(self, page: ft.Page | None = None) -> Notification:
        """显示。可重复调用（会作为新的一条再弹一次）。"""
        page = page or ft.context.page
        self._host = host_for(page, self.position, inset=self.offset, gap=GAP)
        self._card = self._host.push(
            self._build(),
            duration=self.duration,
            on_close=self.on_close,
        )
        return self

    def close(self) -> None:
        """立刻关闭本条（带退场动画）。"""
        if self._host is not None and self._card is not None:
            self._host.close(self._card)

    # ------------------------------------------------------------------
    # 渲染
    # ------------------------------------------------------------------

    def _build(self) -> ft.Control:
        # 两段式：标题行（图标 + 标题 + 关闭）在上，正文另起一行、只缩进到标题。
        # 正文因此能吃到关闭按钮那 30px —— 340 宽的卡片里这是"少折一行"的关键。
        head: list[ft.Control] = [icon_chip(self.style_type, size=24, icon_size=16)]
        head.append(self._title() if self.title else self._body_text(expand=True))
        if self.show_close:
            head.append(self._close_button())

        blocks: list[ft.Control] = [
            ft.Row(
                controls=head,
                spacing=SPACE["2"],
                tight=False,
                vertical_alignment=ft.CrossAxisAlignment.START
                if self.title
                else ft.CrossAxisAlignment.CENTER,
            )
        ]
        if self.title and self.content:
            blocks.append(
                ft.Container(
                    padding=ft.Padding.only(left=ICON + SPACE["2"]),
                    content=self._body_text(),
                )
            )
        return ft.Container(
            width=self.width,
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border=ft.Border.all(1, overlay(0.06)),
            border_radius=RADIUS["xl"],
            padding=ft.Padding.symmetric(horizontal=SPACE["3"] + 2, vertical=SPACE["3"]),
            shadow=elevation(3),
            on_click=self._clicked if self.on_click is not None else None,
            content=ft.Column(controls=blocks, spacing=SPACE["1"], tight=True),
        )

    def _clicked(self, _e: ft.Event[ft.Container]) -> None:
        if self.on_click is not None:
            self.on_click()

    def _title(self) -> ft.Control:
        return ft.Text(
            self.title,
            size=FONT_SIZE["subtitle"],
            weight=FONT_WEIGHT["semibold"],
            color=ft.Colors.ON_SURFACE,
            expand=True,
        )

    def _body_text(self, *, expand: bool = False) -> ft.Control:
        if not isinstance(self.content, str):
            return self.content
        return ft.Text(
            self.content,
            size=FONT_SIZE["body"],
            color=ft.Colors.ON_SURFACE_VARIANT,
            expand=expand,
        )

    def _close_button(self) -> ft.Control:
        return ft.IconButton(
            icon=ft.Icons.CLOSE_ROUNDED,
            icon_size=16,
            width=24,
            height=24,
            padding=0,
            tooltip=t("ui.common.close"),
            style=ft.ButtonStyle(
                color={ft.ControlState.DEFAULT: ft.Colors.ON_SURFACE_VARIANT},
                overlay_color=overlay(0.08),
            ),
            on_click=lambda _e: self.close(),
        )


@ft.component
def App():
    """Notification 运行示例。"""
    page = ft.context.page
    styles = (
        ("默认", StyleType.DEFAULT),
        ("信息", StyleType.INFO),
        ("成功", StyleType.SUCCESS),
        ("警告", StyleType.WARNING),
        ("错误", StyleType.ERROR),
    )

    def show(style: StyleType, name: str) -> Callable[[ft.Event[ft.Button]], None]:
        def _handler(_e: ft.Event[ft.Button]) -> None:
            Notification(
                f"这是一条{name}通知的正文，用来确认标题与正文的排布。",
                title=f"{name}通知",
                style_type=style,
            ).show(page)

        return _handler

    return ft.Column(
        controls=[
            ft.Text("Notification 通知", size=20, weight=ft.FontWeight.BOLD),
            ft.Text(
                "系统级的被动提醒：贴在角落、有标题、可常驻",
                size=13,
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
            ft.Divider(),
            ft.Row(
                wrap=True,
                spacing=10,
                run_spacing=10,
                controls=[
                    ft.Button(name, on_click=show(style, name))
                    for name, style in styles
                ],
            ),
            ft.Row(
                spacing=10,
                controls=[
                    ft.Button(
                        "左下角",
                        on_click=lambda _e: Notification(
                            "从屏幕左下角弹出。",
                            title="自定义位置",
                            position="bottom-left",
                        ).show(page),
                    ),
                    ft.Button(
                        "右下角",
                        on_click=lambda _e: Notification(
                            "从屏幕右下角弹出。",
                            title="自定义位置",
                            position="bottom-right",
                        ).show(page),
                    ),
                    ft.Button(
                        "常驻",
                        on_click=lambda _e: Notification(
                            "不会自动关闭，需要点右上角的 ×。",
                            title="需要处理",
                            style_type=StyleType.WARNING,
                            duration=0,
                        ).show(page),
                    ),
                    ft.Button("全部关闭", on_click=lambda _e: Notification.close_all(page)),
                ],
            ),
        ]
    )


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
