# ruff: noqa: DTZ011
# 组件契约是「本地、naive 的日期」：日期没有时区，比较与显示都按用户所在时区的
# 本地日历走。时区换算属于调用方业务，见 SPEC 的 notes。

"""日期选择器 (DateInput)。

交互模型对齐 Element Plus / Ant Design 的日期选择器：**一个输入框，点开挂出面板**。
面板有三种粒度（日 / 月 / 年），``type`` 决定选什么、能选几个、要不要成对选：

===================  ==========================  ================================================
``type``             值形状                       说明
===================  ==========================  ================================================
``date``             ``date | None``             单个日期
``week``             ``date | None``             整周（值是周内任意一天，显示"2026 年第 39 周"）
``month``            ``date | None``             单月（值的日恒为 1）
``year``             ``date | None``             单年（值的月日恒为 1-1）
``dates``            ``list[date]``              多个日期
``months``           ``list[date]``              多个月份
``years``            ``list[date]``              多个年份
``daterange``        ``(date, date) | None``     日期范围，两列月历并排
``monthrange``       ``(date, date) | None``     月份范围，两列月网格并排
===================  ==========================  ================================================

设计要点：

- **一套渲染，四套语义**。日 / 月 / 年三种网格共用同一套格子绘制，选中、区间连条、
  今天、禁用、非本月这些状态全部由 :class:`~ui.input.calendar_panel.DayMark`
  表达 —— 所以"选多个"和"选范围"不是两个组件，只是同一个格子算出了不同的标记。
- **粒度可下钻**。``date`` 里点标题进月网格、再点进年网格，选完逐层退回；
  ``month`` 从月网格起步，点标题进年网格。一年一跳、十年一跳，不用连点十几次翻页。
- **范围永远是两列**。左早右晚，翻页整体平移，中间不做"跨年就断"的特殊处理。
- **值只有一种类型**：``datetime.date``。月份就是"该月 1 号"，年份就是"该年 1 月 1 日"，
  不给调用方再造一套 ``YearMonth`` 类型 —— 比较、格式化、序列化都还是标准库那套。

.. note::
    面板挂在**页面浮层**（``page.overlay``）上，因此折叠态的高度就是整个组件
    占用布局的高度。浮层需要 ``page.render`` 这条根视图路径；若宿主用的是
    ``page.render_views``（Router 的 ``manage_views=True`` 视图栈），浮层层会被
    视图盖住，此时组件**自动降级为流内展开**。也可用 ``float_panel=False``
    强制走流内展开。判定见 :func:`ui.core.float_layer.overlay_usable`。

.. note::
    ``TextField`` 在 flet 1.0.0 里会吞掉所有指针事件 —— 真机实测外层
    ``GestureDetector`` 完全收不到点击。因此面板**未展开**时把输入框置为
    ``ignore_pointers``，让整框的点击都归外层；**展开后**再恢复响应，这样点框内
    文字就能落光标、直接键盘输入。

.. note::
    **键入只对单值类型开放**（``date`` / ``month`` / ``year``）：范围与多选没有
    无歧义的文本写法（``~`` 还是 ``-``？两个日期还是一个？），与其猜，不如让
    面板去点 —— 这也是桌面日历的通行做法。

用法::

    d = DateInput(label="开始日期", value=datetime.date(2026, 9, 26))
    r = DateInput(label="活动周期", type="daterange")
    m = DateInput(label="生效月份", type="monthrange")
"""

from __future__ import annotations

import datetime
from collections.abc import Callable, Sequence
from dataclasses import dataclass

import flet as ft

from ui.core.doc import Api, Example, Spec, info, run, tip, warn
from ui.core.float_layer import use_float_layer
from ui.core.format import calendar_title, format_date, format_list
from ui.core.i18n import t, use_t
from ui.core.tokens import FONT_SIZE
from ui.input.calendar_panel import (
    CAL_W,
    FIELD_HEIGHT,
    FIELD_WIDTH,
    FOOTER_H,
    PANEL_GAP,
    PANEL_H,
    RANGE_W,
    TEXT_SIZE,
    WEEKDAYS,  # noqa: F401  (历史导入路径)
    CalendarPanel,
    DayMark,
    _get_days_in_month,  # noqa: F401  (兼容导入)
    _is_leap_year,  # noqa: F401  (兼容导入)
    _norm_ym,
    place_panel,
)
from ui.input.input import Label

__all__ = ["DateInput", "DateType"]

#: 支持的类型。分组决定"值形状"，也决定面板列数与是否允许键入。
SINGLE = ("date", "week", "month", "year")
MULTI = ("dates", "months", "years")
RANGE = ("daterange", "monthrange")
ALL_TYPES = SINGLE + MULTI + RANGE

#: 别名，供类型注解与 IDE 提示（运行时仍是普通字符串）。
DateType = str

#: 各类型的起始粒度。
_BASE_MODE = {
    "date": "day",
    "week": "day",
    "dates": "day",
    "daterange": "day",
    "month": "month",
    "months": "month",
    "monthrange": "month",
    "year": "year",
    "years": "year",
}

