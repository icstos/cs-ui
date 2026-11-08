"""列表项 (ListTile) —— 列表里的一行：头像 / 图标 + 主副标题 + 尾部操作。

一行要同时说清三件事：谁（``leading``）、是什么（``title`` / ``subtitle``）、
能对它做什么（``trailing``）。这三段交给 :class:`flet.ListTile` 排版，行高、
垂直居中、最小触摸区都由 Material 的密度规则给出 —— 所以同一个页面里的名单、
设置项、搜索结果看起来是同一套行，而不是三种手拼的 ``Row``。

用法::

    ListTile(
        leading=CircleAvatar(content=Text("林")),
        title=Text("SO-1042 退款审核"),
        subtitle=Text("林一舟 · ¥1,280 · 2 小时前"),
        trailing=Icon(Icons.CHEVRON_RIGHT, size=18),
        on_click=open_ticket,
    )

两条容易踩的：两行副标题必须同时开 ``is_three_line=True``，否则 Flutter 仍按
两行排版、高度不够，第二行会被裁掉；整行可点时尾部只放图标，别再放按钮 ——
两个点击目标会互相抢手势，用户也分不清点中的是哪一个。
"""

from __future__ import annotations

import flet as ft

from ui.core.doc import Api, Example, Spec, info, run, tip, warn
from ui.core.tokens import FONT_SIZE, FONT_WEIGHT

__all__ = ["ListTile"]

MUTED = ft.Colors.ON_SURFACE_VARIANT


@ft.control
class ListTile(ft.ListTile):
    """列表里的一行。参数与 :class:`flet.ListTile` 完全一致，不预设任何样式。

    Notes:
        两行副标题要自己开 ``is_three_line``：控件不会替你猜副标题有几行，
        猜错的表现是第二行被裁掉一半。
    """


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
def _avatar(initial: str) -> ft.Control:
    return ft.CircleAvatar(
        radius=16,
        bgcolor=ft.Colors.SECONDARY_CONTAINER,
        color=ft.Colors.ON_SECONDARY_CONTAINER,
        content=ft.Text(initial, size=FONT_SIZE["small"], weight=FONT_WEIGHT["medium"]),
    )


#: 待办工单：(键, 头像字, 标题, 副标题)
_TICKETS: tuple[tuple[str, str, str, str], ...] = (
    ("SO-1042", "林", "SO-1042 退款审核", "林一舟 · ¥1,280 · 2 小时前"),
    ("SO-1043", "赵", "SO-1043 地址更正", "赵思远 · 顺丰 SF1029384 · 5 小时前"),
    ("SO-1047", "陈", "SO-1047 补开发票", "陈可 · 增值税专票 · 昨天 18:20"),
    ("SO-1051", "王", "SO-1051 物流异常", "王砚 · 滞留杭州中转 · 昨天 16:05"),
)


@ft.component
def _basic() -> ft.Control:
    """点一行选中：选中底由 ListTile 自己画，调用方只管把键写回 state。"""
    picked, set_picked = ft.use_state("SO-1042")

    def pick(key: str):
        def handler(_event: ft.Event[ft.ListTile]) -> None:
            set_picked(key)

        return handler

    owner = next(
        (sub.split(" · ")[0] for key, _, _, sub in _TICKETS if key == picked), ""
    )
    return ft.Container(
        width=560,
        content=ft.Column(
            spacing=0,
            controls=[
                *[
                    ft.ListTile(
                        leading=_avatar(initial),
                        title=ft.Text(
                            title,
                            size=FONT_SIZE["body"],
                            weight=FONT_WEIGHT["medium"],
                        ),
                        subtitle=ft.Text(
                            subtitle, size=FONT_SIZE["small"], color=MUTED
                        ),
                        trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT, size=18, color=MUTED),
                        selected=key == picked,
                        on_click=pick(key),
                    )
                    for key, initial, title, subtitle in _TICKETS
                ],
                ft.Container(
                    padding=ft.Padding.only(left=16, top=8),
                    content=ft.Text(
                        f"当前选中：{picked}（{owner}）",
                        size=FONT_SIZE["caption"],
                        color=MUTED,
                    ),
                ),
            ],
        ),
    )


