"""月历视图混入 (CalendarPanel)：``DateInput`` / ``DateTimeInput`` 共用的日历。

抽这一层的理由很直接：日期选择器和日期时间选择器用的是**同一张月历** ——
头部翻页、星期表头、6 × 7 日期网格、年月网格、悬停 / 选中 / 禁用配色，逐像素一致。
差异只有四处，宿主类覆写对应的"钩子"即可：

======================  ==========================  ==============================
钩子                     ``DateInput``               ``DateTimeInput``
======================  ==========================  ==============================
``_cal_bounds()``        ``min_date`` .. ``max_date``  ``min_datetime`` .. ``max_datetime``
``_cal_is_selected(d)``  ``d == value``               ``d == value.date()``
``_cal_day_enabled(d)``  默认（按 ``_cal_bounds``）  默认
``_cal_pick(d)``         选中并收起                  只改日期部分，面板保持展开
======================  ==========================  ==============================

宿主须提供以下字段 / 方法（本混入只读不写）：

- ``_view_year`` / ``_view_month``：面板正在显示的年月；
- ``_mode``：``"day"`` 月历 / ``"month"`` 年月网格；
- ``first_day_weekday`` / ``weekday_labels``：星期排布（见 :data:`WEEKDAYS`）。

折叠态输入框、面板外壳、浮层定位这些**与月历无关**的部分已经上移到
:class:`~ui.input.panel_field.PanelField`（``DateInput`` / ``DateTimeInput`` /
``ColorPicker`` 三家共用），本类只保留月历本身的渲染。

.. note::
    ``FIELD_*`` / ``PANEL_*`` / ``*_SIZE`` / ``HOVER_BG`` / ``DISABLED_FG`` /
    ``place_panel`` / ``_truthy`` 这些名字**仍从本模块重导出**（历史上它们定义
    在这里，``date_input`` / ``datetime_input`` 以及仓库外的代码都按老路径导入）。
    新代码请直接从 :mod:`ui.input.panel_field` 导入。
"""

from __future__ import annotations

import datetime

import flet as ft

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

__all__ = ["CalendarPanel", "WEEKDAYS", "place_panel", "panel_shell"]

# ---------------------------------------------------------------------------
# 尺寸（月历独有）
# ---------------------------------------------------------------------------
CELL_W = 34  # 日期格宽
CELL_H = 32  # 日期格高
GRID_ROWS = 6  # 月历固定 6 行（容纳跨月的 42 天）
HEADER_H = 38  # 面板头部（翻页 + 年月标题）
WEEKDAY_H = 26  # 星期行
FOOTER_H = 34  # 面板页脚
MONTH_H = 48  # 年月网格的单格高（4 × 48 = 192 = 6 × CELL_H）
CELL_RADIUS = 6  # 日期格圆角

CAL_GRID_W = CELL_W * 7  # 月历栅格宽
CAL_GRID_H = WEEKDAY_H + CELL_H * GRID_ROWS  # 月历栅格高（星期行 + 6 行日期）
CAL_W = PANEL_PAD * 2 + CAL_GRID_W + 2  # 只放月历时面板的宽（含 1px 边框 ×2）
PANEL_H = PANEL_PAD * 2 + 2 + HEADER_H + CAL_GRID_H + 1 + FOOTER_H  # 面板高

# ---------------------------------------------------------------------------
# 配色（月历独有；通用的 HOVER_BG / DISABLED_FG 在 panel_field）
# ---------------------------------------------------------------------------
TODAY_BG = ft.Colors.with_opacity(0.10, ft.Colors.PRIMARY)  # "今天"淡色底
SELECTED_BG = ft.Colors.PRIMARY  # 选中填色

#: 星期标签，索引与 ``datetime.date.weekday()`` 一致：0 = 周一 … 6 = 周日。
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


