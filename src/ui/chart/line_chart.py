"""
折线图组件 (LineChart)

基于 flet_charts.LineChart 封装，参考 Streamlit st.line_chart 的参数风格，
提供更简洁、美观的折线图绘制能力。

支持：
- 单条/多条折线
- 字典、列表、元组多种数据格式
- 自动轴范围计算
- 美观的默认配色和样式
"""

import math
from collections.abc import Sequence
from typing import cast

import flet as ft
import flet_charts as ftc

# 内置美观配色方案
LINE_COLORS = [
    "#1f6feb",  # 蓝色
    "#10b981",  # 绿色
    "#f59e0b",  # 橙色
    "#ef4444",  # 红色
    "#8b5cf6",  # 紫色
    "#ec4899",  # 粉色
    "#06b6d4",  # 青色
    "#f97316",  # 深橙
]

type DataRow = dict[str, int | float] | tuple | list
type DataInput = (
    list[DataRow]
    | dict[str, list[int | float]]
    | list[int | float]
    | tuple[int | float, ...]
    | list[tuple | list]
)
type SeriesData = list[tuple[str, list[tuple[float, float]]]]


class LineChart(ftc.LineChart):
    """
    折线图组件，继承自 flet_charts.LineChart。

    参考 Streamlit 的 st.line_chart 参数风格，简化数据传入方式，
    并提供美观的默认样式。

    Parameters
    ----------
        data : DataInput
            折线图数据。支持以下格式：
            - 字典列表: [{"x": 1, "y": 2}, {"x": 2, "y": 3}, ...]
            - 列字典: {"x": [1,2,3], "y": [4,5,6], "z": [7,8,9]}
            - 数值列表: [1, 2, 3, 4, 5]（自动产生 x 轴）
            - 元组列表: [(1,2), (2,3), (3,5), ...]
        x : str, optional
            用作 x 轴的列名。当 data 为列字典或字典列表时有效。
        y : str or list of str, optional
            用作 y 轴的列名。支持传入多个列名绘制多条折线。
        width : int or float, optional
            图表宽度。默认由容器自动决定。
        height : int or float, optional
            图表高度。默认为 400。
        use_container_width : bool, optional
            是否撑满容器宽度。默认为 True。
        title : str, optional
            图表标题。默认为 None。
        color : str or list of str, optional
            折线颜色。自动使用内置配色方案。
        curved : bool, optional
            是否使用平滑曲线。默认为 True。
        show_grid : bool, optional
            是否显示网格线。默认为 True。
        show_legend : bool, optional
            是否显示图例（通过左轴标题显示）。默认为 True。
        tooltip : bool, optional
            是否显示悬停提示。默认为 True。
        stroke_width : int or float, optional
            线条粗细。默认为 2.0。
        show_points : bool, optional
            是否显示数据点标记。默认为 False。
        interactive : bool, optional
            是否支持交互。默认为 True。
        **kwargs : dict
            其他传递给 flet_charts.LineChart 的参数。

    Examples
    --------
    >>> import flet as ft
    >>> from cs_ui.chart.line_chart import LineChart
    >>>
    >>> # 简单数值列表
    >>> chart = LineChart(data=[1, 3, 2, 5, 4, 6, 8])
    >>>
    >>> # 字典列表
    >>> chart = LineChart(
    ...     data=[{"x": 1, "y": 3}, {"x": 2, "y": 5}, {"x": 3, "y": 2}],
    ...     x="x", y="y"
    ... )
    >>>
    >>> # 多条折线 (列字典)
    >>> chart = LineChart(
    ...     data={"月份": [1,2,3], "销量A": [3,5,2], "销量B": [4,6,3]},
    ...     x="月份",
    ...     y=["销量A", "销量B"]
    ... )
    >>>
    >>> # 元组列表
    >>> chart = LineChart(data=[(1,3),(2,5),(3,2)])
    """

    def __init__(
        self,
        data: DataInput | None = None,
        x: str | None = None,
        y: str | list[str] | None = None,
        width: int | float | None = None,
        height: int | float | None = 400,
        use_container_width: bool = True,
        title: str | None = None,
        color: str | list[str] | None = None,
        curved: bool = True,
        show_grid: bool = True,
        show_legend: bool = True,
        tooltip: bool = True,
        stroke_width: int | float = 2.0,
        show_points: bool = False,
        interactive: bool = True,
        **kwargs,
    ) -> None:
        colors = self._resolve_colors(color, 1)

        if data is not None:
            parsed_data, series_names = self._parse_data(data, x, y)
            n_series = len(series_names) or 1
            colors = self._resolve_colors(color, n_series)

            data_series = [
                ftc.LineChartData(
                    points=self._build_data_points(
                        points, colors[i % len(colors)], show_points
                    ),
                    color=colors[i % len(colors)],
                    stroke_width=float(stroke_width),
                    curved=curved,
                    prevent_curve_over_shooting=True,
                )
                for i, (_, points) in enumerate(parsed_data)
            ]
        else:
            data_series = []

        super().__init__(
            data_series=data_series,
            width=width,
            height=height,
            expand=use_container_width or None,
            interactive=interactive,
            bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.GREY_900),
            border=ft.Border(
                **{
                    side: ft.BorderSide(
                        0.5, ft.Colors.with_opacity(0.08, ft.Colors.GREY_700)
                    )
                    for side in ("left", "top", "right", "bottom")
                }
            ),
            left_axis=ftc.ChartAxis(
                show_labels=True, labels=[], title=None, title_size=12
            ),
            bottom_axis=ftc.ChartAxis(
                show_labels=True, labels=[], title=None, title_size=12
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
                        stroke_color=ft.Colors.WHITE,
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
        """构建网格线配置。"""
        return (
            ftc.ChartGridLines(
                color=ft.Colors.with_opacity(0.1, ft.Colors.GREY_700),
                width=0.5,
            )
            if show_grid
            else None
        )

    @staticmethod
    def _build_tooltip(tooltip: bool) -> ftc.LineChartTooltip | None:
        """构建悬停提示配置。"""
        return (
            ftc.LineChartTooltip(
                bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.GREY_900),
                border_radius=8,
                padding=10,
                max_width=180,
            )
            if tooltip
            else None
        )

    # ------------------------------------------------------------------
    # 数据解析
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_data(
        data: DataInput, x: str | None, y: str | list[str] | None
    ) -> tuple[SeriesData, list[str]]:
        """解析数据，返回 (series_list, series_names)。"""
        match data:
            case dict():
                return LineChart._parse_dict_data(data, x, y)
            case [dict(), *_]:
                return LineChart._parse_dict_list_data(cast(list[dict], data), x, y)
            case [(list() | tuple()), *_]:
                return LineChart._parse_tuple_list_data(cast(list[tuple | list], data))
            case [int() | float(), *_] | (int() | float(), *_):
                return LineChart._parse_value_list_data(
                    cast(Sequence[int | float], data)
                )
            case _:
                return [], []

    @staticmethod
    def _resolve_y_keys(
        keys: list[str], x_key: str, y: str | list[str] | None
    ) -> list[str]:
        """统一解析 y 轴列名。"""
        match y:
            case str():
                return [y]
            case list():
                return y
            case _:
                return [k for k in keys if k != x_key]

    @staticmethod
    def _parse_dict_data(
        data: dict[str, list[int | float]],
        x: str | None,
        y: str | list[str] | None,
    ) -> tuple[SeriesData, list[str]]:
        """解析列字典格式: {"x": [1,2,3], "y": [4,5,6]}。"""
        keys = list(data.keys())
        if not keys:
            return [], []

        x_key = x or keys[0]
        x_values = data.get(x_key, [])
        if not x_values:
            return [], []

        y_keys = LineChart._resolve_y_keys(keys, x_key, y)
        result = [
            (
                y_key,
                [
                    (float(x_values[i]), float(data[y_key][i]))
                    for i in range(min(len(x_values), len(data[y_key])))
                ],
            )
            for y_key in y_keys
            if y_key in data
        ]
        return result, [y_key for y_key in y_keys if y_key in data]

    @staticmethod
    def _parse_dict_list_data(
        data: list[dict[str, int | float]],
        x: str | None,
        y: str | list[str] | None,
    ) -> tuple[SeriesData, list[str]]:
        """解析字典列表格式: [{"x":1,"y":2}, {"x":2,"y":3}]。"""
        if not data:
            return [], []

        keys = list(data[0].keys())
        x_key = x or keys[0]
        y_keys = LineChart._resolve_y_keys(keys, x_key, y)

        if not y_keys:
            return [], []

        result = [
            (
                y_key,
                [
                    (float(row[x_key]), float(row[y_key]))
                    for row in data
                    if x_key in row and y_key in row
                ],
            )
            for y_key in y_keys
        ]
        return result, y_keys

    @staticmethod
    def _parse_tuple_list_data(
        data: list[tuple | list],
    ) -> tuple[SeriesData, list[str]]:
        """解析元组/列表列表: [(1,2), (2,3)]。"""
        points = [
            (float(item[0]), float(item[1]))
            for item in data
            if isinstance(item, (list, tuple)) and len(item) >= 2
        ]
        return [("series", points)], ["series"]

    @staticmethod
    def _parse_value_list_data(
        data: Sequence[int | float],
    ) -> tuple[SeriesData, list[str]]:
        """解析数值列表: [1, 2, 3, 4, 5]。"""
        points = [(float(i), float(val)) for i, val in enumerate(data)]
        return [("series", points)], ["series"]

    # ------------------------------------------------------------------
    # 颜色解析
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_colors(color: str | list[str] | None, count: int) -> list[str]:
        """解析并分配颜色。"""
        match color:
            case str():
                return [color] * count
            case list():
                return (
                    color[:count]
                    if len(color) >= count
                    else color + LINE_COLORS[count - len(color) :]
                )
            case _:
                return LINE_COLORS[:count]