@ft.component
def _trailing() -> ft.Control:
    """尾部三种操作：开关、文字按钮、箭头。动作都会回写到下面那行 state。"""
    notify, set_notify = ft.use_state(True)
    note, set_note = ft.use_state("开关与按钮都会回写本地 state")

    def toggle(event: ft.Event[ft.Switch]) -> None:
        set_notify(event.control.value)
        set_note("构建通知：" + ("已开启" if event.control.value else "已关闭"))

    return ft.Container(
        width=560,
        content=ft.Column(
            spacing=0,
            controls=[
                ft.ListTile(
                    leading=ft.Icon(
                        ft.Icons.NOTIFICATIONS_OUTLINED, size=20, color=MUTED
                    ),
                    title=ft.Text(
                        "构建通知",
                        size=FONT_SIZE["body"],
                        weight=FONT_WEIGHT["medium"],
                    ),
                    subtitle=ft.Text(
                        "失败与恢复时各推一条",
                        size=FONT_SIZE["small"],
                        color=MUTED,
                    ),
                    trailing=ft.Switch(value=notify, on_change=toggle),
                ),
                ft.ListTile(
                    leading=ft.Icon(
                        ft.Icons.SYSTEM_UPDATE_ALT_OUTLINED, size=20, color=MUTED
                    ),
                    title=ft.Text(
                        "版本更新",
                        size=FONT_SIZE["body"],
                        weight=FONT_WEIGHT["medium"],
                    ),
                    subtitle=ft.Text(
                        "0.1.1 · 3 天前发布",
                        size=FONT_SIZE["small"],
                        color=MUTED,
                    ),
                    trailing=ft.TextButton(
                        "查看",
                        on_click=lambda _e: set_note("已是最新版本 0.1.1"),
                    ),
                ),
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.STORAGE_OUTLINED, size=20, color=MUTED),
                    title=ft.Text(
                        "存储空间",
                        size=FONT_SIZE["body"],
                        weight=FONT_WEIGHT["medium"],
                    ),
                    subtitle=ft.Text(
                        "已用 2.4 GB / 10 GB",
                        size=FONT_SIZE["small"],
                        color=MUTED,
                    ),
                    trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT, size=18, color=MUTED),
                    on_click=lambda _e: set_note("打开存储管理"),
                ),
                ft.Container(
                    padding=ft.Padding.only(left=16, top=8),
                    content=ft.Text(note, size=FONT_SIZE["caption"], color=MUTED),
                ),
            ],
        ),
    )


_LONG = (
    "客户反馈：同一笔订单在 10:12 与 10:14 各发起一次支付，回调只到达一笔，"
    "财务对账时两边金额对不上，需要人工核对流水并确认是否需要退款。"
)


@ft.component
def _two_lines() -> ft.Control:
    """副标题两行：宽 420px，第二行末尾收省略号，行高由 is_three_line 撑开。"""
    return ft.Container(
        width=420,
        content=ft.Column(
            spacing=0,
            controls=[
                ft.ListTile(
                    leading=ft.Icon(
                        ft.Icons.DESCRIPTION_OUTLINED, size=20, color=MUTED
                    ),
                    title=ft.Text(
                        "对账差异 · 2026-11",
                        size=FONT_SIZE["body"],
                        weight=FONT_WEIGHT["medium"],
                    ),
                    subtitle=ft.Text(
                        _LONG,
                        size=FONT_SIZE["small"],
                        color=MUTED,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    is_three_line=True,
                    trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT, size=18, color=MUTED),
                ),
                ft.ListTile(
                    leading=ft.Icon(
                        ft.Icons.DESCRIPTION_OUTLINED, size=20, color=MUTED
                    ),
                    title=ft.Text(
                        "对账差异 · 2026-10",
                        size=FONT_SIZE["body"],
                        weight=FONT_WEIGHT["medium"],
                    ),
                    subtitle=ft.Text(
                        "已处理，差异 0.00 元",
                        size=FONT_SIZE["small"],
                        color=MUTED,
                    ),
                    trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT, size=18, color=MUTED),
                ),
            ],
        ),
    )


# ---------------------------------------------------------------------------
# 示例源码（“查看代码”面板）
# ---------------------------------------------------------------------------
_BASIC_CODE = """ListTile(
    leading=CircleAvatar(content=Text("林")),
    title=Text("SO-1042 退款审核", size=14),
    subtitle=Text("林一舟 · ¥1,280 · 2 小时前", size=12),
    trailing=Icon(Icons.CHEVRON_RIGHT, size=18),
    selected=key == picked,            # 选中底由主题的 secondaryContainer 给
    on_click=lambda e: set_picked(key),
)"""

_TRAILING_CODE = """ListTile(
    title=Text("构建通知"),
    subtitle=Text("失败与恢复时各推一条"),
    trailing=Switch(value=notify, on_change=on_toggle),
)

# 整行可点时尾部只放箭头：再放按钮，两个点击目标会互相抢手势
ListTile(
    title=Text("存储空间"),
    trailing=Icon(Icons.CHEVRON_RIGHT),
    on_click=open_storage,
)"""

_THREE_LINE_CODE = """ListTile(
    title=Text("对账差异 · 2026-11"),
    subtitle=Text("客户反馈的完整描述，超出两行就收省略号……",
                  max_lines=2, overflow=TextOverflow.ELLIPSIS),
    is_three_line=True,        # 少了它，第二行会被裁掉
)"""


