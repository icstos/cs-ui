"""面积图 (AreaChart) —— 折线下方铺满颜色。

复用 :class:`flet_charts.LineChart` 的「线下填充」能力：数据解析、坐标轴、
悬停提示与折线图完全一致，差别只在每条序列多填充一块区域。

填充默认是自上而下的渐变（线处最浓、贴近基线处淡出），因为一整块实色会让
相邻序列互相压住；``gradient=False`` 时退回纯色 + 固定透明度。

用法::

    AreaChart(
        data={"日期": [1, 2, 3], "日活": [1840, 1930, 1880]},
        x="日期",
        y="日活",
        height=260,
    )
"""

from __future__ import annotations

import flet as ft
import flet_charts as ftc

from ui.chart._data import (
    CHART_COLORS,
    DataInput,
    parse_data,
    resolve_colors,
    resolve_x_labels,
    x_axis_label_size,
    x_axis_labels,
    y_axis_label_size,
)
from ui.core.doc import Api, Example, Spec, info, run, tip, warn

__all__ = ["AreaChart"]


class AreaChart(ftc.LineChart):
    """面积图组件，继承自 :class:`flet_charts.LineChart`。

    Args:
        data: 面积图数据，支持字典列表 / 列字典 / 数值列表 / 元组列表。
        x: 用作 x 轴的列名。
        y: 用作 y 轴的列名，可传列表绘制多层面积。
        height: 图表高度，默认 400。
        width: 图表宽度，默认由容器决定。
        use_container_width: 是否撑满容器宽度，默认 True。
        color: 线条与填充颜色，可传列表按序列配色。
        opacity: 填充浓度（0~1）：纯色模式是填充透明度，渐变模式是顶端浓度。
        curved: 是否使用平滑曲线，默认 True。
        gradient: 是否使用自上而下的渐变填充，默认 True。
        show_grid: 是否显示网格线，默认 True。
        tooltip: 是否显示悬停提示，默认 True。
        stroke_width: 线条粗细，默认 2.0。
        show_points: 是否显示数据点，默认 False。
        show_x_labels: 是否显示 x 轴标签，默认 True。
        **kwargs: 其他传递给 :class:`flet_charts.LineChart` 的参数。
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
        opacity: float = 0.22,
        curved: bool = True,
        gradient: bool = True,
        show_grid: bool = True,
        tooltip: bool = True,
        stroke_width: float = 2.0,
        show_points: bool = False,
        show_x_labels: bool = True,
        **kwargs,
    ) -> None:
        series, names = parse_data(data, x, y) if data is not None else ([], [])
        colors = resolve_colors(color, max(len(names), 1))
        x_labels = x_axis_labels(series, resolve_x_labels(data, x) if data else None)

        data_series = [
            ftc.LineChartData(
                points=[
                    ftc.LineChartDataPoint(
                        x=px,
                        y=py,
                        point=(
                            ftc.ChartCirclePoint(
                                color=colors[i % len(colors)],
                                radius=3.5,
                                stroke_color=ft.Colors.SURFACE,
                                stroke_width=1.5,
                            )
                            if show_points
                            else None
                        ),
                    )
                    for px, py in points
                ],
                color=colors[i % len(colors)],
                stroke_width=float(stroke_width),
                curved=curved,
                prevent_curve_over_shooting=True,
                below_line_bgcolor=(
                    None
                    if gradient
                    else ft.Colors.with_opacity(opacity, colors[i % len(colors)])
                ),
                below_line_gradient=(
                    ft.LinearGradient(
                        begin=ft.Alignment.TOP_CENTER,
                        end=ft.Alignment.BOTTOM_CENTER,
                        colors=[
                            ft.Colors.with_opacity(
                                opacity * 1.6, colors[i % len(colors)]
                            ),
                            ft.Colors.with_opacity(0.02, colors[i % len(colors)]),
                        ],
                    )
                    if gradient
                    else None
                ),
            )
            for i, (_name, points) in enumerate(series)
        ]

        super().__init__(
            data_series=data_series,
            width=width,
            height=height,
            expand=use_container_width or None,
            bgcolor=ft.Colors.with_opacity(0.02, ft.Colors.ON_SURFACE),
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            left_axis=ftc.ChartAxis(
                show_labels=True,
                labels=[],
                title=None,
                label_size=y_axis_label_size(series),
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
                title=None,
                label_size=x_axis_label_size(x_labels),
                show_min=False,
                show_max=False,
            ),
            horizontal_grid_lines=self._grid_lines(show_grid),
            vertical_grid_lines=self._grid_lines(show_grid),
            tooltip=(
                ftc.LineChartTooltip(
                    bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.GREY_900),
                    border_radius=8,
                    padding=10,
                )
                if tooltip
                else None
            ),
            **kwargs,
        )

    @staticmethod
    def _grid_lines(show_grid: bool) -> ftc.ChartGridLines | None:
        """网格线走角色色：写死的灰在深色主题下看不见。"""
        return (
            ftc.ChartGridLines(
                color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE_VARIANT),
                width=1,
            )
            if show_grid
            else None
        )


# ======================================================================
# 示例
# ======================================================================


def _single() -> ft.Control:
    """单系列：两周的日活，面积随数值起落。"""
    return AreaChart(
        data={
            "日期": list(range(1, 15)),
            "日活": [
                1840,
                1930,
                1880,
                2050,
                2180,
                2110,
                2260,
                2390,
                2320,
                2470,
                2580,
                2510,
                2690,
                2740,
            ],
        },
        x="日期",
        y="日活",
        height=260,
    )


def _layers() -> ft.Control:
    """三层重叠：量级大的先画，小的叠在上面才看得见。"""
    return AreaChart(
        data={
            "月份": [f"{m}月" for m in range(1, 13)],
            "Web": [
                4200,
                4380,
                4510,
                4820,
                5100,
                5360,
                5720,
                5940,
                5810,
                6120,
                6480,
                6720,
            ],
            "App": [
                1800,
                1920,
                2100,
                2260,
                2440,
                2610,
                2800,
                3010,
                3180,
                3320,
                3510,
                3740,
            ],
            "小程序": [
                620,
                680,
                740,
                810,
                860,
                940,
                1020,
                1100,
                1180,
                1240,
                1330,
                1410,
            ],
        },
        x="月份",
        y=["Web", "App", "小程序"],
        height=300,
        show_points=False,
    )


def _solid() -> ft.Control:
    """纯色填充：关掉渐变，只留一层固定透明度的色块。"""
    return AreaChart(
        data={
            "日期": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"],
            "会话量": [320, 380, 355, 420, 465, 440, 510],
        },
        x="日期",
        y="会话量",
        height=240,
        color=CHART_COLORS[2],
        gradient=False,
        opacity=0.35,
    )


_BASIC_CODE = """AreaChart(
    data={
        "日期": ["周一", "周二", "周三", "周四"],
        "会话量": [320, 380, 355, 420],
    },
    x="日期",
    y="会话量",
    height=240,
)

