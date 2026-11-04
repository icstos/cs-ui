"""日历 (Calendar) —— 整月大日历面板。

参考 Ant Design ``Calendar``。它和 :class:`~ui.input.DateInput` 不是一回事：

============  ====================================  ==========================
               ``DateInput``                          ``Calendar``
============  ====================================  ==========================
回答的问题      "选哪一天"                             "这段时间里有什么"
形态           下拉面板，一格 34px，点完即收            整面板，格子够大
每格内容        日期数字                              数字 + 任意控件
============  ====================================  ==========================

所以 ``Calendar`` 的格子留了 ``cell_content``：日程条数、值班人、版本号、
当天的小色点，都塞得进去。

用法::

    cal = Calendar(
        value=date(2026, 11, 5),
        cell_content=lambda day: dot if day.day % 7 == 0 else None,
        on_select=lambda day: print("选中", day),
    )
    Column([cal.ui()])

四条实现取舍（改前先读）
------------------------
1. **只有月 / 年两级，没有"十年"级**。AntD 的头部是「年下拉 + 月下拉」，本库
   统一走"点标题放大"这一手（``DateInput`` 已经是这样）：点标题进月网格，点
   月份回月视图，标题本身就是当前粒度，不需要额外的下拉控件。
2. **选中态收在内侧小胶囊上，不铺满整格**。整月日历的格子宽到 100px 以上，
   整格填色会糊成一块色斑；把"选中 / 今天 / 悬停"收进 30px 的圆角胶囊，
   格子再宽也读得出选的是哪一天，观感与 AntD 一致。
3. **悬停只换一个胶囊底色，且范围没变就不重绘**。42 个格子各挂 ``on_hover``，
   鼠标划过一行会收到几十次事件 —— 比较"当前悬停的那一天"，没变就直接 return。
4. **月视图固定 6 行**。有的月份 4 行就够（如 2 月 1 日恰逢周首），但行数随
   月份变会让整个面板上下跳；固定 42 格，切月时高度恒定。跨月的格子照常
   显示（灰字），点它直接跳到那个月 —— 这是日历最自然的"翻页"手势。

性能：一次渲染约 42 × 3 个控件（含格子内的小胶囊），悬停只重建这一层，
本机 <1ms。年份视图同理 12 格。
"""

from __future__ import annotations

import datetime as _dt
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import flet as ft

from ui.core.format import calendar_title, first_weekday, month_cell, weekday_names
from ui.core.i18n import t, use_t
from ui.core.theme import use_theme
from ui.core.tokens import FONT_SIZE, FONT_WEIGHT, RADIUS, SPACE, hairline, overlay

__all__ = ["MODES", "Calendar", "month_grid", "shift_month"]

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------
#: 面板粒度。``month`` = 6 × 7 日网格；``year`` = 4 × 3 月网格。
MODES: tuple[str, ...] = ("month", "year")

GRID_COLS = 7
GRID_ROWS = 6
UNIT_COLS = 3  # 年视图：一行 3 个月
UNIT_ROWS = 4  # 年视图：一共 4 行

DOT = 30  # 数字胶囊的直径（选中 / 今天 / 悬停都画在这个尺寸里）
DEFAULT_CELL_H = 42  # 日期格高；要往格里放内容时调大
WEEKDAY_H = 32  # 星期表头高
TITLE_PAD_H = 8  # 标题左右内边距
TITLE_PAD_V = 4


# ---------------------------------------------------------------------------
# 纯函数（单测直接断言这几个）
# ---------------------------------------------------------------------------
def shift_month(year: int, month: int, delta: int) -> tuple[int, int]:
    """``(2026, 11)`` 加 ``-1`` 个月 → ``(2026, 10)``；跨年自动进位。"""
    index = year * 12 + (month - 1) + delta
    return index // 12, index % 12 + 1


def month_grid(year: int, month: int, first_day: int = 0) -> tuple[_dt.date, ...]:
    """月历网格的 42 天（``GRID_ROWS * GRID_COLS``）。

    Args:
        year: 年。
        month: 月（1~12）。
        first_day: 每周首日，``0`` = 周一 … ``6`` = 周日。

    Returns:
        网格第一格到最后一格的日期，首尾可能落在上 / 下个月 —— 这是**故意**的：
        固定 42 格才能让面板高度不随月份跳动。
    """
    first = _dt.date(year, month, 1)
    offset = (first.weekday() - first_day) % 7
    start = first - _dt.timedelta(days=offset)
    return tuple(start + _dt.timedelta(days=i) for i in range(GRID_ROWS * GRID_COLS))


