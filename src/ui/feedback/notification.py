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
- **正文吃满宽度**：正文独立成段并缩进到标题左侧，右侧借用关闭按钮的位置，
  360 宽的卡片里这是少折一行的关键。
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
    SPACE,
    elevation,
    overlay,
)
from ui.input.button import Button

from ._look import icon_chip
from ._overlay import SLOTS, OverlayCard, host_for, peek_host

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
        width: 卡片宽度，默认 360。
        offset: 距窗口边缘的距离；``None`` 用该位置的默认值 24。
            **同位置的卡片共用第一次的取值**。
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
            raise ValueError(f"position 只支持 {', '.join(SLOTS)}，收到 {position!r}")
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
        self._card: OverlayCard | None = None
        self._host: Any = None

    # ------------------------------------------------------------------
    # 便捷入口
    # ------------------------------------------------------------------

    @classmethod
    def open(
        cls,
        title: ft.StrOrControl = "",
        content: ft.StrOrControl = "",
        *,
        page: ft.Page | None = None,
        **kw: Any,
    ) -> Notification:
        """显示一条通知（默认信息类型）。"""
        return cls(content, title=title, **kw).show(page=page)

    @classmethod
    def success(
        cls,
        title: ft.StrOrControl = "",
        content: ft.StrOrControl = "",
        *,
        page: ft.Page | None = None,
        **kw: Any,
    ) -> Notification:
        """显示一条成功通知。"""
        return cls(content, title=title, style_type=StyleType.SUCCESS, **kw).show(
            page=page
        )

    @classmethod
    def info(
        cls,
        title: ft.StrOrControl = "",
        content: ft.StrOrControl = "",
        *,
        page: ft.Page | None = None,
        **kw: Any,
    ) -> Notification:
        """显示一条信息通知。"""
        return cls(content, title=title, style_type=StyleType.INFO, **kw).show(
            page=page
        )

    @classmethod
    def warning(
        cls,
        title: ft.StrOrControl = "",
        content: ft.StrOrControl = "",
        *,
        page: ft.Page | None = None,
        **kw: Any,
    ) -> Notification:
        """显示一条警告通知。"""
        return cls(content, title=title, style_type=StyleType.WARNING, **kw).show(
            page=page
        )

    @classmethod
    def error(
        cls,
        title: ft.StrOrControl = "",
        content: ft.StrOrControl = "",
        *,
        page: ft.Page | None = None,
        **kw: Any,
    ) -> Notification:
        """显示一条错误通知。"""
        return cls(content, title=title, style_type=StyleType.ERROR, **kw).show(
            page=page
        )

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
        # 正文因此能吃到关闭按钮那 30px —— 360 宽的卡片里这是"少折一行"的关键。
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
            padding=ft.Padding.symmetric(
                horizontal=SPACE["3"] + 2, vertical=SPACE["3"]
            ),
            shadow=elevation(3),
            on_click=self._clicked if self.on_click is not None else None,
            content=ft.Column(controls=blocks, spacing=SPACE["1"], tight=True),
        )

    def _clicked(self, _e: ft.Event[ft.Container]) -> None:
        if self.on_click is not None:
            self.on_click()

    def _title(self) -> ft.Control:
        if not isinstance(self.title, str):
            return ft.Container(expand=True, content=self.title)
        return ft.Text(
            self.title,
            size=FONT_SIZE["body"],
            weight=FONT_WEIGHT["semibold"],
            color=ft.Colors.ON_SURFACE,
            expand=True,
        )

    def _body_text(self, *, expand: bool = False) -> ft.Control:
        if not isinstance(self.content, str):
            # 传控件时同样要吃掉标题行的剩余宽度，否则关闭按钮会贴着它站
            return (
                ft.Container(expand=True, content=self.content)
                if expand
                else self.content
            )
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


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
def _caption(text: str) -> ft.Control:
    return ft.Text(text, size=FONT_SIZE["small"], color=ft.Colors.ON_SURFACE_VARIANT)


