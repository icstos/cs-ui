"""柱状图 (BarChart) —— 用柱长比较类目。

基于 ``flet_charts.BarChart`` 封装，把「一行一个类目、一列一个系列」的表格数据
排成柱子：默认每组的柱子并排（分组），``stacked=True`` 时改为自下而上堆叠。

柱子的 x 位置固定取类目下标，而不是原始数值 —— 柱状图的 x 是分类轴，类目之间
的距离必须相等，否则「1 月」和「12 月」之间会空出一大块。

用法::

    BarChart(
        data={"季度": ["Q1", "Q2"], "线上": [12, 18], "线下": [8, 6]},
        x="季度",
        y=["线上", "线下"],
        height=280,
    )
"""

from __future__ import annotations

import math

import flet as ft
import flet_charts as ftc

from ui.chart._data import (
    TOOLTIP_BG,
    TOOLTIP_PAD,
    TOOLTIP_RADIUS,
    chart_palette,
    DataInput,
    Series,
    parse_data,
    resolve_colors,
    resolve_x_labels,
    x_axis_label_size,
    y_axis_label_size,
)
from ui.core.doc import Api, Example, Spec, info, run, tip, warn

__all__ = ["BarChart"]


def _bar_labels(
    series: list[Series], raw_labels: list[str] | None, count: int = 12
) -> list[tuple[float, str]]:
    """按**柱子的下标**生成底轴标签。

    数值 x（``季度=[1, 2, 3, 4]``）如果交给等距刻度生成器，标签会落在 1..4 而
    柱子落在 0..3，整排标签右移一格。柱子按位置排，标签就按位置标。
    """
    if not series or not series[0][1]:
        return []
    points = series[0][1]
    total = len(points)
    step = max(1, math.ceil(total / max(count, 1)))
    out: list[tuple[float, str]] = []
    for index in range(0, total, step):
        text = (
            raw_labels[index]
            if raw_labels and index < len(raw_labels)
            else f"{points[index][0]:g}"
        )
        out.append((float(index), text))
    return out


