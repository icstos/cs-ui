"""折线图 (LineChart) —— 用斜率表达趋势。

基于 ``flet_charts.LineChart`` 封装，沿用 Streamlit ``st.line_chart`` 的数据入参
风格：字典列表 / 列字典 / 数值列表 / 元组列表都能直接喂进来，x 轴是数值时按
数值刻度排布，是文本时（``1月`` / ``Q1``）自动按下标等距排布并显示原文。

x 轴与 y 轴标签的 ``label_size`` 由 :mod:`ui.chart._data` 按最长文本估算 ——
flet-charts 的默认值 22px 会把 ``1,200`` 挤成逐字换行的竖排数字。

用法::

    LineChart(
        data={"月份": ["1月", "2月"], "付费用户": [820, 932]},
        x="月份",
        y="付费用户",
        height=280,
    )
"""

from __future__ import annotations

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
    x_axis_labels,
    y_axis_label_size,
)
from ui.core.doc import Api, Example, Spec, info, run, tip, warn

type SeriesData = list[Series]


def _legend(names: list[str], colors: list[str]) -> ft.Control:
    """顶部图例：色点 + 系列名。

    画在 ``top_axis`` 的标题里，而不是页面里另起一行 —— 否则图表高度一变，
    图例就会跟着上下跳，同一页里的两张图对不齐。
    """
    items = [
        ft.Row(
            tight=True,
            spacing=6,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=8,
                    height=8,
                    border_radius=4,
                    bgcolor=colors[index % len(colors)],
                ),
                ft.Text(name, size=11, color=ft.Colors.ON_SURFACE_VARIANT),
            ],
        )
        for index, name in enumerate(names)
    ]
    return ft.Row(
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=18,
        controls=items,
    )


