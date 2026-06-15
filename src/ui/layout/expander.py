"""Expander 可展开/折叠部件 — 视觉增强版."""

from __future__ import annotations

from typing import Any

import flet as ft

# ---------------------------------------------------------------------------
# 颜色常量
# ---------------------------------------------------------------------------
_COLOR_TITLE_BG: str = ft.Colors.GREY_100
_COLOR_TITLE_HOVER: str = ft.Colors.BLUE_50
_COLOR_CONTENT_BG: str = ft.Colors.WHITE
_COLOR_BORDER: str = ft.Colors.GREY_200
_COLOR_ICON: str = ft.Colors.GREY_600

# 动画参数
_ANIM_DURATION_MS: int = 300
_ANIM_CURVE: ft.AnimationCurve = ft.AnimationCurve.EASE_IN_OUT

# 默认圆角半径
_DEFAULT_BORDER_RADIUS: float = 8.0


@ft.control
class Expander(ft.ExpansionTile):
    """可展开/折叠卡片控件。

    增强特性:
    - 展开/折叠内容平滑过渡动画
    - 圆角卡片风格，内容区上边框分隔
    - 适当的内边距和视觉层次
    - 展开/折叠动画过渡（标题及内容区）
    """

    # ---- 可自定义外观 -------------------------------------------------
    title: ft.StrOrControl | ft.Container
    dense: bool | None = None
    affinity: ft.TileAffinity = ft.TileAffinity.PLATFORM
    bgcolor: str = _COLOR_TITLE_BG
    collapsed_bgcolor: str = _COLOR_TITLE_BG
    expanded_cross_axis_alignment: ft.CrossAxisAlignment = ft.CrossAxisAlignment.START

    # 圆角半径（px）
    border_radius: float | int = _DEFAULT_BORDER_RADIUS

    def __init__(
        self,
        title: ft.StrOrControl | ft.Container,
        controls: list[ft.Control] | None = None,
        subtitle: ft.StrOrControl | None = None,
        leading: ft.Control | None = None,
        trailing: ft.Control | None = None,
        dense: bool | None = None,
        affinity: ft.TileAffinity = ft.TileAffinity.PLATFORM,
        bgcolor: str = _COLOR_TITLE_BG,
        collapsed_bgcolor: str = _COLOR_TITLE_BG,
        border_radius: float | int = _DEFAULT_BORDER_RADIUS,
        **kwargs: Any,
    ) -> None:
        """初始化 Expander 控件。

        参数:
            title: 标题文本或控件。
            controls: 展开后显示的内容控件列表。
            subtitle: 副标题文本或控件（可选）。
            leading: 标题左侧图标/控件（可选）。
            trailing: 标题右侧图标/控件（可选）。
            dense: 是否紧凑模式。
            affinity: 标题对齐方式。
            bgcolor: 展开时标题背景颜色。
            collapsed_bgcolor: 折叠时标题背景颜色。
            border_radius: 整体圆角半径（px）。
            **kwargs: 传递给父类的其他参数。
        """
        super().__init__(
            title=title,
            controls=controls,
            subtitle=subtitle,
            leading=leading,
            trailing=trailing,
            dense=dense,
            affinity=affinity,
            bgcolor=bgcolor,
            collapsed_bgcolor=collapsed_bgcolor,
            **kwargs,
        )
        self.border_radius = border_radius

    def init(self) -> None:
        """flet 框架生命周期：构建 UI 树。"""
        self._build_title()
        self._build_subtitle()
        self._build_controls()

    # ------------------------------------------------------------------
    # 内部构建方法
    # ------------------------------------------------------------------

    def _build_title(self) -> None:
        """将 title 包装成带圆角和样式的容器。"""
        if isinstance(self.title, str):
            self.title = ft.Container(
                ft.Text(
                    self.title,
                    size=14,
                    weight=ft.FontWeight.W_500,
                    color=ft.Colors.GREY_800,
                ),
            )

        # 如果 title 已经是 Container，复用并增强；否则包裹一层
        if isinstance(self.title, ft.Container):
            self.title.padding = self.title.padding or ft.Padding.only(
                left=16, top=10, bottom=10, right=12
            )
            self.title.animate = ft.Animation(_ANIM_DURATION_MS, _ANIM_CURVE)
            self.title.border_radius = ft.BorderRadius.only(
                top_left=self.border_radius,
                top_right=self.border_radius,
            )
            self.title.bgcolor = self.title.bgcolor or _COLOR_TITLE_BG
        else:
            self.title = ft.Container(
                content=self.title,
                padding=ft.Padding.only(left=16, top=10, bottom=10, right=12),
                animate=ft.Animation(_ANIM_DURATION_MS, _ANIM_CURVE),
                border_radius=ft.BorderRadius.only(
                    top_left=self.border_radius,
                    top_right=self.border_radius,
                ),
                bgcolor=_COLOR_TITLE_BG,
            )

        # 用 Container 包裹标题以设置圆角和溢出剪裁
        self.title = ft.Container(
            content=self.title,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        )

    def _build_subtitle(self) -> None:
        """规范化 subtitle 为 Container。"""
        if self.subtitle is None:
            return
        if isinstance(self.subtitle, str):
            self.subtitle = ft.Container(
                ft.Text(
                    self.subtitle,
                    size=12,
                    color=ft.Colors.GREY_500,
                ),
                padding=ft.Padding.only(right=12),
            )
        elif not isinstance(self.subtitle, ft.Container):
            self.subtitle = ft.Container(content=self.subtitle)

    def _build_controls(self) -> None:
        """将展开内容包装为圆角卡片风格容器。"""
        if self.controls is None or len(self.controls) == 0:
            return

        inner = ft.Column(
            controls=self.controls,
            spacing=0,
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.START,
            expand=True,
        )

        self.controls = [
            ft.Container(
                content=inner,
                bgcolor=_COLOR_CONTENT_BG,
                expand=True,
                alignment=ft.Alignment.TOP_LEFT,
                padding=ft.Padding.only(left=20, top=10, bottom=12, right=16),
                border=ft.Border.only(
                    top=ft.BorderSide(1, _COLOR_BORDER),
                ),
                border_radius=ft.BorderRadius.only(
                    bottom_left=self.border_radius,
                    bottom_right=self.border_radius,
                ),
                # 内容区展开/折叠动画
                animate=ft.Animation(_ANIM_DURATION_MS, _ANIM_CURVE),
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            )
        ]


# ---------------------------------------------------------------------------
# 测试入口
# ---------------------------------------------------------------------------


@ft.component
def App() -> ft.Control:
    """Expander 测试页面。"""
    return ft.Column(
        controls=[
            Expander(
                title="Expander 控制件",
                # subtitle="点击展开查看更多",
                controls=[
                    ft.Text("这是展开后的第一行内容。", size=13),
                    ft.Text("这是展开后的第二行内容。", size=13),
                    ft.Text("你可以在此放置任意控件。", size=13),
                ],
                # leading=ft.Icon(ft.Icons.INFO_OUTLINE, color=_COLOR_ICON),
            ),
            Expander(
                title="Expander 控制件",
                # subtitle="点击展开查看更多",
                controls=[
                    ft.Text("这是展开后的第一行内容。", size=13),
                    ft.Text("这是展开后的第二行内容。", size=13),
                    ft.Text("你可以在此放置任意控件。", size=13),
                ],
                # leading=ft.Icon(ft.Icons.INFO_OUTLINE, color=_COLOR_ICON),
            ),
        ]
    )


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
