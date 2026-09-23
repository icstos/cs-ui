"""页面布局容器 (PageLayout)。

把一个页面的内容统一收敛到「标题 + 内容 + 内边距 + 滚动」的标准骨架，
避免每个页面重复书写 padding / spacing / scroll。

.. note::
   这里刻意命名为 ``PageLayout`` 而非 ``Page``，以免在 ``from ui import *``
   时覆盖 Flet 原生的 :class:`flet.Page`。

用法::

    PageLayout(
        title="用户管理",
        subtitle="管理系统用户、角色与权限",
        controls=[user_table, Pagination(...)],
    )
"""

from __future__ import annotations

from dataclasses import field

import flet as ft

__all__ = ["PageLayout"]

TITLE_SIZE = 22
SUBTITLE_SIZE = 13


@ft.control
class PageLayout(ft.Container):
    """标准页面骨架容器，继承自 :class:`flet.Container`。

    Args:
        controls: 页面内容控件列表。
        title: 页面标题，为空则不渲染标题区。
        subtitle: 页面副标题。
        actions: 标题右侧的操作区控件（如按钮）。
        padding: 页面内边距，默认 20。
        spacing: 内容间距，默认 12。
        scroll: 滚动模式，默认 ``AUTO``；传 ``None`` 关闭滚动。
        horizontal_alignment: 内容水平对齐方式。
        bgcolor: 页面背景色。
    """

    controls: list[ft.Control] = field(default_factory=list)
    title: str = ""
    subtitle: str = ""
    actions: list[ft.Control] = field(default_factory=list)
    padding: ft.PaddingValue = 20
    spacing: int = 12
    scroll: ft.ScrollMode | None = ft.ScrollMode.AUTO
    horizontal_alignment: ft.CrossAxisAlignment = ft.CrossAxisAlignment.START
    bgcolor: ft.ColorValue = ft.Colors.TRANSPARENT

    def init(self):
        if self.expand is None:
            self.expand = True

        body: list[ft.Control] = []
        header = self._build_header()
        if header is not None:
            body.append(header)
        body.extend(self.controls)

        self.content = ft.Column(
            controls=body,
            spacing=self.spacing,
            scroll=self.scroll,
            horizontal_alignment=self.horizontal_alignment,
            expand=True,
        )

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _build_header(self) -> ft.Control | None:
        """构建标题区；无标题且无操作按钮时返回 None。"""
        has_title = bool(self.title or self.subtitle)
        if not has_title and not self.actions:
            return None

        left: list[ft.Control] = []
        if self.title:
            left.append(ft.Text(self.title, size=TITLE_SIZE, weight=ft.FontWeight.BOLD))
        if self.subtitle:
            left.append(
                ft.Text(
                    self.subtitle,
                    size=SUBTITLE_SIZE,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                )
            )

        return ft.Row(
            controls=[
                ft.Column(controls=left, spacing=2, expand=True),
                *self.actions,
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
        )


@ft.component
def App():
    """PageLayout 组件运行示例。"""

    def stat(label: str, value: str, color: str) -> ft.Control:
        return ft.Card(
            elevation=1,
            content=ft.Container(
                padding=16,
                border_radius=8,
                content=ft.Column(
                    spacing=4,
                    controls=[
                        ft.Text(value, size=24, weight=ft.FontWeight.BOLD, color=color),
                        ft.Text(label, size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                    ],
                ),
            ),
        )

    return ft.Container(
        height=520,
        content=PageLayout(
            title="用户管理",
            subtitle="管理系统用户、角色与权限",
            actions=[
                ft.Button("导出"),
                ft.Button("新建用户", icon=ft.Icons.ADD),
            ],
            controls=[
                ft.Row(
                    wrap=True,
                    spacing=12,
                    controls=[
                        stat("总用户", "1,286", "#1f6feb"),
                        stat("活跃用户", "942", "#10b981"),
                        stat("待审核", "37", "#f59e0b"),
                    ],
                ),
                ft.Divider(),
                ft.Text("页面内容区", size=16, weight=ft.FontWeight.BOLD),
                ft.ListTile(
                    title=ft.Text("统一内边距与间距"),
                    subtitle=ft.Text("无需每个页面重复设置 padding / spacing"),
                ),
                ft.ListTile(
                    title=ft.Text("内置滚动"),
                    subtitle=ft.Text("默认 ScrollMode.AUTO，内容超长自动滚动"),
                ),
                ft.ListTile(
                    title=ft.Text("可选标题区"),
                    subtitle=ft.Text("提供 title / subtitle / actions 即可渲染"),
                ),
            ],
        ),
    )


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
