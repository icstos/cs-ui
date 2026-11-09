"""月历视图 (CalendarPanel)：``DateInput`` / ``DateTimeInput`` 共用的日历渲染层。

一张面板由三部分组成 —— 页头（翻页 + 标题）、视图主体、页脚 —— 主体有三种单位：

=========  ====================================  ====================
``_mode``   画什么                                标题 / 单次翻页
=========  ====================================  ====================
``day``     6 × 7 日期网格                        年月 / 一个月
``month``   4 × 3 月网格（一屏一年）               年份 / 一年
``year``    4 × 3 年网格（一屏 12 年）             年份区间 / 12 年
=========  ====================================  ====================

面板可以并排放 **两列**（``_cal_view_count() == 2``），用于日期范围 / 月份范围：
两列各有独立的年月与页头，翻页时整体平移，保证"左早右晚"始终相邻。

**视觉状态全部由 :class:`DayMark` 表达** —— 选中（实心圆）、区间连条（浅色带，
两端圆角）、今天、禁用、非本月。单值 / 多值 / 区间 / 整周四套语义因此共用同一套
格子渲染，不各画一遍；宿主只需要回答"这一格现在是什么状态"。

宿主须提供以下字段 / 方法（本混入只读不写）：

- ``notify()`` / ``_hover`` / ``_hover_day``：``@ft.observable`` 提供 + 本层维护；
- ``_views: list[tuple[int, int]]``：每列正在显示的年月，**由宿主在
  ``__post_init__`` 里初始化**（长度 = :meth:`_cal_view_count`）；
- ``_mode``：``"day"`` / ``"month"`` / ``"year"``。

.. note::
    ``FIELD_*`` / ``PANEL_*`` / ``*_SIZE`` / ``HOVER_BG`` / ``DISABLED_FG`` /
    ``place_panel`` / ``_truthy`` 这些名字**仍从本模块重导出**（历史上它们定义
    在这里，``date_input`` / ``datetime_input`` 以及仓库外的代码都按老路径导入）。
    新代码请直接从 :mod:`ui.input.panel_field` 导入。
"""

from __future__ import annotations

import datetime
from typing import NamedTuple

import flet as ft

from ui.core.format import calendar_title, first_weekday, month_cell, weekday_names
from ui.core.i18n import t
from ui.core.tokens import accent_soft

# 通用外壳（尺寸 / 配色 / 定位 / 混入）全部来自 panel_field。
# 这里原样重导出，保持 `from ui.input.calendar_panel import PANEL_PAD` 这类
# 历史导入路径可用。
from ui.input.panel_field import (  # noqa: F401
    DISABLED_FG,
    FIELD_HEIGHT,
    FIELD_PAD_H,
    FIELD_RADIUS,
    FIELD_WIDTH,
    HOVER_BG,
    LABEL_SIZE,
    NAV_RADIUS,
    NAV_SIZE,
    PANEL_GAP,
    PANEL_PAD,
    SCREEN_MARGIN,
    SMALL_SIZE,
    TEXT_SIZE,
    PanelField,
    _truthy,
    panel_shell,
    place_panel,
)

__all__ = ["CalendarPanel", "DayMark", "WEEKDAYS", "place_panel", "panel_shell"]

# ---------------------------------------------------------------------------
# 尺寸（月历独有）
# ---------------------------------------------------------------------------
CELL_W = 34  # 日期格宽
CELL_H = 32  # 日期格高
GRID_ROWS = 6  # 月历固定 6 行（容纳跨月的 42 天）
GRID_COLS = 7
HEADER_H = 38  # 面板页头（翻页 + 标题）
WEEKDAY_H = 26  # 星期行
FOOTER_H = 34  # 面板页脚
UNIT_COLS = 3  # 月 / 年网格列数
UNIT_ROWS = 4  # 月 / 年网格行数
UNIT_H = 54  # 月 / 年网格单格高（4 × 54 ≈ 月历的 218）
UNIT_GAP = 12  # 双面板之间的间距
DOT = 26  # 选中圆直径（比格子小一圈，留出连条的"呼吸"）
CELL_RADIUS = 6  # 日期格连条端头的圆角
BAND_H = 34  # 月 / 年格的连条高度（比格子矮一圈，行与行之间才断得开）
UNIT_RADIUS = 15  # 月 / 年格连条端头圆角（≈半高，收成胶囊）