class LineChart(ftc.LineChart):
    """折线图组件，继承自 :class:`flet_charts.LineChart`。

    参考 Streamlit 的 ``st.line_chart`` 参数风格，简化数据传入方式，
    并提供美观的默认样式。

    Args:
        data: 折线图数据。支持字典列表 ``[{"x": 1, "y": 2}, ...]``、列字典
            ``{"x": [1, 2], "y": [3, 4]}``、数值列表 ``[1, 2, 3]``（x 轴自动
            取下标）与元组列表 ``[(1, 2), (2, 3)]``。
        x: 用作 x 轴的列名。留空取第一列。
        y: 用作 y 轴的列名。传列表即多系列。
        width: 图表宽度；默认由容器决定。
        height: 图表高度，默认 400。
        use_container_width: 是否撑满容器宽度，默认 True。
        title: 图表标题，画在顶部；与图例同时存在时上下叠成两行。
        color: 序列颜色，单个色值应用到所有序列，列表按序分配。
        curved: 是否把折线画成平滑曲线，默认 True。
        show_grid: 是否显示横向与纵向网格线，默认 True。
        show_legend: 多系列时是否在图表顶部画图例，默认 True。
        tooltip: 是否显示悬停提示，默认 True。
        stroke_width: 线宽，默认 2.0。
        show_points: 是否画出每个数据点，默认 False。
        interactive: 是否响应悬停等交互，默认 True。
        show_x_labels: 是否显示 x 轴标签，默认 True。
        **kwargs: 透传给 :class:`flet_charts.LineChart`。
    """

    def __init__(
        self,
        data: DataInput | None = None,
        x: str | None = None,
        y: str | list[str] | None = None,
        width: float | None = None,
        height: float | None = 400,
        use_container_width: bool = True,
        title: str | None = None,
        color: str | list[str] | None = None,
        curved: bool = True,
        show_grid: bool = True,
        show_legend: bool = True,
        tooltip: bool = True,
        stroke_width: float = 2.0,
        show_points: bool = False,
        interactive: bool = True,
        show_x_labels: bool = True,
        **kwargs,
    ) -> None:
        # 先给空值：data=None 时下面的 axis 尺寸计算仍要能读到这两个变量
        parsed_data: SeriesData = []
        series_names: list[str] = []
        x_labels: list[tuple[float, str]] = []

        if data is not None:
            parsed_data, series_names = parse_data(data, x, y)
            x_labels = x_axis_labels(parsed_data, resolve_x_labels(data, x))

        colors = resolve_colors(color, max(len(series_names), 1))
        show = show_legend and len(series_names) > 1

        # 标题与图例共用顶部轴：两者都有时叠成两行，标题占第一行
        top_blocks: list[ft.Control] = []
        if title:
            top_blocks.append(
                ft.Text(
                    title,
                    size=12,
                    weight=ft.FontWeight.W_600,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                )
            )
        if show:
            top_blocks.append(_legend(series_names, colors))
        top_title = (
            None
            if not top_blocks
            else (
                top_blocks[0]
                if len(top_blocks) == 1
                else ft.Column(
                    spacing=4,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=top_blocks,
                )
            )
        )

        data_series = [
            ftc.LineChartData(
                points=self._build_data_points(
                    points, colors[i % len(colors)], show_points
                ),
                color=colors[i % len(colors)],
                stroke_width=float(stroke_width),
                curved=curved,
                # 平滑曲线会在尖峰外"过冲"，画出一条数据里并不存在的凸起
                prevent_curve_over_shooting=True,
            )
            for i, (_, points) in enumerate(parsed_data)
        ]

        super().__init__(
            data_series=data_series,
            width=width,
            height=height,
            expand=use_container_width or None,
            interactive=interactive,
            bgcolor=ft.Colors.with_opacity(0.02, ft.Colors.ON_SURFACE),
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            top_axis=(
                ftc.ChartAxis(
                    title=top_title,
                    show_labels=False,
                    title_size=40 if len(top_blocks) > 1 else 22,
                )
                if top_title is not None
                else None
            ),
            left_axis=ftc.ChartAxis(
                show_labels=True,
                labels=[],
                title=None,
                title_size=12,
                label_size=y_axis_label_size(parsed_data),
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
                title_size=12,
                label_size=x_axis_label_size(x_labels),
                show_min=False,
                show_max=False,
            ),
            horizontal_grid_lines=self._build_grid_lines(show_grid),
            vertical_grid_lines=self._build_grid_lines(show_grid),
            tooltip=self._build_tooltip(tooltip),
            min_x=None,
            max_x=None,
            min_y=None,
            max_y=None,
            **kwargs,
        )

    # ------------------------------------------------------------------
    # 内部构建方法
    # ------------------------------------------------------------------

    @staticmethod
    def _build_data_points(
        points: list[tuple[float, float]], color: str, show_points: bool
    ) -> list[ftc.LineChartDataPoint]:
        """构建数据点列表，可选显示圆点标记。"""
        return [
            ftc.LineChartDataPoint(
                x=x_val,
                y=y_val,
                point=(
                    ftc.ChartCirclePoint(
                        color=color,
                        radius=3.5,
                        stroke_color=ft.Colors.SURFACE,
                        stroke_width=1.5,
                    )
                    if show_points
                    else None
                ),
            )
            for x_val, y_val in points
        ]

    @staticmethod
    def _build_grid_lines(show_grid: bool) -> ftc.ChartGridLines | None:
        """构建网格线配置。

        用 ``OUTLINE_VARIANT`` 而不是固定灰：写死的 ``GREY_700`` 在深色主题的
        深底上几乎看不见，而角色色由 Flutter 按当前色板解析。
        """
        return (
            ftc.ChartGridLines(
                color=ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE_VARIANT),
                width=1,
            )
            if show_grid
            else None
        )

    @staticmethod
    def _build_tooltip(tooltip: bool) -> ftc.LineChartTooltip | None:
        """构建悬停提示配置。"""
        return (
            ftc.LineChartTooltip(
                bgcolor=TOOLTIP_BG,
                border_radius=TOOLTIP_RADIUS,
                padding=TOOLTIP_PAD,
                max_width=180,
            )
            if tooltip
            else None
        )


# ======================================================================
# 示例
# ======================================================================


def _trend() -> ft.Control:
    """单系列、分类 x 轴：12 个月的付费用户数。"""
    return LineChart(
        data={
            "月份": [
                "1月",
                "2月",
                "3月",
                "4月",
                "5月",
                "6月",
                "7月",
                "8月",
                "9月",
                "10月",
                "11月",
                "12月",
            ],
            "付费用户": [
                820,
                932,
                1015,
                1180,
                1260,
                1420,
                1550,
                1610,
                1580,
                1720,
                1890,
                2040,
            ],
        },
        x="月份",
        y="付费用户",
        height=280,
    )


def _multi() -> ft.Control:
    """三条渠道的周访问量：颜色 + 顶部图例区分系列。"""
    return LineChart(
        data={
            "周次": [1, 2, 3, 4, 5, 6, 7, 8],
            "自然搜索": [1200, 1320, 1280, 1450, 1520, 1480, 1610, 1750],
            "付费投放": [800, 860, 940, 910, 1040, 1120, 1080, 1190],
            "直接访问": [640, 610, 700, 760, 720, 790, 830, 880],
        },
        x="周次",
        y=["自然搜索", "付费投放", "直接访问"],
        height=300,
    )


