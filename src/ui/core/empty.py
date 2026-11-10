"""空状态：所有组件共用的「这里没有内容」写法。

为什么值得单独一个模块
----------------------
空态最容易被当成"顺手一行 Text"。四个下拉各写一遍时，同一个"暂无数据"的字号、
颜色、留白全不一样 —— 用户不会逐处比对，但会觉得"这个框架不整齐"。

两条硬规则
----------
1. **文字色取 ``ON_SURFACE_VARIANT``，不取 ``OUTLINE``。**
   Material 3 里 ``outline`` 是**边框 / 分隔线**的角色，`on_surface_variant`
   才是次要文字。用 outline 当文字色，在浅色主题下对比度只有约 3.2:1，
   刚好卡在 WCAG AA 的及格线下面 —— 空态本来信息就少，更要读得清。
2. **高度必须有下限。** 高度塌成 0 的空面板在页面上等于消失了：用户看到的是
   "这里什么都没有"，而不是"这里本来该有东西，只是还没有"。

两种形态
--------
* :func:`empty_line` —— 单行居中。下拉面板、小列表用这个。
* :func:`empty_block` —— 图标垫底 + 主文 + 可选的下一步提示。整块区域
  （传输框、结果页、详情区）用这个，`:func:`empty_line`` 在大片留白里
  会飘着像渲染失败。

用法::

    from ui.core.empty import empty_line, empty_block

    empty_line(height=64)                      # 「暂无数据」，自带语言包
    empty_line("没有匹配的项", height=40)        # 覆盖文案
    empty_block("还没有任何订单", hint="点右上角「新建」开始",
                icon=ft.Icons.INBOX)
"""

from __future__ import annotations

import flet as ft

from ui.core.tokens import FONT_SIZE, ICON_SIZE, RADIUS, SPACE, overlay

__all__ = [
    "EMPTY_HEIGHT",
    "EMPTY_ICON_BOX",
    "EMPTY_LINE_HEIGHT",
    "empty_block",
    "empty_line",
]

#: 整块空态的最小高度：低于这个数，"什么都没有"就读成了"加载失败"。
EMPTY_HEIGHT = 72

#: 单行空态（下拉面板）的最小高度：两行选项的高度，视觉上仍是个列表。
EMPTY_LINE_HEIGHT = 64

#: 图标垫底的圆形底直径。320px 的面板里，一枚裸图标会飘得像渲染失败，
#: 给它一块"印章"就落地了（这个值来自 Transfer 的实测）。
EMPTY_ICON_BOX = 48


def _default_text() -> str:
    """默认文案取语言包 —— 避免各处再写一遍"暂无数据"。"""
    from ui.core.i18n import t

    return t("ui.common.empty")


def empty_line(
    text: str | None = None,
    *,
    height: float = EMPTY_LINE_HEIGHT,
    width: float | None = None,
    size: int | None = None,
    align: ft.Alignment = ft.Alignment.CENTER,
    padding: ft.Padding | None = None,
) -> ft.Control:
    """单行空态：一行灰字，撑住给定高度。

    Args:
        text: 文案；``None`` 取语言包的「暂无数据」。
        height: 占位高度，默认 :data:`EMPTY_LINE_HEIGHT`。永远是"至少这么高"，
            不会因为父容器挤压而塌成 0。
        width: 固定宽度（下拉面板的列宽）。``None`` 表示跟随父容器。
        size: 字号，默认 ``FONT_SIZE["small"]``。下拉行用小一号，和选项文字
            拉开层次，又不至于像注脚。
        align: 对齐。默认居中；**下拉面板里请传 ``CENTER_LEFT`` 并配
            ``padding``**，让空态读起来像"列表的最后一行"，而不是浮在面板中间。
        padding: 内边距。左对齐时通常要和选项行的左右留白一致。

    Returns:
        一个居中的 :class:`flet.Container`，可直接放进任何列表位置。
    """
    return ft.Container(
        width=width,
        height=height,
        padding=padding,
        alignment=align,
        content=ft.Text(
            text or _default_text(),
            size=size if size is not None else FONT_SIZE["small"],
            color=ft.Colors.ON_SURFACE_VARIANT,
            text_align=ft.TextAlign.CENTER,
        ),
    )


def empty_block(
    text: str | None = None,
    *,
    hint: str | None = None,
    icon: ft.IconData | None = None,
    height: float | None = EMPTY_HEIGHT,
    width: float | None = None,
) -> ft.Control:
    """整块空态：图标（可选）+ 主文 + 下一步提示（可选）。

    Args:
        text: 主文；``None`` 取语言包的「暂无数据」。
        hint: 第二行提示，说明"下一步该做什么"。**只在真的存在下一步时给** ——
            搜索无结果时说「去别处勾选」是假话，那是被筛掉了不是被搬走了。
        icon: 图标。``None`` 时不画图标，只剩两行字。
        height: 占位高度，默认 :data:`EMPTY_HEIGHT`；显式传 ``None`` 表示
            "由父容器撑开"（``expand=True`` 的整块结果区用这个）。
        width: 固定宽度，一般不用。

    Returns:
        居中的 :class:`flet.Container`。
    """
    lines: list[ft.Control] = []
    if icon is not None:
        lines.append(
            ft.Container(
                width=EMPTY_ICON_BOX,
                height=EMPTY_ICON_BOX,
                border_radius=RADIUS["full"],
                bgcolor=overlay(0.04),
                alignment=ft.Alignment.CENTER,
                content=ft.Icon(icon, size=ICON_SIZE["2xl"], color=ft.Colors.ON_SURFACE_VARIANT),
            )
        )
    lines.append(
        ft.Text(
            text or _default_text(),
            size=FONT_SIZE["body"],
            color=ft.Colors.ON_SURFACE_VARIANT,
            text_align=ft.TextAlign.CENTER,
        )
    )
    if hint:
        lines.append(
            ft.Text(
                hint,
                size=FONT_SIZE["small"],
                color=ft.Colors.ON_SURFACE_VARIANT,
                text_align=ft.TextAlign.CENTER,
            )
        )

    return ft.Container(
        width=width,
        height=height,
        alignment=ft.Alignment.CENTER,
        content=ft.Column(
            spacing=SPACE["2"],
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=lines,
        ),
    )
