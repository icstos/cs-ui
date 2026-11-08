"""热力图 (Heatmap) —— 日历网格版。

参考 Naive UI ``n-heatmap`` / GitHub 贡献墙：把一段时间铺成"若干列 × 7 行"的
方格，用颜色深浅表达"这一天有多活跃"。一年 365 天的疏密，一眼看完。

五条实现取舍（改前先读）：

1. **顺序色阶自带浅深两套**。M3 的 ``ColorScheme`` 是"语义角色"，推不出"由浅
   到深的 4 级绿"，所以色阶按主题写死（:data:`COLOR_THEMES`）。但**底板色**
   （空白天）不走色阶，用 ``overlay()`` —— 角色 + 透明度由 Flutter 按当前主题
   解析，明暗自动正确。
2. **一个手势控件，不是 371 个**。整片网格只挂一个 :class:`flet.GestureDetector`，
   用 ``local_position`` 反算格子（``col = x // 步距``）。每格各挂一个手势会让
   控件树翻倍，鼠标划过时还要逐个命中测试。
3. **只在"跨格"时重绘**。悬停事件按像素触发，每来一次就 ``notify()`` 的话，
   鼠标划过一行会触发上百次重绘。这里比较格子索引，**变了才重绘**。
4. **网格构建一次就留着**。371 个格子重建一次约 6ms（本机实测），而悬停只应该
   换一个气泡。所以网格 / 标签按"数据指纹 + 几何参数"缓存，悬停时 flet 的 diff
   看到同一个控件对象直接跳过，渲染成本从"整个热力图"降到"一个气泡"。
5. **tooltip 用 ``bottom`` 锚定**。气泡高度随文案行数变化，用 ``top`` 锚定会向
   下方长出去盖住格子；``bottom`` 锚定则**向上生长**，第一行（上方没空间）改用
   ``top`` 往下放。

用法::

    heatmap = Heatmap(
        data=[
            HeatmapItem(date(2026, 9, 26), 12),
            {"date": date(2026, 9, 27), "value": 3},
            (date(2026, 9, 28), 0),
        ],
        color_theme="green",
        size="medium",
    )
    ...
    Column([heatmap.ui()])

``data`` 支持三种写法：:class:`HeatmapItem`、``dict``（认 ``date`` / ``day`` /
``timestamp`` 与 ``value``）、``(date, value)`` 二元组。
"""

from __future__ import annotations

import datetime as _dt
import math
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import flet as ft

from ui.core.doc import Api, Example, Spec, info, run, tip, warn
from ui.core.empty import empty_line
from ui.core.format import first_weekday as locale_first_weekday
from ui.core.format import format_date, format_number, month_name, weekday_names
from ui.core.i18n import t, use_t
from ui.core.theme import theme_state, use_theme
from ui.core.tokens import FONT_SIZE, SPACE, overlay

__all__ = ["COLOR_THEMES", "Heatmap", "HeatmapItem"]

# ---------------------------------------------------------------------------
# 视觉常量
# ---------------------------------------------------------------------------
#: ``size`` → (格子边长, 横向间距, 纵向间距, 圆角, 标签字号)
SIZES: dict[str, tuple[int, int, int, int, float]] = {
    "small": (10, 3, 3, 2, 9.5),
    "medium": (12, 4, 4, 3, FONT_SIZE["caption"]),
    "large": (16, 5, 5, 4, 12.0),
}

LABEL_PAD = 8  # 星期标签与网格之间的空隙
LABEL_GAP = 6  # 相邻月份标签之间至少留的空隙
MONTH_GAP = 5  # 月份标签行与网格之间的空隙
FOOTER_GAP = 10  # 图例行与网格之间的空隙
TIP_GAP = 6  # tooltip 与格子之间的空隙
TIP_PAD_H = 9  # tooltip 左右内边距
TIP_MIN_W = 72
TIP_MAX_W = 260
TIP_ROOM_UP = 40  # 单元格顶边小于这个值就往下弹气泡
SEVEN = 7

#: 顺序色阶：``light`` / ``dark`` 各一套，由浅到深。
#: 为什么写死：M3 没有"第 3 级绿"这种角色，只能由主题给出具体值。
COLOR_THEMES: dict[str, dict[str, tuple[str, ...]]] = {
    "green": {
        "light": ("#9BE9A8", "#40C463", "#30A14E", "#216E39"),
        "dark": ("#0E4429", "#006D32", "#26A641", "#39D353"),
    },
    "blue": {
        "light": ("#BAE0FF", "#69B1FF", "#1677FF", "#0958D9"),
        "dark": ("#102A43", "#0C4A8A", "#1677FF", "#69B1FF"),
    },
    "orange": {
        "light": ("#FFE0B2", "#FFC069", "#FA8C16", "#D46B08"),
        "dark": ("#3B2308", "#7C4A0B", "#FA8C16", "#FFC069"),
    },
    "purple": {
        "light": ("#E9D8FD", "#C4A0F5", "#8B5CF6", "#6B21A8"),
        "dark": ("#2A1840", "#4C2A80", "#8B5CF6", "#C4A0F5"),
    },
    "red": {
        "light": ("#FFD8D6", "#FFA39E", "#F5222D", "#A8071A"),
        "dark": ("#3D0F12", "#7A1218", "#F5222D", "#FFA39E"),
    },
}