class CalendarPanel(PanelField):
    """月历视图混入。见模块 docstring 的钩子表。"""

    # ---- 宿主契约（由宿主类提供；这里列出便于对照） ----
    #   _view_year / _view_month / _mode / first_day_weekday / weekday_labels
    #   （其余 contract 见 PanelField）

    # ------------------------------------------------------------------
    # 钩子：宿主覆写
    # ------------------------------------------------------------------
    def _cal_bounds(self) -> tuple[datetime.date, datetime.date]:
        """可选日期范围（含端点）。宿主必须覆写，否则一切皆可选。"""
        return datetime.date.min, datetime.date.max

    def _cal_is_selected(self, day: datetime.date) -> bool:
        """``day`` 是否为"已选中"（决定填色高亮）。"""
        return getattr(self, "value", None) == day

    def _cal_is_month_selected(self, month: int) -> bool:
        """年月网格里该月是否命中当前值（``date`` / ``datetime`` 都可用）。"""
        value = getattr(self, "value", None)
        if value is None:
            return False
        return value.year == self._view_year and value.month == month

    def _cal_day_enabled(self, day: datetime.date) -> bool:
        """``day`` 是否可选。"""
        lo, hi = self._cal_bounds()
        return lo <= day <= hi

    def _cal_pick(self, day: datetime.date) -> None:
        """用户点了某一天。宿主决定"选完收起"还是"只改日期部分"。"""
        raise NotImplementedError

    # ------------------------------------------------------------------
    # 状态迁移
    # ------------------------------------------------------------------
    def _cal_shift_month(self, delta: int) -> None:
        """面板月份 ±N（自动跨年）。"""
        y, m = self._view_year, self._view_month + delta
        y += (m - 1) // 12
        self._view_year, self._view_month = y, (m - 1) % 12 + 1
        self._hover = None
        self.notify()  # type: ignore[attr-defined]

    def _cal_shift_year(self, delta: int) -> None:
        """面板年份 ±N（年月网格视图用）。"""
        self._view_year += delta
        self._hover = None
        self.notify()  # type: ignore[attr-defined]

    def _cal_toggle_mode(self) -> None:
        """月历 ⇄ 年月网格。"""
        self._mode = "month" if self._mode == "day" else "day"
        self._hover = None
        self.notify()  # type: ignore[attr-defined]

    def _cal_select_month(self, month: int) -> None:
        """在年月网格里选中某月，回到月历。"""
        self._view_month = month
        self._mode = "day"
        self._hover = None
        self.notify()  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # 面板头部
    # ------------------------------------------------------------------
    def _cal_header(self) -> ft.Control:
        """面板头部：翻页箭头 + 可点击的年月标题（点它切年月网格）。"""
        if self._mode == "month":
            title: str = f"{self._view_year} 年"
            unit = "年"
            prev = lambda: self._cal_shift_year(-1)  # noqa: E731
            nxt = lambda: self._cal_shift_year(1)  # noqa: E731
        else:
            title = f"{self._view_year} 年 {self._view_month} 月"
            unit = "月"
            prev = lambda: self._cal_shift_month(-1)  # noqa: E731
            nxt = lambda: self._cal_shift_month(1)  # noqa: E731

        title_btn = ft.Container(
            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
            border_radius=ft.BorderRadius.all(NAV_RADIUS),
            bgcolor=HOVER_BG if self._hover == "title" else None,
            on_click=lambda _e: self._cal_toggle_mode(),
            on_hover=lambda e: self._hover_key("title", _truthy(e.data)),
            content=ft.Row(
                tight=True,
                spacing=2,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text(
                        title,
                        size=TEXT_SIZE,
                        weight=ft.FontWeight.W_600,
                        color=ft.Colors.ON_SURFACE,
                    ),
                    ft.Icon(
                        ft.Icons.ARROW_DROP_UP
                        if self._mode == "month"
                        else ft.Icons.ARROW_DROP_DOWN,
                        size=16,
                        color=ft.Colors.OUTLINE,
                    ),
                ],
            ),
        )

        return ft.Container(
            height=HEADER_H,
            content=ft.Row(
                spacing=0,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    self._nav_button("prev", ft.Icons.CHEVRON_LEFT, prev, f"上一{unit}"),
                    ft.Container(
                        expand=True, alignment=ft.Alignment.CENTER, content=title_btn
                    ),
                    self._nav_button("next", ft.Icons.CHEVRON_RIGHT, nxt, f"下一{unit}"),
                ],
            ),
        )

    # ------------------------------------------------------------------
    # 月历
    # ------------------------------------------------------------------
    def _cal_body(self) -> ft.Control:
        """月历主体；年月网格视图下换成 4 × 3。"""
        if self._mode == "month":
            return self._cal_months()
        return ft.Column(
            spacing=0, controls=[self._cal_weekdays(), self._cal_days()]
        )

    def _cal_weekday_sequence(self) -> list[str]:
        """按 ``first_day_weekday`` 旋转后的星期标签（长度恒为 7）。

        ``WEEKDAYS[i]`` 对应 ``weekday() == i``；首列要放 ``first_day_weekday``，
        所以序列从该下标开始绕一圈。
        """
        labels = [str(x) for x in self.weekday_labels][:7] or list(WEEKDAYS)
        offset = int(self.first_day_weekday) % 7
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

    def _cal_grid_start(self) -> datetime.date:
        """网格第一格对应的日期（可能落在上月）。"""
        first = datetime.date(self._view_year, self._view_month, 1)
        offset = (first.weekday() - int(self.first_day_weekday)) % 7
        return first - datetime.timedelta(days=offset)

    def _cal_days(self) -> ft.Control:
        """6 × 7 日期网格，固定 6 行 —— 面板高度不随月份跳动。"""
        start = self._cal_grid_start()
        rows: list[ft.Control] = []
        for r in range(GRID_ROWS):
            rows.append(
                ft.Row(
                    spacing=0,
                    controls=[
                        self._cal_day_cell(start + datetime.timedelta(days=r * 7 + c))
                        for c in range(7)
                    ],
                )
            )
        return ft.Container(
            height=CELL_H * GRID_ROWS,
            content=ft.Column(spacing=0, controls=rows),
        )

    def _cal_day_cell(self, day: datetime.date) -> ft.Control:
        """单个日期格：选中填主色、"今天"淡色底、越界灰字禁用。"""
        key = day.isoformat()
        in_month = (day.year, day.month) == (self._view_year, self._view_month)
        enabled = self._cal_day_enabled(day)
        selected = enabled and self._cal_is_selected(day)
        is_today = day == datetime.date.today()
        hovered = enabled and self._hover == key

        bgcolor: ft.ColorValue | None
        color: ft.ColorValue
        if selected:
            bgcolor, color = SELECTED_BG, ft.Colors.ON_PRIMARY
        elif not enabled:
            bgcolor, color = None, DISABLED_FG
        elif hovered:
            bgcolor = HOVER_BG
            color = ft.Colors.ON_SURFACE if in_month else ft.Colors.OUTLINE
        elif is_today:
            bgcolor, color = TODAY_BG, ft.Colors.PRIMARY
        elif not in_month:
            bgcolor, color = None, ft.Colors.OUTLINE
        else:
            bgcolor, color = None, ft.Colors.ON_SURFACE

        return ft.Container(
            width=CELL_W,
            height=CELL_H,
            alignment=ft.Alignment.CENTER,
            border_radius=ft.BorderRadius.all(CELL_RADIUS),
            bgcolor=bgcolor,
            on_click=None if not enabled else (lambda _e, d=day: self._cal_pick(d)),
            on_hover=None
            if not enabled
            else (lambda e, k=key: self._hover_key(k, _truthy(e.data))),
            content=ft.Text(
                str(day.day),
                size=TEXT_SIZE,
                color=color,
                weight=ft.FontWeight.W_600
                if (selected or (is_today and enabled))
                else ft.FontWeight.NORMAL,
            ),
        )

    def _cal_months(self) -> ft.Control:
        """4 × 3 年月网格，高度与月历区一致（面板不跳动）。"""
        pad = max(0, (CAL_GRID_H - MONTH_H * 4) // 2)
        rows: list[ft.Control] = []
        for r in range(4):
            rows.append(
                ft.Row(
                    spacing=0,
                    expand=True,
                    controls=[
                        self._cal_month_cell(r * 3 + c + 1) for c in range(3)
                    ],
                )
            )
        return ft.Container(
            height=CAL_GRID_H,
            padding=ft.Padding.symmetric(vertical=pad),
            content=ft.Column(spacing=0, expand=True, controls=rows),
        )

    def _cal_month_cell(self, month: int) -> ft.Control:
        """年月网格里的单个月份。"""
        key = f"m{month}"
        selected = self._cal_is_month_selected(month)
        enabled = self._cal_month_enabled(month)
        hovered = enabled and self._hover == key

        bgcolor: ft.ColorValue | None
        color: ft.ColorValue
        if selected:
            bgcolor, color = SELECTED_BG, ft.Colors.ON_PRIMARY
        elif not enabled:
            bgcolor, color = None, DISABLED_FG
        elif hovered:
            bgcolor, color = HOVER_BG, ft.Colors.ON_SURFACE
        else:
            bgcolor, color = None, ft.Colors.ON_SURFACE

        return ft.Container(
            height=MONTH_H,
            expand=True,
            alignment=ft.Alignment.CENTER,
            border_radius=ft.BorderRadius.all(CELL_RADIUS),
            bgcolor=bgcolor,
            on_click=None
            if not enabled
            else (lambda _e, m=month: self._cal_select_month(m)),
            on_hover=None
            if not enabled
            else (lambda e, k=key: self._hover_key(k, _truthy(e.data))),
            content=ft.Text(
                f"{month} 月",
                size=TEXT_SIZE,
                color=color,
                weight=ft.FontWeight.W_600 if selected else ft.FontWeight.NORMAL,
            ),
        )

    def _cal_month_enabled(self, month: int) -> bool:
        """该月的任意一天在可选范围内即可选。"""
        lo, hi = self._cal_bounds()
        first = datetime.date(self._view_year, month, 1)
        last = datetime.date(
            self._view_year, month, _get_days_in_month(self._view_year, month)
        )
        return last >= lo and first <= hi
