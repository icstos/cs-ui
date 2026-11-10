"""状态栏 (StatusBar) —— 窗口底部那一行：左侧统计、右侧状态与动作。

桌面应用的窗口是分层的：顶部工具行、中间内容、**底部一条薄状态栏**。它不抢
注意力，但随时回答三个问题 —— 现在有多少数据、系统是否正常、还能做什么。

为什么与 :class:`~ui.navigation.app_bar.AppBar` 成对存在
----------------------------------------------------------
一条在内容之上、一条在内容之下，承担同一种职责：把「不属于内容本身、但整页
都要知道」的信息放在边上。两者都不进 Material 的 ``View`` 槽位，而是普通
``Container``，所以往任何一列里塞都行。

设计取舍
--------
- **只有状态点带颜色**。把整条状态栏染成红/绿在长会话里会持续抢注意力；一个
  6px 的点足以表达「正常 / 进行中 / 故障」，文字保持中性灰。
- **文字 12px、高度 30**。状态栏是可扫读的辅助信息，不该和正文同档；30 =
  上下各 8px + 一行 14px 行高，再矮就会把字顶到边上。
- **左侧吃满剩余宽度**。统计类文字（"已加载 200 / 9435 条"）长度不固定，
  让它 expand，右侧的状态点与动作才会稳稳贴右，不会随文字长短跳动。
- **``status`` 既能给字符串也能给控件**。需要强调（如故障时用危险色）时传
  一个 :class:`ui.Text` 自己上色，组件不替调用方猜哪种语气该变红。

用法::

    Column([
        ListView(expand=True),
        StatusBar(
            summary="已加载 200 / 9435 条，已选中 1 项",
            status="耗时 102 ms",
            tone="success",
            actions=[IconButton(icon=ft.Icons.DARK_MODE, icon_size=15)],
        ),
    ])
"""

from __future__ import annotations

from dataclasses import field

import flet as ft

from ui.core.doc import Example, Spec, info, run, tip
from ui.core.tokens import FONT_SIZE, FONT_WEIGHT, RADIUS, SPACE, accent_fill, hairline

__all__ = ["StatusBar"]

HEIGHT = 30
#: 状态点的直径。6px 是「一眼看见但不刺眼」的下限：再小在 1.25 倍缩放下会糊掉。
DOT = 6

#: 状态点可用的语气 → 由 cs-ui 的语义色解析（M3 没有 success/warning 这些角色）。
TONES: tuple[str, ...] = ("neutral", "info", "success", "warning", "danger")


@ft.control
class StatusBar(ft.Container):
    """窗口底部的一行状态栏。

    .. warning::
        左侧字段叫 ``summary`` 而不是 ``left`` —— ``ft.Container`` 自己就有
        ``left``（Stack 里的定位偏移），重名会让 Container 把文案当作坐标发给
        Flutter，客户端直接整页白屏且 **Python 侧不报任何错**（实测踩过）。

    Args:
        summary: 左侧统计文案，``str`` 或任意控件。给字符串时按次要文字着色并吃满宽度。
        status: 右侧状态文案，``str`` 或任意控件。给控件时样式由调用方负责。
        tone: 状态点的语气，取 :data:`TONES`；未知值退回 ``neutral``（不抛异常）。
        actions: 最右侧的动作控件，通常是一两个 ``IconButton``。
        show_dot: 是否显示状态点。没有状态可报（纯统计条）时关掉。
        divider: 顶部发丝线。默认开 —— 状态栏与内容之间需要一条边界。
    """

    summary: ft.StrOrControl = ""
    status: ft.StrOrControl = ""
    tone: str = "neutral"
    actions: list[ft.Control] = field(default_factory=list)
    show_dot: bool = True
    divider: bool = True

    def init(self):
        # height / padding 在 init() 里设，不做成构造参数：Container 已经有这两个
        # 字段，重复声明会把位置参数挤乱（AppBar 踩过同一个坑）。
        self.height = HEIGHT
        self.padding = ft.Padding(SPACE["3"], SPACE["1"], SPACE["1"], SPACE["1"])
        self.bgcolor = self.bgcolor or ft.Colors.SURFACE_CONTAINER_LOW
        if self.divider:
            self.border = self.border or ft.Border(top=hairline())

        self.content = ft.Row(
            spacing=SPACE["1"],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                self._side(self.summary, expand=True),
                *([self._dot()] if self.show_dot else []),
                self._side(self.status),
                *self.actions,
            ],
        )

    # ------------------------------------------------------------------
    def _side(self, value: ft.StrOrControl, *, expand: bool = False) -> ft.Control:
        """字符串按次要文字渲染；控件原样放过，样式归调用方。"""
        if not isinstance(value, str):
            return value
        return ft.Text(
            value,
            size=FONT_SIZE["small"],
            weight=FONT_WEIGHT["regular"],
            color=ft.Colors.ON_SURFACE_VARIANT,
            expand=expand,
            no_wrap=True,
            overflow=ft.TextOverflow.ELLIPSIS,
        )

    def _dot(self) -> ft.Control:
        """状态点：用语义色的**实底**而不是文字色 —— 小色块要压得住，淡一档就看不见。"""
        tone = self.tone if self.tone in TONES else "neutral"
        return ft.Container(
            width=DOT,
            height=DOT,
            border_radius=RADIUS["full"],
            bgcolor=ft.Colors.OUTLINE if tone == "neutral" else accent_fill(tone),
        )


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
def _frame(*controls: ft.Control) -> ft.Control:
    """把状态栏和一块内容框在一起，看得见它「贴底」的关系。"""
    return ft.Container(
        border_radius=RADIUS["md"],
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        content=ft.Column(spacing=0, controls=list(controls)),
    )