@ft.component
def _basic() -> ft.Control:
    """一张最普通的通知卡：标题 + 正文 + 关闭，4.5 秒后自己收起。"""
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
                        "同步完成",
                        style_type=StyleType.PRIMARY,
                        plain=True,
                        on_click=lambda _e: Notification(
                            "3 个组件已更新到最新版本。",
                            title="同步完成",
                            style_type=StyleType.SUCCESS,
                        ).show(page),
                    ),
                    Button(
                        "连接中断（常驻）",
                        style_type=StyleType.ERROR,
                        plain=True,
                        on_click=lambda _e: Notification(
                            "正在重试，恢复后会自动继续同步。",
                            title="连接已断开",
                            style_type=StyleType.ERROR,
                            duration=0,
                        ).show(page),
                    ),
                    Button(
                        "贴左下角",
                        plain=True,
                        on_click=lambda _e: Notification(
                            "从屏幕左下角长出来，新的一条排在更下面。",
                            title="自定义位置",
                            position="bottom-left",
                        ).show(page),
                    ),
                    Button(
                        "全部关闭", on_click=lambda _e: Notification.close_all(page)
                    ),
                ],
            ),
            _caption(
                "默认贴右上角：有标题就把正文压到下一行并缩进，没有标题时图标、"
                "正文、关闭按钮排成一行。"
            ),
        ],
    )