CAL_GRID_W = CELL_W * GRID_COLS  # 月历栅格宽 238
CAL_GRID_H = WEEKDAY_H + CELL_H * GRID_ROWS  # 月历栅格高 218
CAL_W = PANEL_PAD * 2 + CAL_GRID_W + 2  # 只放一列时面板的宽（含 1px 边框 ×2）
RANGE_W = PANEL_PAD * 2 + CAL_GRID_W * 2 + UNIT_GAP + 2  # 两列并排时的面板宽
PANEL_H = PANEL_PAD * 2 + 2 + HEADER_H + CAL_GRID_H + 1 + FOOTER_H  # 面板高

# ---------------------------------------------------------------------------
# 配色（月历独有；通用的 HOVER_BG / DISABLED_FG 在 panel_field）
# ---------------------------------------------------------------------------
TODAY_BG = accent_soft("primary")  # "今天"淡色底（12% 主色，与其它选中态同档）
SELECTED_BG = ft.Colors.PRIMARY  # 选中填色
BAND_BG = accent_soft("primary")  # 区间 / 整周连条

#: 星期标签的**中文字形兜底**，索引与 ``datetime.date.weekday()`` 一致：
#: 0 = 周一 … 6 = 周日。真正的标签来自语言包（``ui.calendar.weekdays``），
#: 这个常量只在语言包异常时兜底，并供老代码按原路径导入。
WEEKDAYS = ("一", "二", "三", "四", "五", "六", "日")


# ---------------------------------------------------------------------------
# 纯函数工具
# ---------------------------------------------------------------------------
def _is_leap_year(year: int) -> bool:
    """判断是否为闰年。"""
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


def _get_days_in_month(year: int, month: int) -> int:
    """根据年月获取该月天数，自动处理闰年二月。"""
    if month == 2:
        return 29 if _is_leap_year(year) else 28
    if month in (4, 6, 9, 11):
        return 30
    return 31


def _norm_ym(year: int, month: int) -> tuple[int, int]:
    """把任意月偏移归一到 ``(年, 1..12)``。"""
    year += (month - 1) // 12
    return year, (month - 1) % 12 + 1


def year_page(year: int) -> int:
    """年网格的起始年（一屏 12 年）。"""
    return year - year % 12


class DayMark(NamedTuple):
    """一个格子的视觉状态（日期 / 月 / 年三种网格共用）。

    Attributes:
        selected: 画实心圆（选中项）。
        band: 画浅色连条（区间中间段、整周）。
        round_left: 连条在左边收圆角（区间起点，或本行首格）。
        round_right: 连条在右边收圆角（区间终点，或本行末格）。
    """

    selected: bool = False
    band: bool = False
    round_left: bool = False
    round_right: bool = False


_EMPTY = DayMark()


