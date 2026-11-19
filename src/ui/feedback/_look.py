"""语义类型 → 图标 / 强调色 / 淡底色。

``Message`` / ``Notification`` / ``AlertDialog`` / ``Button`` 共用这一套"类型
长相"：换一处，四处一起变。这是全框架唯一一个把 :class:`StyleType` 翻成具体
颜色的地方。

色值全部来自 :mod:`ui.core.tokens` 的强调角色四联（``accent_fill`` /
``accent_on`` / ``accent_text`` / ``accent_soft``），所以这里**不出现任何色值**：

* ``primary`` 走 M3 的 ``PRIMARY`` 角色 —— 换主色种子时按钮、徽标、消息条
  一起变，不需要重建控件；
* ``success`` / ``warning`` / ``info`` / ``neutral`` 是 M3 没有的角色，由
  :data:`ui.core.tokens.SEMANTIC` 按当前明暗给出一对具体值，且都过了
  WCAG 4.5:1（见 ``scripts/_theme_logic.py`` 的断言）。

用法::

    style = feedback_style(StyleType.SUCCESS)
    style.fill   # 实底：成功徽标 / 实心按钮
    style.text   # 压在页面上的字：提示条标题 / 镂空按钮
    style.soft   # 12% 淡底：需要淡底的场合（如计数徽标）
    icon_chip(StyleType.SUCCESS)  # 纯色语义图标，20px，不带背景块
"""

from __future__ import annotations

import flet as ft

from ui.core.constants import FeedbackStyle, StyleType
from ui.core.tokens import (
    ICON_SIZE,
    accent_fill,
    accent_on,
    accent_soft,
    accent_text,
    accent_wash,
)

__all__ = [
    "SEMANTIC_ICON_SIZE",
    "accent",
    "feedback_style",
    "icon",
    "icon_chip",
    "soft",
    "wash",
]

#: 类型 → (图标, 强调角色)。``DEFAULT`` 是"中性通知"，不是错误，所以走 neutral。
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


def feedback_style(style_type: StyleType) -> FeedbackStyle:
    """把类型解析成整套视觉（图标 + 四个色位）。

    结果**不要缓存成模块级常量**：颜色取决于当前明暗模式，缓存一次就再也
    不跟着主题变了。渲染时现调，几次字符串拼接的开销可以忽略。
    """
    icon_data, role = _entry(style_type)
    return FeedbackStyle(
        icon=icon_data,
        role=role,
        fill=accent_fill(role),
        on=accent_on(role),
        text=accent_text(role),
        soft=accent_soft(role),
    )


def icon(style_type: StyleType) -> ft.IconData:
    """该类型用的图标。"""
    return _entry(style_type)[0]


def accent(style_type: StyleType) -> str:
    """该类型压在**表面色**上的强调色（图标色、标题色）。"""
    return accent_text(_entry(style_type)[1])


def soft(style_type: StyleType) -> str:
    """该类型的**小面积**淡底（12%）：计数徽标等需要淡底的场合。"""
    return accent_soft(_entry(style_type)[1])


def wash(style_type: StyleType) -> str:
    """该类型的**大面积**淡底（8%）：对话框标题带、提示条整行。"""
    return accent_wash(_entry(style_type)[1])


#: 语义图标尺寸。比正文（14px）大一号，去掉淡底后仍能被先于文字读到。
SEMANTIC_ICON_SIZE: int = ICON_SIZE["xl"]


def icon_chip(style_type: StyleType, *, size: int = SEMANTIC_ICON_SIZE) -> ft.Control:
    """语义图标：纯色图标，不带背景块。

    早期版本在图标下垫一块 12% 的淡底圆角方块。淡底让图标显小、发灰，几个
    提示叠在一起又凑成一排色块。参考 Ant Design / MUI 的做法 —— 语义图标
    直接用 ``accent_text`` 着色，不垫底色：颜色本就是为"压在表面色上"解的
    对比度（浅 5:1 / 深 7:1），去掉底不改变可读性，反而更清晰简洁。

    ``size`` 现在就是图标尺寸（不再有容器），默认 20px，比正文大一号。
    """
    return ft.Icon(icon(style_type), size=size, color=accent(style_type))