# 多层面积：y 传列表，默认渐变填充，后画的序列盖住先画的
AreaChart(data=rows, x="月份", y=["Web", "App"], gradient=True)"""

SPEC = Spec(
    name="AreaChart",
    summary="在折线下方填充颜色，强调量级而不只是方向。",
    definition=(
        "面积图是折线的加重版：线下区域被填满，视觉重量与数值成正比，所以它先让人"
        "看到「有多少」，再看到「怎么变」。默认填充是自上而下的渐变 —— 线附近浓、"
        "贴近基线处淡出，这样两层面积重叠时下面那层仍能透出来；换成实色就等于用"
        "上层把下层涂掉。"
    ),
    anatomy=[
        ("轮廓线", "序列顶部那条线，颜色与填充同源；线宽默认 2px、平滑。"),
        (
            "填充区",
            "线条与基线之间的区域。渐变模式顶端约 35% 浓度、向下淡到 2%；纯色模式用固定 opacity。",
        ),
        ("坐标轴", "与折线图共用：左轴按数据范围出刻度，底轴支持数值与分类两种 x。"),
        ("悬停提示", "提示框显示所在点的坐标，填充区本身不响应点击。"),
    ],
    when=[
        "一条序列的量级本身就是重点（日活、营收、流量）",
        "2-3 条量级差距明显的序列同图对照，重叠后仍能分辨",
        "强调长期波动形态：峰谷的高度差比精确取值更重要",
    ],
    avoid=[
        "两条数值接近的序列要比高低：面积互相遮盖，改用 LineChart",
        "需要看各部分的加总或占比：本组件不做堆叠，改用堆叠柱状图",
        "离散类目的横向比较：面积没有共同基线，改用 BarChart",
    ],
    examples=[
        Example(
            "单系列",
            _single,
            hint="两周日活：默认渐变填充，峰谷直接体现在色的厚度上。",
            code=_BASIC_CODE,
        ),
        Example(
            "多层重叠",
            _layers,
            hint="Web / App / 小程序三层。按量级从大到小传，小序列才不会被盖住。",
        ),
        Example(
            "纯色填充",
            _solid,
            hint="gradient=False + opacity=0.35：只要一层均匀底色时用这种形态。",
        ),
    ],
    api=[
        Api("data", "DataInput | None", "None", "数据源，格式与 LineChart 相同"),
        Api("x", "str | None", "None", "x 轴列名；留空取第一列"),
        Api("y", "str | list[str] | None", "None", "y 轴列名，传列表画多层面积"),
        Api("color", "str | list[str] | None", "None", "线条与填充的颜色，按序列分配"),
        Api(
            "opacity", "float", "0.22", "填充浓度：纯色模式是透明度，渐变模式是顶端浓度"
        ),
        Api("gradient", "bool", "True", "渐变填充；关闭后退回纯色"),
        Api("curved", "bool", "True", "平滑轮廓线"),
        Api("show_points", "bool", "False", "是否标出每个数据点"),
        Api("show_grid", "bool", "True", "横纵网格线"),
        Api("height", "float", "400", "图表高度"),
    ],
    notes=[
        info(
            "opacity 在两种填充模式下含义不同：渐变模式它决定顶端浓度（再乘 1.6），"
            "纯色模式它直接就是填充透明度。"
        ),
        warn(
            "面积按传入顺序叠放，后画的序列压住先画的。多层时把量级最大的放第一个，"
            "否则小序列会被整块盖掉。"
        ),
        tip(
            "本组件不做堆叠（各层都从基线算起）。需要「累计」时先把数据按行累加，"
            "再传给 AreaChart —— 图形本身不会替你做加法。"
        ),
    ],
    tags=("面积图", "area", "填充", "趋势"),
)


if __name__ == "__main__":
    run(SPEC)