class BarChart(ftc.BarChart):
    """柱状图组件，继承自 :class:`flet_charts.BarChart`。

    Args:
        data: 柱状图数据。支持字典列表 ``[{"x": 1, "y": 2}, ...]``、列字典
            ``{"季度": [...], "线上": [...]}``、数值列表与元组列表。
        x: 用作 x 轴的列名。
        y: 用作 y 轴的列名，可传列表绘制多组柱状。
        height: 图表高度，默认 400。
        width: 图表宽度，默认由容器决定。
        use_container_width: 是否撑满容器宽度，默认 True。
        color: 柱体颜色，可传列表为每组分别配色。
        stacked: 是否堆叠显示（默认 False，即分组并列显示）。
        rod_width: 单个柱体宽度；留空按类目数与系列数自适应。
        group_spacing: 组间距，默认 16。
        show_grid: 是否显示网格线，默认 True。
        tooltip: 是否显示悬停提示（多系列时带系列名），默认 True。
        border_radius: 柱体顶端圆角，默认 4。
        show_x_labels: 是否显示 x 轴标签，默认 True。
        **kwargs: 其他传递给 :class:`flet_charts.BarChart` 的参数。
    """

    def __init__(
        self,
        data: DataInput | None = None,
        x: str | None = None,
        y: str | list[str] | None = None,
        width: float | None = None,
        height: float = 400,
        use_container_width: bool = True,
        color: str | list[str] | None = None,
        stacked: bool = False,
        rod_width: float | None = None,
        group_spacing: float = 16,
        show_grid: bool = True,
        tooltip: bool = True,
        border_radius: float = 4,
        show_x_labels: bool = True,
        **kwargs,
    ) -> None:
        series, names = parse_data(data, x, y) if data is not None else ([], [])
        colors = resolve_colors(color, max(len(names), 1))

        x_values: list[float] = []
        if series:
            x_values = [p[0] for p in series[0][1]]

        width_value = (
            rod_width
            if rod_width is not None
            else self._auto_rod_width(len(x_values), len(series))
        )
        multi = len(series) > 1
        last = len(series) - 1

        groups = [
            ftc.BarChartGroup(
                x=i,
                rods=[
                    self._build_rod(
                        value=points[i][1] if i < len(points) else 0,
                        color=colors[s_index % len(colors)],
                        width_value=width_value,
                        stacked=stacked,
                        border_radius=border_radius,
                        # 分组时每根柱子都露在外侧；堆叠时只有最上面一段露出来
                        rounded=(not stacked) or s_index == last,
                        # 多系列时把系列名写进提示框，否则一排柱子分不清谁是谁
                        label=name if multi else "",
                    )
                    for s_index, (name, points) in enumerate(series)
                ],
                group_vertically=stacked,
            )
            for i in range(len(x_values))
        ]

        x_labels = _bar_labels(
            series, resolve_x_labels(data, x) if data is not None else None
        )
        # 堆叠时左轴量程是每组的合计，标签宽度也要按合计估，否则大数字会被裁
        y_ref = self._stacked_series(series) if stacked else series

        super().__init__(
            groups=groups,
            width=width,
            height=height,
            expand=use_container_width or None,
            group_spacing=group_spacing,
            bgcolor=ft.Colors.with_opacity(0.02, ft.Colors.ON_SURFACE),
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            left_axis=ftc.ChartAxis(
                show_labels=True,
                labels=[],
                title=None,
                label_size=y_axis_label_size(y_ref),
                # 自动刻度已覆盖数据范围，再画极值标签会与之重叠
                show_min=False,
                show_max=False,
            ),
            bottom_axis=ftc.ChartAxis(
                show_labels=show_x_labels,
                labels=(
                    [ftc.ChartAxisLabel(value=v, label=text) for v, text in x_labels]
                    if show_x_labels
                    else []
                ),
                label_size=x_axis_label_size(x_labels),
                show_min=False,
                show_max=False,
            ),
            horizontal_grid_lines=(
                ftc.ChartGridLines(
                    color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE_VARIANT),
                    width=1,
                )
                if show_grid
                else None
            ),
            tooltip=(
                ftc.BarChartTooltip(
                    bgcolor=TOOLTIP_BG,
                    border_radius=TOOLTIP_RADIUS,
                    padding=TOOLTIP_PAD,
                )
                if tooltip
                else None
            ),
            **kwargs,
        )

    # ------------------------------------------------------------------
    # 内部构建方法
    # ------------------------------------------------------------------

    @staticmethod
    def _auto_rod_width(group_count: int, series_count: int) -> int:
        """根据数据量自适应计算柱体宽度。"""
        if group_count <= 0:
            return 22
        lane = 520 / group_count
        return int(max(6, min(28, lane / max(series_count, 1) - 4)))

    @staticmethod
    def _stacked_series(series: list[Series]) -> list[Series]:
        """把多系列压成「每组合计」的一条序列，只用于估算左轴标签宽度。"""
        totals: dict[float, float] = {}
        for _, points in series:
            for x_val, y_val in points:
                totals[x_val] = totals.get(x_val, 0.0) + y_val
        return [("stacked", sorted(totals.items()))]

    @staticmethod
    def _build_rod(
        *,
        value: float,
        color: str,
        width_value: int,
        stacked: bool,
        border_radius: float,
        rounded: bool,
        label: str,
    ) -> ftc.BarChartRod:
        """构建单个柱体。

        圆角加在「看得见的那一端」：正值柱在顶部、负值柱在底部；堆叠时只有最外层
        那段露出来，中间段保持直角。
        """
        if rounded:
            radius = (
                ft.BorderRadius.only(
                    bottom_left=border_radius, bottom_right=border_radius
                )
                if value < 0
                else border_radius
            )
        else:
            radius = ft.BorderRadius.only(top_left=0, top_right=0)
        return ftc.BarChartRod(
            to_y=value,
            width=width_value,
            color=color,
            border_radius=radius,
            tooltip=f"{label} {value:g}".strip(),
        )


# ======================================================================
# 示例
# ======================================================================


def _grouped() -> ft.Control:
    """分组：同一季度线上线下并排，长度直接可比。"""
    return BarChart(
        data={
            "季度": ["Q1", "Q2", "Q3", "Q4"],
            "线上": [126, 148, 139, 172],
            "线下": [88, 79, 94, 102],
        },
        x="季度",
        y=["线上", "线下"],
        height=280,
    )


def _stacked() -> ft.Control:
    """堆叠：每根柱子是当月总量，内部分段是渠道构成。"""
    return BarChart(
        data={
            "月份": ["3月", "4月", "5月", "6月", "7月"],
            "直营": [62, 70, 78, 84, 96],
            "分销": [42, 46, 51, 58, 61],
            "线上": [35, 39, 44, 47, 55],
        },
        x="月份",
        y=["直营", "分销", "线上"],
        stacked=True,
        height=300,
        group_spacing=24,
    )


def _negative() -> ft.Control:
    """负值：柱子从 0 基线向下长，正负月份一眼分清。"""
    return BarChart(
        data={
            "月份": ["1月", "2月", "3月", "4月", "5月", "6月"],
            "净现金流": [12.4, 8.6, -3.2, -6.8, 4.5, 9.1],
        },
        x="月份",
        y="净现金流",
        height=260,
        color=chart_palette()[1],
    )


