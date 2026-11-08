"""语义图标：一个动作对应一个图标，只在这里定义。

为什么要单独一层
----------------
图标是"同一个动作、好几种画法"最容易失控的地方。实测框架里"点一下展开面板"
这一个动作，同时存在四种画法：

====================================  ==================================
位置                                  用的图标
====================================  ==================================
``SelectBox``                         （交给 flet 内置）
``Cascader``                          ``KEYBOARD_ARROW_DOWN``
``ColorPicker``                       ``KEYBOARD_ARROW_DOWN``
``Calendar``                          ``ARROW_DROP_DOWN_ROUNDED``
``DateTimeInput``                     ``EXPAND_MORE``
``MultiSelect``                       ``ARROW_DROP_DOWN``
====================================  ==================================

放在同一个表单里，四个控件右侧的三角形粗细、大小、圆润度各不相同 —— 用户
说不出哪里不对，但会觉得"不是一个产品"。图标不像颜色那样能靠主题统一，
它没有"角色"这一层，所以只能靠**约定 + 一处定义**。

两族语义，不要混用
------------------
1. **展开面板**（``PANEL_OPEN`` / ``PANEL_CLOSE``）—— 实心三角。
   Material 的 ``arrow_drop_*`` 就是为这个语义画的：它表示"这块区域会展开"，
   和工具栏上那些细线箭头（返回、前进）在视觉上要能区分开。
2. **步进增减**（``STEP_UP`` / ``STEP_DOWN``）—— 细箭头。
   数字输入框、时间字段的上下调节，用的是"按键箭头" ``keyboard_arrow_*``，
   它暗示"按一次动一格"，与"展开一块区域"是两回事。

层级展开（树、子菜单）用 ``DISCLOSURE``，靠旋转 90° 表达开合，不换图标 ——
换图标会让行内的图标跳动，破坏列表的垂直对齐。

用法::

    from ui.core.icons import PANEL_OPEN, PANEL_CLOSE

    ft.Icon(PANEL_CLOSE if self.is_open else PANEL_OPEN, size=ICON_SIZE["lg"])
"""

from __future__ import annotations

import flet as ft

__all__ = [
    "PANEL_OPEN",
    "PANEL_CLOSE",
    "STEP_UP",
    "STEP_DOWN",
    "DISCLOSURE",
    "CLOSE",
    "CLEAR",
    "SEARCH",
    "CHECK",
]

#: 面板收起时：向下的实心三角（"点这里会往下展开"）
PANEL_OPEN: ft.IconData = ft.Icons.ARROW_DROP_DOWN
#: 面板展开时：向上的实心三角
PANEL_CLOSE: ft.IconData = ft.Icons.ARROW_DROP_UP

#: 步进器向上 / 向下（每次动一格）
STEP_UP: ft.IconData = ft.Icons.KEYBOARD_ARROW_UP
STEP_DOWN: ft.IconData = ft.Icons.KEYBOARD_ARROW_DOWN

#: 层级展开：向右的细箭头，展开时由控件旋转 90°（不要换成别的图标）
DISCLOSURE: ft.IconData = ft.Icons.CHEVRON_RIGHT

#: 关闭浮层 / 取消（X）
CLOSE: ft.IconData = ft.Icons.CLOSE
#: 清空输入（X，与 CLOSE 同形；单独命名是为了让"清空"能被搜到）
CLEAR: ft.IconData = ft.Icons.CLOSE
#: 搜索
SEARCH: ft.IconData = ft.Icons.SEARCH
#: 勾选 / 已选
CHECK: ft.IconData = ft.Icons.CHECK
