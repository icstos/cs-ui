"""时间线组件 (Timeline)。

以垂直时间轴展示事件流。参考 Element Plus ``el-timeline``、Ant Design ``Timeline``、
Vuetify ``v-timeline`` 与 MUI ``Timeline`` 的共识能力，收敛成桌面端的形态：

- **三种对齐**：``mode="right"``（轴在左，默认）/ ``"left"``（轴在右）/
  ``"alternate"``（左右交替，中轴居中）；
- **时间戳位置**：``time_position="opposite"``（默认，放在轴**另一侧**独立成列 ——
  VS Code 时间线视图、GitHub 提交列表都是这个形态）/ ``"top"``（标题上方，
  Element Plus 风格）/ ``"inline"``（与标题同行、分居两端 —— 旧版行为）/
  ``"hidden"``；
- **节点语义**：``type`` 给语义色（primary / success / warning / danger / info /
  neutral），``variant`` 给形态（``filled`` 实心 / ``outlined`` 空心环 /
  ``plain`` 轻量小点），``size`` 给三档尺寸（small / default / large）；
  每项都可在 :class:`TimelineItem` 上单独覆盖；
- **连接线**：``line_color`` / ``line_width`` / ``show_last_line``，
  ``line_fade=True`` 让末段渐隐收尾，``line_style="none"`` 去掉线只留节点；
- **节奏**：``density`` 三档（compact / default / comfortable）；
- **交互**：item 级 ``on_click`` 或全局 ``on_item_click`` 让整行可点，
  悬停高亮与点击水波纹由 Material 的 ``ink`` 绘制；``disabled`` 置灰且不可点；
- **进行中节点**：``pending`` 在末尾挂一个空心环节点（Ant Design 的 pending）；
- **富内容**：item 的 ``content`` 可塞任意控件，``subtitle`` 只是它的快捷写法。

.. note::
    节点**始终与内容首行垂直居中**：轴轨与内容两侧共用同一个"首行行盒"高度，
    所以换 ``size``（18 / 26 / 34）或 ``density`` 之后轴线依然笔直，
    节点不会相对标题上下漂。

.. note::
    flet 的 ``ft.BorderStyle`` 只有 ``NONE`` / ``SOLID``，画不出虚线边框，
    因此没有 ``line_style="dashed"``；线型收敛为 ``solid`` / ``none`` +
    ``line_fade`` 渐隐。

.. note::
    ``done=True`` 是 ``icon=CHECK`` + ``type="success"`` 的语法糖；
    显式给了 ``icon`` / ``color`` / ``type`` 就以显式值为准。

用法::

    Timeline(items=[
        TimelineItem("项目启动", "09-01 09:00", "完成立项", icon=ft.Icons.ROCKET_LAUNCH),
        TimelineItem("开发完成", "09-18 18:20", done=True),
        TimelineItem("灰度发布", "待开始"),
    ])
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import flet as ft

__all__ = ["Timeline", "TimelineItem"]

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------
#: 兼容旧值的默认节点色（未给 ``type`` / ``color`` 时兜底）。
DEFAULT_COLOR = "#1f6feb"
#: 兼容旧值 —— 等价于 ``size="default"``。
DOT_SIZE = 26
LINE_WIDTH = 2
RAIL_WIDTH = 32

#: 语义色。flet 的 ``ft.Colors`` 没有 SUCCESS / WARNING / INFO，
#: 这几档取与项目其它组件一致的固定色（demo 里已在用同一套）。
TYPE_COLORS: dict[str, ft.ColorValue] = {
    "success": "#10b981",
    "warning": "#f59e0b",
    "danger": "#ef4444",
    "info": "#6b7280",
}

DOT_SIZES: dict[str, int] = {"small": 18, "default": DOT_SIZE, "large": 34}

#: 内容首行的基准行盒高度。节点与它共用同一个行盒，轴线才不歪。
FIRST_LINE_H = 22

#: 密度：``gap`` = 相邻节点的留白，``pad`` = 悬停底色相对内容的外扩。
DENSITIES: dict[str, dict[str, int]] = {
    "compact": {"gap": 8, "pad": 3},
    "default": {"gap": 14, "pad": 6},
    "comfortable": {"gap": 26, "pad": 8},
}

MODES = ("right", "left", "alternate")
TIME_POSITIONS = ("opposite", "top", "inline", "hidden")
VARIANTS = ("filled", "outlined", "plain")
LINE_STYLES = ("solid", "none")

RAIL_PAD = 6  # 轴轨在节点两侧的留白
RAIL_GAP = 8  # 轴轨与内容之间的间距
TIME_GAP = 12  # 时间戳列与轴轨之间的间距

_TITLE_SIZE = 14
_SUB_SIZE = 12
_TIME_SIZE = 12

MUTED = ft.Colors.ON_SURFACE_VARIANT
DISABLED_FG = ft.Colors.with_opacity(0.38, ft.Colors.ON_SURFACE)


@dataclass
class TimelineItem:
    """时间线上的一个节点。

    Args:
        title: 主标题。
        time: 时间戳文本。
        subtitle: 次要说明文本（``content`` 的快捷写法）。
        icon: 节点图标。``None`` 时按 ``variant`` 画圆点。
        color: 节点颜色，优先级最高。
        done: 已完成 —— 未显式给 ``icon`` 时用对勾、未给 ``color`` / ``type`` 时用
            ``success`` 色。
        type: 语义色名（primary / success / warning / danger / info / neutral）。
        variant: 节点形态（filled / outlined / plain），覆盖 :class:`Timeline` 同名参数。
        size: 节点尺寸（small / default / large），覆盖 :class:`Timeline` 同名参数。
        content: 富内容控件，追加在文字之后（可用它放任意控件）。
        on_click: 点击回调，优先于 :attr:`Timeline.on_item_click`。
        disabled: 置灰且不可点。
    """

    title: str
    time: str = ""
    subtitle: str = ""
    icon: ft.IconData | None = None
    color: ft.ColorValue | None = None
    done: bool = False
    type: str | None = None
    variant: str | None = None
    size: str | None = None
    content: ft.Control | None = None
    on_click: Callable[["TimelineItem"], None] | None = None
    disabled: bool = False


@ft.control
class Timeline(ft.Column):
    """垂直时间线组件，继承自 :class:`flet.Column`。

    Args:
        items: :class:`TimelineItem` 列表。
        line_color: 连接线颜色，默认跟随主题 ``OUTLINE_VARIANT``。
        dot_size: 显式指定所有节点的直径；``None``（默认）则跟随 ``size``。
        show_last_line: 是否画出最后一个节点下方的连接线。
        mode: 对齐方式 —— ``right`` / ``left`` / ``alternate``。
        time_position: 时间戳位置 —— ``opposite`` / ``top`` / ``inline`` / ``hidden``。
        time_width: ``opposite`` 且非 ``alternate`` 时，时间列的宽度。
        density: 疏密 —— ``compact`` / ``default`` / ``comfortable``。
        reverse: 倒序展示（最新的在最上面）。
        size: 节点尺寸 —— ``small`` / ``default`` / ``large``。
        variant: 节点形态 —— ``filled`` / ``outlined`` / ``plain``。
        type: 默认语义色 —— ``primary`` / ``success`` / ``warning`` / ``danger`` /
            ``info`` / ``neutral``。
        line_width: 连接线宽度，默认 2。
        line_fade: 让最后一个节点下方的线渐隐收尾（同时会画出该段线）。
        line_style: ``solid``（默认）或 ``none``（去掉线，只留节点）。
        pending: 末尾的"进行中"节点 —— ``True`` 用默认文案，字符串自定义标题，
            也可以直接给一个 :class:`TimelineItem`。
        ink: 可点击项是否带材质水波纹与悬停高亮（由 Flutter 的 Material ink 绘制，
            不需要 Python 侧重绘，所以在大列表里也不掉帧）。
        on_item_click: 全局点击回调，接收被点的 :class:`TimelineItem`。
    """

    items: list[TimelineItem] = field(default_factory=list)
    line_color: ft.ColorValue = ft.Colors.OUTLINE_VARIANT
    dot_size: int | None = None
    show_last_line: bool = False

    mode: str = "right"
    time_position: str = "opposite"
    time_width: int = 112
    density: str = "default"
    reverse: bool = False

    size: str = "default"
    variant: str = "filled"
    type: str = "primary"

    line_width: int = LINE_WIDTH
    line_fade: bool = False
    line_style: str = "solid"

    pending: str | TimelineItem | bool | None = None
    ink: bool = True
    on_item_click: Callable[[TimelineItem], None] | None = None

    def init(self):
        self.spacing = 0
        # 每行是一个 Row，其中内容列用 expand 吃掉剩余宽度 —— 交叉轴必须 STRETCH，
        # 否则 Row 会 shrink-wrap 成"时间列 + 轴轨"的宽度，内容列被压成 0 宽。
        self.horizontal_alignment = ft.CrossAxisAlignment.STRETCH

        ordered = list(reversed(self.items)) if self.reverse else list(self.items)
        pending = self._pending_item()
        total = len(ordered) + (1 if pending is not None else 0)

        # 轴轨宽度与首行行盒都取"最大节点"口径算一次，保证全域一致：
        # 所有节点落在同一条中轴上，且与各自内容首行垂直居中。
        dots = [self._dot_h(item) for item in ordered]
        if pending is not None:
            dots.append(self._dot_h(pending))
        self._dot_max: int = max(dots or [DOT_SIZE])
        self._node_h: int = max(FIRST_LINE_H, self._dot_max + 2)

        controls: list[ft.Control] = [
            self._build_row(item, index, total, is_pending=False)
            for index, item in enumerate(ordered)
        ]
        if pending is not None:
            controls.append(
                self._build_row(pending, total - 1, total, is_pending=True)
            )
        self.controls = controls

    # ------------------------------------------------------------------
    # 参数归一
    # ------------------------------------------------------------------
    def _opt(self, value: str, allowed: tuple[str, ...], fallback: str) -> str:
        return value if value in allowed else fallback

    @property
    def _mode(self) -> str:
        return self._opt(self.mode, MODES, "right")

    @property
    def _time_position(self) -> str:
        return self._opt(self.time_position, TIME_POSITIONS, "opposite")

    @property
    def _density(self) -> dict[str, int]:
        return DENSITIES.get(self.density, DENSITIES["default"])

    @property
    def _gap(self) -> int:
        return self._density["gap"]

    @property
    def _pad(self) -> int:
        return self._density["pad"]

    def _type_color(self, name: str | None) -> ft.ColorValue | None:
        """语义色名 → 颜色；未知返回 ``None``（由调用方兜底）。"""
        if name == "primary":
            return ft.Colors.PRIMARY
        if name == "neutral":
            return ft.Colors.OUTLINE
        return TYPE_COLORS.get(name or "")

    def _dot_h(self, item: TimelineItem) -> int:
        """该节点的直径。显式 ``dot_size`` 优先，其次 item.size，最后全局 size。"""
        if self.dot_size:
            return int(self.dot_size)
        return DOT_SIZES.get(item.size or self.size, DOT_SIZE)

    def _item_variant(self, item: TimelineItem) -> str:
        return self._opt(item.variant or self.variant, VARIANTS, "filled")

    def _item_icon(self, item: TimelineItem) -> ft.IconData | None:
        if item.icon is not None:
            return item.icon
        return ft.Icons.CHECK if item.done else None

    def _item_color(self, item: TimelineItem, is_pending: bool = False) -> ft.ColorValue:
        """节点颜色，优先级：color > type > done > pending > 全局 type > 兜底。"""
        if item.color is not None:
            return item.color
        if item.type is not None:
            return self._type_color(item.type) or DEFAULT_COLOR
        if item.done:
            return self._type_color("success") or DEFAULT_COLOR
        if is_pending:
            return ft.Colors.PRIMARY
        return self._type_color(self.type) or DEFAULT_COLOR

    def _content_on_right(self, index: int) -> bool:
        """该行的内容在轴的右侧吗。"""
        mode = self._mode
        if mode == "left":
            return False
        if mode == "alternate":
            return index % 2 == 0
        return True

    def _pending_item(self) -> TimelineItem | None:
        """把 ``pending`` 参数归一成一个 :class:`TimelineItem`。"""
        pending = self.pending
        if pending is None or pending is False:
            return None
        if isinstance(pending, TimelineItem):
            return pending
        if pending is True:
            return TimelineItem(title="进行中")
        return TimelineItem(title=str(pending))

    # ------------------------------------------------------------------
    # 行
    # ------------------------------------------------------------------
    def _build_row(
        self, item: TimelineItem, index: int, total: int, *, is_pending: bool
    ) -> ft.Control:
        """一行 = ``[对侧时间列] + 轴轨 + 内容``（内容在左时左右互换）。"""
        first = index == 0
        last = index == total - 1
        on_right = self._content_on_right(index)

        rail = self._rail(item, first, last, is_pending)
        body = self._build_content(item, on_right, is_pending)

        # 时间列无条件占位（哪怕这一项没有时间戳）—— 否则该行的轴轨会左移，
        # 整条时间线在这一行断开对齐。``alternate`` 下更是必须占位：
        # 少了它中轴就偏到一侧去了。
        time_cell: ft.Control | None = None
        if self._time_position == "opposite" or self._mode == "alternate":
            time_cell = self._time_cell(item, on_right)

        cells: list[ft.Control] = (
            [time_cell, rail, body] if on_right else [body, rail, time_cell]
        )
        # intrinsic_height 是必须的：它让 Row 先用"固有高度"量一遍子项
        # （轴轨里那条 Stack 的固有高度是 0，行高因此完全由内容决定），
        # 再把这个高度以 **tight** 约束发给每个子项 —— 于是 STRETCH 能把
        # 轴轨拉到与内容等高，线的 top / bottom 定位也就有了参照。
        # 少了它，Row 会拿着父级给的"无界高度"去拉伸子项，整行会炸到无限高
        # （症状：第一行占满整屏、后面的行全被挤出视口）。
        return ft.Row(
            spacing=0,
            intrinsic_height=True,
            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[c for c in cells if c is not None],
        )

    def _rail(
        self, item: TimelineItem, first: bool, last: bool, is_pending: bool
    ) -> ft.Control:
        """轴轨：连接线 + 节点，都用 :class:`flet.Stack` 绝对定位摆放。

        这里**不能用 ``expand`` 撑线**：`ft.Column` 的主轴是垂直方向，而时间线
        每一行的高度是由右侧内容决定的（父级给的高度约束是"无界"），
        ``expand`` 的子项会让这个 Column 反过来把整行撑到无限高 ——
        表现就是第一行占满整屏、后面的行全被挤出视口。

        改用 Stack 的 ``top`` / ``bottom`` 定位后，Stack 的固有高度只由节点决定，
        行高仍然由内容说了算；Stretch 会把 Stack 拉到行高，线也就自然撑满了。

        - 非首行：线从**行顶**开始，接住上一行落下来的半段；
        - 首行：线从节点中心开始（上方不画）；
        - 末行：``show_last_line`` / ``line_fade`` 为假时，线止于内容底部
          （留出 ``gap`` 的空档），为真时延伸到行底并可渐隐。
        """
        rail_w = self._dot_max + RAIL_PAD * 2
        node_h = self._node_h
        dot_h = self._dot_h(item)
        show_below = (not last) or self.show_last_line or self.line_fade

        line: ft.Control = ft.Container(
            left=rail_w / 2 - self.line_width / 2,
            top=0 if not first else node_h / 2,
            bottom=0 if show_below else self._gap,
            width=self.line_width,
        )
        if self.line_style != "none":
            if last and self.line_fade:
                line.gradient = ft.LinearGradient(
                    begin=ft.Alignment.TOP_CENTER,
                    end=ft.Alignment.BOTTOM_CENTER,
                    colors=[
                        self.line_color,
                        ft.Colors.with_opacity(0.0, self.line_color),
                    ],
                )
            else:
                line.bgcolor = self.line_color

        return ft.Stack(
            width=rail_w,
            controls=[
                line,
                ft.Container(
                    left=(rail_w - dot_h) / 2,
                    top=(node_h - dot_h) / 2,
                    width=dot_h,
                    height=dot_h,
                    alignment=ft.Alignment.CENTER,
                    content=self._dot(item, is_pending),
                ),
            ],
        )

    # ------------------------------------------------------------------
    # 节点
    # ------------------------------------------------------------------
    def _dot(self, item: TimelineItem, is_pending: bool) -> ft.Control:
        """节点。``filled`` 实心 / ``outlined`` 空心环 / ``plain`` 轻量小点。"""
        size = self._dot_h(item)
        color = self._item_color(item, is_pending)
        radius = ft.BorderRadius.all(size / 2)
        icon = self._item_icon(item)

        if is_pending:
            # 进行中：空心环 + 中心小实心点（不依赖虚线，flet 画不出虚线边框）
            core = size * 0.28
            return ft.Container(
                width=size,
                height=size,
                border_radius=radius,
                border=ft.Border.all(self.line_width + 1, color),
                bgcolor=ft.Colors.SURFACE,
                alignment=ft.Alignment.CENTER,
                content=ft.Container(
                    width=core,
                    height=core,
                    border_radius=ft.BorderRadius.all(core / 2),
                    bgcolor=color,
                ),
            )

        if self._item_variant(item) == "plain":
            dot = size * 0.42
            return ft.Container(
                width=dot,
                height=dot,
                border_radius=ft.BorderRadius.all(dot / 2),
                bgcolor=color,
            )

        if self._item_variant(item) == "outlined":
            core = size * 0.34
            return ft.Container(
                width=size,
                height=size,
                border_radius=radius,
                border=ft.Border.all(2, color),
                bgcolor=ft.Colors.SURFACE,
                alignment=ft.Alignment.CENTER,
                content=(
                    ft.Icon(icon, size=size * 0.55, color=color)
                    if icon is not None
                    else ft.Container(
                        width=core,
                        height=core,
                        border_radius=ft.BorderRadius.all(core / 2),
                        bgcolor=color,
                    )
                ),
            )

        # filled
        if icon is not None:
            return ft.Container(
                width=size,
                height=size,
                border_radius=radius,
                bgcolor=color,
                alignment=ft.Alignment.CENTER,
                content=ft.Icon(icon, size=size * 0.55, color=ft.Colors.WHITE),
            )
        core = size * 0.5
        return ft.Container(
            width=core,
            height=core,
            border_radius=ft.BorderRadius.all(core / 2),
            bgcolor=color,
        )

    # ------------------------------------------------------------------
    # 内容
    # ------------------------------------------------------------------
    def _time_cell(self, item: TimelineItem, on_right: bool) -> ft.Control:
        """对侧的时间列。``alternate`` 下用 ``expand`` 让中轴真正居中。

        ``time_position="hidden"`` 时列里不放文字，但**列本身照样保留** ——
        它已经成了中轴定位的一部分。
        """
        align = ft.Alignment.CENTER_RIGHT if on_right else ft.Alignment.CENTER_LEFT
        pad = (
            ft.Padding.only(right=TIME_GAP)
            if on_right
            else ft.Padding.only(left=TIME_GAP)
        )
        label = "" if self._time_position == "hidden" else item.time
        cell = ft.Container(
            width=None if self._mode == "alternate" else self.time_width,
            padding=pad,
            content=ft.Column(
                spacing=0,
                horizontal_alignment=(
                    ft.CrossAxisAlignment.END
                    if on_right
                    else ft.CrossAxisAlignment.START
                ),
                controls=[
                    ft.Container(
                        height=self._node_h,
                        alignment=align,
                        content=ft.Text(
                            label,
                            size=_TIME_SIZE,
                            color=DISABLED_FG if item.disabled else ft.Colors.OUTLINE,
                            # 时间戳不允许折行 —— 折了就会把行高撑开、轴线跟着错位
                            no_wrap=True,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                    )
                ],
            ),
        )
        if self._mode == "alternate":
            cell.expand = True
        return cell

    def _content_lines(self, item: TimelineItem, on_right: bool) -> list[ft.Control]:
        """内容区的行控件列表。**第一行**会被放进固定高度的"首行行盒"与节点对中。

        ``time_position`` 决定时间戳落到哪里（``top`` 在标题上方、``inline`` 与标题
        同行两端、``opposite`` 由 :meth:`_time_cell` 在另一侧成列、``hidden`` 不显示）。
        """
        t_align = ft.TextAlign.LEFT if on_right else ft.TextAlign.RIGHT
        fg = DISABLED_FG if item.disabled else None

        title = ft.Text(
            item.title,
            size=_TITLE_SIZE,
            weight=ft.FontWeight.W_600,
            text_align=t_align,
            color=fg,
            # 首行行盒高度固定（节点要与它垂直居中），所以标题必须单行；
            # 需要多行说明请用 subtitle，或者直接塞 content 控件。
            no_wrap=True,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        time_text = (
            ft.Text(item.time, size=_TIME_SIZE, color=fg or ft.Colors.OUTLINE)
            if item.time
            else None
        )

        tpos = self._time_position
        if tpos == "top" and time_text is not None:
            lines: list[ft.Control] = [time_text, title]
        elif tpos == "inline" and time_text is not None:
            lines = [
                ft.Row(
                    spacing=8,
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[title, time_text],
                )
            ]
        else:
            lines = [title]

        if item.subtitle:
            lines.append(
                ft.Text(
                    item.subtitle,
                    size=_SUB_SIZE,
                    color=fg or MUTED,
                    text_align=t_align,
                )
            )
        if item.content is not None:
            lines.append(item.content)
        return lines

    def _build_content(
        self, item: TimelineItem, on_right: bool, is_pending: bool
    ) -> ft.Control:
        """内容区：首行行盒 + 后续行，可点击时套一层 Material ink。"""
        lines = self._content_lines(item, on_right)

        inner = ft.Column(
            spacing=2,
            horizontal_alignment=(
                ft.CrossAxisAlignment.START
                if on_right
                else ft.CrossAxisAlignment.END
            ),
            controls=[
                ft.Container(
                    height=self._node_h,
                    alignment=(
                        ft.Alignment.CENTER_LEFT
                        if on_right
                        else ft.Alignment.CENTER_RIGHT
                    ),
                    content=lines[0],
                ),
                *lines[1:],
            ],
        )

        box = ft.Container(
            padding=ft.Padding.symmetric(horizontal=self._pad, vertical=self._pad),
            border_radius=8,
            content=inner,
        )

        clickable = not item.disabled and bool(item.on_click or self.on_item_click)
        if clickable:
            # 悬停高亮与点击水波纹都交给 Material 的 ink 去画。
            # 这里**不能**用 on_hover 回写 bgcolor：`@ft.component` 构建出的控件树
            # 是 frozen 的（flet `components/component.py` 会给每个控件打 _frozen），
            # 命令式 `control.update()` 会直接抛
            # `RuntimeError: Frozen control cannot be updated.`。
            box.ink = self.ink
            box.ink_color = ft.Colors.with_opacity(0.08, ft.Colors.ON_SURFACE)
            box.on_click = lambda _e, it=item: self._fire(it)

        wrap = ft.Container(
            expand=True,
            padding=ft.Padding.only(bottom=self._gap),
            content=box,
        )
        return wrap

    def _fire(self, item: TimelineItem) -> None:
        callback = item.on_click or self.on_item_click
        if callback is not None:
            callback(item)


@ft.component
def App():
    """Timeline 组件运行示例。"""
    return ft.Column(
        scroll=ft.ScrollMode.AUTO,
        spacing=20,
        # 时间线需要横向约束才会撑满；放在 shrink-wrap 的 Column 里会被压扁。
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        controls=[
            ft.Column(
                spacing=4,
                controls=[
                    ft.Text("Timeline 时间线", size=20, weight=ft.FontWeight.BOLD),
                    ft.Text(
                        "时间在轴的对侧独立成列，节点与标题垂直居中；"
                        "pending 在末尾挂一个进行中节点。",
                        size=13,
                        color="#6b7280",
                    ),
                ],
            ),
            ft.Divider(),
            ft.Text("默认（time_position=opposite + type 语义色）", size=16, weight=ft.FontWeight.BOLD),
            Timeline(
                items=[
                    TimelineItem(
                        "项目启动",
                        "2026-09-01 09:00",
                        "完成立项与团队组建",
                        icon=ft.Icons.ROCKET_LAUNCH,
                        type="primary",
                    ),
                    TimelineItem(
                        "需求评审",
                        "2026-09-05 10:30",
                        "确认 12 项需求，关闭 3 项疑问",
                        icon=ft.Icons.FACT_CHECK,
                        type="info",
                    ),
                    TimelineItem(
                        "开发完成",
                        "2026-09-18 18:20",
                        "全部组件迁移至 Flet 1.0.0",
                        done=True,
                    ),
                    TimelineItem("灰度发布", "2026-09-26 14:00", "首批 5% 流量", type="warning"),
                ],
                pending="待全量上线",
            ),
            ft.Divider(),
            ft.Text("左右交替（mode=alternate）", size=16, weight=ft.FontWeight.BOLD),
            Timeline(
                mode="alternate",
                items=[
                    TimelineItem("上午 9:00", "09:00", "晨会同步进度", type="info"),
                    TimelineItem("上午 11:30", "11:30", "完成接口联调", done=True),
                    TimelineItem("下午 14:00", "14:00", "修复 3 个回归问题", type="warning"),
                    TimelineItem("下午 18:20", "18:20", "提交测试版本", done=True),
                ],
                line_fade=True,
            ),
            ft.Divider(),
            ft.Text("空心环 + 紧凑 + 可点击", size=16, weight=ft.FontWeight.BOLD),
            Timeline(
                variant="outlined",
                size="small",
                density="compact",
                time_position="inline",
                items=[
                    TimelineItem("提交申请", "09:12", "材料已上传", done=True),
                    TimelineItem("部门审批", "10:30", "审核人：张工", type="warning"),
                    TimelineItem("财务复核", "14:05", "等待财务确认", type="info"),
                    TimelineItem("归档", "—", "完成后自动归档", disabled=True),
                ],
                on_item_click=lambda item: print(f"[Timeline] 点击 {item.title}"),
            ),
            ft.Divider(),
            ft.Text("无轴线的事件流（line_style=none + plain）", size=16, weight=ft.FontWeight.BOLD),
            Timeline(
                variant="plain",
                line_style="none",
                density="compact",
                size="small",
                items=[
                    TimelineItem("构建成功", "10:00", "耗时 42s", type="success"),
                    TimelineItem("部署测试环境", "10:12", "v1.4.0-rc1", type="warning"),
                    TimelineItem("自动化用例", "10:20", "128 / 128 通过", type="success"),
                ],
            ),
            ft.Divider(),
            ft.Text("轴在右（mode=left）· 时间在上（time_position=top）", size=16, weight=ft.FontWeight.BOLD),
            Timeline(
                mode="left",
                time_position="top",
                dot_size=22,
                items=[
                    TimelineItem("v0.9.0", "2026-08-12", "组件库首次发布"),
                    TimelineItem("v1.0.0", "2026-09-26", "迁移至 Flet 1.0.0", done=True),
                ],
            ),
        ],
    )


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