#: 值的粒度：月 -> 日恒为 1；年 -> 月日恒为 1-1。
_MONTH_LEVEL = ("month", "months", "monthrange")
_YEAR_LEVEL = ("year", "years")


# ---------------------------------------------------------------------------
# 纯函数工具
# ---------------------------------------------------------------------------
def _as_date(value: object) -> datetime.date | None:
    """把入参收敛成 ``datetime.date``；``datetime`` 取日期部分，其它类型忽略。"""
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    return None


def _snap(day: datetime.date, granularity: str) -> datetime.date:
    """把日期对齐到当前粒度（月 -> 1 号，年 -> 1 月 1 日）。"""
    if granularity == "month":
        return day.replace(day=1)
    if granularity == "year":
        return day.replace(month=1, day=1)
    return day


def _parse_date(text: str | None) -> datetime.date | None:
    """尽力把用户敲的字符串解析成日期，失败返回 ``None``。

    支持 ``2026-09-26`` / ``2026/9/26`` / ``2026.9.26`` / ``20260926`` /
    ``2026年9月26日``（也接受末尾带不带"日"、各部分补不补零），以及
    ``09/26/2026`` 这类**月日在前**的写法。

    为什么后者要认：英文界面显示的是 ``09/26/2026``（见
    :func:`ui.core.format.format_date`），如果只认 ISO 顺序，用户照着框里
    显示的样子改一下就变成"日期非法"—— 这是本地化最常见的自相矛盾。
    判别规则很简单：4 位的那一段是年；都是短数字时，首位 ≤ 12 按月在前、
    否则按日在前的欧洲写法。
    """
    s = (text or "").strip()
    if not s:
        return None
    for ch in ("年", "月", "日", "/", ".", " "):
        s = s.replace(ch, "-")
    parts = [p for p in s.split("-") if p]
    try:
        if len(parts) == 1 and len(parts[0]) == 8 and parts[0].isdigit():
            return datetime.date(
                int(parts[0][:4]), int(parts[0][4:6]), int(parts[0][6:])
            )
        if len(parts) == 3:
            first, second, third = (int(p) for p in parts)
            if len(parts[0]) == 4:  # 2026-09-26
                return datetime.date(first, second, third)
            if len(parts[2]) == 4 or third > 31:  # 09/26/2026 或 26/09/2026
                year = third
                month, day = (first, second) if first <= 12 else (second, first)
                return datetime.date(year, month, day)
    except ValueError:
        return None
    return None


def _split(text: str | None) -> list[str]:
    """把 ``2026-09`` / ``2026年9月`` / ``202609`` 拆成数字段。"""
    s = (text or "").strip()
    for ch in ("年", "月", "日", "/", ".", " ", "-"):
        s = s.replace(ch, "-")
    return [p for p in s.split("-") if p]


def _parse_month(text: str | None) -> datetime.date | None:
    """解析到"月"：``2026-09`` / ``2026/9`` / ``202609`` / 只写 ``2026``（取 1 月）。"""
    parts = _split(text)
    try:
        if len(parts) == 1 and parts[0].isdigit():
            raw = parts[0]
            if len(raw) == 6:
                return datetime.date(int(raw[:4]), int(raw[4:]), 1)
            if len(raw) == 4:
                return datetime.date(int(raw), 1, 1)
        if len(parts) == 2:
            return datetime.date(int(parts[0]), int(parts[1]), 1)
    except ValueError:
        return None
    return None


def _parse_year(text: str | None) -> datetime.date | None:
    """解析到"年"：``2026`` / ``2026 年``。"""
    parts = _split(text)
    if len(parts) == 1 and len(parts[0]) == 4 and parts[0].isdigit():
        return datetime.date(int(parts[0]), 1, 1)
    return None


def week_bounds(
    day: datetime.date, first_weekday: int
) -> tuple[datetime.date, int, int]:
    """``day`` 所在的那一周：返回 ``(周首日, ISO 年, ISO 周号)``。

    周首日跟着界面语言（中文周一、英文周日），但**周号统一按 ISO 算**：取该行的
    第 4 天（周一制就是周四）的 ISO 周号。ISO 周由周四定义，周一制算出来是精确值；
    周日制下那行是 周日..周六，其中周三、周四同属一个 ISO 周，取周三也一样 ——
    所以这一个公式在两种首日下都对。
    """
    start = day - datetime.timedelta(days=(day.weekday() - first_weekday) % 7)
    iso = (start + datetime.timedelta(days=3)).isocalendar()
    return start, iso.year, iso.week


