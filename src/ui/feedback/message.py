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
- **宽度跟窗口**：360 的定宽在窄窗口里会顶出右边，显示时按可用宽度收一收。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import flet as ft

from ui.core.constants import StyleType
from ui.core.doc import Api, Example, Spec, info, run, tip, warn
from ui.core.i18n import t
from ui.core.tokens import (
    FONT_SIZE,
    FONT_WEIGHT,
    RADIUS,
    SEMANTIC_TINT,
    SPACE,
    elevation,
    overlay,
)
from ui.input.button import Button

from ._look import accent as _accent
from ._look import icon_chip
from ._overlay import DEFAULT_INSET, Card, host_for, peek_host

__all__ = ["Message"]

POSITION = "top-center"
GAP = 10
#: 卡片宽度。**定宽不是偷懒**：居中靠"给定宽度 + 算左偏移"来定位，
#: 因为撑满宽度的浮层节点会把自己那条横带里的点击全部吃掉（见 _overlay）。
#: 顺带的好处是一叠提示宽度一致，看着像一列而不是一堆。
WIDTH = 360
DEFAULT_DURATION = 3000

#: 语义类型 → (按钮文案, 提示内容)。示例用，不参与组件逻辑。
_SEMANTIC_DEMOS: tuple[tuple[str, str, StyleType], ...] = (
    ("成功", "已保存 3 项修改", StyleType.SUCCESS),
    ("警告", "网络较慢，保存可能需要几秒", StyleType.WARNING),
    ("错误", "保存失败，请检查网络后重试", StyleType.ERROR),
    ("信息", "有新版本可用，重启后生效", StyleType.INFO),
)


