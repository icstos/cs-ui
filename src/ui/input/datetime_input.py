"""日期时间选择器 (DateTimeInput)。

一个输入框挂出**一整块面板**：左边是月历（与 :class:`~ui.input.date_input.DateInput`
同一张，逐像素一致），右边是「时 / 分 / 秒」三列**时间轮盘**。交互模型参考
Element Plus / Ant Design 的 ``datetime`` 选择器，并按桌面端的直觉做了三处收敛：

- **日期与时间并排**，不再上下堆叠 —— 面板高度与 ``DateInput`` 完全相同（309），
  两个组件并排放在表单里不会出现高度差；
- **点日期不收起**：``datetime`` 场景下日期只是第一步，选完还要调时间。日期、
  时间、轮盘点击**全部即改即生效**（没有"待提交"状态），点「完成」或面板外部
  才收起 —— 中途关掉也不会丢操作；
- **时间轮盘**：选中项固定居中并填色，上下各留 3 格做"纵深"（越远越淡），
  ``▲ ▼`` 步进、滚轮步进、直接点任意可见值跳转。三列都是**环形**的
  （``23 → 00``、``55 分 → 00 分``），所以永远不用"从头翻到尾"。

框内可直接键入，支持 ``2026-09-26 09:30`` / ``2026/9/26 9:30:15`` /
``20260926 0930`` / ``2026年9月26日 9时30分``；只给日期则保留原时间，只给时间
则保留原日期。非法输入回车时框体转红边并还原。

.. note::
    面板挂在**页面浮层**（``page.overlay``）上，折叠态的高度就是整个组件占用
    布局的高度。浮层需要 ``page.render`` 这条根视图路径；``page.render_views``
    （``Router(manage_views=True)`` 视图栈）下会被视图盖住，此时自动降级为
    流内展开。见 :func:`ui.core.float_layer.overlay_usable`。

.. note::
    月历本体来自 :class:`ui.input.calendar_panel.CalendarPanel`；本类只覆写三个
    钩子（``_cal_bounds`` / ``_cal_is_selected`` / ``_cal_pick``），再加上右侧
    的时间列与页脚。

.. note::
    ``with_seconds=False``（默认）时，秒会被**强制归零** —— 框里显示什么，
    ``value`` 就是什么，不会出现"看着是 09:30、值是 09:30:47"的隐性偏差。
    因此外部传入的 ``value`` 也会在构造时统一按该规则规整（微秒恒清零）。

用法::

    d = DateTimeInput(label="会议时间", value=datetime.datetime(2026, 9, 26, 9, 30))
    ...
    container = d.ui()
"""

from __future__ import annotations

import datetime
import re
from collections.abc import Callable
from dataclasses import dataclass

import flet as ft

from ui.core.float_layer import use_float_layer
from ui.input.calendar_panel import (
    CAL_GRID_H,
    CAL_GRID_W,
    CELL_RADIUS,
    FIELD_HEIGHT,
    FIELD_WIDTH,
    FOOTER_H,
    HEADER_H,
    HOVER_BG,
    LABEL_SIZE,
    PANEL_GAP,
    PANEL_PAD,
    SELECTED_BG,
    TEXT_SIZE,
    WEEKDAYS,
    CalendarPanel,
    _truthy,
    place_panel,
)
from ui.input.date_input import _parse_date
from ui.input.input import Label

__all__ = ["DateTimeInput"]

# ---------------------------------------------------------------------------
# 时间列（右侧轮盘）
# ---------------------------------------------------------------------------
TIME_COL_W = 44  # 单列宽
TIME_COL_GAP = 6  # 列间距
TIME_LABEL_H = 20  # 列头（时 / 分 / 秒）
TIME_ARROW_H = 26  # 上 / 下步进按钮（与 NAV_SIZE 一致）
TIME_ROW_H = 26  # 单行高
TIME_ROWS = 7  # 可视窗口行数（选中项居中 => 上下各 3 行）