@ft.observable
@dataclass
class DateInput(CalendarPanel, Label):
    """日期 / 周 / 月 / 年 / 多选 / 范围 选择器。

    Args:
        value: 当前值。形状随 ``type`` 变化（见模块 docstring 的表）：单值是
            ``date | None``，多选是 ``list[date]``，范围是 ``(start, end)``；
            范围允许半填 ``(start, None)``。
        type: 选择类型，见 :data:`ALL_TYPES`。默认 ``"date"``。
        min_date: 可选下界（含当天）。``None`` 时取 ``year_range`` 的起始年 1 月 1 日。
        max_date: 可选上界（含当天）。``None`` 时取 ``year_range`` 的结束年 12 月 31 日。
        year_range: 可选的年份范围，默认 ``(1900, 2100)``。
        display_format: 单值日期的 ``strftime`` 格式。``None``（默认）跟随界面语言。
        placeholder: 未选择时的占位文本。``None``（默认）取语言包里对应类型的文案。
        separator: 范围两端之间的连接符。``None``（默认）取语言包的 ``" ~ "``。
        first_day_weekday: 每周首日，``0`` = 周一 … ``6`` = 周日。``None`` 跟随语言。
        weekday_labels: 7 个星期标签，索引同上。``None`` 取语言包。
        width: 输入框宽度。``None``（默认）按类型取：单值 240，范围 300
            —— 范围要放得下 "2026-09-01 ~ 2026-09-20" 这一整串。
        height: 输入框高度，默认 40。
        clearable: 是否允许清空，默认 True。
        disabled: 是否禁用。
        is_open: 面板是否展开（运行期状态，可代码控制）。
        float_panel: 面板是否走页面浮层。``None`` 自动，``True`` / ``False`` 强制。
        on_change: 值变化回调，接收与 ``value`` 同形状的最新值。
    """

    value: datetime.date | Sequence[datetime.date] | None = None
    type: DateType = "date"
    min_date: datetime.date | None = None
    max_date: datetime.date | None = None
    year_range: tuple[int, int] = (1900, 2100)
    display_format: str | None = None
    placeholder: str | None = None
    separator: str | None = None
    first_day_weekday: int | None = None
    weekday_labels: tuple[str, ...] | None = None
    width: int | float | None = None
    height: int | float = FIELD_HEIGHT
    clearable: bool = True
    disabled: bool = False
    is_open: bool = False
    float_panel: bool | None = None
    on_change: Callable[[object], None] | None = None

    def __post_init__(self) -> None:
        if self.type not in ALL_TYPES:
            raise ValueError(
                f"DateInput.type 不支持 {self.type!r}，可选：{'/'.join(ALL_TYPES)}"
            )
        if self.width is None:
            # 范围要同时放下两个日期，240 会把右半边吃掉
            self.width = FIELD_WIDTH + 60 if self.type in RANGE else FIELD_WIDTH
        # 运行期状态：下划线开头 => 不参与序列化，变更后靠 notify() 重绘。
        self._sel: list[datetime.date] = self._normalize_sel(self.value)
        self.value = self._value_of(self._sel)  # 入参一律规整成规范形状
        self._hover: str | None = None  # 当前悬停元素的 key
        self._hover_day: datetime.date | None = None  # 悬停的日期（区间预览用）
        self._anchor: tuple[float, float] | None = None  # 输入框左上角页面坐标
        self._field_w: float = float(self.width)  # 输入框实测宽（on_size_change 上报）
        self._field_h: float = float(self.height)
        self._text: str | None = None  # 用户正在输入的原文；None = 显示格式化值
        self._invalid: bool = False  # 键入内容非法（框体转红边）
        self._emitted = self.value  # 上次广播出去的值
        self._mode: str = _BASE_MODE[self.type]  # "day" / "month" / "year"
        self._views: list[tuple[int, int]] = self._initial_views()

    # ------------------------------------------------------------------
    # 值：规整 / 还原
    # ------------------------------------------------------------------
    @property
    def granularity(self) -> str:
        """值的粒度：``"day"`` / ``"month"`` / ``"year"``。"""
        if self.type in _MONTH_LEVEL:
            return "month"
        if self.type in _YEAR_LEVEL:
            return "year"
        return "day"

    def _normalize_sel(self, value: object) -> list[datetime.date]:
        """把任意入参收敛成内部表示：按粒度对齐、去重、升序的点列表。"""
        granularity = self.granularity
        if self.type in RANGE:
            items = list(value) if isinstance(value, (tuple, list)) else []
            points = [
                _snap(day, granularity)
                for day in (_as_date(item) for item in items[:2])
                if day is not None
            ]
            return sorted(points) if len(points) == 2 else points
        if self.type in MULTI:
            items = value if isinstance(value, (list, tuple, set)) else [value]
            found = {
                _snap(day, granularity)
                for day in (_as_date(item) for item in items)
                if day is not None
            }
            return sorted(found)
        day = _as_date(value)
        return [_snap(day, granularity)] if day is not None else []

    def _value_of(self, sel: list[datetime.date]) -> object:
        """内部表示 -> 对外的 ``value`` 形状。"""
        if self.type in RANGE:
            if not sel:
                return None
            return (sel[0], sel[1] if len(sel) > 1 else None)
        if self.type in MULTI:
            return list(sel)
        return sel[0] if sel else None

    def _initial_views(self) -> list[tuple[int, int]]:
        """面板初始显示的年月：优先落在已选值上，否则今天。"""
        base = self._sel[0] if self._sel else datetime.date.today()
        year, month = base.year, base.month
        if self.type == "monthrange":
            return [(year, month), (year + 1, month)]
        if self.type in RANGE:
            return [(year, month), _norm_ym(year, month + 1)]
        return [(year, month)]

    # ------------------------------------------------------------------
    # 公开操作
    # ------------------------------------------------------------------
    def open(self, focus: datetime.date | None = None) -> None:
        """展开面板；``focus`` 指定面板先跳到的月份（默认跟随当前值 / 今天）。"""
        if self.disabled or self.is_open:
            return
        self._mode = _BASE_MODE[self.type]
        self._invalid = False
        self._hover = None
        self._hover_day = None
        base = focus or (self._sel[0] if self._sel else datetime.date.today())
        self._views = self._views_from(base)
        self.is_open = True
        self.notify()  # type: ignore[attr-defined]

    def _views_from(self, base: datetime.date) -> list[tuple[int, int]]:
        """以 ``base`` 为左列，向右补出第二列（范围类型才有）。"""
        year, month = base.year, base.month
        if self.type == "monthrange":
            return [(year, month), (year + 1, month)]
        if self.type in RANGE:
            return [(year, month), _norm_ym(year, month + 1)]
        return [(year, month)]

    def close(self) -> None:
        """收起面板（放弃未提交的键入内容）。"""
        if not self.is_open:
            return
        self.is_open = False
        self._hover = None
        self._hover_day = None
        self._text = None
        self._invalid = False
        self.notify()  # type: ignore[attr-defined]

    def toggle_open(self) -> None:
        """展开 / 收起。"""
        self.close() if self.is_open else self.open()

    def clear(self) -> None:
        """清空已选值。"""
        if not self._sel:
            return
        self._commit([])

    def select(self, value: object, close: bool = True) -> None:
        """选中一个值（形状随 ``type``）；``close=False`` 时保持面板展开。

        越界的值**整体拒绝**而不是挑着收 —— 范围里只收一半会得到一个
        用户没表达过的区间，比什么都不做更难排查。
        """
        self._assign(value, close=close)

    def set_value(self, value: object) -> None:
        """等价于 ``select(value, close=False)``，语义更贴近"外部灌值"。"""
        self._assign(value)

    def _assign(self, value: object, *, close: bool = False) -> None:
        """校验范围后再写。越界入参静默忽略（与面板点选的边界行为一致）。"""
        sel = self._normalize_sel(value)
        if any(not self._accepts_point(point) for point in sel):
            return
        self._commit(sel, close=close)

    def refresh(self) -> None:
        """外部直接改过 ``value`` 后调用：重新规整内部状态并重绘。"""
        self._sel = self._normalize_sel(self.value)
        self.value = self._value_of(self._sel)
        self._emitted = self.value
        self._views = self._initial_views()
        self.notify()  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # 只读属性
    # ------------------------------------------------------------------
    @property
    def display_text(self) -> str:
        """当前值的文本，空值返回空串，便于表单提交 / 日志。"""
        if not self._sel:
            return ""
        if self.type in RANGE:
            head = self._fmt(self._sel[0])
            if len(self._sel) > 1:
                return f"{head}{self._sep}{self._fmt(self._sel[1])}"
            return f"{head}{self._sep}"  # 半填：留住连接符，提示"还差一个"
        if self.type in MULTI:
            # 日期串最长（10 字符），只留一项再加 "+N"，否则 240px 的框必然截断
            limit = 1 if self.type == "dates" else 2
            return format_list((self._fmt(day) for day in self._sel), limit=limit)
        if self.display_format and self.granularity == "day":
            return self._sel[0].strftime(self.display_format)
        return self._fmt(self._sel[0])

    @property
    def _sep(self) -> str:
        return self.separator or t("ui.format.range_sep")

    def _fmt(self, day: datetime.date) -> str:
        """按当前类型的粒度格式化一个点。"""
        if self.granularity == "month":
            return calendar_title(day.year, day.month)
        if self.granularity == "year":
            return calendar_title(day.year, 1, mode="year")
        if self.type == "week":
            _, iso_year, week = week_bounds(day, self._cal_first_day())
            return t("ui.date.week", year=iso_year, n=week)
        if self.display_format:
            return day.strftime(self.display_format)
        return format_date(day)

    @property
    def _min(self) -> datetime.date:
        """可选下界。"""
        if self.min_date is not None:
            return self.min_date
        lo, _hi = sorted(self.year_range)
        return datetime.date(lo, 1, 1)

    @property
    def _max(self) -> datetime.date:
        """可选上界。"""
        if self.max_date is not None:
            return self.max_date
        _lo, hi = sorted(self.year_range)
        return datetime.date(hi, 12, 31)

    @property
    def show_clear_link(self) -> bool:
        """页脚是否显示「清除」。"""
        return self.clearable and bool(self._sel)

    def _show_clear(self) -> bool:
        """框内 ×：可清空、未禁用、且当前有值。"""
        return self.clearable and not self.disabled and bool(self._sel)

    @property
    def _editable(self) -> bool:
        """是否允许键入：只有单值类型有无歧义的文本写法。"""
        return self.type in ("date", "month", "year")

    def _accepts_point(self, day: datetime.date) -> bool:
        """``day``（已对齐粒度）是否落在可选范围内。"""
        return self._min <= day <= self._max

    #: 老名字，``DateTimeInput`` 与既有测试按这个名字调用。
    _accepts = _accepts_point

    # ------------------------------------------------------------------
    # 月历钩子
    # ------------------------------------------------------------------
    def _cal_view_count(self) -> int:
        return 2 if self.type in RANGE else 1

    def _cal_bounds(self) -> tuple[datetime.date, datetime.date]:
        return self._min, self._max

    def _cal_picks_month(self) -> bool:
        return self.type in ("month", "months", "monthrange")

    def _cal_picks_year(self) -> bool:
        return self.type in ("year", "years")

    def _hover_point(self) -> datetime.date | None:
        """悬停日期对齐到当前粒度（区间预览要用同一套坐标）。"""
        day = self._hover_day
        return None if day is None else _snap(day, self.granularity)

    def _range_mark(self, point: datetime.date) -> DayMark:
        """区间 / 整周的连条：起终点画实心圆，中间填浅色带，两端收圆角。"""
        if not self._sel:
            return DayMark()
        start = self._sel[0]
        end = self._sel[1] if len(self._sel) > 1 else self._hover_point()
        selected = point == start or (end is not None and point == end)
        if end is None or end == start:
            return DayMark(selected=point == start)
        lo, hi = (start, end) if start <= end else (end, start)
        if lo <= point <= hi:
            return DayMark(
                selected=selected,
                band=True,
                round_left=point == lo,
                round_right=point == hi,
            )
        return DayMark(selected=selected)

    def _cal_marks(self, day: datetime.date) -> DayMark:
        if self.type == "week":
            row = self._week_start(day)
            if self._sel and self._week_start(self._sel[0]) == row:
                return DayMark(band=True, selected=day == self._sel[0])
            hovered = self._hover_day
            return DayMark(
                band=hovered is not None and self._week_start(hovered) == row
            )
        if self.type == "dates":
            return DayMark(selected=day in self._sel)
        if self.type in RANGE:
            return self._range_mark(day)
        return DayMark(selected=bool(self._sel) and day == self._sel[0])

    def _cal_month_marks(self, year: int, month: int) -> DayMark:
        point = datetime.date(year, month, 1)
        if self.type == "months":
            return DayMark(selected=point in self._sel)
        if self.type in RANGE:
            return self._range_mark(point)
        # 单值类型：值可能是"某月 26 号"，比较前先对齐到月，否则下钻到月网格
        # 时当前月不高亮 —— 看起来像"什么都没选"。
        return DayMark(
            selected=bool(self._sel) and _snap(self._sel[0], "month") == point
        )

    def _cal_year_marks(self, year: int) -> DayMark:
        point = datetime.date(year, 1, 1)
        if self.type == "years":
            return DayMark(selected=point in self._sel)
        return DayMark(
            selected=bool(self._sel) and _snap(self._sel[0], "year") == point
        )

    def _week_start(self, day: datetime.date) -> datetime.date:
        return week_bounds(day, self._cal_first_day())[0]

    # ------------------------------------------------------------------
    # 点选
    # ------------------------------------------------------------------
    def _cal_pick(self, day: datetime.date) -> None:
        """点某一天：按类型决定"选值收起 / 切换 / 记区间端点"。"""
        if self.disabled:
            return
        if self.type == "week":
            self._commit([self._week_start(day)], close=True)
        elif self.type == "dates":
            self._toggle(day)
        elif self.type == "daterange":
            self._pick_range(day)
        else:
            self._commit([day], close=True)

    def _cal_pick_month(self, year: int, month: int, idx: int = 0) -> None:
        """点某个月（月选择器 / 月份范围）。"""
        if self.disabled:
            return
        point = datetime.date(year, month, 1)
        if self.type == "months":
            self._toggle(point)
        elif self.type == "monthrange":
            self._pick_range(point)
        else:
            self._commit([point], close=True)

    def _cal_pick_year(self, year: int, idx: int = 0) -> None:
        """点某个年（年选择器 / 多年选择）。"""
        if self.disabled:
            return
        point = datetime.date(year, 1, 1)
        if self.type == "years":
            self._toggle(point)
        else:
            self._commit([point], close=True)

    def _pick_today(self) -> None:
        """页脚「今天」：交给点选逻辑处理，各类型语义自然一致。"""
        self._cal_pick(datetime.date.today())

    # ------------------------------------------------------------------
    # 写值
    # ------------------------------------------------------------------
    def _toggle(self, point: datetime.date) -> None:
        """多选：有就去掉，没有就加上（保持升序，显示稳定）。"""
        if point in self._sel:
            self._commit([day for day in self._sel if day != point])
        else:
            self._commit(sorted([*self._sel, point]))

    def _pick_range(self, point: datetime.date) -> None:
        """范围：第一下记起点，第二下补终点（自动纠正先后），第三下重新开始。"""
        if len(self._sel) != 1:
            self._commit([point])
            return
        first = self._sel[0]
        lo, hi = (first, point) if first <= point else (point, first)
        self._commit([lo, hi], close=True)

    def _commit(
        self,
        sel: list[datetime.date],
        *,
        close: bool = False,
        text: str | None = None,
    ) -> None:
        """内部唯一写入口：同步 ``value`` / 视图 / 键入态，然后广播。

        ``text`` 只在"边打字边生效"时传：用户正在输入的原文要留着，
        否则每敲一个字符光标就会跳回末尾。
        """
        self._sel = list(sel)
        self.value = self._value_of(self._sel)
        self._text = text
        self._invalid = False
        self._hover = None
        self._hover_day = None
        # 单值类型选完就把面板挪到那个月（多选 / 范围不挪，否则会打断连续点选）
        if self.type in SINGLE and self._sel:
            self._views = self._views_from(self._sel[0])
        self._emit()
        if close:
            self.close()

    def _emit(self) -> None:
        """广播变化。

        ``on_change`` **按值变化去重**：同一个值只回调一次 —— 重复点已选中的
        那一天、键入与当前值相同的文本都不会重复触发外部回调。
        """
        if self.value != self._emitted:
            self._emitted = self.value
            if self.on_change:
                self.on_change(self.value)
        self.notify()  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    @ft.component
    def ui(self) -> ft.Control:
        """构建日期选择器 UI。"""
        use_t()  # 订阅语言：占位符、页脚、标题、星期名都要跟着切
        page = ft.context.page
        field = self._build_field(self._text_field(), self._trailing_icon())
        panel = self._build_panel()
        floating = self._should_float(page)

        if floating:
            body: ft.Control = field  # 面板在浮层里，布局只占折叠态的高度
        elif self.is_open and not self.disabled:
            body = ft.Column(controls=[field, panel], spacing=PANEL_GAP)
        else:
            body = field

        width = self._panel_width()
        left, top, bottom = place_panel(
            page, self._anchor, self._field_h, width, PANEL_H
        )
        # 无条件调用（hook 顺序必须稳定）；visible=False 时浮层自动移除。
        # hole 把输入框从遮罩里挖出来：展开后还要能点框内文字落光标。
        use_float_layer(
            page=page,
            visible=floating and self.is_open and not self.disabled,
            left=left,
            top=top,
            bottom=bottom,
            content=panel,
            on_dismiss=self.close,
            hole=self._hole(),
        )

        return self._with_label(body)

    def _panel_width(self) -> float:
        """面板宽：范围类型两列并排，其余一列。"""
        return RANGE_W if self.type in RANGE else CAL_W

    # ---- 输入框 ----

    def _trailing_icon(self) -> ft.Control:
        """尾图标：范围类型用区间图标，其余用日历图标。"""
        icon = ft.Icons.DATE_RANGE if self.type in RANGE else ft.Icons.CALENDAR_MONTH
        return ft.Icon(
            icon,
            size=18,
            color=ft.Colors.OUTLINE if self.disabled else ft.Colors.ON_SURFACE_VARIANT,
        )

    def _text_field(self) -> ft.Control:
        """框内文本。收起态 ``ignore_pointers`` —— 让点击穿透到外层手势。"""
        editable = self._editable and not self.disabled
        return ft.TextField(
            value=self._text if self._text is not None else self.display_text,
            border=ft.NoInputBorder(),
            filled=False,
            dense=True,
            text_size=TEXT_SIZE,
            color=ft.Colors.ON_SURFACE if not self.disabled else ft.Colors.OUTLINE,
            content_padding=ft.Padding.symmetric(vertical=6),
            hint_text=self.placeholder or t(f"ui.date.ph.{self.type}"),
            hint_style=ft.TextStyle(size=TEXT_SIZE, color=ft.Colors.OUTLINE),
            keyboard_type=ft.KeyboardType.DATETIME,
            read_only=not editable,
            # 关键：收起（或禁用）时不吃指针事件，否则外层 GestureDetector 拿不到点击。
            ignore_pointers=self.disabled or not self.is_open or not editable,
            on_change=None if not editable else self._on_text_change,
            on_submit=None if not editable else self._on_text_submit,
            on_blur=None if not editable else self._on_text_blur,
        )

    def _parse(self, text: str | None) -> datetime.date | None:
        """按当前类型解析键入内容。"""
        if self.type == "month":
            return _parse_month(text)
        if self.type == "year":
            return _parse_year(text)
        return _parse_date(text)

    def _on_text_change(self, e: ft.ControlEvent) -> None:
        """键入过程中即时解析：合法就同步 ``value`` 并广播，全程不打断输入。

        "合法就落地"是和 Element Plus 一致的模型 —— 敲到哪算到哪，失焦不会丢；
        敲到非法内容时保持上一个合法值，框体不标红（还在输入中，不算错）。
        """
        text = e.data or ""
        self._text = text
        self._invalid = False
        parsed = self._parse(text)
        if parsed is not None and self._accepts_point(parsed) and parsed != self.value:
            self._commit([parsed], text=text)
            return
        self.notify()  # type: ignore[attr-defined]

    def _on_text_submit(self, e: ft.ControlEvent) -> None:
        """回车提交：合法则选中并收起，非法则原样还原并标红。"""
        parsed = self._parse(
            self._text if self._text is not None else self.display_text
        )
        self._text = None
        if parsed is not None and self._accepts_point(parsed):
            self._invalid = False
            self._commit([parsed], close=True)
            return
        if not self._sel:
            # 本来就是空的，敲了半截又回车 —— 没东西可还原，也不算错。
            self._invalid = False
            self.notify()  # type: ignore[attr-defined]
            return
        self._invalid = True
        self.notify()  # type: ignore[attr-defined]

    def _on_text_blur(self, e: ft.ControlEvent) -> None:
        """失焦即放弃未提交的键入（回到格式化值）。

        非法输入回车后 ``_text`` 已经是 ``None``，但红边还在 —— 失焦是这次
        输入的终点，把 ``_invalid`` 一并清掉，否则红边会一直挂在框上。
        """
        if self._text is None and not self._invalid:
            return
        self._text = None
        self._invalid = False
        self.notify()  # type: ignore[attr-defined]

    # ---- 面板 ----

    def _build_panel(self) -> ft.Control:
        """面板：视图（1~2 列）+ 分隔线 + 页脚。"""
        return self._panel_shell(
            self._panel_width(),
            ft.Column(
                spacing=0,
                controls=[self._cal_panel(), self._divider(), self._footer()],
            ),
        )

    def _footer(self) -> ft.Control:
        """页脚：左侧「今天」（日粒度才有），右侧「清除」（有值且可清空时）。"""
        controls: list[ft.Control] = []
        if self.type in ("date", "week", "dates"):
            controls.append(
                self._link_button(
                    "today",
                    t("ui.date.today"),
                    self._pick_today,
                    enabled=self._cal_day_enabled(datetime.date.today()),
                )
            )
        controls.append(ft.Container(expand=True))
        if self.show_clear_link:
            controls.append(
                self._link_button("clear", t("ui.common.clear"), self.clear)
            )
        return ft.Container(
            height=FOOTER_H,
            padding=ft.Padding.only(left=2, right=2),
            content=ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=controls
            ),
        )