def _points() -> ft.Control:
    """平滑曲线 + 数据点：点数不多时，圆点让每个观测值都可读。"""
    return LineChart(
        data=[
            (1, 186),
            (2, 172),
            (3, 178),
            (4, 160),
            (5, 154),
            (6, 149),
            (7, 158),
            (8, 141),
            (9, 136),
            (10, 130),
            (11, 128),
            (12, 119),
        ],
        height=260,
        color=chart_palette()[4],
        curved=True,
        show_points=True,
        stroke_width=2.5,
        show_grid=False,
    )


_BASIC_CODE = """LineChart(
    data={
        "月份": ["1月", "2月", "3月", "4月"],
        "付费用户": [820, 932, 1015, 1180],
    },
    x="月份",          # 文本列 → 分类轴，按原文显示
    y="付费用户",
    height=280,
)

# 多系列：y 传列表，颜色按内置色板依次取，图例自动出现在顶部
LineChart(data=rows, x="周次", y=["自然搜索", "付费投放"])"""

SPEC = Spec(
    name="LineChart",
    summary="按 x 的顺序连接数据点，用斜率表达趋势。",
    definition=(
        "折线图回答的是「在变好还是变坏」。它把同一序列的相邻点连成一条路径，"
        "默认平滑但抑制过冲 —— 贝塞尔曲线不会在尖峰外拉出数据里并不存在的凸起。"
        "x 轴允许是数值（1..12），也允许是文本（「1月」），后者自动退化成等距下标"
        "并显示原文，所以按月的业务数据不必先编码成数字。"
    ),
    anatomy=[
        (
            "坐标轴",
            "左轴刻度由数据范围自动生成；底轴按 x 是数值还是分类切换刻度或原文。",
        ),
        (
            "折线",
            "每条序列一条路径，默认 2px、平滑；颜色取 color 参数或内置分类色板。",
        ),
        (
            "数据点",
            "show_points 时才画圆点（半径 3.5、描边取面板底色）；默认关闭，点一多就糊成一条带。",
        ),
        (
            "图例",
            "多系列时在图表顶部居中排一行「色点 + 系列名」；单系列不重复系列名。",
        ),
        ("悬停提示", "提示框只显示所在点的坐标，线本身不接收点击。"),
    ],
    when=[
        "x 有序且连续（月份、周次、日期），读者关心走势而不是构成",
        "同一张图里比较 2-5 条序列的高低与交叉",
        "数据点超过十几个，柱状图会挤得读不出单个类目",
    ],
    avoid=[
        "比较离散类目的大小：柱子的长度比线的斜率更容易精确比较，用 BarChart",
        "表达部分与整体：重叠的面积看不出占比，改用堆叠柱状图",
        "只有一两个观测点：连线本身不传递信息，改用指标卡或柱状图",
    ],
    examples=[
        Example(
            "单系列趋势",
            _trend,
            hint="12 个月的付费用户数。文本 x 轴自动等距排布，标签取原文。",
            code=_BASIC_CODE,
        ),
        Example(
            "多系列与图例",
            _multi,
            hint="三条渠道同图对比：颜色按内置色板分配，图例固定在图表顶部。",
        ),
        Example(
            "平滑曲线与数据点",
            _points,
            hint="12 个观测值 + show_points：点不多时逐个标出，读数不用靠悬停。",
        ),
    ],
    api=[
        Api(
            "data",
            "DataInput | None",
            "None",
            "数据源：列字典 / 字典列表 / 数值列表 / 元组列表",
        ),
        Api("x", "str | None", "None", "x 轴列名；留空取第一列"),
        Api("y", "str | list[str] | None", "None", "y 轴列名，传列表画多条折线"),
        Api("color", "str | list[str] | None", "None", "序列颜色，列表按序分配"),
        Api("curved", "bool", "True", "平滑曲线；关闭后是直线段"),
        Api("show_points", "bool", "False", "是否标出每个数据点"),
        Api(
            "show_legend",
            "bool",
            "True",
            "多系列时在顶部画图例；单系列始终不画",
        ),
        Api("show_grid", "bool", "True", "横纵网格线"),
        Api("stroke_width", "float", "2.0", "线宽"),
        Api("height", "float | None", "400", "图表高度"),
    ],
    notes=[
        tip(
            "data 为空或解析不出序列时只画空坐标系，不再抛 UnboundLocalError —— "
            "此前 axis 尺寸计算会在 data=None 时读到未初始化的变量。"
        ),
        info(
            "图例画在顶部轴标题里，不额外占一行布局，所以同一页多张图的高度不会因为"
            "「有没有图例」而错位。"
        ),
        warn(
            "系列色是固定的分类色板（相邻色必须能区分），不跟主题主色走；面板底色、"
            "边框与网格线已改用角色色，深色主题下网格不会消失。"
        ),
    ],
    tags=("折线图", "line", "趋势", "曲线"),
)


if __name__ == "__main__":
    run(SPEC)