def _body(text: str, height: int = 96) -> ft.Control:
    return ft.Container(
        height=height,
        padding=SPACE["4"],
        alignment=ft.Alignment.CENTER_LEFT,
        content=ft.Text(
            text, size=FONT_SIZE["small"], color=ft.Colors.ON_SURFACE_VARIANT
        ),
    )


@ft.component
def _basic() -> ft.Control:
    return _frame(
        _body("上面是内容区，下面是状态栏 —— 它们是同级的兄弟，谁高谁矮由内容决定。"),
        StatusBar(
            summary="已加载 200 / 9435 条，已选中 1 项",
            status="耗时 102 ms",
            tone="success",
        ),
    )


@ft.component
def _tone() -> ft.Control:
    """五种语气叠在一起：只有点和文案的语气在变，整条底色不动。"""
    rows = [
        ("数据库已连接 · 延迟 3 ms", "就绪", "success"),
        ("正在同步 1 283 条变更", "进行中", "warning"),
        ("对象存储不可达", "重试 2/5", "danger"),
        ("只读模式：许可证将在 7 天后过期", "提示", "info"),
        ("没有可显示的内容", "空闲", "neutral"),
    ]
    return ft.Container(
        border_radius=RADIUS["md"],
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        content=ft.Column(
            spacing=0,
            controls=[
                StatusBar(summary=left, status=status, tone=tone)
                for left, status, tone in rows
            ],
        ),
    )


@ft.component
def _actions() -> ft.Control:
    """右侧动作：把「总是可用」的入口（主题、设置）放在这里，比塞进工具栏稳。"""
    page = ft.context.page
    return _frame(
        _body("动作贴右：左栏文字变长时，右侧按钮不会跟着左右跳。"),
        StatusBar(
            summary="12 个文件 · 3 个待确认 · 最后同步于 2 分钟前",
            status="sync 已完成",
            tone="success",
            actions=[
                ft.IconButton(
                    icon=ft.Icons.DARK_MODE,
                    icon_size=15,
                    icon_color=ft.Colors.ON_SURFACE_VARIANT,
                    tooltip="切换深色主题",
                    on_click=lambda: page.show_dialog(ft.SnackBar("切换主题")),
                ),
                ft.IconButton(
                    icon=ft.Icons.SETTINGS_OUTLINED,
                    icon_size=15,
                    icon_color=ft.Colors.ON_SURFACE_VARIANT,
                    tooltip="设置",
                    on_click=lambda: page.show_dialog(ft.SnackBar("打开设置")),
                ),
            ],
        ),
    )


SPEC = Spec(
    name="StatusBar",
    summary="窗口底部那一行：左侧统计、右侧状态点与动作。",
    definition=(
        "桌面应用的窗口是分层的：顶部工具行、中间内容、底部一条薄状态栏。状态栏"
        "放「不属于内容本身、但整页都要知道」的信息 —— 有多少数据、系统是否正常、"
        "还能做什么。它用普通 Container 实现，放进任何一列都行，不占 Material 的"
        "View 槽位。"
    ),
    anatomy=[
        ("左栏", "统计与说明，吃满剩余宽度；文字长也不推动右侧的点和按钮。"),
        ("状态点", "6px 圆点，语气由 tone 决定。只有它带颜色，整条底色保持中性。"),
        ("状态文案", "一句话说明当前状态。需要强调时可传 Text 自己上色。"),
        ("动作区", "最右侧的常驻入口（主题、设置）。贴右对齐，不随左栏文字跳动。"),
        ("顶部分隔线", "一条发丝线；关掉它，状态栏会与内容粘成一片。"),
    ],
    when=[
        "桌面应用需要在窗口底部常驻「有多少、正不正常」",
        "列表 / 表格页：结果量、选中量、耗时这类随时要看的信息",
        "需要放一两个「总是可用」的入口（主题、设置、连接状态）",
    ],
    avoid=[
        "移动端页面：底部已被导航栏占据，状态栏会被挤成两层",
        "要传达的是一条会过期的消息（保存成功 / 请求失败）：用 Message 或 Notification",
        "信息量多到要滚动：那是折叠面板的事，状态栏只放一句话",
    ],
    examples=[
        Example(
            "基础用法",
            _basic,
            hint="左统计 + 状态点 + 耗时；高度 30、文字 12px，贴底不抢戏。",
        ),
        Example(
            "语气",
            _tone,
            hint="success / warning / danger / info / neutral 五种点色，底色与文字都不变。",
        ),
        Example(
            "右侧动作",
            _actions,
            hint="actions 贴右；左侧文案变长时按钮位置不动。",
        ),
    ],
    target=StatusBar,
    notes=[
        info(
            "只有状态点带颜色是有意的：整条染色的状态栏在长会话里会持续抢注意力，"
            "而 6px 的点已经足够表达「正常 / 进行中 / 故障」。"
        ),
        tip(
            "状态文案需要变红时，传一个 Text（例如 color=semantic_text('danger')）"
            "而不是给组件加开关 —— 语气由调用方决定，组件不猜。"
        ),
        (
            "warn",
            "高度固定在 init() 里是 30px：状态栏不是操作区，塞进 36 以上的控件"
            "（大按钮）会把它顶开。需要动作就用 icon_size 15~18 的小图标按钮。",
        ),
        (
            "warn",
            "左侧字段叫 summary 而不是 left。ft.Container 自己就有 left / top / "
            "right / bottom（Stack 定位），重名会让文案被当成坐标发给 Flutter："
            "客户端整页白屏，而 Python 侧一句错都不报。",
        ),
    ],
    tags=("状态栏", "底部栏", "statusbar", "status", "统计", "导航"),
)


if __name__ == "__main__":
    run(SPEC)
