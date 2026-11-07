"""应用栏 (AppBar) —— 页面顶部那一行：返回、标题、副标题、右侧操作。

与 ``ft.AppBar`` 的区别：那个是 Material 的 ``AdaptiveControl``，只能挂在
``View.appbar`` 上，进不了 ``Column``；这里是一个普通的 ``Container``，放进
页面里的任何一列都行 —— 桌面应用更常见的形态是「窗口里再分栏」，顶部那一条
属于内容区，而不是窗口本身。

用法::

    Column([
        AppBar(title="主机列表", subtitle="共 12 台", show_back=True,
               actions=[IconButton(icon=ft.Icons.REFRESH)]),
        ListView(expand=True),
    ])
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import field

import flet as ft

from ui.core.doc import Example, Spec, run
from ui.core.tokens import FONT_SIZE, FONT_WEIGHT, RADIUS, SPACE, hairline

__all__ = ["AppBar"]

HEIGHT = 56
LEAD_SIZE = 32


@ft.control
class AppBar(ft.Container):
    """页面内应用栏。

    Args:
        title: 标题，``str`` 或任意控件。传控件时样式由调用方负责。
        subtitle: 标题下的第二行小字（数量、状态、面包屑都可以）。
        leading: 左侧自定义控件（头像、图标）。与 ``show_back`` 二选一。
        actions: 右侧操作区，通常是 ``IconButton`` 或 ``Button``。
        show_back: 显示返回箭头。点击触发 ``on_back``。
        on_back: 返回回调；不传时箭头只是装饰，不响应点击。
        divider: 底部一条发丝线。默认开 —— 顶栏与内容之间需要一个边界。
        spacing: 标题与两端的间距，默认 16。
    """

    title: ft.StrOrControl = ""
    subtitle: str = ""
    leading: ft.Control | None = None
    actions: list[ft.Control] = field(default_factory=list)
    show_back: bool = False
    on_back: Callable[[], None] | None = None
    divider: bool = True
    spacing: int = SPACE["4"]

    def init(self):
        self.height = HEIGHT
        self.padding = ft.Padding.symmetric(horizontal=self.spacing)
        self.bgcolor = self.bgcolor or ft.Colors.SURFACE
        self.alignment = ft.Alignment.CENTER_LEFT
        if self.divider:
            self.border = self.border or ft.Border(bottom=hairline())

        head: list[ft.Control] = []
        if self.leading is not None:
            head.append(self.leading)
        elif self.show_back:
            head.append(self._back())

        titles: list[ft.Control] = [
            ft.Text(self.title, size=FONT_SIZE["title"], weight=FONT_WEIGHT["semibold"])
            if isinstance(self.title, str)
            else self.title,
            *(
                [
                    ft.Text(
                        self.subtitle,
                        size=FONT_SIZE["small"],
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    )
                ]
                if self.subtitle
                else []
            ),
        ]

        self.content = ft.Row(
            spacing=SPACE["2"],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                *head,
                ft.Column(spacing=0, tight=True, controls=titles),
                ft.Container(expand=True),
                *self.actions,
            ],
        )

    def _back(self) -> ft.Control:
        """返回箭头：自绘一个 32 的方块，不吃 Material 的 48 命中区。"""
        return ft.Container(
            width=LEAD_SIZE,
            height=LEAD_SIZE,
            border_radius=RADIUS["sm"],
            alignment=ft.Alignment.CENTER,
            ink=self.on_back is not None,
            tooltip="返回",
            on_click=(lambda _e: self.on_back()) if self.on_back else None,
            content=ft.Icon(
                ft.Icons.ARROW_BACK, size=18, color=ft.Colors.ON_SURFACE_VARIANT
            ),
        )


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
@ft.component
def _basic() -> ft.Control:
    page = ft.context.page
    return ft.Container(
        border_radius=RADIUS["md"],
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        content=ft.Column(
            spacing=0,
            controls=[
                AppBar(
                    title="主机列表",
                    subtitle="共 12 台 · 3 台异常",
                    show_back=True,
                    on_back=lambda: page.show_dialog(
                        ft.SnackBar(content="点了返回（真实项目里换成 page.navigate）")
                    ),
                    actions=[
                        ft.IconButton(
                            icon=ft.Icons.REFRESH,
                            icon_size=18,
                            icon_color=ft.Colors.ON_SURFACE_VARIANT,
                            tooltip="刷新",
                        ),
                        ft.IconButton(
                            icon=ft.Icons.MORE_HORIZ,
                            icon_size=18,
                            icon_color=ft.Colors.ON_SURFACE_VARIANT,
                            tooltip="更多",
                        ),
                    ],
                ),
                ft.Container(
                    padding=16,
                    content=ft.Text(
                        "顶栏与内容是同级兄弟：AppBar 只管那一行，下面放什么由页面决定。",
                        size=FONT_SIZE["body"],
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                ),
            ],
        ),
    )


@ft.component
def _leading() -> ft.Control:
    """左侧换成头像：返回箭头不是唯一选择。"""
    return ft.Container(
        border_radius=RADIUS["md"],
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        content=AppBar(
            leading=ft.Container(
                width=30,
                height=30,
                border_radius=RADIUS["full"],
                bgcolor=ft.Colors.PRIMARY_CONTAINER,
                alignment=ft.Alignment.CENTER,
                content=ft.Text(
                    "SC",
                    size=11,
                    weight=FONT_WEIGHT["bold"],
                    color=ft.Colors.ON_PRIMARY_CONTAINER,
                ),
            ),
            title="cs-ui",
            subtitle="已连接 · 本地工作区",
            divider=False,
            actions=[
                ft.IconButton(
                    icon=ft.Icons.SETTINGS_OUTLINED,
                    icon_size=18,
                    icon_color=ft.Colors.ON_SURFACE_VARIANT,
                    tooltip="设置",
                )
            ],
        ),
    )


SPEC = Spec(
    name="AppBar",
    summary="页面顶部那一行：返回、标题、副标题与右侧操作。",
    definition=(
        "桌面应用的顶部条常常属于**内容区**而不是窗口：左边一列导航之后，右侧"
        "这块内容自己有一条标题栏。Flet 的 ft.AppBar 是 Material 的 AdaptiveControl，"
        "只能挂在 View 上；这里用普通 Container 实现同样的视觉，放进任何一列都行。"
    ),
    anatomy=[
        ("左侧", "返回箭头（32 方块，不吃 48 命中区）或自定义 leading，二选一。"),
        ("标题区", "标题 + 可选副标题。副标题放数量、状态或面包屑，比再开一行省空间。"),
        ("弹性空档", "标题与操作之间自动撑开，操作永远贴右。"),
        ("操作区", "右侧若干 IconButton。超过 3 个就该收进「更多」。"),
        ("底部分隔线", "一条发丝线；关掉它，顶栏会与内容粘成一片。"),
    ],
    when=[
        "页面内需要一行「我在哪、能做什么」",
        "分栏布局：左导航 + 右侧内容，内容自己带标题栏",
        "需要在标题旁放返回或刷新这类页面级动作",
    ],
    avoid=[
        "已经有全局顶栏（站点外壳）时再叠一条，会出现两层标题",
        "只需要一个标题：直接 Text 更省事，别再包一层",
    ],
    examples=[
        Example("基础用法", _basic, hint="标题 + 副标题 + 返回 + 两个操作。"),
        Example("自定义左侧", _leading, hint="leading 换个头像，divider=False 去掉分隔线。"),
    ],
    target=AppBar,
    notes=[
        (
            "tip",
            "height 在 init() 里设成 56，而不是做成构造参数 —— Container 已经有 "
            "height 字段，再声明一次会把位置参数挤乱（Button 踩过同一个坑）。",
        ),
        (
            "info",
            "返回箭头只调 on_back；不传时它不可点。路由栈由应用的 Router 管，"
            "组件不该猜「返回」到底意味着哪一页。",
        ),
    ],
    tags=("顶栏", "标题栏", "工具栏", "appbar", "toolbar"),
)


if __name__ == "__main__":
    run(SPEC)