class Message:
    """顶部居中的一条提示。

    Args:
        content: 提示文本，或任意控件。
        style_type: 语义类型，决定图标与强调色。
        duration: 自动关闭的毫秒数；``0`` 表示常驻（需要配 ``show_close=True``）。
        show_close: 是否显示关闭按钮。默认不显示——它会自己走。
        center: 文字居中。默认左对齐（图标 + 文本是更常见的读法）。
        grouping: 内容与类型都相同时合并计数，而不是叠出多条。
        width: 卡片宽度，默认 :data:`WIDTH`；窗口更窄时按可用宽度收缩。
        offset: 距窗口顶部的距离；``None`` 用该位置的默认值 20。
            **同位置的提示共用第一次的取值**。
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
    def open(
        cls, content: ft.StrOrControl = "", *, page: ft.Page | None = None, **kw: Any
    ) -> Message:
        """显示一条信息提示（默认类型）。"""
        return cls(content, **kw).show(page=page)

    @classmethod
    def success(
        cls, content: ft.StrOrControl, *, page: ft.Page | None = None, **kw: Any
    ) -> Message:
        """显示一条成功提示。"""
        return cls(content, style_type=StyleType.SUCCESS, **kw).show(page=page)

    @classmethod
    def info(
        cls, content: ft.StrOrControl, *, page: ft.Page | None = None, **kw: Any
    ) -> Message:
        """显示一条信息提示。"""
        return cls(content, style_type=StyleType.INFO, **kw).show(page=page)

    @classmethod
    def warning(
        cls, content: ft.StrOrControl, *, page: ft.Page | None = None, **kw: Any
    ) -> Message:
        """显示一条警告提示。"""
        return cls(content, style_type=StyleType.WARNING, **kw).show(page=page)

    @classmethod
    def error(
        cls, content: ft.StrOrControl, *, page: ft.Page | None = None, **kw: Any
    ) -> Message:
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
            self._build(self._fit_width(page)),
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

    def _fit_width(self, page: ft.Page) -> float:
        """把定宽收进窗口：360 的卡片在 400px 的窗口里会顶掉右边。

        只在本条显示时算一次 —— 浮层节点是绝对定位的，窗口缩放不会重排，
        但下次弹出的提示会按新宽度来。
        """
        try:
            available = float(getattr(page, "width", 0) or 0)
        except (TypeError, ValueError):
            return self.width
        if available <= 0:
            return self.width
        inset = self.offset if self.offset is not None else DEFAULT_INSET[POSITION]
        usable = available - 2 * inset - GAP
        return min(self.width, usable) if usable > 0 else self.width

    def _build(self, width: float | None = None) -> ft.Control:
        accent = _accent(self.style_type)
        controls: list[ft.Control] = [icon_chip(self.style_type), self._body()]
        if self.show_close:
            controls.append(self._close_button())
        if self.grouping:
            controls.append(self._count_badge(accent))
        return ft.Container(
            width=self.width if width is None else width,
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border=ft.Border.all(1, overlay(0.06)),
            border_radius=RADIUS["xl"],
            padding=ft.Padding.symmetric(horizontal=SPACE["4"] + 2, vertical=8),
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
            bgcolor=ft.Colors.with_opacity(SEMANTIC_TINT, accent),
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


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
def _caption(text: str) -> ft.Control:
    return ft.Text(text, size=FONT_SIZE["small"], color=ft.Colors.ON_SURFACE_VARIANT)


@ft.component
def _semantics() -> ft.Control:
    """四条语义色各弹一次：颜色只落在图标块上，正文永远是正文色。"""
    page = ft.context.page

    def trigger(text: str, style: StyleType) -> Callable[[Any], None]:
        def _handler(_e: Any) -> None:
            Message(text, style_type=style).show(page)

        return _handler

    return ft.Column(
        spacing=12,
        controls=[
            ft.Row(
                spacing=10,
                wrap=True,
                run_spacing=10,
                controls=[
                    Button(
                        label,
                        style_type=StyleType.PRIMARY,
                        plain=True,
                        on_click=trigger(text, style),
                    )
                    for label, text, style in _SEMANTIC_DEMOS
                ],
            ),
            _caption(
                "点任意一个：提示从顶部居中落下，3 秒后自己走开；"
                "期间鼠标停在上面会暂停计时。"
            ),
        ],
    )


@ft.component
def _close_and_merge() -> ft.Control:
    """常驻提示要自己给关闭按钮；同款提示合并成一条并重置计时。"""
    page = ft.context.page
    return ft.Column(
        spacing=12,
        controls=[
            ft.Row(
                spacing=10,
                wrap=True,
                run_spacing=10,
                controls=[
                    Button(
                        "常驻（带关闭）",
                        style_type=StyleType.PRIMARY,
                        plain=True,
                        on_click=lambda _e: Message(
                            "导出任务已开始，完成后会自动下载。",
                            duration=0,
                            show_close=True,
                        ).show(page),
                    ),
                    Button(
                        "点三次「已保存」",
                        plain=True,
                        on_click=lambda _e: Message(
                            "已保存",
                            style_type=StyleType.SUCCESS,
                            grouping=True,
                        ).show(page),
                    ),
                    Button("全部关闭", on_click=lambda _e: Message.close_all(page)),
                ],
            ),
            _caption(
                "duration=0 的提示不会自己走，所以必须给关闭按钮；"
                "grouping 把内容与类型都相同的合并成「×3」，计时也重新开始。"
            ),
        ],
    )


@ft.component
def _long_text() -> ft.Control:
    """定宽卡片里的长文案：折行而不是一路顶出屏幕右边。"""
    page = ft.context.page
    text = (
        "连接已断开，正在重试。恢复后会自动继续同步刚才那 12 个文件，"
        "不需要重新点一次保存，也不会重复上传。"
    )
    return ft.Column(
        spacing=12,
        controls=[
            Button(
                "长文案",
                plain=True,
                on_click=lambda _e: Message(text, style_type=StyleType.WARNING).show(
                    page
                ),
            ),
            _caption("360 的定宽让多行提示折行；图标跟着文本块垂直居中，不贴第一行。"),
        ],
    )


_SEMANTICS_CODE = """from ui.core.constants import StyleType
from ui.feedback import Message

Message.success("已保存")                  # 3 秒后自动消失
Message.warning("网络较慢，保存可能需要几秒")
Message.error("保存失败，请重试", duration=5000)

# 常驻：等用户自己关（duration=0 必须配 show_close）
Message("正在导出…", duration=0, show_close=True).show(page)"""

_MERGE_CODE = """# 内容与类型都相同的提示合并成一条，徽标显示 ×3
Message("已保存", style_type=StyleType.SUCCESS, grouping=True).show(page)