# ======================================================================
# 声明式示例 (ft.component)
# ======================================================================


@ft.component
def App() -> ft.Column:
    """LineChart 组件运行示例，展示所有数据格式和常用配置。"""
    heading = lambda text: ft.Text(
        text, size=16, weight=ft.FontWeight.BOLD, color="#1f2937"
    )
    subtitle = lambda text: ft.Text(text, size=12, color="#6b7280")

    return ft.Column(
        controls=[
            ft.Text(
                "LineChart 折线图组件",
                size=28,
                weight=ft.FontWeight.BOLD,
                color="#1f2937",
            ),
            ft.Text("支持多种数据格式，自动配色，交互式提示", size=14, color="#6b7280"),
            ft.Divider(),
            # 1. 简单数值列表
            heading("1. 数值列表 → 自动生成 X 轴索引"),
            subtitle("data=[1, 3, 2, 5, 4, 6, 8]"),
            LineChart(data=[1, 3, 2, 5, 4, 6, 8], height=250, show_points=True),
            ft.Divider(),
            # 2. 字典列表
            heading("2. 字典列表"),
            subtitle("data=[{'x':1,'y':3}, {'x':2,'y':5}, ...]"),
            LineChart(
                data=[
                    {"x": 1, "y": 3},
                    {"x": 2, "y": 5},
                    {"x": 3, "y": 2},
                    {"x": 4, "y": 7},
                    {"x": 5, "y": 4},
                ],
                x="x",
                y="y",
                height=250,
                color="#10b981",
            ),
            ft.Divider(),
            # 3. 多条折线 (列字典)
            heading("3. 多条折线 (列字典)"),
            subtitle("data={'月份':[1..5], '销量A':[...], '销量B':[...]}"),
            LineChart(
                data={
                    "月份": [1, 2, 3, 4, 5],
                    "销量A": [3, 5, 2, 7, 4],
                    "销量B": [4, 6, 3, 8, 5],
                },
                x="月份",
                y=["销量A", "销量B"],
                height=280,
                curved=True,
                show_points=True,
            ),
            ft.Divider(),
            # 4. 元组列表
            heading("4. 元组列表"),
            subtitle("data=[(1,3), (2,5), (3,2), (4,7), (5,4)]"),
            LineChart(
                data=[(1, 3), (2, 5), (3, 2), (4, 7), (5, 4)],
                height=250,
                color="#8b5cf6",
                show_points=True,
            ),
            ft.Divider(),
            # 5. 无网格无提示
            heading("5. 无网格、无提示、粗线条"),
            subtitle("show_grid=False, tooltip=False, stroke_width=3.0"),
            LineChart(
                data=[(1, 2), (2, 5), (3, 3), (4, 8), (5, 6)],
                height=220,
                color="#ef4444",
                show_grid=False,
                tooltip=False,
                stroke_width=3.0,
            ),
            ft.Divider(),
            # 6. 多条折线 (字典列表)
            heading("6. 多条折线 (字典列表)"),
            subtitle("y=['销售额', '利润']"),
            LineChart(
                data=[
                    {"月份": 1, "销售额": 10, "利润": 3},
                    {"月份": 2, "销售额": 15, "利润": 5},
                    {"月份": 3, "销售额": 12, "利润": 4},
                    {"月份": 4, "销售额": 20, "利润": 8},
                    {"月份": 5, "销售额": 18, "利润": 7},
                ],
                x="月份",
                y=["销售额", "利润"],
                height=280,
                show_points=True,
            ),
            ft.Divider(),
            # 7. 大量数据
            heading("7. 大量数据 (50个点)，平滑曲线"),
            subtitle("curved=True, show_points=False"),
            LineChart(
                data=[
                    (i, 10 + 5 * math.sin(i * 0.3) + 3 * math.cos(i * 0.7))
                    for i in range(50)
                ],
                height=280,
                curved=True,
                show_points=False,
                color="#06b6d4",
            ),
        ],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