# ---------------------------------------------------------------------------
# 独立运行：组件介绍 + 示例 + API
# ---------------------------------------------------------------------------
def _caption(text: str) -> ft.Control:
    return ft.Text(
        text,
        size=FONT_SIZE["small"],
        color=ft.Colors.ON_SURFACE_VARIANT,
        style=ft.TextStyle(height=1.6),
    )


@ft.component
def _echo(field: DateInput) -> ft.Control:
    """把当前值读出来 —— DateInput 是 observable，值一变这里就跟着重绘。"""
    return _caption(f"当前值：{field.display_text or '（未选择）'}")


@ft.component
def _basic() -> ft.Control:
    value, set_value = ft.use_state(datetime.date(2026, 9, 26))
    field = DateInput(label="开始日期", value=value, on_change=set_value)
    return ft.Column(
        spacing=10,
        controls=[
            field.ui(),
            _caption(f"当前值：{value.isoformat() if value else '（未选择）'}"),
            ft.Row(
                spacing=8,
                controls=[
                    ft.Button(
                        "设为今天",
                        on_click=lambda _: set_value(datetime.date.today()),
                    ),
                    ft.Button("清空", on_click=lambda _: set_value(None)),
                ],
            ),
        ],
    )


@ft.component
def _granularity() -> ft.Control:
    fields = [
        DateInput(label="日期", value=datetime.date(2026, 9, 26)),
        DateInput(label="整周", type="week", value=datetime.date(2026, 9, 26)),
        DateInput(label="整月", type="month", value=datetime.date(2026, 9, 1)),
        DateInput(label="整年", type="year", value=datetime.date(2026, 1, 1)),
    ]
    return ft.Column(
        spacing=12,
        controls=[
            *[field.ui() for field in fields],
            _caption(
                "type 同时改变粒度与值形状：周的 value 是周内任意一天，"
                "显示时才换算成 ISO 周号；月落在 1 号，年落在 1 月 1 日。"
            ),
        ],
    )