@ft.component
def _with_actions() -> ft.Control:
    """正文里放按钮：通知自己不会关，等用户在卡片上做选择。"""
    page = ft.context.page
    holder: dict[str, Notification] = {}

    def open_card(_e: Any) -> None:
        def later(_ev: Any) -> None:
            holder["n"].close()
            Notification(
                "10 分钟后会再提醒一次。",
                title="已推迟",
                style_type=StyleType.INFO,
            ).show(page)

        def done(_ev: Any) -> None:
            holder["n"].close()

        card = Notification(
            title="构建完成",
            content=ft.Column(
                spacing=SPACE["2"],
                controls=[
                    ft.Text(
                        "产物已生成，可以部署到预览环境。",
                        size=FONT_SIZE["body"],
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                    ft.Row(
                        spacing=SPACE["1"],
                        controls=[
                            ft.TextButton("稍后", on_click=later),
                            ft.TextButton("查看产物", on_click=done),
                        ],
                    ),
                ],
            ),
            duration=0,
        )
        holder["n"] = card
        card.show(page)

    return ft.Column(
        spacing=12,
        controls=[
            Button(
                "带操作的通知",
                style_type=StyleType.PRIMARY,
                plain=True,
                on_click=open_card,
            ),
            _caption(
                "操作按钮放在 content 里（组件本身没有 actions 参数）："
                "duration=0 常驻，点任意一个按钮后主动 close()。"
            ),
        ],
    )


@ft.component
def _icon_and_time() -> ft.Control:
    """图标与时间戳：把元信息做成正文的第一行，位置换到右下角。"""
    page = ft.context.page

    def open_card(_e: Any) -> None:
        content = ft.Column(
            spacing=SPACE["1"],
            controls=[
                ft.Row(
                    spacing=SPACE["1"],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(
                            ft.Icons.HISTORY_ROUNDED,
                            size=14,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        ft.Text(
                            "2 分钟前",
                            size=FONT_SIZE["caption"],
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                    ],
                ),
                ft.Text(
                    "「组件文档」的 3 处示例已由后台自动保存。",
                    size=FONT_SIZE["body"],
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
            ],
        )
        Notification(
            title="草稿已保存",
            content=content,
            style_type=StyleType.INFO,
            position="bottom-right",
            duration=0,
        ).show(page)

    return ft.Column(
        spacing=12,
        controls=[
            Button("图标与时间", plain=True, on_click=open_card),
            _caption("类型图标在标题左侧，时间这类次要信息放进正文的第一行。"),
        ],
    )


_BASIC_CODE = """from ui.core.constants import StyleType
from ui.feedback import Notification

Notification.success("同步完成", "3 个组件已更新到最新版本")

# 常驻：系统级问题不该「没看见就走了」
Notification(
    title="连接已断开",
    content="正在重试，恢复后会自动继续同步。",
    style_type=StyleType.ERROR,
    duration=0,            # 0 = 不自动关闭
).show(page)"""

_ACTION_CODE = """# 组件没有 actions 参数：按钮放进 content 里
card = Notification(
    title="构建完成",
    content=Column([
        Text("产物已生成，可以部署到预览环境。"),
        Row([TextButton("稍后", on_click=lambda _: card.close())]),
    ]),
    duration=0,
)
card.show(page)"""


SPEC = Spec(
    name="Notification",
    summary="贴在窗口角落的通知卡：有标题、可带操作，也能一直挂着等人处理。",
    definition=(
        "Notification 通报的是「系统发生了什么」：后台同步完成、有新版本、连接断了。"
        "它从窗口的某个角浮出来，带标题与正文，默认 4.5 秒后收起，也可以用 "
        "duration=0 常驻。和 Message 的区别不在长相而在职责 —— 一条是操作回执，"
        "一条是用户即使没盯着屏幕也该知道的消息。"
    ),
    anatomy=[
        (
            "图标块",
            (
                "24px 的淡底方块 + 语义图标，与标题同一行。底色只有 12% 的强调色，"
                "四张通知叠在一起时也不会变成一排色块。"
            ),
        ),
        (
            "标题行",
            (
                "图标、标题、关闭按钮。标题是 14px 半粗的正文色；没有标题时图标、正文、"
                "关闭按钮直接排成一行，高度少一截。"
            ),
        ),
        (
            "正文",
            (
                "独立成段、左边缩进到标题（24 + 8），右边借用关闭按钮让出的宽度；"
                "360 宽的卡片里这是「少折一行」的关键。"
            ),
        ),
        (
            "操作区",
            (
                "把按钮放进 content 里的一个 Row。组件本身不给 actions —— 文案与个数"
                "都归调用方，组件只保证卡片不拦事件。"
            ),
        ),
        (
            "锚点",
            (
                "四个角任选，默认右上；贴底的两个位置，新通知从下面长出来，"
                "最新的那条永远贴着屏幕边缘。"
            ),
        ),
    ],
    when=[
        "后台任务完成或失败，用户当时可能在看别的区域",
        "需要事后处理的系统消息：新版本、配额、连接状态",
        "多个任务并行，要把各自的进度分开通报",
    ],
    avoid=[
        "用户刚点的那一下的回执：用 Message，角落离视线中心太远",
        "需要立刻做决定的事：用 AlertDialog，通知可以被划走",
        "正文超过三四行：进详情页或侧栏，通知里塞长文没人读",
    ],
    examples=[
        Example(
            "基础通知",
            _basic,
            hint="标题 + 正文 + 关闭；常驻与贴左下角也在这一组按钮里。",
            code=_BASIC_CODE,
        ),
        Example(
            "带操作按钮",
            _with_actions,
            hint="按钮放进 content，duration=0 常驻，点完由调用方 close()。",
            code=_ACTION_CODE,
        ),
        Example(
            "图标与时间",
            _icon_and_time,
            hint="时间这类元信息做成正文第一行；位置换到右下角。",
        ),
    ],
    api=[
        Api("content", "str | Control", '""', "正文；也可以直接给控件（含按钮行）"),
        Api("title", "str | Control", '""', "标题；留空则图标与正文排成一行"),
        Api(
            "style_type",
            "StyleType",
            "StyleType.INFO",
            "语义类型，决定图标与强调色",
        ),
        Api("duration", "int", "4500", "自动关闭的毫秒数；0 表示常驻"),
        Api("position", "str", '"top-right"', "四角之一，另有 top-center"),
        Api("show_close", "bool", "True", "显示关闭按钮；常驻通知别关掉它"),
        Api("width", "float", "360", "卡片宽度"),
        Api("offset", "int | None", "None", "距窗口边缘距离；None 用该位置默认值 24"),
        Api(
            "on_click",
            "Callable[[], None] | None",
            "None",
            "点整卡的回调，关闭按钮不触发",
        ),
        Api(
            "on_close",
            "Callable[[], None] | None",
            "None",
            "消失（含自动关闭）后的回调",
        ),
    ],
    notes=[
        info(
            "标题与正文是两段：有标题时正文缩进到标题左侧，因此右侧能吃满关闭按钮"
            "让出的那 30px；没有标题时三者排成一行，卡片更矮。title 与 content 都"
            "接受控件，标题会被包进一个撑满的容器，正文则原样交给调用方排版。"
        ),
        warn(
            "position 在构造时就校验，写错立刻抛 ValueError，不会静默落到默认角落；"
            "top-center 与 Message 抢同一个位置，两条同时出现会叠在一起。"
        ),
        tip(
            "系统级问题用 duration=0，并保留默认的关闭按钮。自动收起的通知只适合"
            "「看一眼就够」的信息，需要处理的必须由用户自己结束它。"
        ),
    ],
    tags=("通知", "notification", "角标", "系统消息", "反馈"),
)


if __name__ == "__main__":
    run(SPEC)