DEFAULT_THEME = "green"
DEFAULT_SIZE = "medium"
#: 空白天底板色 —— 角色 + 透明度，明暗自适应
DEFAULT_MIN_COLOR: ft.ColorValue = overlay(0.08)


# ---------------------------------------------------------------------------
# 数据项与解析
# ---------------------------------------------------------------------------
@dataclass
class HeatmapItem:
    """一天的数据。

    Args:
        date: 日期（只取"哪一天"，时分秒忽略）。
        value: 数值。``None`` 与 ``0`` 等价于"空白"，用底板色画。
        data: 原始业务对象，回调里用 ``item.data`` 取回。
    """

    date: _dt.date
    value: float | None = None
    data: Any = None

    @property
    def has_value(self) -> bool:
        """是否有有效数值（> 0）。"""
        return self.value is not None and self.value > 0


def _as_date(raw: Any) -> _dt.date:
    """把 ``date`` / ``datetime`` / ISO 字符串 / 秒级·毫秒级时间戳折成 ``date``。"""
    if isinstance(raw, _dt.datetime):
        return raw.date()
    if isinstance(raw, _dt.date):
        return raw
    if isinstance(raw, str):
        return _dt.date.fromisoformat(raw[:10])
    if isinstance(raw, (int, float)):
        # > 1e11 视为毫秒：秒级时间戳要到公元 5138 年才这么大
        seconds = raw / 1000 if raw > 1e11 else raw
        return _dt.datetime.fromtimestamp(seconds).date()  # noqa: DTZ006
    raise TypeError(f"无法把 {raw!r} 解析成日期")


def _as_item(raw: HeatmapItem | Mapping[str, Any] | Sequence[Any]) -> HeatmapItem:
    """把各种入参形状折成 :class:`HeatmapItem`。"""
    if isinstance(raw, HeatmapItem):
        return raw
    if isinstance(raw, Mapping):
        day = raw.get("date") or raw.get("day") or raw.get("timestamp")
        if day is None:
            raise ValueError(f"数据项缺少 date / day / timestamp：{raw!r}")
        return HeatmapItem(_as_date(day), raw.get("value"), raw.get("data"))
    if isinstance(raw, Sequence) and len(raw) == 2:
        return HeatmapItem(_as_date(raw[0]), raw[1])
    raise TypeError(f"无法把 {raw!r} 当作热力图数据项")


def _text_width(text: str, size: float) -> float:
    """粗估一行文本的像素宽：CJK 按字号，拉丁按 0.6 倍字号。

    只用于给 tooltip 定宽 —— 估小了文字换行（还能看），估大了气泡偏宽。
    """
    total = 0.0
    for ch in text:
        total += size if ord(ch) > 0x2E7F else size * 0.6
    return total