#: 时间列必须与月历列**等高**，面板才不会是"一高一低"的阶梯。
TIME_COL_H = HEADER_H + CAL_GRID_H  # 38 + 218 = 256
TIME_COL_CONTENT_H = TIME_LABEL_H + TIME_ARROW_H * 2 + TIME_ROW_H * TIME_ROWS
TIME_PAD_V = max(0, (TIME_COL_H - TIME_COL_CONTENT_H) // 2)  # 余量上下均分

#: 竖向分隔线连同左右留白占的宽度。
V_DIV_W = 1 + PANEL_PAD * 2

#: 轮盘的"纵深"：离中心越远的行越淡（索引 = 距离行数）。
WHEEL_FADE = (1.0, 0.62, 0.40, 0.24)

#: 三列的定义：(字段名, 列头文案, 取值上限, 步长字段名)
TIME_KINDS = ("hour", "minute", "second")
TIME_LABELS = {"hour": "时", "minute": "分", "second": "秒"}
TIME_STEPS = {"hour": "hour_step", "minute": "minute_step", "second": "second_step"}

#: 时间部分的常见写法（``09:30`` / ``9时30分`` / ``0930`` / ``093000``）。
_TIME_TOKEN = re.compile(
    r"(\d{1,2}:\d{1,2}(?::\d{1,2})?"  # 09:30 / 09:30:15
    r"|\d{1,2}[时点]\d{0,2}(?:分\d{0,2})?(?:秒)?)"  # 9时30分 / 9时
)


# ---------------------------------------------------------------------------
# 纯函数工具
# ---------------------------------------------------------------------------
def _split_datetime_text(text: str | None) -> tuple[str, str]:
    """把用户敲的整串拆成 ``(日期串, 时间串)``，某一段没给就是空串。

    支持空格 / ``T`` 分隔、``09:30`` 冒号式、``9时30分`` 中式，以及
    ``20260926 0930`` 这种"贴着写"的形式。
    """
    s = (text or "").strip().replace("：", ":").replace("T", " ")
    if not s:
        return "", ""

    m = _TIME_TOKEN.search(s)
    if m:
        return s[: m.start()].strip(" -/.、,，"), m.group(0)

    # 空格分隔的两段，后一段是纯数字（0930 / 093000）
    parts = s.split()
    if len(parts) >= 2 and parts[-1].isdigit() and len(parts[-1]) in (4, 6):
        return " ".join(parts[:-1]), parts[-1]
    return s, ""


def _parse_time_parts(text: str | None) -> dict[str, int] | None:
    """解析时间串，返回**只包含出现过的字段**的字典；失败返回 ``None``。

    只给小时就只返回 ``{"hour": …}``，调用方据此保留原有的分 / 秒 —— 这样
    "改时间的一部分"不会顺手把没提的部分清零。
    """
    s = (text or "").strip()
    if not s:
        return None
    for ch, rep in (("时", ":"), ("点", ":"), ("分", ":"), ("秒", ""), ("：", ":")):
        s = s.replace(ch, rep)
    s = s.strip(": ").strip()
    if not s:
        return None

    if ":" in s:
        parts = s.split(":")
    elif s.isdigit() and len(s) in (1, 2, 4, 6):
        # 0930 / 093000 这种连写；1~2 位当作"只有小时"
        parts = [s] if len(s) <= 2 else [s[i : i + 2] for i in range(0, len(s), 2)]
    else:
        return None

    if len(parts) > 3 or any(not p.isdigit() for p in parts):
        return None
    out = {k: int(p) for k, p in zip(TIME_KINDS, parts)}
    if out.get("hour", 0) > 23 or out.get("minute", 0) > 59 or out.get("second", 0) > 59:
        return None
    return out


def _parse_datetime(
    text: str | None, base: datetime.datetime
) -> datetime.datetime | None:
    """解析日期时间串；没提到的部分沿用 ``base``。失败返回 ``None``。"""
    date_text, time_text = _split_datetime_text(text)
    day = _parse_date(date_text) if date_text else None
    parts = _parse_time_parts(time_text)
    if day is None and parts is None:
        return None
    parts = parts or {}
    d = day or base.date()
    return datetime.datetime(
        d.year,
        d.month,
        d.day,
        parts.get("hour", base.hour),
        parts.get("minute", base.minute),
        parts.get("second", base.second),
    )


def _positive(value: object, fallback: int = 1) -> int:
    """把步长规整成正整数。"""
    try:
        step = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return fallback
    return step if step > 0 else fallback


@ft.observable
@dataclass
class DateTimeInput(CalendarPanel, Label):
    """日期时间选择器：输入框 + 悬浮「月历 + 时间轮盘」面板。

    Args:
        value: 当前日期时间。``None`` 表示取 ``datetime.now()``（截到秒 / 分）。
        min_datetime: 可选下界（含）。``None`` 时取 ``year_range`` 起始年 1 月 1 日 00:00。
        max_datetime: 可选上界（含）。``None`` 时取 ``year_range`` 结束年 12 月 31 日 23:59:59。
        year_range: 未显式给 min / max 时使用的年份兜底范围，默认 ``(1900, 2100)``。
        with_seconds: 是否显示秒列，默认 False（此时秒恒为 0）。
        hour_step: 小时步长，默认 1。
        minute_step: 分钟步长，默认 1（常用 1 / 5 / 10 / 15 / 30）。
        second_step: 秒步长，默认 10。
        display_format: 框内文本的 ``strftime`` 格式。``None``（默认）时按
            ``with_seconds`` 自动选 ``"%Y-%m-%d %H:%M:%S"`` / ``"%Y-%m-%d %H:%M"``。
        placeholder: 未填写时的占位文本。
        first_day_weekday: 每周首日，索引同 ``datetime.date.weekday()``
            —— ``0`` = 周一（默认）、``6`` = 周日。
        weekday_labels: 7 个星期标签，索引同上。
        width: 输入框宽度，默认 240。
        height: 输入框高度，默认 40。
        clearable: 是否允许清空（框内 × 与页脚「清除」），默认 True。
        disabled: 是否禁用。
        is_open: 面板是否展开（运行期状态，可代码控制）。
        float_panel: 面板是否走页面浮层。``None``（默认）表示自动。
        on_change: 变化回调，接收最新的 ``datetime.datetime | None``。
    """

    value: datetime.datetime | None = None
    min_datetime: datetime.datetime | None = None
    max_datetime: datetime.datetime | None = None
    year_range: tuple[int, int] = (1900, 2100)
    with_seconds: bool = False
    hour_step: int = 1
    minute_step: int = 1
    second_step: int = 10
    display_format: str | None = None
    placeholder: str = "请选择日期时间"
    first_day_weekday: int = 0
    weekday_labels: tuple[str, ...] = WEEKDAYS
    width: int | float = FIELD_WIDTH
    height: int | float = FIELD_HEIGHT
    clearable: bool = True
    disabled: bool = False
    is_open: bool = False
    float_panel: bool | None = None
    on_change: Callable[[datetime.datetime | None], None] | None = None

    def __post_init__(self) -> None:
        # 运行期状态：下划线开头 => 不参与序列化，变更后靠 notify() 重绘。
        self._hover: str | None = None  # 当前悬停元素的 key
        self._anchor: tuple[float, float] | None = None  # 输入框左上角页面坐标
        self._field_w: float = float(self.width)  # 输入框实测宽（on_size_change 上报）
        self._field_h: float = float(self.height)
        self._text: str | None = None  # 用户正在输入的原文；None = 显示格式化值
        self._invalid: bool = False  # 键入内容非法（框体转红边）
        if self.value is None:
            self.value = self._normalize(datetime.datetime.now())
        else:
            self.value = self._normalize(self.value)
        self._emitted: datetime.datetime | None = self.value  # 上次广播出去的值
        self._view_year: int = self.value.year  # 面板显示的年份
        self._view_month: int = self.value.month  # 面板显示的月份
        self._mode: str = "day"  # "day" = 月历， "month" = 年月网格

    # ------------------------------------------------------------------
    # 公开操作
    # ------------------------------------------------------------------
    def open(self, focus: datetime.datetime | None = None) -> None:
        """展开面板；``focus`` 指定面板先跳到的月份（默认跟随当前值）。"""
        if self.disabled or self.is_open:
            return
        target = focus or self.value or datetime.datetime.now()
        self._view_year, self._view_month = target.year, target.month
        self._mode = "day"
        self._invalid = False
        self.is_open = True
        self.notify()  # type: ignore[attr-defined]

    def close(self) -> None:
        """收起面板（放弃未提交的键入内容）。"""
        if not self.is_open:
            return
        self.is_open = False
        self._hover = None
        self._text = None
        self.notify()  # type: ignore[attr-defined]

    def toggle_open(self) -> None:
        """展开 / 收起。"""
        self.close() if self.is_open else self.open()

    def clear(self) -> None:
        """清空已选日期时间。"""
        if self.value is None:
            return
        self.value = None
        self._text = None
        self._invalid = False
        self._emit()

    def select(self, value: datetime.datetime, close: bool = True) -> None:
        """选中某个日期时间；``close=False`` 时保持面板展开。"""
        if not self._accepts(value):
            return
        self.value = self._normalize(value)
        self._text = None
        self._invalid = False
        self._view_year, self._view_month = self.value.year, self.value.month
        self._emit()
        if close:
            self.close()

    def set_time(
        self,
        hour: int | None = None,
        minute: int | None = None,
        second: int | None = None,
    ) -> None:
        """只改时间部分（``None`` 表示该字段不动）。"""
        base = self.value or datetime.datetime.now()
        changes = {
            k: v for k, v in (("hour", hour), ("minute", minute), ("second", second))
            if v is not None
        }
        if changes:
            self._assign(base.replace(**changes))

    # ------------------------------------------------------------------
    # 只读属性
    # ------------------------------------------------------------------
    @property
    def display_text(self) -> str:
        """当前值的格式化文本，空值返回空串，便于表单提交 / 日志。"""
        return "" if self.value is None else self.value.strftime(self._fmt)

    @property
    def _fmt(self) -> str:
        """框内文本格式：显式指定优先，否则按 ``with_seconds`` 自动选。"""
        if self.display_format:
            return self.display_format
        return "%Y-%m-%d %H:%M:%S" if self.with_seconds else "%Y-%m-%d %H:%M"

    @property
    def _min(self) -> datetime.datetime:
        """可选下界。"""
        if self.min_datetime is not None:
            return self.min_datetime
        lo, _ = sorted(self.year_range)
        return datetime.datetime(lo, 1, 1)

    @property
    def _max(self) -> datetime.datetime:
        """可选上界。"""
        if self.max_datetime is not None:
            return self.max_datetime
        _, hi = sorted(self.year_range)
        return datetime.datetime(hi, 12, 31, 23, 59, 59)

    @property
    def show_clear_link(self) -> bool:
        """页脚是否显示「清除」。"""
        return self.clearable and self.value is not None

    @property
    def _kinds(self) -> tuple[str, ...]:
        """当前启用的时间列。"""
        return TIME_KINDS if self.with_seconds else TIME_KINDS[:2]

    # ------------------------------------------------------------------
    # 月历钩子（其余月历能力来自 CalendarPanel）
    # ------------------------------------------------------------------
    def _cal_bounds(self) -> tuple[datetime.date, datetime.date]:
        return self._min.date(), self._max.date()

    def _cal_is_selected(self, day: datetime.date) -> bool:
        """日期格的高亮看**日期部分**（``datetime`` 不能直接和 ``date`` 比）。"""
        return self.value is not None and self.value.date() == day

    def _cal_pick(self, day: datetime.date) -> None:
        """点某一天：只改日期部分，面板保持展开（接着还要调时间）。"""
        base = self.value or datetime.datetime.now()
        self._assign(base.replace(year=day.year, month=day.month, day=day.day))

    def _accepts(self, value: datetime.datetime) -> bool:
        """``value`` 是否落在可选范围内。"""
        return self._min <= value <= self._max

    # ------------------------------------------------------------------
    # 值变更
    # ------------------------------------------------------------------
    def _normalize(self, value: datetime.datetime) -> datetime.datetime:
        """规整到本组件承诺的精度：微秒恒清零，不显示秒时秒也清零。"""
        value = value.replace(microsecond=0)
        return value if self.with_seconds else value.replace(second=0)

    def _clamp(self, value: datetime.datetime) -> datetime.datetime:
        """钳到可选范围内（面板允许选到"当天"，但当天的时间可能越界）。"""
        lo, hi = self._min, self._max
        return min(max(value, lo), hi)

    def _assign(self, value: datetime.datetime) -> None:
        """统一的赋值入口：规整 → 钳制 → 重置键入态 → 广播。"""
        self.value = self._clamp(self._normalize(value))
        self._text = None
        self._invalid = False
        self._view_year, self._view_month = self.value.year, self.value.month
        self._emit()

    def _emit(self) -> None:
        """广播变化。

        ``on_change`` **按值变化去重**：同一个值只回调一次，点重复的日期 /
        时间、键入与当前值相同的文本都不会重复触发外部回调。
        """
        if self.value != self._emitted:
            self._emitted = self.value
            if self.on_change:
                self.on_change(self.value)
        self.notify()  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # 时间列
    # ------------------------------------------------------------------
    def _time_values(self, kind: str) -> list[int]:
        """该列的全部可选值（步长对齐；当前值不在序列里时补进去）。

        补当前值是为了让"高亮"永远等于 ``value``：``minute_step=5`` 而值是 37 时，
        列里会出现 ``… 35, 37, 40 …`` 而不是"无高亮"。
        """
        step = _positive(getattr(self, TIME_STEPS[kind]))
        base = range(0, 24 if kind == "hour" else 60, step)
        current = self._time_current(kind)
        values = sorted({*base, current})
        return values

    def _time_current(self, kind: str) -> int:
        """当前值在该列上的分量。"""
        value = self.value or datetime.datetime.now()
        return int(getattr(value, kind))

    def _step_time(self, kind: str, delta: int) -> None:
        """该列按步长前后移动 ``delta`` 格（**环形**，越界回绕）。"""
        values = self._time_values(kind)
        idx = (values.index(self._time_current(kind)) + delta) % len(values)
        self.set_time(**{kind: values[idx]})

    def _on_time_wheel(self, kind: str, e: ft.ScrollEvent) -> None:
        """列上滚轮 = 步进一格（向下滚 = 值变大，与"向下翻列表"一致）。"""
        delta = getattr(e, "scroll_delta", None)
        dy = float(getattr(delta, "y", 0) or 0)
        if dy:
            self._step_time(kind, 1 if dy > 0 else -1)

    def _time_window(self, kind: str) -> list[tuple[int, int]]:
        """可视窗口：``[(偏移, 值)]``，偏移 0 即选中项，**环形**取满 :data:`TIME_ROWS` 行。

        环形是有意的：小时列 ``23`` 的下一格就是 ``00``，分钟列 ``55`` 之后回到
        ``00``，用户永远不会撞上"到头了"的死胡同。
        """
        values = self._time_values(kind)
        half = TIME_ROWS // 2
        idx = values.index(self._time_current(kind))
        return [
            (off, values[(idx + off) % len(values)]) for off in range(-half, half + 1)
        ]

    def _time_column(self, kind: str) -> ft.Control:
        """一列时间轮盘：列头 + ▲ + :data:`TIME_ROWS` 行 + ▼。"""
        rows: list[ft.Control] = [self._time_arrow(kind, -1)]
        rows.extend(
            self._time_row(kind, value, offset)
            for offset, value in self._time_window(kind)
        )
        rows.append(self._time_arrow(kind, 1))
        body = ft.Container(
            width=TIME_COL_W,
            height=TIME_COL_CONTENT_H,
            content=ft.Column(
                spacing=0,
                controls=[
                    ft.Container(
                        height=TIME_LABEL_H,
                        alignment=ft.Alignment.CENTER,
                        content=ft.Text(
                            TIME_LABELS[kind],
                            size=LABEL_SIZE,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                    ),
                    *rows,
                ],
            ),
        )
        # 滚轮挂在整列上（列头 / 箭头也算），命中范围大一点更好按。
        return ft.GestureDetector(
            on_scroll=lambda e, k=kind: self._on_time_wheel(k, e),
            content=body,
        )

    def _time_row(self, kind: str, value: int, offset: int) -> ft.Control:
        """轮盘里的一行。``offset == 0`` 是选中项（居中、填色）。"""
        selected = offset == 0
        key = f"t{kind}:{value}"
        fade = WHEEL_FADE[min(abs(offset), len(WHEEL_FADE) - 1)]

        bgcolor: ft.ColorValue | None
        color: ft.ColorValue
        if selected:
            bgcolor, color = SELECTED_BG, ft.Colors.ON_PRIMARY
        elif self._hover == key:
            bgcolor, color = HOVER_BG, ft.Colors.ON_SURFACE
        else:
            bgcolor, color = None, ft.Colors.with_opacity(fade, ft.Colors.ON_SURFACE)

        return ft.Container(
            height=TIME_ROW_H,
            alignment=ft.Alignment.CENTER,
            border_radius=ft.BorderRadius.all(CELL_RADIUS),
            bgcolor=bgcolor,
            on_click=lambda _e, k=kind, v=value: self.set_time(**{k: v}),
            on_hover=lambda e, kk=key: self._hover_key(kk, _truthy(e.data)),
            content=ft.Text(
                f"{value:02d}",
                size=TEXT_SIZE,
                color=color,
                weight=ft.FontWeight.W_600 if selected else ft.FontWeight.NORMAL,
            ),
        )

    def _time_arrow(self, kind: str, delta: int) -> ft.Control:
        """列上的 ▲ / ▼：按步长增减一格（环形）。"""
        return ft.Container(
            height=TIME_ARROW_H,
            alignment=ft.Alignment.CENTER,
            content=self._nav_button(
                f"t{kind}:{'up' if delta < 0 else 'down'}",
                ft.Icons.EXPAND_LESS if delta < 0 else ft.Icons.EXPAND_MORE,
                lambda: self._step_time(kind, delta),
                "上一格（滚轮同样可用）" if delta < 0 else "下一格（滚轮同样可用）",
            ),
        )

    def _time_block(self) -> ft.Control:
        """三列时间轮盘整体（高度与月历列一致）。"""
        return ft.Container(
            height=TIME_COL_H,
            padding=ft.Padding.symmetric(vertical=TIME_PAD_V),
            content=ft.Row(
                spacing=TIME_COL_GAP,
                controls=[self._time_column(k) for k in self._kinds],
            ),
        )

    # ------------------------------------------------------------------
    # 面板
    # ------------------------------------------------------------------
    def _panel_w(self) -> float:
        """面板宽 = 月历列 + 分隔线 + N 列时间轮盘（含边框）。"""
        cols = len(self._kinds)
        time_w = cols * TIME_COL_W + (cols - 1) * TIME_COL_GAP
        return PANEL_PAD * 2 + CAL_GRID_W + V_DIV_W + time_w + 2

    def _build_panel(self) -> ft.Control:
        """面板：``[月历 | 时间轮盘]`` + 分隔线 + 页脚。"""
        calendar = ft.Container(
            width=CAL_GRID_W,
            content=ft.Column(
                spacing=0,
                controls=[self._cal_header(), self._cal_body()],
            ),
        )
        vertical = ft.Container(
            width=1,
            height=TIME_COL_H,
            bgcolor=ft.Colors.OUTLINE_VARIANT,
            margin=ft.Padding.symmetric(horizontal=PANEL_PAD),
        )
        return self._panel_shell(
            self._panel_w(),
            ft.Column(
                spacing=0,
                controls=[
                    ft.Row(
                        spacing=0,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                        controls=[calendar, vertical, self._time_block()],
                    ),
                    self._divider(),
                    self._footer(),
                ],
            ),
        )

    def _footer(self) -> ft.Control:
        """页脚：``今天 此刻`` … ``清除 完成``。"""
        controls: list[ft.Control] = [
            self._link_button(
                "today",
                "今天",
                self._pick_today,
                enabled=self._today_enabled(),
            ),
            self._link_button("now", "此刻", self._pick_now),
            ft.Container(expand=True),
        ]
        if self.show_clear_link:
            controls.append(self._link_button("clear", "清除", self.clear))
        controls.append(self._link_button("done", "完成", self.close))
        return ft.Container(
            height=FOOTER_H,
            padding=ft.Padding.only(left=2, right=2),
            content=ft.Row(
                spacing=2,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=controls,
            ),
        )

    def _today_enabled(self) -> bool:
        """「今天」是否可用（今天这一天的任意时刻在范围内）。"""
        today = datetime.date.today()
        return self._min.date() <= today <= self._max.date()

    def _pick_today(self) -> None:
        """「今天」：只换日期、保留时间。"""
        today = datetime.date.today()
        base = self.value or datetime.datetime.now()
        self._assign(base.replace(year=today.year, month=today.month, day=today.day))

    def _pick_now(self) -> None:
        """「此刻」：日期与时间都取现在。"""
        self._assign(datetime.datetime.now())

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    @ft.component
    def ui(self) -> ft.Control:
        """构建日期时间选择器 UI。"""
        page = ft.context.page
        field = self._build_field(
            self._text_field(),
            ft.Icon(
                ft.Icons.EDIT_CALENDAR,
                size=18,
                color=ft.Colors.OUTLINE if self.disabled else ft.Colors.ON_SURFACE_VARIANT,
            ),
        )
        panel = self._build_panel()
        panel_w, panel_h = self._panel_w(), self._panel_h()
        floating = self._should_float(page)

        if floating:
            # 面板在浮层里，布局只占折叠态的高度。
            body: ft.Control = field
        elif self.is_open and not self.disabled:
            # 降级：面板流内展开，下方内容随之下移。
            body = ft.Column(controls=[field, panel], spacing=PANEL_GAP)
        else:
            body = field

        left, top, bottom = place_panel(
            page, self._anchor, self._field_h, panel_w, panel_h
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

    def _panel_h(self) -> float:
        """面板高 = 月历列 + 分隔线 + 页脚（与 ``DateInput`` 完全一致）。"""
        return PANEL_PAD * 2 + 2 + TIME_COL_H + 1 + FOOTER_H

    # ---- 输入框 ----

    def _text_field(self) -> ft.Control:
        """框内文本。收起态 ``ignore_pointers`` —— 让点击穿透到外层手势。"""
        return ft.TextField(
            value=self._text if self._text is not None else self.display_text,
            border=ft.NoInputBorder(),
            filled=False,
            dense=True,
            text_size=TEXT_SIZE,
            color=self._fg,
            content_padding=ft.Padding.symmetric(vertical=6),
            hint_text=self.placeholder,
            hint_style=ft.TextStyle(size=TEXT_SIZE, color=ft.Colors.OUTLINE),
            keyboard_type=ft.KeyboardType.DATETIME,
            read_only=self.disabled,
            # 关键：收起（或禁用）时不吃指针事件，否则外层 GestureDetector 拿不到点击。
            ignore_pointers=self.disabled or not self.is_open,
            on_change=None if self.disabled else self._on_text_change,
            on_submit=None if self.disabled else self._on_text_submit,
            on_blur=None if self.disabled else self._on_text_blur,
        )

    def _on_text_change(self, e: ft.ControlEvent) -> None:
        """键入过程中即时解析：合法就落地并广播，全程不打断输入。

        "合法就落地"（同 Element Plus）—— 敲到哪算到哪，失焦不会丢；敲到非法
        内容时保持上一个合法值，框体不标红（还在输入中，不算错）。
        """
        text = e.data or ""
        self._text = text
        self._invalid = False
        parsed = self._parse(text)
        if parsed is not None and parsed != self.value:
            self.value = parsed
            self._view_year, self._view_month = parsed.year, parsed.month
            self._emit()
            return
        self.notify()  # type: ignore[attr-defined]

    def _on_text_submit(self, e: ft.ControlEvent) -> None:
        """回车提交：合法则选中并收起，非法则原样还原并标红。"""
        raw = self._text if self._text is not None else self.display_text
        parsed = self._parse(raw)
        self._text = None
        if parsed is not None:
            self._invalid = False
            self.select(parsed)
            return
        if self.value is None:
            # 本来就是空的，敲了半截又回车 —— 没东西可还原，也不算错。
            self._invalid = False
            self.notify()  # type: ignore[attr-defined]
            return
        self._invalid = True
        self.notify()  # type: ignore[attr-defined]

    def _on_text_blur(self, e: ft.ControlEvent) -> None:
        """失焦即放弃未提交的键入（回到格式化值）。"""
        if self._text is None:
            return
        self._text = None
        self.notify()  # type: ignore[attr-defined]

    def _parse(self, text: str | None) -> datetime.datetime | None:
        """解析键入文本 → 规整 → 钳制；不在可选范围内返回 ``None``。"""
        base = self.value or datetime.datetime.now()
        parsed = _parse_datetime(text, base)
        if parsed is None:
            return None
        parsed = self._normalize(parsed)
        return parsed if self._accepts(parsed) else None


@ft.component
def App():
    """DateTimeInput 组件运行示例。"""
    start = DateTimeInput(
        label="开始时间",
        is_required=True,
        value=datetime.datetime(2026, 9, 26, 9, 30),
        on_change=lambda v: print(f"[DateTimeInput] 选中 {v}"),
    )
    end = DateTimeInput(
        label="结束时间",
        value=datetime.datetime(2026, 12, 31, 23, 59),
        minute_step=5,
        is_vertical=True,
    )
    precise = DateTimeInput(
        label="含秒",
        with_seconds=True,
        second_step=5,
        minute_step=15,
    )
    bounded = DateTimeInput(
        label="会议窗口",
        value=datetime.datetime(2026, 9, 10, 14, 0),
        min_datetime=datetime.datetime(2026, 9, 5, 8, 0),
        max_datetime=datetime.datetime(2026, 9, 20, 18, 0),
    )
    frozen = DateTimeInput(
        label="只读",
        value=datetime.datetime(2026, 1, 1, 0, 0),
        disabled=True,
        clearable=False,
    )

    return ft.Column(
        controls=[
            ft.Text("DateTimeInput 日期时间选择器", size=20, weight=ft.FontWeight.BOLD),
            ft.Text(
                "点框体挂出「月历 + 时/分/秒轮盘」（悬浮、不推下方内容）；"
                "点日期不收起，可接着调时间，滚轮或 ▲▼ 步进，点「完成」收起",
                size=13,
                color="#6b7280",
            ),
            ft.Divider(),
            start.ui(),
            ft.Divider(),
            end.ui(),
            ft.Divider(),
            precise.ui(),
            ft.Divider(),
            bounded.ui(),
            ft.Divider(),
            frozen.ui(),
            ft.Divider(),
            ft.Button(
                content="打印当前值",
                on_click=lambda _: print(
                    f"{start.value} / {end.value} / {precise.value} / "
                    f"{bounded.value} / {frozen.value}"
                ),
            ),
        ],
        spacing=14,
    )


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
