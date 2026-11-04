"""Message 消息提示。

用于**主动操作**之后的反馈：保存成功、请求失败、已复制。它出现在顶部居中、
一行字、几秒后自己走开，不打断手上的事。

与 :class:`~ui.feedback.notification.Notification` 的分界
--------------------------------------------------------
``Message`` 是"我做了什么"的回执，``Notification`` 是"系统发生了什么"的通报。
前者短、居中、无标题；后者长、贴角、有标题与关闭按钮。别把两者用反——
用户对"屏幕顶上掉下来一条"的注意力投放是不同的。

用法::

    Message.success("已保存")
    Message.error("请求失败，请重试", duration=5000)

    # 需要拿到句柄再手动关闭时
    msg = Message("正在同步…", duration=0, show_close=True).show()
    msg.close()

设计取舍
--------
- **不用 ``SnackBar``**：它走弹层栈，一次只能有一条，位置还钉在底部。
  见 :mod:`ui.feedback._overlay`。
- **合并同款**：``grouping=True`` 时，内容与类型都相同的提示不新增，只把
  计数加一（``已保存 ×3``），并重置计时——连点三次不该刷出三条。
- **悬停暂停**：鼠标停在提示上时倒计时冻结，移开续上。
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

from ._look import accent as _accent
from ._look import icon_chip
from ._overlay import Card, host_for, peek_host

__all__ = ["Message"]

POSITION = "top-center"
GAP = 10
#: 卡片宽度。**定宽不是偷懒**：居中靠"给定宽度 + 算左偏移"来定位，
#: 因为撑满宽度的浮层节点会把自己那条横带里的点击全部吃掉（见 _overlay）。
#: 顺带的好处是一叠提示宽度一致，看着像一列而不是一堆。
WIDTH = 360
DEFAULT_DURATION = 3000


class Message:
    """顶部居中的一条提示。

    Args:
        content: 提示文本，或任意控件。
        style_type: 语义类型，决定图标与强调色。
        duration: 自动关闭的毫秒数；``0`` 表示常驻（需要配 ``show_close=True``）。
        show_close: 是否显示关闭按钮。默认不显示——它会自己走。
        center: 文字居中。默认左对齐（图标 + 文本是更常见的读法）。
        grouping: 内容与类型都相同时合并计数，而不是叠出多条。
        width: 卡片宽度，默认 :data:`WIDTH`。**同位置的提示共用第一个取值**。
        offset: 距窗口顶部的距离，默认 20。**同位置的提示共用第一次的取值**。
        on_close: 消失后的回调。
    """

    def __init__(
        self,
        content: ft.StrOrControl = "",
        *,
        style_type: StyleType = StyleType.INFO,
        duration: int = DEFAULT_DURATION,
        show_close: bool = False,
        center: bool = False,
        grouping: bool = False,
        width: float = WIDTH,
        offset: int | None = None,
        on_close: Callable[[], None] | None = None,
    ) -> None:
        self.content = content
        self.style_type = style_type
        self.duration = duration
        self.show_close = show_close
        self.center = center
        self.grouping = grouping
        self.width = width
        self.offset = offset
        self.on_close = on_close
        self._card: Card | None = None
        self._host: Any = None
        self._badge: ft.Text | None = None
        self._badge_box: ft.Container | None = None

    # ------------------------------------------------------------------
    # 便捷入口
    # ------------------------------------------------------------------

    @classmethod
    def open(cls, content: ft.StrOrControl = "", *, page: ft.Page | None = None, **kw: Any) -> Message:
        """显示一条信息提示（默认类型）。"""
        return cls(content, **kw).show(page=page)

    @classmethod
    def success(cls, content: ft.StrOrControl, *, page: ft.Page | None = None, **kw: Any) -> Message:
        """显示一条成功提示。"""
        return cls(content, style_type=StyleType.SUCCESS, **kw).show(page=page)

    @classmethod
    def info(cls, content: ft.StrOrControl, *, page: ft.Page | None = None, **kw: Any) -> Message:
        """显示一条信息提示。"""
        return cls(content, style_type=StyleType.INFO, **kw).show(page=page)

    @classmethod
    def warning(cls, content: ft.StrOrControl, *, page: ft.Page | None = None, **kw: Any) -> Message:
        """显示一条警告提示。"""
        return cls(content, style_type=StyleType.WARNING, **kw).show(page=page)

    @classmethod
    def error(cls, content: ft.StrOrControl, *, page: ft.Page | None = None, **kw: Any) -> Message:
        """显示一条错误提示。"""
        return cls(content, style_type=StyleType.ERROR, **kw).show(page=page)

    @classmethod
    def close_all(cls, page: ft.Page | None = None) -> None:
        """关掉当前页上所有提示。"""
        host = peek_host(page or ft.context.page, POSITION)
        if host is not None:
            host.clear()

    # ------------------------------------------------------------------
    # 生命周期
    # ------------------------------------------------------------------

    def show(self, page: ft.Page | None = None) -> Message:
        """显示。可重复调用（会作为新的一条再弹一次）。"""
        page = page or ft.context.page
        self._host = host_for(page, POSITION, inset=self.offset, gap=GAP)
        self._card = self._host.push(
            self._build(),
            duration=self.duration,
            merge_key=self._merge_key(),
            on_merge=self._on_merge,
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
        accent = _accent(self.style_type)
        controls: list[ft.Control] = [icon_chip(self.style_type), self._body()]
        if self.show_close:
            controls.append(self._close_button())
        if self.grouping:
            controls.append(self._count_badge(accent))
        return ft.Container(
            width=self.width,
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border=ft.Border.all(1, overlay(0.06)),
            border_radius=RADIUS["xl"],
            padding=ft.Padding.symmetric(horizontal=SPACE["3"] + 2, vertical=9),
            shadow=elevation(2),
            content=ft.Row(
                controls=controls,
                spacing=SPACE["2"] + 2,
                tight=False,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER
                if self.center
                else ft.MainAxisAlignment.START,
            ),
        )

    def _body(self) -> ft.Control:
        if isinstance(self.content, str):
            return ft.Text(
                self.content,
                size=FONT_SIZE["body"] + 1,
                color=ft.Colors.ON_SURFACE,
                text_align=ft.TextAlign.CENTER if self.center else ft.TextAlign.START,
                expand=True,
            )
        return self.content

    def _close_button(self) -> ft.Control:
        return ft.IconButton(
            icon=ft.Icons.CLOSE_ROUNDED,
            icon_size=15,
            width=22,
            height=22,
            padding=0,
            tooltip=t("ui.common.close"),
            style=ft.ButtonStyle(
                color={ft.ControlState.DEFAULT: ft.Colors.ON_SURFACE_VARIANT},
                overlay_color=overlay(0.08),
            ),
            on_click=lambda _e: self.close(),
        )

    def _count_badge(self, accent: str) -> ft.Control:
        self._badge = ft.Text(
            "×1",
            size=FONT_SIZE["caption"],
            color=accent,
            weight=FONT_WEIGHT["semibold"],
        )
        self._badge_box = ft.Container(
            bgcolor=ft.Colors.with_opacity(0.12, accent),
            border_radius=RADIUS["full"],
            padding=ft.Padding.symmetric(horizontal=SPACE["1"] + 2, vertical=0),
            content=self._badge,
            visible=False,
        )
        return self._badge_box

    # ------------------------------------------------------------------
    # 合并
    # ------------------------------------------------------------------

    def _merge_key(self) -> Any:
        """内容与类型都相同才合并；传控件时无法比较，一律不合并。"""
        if not self.grouping or not isinstance(self.content, str):
            return None
        return (self.content, self.style_type)

    def _on_merge(self, count: int) -> None:
        if self._badge is not None:
            self._badge.value = f"×{count}"
        if self._badge_box is not None:
            self._badge_box.visible = True

@ft.component
def App():
    """Message 运行示例。"""
    page = ft.context.page
    styles = (
        ("默认", StyleType.DEFAULT),
        ("主要", StyleType.PRIMARY),
        ("信息", StyleType.INFO),
        ("成功", StyleType.SUCCESS),
        ("警告", StyleType.WARNING),
        ("错误", StyleType.ERROR),
    )

    def show(style: StyleType, text: str) -> Callable[[ft.Event[ft.Button]], None]:
        def _handler(_e: ft.Event[ft.Button]) -> None:
            Message(text, style_type=style).show(page)

        return _handler

    return ft.Column(
        controls=[
            ft.Text("Message 消息提示", size=20, weight=ft.FontWeight.BOLD),
            ft.Text(
                "主动操作后的反馈：顶部居中、自动消失、不打断操作",
                size=13,
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
            ft.Divider(),
            ft.Row(
                wrap=True,
                spacing=10,
                run_spacing=10,
                controls=[
                    ft.Button(name, on_click=show(style, f"这是一条{name}提示"))
                    for name, style in styles
                ],
            ),
            ft.Row(
                spacing=10,
                controls=[
                    ft.Button(
                        "可关闭",
                        on_click=lambda _e: Message(
                            "提示会一直留着，直到你点右上角的 ×", duration=0, show_close=True
                        ).show(page),
                    ),
                    ft.Button(
                        "合并计数",
                        on_click=lambda _e: Message(
                            "已保存", style_type=StyleType.SUCCESS, grouping=True
                        ).show(page),
                    ),
                    ft.Button(
                        "长文案",
                        on_click=lambda _e: Message(
                            "这是一条很长的提示文案，用来确认文字会在卡片里折行，"
                            "而不是一路顶出屏幕右边。多行时图标仍然垂直居中。",
                            style_type=StyleType.WARNING,
                        ).show(page),
                    ),
                    ft.Button("全部关闭", on_click=lambda _e: Message.close_all(page)),
                ],
            ),
        ]
    )


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