class CalendarPanel(PanelField):
    """月历 / 月网格 / 年网格三种视图的渲染层。见模块 docstring 的宿主契约。"""

    # ---- 宿主契约（由宿主类提供；这里列出便于对照） ----
    #   _views / _mode / _hover / _hover_day / notify()

    # ------------------------------------------------------------------
    # 钩子：宿主覆写
    # ------------------------------------------------------------------
    def _cal_view_count(self) -> int:
        """面板要并排渲染几列：单值 / 多值 1 列，区间 2 列。"""
        return 1

    def _cal_bounds(self) -> tuple[datetime.date, datetime.date]:
        """可选日期范围（含端点）。宿主必须覆写，否则一切皆可选。"""
        return datetime.date.min, datetime.date.max

    def _cal_is_selected(self, day: datetime.date) -> bool:
        """``day`` 是否为"已选中"（默认单值语义）。"""
        return getattr(self, "value", None) == day

    def _cal_marks(self, day: datetime.date) -> DayMark:
        """日期格的视觉状态。默认："值等于这一天就画实心圆"。"""
        return DayMark(selected=self._cal_is_selected(day))

    def _cal_month_marks(self, year: int, month: int) -> DayMark:
        """月网格单格的视觉状态。默认："值落在该年月就画实心圆"。"""
        value = getattr(self, "value", None)
        same = value is not None and (value.year, value.month) == (year, month)
        return DayMark(selected=same)

    def _cal_year_marks(self, year: int) -> DayMark:
        """年网格单格的视觉状态。默认："值落在该年就画实心圆"。"""
        value = getattr(self, "value", None)
        return DayMark(selected=value is not None and value.year == year)

    def _cal_pick(self, day: datetime.date) -> None:
        """用户点了某一天。宿主决定"选完收起"还是"只改日期部分"。"""
        raise NotImplementedError

    def _cal_pick_month(self, year: int, month: int, idx: int = 0) -> None:
        """用户点了某个月（``idx`` 是双面板时的列号）。"""
        raise NotImplementedError

    def _cal_pick_year(self, year: int, idx: int = 0) -> None:
        """用户点了某个年。"""
        raise NotImplementedError

    def _cal_picks_month(self) -> bool:
        """月网格是"选值"（True）还是"只当跳板"（False）。

        日期选择器里点月只是回到月历，月份选择器里点月才是选值 —— 同一个
        网格两种语义，靠这一个钩子区分，渲染层不必知道是哪个组件。
        """
        return False

    def _cal_picks_year(self) -> bool:
        """年网格是"选值"还是"只当跳板"。"""
        return False

    # ------------------------------------------------------------------
    # 视图状态
    # ------------------------------------------------------------------
    @property
    def _cal_view(self) -> tuple[int, int]:
        """第 0 列正在显示的年月（单面板组件最常用的一对）。"""
        return self._views[0]

    @property
    def _view_year(self) -> int:
        return self._views[0][0]

    @_view_year.setter
    def _view_year(self, value: int) -> None:
        self._patch_view(0, year=int(value))

    @property
    def _view_month(self) -> int:
        return self._views[0][1]

    @_view_month.setter
    def _view_month(self, value: int) -> None:
        self._patch_view(0, month=int(value))

    def _cal_views(self) -> list[tuple[int, int]]:
        """当前要渲染的 ``(年, 月)`` 列表（长度 = 列数）。"""
        count = self._cal_view_count()
        views = list(self._views)
        while len(views) < count:
            views.append(views[-1] if views else (datetime.date.today().year, 1))
        return views[:count]

    def _patch_view(self, idx: int, *, year: int | None = None, month: int | None = None) -> None:
        """只改第 ``idx`` 列的年 / 月（保持另一维与相邻列的偏移）。"""
        views = list(self._cal_views())
        while len(views) <= idx:
            views.append(views[-1])
        y, m = views[idx]
        views[idx] = _norm_ym(year if year is not None else y, month if month is not None else m)
        self._views = views

    def _set_views(self, views: list[tuple[int, int]]) -> None:
        """整体替换（正常情况下长度 = 列数）。"""
        count = self._cal_view_count()
        out = [_norm_ym(y, m) for y, m in views]
        while len(out) < count:
            out.append(out[-1] if out else (datetime.date.today().year, 1))
        self._views = out[:count]
        self._hover = None  # type: ignore[attr-defined]
        self._hover_day = None  # type: ignore[attr-defined]
        self.notify()  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # 翻页 / 缩放
    # ------------------------------------------------------------------
    def _cal_shift(self, delta: int) -> None:
        """整体前 / 后翻 N 个单位（单位由当前视图决定）。"""
        if self._mode == "year":  # type: ignore[attr-defined]
            self._cal_shift_year(12 * delta)
        elif self._mode == "month":  # type: ignore[attr-defined]
            self._cal_shift_year(delta)
        else:
            self._cal_shift_month(delta)

    def _cal_shift_month(self, delta: int) -> None:
        """整体前后平移 N 个月（自动跨年；两列一起动，保持相邻）。"""
        self._set_views([(y, m + delta) for y, m in self._cal_views()])

    def _cal_shift_year(self, delta: int) -> None:
        """整体前后平移 N 年。"""
        self._set_views([(y + delta, m) for y, m in self._cal_views()])

    def _cal_zoom_out(self) -> None:
        """粒度放大一级：日 → 月 → 年（年已经是顶层，不再动）。"""
        if self._mode == "year":  # type: ignore[attr-defined]
            return
        self._mode = "year" if self._mode == "month" else "month"  # type: ignore[attr-defined]
        self._hover = None  # type: ignore[attr-defined]
        self.notify()  # type: ignore[attr-defined]

    #: 老名字（只在"日 ⇄ 月"两级时才有意义），保留给既有调用方。
    _cal_toggle_mode = _cal_zoom_out

    def _cal_select_month(self, month: int) -> None:
        """在月网格里选中某月，回到日视图（日期选择器的"跳转"，不选值）。"""
        self._mode = "day"  # type: ignore[attr-defined]
        views = self._cal_views()
        self._set_views([(views[0][0], month)] + views[1:])

    def _cal_select_year(self, year: int) -> None:
        """在年网格里选中某年，落到月网格。"""
        self._mode = "month"  # type: ignore[attr-defined]
        views = self._cal_views()
        self._set_views([(year, views[0][1])] + views[1:])

    # ------------------------------------------------------------------
    # 面板页头
    # ------------------------------------------------------------------
    def _cal_header(self, idx: int = 0) -> ft.Control:
        """页头：翻页箭头 + 可点的标题（点它放大粒度）。

        标题与翻页提示都取自语言包：中文是「2026 年 9 月 / 上一月」，英文是
        「September 2026 / Previous month」—— 不是把中文标题翻译一遍就算完，
        英文的语序本来就是"月在前"。
        """
        year, month = self._cal_views()[idx]
        mode = self._mode  # type: ignore[attr-defined]
        if mode == "year":
            start = year_page(year)
            title = t("ui.calendar.title_years", a=start, b=start + 11)
            prev_tip, next_tip = t("ui.calendar.prev_year"), t("ui.calendar.next_year")
        elif mode == "month":
            title = calendar_title(year, month, mode="year")
            prev_tip, next_tip = t("ui.calendar.prev_year"), t("ui.calendar.next_year")
        else:
            title = calendar_title(year, month)
            prev_tip, next_tip = t("ui.calendar.prev_month"), t("ui.calendar.next_month")

        return ft.Container(
            height=HEADER_H,
            content=ft.Row(
                spacing=0,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    self._nav_button(
                        f"prev{idx}", ft.Icons.CHEVRON_LEFT,
                        lambda d=-1: self._cal_shift(d), prev_tip,
                    ),
                    ft.Container(
                        expand=True,
                        alignment=ft.Alignment.CENTER,
                        content=self._cal_title(title, idx, zoomable=mode != "year"),
                    ),
                    self._nav_button(
                        f"next{idx}", ft.Icons.CHEVRON_RIGHT,
                        lambda d=1: self._cal_shift(d), next_tip,
                    ),
                ],
            ),
        )

    def _cal_title(self, text: str, idx: int, *, zoomable: bool) -> ft.Control:
        """可点的标题。年视图到顶了，就没有下拉箭头、也不响应点击。"""
        icon: ft.Control | None = (
            ft.Icon(
                ft.Icons.ARROW_DROP_UP if self._mode == "year" else ft.Icons.ARROW_DROP_DOWN,  # type: ignore[attr-defined]
                size=16,
                color=ft.Colors.OUTLINE,
            )
            if zoomable
            else None
        )
        row = ft.Row(
            tight=True,
            spacing=2,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(
                    text, size=TEXT_SIZE, weight=ft.FontWeight.W_600,
                    color=ft.Colors.ON_SURFACE,
                ),
                *([icon] if icon is not None else []),
            ],
        )
        if not zoomable:
            return row
        key = f"title{idx}"
        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
            border_radius=ft.BorderRadius.all(NAV_RADIUS),
            bgcolor=HOVER_BG if self._hover == key else None,  # type: ignore[attr-defined]
            on_click=lambda _e: self._cal_zoom_out(),
            on_hover=lambda e, k=key: self._hover_key(k, _truthy(e.data)),
            content=row,
        )

    # ------------------------------------------------------------------
    # 视图主体
    # ------------------------------------------------------------------
    def _cal_column(self, idx: int = 0) -> ft.Control:
        """一列 = 页头 + 主体。宽度锁定，双面板并排时两列严格等宽。"""
        return ft.Container(
            width=CAL_GRID_W,
            content=ft.Column(
                spacing=0, horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                controls=[self._cal_header(idx), self._cal_body(idx)],
            ),
        )

    def _cal_panel(self) -> ft.Control:
        """面板主体：单列原样返回，双列并排（中间留 :data:`UNIT_GAP`）。"""
        cols = [self._cal_column(i) for i in range(self._cal_view_count())]
        if len(cols) == 1:
            return cols[0]
        return ft.Row(
            spacing=UNIT_GAP,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=cols,
        )

    def _cal_body(self, idx: int = 0) -> ft.Control:
        """主体：按当前粒度画日网格 / 月网格 / 年网格；高度恒为 ``CAL_GRID_H``。"""
        if self._mode == "year":  # type: ignore[attr-defined]
            return self._cal_years(idx)
        if self._mode == "month":  # type: ignore[attr-defined]
            return self._cal_months(idx)
        return ft.Column(
            spacing=0,
            controls=[self._cal_weekdays(), self._cal_days(idx)],
        )

    # ---- 日视图 ----

    def _cal_first_day(self) -> int:
        """每周首日：宿主显式给就用宿主的，``None`` 表示跟随界面语言。

        中文习惯周一起、英文习惯周日起 —— 这是"日历看起来像本地软件"的关键
        细节之一，所以做成语言驱动的默认值而不是写死。
        """
        value = getattr(self, "first_day_weekday", None)
        return first_weekday() if value is None else int(value) % 7

    def _cal_weekday_sequence(self) -> list[str]:
        """按首日旋转后的星期标签（长度恒为 7）。

        ``WEEKDAYS[i]`` 对应 ``weekday() == i``；首列要放首日，
        所以序列从该下标开始绕一圈。
        """
        source = getattr(self, "weekday_labels", None) or weekday_names() or WEEKDAYS
        labels = [str(x) for x in source][:7]
        while len(labels) < 7:  # 语言包给短了就补，宁可重复也不让表头错位
            labels.append(WEEKDAYS[len(labels)])
        offset = self._cal_first_day()
        return labels[offset:] + labels[:offset]

    def _cal_weekdays(self) -> ft.Control:
        """星期表头。"""
        return ft.Container(
            height=WEEKDAY_H,
            content=ft.Row(
                spacing=0,
                controls=[
                    ft.Container(
                        width=CELL_W,
                        alignment=ft.Alignment.CENTER,
                        content=ft.Text(
                            label, size=LABEL_SIZE, color=ft.Colors.ON_SURFACE_VARIANT
                        ),
                    )
                    for label in self._cal_weekday_sequence()
                ],
            ),
        )

    def _cal_grid_start(self, idx: int = 0) -> datetime.date:
        """网格第一格对应的日期（可能落在上月）。"""
        year, month = self._cal_views()[idx]
        first = datetime.date(year, month, 1)
        offset = (first.weekday() - self._cal_first_day()) % 7
        return first - datetime.timedelta(days=offset)

    def _cal_days(self, idx: int = 0) -> ft.Control:
        """6 × 7 日期网格，固定 6 行 —— 面板高度不随月份跳动。"""
        start = self._cal_grid_start(idx)
        rows: list[ft.Control] = []
        for r in range(GRID_ROWS):
            rows.append(
                ft.Row(
                    spacing=0,
                    controls=[
                        self._cal_day_cell(start + datetime.timedelta(days=r * 7 + c), c)
                        for c in range(GRID_COLS)
                    ],
                )
            )
        return ft.Container(
            height=CELL_H * GRID_ROWS,
            content=ft.Column(spacing=0, controls=rows),
        )

    def _cal_day_cell(self, day: datetime.date, col: int = 0) -> ft.Control:
        """单个日期格：实心圆选中、区间连条、今天淡色、越界灰字禁用。"""
        enabled = self._cal_day_enabled(day)
        mark = self._cal_marks(day) if enabled else _EMPTY
        in_month = (day.year, day.month) == self._cal_views()[0]
        is_today = day == datetime.date.today()
        hovered = enabled and getattr(self, "_hover_day", None) == day

        if mark.selected:
            color: ft.ColorValue = ft.Colors.ON_PRIMARY
        elif not enabled:
            color = DISABLED_FG
        elif is_today:
            color = ft.Colors.PRIMARY
        elif in_month:
            color = ft.Colors.ON_SURFACE
        else:
            color = ft.Colors.OUTLINE

        text = ft.Text(
            str(day.day),
            size=TEXT_SIZE,
            color=color,
            weight=ft.FontWeight.W_600
            if enabled and (mark.selected or is_today)
            else ft.FontWeight.NORMAL,
        )
        # 圆点单独一层：连条填满整格，圆点浮在上面 —— 只有一个控件、没有 Stack。
        dot_bg: ft.ColorValue | None = None
        if mark.selected:
            dot_bg = SELECTED_BG
        elif hovered:
            dot_bg = HOVER_BG
        content: ft.Control = text
        if dot_bg is not None:
            content = ft.Container(
                width=DOT,
                height=DOT,
                border_radius=ft.BorderRadius.all(DOT / 2),
                bgcolor=dot_bg,
                alignment=ft.Alignment.CENTER,
                content=text,
            )

        return ft.Container(
            width=CELL_W,
            height=CELL_H,
            alignment=ft.Alignment.CENTER,
            border_radius=self._band_radius(mark, col),
            bgcolor=BAND_BG if mark.band else None,
            on_click=None if not enabled else (lambda _e, d=day: self._cal_pick(d)),
            on_hover=None if not enabled else (lambda e, d=day: self._cal_hover(d, e)),
            content=content,
        )

    @staticmethod
    def _band_radius(
        mark: DayMark, col: int, radius: float = CELL_RADIUS, cols: int = GRID_COLS
    ) -> ft.BorderRadius | None:
        """连条的端头圆角：区间端点或行首 / 行末收圆，中间段保持方角拼接。"""
        if not mark.band:
            return None
        left = mark.round_left or col == 0
        right = mark.round_right or col == cols - 1
        return ft.BorderRadius.only(
            top_left=radius if left else 0,
            bottom_left=radius if left else 0,
            top_right=radius if right else 0,
            bottom_right=radius if right else 0,
        )

    def _cal_hover(self, day: datetime.date, e: ft.Event) -> None:
        """悬停：既用于常规高亮，也用于区间"拖到尾"的预览。"""
        entering = _truthy(e.data)
        current = getattr(self, "_hover_day", None)
        if entering:
            if current == day:
                return
            self._hover_day = day  # type: ignore[attr-defined]
        else:
            if current != day:
                return
            self._hover_day = None  # type: ignore[attr-defined]
        self._hover = day.isoformat()  # type: ignore[attr-defined]
        self.notify()  # type: ignore[attr-defined]

    def _cal_day_enabled(self, day: datetime.date) -> bool:
        """``day`` 是否可选。"""
        lo, hi = self._cal_bounds()
        return lo <= day <= hi

    # ---- 月 / 年网格 ----

    def _cal_months(self, idx: int = 0) -> ft.Control:
        """4 × 3 月网格，高度与月历区一致（面板不跳动）。"""
        year = self._cal_views()[idx][0]
        rows = [
            ft.Row(
                spacing=0,
                height=UNIT_H,
                controls=[
                    self._cal_month_cell(year, r * UNIT_COLS + c + 1, c)
                    for c in range(UNIT_COLS)
                ],
            )
            for r in range(UNIT_ROWS)
        ]
        return ft.Container(
            height=CAL_GRID_H,
            padding=ft.Padding.symmetric(vertical=(CAL_GRID_H - UNIT_H * UNIT_ROWS) // 2),
            content=ft.Column(spacing=0, controls=rows),
        )

    def _unit_cell(
        self,
        text: str,
        mark: DayMark,
        col: int,
        *,
        enabled: bool,
        hovered: bool,
        on_click,
        on_hover,
        pill_w: float,
    ) -> ft.Control:
        """月 / 年网格共用的格子。

        连条画在**内侧一条矮带**上而不是整格：整格高 54，行与行之间没有缝，
        铺成整格会糊成一整块色斑；收成 34 高的胶囊带，每行才读得出是"一段"。
        """
        color: ft.ColorValue = (
            ft.Colors.ON_PRIMARY if mark.selected
            else DISABLED_FG if not enabled
            else ft.Colors.ON_SURFACE
        )
        label = ft.Text(
            text,
            size=TEXT_SIZE,
            color=color,
            weight=ft.FontWeight.W_600 if mark.selected else ft.FontWeight.NORMAL,
        )
        pill_bg: ft.ColorValue | None = (
            SELECTED_BG if mark.selected
            else (HOVER_BG if hovered and not mark.band else None)
        )
        content = label
        if pill_bg is not None:
            content = ft.Container(
                height=28,
                width=pill_w,
                border_radius=ft.BorderRadius.all(14),
                bgcolor=pill_bg,
                alignment=ft.Alignment.CENTER,
                content=label,
            )
        # 内层永远是"一条居中横带"：有连条时 34 高（行与行断得开），没有时铺满
        # 整格。统一结构的好处是文字基线每格都一样，不会"有连条的行居中、
        # 没连条的行贴顶"。
        inner = ft.Container(
            expand=True,
            height=BAND_H if mark.band else UNIT_H,
            bgcolor=BAND_BG if mark.band else None,
            border_radius=self._band_radius(
                mark, col, radius=UNIT_RADIUS, cols=UNIT_COLS
            ),
            alignment=ft.Alignment.CENTER,
            content=content,
        )
        return ft.Container(
            height=UNIT_H,
            expand=True,
            on_click=None if not enabled else on_click,
            on_hover=None if not enabled else on_hover,
            content=ft.Row(
                spacing=0,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[inner],
            ),
        )



    def _cal_month_cell(self, year: int, month: int, col: int = 0) -> ft.Control:
        """月网格里的单个月。"""
        key = f"m{year}-{month}"
        enabled = self._cal_month_enabled(month, year)
        mark = self._cal_month_marks(year, month) if enabled else _EMPTY
        return self._unit_cell(
            month_cell(month),
            mark,
            col,
            enabled=enabled,
            hovered=self._hover == key,  # type: ignore[attr-defined]
            on_click=lambda _e, y=year, m=month: self._cal_month_clicked(y, m),
            on_hover=lambda e, k=key: self._hover_key(k, _truthy(e.data)),
            pill_w=56,
        )

    def _cal_month_clicked(self, year: int, month: int, idx: int = 0) -> None:
        """点月：选值的宿主直接选，否则只当作"跳回日视图"的跳板。"""
        if self._cal_picks_month():
            self._cal_pick_month(year, month, idx)
        else:
            self._cal_select_month(month)

    def _cal_years(self, idx: int = 0) -> ft.Control:
        """4 × 3 年网格，一屏 12 年。"""
        start = year_page(self._cal_views()[idx][0])
        rows = [
            ft.Row(
                spacing=0,
                height=UNIT_H,
                controls=[
                    self._cal_year_cell(start + r * UNIT_COLS + c, c)
                    for c in range(UNIT_COLS)
                ],
            )
            for r in range(UNIT_ROWS)
        ]
        return ft.Container(
            height=CAL_GRID_H,
            padding=ft.Padding.symmetric(vertical=(CAL_GRID_H - UNIT_H * UNIT_ROWS) // 2),
            content=ft.Column(spacing=0, controls=rows),
        )

    def _cal_year_cell(self, year: int, col: int = 0) -> ft.Control:
        """年网格里的单个年份。"""
        key = f"y{year}"
        enabled = self._cal_year_enabled(year)
        mark = self._cal_year_marks(year) if enabled else _EMPTY
        return self._unit_cell(
            calendar_title(year, 1, mode="year"),
            mark,
            col,
            enabled=enabled,
            hovered=self._hover == key,  # type: ignore[attr-defined]
            on_click=lambda _e, y=year: self._cal_year_clicked(y),
            on_hover=lambda e, k=key: self._hover_key(k, _truthy(e.data)),
            pill_w=72,
        )

    def _cal_year_clicked(self, year: int, idx: int = 0) -> None:
        """点年：选值的宿主直接选，否则落到该年的月网格。"""
        if self._cal_picks_year():
            self._cal_pick_year(year, idx)
        else:
            self._cal_select_year(year)

    def _cal_month_enabled(self, month: int, year: int | None = None) -> bool:
        """该月的任意一天在可选范围内即可选。"""
        year = self._cal_views()[0][0] if year is None else year
        lo, hi = self._cal_bounds()
        first = datetime.date(year, month, 1)
        last = datetime.date(year, month, _get_days_in_month(year, month))
        return last >= lo and first <= hi

    def _cal_year_enabled(self, year: int) -> bool:
        """该年的任意一天在可选范围内即可选。"""
        lo, hi = self._cal_bounds()
        return datetime.date(year, 12, 31) >= lo and datetime.date(year, 1, 1) <= hi