# ---------------------------------------------------------------------------
# 组件说明
# ---------------------------------------------------------------------------
SPEC = Spec(
    name="ListTile",
    summary="列表里的一行：头像或图标 + 主标题 + 副标题，尾部留给一个操作。",
    definition=(
        "ListTile 是「一行记录」的标准骨架。它不画外框、不做分组，只把行拆成三段固定"
        "位置：leading 放头像或图标，title 与 subtitle 放两行文字，trailing 放箭头、"
        "开关或按钮。这样做的价值在一致性 —— 名单、设置项、搜索结果如果各拼一个 Row，"
        "行高与内边距一定会有细微差别，滚动时第一眼就能看出来。"
    ),
    anatomy=[
        (
            "leading",
            "头像（CircleAvatar）或图标；它参与行高计算，别塞比文字高得多的控件。",
        ),
        ("title", "主标题，一行；放「哪一条」，不要把整段说明塞进来。"),
        (
            "subtitle",
            "副标题，第二行。要显示两行必须同时开 is_three_line，否则高度不够、第二行被裁。",
        ),
        (
            "trailing",
            "行尾操作：箭头 / 开关 / 按钮。整行可点时只放图标，按钮会抢走同一次点击。",
        ),
        (
            "选中态",
            "selected=True 铺一层主题的 secondaryContainer；配合 on_click 回写 state 即可。",
        ),
    ],
    when=[
        "名单、会话、工单这类「结构相同的一行条记录」",
        "设置项：左边图标 + 标题说明，右边开关或箭头",
        "点一行进详情：整行可点，比只让标题可点的命中区大得多",
    ],
    avoid=[
        (
            "自己拼 Row(头像 + Column(标题, 副标题) + 图标)：行高、垂直居中与触摸区都要重算，"
            "还会和页面里其他行对不齐"
        ),
        "整列列表：ListTile 只管一行，外层用 ListView（或 Column）承载，滚动交出去",
        "多字段详情：一行塞四个字段会挤，用 Descriptions 的键值网格",
    ],
    examples=[
        Example(
            "基础用法",
            _basic,
            hint="四条工单：头像 + 标题 + 副标题 + 箭头，点一行切换选中。",
            code=_BASIC_CODE,
        ),
        Example(
            "尾部操作",
            _trailing,
            hint="开关、文字按钮、箭头三种尾巴；动作结果回写到下方那行说明。",
            code=_TRAILING_CODE,
        ),
        Example(
            "两行副标题",
            _two_lines,
            hint="420px 宽、副标题两行收省略号；is_three_line 决定这一行给不给第二行留高度。",
            code=_THREE_LINE_CODE,
        ),
    ],
    api=[
        Api(
            "leading",
            "IconData | Control | None",
            "None",
            "行首的头像或图标",
        ),
        Api("title", "str | Control | None", "None", "主标题，放「哪一条」"),
        Api(
            "subtitle",
            "str | Control | None",
            "None",
            "副标题；多行需配 is_three_line",
        ),
        Api(
            "trailing",
            "IconData | Control | None",
            "None",
            "行尾操作：箭头 / 开关 / 按钮",
        ),
        Api(
            "is_three_line",
            "bool | None",
            "None",
            "给两行副标题留高度；默认按单行算",
        ),
        Api("selected", "bool", "False", "选中态：铺一层 secondaryContainer"),
        Api(
            "on_click",
            "Callable[[Event], None] | None",
            "None",
            "整行点击；可点就别再在 trailing 放按钮",
        ),
        Api("dense", "bool | None", "None", "紧凑行：字号与上下留白一起收一档"),
        Api(
            "content_padding",
            "Padding | int | None",
            "None",
            "行内边距；列表本身已有 padding 时通常不用改",
        ),
    ],
    notes=[
        tip(
            "is_three_line=True 才给两行副标题留高度。不开的话 Flutter 仍按两行排版、"
            "行高却按两行以内算，第二行会被裁掉一半 —— 这是 ListTile 最常见的「字被吃掉」。"
        ),
        info(
            "选中底不需要自己指定 selected_tile_color：它来自主题的 secondaryContainer，"
            "深色主题下会自动换成合适合成色，写死一个色值反而只有一种主题能用。"
        ),
        warn(
            "整行 on_click 与 trailing 里的按钮同时存在时，两个点击目标会抢同一个手势，"
            "用户也分不清点中的是哪一个。要么整行可点、尾部只放图标，要么去掉行点击。"
        ),
    ],
    tags=("列表项", "listtile", "行", "条目", "设置项"),
)


if __name__ == "__main__":
    run(SPEC)
