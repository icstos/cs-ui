"""控件样式工厂。

Flet 1.0.0 起，输入类控件的 ``border_radius`` / ``border_color`` /
``border_width`` / ``focused_border_*`` 等零散字段已废弃，
统一收敛到 ``border`` 字段（``OutlineInputBorder`` / ``UnderlineInputBorder``）。

本模块提供风格统一的构造器，供各输入组件复用，避免样式散落各处。

.. important::
    ``OutlineInputBorder.side`` 的类型是 **单个** ``BorderSide``，
    「按状态给不同边框」必须把状态字典交给 ``FormFieldControl.border`` 本身::

        # 正确
        ft.TextField(border={ft.ControlState.FOCUSED: ft.OutlineInputBorder(...)})

        # 错误——side 收到 dict 后无法解析，静默退回 BorderSide 默认值（黑色）
        ft.OutlineInputBorder(side={ft.ControlState.FOCUSED: ...})

    因此本模块的 :func:`outline_input` / :func:`underline_input`
    返回的是 ``dict[ControlState, InputBorder]``，而不是 ``InputBorder``。

.. note::
    受支持的 ``ControlState`` 仅有 ``DEFAULT`` / ``FOCUSED`` / ``ERROR`` /
    ``DISABLED``（见 ``FormFieldControl.border`` 文档）；未声明的状态回落到
    ``DEFAULT``。``HOVERED`` 对输入边框不生效，悬停反馈请用
    ``FormFieldControl.hover_color``（填充色）。

.. warning::
    字典形式下，某个状态若**未显式**给出 ``side``，它会继承 ``DEFAULT`` 条目的
    ``side``。所以只想改常规色、其余交给主题时，不要给 ``DEFAULT`` 传 ``side``，
    即 ``color=None``。
"""

from __future__ import annotations

import flet as ft

__all__ = [
    "INPUT_RADIUS",
    "INPUT_HEIGHT",
    "outline_input",
    "underline_input",
]

#: 输入类控件的默认圆角
INPUT_RADIUS = 6

#: 输入类控件的默认高度
INPUT_HEIGHT = 36

#: 聚焦态边框默认颜色
DEFAULT_FOCUSED_COLOR = ft.Colors.PRIMARY

#: 错误态边框默认颜色
DEFAULT_ERROR_COLOR = ft.Colors.ERROR


def _state_borders(
    factory: type,
    *,
    color: ft.ColorValue | None,
    focused_color: ft.ColorValue | None,
    error_color: ft.ColorValue | None,
    width: float,
    focused_width: float,
    shape: dict,
) -> dict[ft.ControlState, ft.InputBorder]:
    """把「常规色 / 聚焦色 / 错误色」摊平成 ``ControlState → InputBorder``。

    ``color`` 为 ``None`` 时不写 ``DEFAULT.side``，让 Material 主题自行决定
    各状态的颜色（字典中未显式声明 ``side`` 的条目会继承 ``DEFAULT``；此处
    ``DEFAULT`` 也没有 ``side``，因此所有状态都回到主题解析）。
    """
    normal = None if color is None else ft.BorderSide(width, color)
    active = ft.BorderSide(
        focused_width,
        focused_color if focused_color is not None else DEFAULT_FOCUSED_COLOR,
    )
    invalid = ft.BorderSide(
        width,
        error_color if error_color is not None else DEFAULT_ERROR_COLOR,
    )

    borders: dict[ft.ControlState, ft.InputBorder] = {
        ft.ControlState.DEFAULT: factory(side=normal, **shape),
        ft.ControlState.FOCUSED: factory(side=active, **shape),
        ft.ControlState.ERROR: factory(side=invalid, **shape),
    }
    if normal is not None:
        # 显式禁用色，避免落到 FOCUSED 的继承链上
        borders[ft.ControlState.DISABLED] = factory(
            side=ft.BorderSide(width, ft.Colors.OUTLINE_VARIANT), **shape
        )
    return borders


def outline_input(
    radius: int | float = INPUT_RADIUS,
    color: ft.ColorValue | None = None,
    focused_color: ft.ColorValue | None = None,
    width: float = 1.0,
    error_color: ft.ColorValue | None = None,
) -> dict[ft.ControlState, ft.InputBorder]:
    """构造统一样式的描边输入边框（状态 → 边框 映射）。

    直接赋给输入类控件的 ``border``::

        ft.TextField(border=outline_input(color=ft.Colors.GREY_300))

    Args:
        radius: 圆角半径，默认 :data:`INPUT_RADIUS`。
        color: 常规状态边框颜色。``None``（默认）交给主题解析，
            即色板里的 ``OUTLINE_VARIANT`` 一类的灰。
        focused_color: 聚焦状态边框颜色，默认主题主色。
        width: 边框宽度，默认 1.0。
        error_color: 错误状态边框颜色，默认主题的 ``ERROR``。

    Returns:
        ``{ControlState.DEFAULT | FOCUSED | ERROR | DISABLED: OutlineInputBorder}``。
    """
    return _state_borders(
        ft.OutlineInputBorder,
        color=color,
        focused_color=focused_color,
        error_color=error_color,
        width=width,
        focused_width=width,
        shape={"border_radius": ft.BorderRadius.all(radius)},
    )


def underline_input(
    color: ft.ColorValue | None = None,
    focused_color: ft.ColorValue | None = None,
    width: float = 1.0,
    error_color: ft.ColorValue | None = None,
) -> dict[ft.ControlState, ft.InputBorder]:
    """构造统一样式的下划线输入边框（状态 → 边框 映射）。

    聚焦态下划线加粗到 ``width * 2``，与 Material 规范一致。
    """
    return _state_borders(
        ft.UnderlineInputBorder,
        color=color,
        focused_color=focused_color,
        error_color=error_color,
        width=width,
        focused_width=width * 2,
        shape={},
    )
