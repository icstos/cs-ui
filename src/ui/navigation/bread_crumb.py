"""面包屑导航 (BreadCrumb)。

用法::

    BreadCrumb(items=["首页", ("组件", "/components"), "表格"])

items 中的每一项既可以是纯文本（不可点击），
也可以是 ``(文本, 路由)`` 元组 / :class:`Crumb`，点击后自动跳转。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import flet as ft

__all__ = ["BreadCrumb", "Crumb"]

SEPARATOR_ICON = ft.Icons.CHEVRON_RIGHT
ICON_SIZE = 16
TEXT_SIZE = 14


@dataclass
class Crumb:
    """面包屑中的一项。

    Args:
        text: 显示文本。
        route: 点击后跳转的路由，为 ``None`` 时不可点击。
        icon: 可选的图标。
    """

    text: str
    route: str | None = None
    icon: ft.IconData | None = None


def _to_crumb(item: str | tuple[str, str] | Crumb) -> Crumb:
    """把简写形式统一转换为 :class:`Crumb`。"""
    match item:
        case Crumb():
            return item
        case (text, route):
            return Crumb(text=str(text), route=str(route))
        case str():
            return Crumb(text=item)
        case _:
            return Crumb(text=str(item))


@ft.control
class BreadCrumb(ft.Row):
    """面包屑导航组件，继承自 :class:`flet.Row`。

    Args:
        items: 面包屑项，支持 ``str`` / ``(文本, 路由)`` / :class:`Crumb`。
        separator: 分隔符图标，默认 ``CHEVRON_RIGHT``。
        active_color: 最后一项（当前页）的颜色。
        inactive_color: 其余项的颜色。
        on_item_click: 自定义点击回调；未提供时按 ``route`` 自动跳转。
    """

    items: list = field(default_factory=list)
    separator: ft.IconData = SEPARATOR_ICON
    active_color: ft.ColorValue = ft.Colors.ON_SURFACE
    inactive_color: ft.ColorValue = ft.Colors.ON_SURFACE_VARIANT
    on_item_click: Callable[[Crumb], None] | None = None

    def init(self):
        crumbs = [_to_crumb(item) for item in self.items]
        self.spacing = 2
        self.vertical_alignment = ft.CrossAxisAlignment.CENTER
        self.controls = self._build(crumbs)

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _build(self, crumbs: list[Crumb]) -> list[ft.Control]:
        """构建面包屑控件列表。"""
        controls: list[ft.Control] = []
        last_index = len(crumbs) - 1

        for index, crumb in enumerate(crumbs):
            is_last = index == last_index
            controls.append(self._build_crumb(crumb, is_last))
            if not is_last:
                controls.append(
                    ft.Icon(
                        icon=self.separator,
                        size=ICON_SIZE,
                        color=self.inactive_color,
                    )
                )
        return controls

    def _build_crumb(self, crumb: Crumb, is_last: bool) -> ft.Control:
        """构建单个面包屑项。"""
        color = self.active_color if is_last else self.inactive_color
        weight = ft.FontWeight.W_600 if is_last else None
        content: ft.Control = ft.Row(
            controls=[
                *([ft.Icon(crumb.icon, size=ICON_SIZE, color=color)] if crumb.icon else []),
                ft.Text(crumb.text, size=TEXT_SIZE, color=color, weight=weight),
            ],
            spacing=4,
            tight=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        clickable = crumb.route is not None or self.on_item_click is not None
        if not clickable:
            return ft.Container(
                content=content, padding=ft.Padding.symmetric(vertical=2, horizontal=6)
            )

        return ft.Container(
            content=content,
            padding=ft.Padding.symmetric(vertical=2, horizontal=6),
            border_radius=ft.BorderRadius.all(6),
            ink=True,
            data=crumb,
            on_click=self._handle_click,
            tooltip=crumb.text,
        )

    def _handle_click(self, e: ft.ControlEvent) -> None:
        """点击处理：优先使用自定义回调，否则按 route 跳转。"""
        crumb: Crumb = e.control.data
        if callable(self.on_item_click):
            self.on_item_click(crumb)
            return
        if crumb.route:
            e.page.navigate(crumb.route)


@ft.component
def App():
    """BreadCrumb 组件运行示例。"""
    page = ft.context.page
    return ft.Column(
        controls=[
            ft.Text("BreadCrumb 面包屑", size=20, weight=ft.FontWeight.BOLD),
            ft.Text("支持纯文本、可点击跳转与自定义图标", size=13, color="#6b7280"),
            ft.Divider(),
            BreadCrumb(
                items=[
                    Crumb("首页", "/", icon=ft.Icons.HOME),
                    ("组件", "/components"),
                    ("导航", "/components/navigation"),
                    "面包屑",
                ]
            ),
            ft.Divider(),
            BreadCrumb(
                items=["订单管理", "2026 年", "9 月", "今日订单"],
                separator=ft.Icons.ARROW_RIGHT,
            ),
            ft.Divider(),
            BreadCrumb(
                items=[
                    ("首页", "/"),
                    ("分类", "/category"),
                    "当前页",
                ],
                on_item_click=lambda c: page.show_dialog(
                    ft.SnackBar(content=f"点击了：{c.text} ({c.route})")
                ),
            ),
        ]
    )


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