# ---------------------------------------------------------------------------
# 组件
# ---------------------------------------------------------------------------
@ft.observable
@dataclass
class Heatmap:
    """日历热力图。

    Args:
        data: 数据项序列，元素可为 :class:`HeatmapItem` / ``dict`` / 二元组。
        start: 起始日期，``None`` 取数据最早的一天。
        end: 结束日期，``None`` 取数据最晚的一天。显式给值可以画出"数据没覆盖
            到的空白区"（例如只看今年，而今年还没过完）。
        color_theme: 内置色阶：``green`` / ``blue`` / ``orange`` / ``purple`` /
            ``red``。
        active_colors: 自定义色阶，由浅到深；给了就盖过 ``color_theme``。
        minimum_color: 空白天的底板色，``None`` 用半透明前景色（明暗自适应）。
        value_range: ``(最小, 最大)`` 显式色阶区间；``None`` 由数据推 —— 下限取
            最小的正值、上限取最大值。显式给值可让多张热力图共用一把尺子。
        size: ``small`` / ``medium`` / ``large``。
        first_day_of_week: 每周首日，``0`` = 周一 … ``6`` = 周日。``None`` 跟随
            语言包（中文周一、英文周日）。
        show_month_labels: 顶部月份标签。
        show_week_labels: 左侧星期标签。纵向间距够宽（``large``）时显示全部 7 个，
            否则隔行显示 3 个 —— 挤在一起谁都读不清。
        show_legend: 底部"少 → 多"色阶图例。
        fill_calendar_leading: 首尾未被数据覆盖的格子是否也填底板色。
            ``False`` 留透明（默认，边界更干净）；``True`` 补成完整网格。
        tooltip: 悬停气泡，**默认开** —— 没有反馈的热力图等于一张装饰图。
        tooltip_formatter: 自定义气泡文案，入参 :class:`HeatmapItem`。
        footer: 左下角自定义区域（通常放统计），与网格左边缘对齐。
        x_gap / y_gap: 单独覆盖横向 / 纵向间距，``None`` 用尺寸档位的值。
        width: 组件宽度，``None`` 跟随内容。
        on_cell_click: 点击格子回调，入参 :class:`HeatmapItem`。

    Notes:
        宽度由"列数 × 步距"决定，**不参与父容器的弹性分配** —— 格子必须等比，
        被拉伸就变形了。窄容器里换 ``size="small"``，或在外层套一层可横向滚动的
        容器；组件自己不滚动，因为月份标签、星期标签、网格是三行对齐的，
        内部滚动会让它们不同步。
    """

    data: Iterable[HeatmapItem | Mapping[str, Any] | Sequence[Any]] = ()
    start: _dt.date | None = None
    end: _dt.date | None = None
    color_theme: str = DEFAULT_THEME
    active_colors: Sequence[str] | None = None
    minimum_color: ft.ColorValue | None = None
    value_range: tuple[float, float] | None = None
    size: str = DEFAULT_SIZE
    first_day_of_week: int | None = None
    show_month_labels: bool = True
    show_week_labels: bool = True
    show_legend: bool = True
    fill_calendar_leading: bool = False
    tooltip: bool = True
    tooltip_formatter: Callable[[HeatmapItem], str] | None = None
    footer: ft.Control | None = None
    x_gap: int | None = None
    y_gap: int | None = None
    width: int | float | None = None
    on_cell_click: Callable[[HeatmapItem], None] | None = None

    # ---- 运行期状态（下划线开头：不序列化，靠 notify() 重绘）-------------
    _days: dict[_dt.date, HeatmapItem] = field(
        default_factory=dict, init=False, repr=False
    )
    _first: int = field(default=0, init=False, repr=False)
    _cell: int = field(default=12, init=False, repr=False)
    _gap_x: int = field(default=4, init=False, repr=False)
    _gap_y: int = field(default=4, init=False, repr=False)
    _radius: int = field(default=3, init=False, repr=False)
    _label_size: float = field(default=11.0, init=False, repr=False)
    _ramp: tuple[str, ...] = field(default=(), init=False, repr=False)
    _min_color: ft.ColorValue = field(default=DEFAULT_MIN_COLOR, init=False, repr=False)
    _origin: _dt.date = field(default=_dt.date(1970, 1, 1), init=False, repr=False)
    _span: tuple[_dt.date, _dt.date] = field(
        default=(_dt.date(1970, 1, 1), _dt.date(1970, 1, 1)), init=False, repr=False
    )
    _range: tuple[float, float] = field(default=(0.0, 1.0), init=False, repr=False)
    _cols: int = field(default=0, init=False, repr=False)
    _gutter: int = field(default=0, init=False, repr=False)
    _grid_w: int = field(default=0, init=False, repr=False)
    _grid_h: int = field(default=0, init=False, repr=False)
    _hover: tuple[int, int] | None = field(default=None, init=False, repr=False)
    _stamp: tuple[Any, ...] | None = field(default=None, init=False, repr=False)
    _grid: ft.Control | None = field(default=None, init=False, repr=False)
    _header: ft.Control | None = field(default=None, init=False, repr=False)
    _labels: ft.Control | None = field(default=None, init=False, repr=False)
    _footer: ft.Control | None = field(default=None, init=False, repr=False)

    # =====================================================================
    # 对外查询
    # =====================================================================
    def stats(self) -> dict[str, float]:
        """统计这段时间：``days`` / ``filled`` / ``blank`` / ``peak`` /
        ``mean`` / ``total``。

        ``mean`` 只对**有值的天**求平均（把空白天算进去只会毫无意义地拉低均值）。
        """
        self._prepare()
        values = [it.value for it in self._days.values() if it.has_value]
        total = float(sum(values))
        filled = len(values)
        days = (self._span[1] - self._span[0]).days + 1 if self._days else 0
        return {
            "days": float(max(0, days)),
            "filled": float(filled),
            "blank": float(max(0, days - filled)),
            "peak": float(max(values)) if values else 0.0,
            "mean": total / filled if filled else 0.0,
            "total": total,
        }

    def item_at(self, day: _dt.date) -> HeatmapItem | None:
        """取某一天的数据项（不在数据里则 ``None``）。"""
        self._prepare()
        return self._days.get(day)

    def invalidate(self) -> None:
        """丢弃缓存，下次 :meth:`ui` 重建网格。

        原地改 ``data`` 里的数值（同一个 list、同一个对象）时 flet 收不到通知，
        改完调这个再 ``page.update()`` 即可。
        """
        self._stamp = None
        self._grid = None

    # =====================================================================
    # 准备（解析 + 几何 + 色阶）
    # =====================================================================
    def _prepare(self) -> None:
        """把数据 / 参数折成"一张可以直接画的表"，结果按指纹缓存。

        顺序有讲究：色阶与区间**必须先算**，因为它们是几何指纹的一部分；反过来
        先比指纹再算，指纹里就会一直是上一轮的空色阶，导致每帧都重建。
        """
        self._measure()
        self._days = self._normalize()
        self._compute_range()

        stamp = (self._data_sig(self._days), *self._geometry_key())
        if self._stamp == stamp and self._grid is not None:
            return
        self._stamp = stamp
        self._hover = None
        self._grid = self._header = self._labels = self._footer = None
        self._compute_grid()

    def _measure(self) -> None:
        """尺寸档位与每周首日。每帧都要算，但它只碰常量。"""
        cell, gx, gy, radius, label_size = SIZES.get(self.size, SIZES[DEFAULT_SIZE])
        self._cell = cell
        self._gap_x = gx if self.x_gap is None else max(1, int(self.x_gap))
        self._gap_y = gy if self.y_gap is None else max(1, int(self.y_gap))
        self._radius = radius
        self._label_size = label_size
        self._first = (
            locale_first_weekday()
            if self.first_day_of_week is None
            else int(self.first_day_of_week) % SEVEN
        )

    def _normalize(self) -> dict[_dt.date, HeatmapItem]:
        """入参 → ``{date: item}``。同一天给了多次时后者覆盖前者。"""
        days: dict[_dt.date, HeatmapItem] = {}
        for raw in self.data:
            item = _as_item(raw)
            days[item.date] = item
        return days

    @staticmethod
    def _data_sig(days: Mapping[_dt.date, HeatmapItem]) -> tuple[Any, ...]:
        """数据指纹：日期 + 数值的滚动哈希。O(n) 整数运算，比重建网格便宜两个量级。"""
        sig = 0
        for day, item in days.items():
            value = int((item.value or 0) * 1000)
            sig = (sig * 1000003 + day.toordinal() * 1000003 + value) & 0x7FFFFFFFFFFF
        return (len(days), sig)

    def _geometry_key(self) -> tuple[Any, ...]:
        """影响"格子怎么摆"的参数。"""
        return (
            self.start,
            self.end,
            self.size,
            self.x_gap,
            self.y_gap,
            self.first_day_of_week,
            self.fill_calendar_leading,
            tuple(self._ramp),
            self._min_color,
            self._range,
            theme_state().is_dark,
        )

    def _compute_range(self) -> None:
        """色阶（随主题）与统计区间。"""
        self._ramp = self._resolve_ramp()
        self._min_color = (
            self.minimum_color if self.minimum_color is not None else DEFAULT_MIN_COLOR
        )
        self._range = self._resolve_range()

    def _resolve_ramp(self) -> tuple[str, ...]:
        """取色阶：``active_colors`` > 内置主题 > 默认绿。

        读的是 :func:`theme_state` 单例而不是 ``use_theme()`` —— 后者必须在组件
        上下文里调用，而 :meth:`stats` 之类的公开方法也要能算。
        """
        if self.active_colors:
            return tuple(self.active_colors)
        theme = COLOR_THEMES.get(self.color_theme) or COLOR_THEMES[DEFAULT_THEME]
        return theme["dark" if theme_state().is_dark else "light"]

    def _resolve_range(self) -> tuple[float, float]:
        """色阶区间：显式值 > 由数据推（下限取最小正值）。"""
        if self.value_range:
            lo, hi = float(self.value_range[0]), float(self.value_range[1])
            return (lo, hi) if hi > lo else (lo, lo + 1.0)
        values = [it.value for it in self._days.values() if it.has_value]
        if not values:
            return (0.0, 1.0)
        lo, hi = float(min(values)), float(max(values))
        return (lo, hi) if hi > lo else (lo, lo + 1.0)

    def _compute_grid(self) -> None:
        """算列数、几何尺寸与左侧标签宽度。"""
        first = self.start or (
            min(self._days) if self._days else _dt.datetime.now(tz=_dt.UTC).date()
        )
        last = self.end or (max(self._days) if self._days else first)
        if last < first:
            first, last = last, first
        self._span = (first, last)
        # 起点回退到本周第一天、终点推到本周最后一天，保证每列都是整 7 格
        self._origin = first - _dt.timedelta(
            days=(first.weekday() - self._first) % SEVEN
        )
        tail = last + _dt.timedelta(days=(self._first + 6 - last.weekday()) % SEVEN)
        self._cols = max(1, (tail - self._origin).days // SEVEN + 1)
        self._grid_w = self._cols * self._cell + (self._cols - 1) * self._gap_x
        self._grid_h = SEVEN * self._cell + (SEVEN - 1) * self._gap_y
        self._gutter = 0 if not self.show_week_labels else self._week_gutter()

    def _week_gutter(self) -> int:
        """左侧星期标签列宽：按实际要显示的标签估宽，中英文都放得下。"""
        names = weekday_names()
        width = max(
            _text_width(names[(self._first + row) % SEVEN], self._label_size)
            for row in self._week_rows()
        )
        return int(width) + LABEL_PAD

    def _week_rows(self) -> list[int]:
        """要画标签的行号。纵向够宽就全画，否则隔行画 3 个。"""
        pitch = self._cell + self._gap_y
        return list(range(SEVEN)) if pitch >= 20 else [1, 3, 5]

    # =====================================================================
    # 取值 → 颜色
    # =====================================================================
    def _level(self, item: HeatmapItem | None) -> int:
        """数值 → 色阶层级：``0`` 是底板色，``1..n`` 由浅到深。"""
        if item is None or not item.has_value:
            return 0
        n = len(self._ramp)
        lo, hi = self._range
        ratio = min(1.0, max(0.0, (float(item.value) - lo) / (hi - lo)))
        return min(n, 1 + int(ratio * (n - 1) + 1e-9))

    def _color_of(self, item: HeatmapItem | None) -> ft.ColorValue | None:
        """格子颜色；``None`` 表示透明（数据区间之外的空气格）。"""
        if item is None:
            return None
        level = self._level(item)
        return self._min_color if level == 0 else self._ramp[level - 1]

    def _day_at(self, col: int, row: int) -> _dt.date:
        return self._origin + _dt.timedelta(days=col * SEVEN + row)

    def _painted(self, day: _dt.date) -> bool:
        """这一天是否要画（``False`` = 透明的空气格，只占位不显示）。"""
        if self.fill_calendar_leading:
            return True
        return self._span[0] <= day <= self._span[1]

    # =====================================================================
    # 渲染：网格
    # =====================================================================
    def _cell_control(self, col: int, row: int) -> ft.Control:
        day = self._day_at(col, row)
        item = self._days.get(day)
        return ft.Container(
            width=self._cell,
            height=self._cell,
            bgcolor=self._color_of(item) if self._painted(day) else None,
            border_radius=self._radius,
        )

    def _build_grid(self) -> ft.Control:
        return ft.Row(
            spacing=self._gap_x,
            tight=True,
            controls=[
                ft.Column(
                    spacing=self._gap_y,
                    tight=True,
                    controls=[self._cell_control(col, row) for row in range(SEVEN)],
                )
                for col in range(self._cols)
            ],
        )

    def _month_labels(self) -> list[tuple[int, str]]:
        """月份标签：``[(起始列, 文案)]``，已解决"挤在一起"的冲突。"""
        pitch = self._cell + self._gap_x
        raw: list[tuple[int, str, bool]] = []
        prev_month: int | None = None
        for col in range(self._cols):
            day = self._day_at(col, 0)
            if day.month == prev_month:
                continue
            prev_month = day.month
            starts_before = _dt.date(day.year, day.month, 1) < self._span[0]
            raw.append((col, month_name(day.month, short=True), starts_before))

        # 首列常常是"残月"（只有几天在视野里），且紧挨着下一个整月的标签。
        # 两者挤在一起时留下整月 —— 用户要看的是"这几个月"，残月标签没有信息量。
        if len(raw) >= 2 and raw[0][2]:
            gap = (
                raw[0][0] * pitch + _text_width(raw[0][1], self._label_size) + LABEL_GAP
            )
            if raw[1][0] * pitch < gap:
                raw.pop(0)

        kept: list[tuple[int, str]] = []
        next_free = 0.0
        for col, label, _ in raw:
            x = col * pitch
            if x < next_free:
                continue  # 上一个标签还没结束，这个让位
            kept.append((col, label))
            next_free = x + _text_width(label, self._label_size) + LABEL_GAP
        return kept

    def _build_header(self) -> ft.Control:
        """月份标签行：标签宽度按"到下一个标签为止"的列数给，不做裁剪。"""
        pitch = self._cell + self._gap_x
        kept = self._month_labels()
        cells: list[ft.Control] = []
        for i, (col, label) in enumerate(kept):
            end = kept[i + 1][0] if i + 1 < len(kept) else self._cols
            cells.append(
                ft.Container(
                    width=max(1, (end - col) * pitch - self._gap_x),
                    height=self._label_size + 4,
                    # 不裁剪：最后一列的标签要允许溢出到网格右侧
                    clip_behavior=ft.ClipBehavior.NONE,
                    alignment=ft.Alignment.TOP_LEFT,
                    content=ft.Text(
                        label,
                        size=self._label_size,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                        no_wrap=True,
                    ),
                )
            )
        return ft.Row(spacing=self._gap_x, tight=True, controls=cells)

    def _build_labels(self) -> ft.Control:
        """左侧星期标签列：行高与网格一一对应，文字靠右贴着网格。"""
        names = weekday_names()
        shown = set(self._week_rows())
        return ft.Column(
            spacing=self._gap_y,
            tight=True,
            controls=[
                ft.Container(
                    width=self._gutter - LABEL_PAD,
                    height=self._cell,
                    alignment=ft.Alignment.CENTER_RIGHT,
                    content=ft.Text(
                        names[(self._first + row) % SEVEN] if row in shown else "",
                        size=self._label_size,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                        no_wrap=True,
                    ),
                )
                for row in range(SEVEN)
            ],
        )

    # =====================================================================
    # 渲染：悬停
    # =====================================================================
    def _hit(self, x: float, y: float) -> tuple[int, int] | None:
        """坐标 → 格子。落在间隙里归给左 / 上那一格（人手本来就不精确）。"""
        if self._cols <= 0 or x < 0 or y < 0 or x >= self._grid_w or y >= self._grid_h:
            return None
        col = int(x // (self._cell + self._gap_x))
        row = int(y // (self._cell + self._gap_y))
        if col >= self._cols or row >= SEVEN:
            return None
        return (col, row)

    def _on_hover(self, e: Any) -> None:
        pos = e.local_position
        hit = self._hit(pos.x or 0, pos.y or 0)
        if hit == self._hover:
            return  # 关键：同一格内移动不重绘
        self._hover = hit
        self.notify()  # type: ignore[attr-defined]

    def _on_exit(self, _e: Any) -> None:
        if self._hover is None:
            return
        self._hover = None
        self.notify()  # type: ignore[attr-defined]

    def _on_tap(self, e: Any) -> None:
        """点击格子。

        用事件里的 ``local_position`` 反算，而不是读 :attr:`_hover` —— 触屏
        没有悬停，只靠 hover 记下的坐标，第一次点会落空。
        """
        if self.on_cell_click is None:
            return
        pos = getattr(e, "local_position", None)
        hit = self._hit(pos.x or 0, pos.y or 0) if pos is not None else self._hover
        if hit is None:
            return
        col, row = hit
        item = self._days.get(self._day_at(col, row))
        if item is not None:
            self.on_cell_click(item)

    def _tooltip_text(self, item: HeatmapItem | None, day: _dt.date) -> str:
        if self.tooltip_formatter is not None:
            return self.tooltip_formatter(item or HeatmapItem(day))
        value = format_number(item.value) if item and item.has_value else "0"
        return t("ui.heatmap.tooltip", date=format_date(day), value=value)

    def _build_tooltip(self) -> ft.Control | None:
        """悬停气泡。不悬停时返回 ``None`` —— 装配时会被过滤掉。"""
        if not self.tooltip or self._hover is None:
            return None
        col, row = self._hover
        day = self._day_at(col, row)
        if not self._painted(day):
            return None  # 数据区间外的空气格：不弹
        item = self._days.get(day)

        text = self._tooltip_text(item, day)
        size = FONT_SIZE["caption"]
        width = min(
            TIP_MAX_W, max(TIP_MIN_W, int(_text_width(text, size)) + TIP_PAD_H * 2)
        )

        center_x = col * (self._cell + self._gap_x) + self._cell / 2
        left = min(max(0, int(center_x - width / 2)), max(0, self._grid_w - width))
        cell_top = row * (self._cell + self._gap_y)

        tip = ft.Container(
            width=width,
            bgcolor=ft.Colors.INVERSE_SURFACE,
            border_radius=6,
            padding=ft.Padding.symmetric(horizontal=TIP_PAD_H, vertical=4),
            left=left,
            content=ft.Text(
                text,
                size=size,
                color=ft.Colors.ON_INVERSE_SURFACE,
                text_align=ft.TextAlign.CENTER,
            ),
        )
        # 第一行上方没空间 → 往下放；其余用 bottom 锚定，气泡向上生长
        if cell_top < TIP_ROOM_UP:
            tip.top = cell_top + self._cell + TIP_GAP
        else:
            tip.bottom = self._grid_h - cell_top + TIP_GAP
        return tip

    # =====================================================================
    # 渲染：图例 / 页脚
    # =====================================================================
    def _build_legend(self) -> ft.Control:
        return ft.Row(
            spacing=4,
            tight=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(
                    t("ui.heatmap.less"),
                    size=FONT_SIZE["caption"],
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
                *[
                    ft.Container(
                        width=self._cell,
                        height=self._cell,
                        bgcolor=color,
                        border_radius=self._radius,
                    )
                    for color in (self._min_color, *self._ramp)
                ],
                ft.Text(
                    t("ui.heatmap.more"),
                    size=FONT_SIZE["caption"],
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
            ],
        )

    def _build_footer(self) -> ft.Control | None:
        if self.footer is None and not self.show_legend:
            return None
        return ft.Container(
            # 宽度钉死成"网格宽"：不钉的话父容器会把它拉满，图例就飘到卡片右边缘
            width=self._gutter + self._grid_w,
            padding=ft.Padding.only(left=self._gutter, top=FOOTER_GAP),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    self.footer or ft.Container(),
                    self._build_legend() if self.show_legend else ft.Container(),
                ],
            ),
        )

    # =====================================================================
    # 装配
    # =====================================================================
    @ft.component
    def ui(self) -> ft.Control:
        """构建热力图。"""
        use_t()  # 订阅语言：月份 / 星期 / 图例文案跟着切
        use_theme()  # 订阅主题：色阶与底板色跟着切（_prepare 会读 theme_state）
        self._prepare()

        if not self._days:
            return empty_line(
                t("ui.heatmap.empty"),
                width=self.width,
                height=None,
                padding=ft.Padding.symmetric(vertical=24),
            )

        if self._grid is None:
            self._grid = self._build_grid()
            self._header = self._build_header() if self.show_month_labels else None
            self._labels = self._build_labels() if self.show_week_labels else None
            self._footer = self._build_footer()

        board = ft.Stack(
            width=self._grid_w,
            height=self._grid_h,
            controls=[
                ft.GestureDetector(
                    content=self._grid,
                    on_hover=self._on_hover,
                    on_exit=self._on_exit,
                    on_tap=self._on_tap,
                ),
                *(x for x in [self._build_tooltip()] if x is not None),
            ],
        )

        rows: list[ft.Control] = []
        if self.show_month_labels and self._header is not None:
            rows.append(
                ft.Row(
                    spacing=0,
                    tight=True,
                    controls=[
                        ft.Container(width=self._gutter),
                        ft.Container(
                            content=self._header,
                            padding=ft.Padding.only(bottom=MONTH_GAP),
                        ),
                    ],
                )
            )
        rows.append(
            ft.Row(
                spacing=LABEL_PAD if self.show_week_labels else 0,
                tight=True,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[x for x in (self._labels, board) if x is not None],
            )
        )
        if self._footer is not None:
            rows.append(self._footer)

        return ft.Container(
            width=self.width,
            content=ft.Column(spacing=0, tight=True, controls=rows),
        )


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
_MUTED = ft.Colors.ON_SURFACE_VARIANT

#: 一年份的起点：周一，364 天正好 52 整周，不会出现半截首列。
_YEAR_START = _dt.date(2025, 11, 3)
#: 半年份的起点（也是周一），用来演示尺寸档位。
_HALF_START = _dt.date(2026, 5, 4)


def _daily(start: _dt.date, days: int, *, scale: float = 1.0) -> list[HeatmapItem]:
    """造一段"像真的"数据：两段不同周期的起伏叠加，周末回落。

    用公式而不是 ``random``：每次渲染完全一样，文档截图与示例不会前后打架。
    """
    out: list[HeatmapItem] = []
    for offset in range(days):
        day = start + _dt.timedelta(days=offset)
        wave = 7.2 + 5.0 * math.sin(offset / 8.5) + 3.4 * math.sin(offset / 2.7 + 0.8)
        if day.weekday() >= 5:
            wave -= 4.2
        out.append(HeatmapItem(day, int(max(0, round(wave * scale)))))
    return out


def _caption(text: str) -> ft.Text:
    return ft.Text(text, size=FONT_SIZE["caption"], color=_MUTED)


def _summary(data: list[HeatmapItem]) -> str:
    """底部那行统计：有记录的天数、总量、峰值。"""
    values = [int(item.value or 0) for item in data]
    active = [value for value in values if value]
    return (
        f"{len(active)} 天有记录 · 共 {format_number(sum(values))} 次 · "
        f"峰值 {max(values) if values else 0}"
    )


@ft.component
def _year() -> ft.Control:
    """一年 52 列、small 档；底部左边是自己算的统计，右边是色阶图例。"""

    def build() -> Heatmap:
        data = _daily(_YEAR_START, 364)
        return Heatmap(data=data, size="small", footer=_caption(_summary(data)))

    return ft.use_memo(build, []).ui()


@ft.component
def _large() -> ft.Control:
    """半年、large 档：格子 16px，悬停气泡要等指针停在格子上才出现。"""
    hm = ft.use_memo(
        lambda: Heatmap(
            data=_daily(_HALF_START, 182),
            size="large",
            show_legend=False,
        ),
        [],
    )
    return hm.ui()


@ft.component
def _shared_scale() -> ft.Control:
    """两张图共用 value_range：颜色深浅可以直接横向比，不用换算。"""
    busy = Heatmap(
        data=_daily(_HALF_START, 182, scale=1.7),
        size="small",
        value_range=(0, 24),
        show_legend=False,
        footer=_caption("A 组 · 每天 0–24 次提交"),
    )
    quiet = Heatmap(
        data=_daily(_HALF_START, 182, scale=0.45),
        size="small",
        value_range=(0, 24),
        footer=_caption("B 组 · 同一把尺子"),
    )
    return ft.Column(spacing=SPACE["4"], controls=[busy.ui(), quiet.ui()])


# ---------------------------------------------------------------------------
# 示例源码（“查看代码”面板）
# ---------------------------------------------------------------------------
_YEAR_CODE = """heatmap = Heatmap(
    data=[HeatmapItem(date(2026, 9, 26), 12),      # dict / (date, value) 也认
          {"date": date(2026, 9, 27), "value": 3},
          (date(2026, 9, 28), 0)],
    size="small",
    footer=Text("320 天有记录 · 共 2,304 次"),     # 左下角放自己的统计
)

Column([heatmap.ui()])"""

_LARGE_CODE = """Heatmap(
    data=rows,
    size="large",          # 10 / 12 / 16 三档边长
    show_legend=False,
    tooltip_formatter=lambda item: f"{item.date} · {item.value} 次",
)"""

_SCALE_CODE = """# 同一把尺子：两张图颜色可以直接比
Heatmap(data=group_a, value_range=(0, 24), size="small")
Heatmap(data=group_b, value_range=(0, 24), size="small")

# 不给 value_range 时下限取最小正值、上限取最大值 —— 一张图自己看够用，
# 两张摆放一起就会各拉各的，深浅失去可比性。"""


# ---------------------------------------------------------------------------
# 组件说明
# ---------------------------------------------------------------------------
SPEC = Spec(
    name="Heatmap",
    summary="把一年铺成 7 行方格，用颜色深浅表示每天的量，像贡献墙。",
    definition=(
        "热力图是一张「日历形状」的分布图：每一列一周，上边是周一、下边是周日，"
        "格子深浅表示当天的数。它擅长回答「哪段时间密、哪段时间断了」，不擅长回答"
        "「周三到底是多少」—— 精确值要靠悬停气泡。所以它的取舍是格子尽量小、"
        "数量尽量多，让一年的疏密在一屏里扫完。"
    ),
    anatomy=[
        (
            "格子",
            "边长 10 / 12 / 16 三档（small / medium / large），数值落在 4 级色阶上，圆角 2–4。",
        ),
        (
            "空白格",
            "没有数据的那天用「前景色 + 8% 透明度」当底板，明暗自适应；start / end 之外的格子完全不画。",
        ),
        (
            "月份标签",
            "每个月第一列上方一个；两个标签挤在一起时让位，首列的残月标签直接丢掉。",
        ),
        (
            "星期标签",
            "左侧一列与格子逐行对齐；纵向步距不足 20px 时只画 3 个（隔行），挤在一起的标签谁都读不清。",
        ),
        (
            "悬停气泡",
            "日期 + 数值。第一行上方没空间就向下弹，其余向上生长 —— 不会盖住下一行。",
        ),
        ("图例", "底部「少 → 多」，左边留给 footer 放统计，两边分居。"),
    ],
    when=[
        "年度活跃度：提交、发布、登录、打卡，看疏密比看数字快",
        "需要暴露「哪一段时间断了」：空白与浅色本身就是信息",
        "数据天然是「每天一个数」，粒度为天",
    ],
    avoid=[
        "要精确比较某几天的值：格子不给数字，只能逐个悬停；用柱状图或折线图",
        "时段 / 小时分布：热力图的 7 行固定是星期，换粒度得自己拼格子",
        "只有十几天数据：一排格子读不出趋势，用 Sparkline 或直接列数字",
    ],
    examples=[
        Example(
            "一年",
            _year,
            hint="52 整周、small 档；底部左边是统计、右边是图例，悬停任意格子看当天数值。",
            code=_YEAR_CODE,
        ),
        Example(
            "放大格子",
            _large,
            hint="半年、large 档：格子 16px，星期标签能画全 7 个。",
            code=_LARGE_CODE,
        ),
        Example(
            "共用一把尺子",
            _shared_scale,
            hint="两组数据固定 value_range=(0, 24)，颜色深浅可以直接横向比。",
            code=_SCALE_CODE,
        ),
    ],
    api=[
        Api(
            "data",
            "Iterable[HeatmapItem | dict | tuple]",
            "()",
            "数据项；dict 认 date / day / timestamp 与 value",
        ),
        Api("start", "date | None", "None", "起始日；留空取数据最早的一天"),
        Api(
            "end",
            "date | None",
            "None",
            "结束日；显式给值可以画出数据没覆盖到的空白段",
        ),
        Api("color_theme", "str", "'green'", "green / blue / orange / purple / red"),
        Api(
            "value_range",
            "tuple[float, float] | None",
            "None",
            "固定色阶区间；多张图共用时传同一组值",
        ),
        Api("size", "str", "'medium'", "small / medium / large 三档格子边长"),
        Api(
            "tooltip_formatter",
            "Callable[[HeatmapItem], str] | None",
            "None",
            "自定义气泡文案，入参是当天的数据项",
        ),
        Api("footer", "Control | None", "None", "网格下方左侧的自定义区域，通常放统计"),
        Api(
            "on_cell_click",
            "Callable[[HeatmapItem], None] | None",
            "None",
            "点击有数据的格子时回调",
        ),
        Api(
            "stats()",
            "() -> dict[str, float]",
            "—",
            "只读统计：days / filled / peak / mean / total",
        ),
    ],
    notes=[
        tip(
            "悬停只重画一个气泡：网格与标签按「数据指纹 + 几何参数」缓存，指针在同一格里"
            "移动时连重绘都不发生。点击则用事件坐标反算格子、不读悬停位置 —— 触屏没有"
            "悬停，靠 hover 记下的坐标第一次点会落空。"
        ),
        warn(
            "data 请传 list / tuple。每帧都会把入参重新解析一遍，传生成器时第二次渲染就"
            "空了 —— 屏幕上表现为「图闪一下然后没了」。"
        ),
        info(
            "宽度由「列数 × 步距」定死，不参与父容器的弹性分配 —— 被拉伸格子就变形。"
            "窄了就降 size，或在外层套一个横向滚动容器；组件自己不滚，因为月份标签、"
            "星期标签、网格是三行对齐的。"
        ),
    ],
    tags=("热力图", "heatmap", "贡献图", "活跃度", "日历"),
)


if __name__ == "__main__":
    run(SPEC)