_BASIC_CODE = """BarChart(
    data={
        "季度": ["Q1", "Q2", "Q3", "Q4"],
        "线上": [126, 148, 139, 172],
        "线下": [88, 79, 94, 102],
    },
    x="季度",
    y=["线上", "线下"],   # 两个系列 → 分组并排
    height=280,
)

# 堆叠：改成 stacked=True，柱子高度变成各系列之和
BarChart(data=rows, x="月份", y=["直营", "分销"], stacked=True)"""

SPEC = Spec(
    name="BarChart",
    summary="用柱子的长度比较离散类目的大小，可分组或堆叠。",
    definition=(
        "柱状图给每个类目一根柱子，所有柱子共享同一条 0 基线 —— 长度可以直接比，"
        "这是它相对折线图的优势。多个系列有两种排法：分组并列时比较的是「同一类目"
        "下谁更高」，堆叠时柱高是合计、分段是构成，但中间段的起点不再统一，段与段"
        "之间只能比趋势、不能比长度。"
    ),
    anatomy=[
        (
            "柱体",
            "从 0 基线长出的一根矩形，宽度按类目数与系列数自适应（6-28px）。",
        ),
        (
            "分组与间距",
            "同一类目的多根柱子并排，组间留 group_spacing（默认 16px），组内自动均分。",
        ),
        (
            "基线",
            "所有柱子共用的 0 轴。负值柱向下延伸，正负月份在同一张图里也不会看反。",
        ),
        ("坐标轴", "底轴标类目原文；左轴刻度覆盖数据范围，堆叠时按合计的最大值算。"),
        (
            "悬停提示",
            "单系列只显示数值；多系列带系列名（「线上 172」），否则分不清哪根是哪组。",
        ),
    ],
    when=[
        "比较几个类目的绝对量（各季度营收、各渠道订单数）",
        "类目数量有限（2-12 个），每个类目都值得单独占一根柱子",
        "同时看合计与构成：stacked=True 后柱高是总量，分段是来源",
    ],
    avoid=[
        "看连续趋势：类目之间的间隔是虚构的，改用 LineChart",
        "类目超过十几个或名称很长：柱子会细到看不清，改用表格或折线图",
        "需要横向排名的条形图：本组件只画纵向柱，横向请改用表格或自定义条形",
    ],
    examples=[
        Example(
            "分组",
            _grouped,
            hint="四个季度、两条业务线并排。同一组内比高低，跨组比趋势。",
            code=_BASIC_CODE,
        ),
        Example(
            "堆叠",
            _stacked,
            hint="每月一根柱 = 三个渠道之和，分段颜色对应渠道。圆角只落在最上面一段。",
        ),
        Example(
            "负值",
            _negative,
            hint="净现金流有正有负：柱子从 0 轴向下长，圆角跟着落在柱子的外端。",
        ),
    ],
    api=[
        Api("data", "DataInput | None", "None", "数据源，格式与 LineChart 相同"),
        Api("x", "str | None", "None", "x 轴（类目）列名；留空取第一列"),
        Api("y", "str | list[str] | None", "None", "数值列名，传列表画多组柱"),
        Api("color", "str | list[str] | None", "None", "柱体颜色，按系列分配"),
        Api("stacked", "bool", "False", "堆叠显示；关闭时同组柱子并排"),
        Api("rod_width", "float | None", "None", "单根柱宽，留空自适应 6-28px"),
        Api("group_spacing", "float", "16", "组与组之间的间距"),
        Api("border_radius", "float", "4", "柱体外端圆角"),
        Api("show_grid", "bool", "True", "横向网格线"),
        Api("height", "float", "400", "图表高度"),
    ],
    notes=[
        tip(
            "底轴标签改为按柱子下标生成。数值 x（如季度 1-4）此前会标在 1..4 上、"
            "而柱子排在 0..3，整排标签右移一格。"
        ),
        info(
            "堆叠时圆角只给最上面一段（此前给的是最下面一段，被上层盖住，整根柱子看起来"
            "是方的）；负值柱的圆角落在底部。"
        ),
        warn(
            "flet_charts 的 BarChart 只有纵向柱，没有横向模式。不要用 rotate 把整张图"
            "转 90° —— 坐标轴文字会跟着躺下；横向排名场景用表格或自绘条形。"
        ),
    ],
    tags=("柱状图", "bar", "堆叠", "分组"),
)


if __name__ == "__main__":
    run(SPEC)