def weekday_labels(first_day: int = 0) -> tuple[str, ...]:
    """按首日旋转后的 7 个星期标签（长度恒为 7）。

    ``weekday_names()`` 的下标与 ``date.weekday()`` 一致（0 = 周一），首列要放
    首日，所以序列从该下标开始绕一圈。语言包给短了就补，宁可重复也不让表头错位。
    """
    source = list(weekday_names())
    while len(source) < 7:
        source.append(str(len(source) + 1))
    labels = source[:7]
    offset = int(first_day) % 7
    return tuple(labels[offset:] + labels[:offset])


def _today() -> _dt.date:
    """本地时区下的"今天"。

    不用 ``date.today()``（ruff DTZ011 会拦），也**不能**用 UTC 的今天 ——
    日历高亮的是用户眼前这一天，UTC+8 的凌晨在 UTC 里还停在昨天。
    """
    return _dt.datetime.now(tz=_dt.UTC).astimezone().date()


def _entering(value: object) -> bool:
    """把 hover 事件载荷归一成"进来了吗"（可能是 bool，也可能是 ``"true"``）。"""
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


# ---------------------------------------------------------------------------
# 组件
# ---------------------------------------------------------------------------
@ft.observable
@dataclass
class Calendar:
    """整月大日历。

    Args:
        value: 初始选中的日期，``None`` 表示不选中（视图仍从今天所在月开始）。
            **它只是初始值**：之后用 :meth:`select` 改，或读 :attr:`selected`。
        mode: 初始粒度，``month`` 或 ``year``。
        first_day_of_week: 每周首日，``0`` = 周一 … ``6`` = 周日；``None`` 跟随
            语言包（中文周一、英文周日）。
        valid_range: 可选区间 ``(最早, 最晚)``，区间外的格子灰掉且不可点。
        disabled_date: 逐日禁用，入参 ``date``，返回 ``True`` 表示该日不可选。
            与 ``valid_range`` 取交集（两个限制同时生效）。
        cell_height: 日期格高度，默认 42；要往格里放内容时调大（如 72）。
        cell_content: 每格的附加内容，入参 ``date``，返回控件或 ``None``。
            渲染在日期数字**下方**，像 AntD 的 ``dateCellRender``。
        show_today: 是否显示「今天」按钮。
        footer: 网格下方的自定义区域（当天的日程列表之类）。
        width: 组件宽度，``None`` 跟随父容器。
        on_select: 选中某天时回调，入参 ``date``。
        on_panel_change: 视图变化（翻页 / 切换粒度）时回调，入参
            ``(当前月首日, mode)``。

    Notes:
        网格按行 ``expand``，所以它**会吃满父容器宽度**：日历就该是宽的。
        要定宽就包一层 ``Container(width=...)``。
    """

    value: _dt.date | None = None
    mode: str = "month"
    first_day_of_week: int | None = None
    valid_range: tuple[_dt.date, _dt.date] | None = None
    disabled_date: Callable[[_dt.date], bool] | None = None
    cell_height: float = DEFAULT_CELL_H
    cell_content: Callable[[_dt.date], ft.Control | None] | None = None
    show_today: bool = True
    footer: ft.Control | None = None
    width: int | float | None = None
    on_select: Callable[[_dt.date], None] | None = None
    on_panel_change: Callable[[_dt.date, str], None] | None = None

    # ---- 运行期状态（下划线开头：不参与构造，靠 notify() 重绘）--------------
    _view: tuple[int, int] = field(
        default=(1970, 1), init=False, repr=False
    )
    _selected: _dt.date | None = field(default=None, init=False, repr=False)
    _hover: _dt.date | None = field(default=None, init=False, repr=False)
    _hover_key: str | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.mode not in MODES:
            raise ValueError(f"mode 只能是 {MODES}，收到 {self.mode!r}")
        if self.valid_range is not None:
            lo, hi = self.valid_range
            if lo > hi:
                raise ValueError("valid_range 的先后顺序反了")
        start = self.value or _today()
        self._selected = self.value
        self._view = (start.year, start.month)

    # ==================================================================
    # 对外查询
    # ==================================================================
    @property
    def selected(self) -> _dt.date | None:
        """当前选中的日期（没选则为 ``None``）。"""
        return self._selected

    @property
    def view(self) -> tuple[int, int]:
        """正在显示的年月 ``(year, month)``。"""
        return self._view

    def is_enabled(self, day: _dt.date) -> bool:
        """这一天能不能选（``valid_range`` 与 ``disabled_date`` 同时满足）。"""
        if self.valid_range is not None:
            lo, hi = self.valid_range
            if day < lo or day > hi:
                return False
        return not (self.disabled_date is not None and self.disabled_date(day))

    # ==================================================================
    # 状态变更（也可以从代码里调，不只是点格子）
    # ==================================================================
    def select(self, day: _dt.date) -> None:
        """选中某天：同步把视图挪到它所在的月，并触发 ``on_select``。"""
        if not self.is_enabled(day):
            return
        if day == self._selected and (day.year, day.month) == self._view:
            return  # 重复点同一天不重绘
        self._selected = day
        self._view = (day.year, day.month)
        self._repaint()
        if self.on_select is not None:
            self.on_select(day)

    def go_to(self, year: int, month: int) -> None:
        """跳转到某年某月（不改变选中）。"""
        month = min(12, max(1, int(month)))
        if (year, month) == self._view:
            return
        self._view = (year, month)
        self._repaint()
        self._panel_changed()

    def shift(self, delta: int) -> None:
        """翻页：月视图翻 ``delta`` 个月，年视图翻 ``delta`` 年。"""
        year, month = self._view
        if self.mode == "year":
            year += delta
        else:
            year, month = shift_month(year, month, delta)
        self._view = (year, month)
        self._repaint()
        self._panel_changed()

    def set_mode(self, mode: str) -> None:
        """切换粒度：``month`` ↔ ``year``。"""
        if mode not in MODES:
            raise ValueError(f"mode 只能是 {MODES}，收到 {mode!r}")
        if mode == self.mode:
            return
        self.mode = mode
        self._repaint()
        self._panel_changed()

    def go_today(self) -> None:
        """回到今天：切回月视图、跳到本月，可选则顺手选中。"""
        today = _today()
        changed = self.mode != "month" or self._view != (today.year, today.month)
        self.mode = "month"
        self._view = (today.year, today.month)
        picked = self.is_enabled(today) and today != self._selected
        if picked:
            self._selected = today
        self._repaint()
        if picked and self.on_select is not None:
            self.on_select(today)
        if changed:
            self._panel_changed()

    def invalidate(self) -> None:
        """外部改了 ``disabled_date`` / ``valid_range`` 之后调一下，强制重绘。"""
        self._repaint()

    # ==================================================================
    # 内部工具
    # ==================================================================
    def _repaint(self) -> None:
        """请求重绘。

        名字**不能**叫 ``_notify``：``@ft.observable`` 自己注入了
        ``_notify(name)``，用它做属性变更通知（签名不同，覆盖了会直接
        ``TypeError``）。
        """
        notify = getattr(self, "notify", None)
        if callable(notify):
            notify()

    def _panel_changed(self) -> None:
        if self.on_panel_change is not None:
            year, month = self._view
            self.on_panel_change(_dt.date(year, month, 1), self.mode)

    def _first_day(self) -> int:
        """每周首日：显式给就用显式的，``None`` 跟随界面语言。"""
        if self.first_day_of_week is None:
            return first_weekday()
        return int(self.first_day_of_week) % 7

    def _hover_cell(self, day: _dt.date, value: object) -> None:
        """日期格悬停：范围没变就不重绘（鼠标划过一行会来几十次事件）。"""
        entering = _entering(value)
        current = self._hover
        if entering:
            if current == day:
                return
            self._hover = day
        else:
            if current != day:
                return  # 离开的是别的格子（事件顺序乱时会出现），忽略
            self._hover = None
        self._repaint()

    def _hover_unit(self, key: str, value: object) -> None:
        """月 / 年格悬停，同上。"""
        entering = _entering(value)
        if entering:
            if self._hover_key == key:
                return
            self._hover_key = key
        else:
            if self._hover_key != key:
                return
            self._hover_key = None
        self._repaint()

    # ==================================================================
    # 页头
    # ==================================================================
    def _header(self) -> ft.Control:
        step_key = "ui.calendar.prev_year" if self.mode == "year" else "ui.calendar.prev_month"
        forward_key = (
            "ui.calendar.next_year" if self.mode == "year" else "ui.calendar.next_month"
        )
        controls: list[ft.Control] = [
            self._title(),
            _nav_button(ft.Icons.CHEVRON_LEFT, t(step_key), lambda _e: self.shift(-1)),
            _nav_button(ft.Icons.CHEVRON_RIGHT, t(forward_key), lambda _e: self.shift(1)),
        ]
        if self.show_today:
            controls.append(
                _text_button(t("ui.date.today"), lambda _e: self.go_today())
            )
        controls.extend([ft.Container(expand=True), self._mode_switch()])
        return ft.Container(
            padding=ft.Padding.only(bottom=SPACE["2"]),
            content=ft.Row(
                spacing=SPACE["1"],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=controls,
            ),
        )

    def _title(self) -> ft.Control:
        """标题 = 当前粒度的文字（``2026年11月`` / ``2026年``），点它放大一级。"""
        year, month = self._view
        text = calendar_title(year, month, mode=self.mode)
        target = "month" if self.mode == "year" else "year"
        hovered = self._hover_key == "title"
        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=TITLE_PAD_H, vertical=TITLE_PAD_V),
            border_radius=RADIUS["md"],
            bgcolor=overlay(0.06) if hovered else None,
            on_click=lambda _e: self.set_mode(target),
            on_hover=lambda e: self._hover_unit("title", e.data),
            content=ft.Row(
                spacing=SPACE["1"],
                tight=True,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text(
                        text,
                        size=FONT_SIZE["title"],
                        weight=FONT_WEIGHT["semibold"],
                        color=ft.Colors.ON_SURFACE,
                    ),
                    # 小箭头是"可以点"的视觉提示：没有它，标题看着像纯文字
                    ft.Icon(
                        ft.Icons.ARROW_DROP_DOWN_ROUNDED
                        if self.mode == "month"
                        else ft.Icons.ARROW_DROP_UP_ROUNDED,
                        size=18,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                ],
            ),
        )

    def _mode_switch(self) -> ft.Control:
        """「月 / 年」两档切换。"""
        return ft.Container(
            padding=2,
            border_radius=RADIUS["full"],
            bgcolor=overlay(0.06),
            content=ft.Row(
                spacing=0,
                tight=True,
                controls=[
                    _segment(
                        t("ui.calendar.mode.month"),
                        active=self.mode == "month",
                        on_click=lambda _e: self.set_mode("month"),
                    ),
                    _segment(
                        t("ui.calendar.mode.year"),
                        active=self.mode == "year",
                        on_click=lambda _e: self.set_mode("year"),
                    ),
                ],
            ),
        )

    # ==================================================================
    # 视图主体
    # ==================================================================
    def _weekday_row(self) -> ft.Control:
        return ft.Container(
            # 一条 1px 发丝线把表头和日期分开：42 个数字堆在一起时，
            # 没有它很难一眼看出"星期这一行"到哪儿结束。
            border=ft.Border.only(bottom=hairline()),
            content=ft.Row(
                spacing=0,
                controls=[
                    ft.Container(
                        expand=True,
                        height=WEEKDAY_H,
                        alignment=ft.Alignment.CENTER,
                        content=ft.Text(
                            label,
                            size=FONT_SIZE["small"],
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                    )
                    for label in weekday_labels(self._first_day())
                ],
            ),
        )

    def _month_body(self) -> ft.Control:
        year, month = self._view
        days = month_grid(year, month, self._first_day())
        rows = [
            ft.Row(
                spacing=0,
                controls=[
                    self._day_cell(day, (day.year, day.month) == (year, month))
                    for day in days[row * GRID_COLS : (row + 1) * GRID_COLS]
                ],
            )
            for row in range(GRID_ROWS)
        ]
        return ft.Container(
            padding=ft.Padding.only(top=SPACE["1"]),
            content=ft.Column(spacing=0, tight=True, controls=rows),
        )

    def _day_cell(self, day: _dt.date, in_month: bool) -> ft.Control:
        """单个日期格：数字胶囊 + 可选附加内容。

        胶囊负责表达状态（选中实心 / 今天描边 / 悬停淡底），附加内容在它下方，
        两者都在一个垂直居中的列里 —— 有内容时数字不会被顶到格子上沿。
        """
        enabled = self.is_enabled(day)
        picked = day == self._selected
        today = day == _today()
        hovered = enabled and self._hover == day

        if picked:
            color: ft.ColorValue = ft.Colors.ON_PRIMARY
        elif not enabled:
            color = ft.Colors.OUTLINE_VARIANT
        elif today:
            color = ft.Colors.PRIMARY
        elif in_month:
            color = ft.Colors.ON_SURFACE
        else:
            # 跨月的日子要**明显**比本月淡一档：只差一个色阶（on_surface_variant）
            # 在浅色主题下几乎看不出来，网格会读成"这个月有 42 天"。
            color = ft.Colors.OUTLINE

        if picked:
            bg: ft.ColorValue | None = ft.Colors.PRIMARY
        elif hovered:
            bg = overlay(0.08)
        else:
            bg = None

        pill = ft.Container(
            width=DOT,
            height=DOT,
            bgcolor=bg,
            border=None if picked or not today else ft.Border.all(1, ft.Colors.PRIMARY),
            border_radius=RADIUS["full"],
            alignment=ft.Alignment.CENTER,
            content=ft.Text(
                str(day.day),
                size=FONT_SIZE["body"],
                color=color,
                weight=FONT_WEIGHT["semibold"]
                if picked or today
                else FONT_WEIGHT["regular"],
            ),
        )

        body: list[ft.Control] = [pill]
        if self.cell_content is not None:
            extra = self.cell_content(day)
            if extra is not None:
                body.append(ft.Container(content=extra, padding=ft.Padding.only(top=2)))

        return ft.Container(
            expand=True,
            height=self.cell_height,
            padding=ft.Padding.symmetric(vertical=SPACE["1"], horizontal=2),
            on_click=None if not enabled else (lambda _e, d=day: self.select(d)),
            on_hover=None if not enabled else (lambda e, d=day: self._hover_cell(d, e)),
            content=ft.Column(
                spacing=0,
                tight=True,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=body,
            ),
        )

    def _year_body(self) -> ft.Control:
        year = self._view[0]
        rows = [
            ft.Row(
                spacing=0,
                controls=[
                    self._month_unit(year, row * UNIT_COLS + col + 1)
                    for col in range(UNIT_COLS)
                ],
            )
            for row in range(UNIT_ROWS)
        ]
        return ft.Column(spacing=SPACE["2"], tight=True, controls=rows)

    def _month_unit(self, year: int, month: int) -> ft.Control:
        """年视图里的一个月。点它 = 回到该月的日视图。"""
        key = f"m{year}-{month}"
        picked = self._selected is not None and (
            self._selected.year,
            self._selected.month,
        ) == (year, month)
        hovered = self._hover_key == key

        if picked:
            color: ft.ColorValue = ft.Colors.ON_PRIMARY
        else:
            color = ft.Colors.ON_SURFACE

        pill = ft.Container(
            # 宽度跟着文字走（不是定宽）：``11月`` 与 ``Nov`` 差一倍，
            # 钉死宽度在英文界面里会变成一个空荡荡的长胶囊。
            padding=ft.Padding.symmetric(horizontal=SPACE["4"], vertical=SPACE["1"] - 1),
            bgcolor=ft.Colors.PRIMARY if picked else (overlay(0.08) if hovered else None),
            border_radius=RADIUS["full"],
            alignment=ft.Alignment.CENTER,
            content=ft.Text(
                month_cell(month),
                size=FONT_SIZE["body"],
                color=color,
                weight=FONT_WEIGHT["semibold"]
                if picked
                else FONT_WEIGHT["regular"],
            ),
        )
        return ft.Container(
            expand=True,
            height=self.cell_height + SPACE["3"],
            on_click=lambda _e, m=month: self._pick_month(year, m),
            on_hover=lambda e, k=key: self._hover_unit(k, e.data),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[pill],
            ),
        )

    def _pick_month(self, year: int, month: int) -> None:
        """年视图点了某个月：视图落到那个月，粒度回到月。"""
        self._view = (year, month)
        self.mode = "month"
        self._repaint()
        self._panel_changed()

    # ==================================================================
    # 装配
    # ==================================================================
    @ft.component
    def ui(self) -> ft.Control:
        """构建日历。"""
        use_t()  # 订阅语言：月份名、星期名、「今天」跟着切
        use_theme()  # 订阅主题：胶囊与悬停底色都是角色色

        rows: list[ft.Control] = [self._header()]
        if self.mode == "year":
            rows.append(self._year_body())
        else:
            rows.append(self._weekday_row())
            rows.append(self._month_body())
        if self.footer is not None:
            rows.append(
                ft.Container(
                    padding=ft.Padding.only(top=SPACE["3"]), content=self.footer
                )
            )
        return ft.Container(
            width=self.width,
            content=ft.Column(spacing=0, tight=True, controls=rows),
        )


