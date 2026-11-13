"""MenuBar —— 桌面应用的**下拉菜单栏**（文件 / 编辑 / 视图 …）。

和 :class:`ui.navigation.menu.Menu` 的分工很清楚：``Menu`` 是常驻在侧边的
**导航树**（选中链路、展开、折叠），``MenuBar`` 是窗口顶部的一排**动作入口**
（点开一层下拉、执行完就收起）。把两者合成一个组件只会得到「侧边栏里也能弹出
下拉」这种谁都不需要的形态。

菜单是**数据**，不是一叠控件
----------------------------
``MenuAction`` / ``MenuSection`` 是不可变数据节点，渲染时才生成 Flet 控件。于是：

* 快捷键表、动作清单、禁用状态可以被打印、被断言、被 Agent 检索
  （:func:`shortcut_map` / :func:`find_action` / :func:`validate_sections`）；
* 同一份数据既能生成菜单，也能生成快捷键帮助页 —— 不会出现「菜单写 Ctrl+O、
  帮助页写 Ctrl+0」这种漂移；
* 状态变化（播放中 → 暂停、间隔 3s → 5s）由应用重建数据，不触碰已挂载的
  控件树（flet 1.1 的冻结树不允许在回调里改控件）。

参考 Electron / VS Code 的 ``Menu`` 数据模型、Ant Design 的菜单项三分区
（图标 / 文案 / 快捷键）、Material 3 的菜单 state layer。快捷键用 :class:`ui.Kbd`
画成键帽而不是拼接一行灰字 —— 键帽的形状本身就是「这是一个键」的信息。

用法::

    sections = (
        MenuSection("文件", (
            MenuAction("open", "打开图片", icon=ft.Icons.IMAGE, shortcut="Ctrl+O"),
            MenuAction("assoc", "文件关联", children=(
                MenuAction("assoc.install", "注册为打开方式"),
                MenuAction("assoc.uninstall", "取消关联"),
            )),
            MenuAction("exit", "退出", shortcut="Esc", separator_before=True),
        )),
    )
    MenuBar(sections=sections, on_action=lambda action: dispatch(action.key))
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from typing import Any

import flet as ft

from ui.core.doc import Api, Example, Spec, info, run, tip, warn
from ui.core.tokens import (
    DURATION,
    FONT_SIZE,
    FONT_WEIGHT,
    ICON_SIZE,
    RADIUS,
    SPACE,
    disabled_layer,
    hairline,
    state_layer,
)
from ui.display.kbd import Kbd

__all__ = [
    "BAR_HEIGHT",
    "ITEM_HEIGHT",
    "MENU_DROP",
    "MENU_WIDTH",
    "MenuAction",
    "MenuBar",
    "MenuSection",
    "action_count",
    "find_action",
    "iter_actions",
    "shortcut_map",
    "validate_sections",
]

#: 菜单栏高度 48（4px 网格的 SPACE["12"]），一行 13px 字上下各留 16px 空气。
BAR_HEIGHT: float = SPACE["12"]
#: 下拉项高度 32：桌面端鼠标操作的舒适下限，又不会让 12 项菜单长到半屏。
ITEM_HEIGHT: float = SPACE["8"]
#: 下拉面板最小宽度：让「Ctrl+Shift+O」这类长快捷键不与文案挤在一起。
MENU_WIDTH: float = 220.0
#: 顶栏栏目的面板下沉量：面板顶边正好落在栏底边。
#:
#: Flutter 的 ``MenuStyle.alignment`` 给出的是**对齐点**（``Alignment.withinRect``），
#: 不是「把面板内嵌进锚点矩形」。所以 ``TOP_LEFT`` 只能把面板左上角钉在按钮
#: 左上角 —— 面板就压在顶栏上了。要往下走必须补 :class:`flet.Offset`。
#: 栏目按整栏高度（:data:`BAR_HEIGHT`）布置，锚点顶边即栏顶边，于是偏移刚好一栏高。
MENU_DROP: float = BAR_HEIGHT


@dataclass(frozen=True, slots=True)
class MenuAction:
    """一个可执行的菜单项，或者一组子菜单的入口。

    Args:
        key: 稳定标识。**不要用 label 当键** —— 文案会随语言、随状态变
            （「播放」/「暂停」是同一个动作），键不会。
        label: 显示文案。简短、动词开头，不写标点。
        icon: 前导图标。一级项一般不必配，二级项配了更好扫读。
        shortcut: 快捷键串，``"Ctrl+Shift+O"`` 会渲染成三枚键帽。
        disabled: 禁用。整行置灰、不响应点击。
        checked: 当前项被选中（播放间隔、当前模式这类互斥选项），右侧打勾。
        separator_before: 在这一项上方插一条发丝线，分组而不新增嵌套。
        children: 非空即为子菜单入口，本身**不触发动作**。
        data: 业务载荷，回调里原样取走（例如播放间隔的秒数）。
        on_click: 单项回调，签名 ``(action) -> None``；留空则走
            :func:`MenuBar` 的统一 ``on_action``。
    """

    key: str
    label: str
    icon: ft.IconData | None = None
    shortcut: str = ""
    disabled: bool = False
    checked: bool = False
    separator_before: bool = False
    children: tuple[MenuAction, ...] = ()
    data: Any = None
    on_click: Callable[[MenuAction], None] | None = None

    @property
    def is_leaf(self) -> bool:
        return not self.children


@dataclass(frozen=True, slots=True)
class MenuSection:
    """顶栏的一栏（「文件」「视图」…）。"""

    label: str
    items: tuple[MenuAction, ...] = ()
    icon: ft.IconData | None = None


# ---------------------------------------------------------------------------
# 纯函数：检索、校验、可复算
# ---------------------------------------------------------------------------
def iter_actions(sections: Sequence[MenuSection]) -> Iterator[MenuAction]:
    """先序遍历所有动作（含子菜单入口），供文档 / 快捷键表 / 诊断读取。"""
    for section in sections:
        yield from _walk(section.items)


def _walk(items: Sequence[MenuAction]) -> Iterator[MenuAction]:
    for item in items:
        yield item
        yield from _walk(item.children)


def find_action(sections: Sequence[MenuSection], key: str) -> MenuAction | None:
    """按键找一个动作；找不到返回 ``None``（不给调用方抛异常的机会）。"""
    return next((item for item in iter_actions(sections) if item.key == key), None)


def shortcut_map(sections: Sequence[MenuSection]) -> dict[str, str]:
    """``{动作键: 快捷键}`` 快照。帮助页与键位冲突检查读这一份就够。"""
    return {
        item.key: item.shortcut
        for item in iter_actions(sections)
        if item.shortcut
    }


def action_count(sections: Sequence[MenuSection]) -> int:
    """可执行的叶子动作数（子菜单入口不计）。"""
    return sum(1 for item in iter_actions(sections) if item.is_leaf)


def validate_sections(sections: Sequence[MenuSection]) -> tuple[str, ...]:
    """数据体检：返回问题描述，空元组表示没问题。

    查三件事：重复键（分发会打到第一个，第二个永远点不到）、空栏（顶栏一个
    点不开的按钮）、子菜单入口挂了快捷键（它不执行动作，写了是误导）。
    应用启动时跑一次，比在运行时发现「某个菜单点了没反应」便宜得多。
    """
    problems: list[str] = []
    seen: set[str] = set()
    for section in sections:
        if not section.items:
            problems.append(f"菜单栏「{section.label}」没有任何项")
    for item in iter_actions(sections):
        if item.key in seen:
            problems.append(f"动作键重复：{item.key}")
        seen.add(item.key)
        if item.children and item.shortcut:
            problems.append(f"子菜单入口「{item.key}」不该带快捷键")
    return tuple(problems)


# ---------------------------------------------------------------------------
# 样式
# ---------------------------------------------------------------------------
def _panel_style(alignment: ft.Alignment) -> ft.MenuStyle:
    """下拉面板：浮在内容上的一块容器，靠描边 + 阴影与背景分开。

    ``alignment`` 不在这里写死，因为两种面板的展开方向不同：顶栏栏目要
    **落在栏下方**（``TOP_LEFT`` + :data:`MENU_DROP`），嵌套子菜单要
    **从父项右侧展开**（``TOP_RIGHT``）。写死一个会让另一种压住自己的锚点。

    底色用 ``SURFACE_CONTAINER``（Material 3 的菜单容器色）：它比
    ``SURFACE_CONTAINER_LOWEST`` 高一档。后者在深色主题里常常等于画布底色，
    压在空白画布上时面板与背景同色，只剩一圈描边能看出边界 —— 这个问题在
    ImageViewer 的空窗口里真实出现过。
    """
    return ft.MenuStyle(
        bgcolor=ft.Colors.SURFACE_CONTAINER,
        shadow_color=ft.Colors.SHADOW,
        elevation=8,
        shape=ft.RoundedRectangleBorder(radius=RADIUS["lg"]),
        side=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
        padding=ft.Padding.symmetric(vertical=SPACE["1"]),
        min_size=ft.Size(MENU_WIDTH, 0),
        alignment=alignment,
    )


def _bar_button_style() -> ft.ButtonStyle:
    """顶栏一栏：常态不铺底，悬停才给 8% 状态层，避免一整条被切成色块。"""
    return ft.ButtonStyle(
        color={
            ft.ControlState.DEFAULT: ft.Colors.ON_SURFACE_VARIANT,
            ft.ControlState.HOVERED: ft.Colors.ON_SURFACE,
        },
        bgcolor={ft.ControlState.HOVERED: state_layer("hover")},
        overlay_color=state_layer("pressed"),
        padding=ft.Padding.symmetric(horizontal=SPACE["3"], vertical=SPACE["1"]),
        shape=ft.RoundedRectangleBorder(radius=RADIUS["sm"]),
        animation_duration=DURATION["fast"],
        text_style=ft.TextStyle(size=FONT_SIZE["small"], weight=FONT_WEIGHT["medium"]),
    )


def _item_style() -> ft.ButtonStyle:
    """下拉项：整行可点，悬停靠状态层；文字色交给 MenuItemButton 的 content。"""
    return ft.ButtonStyle(
        padding=ft.Padding.symmetric(horizontal=SPACE["3"], vertical=SPACE["1"]),
        overlay_color=state_layer("hover"),
        shape=ft.RoundedRectangleBorder(radius=RADIUS["sm"]),
        animation_duration=DURATION["fast"],
    )


def _separator() -> ft.Control:
    """菜单内的一条发丝线，左右各缩进 8px，不顶到面板边。"""
    return ft.Container(
        height=1,
        margin=ft.Margin.symmetric(horizontal=SPACE["2"], vertical=SPACE["1"]),
        bgcolor=ft.Colors.OUTLINE_VARIANT,
    )


def _label(text: str, *, dim: bool = False) -> ft.Control:
    return ft.Text(
        text,
        size=FONT_SIZE["small"],
        color=disabled_layer() if dim else ft.Colors.ON_SURFACE,
        no_wrap=True,
        overflow=ft.TextOverflow.ELLIPSIS,
    )


def _trailing(item: MenuAction) -> ft.Control | None:
    """右侧区：键帽与选中勾。两者都在时用 Row 排，不互相覆盖。"""
    parts: list[ft.Control] = []
    if item.shortcut:
        parts.append(Kbd(item.shortcut, dim=item.disabled))
    if item.checked:
        parts.append(
            ft.Icon(ft.Icons.CHECK, size=ICON_SIZE["sm"], color=ft.Colors.PRIMARY)
        )
    if not parts:
        return None
    if len(parts) == 1:
        return parts[0]
    return ft.Row(spacing=SPACE["2"], tight=True, controls=parts)


def _fire(item: MenuAction, on_action: Callable[[MenuAction], None] | None) -> None:
    """统一分发：单项回调优先，其次菜单栏回调；两者都没有就安静地什么都不做。"""
    if item.disabled or not item.is_leaf:
        return
    if item.on_click is not None:
        item.on_click(item)
    elif on_action is not None:
        on_action(item)


def _action_view(
    item: MenuAction, on_action: Callable[[MenuAction], None] | None
) -> list[ft.Control]:
    """一个节点 → 一到两个控件（发丝线 + 菜单项）。"""
    out: list[ft.Control] = []
    if item.separator_before:
        out.append(_separator())

    if item.children:
        out.append(
            ft.SubmenuButton(
                content=_label(item.label),
                leading=(
                    ft.Icon(item.icon, size=ICON_SIZE["sm"],
                            color=ft.Colors.ON_SURFACE_VARIANT)
                    if item.icon else None
                ),
                controls=[
                    control
                    for child in item.children
                    for control in _action_view(child, on_action)
                ],
                style=_item_style(),
                # 子菜单从父项右边缘展开，顶边与父项齐平（桌面菜单的惯常行为）。
                menu_style=_panel_style(ft.Alignment.TOP_RIGHT),
            )
        )
        return out

    trailing = _trailing(item)
    out.append(
        ft.MenuItemButton(
            content=_label(item.label, dim=item.disabled),
            leading=(
                ft.Icon(item.icon, size=ICON_SIZE["sm"],
                        color=ft.Colors.ON_SURFACE_VARIANT)
                if item.icon else None
            ),
            trailing=trailing,
            disabled=item.disabled,
            style=_item_style(),
            on_click=lambda e, a=item: _fire(a, on_action),
        )
    )
    return out


def _section_view(
    section: MenuSection, on_action: Callable[[MenuAction], None] | None
) -> ft.Control:
    return ft.SubmenuButton(
        content=_label(section.label),
        leading=(
            ft.Icon(section.icon, size=ICON_SIZE["sm"],
                    color=ft.Colors.ON_SURFACE_VARIANT)
            if section.icon else None
        ),
        controls=[
            control
            for item in section.items
            for control in _action_view(item, on_action)
        ],
        # 撑满整栏：锚点顶边 = 栏顶边，配合 MENU_DROP 才能精确落在栏底边。
        # 顺带让悬停状态层铺满栏高，和 Windows 11 / VS Code 的顶栏观感一致。
        height=BAR_HEIGHT,
        style=_bar_button_style(),
        menu_style=_panel_style(ft.Alignment.TOP_LEFT),
        alignment_offset=ft.Offset(0, MENU_DROP),
    )


def MenuBar(
    *,
    sections: Sequence[MenuSection],
    on_action: Callable[[MenuAction], None] | None = None,
    height: float = BAR_HEIGHT,
    bgcolor: ft.ColorValue | None = None,
    divider: bool = True,
    divider_color: ft.ColorValue | None = None,
) -> ft.Control:
    """构建顶部菜单栏（纯函数）。

    Args:
        sections: 顶栏各栏的数据。
        on_action: 统一动作分发，入参 :class:`MenuAction`。单项自带
            ``on_click`` 时优先用它，便于少数动作要额外上下文。
        height: 菜单栏高度，默认 :data:`BAR_HEIGHT`（48）。
        bgcolor: 菜单栏底色，默认 ``SURFACE_CONTAINER_LOW``（明暗自适应）。
        divider: 底部分隔线，默认有。
        divider_color: 分隔线颜色。默认走 ``hairline()``（主题角色）；沉浸式
            深色应用可传自己色表里的边框色，让线与面板同族。

    Returns:
        一个可直接放进 ``Column.controls`` 的 :class:`flet.Container`。
    """
    line = ft.BorderSide(1, divider_color) if divider_color else hairline()
    return ft.Container(
        height=height,
        bgcolor=bgcolor if bgcolor is not None else ft.Colors.SURFACE_CONTAINER_LOW,
        border=ft.Border(bottom=line) if divider else None,
        alignment=ft.Alignment.CENTER_LEFT,
        padding=ft.Padding.symmetric(horizontal=SPACE["1"]),
        content=ft.MenuBar(
            controls=[_section_view(section, on_action) for section in sections],
            style=ft.MenuStyle(
                bgcolor=ft.Colors.TRANSPARENT,
                elevation=0,
                padding=0,
                visual_density=ft.VisualDensity.COMPACT,
            ),
        ),
    )


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
def _demo_sections() -> tuple[MenuSection, ...]:
    return (
        MenuSection("文件", (
            MenuAction("open", "打开图片", icon=ft.Icons.IMAGE_OUTLINED,
                       shortcut="Ctrl+O"),
            MenuAction("folder", "打开文件夹", icon=ft.Icons.FOLDER_OPEN_OUTLINED,
                       shortcut="Ctrl+Shift+O"),
            MenuAction("assoc", "文件关联", children=(
                MenuAction("assoc.install", "注册为打开方式"),
                MenuAction("assoc.remove", "取消关联"),
            )),
            MenuAction("exit", "退出", shortcut="Esc", separator_before=True),
        )),
        MenuSection("视图", (
            MenuAction("fit", "适应窗口", shortcut="Ctrl+0"),
            MenuAction("actual", "1:1 原始大小", shortcut="Ctrl+1"),
            MenuAction("interval", "播放间隔", children=(
                MenuAction("interval.3", "3 秒", checked=True, data=3),
                MenuAction("interval.5", "5 秒", data=5),
            )),
        )),
    )


@ft.component
def _basic() -> ft.Control:
    """点开任意一栏：图标 / 文案 / 键帽 / 勾 / 分隔线各就各位。"""
    picked, set_picked = ft.use_state("（还没点过）")
    return ft.Column(
        spacing=SPACE["3"],
        controls=[
            MenuBar(sections=_demo_sections(),
                    on_action=lambda item: set_picked(f"{item.label} · {item.key}")),
            ft.Container(
                padding=SPACE["4"],
                content=ft.Text(f"最近执行：{picked}", size=FONT_SIZE["small"],
                                color=ft.Colors.ON_SURFACE_VARIANT),
            ),
        ],
    )


@ft.component
def _snapshot() -> ft.Control:
    """同一份数据生成的快捷键表 —— 帮助页不必再抄一遍。"""
    rows = [
        ft.Text(f"{key}  →  {shortcut}", size=FONT_SIZE["small"],
                color=ft.Colors.ON_SURFACE_VARIANT)
        for key, shortcut in shortcut_map(_demo_sections()).items()
    ]
    return ft.Container(
        padding=SPACE["4"],
        content=ft.Column(spacing=SPACE["1"], tight=True, controls=rows),
    )


_MENU_CODE = """sections = (
    MenuSection("文件", (
        MenuAction("open", "打开图片", icon=ft.Icons.IMAGE, shortcut="Ctrl+O"),
        MenuAction("exit", "退出", shortcut="Esc", separator_before=True),
    )),
)
MenuBar(sections=sections, on_action=lambda a: dispatch(a.key))
shortcut_map(sections)   # {'open': 'Ctrl+O', 'exit': 'Esc'}"""

