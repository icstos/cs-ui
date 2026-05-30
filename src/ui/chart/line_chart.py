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

from typing import Dict, List, Optional, Sequence, Tuple, Union, cast

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

DataRow = Union[Dict[str, Union[int, float]], Tuple, List]
DataInput = Union[
    List[DataRow],
    Dict[str, List[Union[int, float]]],
    List[Union[int, float]],
    Tuple[Union[int, float], ...],
    List[Union[Tuple, List]],
]


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
            如果为 None 且 data 为字典列表，尝试自动查找 x 轴数据。
        y : str or list of str, optional
            用作 y 轴的列名。支持传入多个列名绘制多条折线。
            如果为 None，自动选择非 x 列的数值列。
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
        data: Optional[DataInput] = None,
        x: Optional[str] = None,
        y: Optional[Union[str, List[str]]] = None,
        width: Optional[Union[int, float]] = None,
        height: Optional[Union[int, float]] = 400,
        use_container_width: bool = True,
        title: Optional[str] = None,
        color: Optional[Union[str, List[str]]] = None,
        curved: bool = True,
        show_grid: bool = True,
        show_legend: bool = True,
        tooltip: bool = True,
        stroke_width: Union[int, float] = 2.0,
        show_points: bool = False,
        interactive: bool = True,
        **kwargs,
    ):
        # --- 构建数据系列 ---
        data_series = []

        if data is not None:
            parsed_data, series_names = self._parse_data(data, x, y)
            colors = self._resolve_colors(
                color, len(series_names) if series_names else 1
            )

            for i, (sname, points) in enumerate(parsed_data):
                color_hex = colors[i % len(colors)]
                line_color = color_hex

                # 构建数据点
                data_points = []
                for x_val, y_val in points:
                    dp = ftc.LineChartDataPoint(x=float(x_val), y=float(y_val))
                    if show_points:
                        dp.point = ftc.ChartCirclePoint(
                            color=color_hex,
                            radius=3.5,
                            stroke_color=ft.Colors.WHITE,
                            stroke_width=1.5,
                        )
                    data_points.append(dp)

                # 构建系列数据
                series = ftc.LineChartData(
                    points=data_points,
                    color=line_color,
                    stroke_width=float(stroke_width),
                    curved=curved,
                    prevent_curve_over_shooting=True,
                )
                data_series.append(series)

        # --- 构建轴 ---
        left_axis = ftc.ChartAxis(
            show_labels=True, labels=[], title=None, title_size=12
        )

        bottom_axis = ftc.ChartAxis(
            show_labels=True, labels=[], title=None, title_size=12
        )

        # --- 网格线 ---
        grid_lines = None
        if show_grid:
            grid_lines = ftc.ChartGridLines(
                color=ft.Colors.with_opacity(0.1, ft.Colors.GREY_700), width=0.5
            )

        # --- 提示框 ---
        chart_tooltip = None
        if tooltip:
            chart_tooltip = ftc.LineChartTooltip(
                bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.GREY_900),
                border_radius=8,
                padding=10,
                max_width=180,
            )

        super().__init__(
            data_series=data_series,
            width=width,
            height=height,
            expand=True if use_container_width else None,
            interactive=interactive,
            bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.GREY_900),
            border=ft.Border(
                left=ft.BorderSide(
                    0.5, ft.Colors.with_opacity(0.08, ft.Colors.GREY_700)
                ),
                top=ft.BorderSide(
                    0.5, ft.Colors.with_opacity(0.08, ft.Colors.GREY_700)
                ),
                right=ft.BorderSide(
                    0.5, ft.Colors.with_opacity(0.08, ft.Colors.GREY_700)
                ),
                bottom=ft.BorderSide(
                    0.5, ft.Colors.with_opacity(0.08, ft.Colors.GREY_700)
                ),
            ),
            left_axis=left_axis,
            bottom_axis=bottom_axis,
            horizontal_grid_lines=grid_lines,
            vertical_grid_lines=grid_lines,
            tooltip=chart_tooltip,
            min_x=None,
            max_x=None,
            min_y=None,
            max_y=None,
            **kwargs,
        )

    # ------------------------------------------------------------------
    # 数据解析
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_data(
        data: DataInput, x: Optional[str], y: Optional[Union[str, List[str]]]
    ) -> Tuple[List[Tuple[str, List[Tuple[float, float]]]], List[str]]:
        """
        解析数据，返回 (series_list, series_names)。
        series_list: [(系列名, [(x1, y1), (x2, y2), ...]), ...]
        """
        if isinstance(data, dict):
            return LineChart._parse_dict_data(data, x, y)
        if isinstance(data, (list, tuple)):
            if not data:
                return [], []
            # 判断元素类型
            first = data[0]
            if isinstance(first, dict):
                return LineChart._parse_dict_list_data(cast(List[Dict], data), x, y)
            if isinstance(first, (list, tuple)):
                return LineChart._parse_tuple_list_data(
                    cast(List[Union[Tuple, List]], data)
                )
            # 数值列表
            return LineChart._parse_value_list_data(
                cast(Sequence[Union[int, float]], data)
            )
        return [], []

    @staticmethod
    def _parse_dict_data(
        data: Dict[str, List[Union[int, float]]],
        x: Optional[str],
        y: Optional[Union[str, List[str]]],
    ) -> Tuple[List[Tuple[str, List[Tuple[float, float]]]], List[str]]:
        """解析列字典格式: {"x": [1,2,3], "y": [4,5,6]}"""
        keys = list(data.keys())
        if not keys:
            return [], []

        x_key = x or keys[0]
        x_values = data.get(x_key, [])
        if not x_values:
            return [], []

        y_keys: List[str] = []
        if isinstance(y, str):
            y_keys = [y]
        elif isinstance(y, list):
            y_keys = y
        else:
            y_keys = [k for k in keys if k != x_key]

        result = []
        for y_key in y_keys:
            if y_key not in data:
                continue
            y_values = data[y_key]
            points = [
                (float(x_values[i]), float(y_values[i]))
                for i in range(min(len(x_values), len(y_values)))
            ]
            result.append((y_key, points))

        return result, y_keys

    @staticmethod
    def _parse_dict_list_data(
        data: List[Dict[str, Union[int, float]]],
        x: Optional[str],
        y: Optional[Union[str, List[str]]],
    ) -> Tuple[List[Tuple[str, List[Tuple[float, float]]]], List[str]]:
        """解析字典列表格式: [{"x":1,"y":2}, {"x":2,"y":3}]"""
        if not data:
            return [], []

        keys = list(data[0].keys())

        x_key = x or keys[0]
        y_keys: List[str] = []
        if isinstance(y, str):
            y_keys = [y]
        elif isinstance(y, list):
            y_keys = y
        else:
            y_keys = [k for k in keys if k != x_key]

        if not y_keys:
            return [], []

        result = []
        for y_key in y_keys:
            points = []
            for row in data:
                if x_key in row and y_key in row:
                    points.append((float(row[x_key]), float(row[y_key])))
            result.append((y_key, points))

        return result, y_keys

    @staticmethod
    def _parse_tuple_list_data(
        data: List[Union[Tuple, List]],
    ) -> Tuple[List[Tuple[str, List[Tuple[float, float]]]], List[str]]:
        """解析元组/列表列表: [(1,2), (2,3)]"""
        points = []
        for item in data:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                points.append((float(item[0]), float(item[1])))
        return [("series", points)], ["series"]

    @staticmethod
    def _parse_value_list_data(
        data: Sequence[Union[int, float]],
    ) -> Tuple[List[Tuple[str, List[Tuple[float, float]]]], List[str]]:
        """解析数值列表: [1, 2, 3, 4, 5]"""
        points = [(float(i), float(val)) for i, val in enumerate(data)]
        return [("series", points)], ["series"]

    # ------------------------------------------------------------------
    # 颜色解析
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_colors(
        color: Optional[Union[str, List[str]]], count: int
    ) -> List[str]:
        """解析并分配颜色"""
        if isinstance(color, str):
            return [color] * count
        if isinstance(color, list):
            return (
                color[:count]
                if len(color) >= count
                else color + LINE_COLORS[: count - len(color)]
            )
        return LINE_COLORS[:count]
