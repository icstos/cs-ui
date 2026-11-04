"""步骤条组件 (Step)。

把"一件事分几步、做到第几步"讲清楚。参考 layui-vue ``lay-step`` 与
Element Plus ``el-steps`` 的共识能力，收敛成桌面端形态：

- **状态机**：每步只会是 ``wait`` / ``process`` / ``finish`` / ``error`` 之一。
  默认按 ``active`` 推导（``index < active`` 已完成、``== active`` 进行中、
  ``> active`` 未开始），也可以在 :class:`StepItem` 上用 ``status`` 单独钉死；
- **两种排布**：``horizontal``（横向平铺，默认）/ ``vertical``（左侧轴轨）；
- **简洁模式**：``simple=True`` 收成一行 "① 标题 › ② 标题"，适合放在工具栏或
  页面顶部，点击即跳转；
- **进度着色**：只给"已经走过"的连接段上色，没走到的是灰线 —— 进度感来自颜色，
  不靠额外装饰；
- **可点击**：``clickable=True``（简洁模式默认开）时整步都是热区，回传
  ``on_change(index)``；组件同时就地更新 ``active``，使用方接不接都有反馈。

.. note::
    组件是**受控**的：``active`` 由使用方给定，点击时的就地更新只是让反馈即时，
    真正的状态源仍在调用方 —— 这样"上一步 / 下一步 / 点击跳转"三条路径行为一致。

.. note::
    圆点永远与**标题首行**垂直居中：横向时标题块顶在圆点行下沿，垂直时标题装进
    与圆点等高的行盒。所以改 ``dot_size`` 轴线也不会歪。

.. note::
    flet 没有"边框虚线"，也未提供步骤条原生控件，连接线由两侧 ``expand`` 的
    半段线拼成 —— 圆点因此在格心，改步骤数量也不会跑偏。

用法::

    Step(
        steps=[
            StepItem("填写信息", "账号与联系方式"),
            StepItem("验证邮箱", "点击邮件里的链接"),
            StepItem("完成", "开始使用"),
        ],
        active=1,
    )
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import flet as ft

__all__ = ["Step", "StepItem"]

# ---------------------------------------------------------------------------
# 尺寸
# ---------------------------------------------------------------------------
DOT = 26  # 圆点直径
DOT_SMALL = 22  # 简洁模式的序号徽章
LINE = 2  # 连接线粗细

TITLE_SIZE = 14
DESC_SIZE = 12
TEXT_GAP = 10  # 圆点行与标题的间距
DESC_GAP = 3  # 标题与描述的间距

ROW_GAP = 20  # 垂直模式每步的下边距
RAIL_GAP = 12  # 垂直模式轴轨与文字的间距

MUTED = ft.Colors.ON_SURFACE_VARIANT
HIDDEN = ft.Colors.TRANSPARENT

#: 步骤状态：``wait`` 未开始 / ``process`` 进行中 / ``finish`` 已完成 / ``error`` 出错。
STATUSES = ("wait", "process", "finish", "error")
STATUS_ALIASES = {"fail": "error", "success": "finish"}

#: 状态 → 文字色（``finish`` 落回常规前景色）。
TEXT_COLORS: dict[str, ft.ColorValue] = {
    "process": ft.Colors.PRIMARY,
    "error": ft.Colors.ERROR,
    "wait": ft.Colors.OUTLINE,
}


@dataclass
class StepItem:
    """一个步骤。

    Args:
        title: 步骤标题（一句话说清这一步做什么）。
        description: 次要说明，显示在标题下方。
        icon: 圆点里的图标。不给时按状态自动取：已完成对勾、出错叉、其余用序号。
        status: 钉死该步状态（``wait`` / ``process`` / ``finish`` / ``error``，
            也接受 ``fail`` / ``success``），不给则跟随 :attr:`Step.active` 推导。
    """

    title: str
    description: str = ""
    icon: ft.IconData | None = None
    status: str | None = None


@ft.control
class Step(ft.Container):
    """步骤条，继承自 :class:`flet.Container`。

    Args:
        steps: :class:`StepItem` 列表，也接受 ``{"title": ..., "description": ...}``
            这种字典写法。
        active: 当前进行到第几步（从 0 开始）；``-1`` 表示一步都没开始。
        direction: ``horizontal``（默认）或 ``vertical``。
        process_status: 当前步的状态，默认 ``process``；想让当前步报错就给 ``error``。
        finish_status: 当前步之前那些步的状态，默认 ``finish``。
        align_center: 横向模式文字是否居中（默认 ``True``）；``False`` 时左对齐。
        simple: 简洁模式 —— 一行序号 + 标题，步骤间用 ``›`` 分隔。
        clickable: 整步可点（触发 :attr:`on_change`）；简洁模式默认开启。
        on_change: 点击回调，参数是被点中的步骤下标。
        dot_size: 圆点直径，默认 26。
    """

    steps: list[StepItem | dict[str, Any]] = field(default_factory=list)
    active: int = 0
    direction: str = "horizontal"
    process_status: str = "process"
    finish_status: str = "finish"
    align_center: bool = True
    simple: bool = False
    clickable: bool = False
    on_change: Callable[[int], None] | None = None
    dot_size: int = DOT

    def init(self):
        self._items: list[StepItem] = [_as_item(s) for s in self.steps]
        self.content = self._build()

    # ------------------------------------------------------------------
    # 状态推导
    # ------------------------------------------------------------------
    @property
    def _current(self) -> int:
        """当前步下标，自动夹在 ``[-1, len-1]`` 内。"""
        if not self._items:
            return -1
        return max(-1, min(self.active, len(self._items) - 1))

    @property
    def _centered(self) -> bool:
        """文字是否居中 —— 只有横向平铺才居中；垂直轴轨和简洁模式一律左对齐。"""
        return (
            self.align_center
            and not self.simple
            and self.direction != "vertical"
        )

    def _status(self, index: int) -> str:
        """该步状态：显式 ``status`` 优先，否则按与 active 的位置关系推导。"""
        pinned = _norm_status(self._items[index].status)
        if pinned is not None:
            return pinned
        current = self._current
        if index < current:
            return _norm_status(self.finish_status) or "finish"
        if index == current:
            return _norm_status(self.process_status) or "process"
        return "wait"

    def _line_color(self, segment: int) -> ft.ColorValue | None:
        """第 ``segment`` 段（连接 ``segment-1`` 与 ``segment``）的颜色。

        ``None`` 表示这一段不存在 —— 首步左边、末步右边都该空着，但**占位宽度
        要留着**，否则圆点会往一侧偏。已经走过的段用主色，其余灰。
        """
        if segment <= 0 or segment >= len(self._items):
            return None
        return (
            ft.Colors.PRIMARY
            if self._current >= segment
            else ft.Colors.OUTLINE_VARIANT
        )

    def _seg(self, segment: int) -> ft.Control:
        """横向的一段连接线（永远占位，只是可能透明）。"""
        return ft.Container(
            expand=True,
            height=LINE,
            bgcolor=self._line_color(segment) or HIDDEN,
        )

    # ------------------------------------------------------------------
    # 圆点
    # ------------------------------------------------------------------
    def _dot(self, index: int, status: str, side: float | None = None) -> ft.Control:
        """圆点 / 徽章：``finish`` 实心、``process`` 淡底描边、``error`` 实心红、``wait`` 灰描边。"""
        size = side or self.dot_size
        item = self._items[index]
        icon = item.icon or _default_icon(status)
        radius = ft.BorderRadius.all(size / 2)
        common = {"width": size, "height": size, "border_radius": radius}

        if status in ("finish", "error"):
            return ft.Container(
                **common,
                bgcolor=(
                    ft.Colors.PRIMARY if status == "finish" else ft.Colors.ERROR
                ),
                alignment=ft.Alignment.CENTER,
                content=_glyph(icon, size, index, ft.Colors.ON_PRIMARY),
            )
        if status == "process":
            return ft.Container(
                **common,
                border=ft.Border.all(LINE, ft.Colors.PRIMARY),
                bgcolor=ft.Colors.with_opacity(0.10, ft.Colors.PRIMARY),
                alignment=ft.Alignment.CENTER,
                content=_glyph(icon, size, index, ft.Colors.PRIMARY),
            )
        return ft.Container(
            **common,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            alignment=ft.Alignment.CENTER,
            content=_glyph(icon, size, index, ft.Colors.OUTLINE),
        )

    # ------------------------------------------------------------------
    # 文字
    # ------------------------------------------------------------------
    def _title(self, index: int, status: str, *, boxed: bool = False) -> ft.Control:
        """标题。``boxed`` 用于垂直模式：塞进与圆点等高的行盒，与圆点对中。"""
        text = ft.Text(
            self._items[index].title,
            size=TITLE_SIZE,
            weight=(
                ft.FontWeight.W_600 if status in ("process", "finish") else None
            ),
            color=TEXT_COLORS.get(status, ft.Colors.ON_SURFACE),
            text_align=ft.TextAlign.CENTER if self._centered else ft.TextAlign.LEFT,
            no_wrap=True,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        if boxed:
            return ft.Container(
                height=self.dot_size,
                alignment=ft.Alignment.CENTER_LEFT,
                content=text,
            )
        return ft.Container(
            alignment=(
                ft.Alignment.CENTER if self._centered else ft.Alignment.CENTER_LEFT
            ),
            content=text,
        )

    def _desc(self, index: int) -> ft.Control | None:
        """描述文字；空描述返回 ``None``（调用方直接跳过）。"""
        desc = self._items[index].description
        if not desc:
            return None
        return ft.Container(
            alignment=(
                ft.Alignment.CENTER if self._centered else ft.Alignment.CENTER_LEFT
            ),
            content=ft.Text(
                desc,
                size=DESC_SIZE,
                color=MUTED,
                text_align=ft.TextAlign.CENTER if self._centered else ft.TextAlign.LEFT,
                max_lines=2,
                overflow=ft.TextOverflow.ELLIPSIS,
            ),
        )

    # ------------------------------------------------------------------
    # 三种布局
    # ------------------------------------------------------------------
    def _build(self) -> ft.Control:
        if not self._items:
            return ft.Row()
        if self.simple:
            return self._simple_row()
        if self.direction == "vertical":
            return self._vertical()
        return self._horizontal()

    def _horizontal(self) -> ft.Control:
        """横向：每步等宽，圆点在格心，相邻两半线拼成连续的一条。"""
        cells: list[ft.Control] = []
        for index in range(len(self._items)):
            status = self._status(index)
            head = ft.Row(
                spacing=0,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    self._seg(index),
                    self._dot(index, status),
                    self._seg(index + 1),
                ],
            )
            cells.append(
                self._cell(
                    index,
                    ft.Column(
                        spacing=TEXT_GAP,
                        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                        controls=[
                            c
                            for c in (
                                head,
                                self._title(index, status),
                                self._desc(index),
                            )
                            if c is not None
                        ],
                    ),
                )
            )
        return ft.Row(
            spacing=0,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=cells,
        )

    def _vertical(self) -> ft.Control:
        """垂直：左侧一条轴轨，圆点与标题首行居中对齐。"""
        rows: list[ft.Control] = []
        last = len(self._items) - 1
        for index in range(len(self._items)):
            status = self._status(index)
            side = self.dot_size
            rail = ft.Stack(
                width=side,
                controls=[
                    ft.Container(
                        left=(side - LINE) / 2,
                        top=0 if index > 0 else side / 2,
                        bottom=0,
                        width=LINE,
                        bgcolor=self._line_color(index + 1) or HIDDEN,
                    ),
                    ft.Container(
                        left=0,
                        top=0,
                        width=side,
                        height=side,
                        alignment=ft.Alignment.CENTER,
                        content=self._dot(index, status),
                    ),
                ],
            )
            body = ft.Container(
                expand=True,
                padding=ft.Padding.only(
                    left=RAIL_GAP, bottom=0 if index == last else ROW_GAP
                ),
                content=ft.Column(
                    spacing=DESC_GAP,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                    controls=[
                        c
                        for c in (
                            self._title(index, status, boxed=True),
                            self._desc(index),
                        )
                        if c is not None
                    ],
                ),
            )
            self._make_hot(index, body)
            rows.append(
                ft.Row(
                    spacing=0,
                    # intrinsic_height + STRETCH：轴轨 Stack 的固有高度是 0，
                    # 先按内容量出整行高度再把轴轨拉满；少了它整行会炸到无界高。
                    intrinsic_height=True,
                    vertical_alignment=ft.CrossAxisAlignment.STRETCH,
                    controls=[rail, body],
                )
            )
        return ft.Column(spacing=0, controls=rows)

    def _simple_row(self) -> ft.Control:
        """简洁模式：``① 标题 › ② 标题``，当前步高亮，整块可点。"""
        cells: list[ft.Control] = []
        for index in range(len(self._items)):
            status = self._status(index)
            chip = ft.Container(
                padding=ft.Padding.symmetric(horizontal=8, vertical=5),
                border_radius=8,
                content=ft.Row(
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        self._dot(index, status, side=DOT_SMALL),
                        ft.Text(
                            self._items[index].title,
                            size=13,
                            weight=(
                                ft.FontWeight.W_600
                                if status in ("process", "finish")
                                else None
                            ),
                            color=TEXT_COLORS.get(status, ft.Colors.ON_SURFACE),
                            no_wrap=True,
                        ),
                    ],
                ),
            )
            cells.append(self._make_hot(index, chip))
            if index < len(self._items) - 1:
                cells.append(
                    ft.Icon(
                        ft.Icons.CHEVRON_RIGHT,
                        size=16,
                        color=ft.Colors.OUTLINE_VARIANT,
                    )
                )
        # 不用 ``wrap``：Row 交给 Flutter 的是 Wrap，宽度约束是 loose 时会塌成
        # "一项一行"。步骤条本就该是一行，放不下时横向滚动更符合桌面直觉。
        return ft.Row(
            spacing=2,
            scroll=ft.ScrollMode.AUTO,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=cells,
        )

    # ------------------------------------------------------------------
    # 交互
    # ------------------------------------------------------------------
    def _interactive(self) -> bool:
        return bool(self.simple or self.clickable) and self.on_change is not None

    def _make_hot(self, index: int, box: ft.Container) -> ft.Container:
        """把一个已经定好尺寸的容器就地变成点击热区（不再套壳 —— 套壳会打断 flex）。"""
        if not self._interactive():
            return box
        # 水波纹与悬停高亮交给 Material ink，不需要 Python 侧重绘。
        box.ink = True
        box.ink_color = ft.Colors.with_opacity(0.06, ft.Colors.PRIMARY)
        box.on_click = lambda _e, i=index: self._select(i)
        return box

    def _cell(self, index: int, content: ft.Control) -> ft.Container:
        """横向的一格：本身是 Row 的 flex 子项（``expand``），所以整格等宽。

        横向不留内边距 —— 相邻两格各自的半段线要严丝合缝地对上，
        留一点缝就会露出断口。
        """
        box = ft.Container(
            expand=True,
            padding=ft.Padding.only(top=4, bottom=8),
            border_radius=8,
            content=content,
        )
        return self._make_hot(index, box)

    def _select(self, index: int) -> None:
        """点击某一步：就地更新 ``active`` 再回调，反馈与状态源都不落空。"""
        if index == self._current:
            return
        self.active = index
        try:
            self.content = self._build()
            self.update()
        except Exception:  # noqa: BLE001 - 尚未挂到页面时只回调，不刷新
            pass
        if self.on_change is not None:
            self.on_change(index)


# ---------------------------------------------------------------------------
# 小工具
# ---------------------------------------------------------------------------
def _as_item(raw: StepItem | dict[str, Any]) -> StepItem:
    return raw if isinstance(raw, StepItem) else StepItem(**raw)


def _norm_status(value: str | None) -> str | None:
    """归一状态名：``fail`` → ``error``、``success`` → ``finish``；非法返回 ``None``。"""
    if not value:
        return None
    name = STATUS_ALIASES.get(value, value)
    return name if name in STATUSES else None


def _default_icon(status: str) -> ft.IconData | None:
    if status == "finish":
        return ft.Icons.CHECK
    if status == "error":
        return ft.Icons.CLOSE
    return None


def _glyph(
    icon: ft.IconData | None, side: float, index: int, color: ft.ColorValue
) -> ft.Control:
    """圆点内容：有图标画图标，没有就画序号（从 1 开始）。"""
    if icon is not None:
        return ft.Icon(icon, size=side * 0.54, color=color)
    return ft.Text(
        str(index + 1),
        size=max(12.0, side * 0.46),
        weight=ft.FontWeight.W_600,
        color=color,
    )