SPEC = Spec(
    name="MenuBar",
    summary="桌面端下拉菜单栏：数据驱动的动作用口，键帽显示快捷键，可导出快捷键表。",
    definition=(
        "窗口顶部的「文件 / 编辑 / 视图」是一排动作入口，不是导航树。本组件把菜单"
        "定义成不可变数据节点，渲染时才生成控件，因此快捷键表、动作清单、禁用与"
        "选中状态都能被检索、断言和复算；同一份数据还能生成帮助页，避免文案漂移。"
    ),
    anatomy=[
        ("顶栏一栏", "撑满栏高，常态不铺底、悬停整栏 8% 状态层；高度 48 对齐 4px 网格。"),
        ("下拉面板", "SURFACE_CONTAINER 底色（比画布高一档）+ 发丝描边 + 8 档阴影；"
                     "顶边落在栏底边，不压住顶栏。"),
        ("子菜单", "从父项右边缘向右展开，顶边与父项齐平。"),
        ("菜单项", "前导图标 / 文案 / 右侧键帽三分区，行高 32。"),
        ("选中与分隔", "互斥项右侧主色勾；分组用 1px 缩进发丝线，不额外嵌套。"),
    ],
    when=[
        "桌面应用需要常驻的文件 / 编辑 / 视图 / 帮助菜单",
        "动作较多且带快捷键，需要一份可查的键位表",
        "菜单项随状态变化（播放 / 暂停、当前档位打勾）",
    ],
    avoid=[
        "常驻侧边导航：用 Menu，那里需要选中链路与折叠",
        "右键上下文菜单：用 PopupMenuButton，锚点在鼠标位置",
        "只有三五个入口的轻工具：一排按钮比下拉少一次点击",
    ],
    examples=[
        Example("完整菜单栏", _basic, code=_MENU_CODE,
                hint="点开任意一栏，观察键帽、勾与分隔线；下方显示最近执行的动作。"),
        Example("导出快捷键表", _snapshot,
                hint="shortcut_map() 直接生成帮助页数据，不需要再抄一遍。"),
    ],
    api=(
        Api("sections", "Sequence[MenuSection]", "", "顶栏各栏的数据"),
        Api("on_action", "Callable[[MenuAction], None] | None", "None", "统一动作分发"),
        Api("height", "float", "48", "菜单栏高度"),
        Api("bgcolor", "ColorValue | None", "None", "底色；None 用主题角色"),
        Api("divider", "bool", "True", "底部分隔线"),
        Api("validate_sections", "function", "", "返回重复键 / 空栏等问题"),
    ),
    notes=[
        tip("用 on_action 统一分发、动作带稳定 key：文案随状态变（播放 ↔ 暂停）时"
            "不需要改任何一处分支，测试也只断言 key。"),
        info("快捷键交给 Kbd 画成键帽，而不是拼进文案。用户读到的是「这是一个键」，"
             "不是一条普通灰字；密度也更好控。"),
        info("面板位置靠 alignment + alignment_offset 两个量配合：Flutter 的 "
             "alignment 只给「对齐点」，不会把面板内嵌到锚点矩形里，所以顶栏栏目必须"
             f"补 MENU_DROP（{MENU_DROP:g}px）才会落在栏下方；子菜单则用 TOP_RIGHT "
             "向右展开。改这两个数之前先看 _panel_style 的注释。"),
        warn("不要在回调里改已挂载的菜单控件：flet 1.1 的控件树是冻结的。状态变了"
             "就重建 sections 数据，让组件整棵重渲染。"),
    ],
    tags=("菜单栏", "下拉菜单", "桌面菜单", "menu bar", "快捷键", "键帽"),
)


if __name__ == "__main__":
    run(SPEC)