@ft.component
def _multi_echo(field: DateInput) -> ft.Control:
    """多选的回显：除了值文本，再报一个已选天数。"""
    return _caption(
        f"已选 {len(field.value or [])} 天：{field.display_text or '（未选择）'}"
        "（多选点一次加一个，面板不收起）"
    )


@ft.component
def _range_multi() -> ft.Control:
    span = ft.use_memo(
        lambda: DateInput(
            label="统计区间",
            type="daterange",
            value=(datetime.date(2026, 9, 1), datetime.date(2026, 9, 20)),
        ),
        [],
    )
    days = ft.use_memo(
        lambda: DateInput(
            label="多选日期",
            type="dates",
            value=[datetime.date(2026, 9, 8), datetime.date(2026, 9, 15)],
        ),
        [],
    )
    return ft.Column(
        spacing=14,
        controls=[
            span.ui(),
            _echo(span),
            days.ui(),
            _multi_echo(days),
        ],
    )


_BASIC_CODE = """value, set_value = ft.use_state(datetime.date(2026, 9, 26))

field = DateInput(label="开始日期", value=value, on_change=set_value)
Column([
    field.ui(),
    ft.Text(f"当前值：{value}"),
    ft.Button("设为今天", on_click=lambda _: set_value(datetime.date.today())),
])"""

