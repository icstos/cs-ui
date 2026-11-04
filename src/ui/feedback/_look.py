"""语义类型 → 图标 / 强调色 / 图标底座。

``Message`` 与 ``Notification`` 共用这一套"类型长相"：换一处，两处一起变。

强调色取自 :mod:`ui.core.tokens` 的语义色——``success`` / ``warning`` 这类角色
Material 3 没有，由框架按明暗主题各给一档，所以这里不写任何裸色值。
用法只有一种：``accent(type)`` 拿色、``icon_chip(type)`` 拿那颗淡底圆角方块。
"""

from __future__ import annotations

import flet as ft

from ui.core.constants import StyleType
from ui.core.tokens import RADIUS, semantic_text

__all__ = ["accent", "icon", "icon_chip"]

#: 类型 → (图标, 语义色角色)。``PRIMARY`` 不是语义角色，直接用主题主色。
_LOOK: dict[StyleType, tuple[ft.IconData, str]] = {
    StyleType.DEFAULT: (ft.Icons.NOTIFICATIONS_ROUNDED, "neutral"),
    StyleType.PRIMARY: (ft.Icons.CAMPAIGN_ROUNDED, "primary"),
    StyleType.INFO: (ft.Icons.INFO_ROUNDED, "info"),
    StyleType.SUCCESS: (ft.Icons.CHECK_CIRCLE_ROUNDED, "success"),
    StyleType.WARNING: (ft.Icons.WARNING_ROUNDED, "warning"),
    StyleType.ERROR: (ft.Icons.ERROR_ROUNDED, "danger"),
}


def _entry(style_type: StyleType) -> tuple[ft.IconData, str]:
    return _LOOK.get(style_type, _LOOK[StyleType.INFO])


def icon(style_type: StyleType) -> ft.IconData:
    """该类型用的图标。"""
    return _entry(style_type)[0]


def accent(style_type: StyleType) -> str:
    """该类型的强调色（同时用作图标色与 12% 淡底）。"""
    role = _entry(style_type)[1]
    return ft.Colors.PRIMARY if role == "primary" else semantic_text(role)


def icon_chip(style_type: StyleType, *, size: int = 22, icon_size: int = 15) -> ft.Control:
    """淡底圆角方块 + 图标。

    给类型一个颜色锚点，又不像"整卡染成绿色"的提示条那样吵。兑 12% 透明度
    而不是实底，是为了在深色主题下也不刺眼。
    """
    color = accent(style_type)
    return ft.Container(
        width=size,
        height=size,
        bgcolor=ft.Colors.with_opacity(0.12, color),
        border_radius=RADIUS["md"],
        alignment=ft.Alignment.CENTER,
        content=ft.Icon(icon(style_type), size=icon_size, color=color),
    )
