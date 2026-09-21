"""图表组件共享的数据解析与配色工具。

本模块被 ``LineChart`` / ``BarChart`` / ``AreaChart`` / ``ScatterChart`` 复用，
统一了“Streamlit 风格”的数据入参语义：

- 字典列表: ``[{"x": 1, "y": 2}, ...]``
- 列字典: ``{"x": [1, 2, 3], "y": [4, 5, 6]}``
- 数值列表: ``[1, 2, 3, 4, 5]``（x 轴自动取 0..n-1）
- 元组/列表序列: ``[(1, 2), (2, 3), ...]``

x 轴同时支持**数值轴**与**分类轴**：当 x 列出现无法转为数值的取值
（如 ``["1月", "2月"]``）时，自动按下标定位，并由
:func:`resolve_x_labels` 提供原始标签供坐标轴显示。
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import cast

# 内置美观配色方案，供所有图表按序取用
CHART_COLORS = [
    "#1f6feb",  # 蓝色
    "#10b981",  # 绿色
    "#f59e0b",  # 橙色
    "#ef4444",  # 红色
    "#8b5cf6",  # 紫色
    "#ec4899",  # 粉色
    "#06b6d4",  # 青色
    "#f97316",  # 深橙
]

type Number = int | float
type DataRow = dict[str, Number] | tuple | list
type DataInput = (
    list[DataRow]
    | dict[str, list[Number]]
    | list[Number]
    | tuple[Number, ...]
    | list[tuple | list]
)
"""一条序列: (序列名, [(x, y), ...])"""
type Series = tuple[str, list[tuple[float, float]]]


# ----------------------------------------------------------------------
# 数据解析
# ----------------------------------------------------------------------


def parse_data(
    data: DataInput, x: str | None = None, y: str | list[str] | None = None
) -> tuple[list[Series], list[str]]:
    """解析用户传入的数据，返回 ``(series_list, series_names)``。

    不支持的格式会安全地返回空结果，而不是抛出异常。
    """
    match data:
        case dict():
            return _parse_dict_data(data, x, y)
        case [dict(), *_]:
            return _parse_dict_list_data(cast(list[dict], data), x, y)
        case [(list() | tuple()), *_]:
            return _parse_tuple_list_data(cast(list[tuple | list], data))
        case [int() | float(), *_] | (int() | float(), *_):
            return _parse_value_list_data(cast(Sequence[Number], data))
        case _:
            return [], []


def resolve_y_keys(
    keys: list[str], x_key: str, y: str | list[str] | None
) -> list[str]:
    """统一解析 y 轴列名：未显式指定时取除 x 之外的所有列。"""
    match y:
        case str():
            return [y]
        case list():
            return list(y)
        case _:
            return [k for k in keys if k != x_key]


def _as_float(value: object) -> float | None:
    """尽力把取值转为 ``float``；失败返回 ``None``（而非抛异常）。"""
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _coerce_x(values: Sequence) -> list[float]:
    """把 x 列转为数值坐标：分类取值退回其下标，保证坐标单调可用。"""
    coords: list[float] = []
    for i, value in enumerate(values):
        coord = _as_float(value)
        coords.append(float(i) if coord is None else coord)
    return coords


def _raw_x_column(
    data: DataInput, x: str | None
) -> list | None:
    """取出 x 列的**原始**取值序列；非列式数据返回 ``None``。"""
    match data:
        case dict():
            keys = list(data.keys())
            if not keys:
                return None
            return list(data.get(x or keys[0], []) or [])
        case [dict(), *_]:
            rows = [r for r in cast(list[dict], data) if isinstance(r, dict)]
            if not rows:
                return None
            x_key = x or next(iter(rows[0]))
            return [r[x_key] for r in rows if x_key in r]
        case _:
            return None


def resolve_x_labels(data: DataInput, x: str | None = None) -> list[str] | None:
    """当 x 轴为**分类轴**时返回原始标签，否则返回 ``None``。

    判定规则：x 列中只要存在无法转为数值的取值，即视为分类轴。
    返回的标签顺序与 :func:`parse_data` 产出的 x 坐标（下标）严格一一对应。
    """
    values = _raw_x_column(data, x)
    if not values:
        return None
    if all(_as_float(v) is not None for v in values):
        return None
    return ["" if v is None else str(v) for v in values]


def _parse_dict_data(
    data: dict[str, list[Number]], x: str | None, y: str | list[str] | None
) -> tuple[list[Series], list[str]]:
    """解析列字典格式: ``{"x": [1,2,3], "y": [4,5,6]}``。"""
    keys = list(data.keys())
    if not keys:
        return [], []

    x_key = x or keys[0]
    x_values = data.get(x_key, [])
    if not x_values:
        return [], []

    y_keys = [k for k in resolve_y_keys(keys, x_key, y) if k in data]
    x_coords = _coerce_x(x_values)

    series: list[Series] = []
    for y_key in y_keys:
        y_values = data[y_key]
        points: list[tuple[float, float]] = []
        for i in range(min(len(x_coords), len(y_values))):
            y_val = _as_float(y_values[i])
            if y_val is None:
                continue
            points.append((x_coords[i], y_val))
        series.append((y_key, points))
    return series, y_keys


def _parse_dict_list_data(
    data: list[dict[str, Number]], x: str | None, y: str | list[str] | None
) -> tuple[list[Series], list[str]]:
    """解析字典列表格式: ``[{"x": 1, "y": 2}, ...]``。"""
    if not data:
        return [], []

    keys = list(data[0].keys())
    x_key = x or keys[0]
    y_keys = resolve_y_keys(keys, x_key, y)
    if not y_keys:
        return [], []

    rows = [row for row in data if isinstance(row, dict) and x_key in row]
    if not rows:
        return [], []

    x_coords = _coerce_x([row[x_key] for row in rows])

    series: list[Series] = []
    for y_key in y_keys:
        points: list[tuple[float, float]] = []
        for i, row in enumerate(rows):
            if y_key not in row:
                continue
            y_val = _as_float(row[y_key])
            if y_val is None:
                continue
            points.append((x_coords[i], y_val))
        series.append((y_key, points))
    return series, y_keys


def _parse_tuple_list_data(data: list[tuple | list]) -> tuple[list[Series], list[str]]:
    """解析元组/列表序列: ``[(1, 2), (2, 3)]``。"""
    points = [
        (float(item[0]), float(item[1]))
        for item in data
        if isinstance(item, (list, tuple)) and len(item) >= 2
    ]
    return [("series", points)], ["series"]


def _parse_value_list_data(data: Sequence[Number]) -> tuple[list[Series], list[str]]:
    """解析数值列表: ``[1, 2, 3, 4, 5]``。"""
    points = [(float(i), float(val)) for i, val in enumerate(data)]
    return [("series", points)], ["series"]


# ----------------------------------------------------------------------
# 配色与坐标轴
# ----------------------------------------------------------------------


def resolve_colors(color: str | list[str] | None, count: int) -> list[str]:
    """解析并分配颜色，长度始终不小于 ``count``。"""
    match color:
        case str():
            return [color] * count
        case list():
            if len(color) >= count:
                return list(color[:count])
            return list(color) + CHART_COLORS[count - len(color) :]
        case _:
            return list(CHART_COLORS[:count])


def data_bounds(
    series: list[Series], min_x: float | None = None, max_x: float | None = None
) -> tuple[float | None, float | None]:
    """计算序列的 x 轴数据范围（用于自动补齐坐标轴标签）。"""
    xs = [p[0] for _, points in series for p in points]
    if not xs:
        return min_x, max_x
    return (min_x if min_x is not None else min(xs)), (
        max_x if max_x is not None else max(xs)
    )


def nice_ticks(
    start: float | None, end: float | None, count: int = 5
) -> list[float]:
    """生成 ``count`` 个均匀刻度值，用于坐标轴标签。"""
    if start is None or end is None or count < 2:
        return []
    if math.isclose(start, end):
        return [start]
    step = (end - start) / (count - 1)
    return [start + step * i for i in range(count)]


def axis_labels(
    start: float | None, end: float | None, count: int = 5, fmt: str = "{:g}"
) -> list[tuple[float, str]]:
    """生成 ``[(value, label), ...]`` 形式的坐标轴标签数据。"""
    return [(v, fmt.format(v)) for v in nice_ticks(start, end, count)]


def x_axis_labels(
    series: list[Series],
    labels: list[str] | None = None,
    count: int = 12,
) -> list[tuple[float, str]]:
    """构建 x 轴 ``[(value, text), ...]`` 标签，数值轴与分类轴通用。

    - ``labels`` 非空 → 分类轴：按下标均匀抽样，保留原始文本。
    - 否则 → 数值轴：由数据范围生成 ``count`` 个等距刻度。

    ``count`` 是希望显示的最大标签数量，避免密集刻度互相重叠。
    """
    if labels:
        total = len(labels)
        step = max(1, math.ceil(total / max(count, 1)))
        return [(float(i), labels[i]) for i in range(0, total, step)]

    if not series:
        return []
    min_x, max_x = data_bounds(series)
    xs = [p[0] for p in series[0][1]]
    if not xs:
        return []
    return axis_labels(min_x, max_x, max(2, min(len(xs), count)))


def series_bounds(series: list[Series]) -> tuple[float | None, float | None]:
    """计算序列的 y 轴取值范围。"""
    ys = [p[1] for _, points in series for p in points]
    if not ys:
        return None, None
    return min(ys), max(ys)


# ----------------------------------------------------------------------
# 坐标轴尺寸
# ----------------------------------------------------------------------

# 半角 / 全角字符的估算宽度（px），用于推算轴标签所需空间
_HALF_WIDTH = 8.0
_FULL_WIDTH = 14.0
_FULL_THRESHOLD = 0x2E7F  # 该码点以上的字符按全角计算
_PADDING = 12.0  # 标签两侧留白


def axis_label_size(labels: Sequence[object], minimum: float = 24.0) -> float:
    """估算坐标轴单个标签所需空间，供 ``ChartAxis.label_size`` 使用。

    flet-charts 的 ``label_size`` 语义是「**每个**标签可用的最大空间」，默认
    仅 22px。位数稍多的数值（如 ``300``）会被挤进 22px 的槽位，表现为
    **逐字换行**的竖排数字，并溢出到相邻文本上方。

    这里按最长标签估算所需宽度。估算刻意保守（余量 ``_PADDING`` 较小），
    因为左轴宽度过大会压缩绘图区，反而让 flet-charts 抽掉首尾刻度。

    Args:
        labels: 轴标签文本序列。
        minimum: 返回值的下限，保证短标签也不会贴着轴。

    Returns:
        估算出的单标签宽度（px）。
    """
    widest = 0.0
    for text in labels:
        width = 0.0
        for char in str(text):
            width += _FULL_WIDTH if ord(char) > _FULL_THRESHOLD else _HALF_WIDTH
        widest = max(widest, width)
    return max(minimum, widest + _PADDING)


def y_axis_label_size(series: list[Series], count: int = 5) -> float:
    """按 y 取值范围估算左侧坐标轴单个标签所需空间。"""
    lo, hi = series_bounds(series)
    return axis_label_size([text for _, text in axis_labels(lo, hi, count)])


def x_axis_label_size(labels: list[tuple[float, str]]) -> float:
    """按 x 轴标签文本估算底部坐标轴单个标签所需空间。

    底部轴同样需要显式设置：flet-charts 在 ``label_size`` 偏小时会抽掉更多
    刻度，导致首尾的 ``1月`` / ``8月`` 不显示。
    """
    return axis_label_size([text for _, text in labels])