SPEC = Spec(
    name="DateInput",
    summary="一个输入框挂出月历面板，选日 / 周 / 月 / 年，也支持多选与区间。",
    definition=(
        "日期选择器解决的是「日期该被点出来，而不是敲出来」。折叠态只占一行输入框，"
        "点开才挂出月历；日、周、月、年四种粒度共用同一套格子，多选与区间只是同一套"
        "格子算出了不同的标记。值始终是标准库的 datetime.date：月份落在 1 号，年份"
        "落在 1 月 1 日，周的值是周内任意一天。"
    ),
    anatomy=[
        (
            "输入框",
            (
                "40px 高；单值 240、区间 300 —— 范围要放得下"
                "「2026-09-01 ~ 2026-09-20」这一整串。"
            ),
        ),
        (
            "面板标题",
            "点击标题逐层下钻（日 → 月 → 年）；左右箭头按视图翻页：日视图翻月、月视图翻年、年视图翻十年。",
        ),
        (
            "日期网格",
            "同一套格子按 type 画出选中、区间连条、今天、禁用与非本月；范围固定两列并排，左早右晚。",
        ),
        (
            "页脚",
            "左侧「今天」只在日粒度出现；右侧「清除」仅在有值且 clearable 时出现。",
        ),
        (
            "值文本",
            "单值跟随界面语言的日期格式；范围用「~」连接，多选只显示一至两项，超出折成「+N」，避免撑破 240px。",
        ),
    ],
    when=[
        "表单要一个明确到某天、某周或某月的字段（生日、账期、报表月份）",
        "需要一次选多个日期，或选一段起止日期（活动周期、统计区间）",
        "希望用户从日历上点选，避免手敲出 2026-13-01 这类非法日期",
    ],
    avoid=[
        "要精确到时分秒：用 DateTimeInput，日期面板里没有时间列",
        "只在「本周 / 本月 / 自定义」三个固定档位里选：用 SegmentedButton 比翻日历快",
        "允许「下周三」这类自然语言输入：先用 Input 解析再 set_value，别把解析塞进日历",
    ],
    examples=[
        Example(
            "基础用法",
            _basic,
            hint="受控写法：面板里选中的值写回 value，下面一行跟着更新；按钮演示从代码改值。",
            code=_BASIC_CODE,
        ),
        Example(
            "四种粒度",
            _granularity,
            hint="日、周、月、年共用同一个组件，type 改的是粒度、显示方式与 value 形状。",
        ),
        Example(
            "区间与多选",
            _range_multi,
            hint="区间是两列并排、点两下补出起止；多选每点一次加一个，面板不收起。",
        ),
    ],
    api=[
        Api(
            "value",
            "date | Sequence[date] | None",
            "None",
            "当前值；形状随 type 变化（单值 / 列表 / 二元组）",
        ),
        Api(
            "type",
            "str",
            "'date'",
            "date / week / month / year / dates / months / years / daterange / monthrange",
        ),
        Api(
            "min_date",
            "date | None",
            "None",
            "可选下界（含当天）；默认取 year_range 起始年",
        ),
        Api(
            "max_date",
            "date | None",
            "None",
            "可选上界（含当天）；默认取 year_range 结束年",
        ),
        Api(
            "display_format",
            "str | None",
            "None",
            "单值日期的 strftime 格式；None 跟随界面语言",
        ),
        Api("placeholder", "str | None", "None", "未选择时的占位文案；None 取语言包"),
        Api(
            "separator",
            "str | None",
            "None",
            "范围两端的连接符；None 取语言包的「 ~ 」",
        ),
        Api("clearable", "bool", "True", "是否显示框内 × 与页脚「清除」"),
        Api("disabled", "bool", "False", "禁用：不展开面板、不响应键入"),
        Api(
            "on_change",
            "Callable[[object], None] | None",
            "None",
            "值变化回调，形状与 value 一致；按值去重",
        ),
    ],
    notes=[
        info(
            "值只有 datetime.date 一种：月是当月 1 号、年是 1 月 1 日、周是周内任意一天"
            "并显示成 ISO 周号。比较、格式化和序列化都还是标准库那套。"
        ),
        tip(
            "面板挂在 page.overlay 上。宿主用 page.render_views（Router 管理视图栈）时"
            "浮层会被视图盖住，组件自动降级为流内展开；也可以用 float_panel=False 强制。"
        ),
        warn(
            "范围与多选不开放键入：~ 还是 -、两个日期还是多个，没有无歧义写法；需要批量"
            "录入时先解析再 set_value。非法键入的红边只保留到失焦 / 收起，不会一直挂在框上。"
        ),
    ],
    tags=("日期", "日历", "date", "picker", "range", "表单"),
)


if __name__ == "__main__":
    run(SPEC)