# ---------------------------------------------------------------------------
# 小控件（页头用）
# ---------------------------------------------------------------------------
def _nav_button(icon: str, tooltip: str, on_click: Any) -> ft.Control:
    """页头的翻页箭头：28×28 的小方块，悬停淡底。"""
    return ft.IconButton(
        icon=icon,
        icon_size=18,
        width=28,
        height=28,
        padding=0,
        tooltip=tooltip,
        style=ft.ButtonStyle(
            color={ft.ControlState.DEFAULT: ft.Colors.ON_SURFACE_VARIANT},
            overlay_color=overlay(0.08),
        ),
        on_click=on_click,
    )


def _text_button(label: str, on_click: Any) -> ft.Control:
    """"今天"这类纯文字按钮：比 ``Button`` 轻，不抢箭头与标题的层级。"""
    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=SPACE["2"], vertical=SPACE["1"]),
        border_radius=RADIUS["md"],
        on_click=on_click,
        content=ft.Text(
            label,
            size=FONT_SIZE["small"],
            color=ft.Colors.PRIMARY,
            weight=FONT_WEIGHT["medium"],
        ),
    )


def _segment(label: str, *, active: bool, on_click: Any) -> ft.Control:
    """「月 / 年」里的一个分段。"""
    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=SPACE["3"], vertical=SPACE["1"]),
        border_radius=RADIUS["full"],
        bgcolor=ft.Colors.SURFACE if active else None,
        on_click=on_click,
        content=ft.Text(
            label,
            size=FONT_SIZE["small"],
            color=ft.Colors.ON_SURFACE if active else ft.Colors.ON_SURFACE_VARIANT,
            weight=FONT_WEIGHT["semibold"] if active else FONT_WEIGHT["regular"],
        ),
    )


# ---------------------------------------------------------------------------
# 演示
# ---------------------------------------------------------------------------
@ft.component
def App():
    """Calendar 运行示例。"""
    def dot(day: _dt.date) -> ft.Control | None:
        """每 5 天来一个小色点，示意"这天有事"。"""
        if day.day % 5:
            return None
        return ft.Container(
            width=5,
            height=5,
            border_radius=RADIUS["full"],
            bgcolor=ft.Colors.PRIMARY,
        )

    plain = Calendar(value=_dt.date(2026, 11, 5))
    marked = Calendar(value=_dt.date(2026, 11, 5), cell_height=64, cell_content=dot)
    year = Calendar(value=_dt.date(2026, 11, 5), mode="year")
    return ft.Column(
        spacing=32,
        controls=[
            ft.Text("Calendar", size=18, weight=ft.FontWeight.W_600),
            ft.Container(width=720, content=plain.ui()),
            ft.Text(
                "cell_content · 每天一个小圆点",
                size=FONT_SIZE["small"],
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
            ft.Container(width=720, content=marked.ui()),
            ft.Text(
                "mode='year'",
                size=FONT_SIZE["small"],
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
            ft.Container(width=720, content=year.ui()),
        ],
    )