# 一次清掉当前页所有提示
Message.close_all(page)"""


SPEC = Spec(
    name="Message",
    summary="主动操作后的回执：顶部居中的一条提示，默认 3 秒后自己走开。",
    definition=(
        "Message 回答的是「我刚才那一下成了没有」。它挂在页面浮层上、顶部居中，"
        "一行字配一个类型图标，默认 3 秒后自动消失，不占布局、不要求用户做任何事。"
        "正因为不拦人，它承载不了「要不要继续」这类需要回应的决定 —— 那种场合"
        "交给 AlertDialog，一个能点到按钮、也必须被处理的地方。"
    ),
    anatomy=[
        (
            "图标块",
            (
                "22px 的淡底方块 + 语义图标。颜色只出现在这里：底是 12% 的强调色，"
                "深色主题下不发亮，类型也能先于文字被读到。"
            ),
        ),
        (
            "正文",
            (
                "单行居中偏左的文本，也可以直接传控件（进度、按钮行）。默认左对齐 —— "
                "图标 + 文字从左往右读，比整体居中更像一条通知。"
            ),
        ),
        (
            "关闭按钮",
            (
                "show_close=True 才出现的 22px ×。默认不给：会自动走的提示多一个动作"
                "只是噪声；而 duration=0 的常驻提示没有它就关不掉。"
            ),
        ),
        (
            "计数徽标",
            (
                "grouping=True 时在右侧出现的「×3」：同款提示合并成一条，连点三次"
                "不该刷出三条。"
            ),
        ),
        (
            "浮层栈",
            (
                "同一页面、同一位置只有一个浮层节点，多条提示在列里往下排；进出场只改"
                "opacity 与 offset，由 Flutter 补间，不逐帧回调。"
            ),
        ),
    ],
    when=[
        "保存、复制、导出这类主动动作完成之后，给一句「成了」",
        "操作失败但不影响继续，只需要说明原因",
        "后台任务开始或结束，用户不必停下手里的输入",
    ],
    avoid=[
        "需要用户确认或选择：用 AlertDialog，提示条里放按钮既难点也容易误触",
        "系统级、需要事后回看的消息：用 Notification，它贴角常驻、有标题",
        "表单字段级的校验错误：写在字段下方，飘在顶部的提示离出错那一格太远",
    ],
    examples=[
        Example(
            "四种语义",
            _semantics,
            hint="成功 / 警告 / 错误 / 信息各弹一次，正文始终是正文色，只有图标块变色。",
            code=_SEMANTICS_CODE,
        ),
        Example(
            "常驻与合并",
            _close_and_merge,
            hint="duration=0 配关闭按钮；grouping 把重复提示收成一条并重置计时。",
            code=_MERGE_CODE,
        ),
        Example(
            "长文案",
            _long_text,
            hint="定宽 360 的卡片里折行，而不是一路顶出屏幕右边。",
        ),
    ],
    api=[
        Api("content", "str | Control", '""', "提示正文；也可以直接给控件"),
        Api(
            "style_type",
            "StyleType",
            "StyleType.INFO",
            "语义类型，决定图标与计数徽标的颜色",
        ),
        Api("duration", "int", "3000", "自动关闭的毫秒数；0 表示常驻"),
        Api("show_close", "bool", "False", "显示右上角关闭按钮，常驻提示必须打开"),
        Api("center", "bool", "False", "文字居中；默认左对齐"),
        Api("grouping", "bool", "False", "内容与类型都相同时合并计数"),
        Api("width", "float", "360", "卡片宽度；窄窗口下按可用宽度收缩"),
        Api("offset", "int | None", "None", "距顶部距离；None 用默认值 20"),
        Api("show(page)", "Message", "—", "挂到浮层上；每次调用都是新的一条"),
        Api("close()", "None", "—", "立刻关闭本条，带退场动画"),
    ],
    notes=[
        tip(
            "duration=0 时必须同时给 show_close=True：常驻是给「需要读完」的提示用的，"
            "不是省掉关闭按钮的理由，否则这条提示只能等下一次 close_all。"
        ),
        info(
            "同一位置（顶部居中）只有一条浮层，多条提示在列里往下排；offset 由第一条"
            "决定，后面的提示传不同的值不会生效。"
        ),
        warn(
            "卡片定宽是为了让一叠提示宽度一致。窗口比卡片窄时会按可用宽度收缩，"
            "所以同一条提示在宽窄不同的窗口里不保证同宽。"
        ),
    ],
    tags=("消息", "提示", "toast", "message", "反馈"),
)


if __name__ == "__main__":
    run(SPEC)
