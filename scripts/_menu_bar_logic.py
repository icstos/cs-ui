"""MenuBar 纯逻辑断言（不启窗口）。

重点守住**面板展开位置**，这是唯一一个「构造期看不出、真机才露馅」的地方：

* Flutter 的 ``MenuStyle.alignment`` 给的是**对齐点**（``Alignment.withinRect``），
  不是「把面板内嵌到锚点矩形」。所以 ``TOP_LEFT`` 只能把面板左上角钉在
  按钮左上角 —— 面板压在顶栏上。
* 顶栏栏目必须撑满整栏高度（``height = BAR_HEIGHT``）+ 下沉 ``MENU_DROP``
  才会正好落在栏底边；少一个都会让面板压住顶栏或悬空一条缝。
* 嵌套子菜单不能用 ``TOP_LEFT``，否则它盖在父面板上而不是向右展开。

颜色、阴影、动画属于渲染期，交给 ``check_all.py`` 的 smoke 与真机探针。

用法::

    python scripts/_menu_bar_logic.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import flet as ft

from ui.navigation.menu_bar import (
    BAR_HEIGHT,
    ITEM_HEIGHT,
    MENU_DROP,
    MENU_WIDTH,
    MenuAction,
    MenuBar,
    MenuSection,
    action_count,
    find_action,
    iter_actions,
    shortcut_map,
    validate_sections,
)

_fails = 0
_passes = 0


def check(name: str, got: object, want: object) -> None:
    global _fails, _passes
    if got == want:
        _passes += 1
        print(f"PASS  {name}")
    else:
        _fails += 1
        print(f"FAIL  {name}: got={got!r} want={want!r}")


def sections() -> tuple[MenuSection, ...]:
    return (
        MenuSection("文件", (
            MenuAction("open", "打开图片", shortcut="Ctrl+O"),
            MenuAction("assoc", "文件关联", children=(
                MenuAction("assoc.on", "注册为打开方式"),
                MenuAction("assoc.off", "取消关联"),
            )),
            MenuAction("exit", "退出", shortcut="Esc", separator_before=True),
        )),
        MenuSection("视图", (
            MenuAction("fit", "适应窗口", shortcut="Ctrl+0"),
            MenuAction("interval", "播放间隔", children=(
                MenuAction("interval.3", "3 秒", checked=True, data=3),
                MenuAction("interval.5", "5 秒", data=5),
            )),
        )),
    )


def nested(control: ft.Control) -> ft.SubmenuButton:
    """在一栏的下拉内容里找出第一个子菜单入口。"""
    return next(item for item in control.controls
                if isinstance(item, ft.SubmenuButton))


# ===========================================================================
print("=== 常量：顶栏与下拉的几何 ===")
check("BAR_HEIGHT 是 4px 网格上的 48", BAR_HEIGHT, 48)
check("ITEM_HEIGHT 是 32", ITEM_HEIGHT, 32)
check("MENU_WIDTH 不窄于 220", MENU_WIDTH, 220.0)
check("MENU_DROP 正好一栏高（锚点顶边 → 栏底边）", MENU_DROP, BAR_HEIGHT)

print()
print("=== 顶栏栏目：撑满整栏 + 面板下沉到栏底边 ===")
bar = MenuBar(sections=sections())
inner = bar.content                       # 内层 ft.MenuBar（条形容器套的）
check("菜单栏是高度 BAR_HEIGHT 的容器", bar.height, BAR_HEIGHT)
check("内层是一排栏目", len(inner.controls), 2)

for view, section in zip(inner.controls, sections()):
    label = section.label
    check(f"「{label}」是下拉入口", isinstance(view, ft.SubmenuButton), True)
    check(f"「{label}」撑满整栏（锚点顶边 = 栏顶边）", view.height, BAR_HEIGHT)
    check(f"「{label}」面板左上角对齐锚点左上角",
          view.menu_style.alignment, ft.Alignment.TOP_LEFT)
    check(f"「{label}」面板整体下沉一栏高",
          view.alignment_offset, ft.Offset(0, MENU_DROP))

print()
print("=== 嵌套子菜单：向右展开，不压住父面板 ===")
for view, section in zip(inner.controls, sections()):
    sub = nested(view)
    check(f"「{section.label}」里能找到子菜单入口",
          isinstance(sub, ft.SubmenuButton), True)
    check(f"「{sub.content.value}」从父项右边缘展开",
          sub.menu_style.alignment, ft.Alignment.TOP_RIGHT)
    check(f"「{sub.content.value}」不再额外下沉",
          sub.alignment_offset, None)

print()
print("=== 面板外观：两种面板共用同一套容器样式 ===")
top_panel = inner.controls[0].menu_style
sub_panel = nested(inner.controls[0]).menu_style
check("顶栏面板与子菜单面板同底色",
      top_panel.bgcolor, sub_panel.bgcolor)
check("面板底色比画布高一档（不与 SURFACE_CONTAINER_LOWEST 撞色）",
      top_panel.bgcolor, ft.Colors.SURFACE_CONTAINER)
check("顶栏面板与子菜单面板同描边",
      top_panel.side, sub_panel.side)
check("面板最小宽度", top_panel.min_size, ft.Size(MENU_WIDTH, 0))

print()
print("=== 菜单数据：检索与体检 ===")
check("叶子动作数（子菜单入口不计）", action_count(sections()), 7)
check("先序遍历含子菜单入口", len(list(iter_actions(sections()))), 9)
check("按 key 找得到", find_action(sections(), "assoc.off").label, "取消关联")
check("找不到给 None", find_action(sections(), "nope"), None)
check("快捷键表", shortcut_map(sections()),
      {"open": "Ctrl+O", "exit": "Esc", "fit": "Ctrl+0"})
check("数据体检无问题", validate_sections(sections()), ())
check(
    "重复键被查出来",
    validate_sections((MenuSection("a", (
        MenuAction("dup", "一"),
        MenuAction("dup", "二"),
    )),)),
    ("动作键重复：dup",),
)
check(
    "空栏被查出来",
    validate_sections((MenuSection("空", ()),)),
    ("菜单栏「空」没有任何项",),
)
check(
    "子菜单入口挂了快捷键被查出来",
    validate_sections((MenuSection("a", (
        MenuAction("parent", "父", shortcut="Ctrl+P", children=(
            MenuAction("child", "子"),
        )),
    )),)),
    ("子菜单入口「parent」不该带快捷键",),
)


print()
print("==============================================")
print(f"{_passes} passed, {_fails} failed")
raise SystemExit(1 if _fails else 0)
