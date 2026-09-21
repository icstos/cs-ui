"""柱状图组件 (BarChart)

基于 ``flet_charts.BarChart`` 封装，参考 Streamlit ``st.bar_chart`` 的参数风格，
提供更简洁、美观的柱状图绘制能力。

支持：
- 单组/多组柱状（分组或堆叠）
- 字典、列表、元组多种数据格式
- 自动坐标轴标签
- 美观的默认配色和圆角
"""

from __future__ import annotations

import flet as ft
import flet_charts as ftc

from ui.chart._data import (
    CHART_COLORS,
    DataInput,
    data_bounds,
    parse_data,
    resolve_colors,
    resolve_x_labels,
    x_axis_label_size,
    x_axis_labels,
    y_axis_label_size,
)

__all__ = ["BarChart"]


class BarChart(ftc.BarChart):
    """柱状图组件，继承自 :class:`flet_charts.BarChart`。

    Args:
        data: 柱状图数据。支持以下格式：
            - 字典列表: ``[{"x": 1, "y": 2}, ...]``
            - 列字典: ``{"月份": [1,2,3], "销量": [4,5,6]}``
            - 数值列表: ``[1, 2, 3, 4, 5]``
            - 元组列表: ``[(1, 2), (2, 3), ...]``
        x: 用作 x 轴的列名。
        y: 用作 y 轴的列名，可传列表绘制多组柱状。
        height: 图表高度，默认 400。
        width: 图表宽度，默认由容器决定。
        use_container_width: 是否撑满容器宽度，默认 True。
        color: 柱体颜色，可传列表为每组分别配色。
        stacked: 是否堆叠显示（默认 False，即分组并列显示）。
        rod_width: 单个柱体宽度，默认根据数据量自适应。
        group_spacing: 组间距，默认 16。
        show_grid: 是否显示网格线，默认 True。
        tooltip: 是否显示悬停提示，默认 True。
        border_radius: 柱体顶部圆角，默认 4。
        show_x_labels: 是否显示 x 轴标签，默认 True。
        **kwargs: 其他传递给 ``flet_charts.BarChart`` 的参数。
    """

    def __init__(
        self,
        data: DataInput | None = None,
        x: str | None = None,
        y: str | list[str] | None = None,
        width: int | float | None = None,
        height: int | float = 400,
        use_container_width: bool = True,
        color: str | list[str] | None = None,
        stacked: bool = False,
        rod_width: int | float | None = None,
        group_spacing: int | float = 16,
        show_grid: bool = True,
        tooltip: bool = True,
        border_radius: int | float = 4,
        show_x_labels: bool = True,
        **kwargs,
    ) -> None:
        series, names = parse_data(data, x, y) if data is not None else ([], [])
        colors = resolve_colors(color, max(len(names), 1))

        x_values: list[float] = []
        if series:
            x_values = [p[0] for p in series[0][1]]

        width_value = rod_width if rod_width is not None else self._auto_rod_width(
            len(x_values), len(series)
        )

        groups = [
            ftc.BarChartGroup(
                x=i,
                rods=[
                    self._build_rod(
                        s_index,
                        points[i][1] if i < len(points) else 0,
                        colors[s_index % len(colors)],
                        width_value,
                        stacked,
                        border_radius,
                    )
                    for s_index, (_name, points) in enumerate(series)
                ],
                group_vertically=stacked,
            )
            for i in range(len(x_values))
        ]

        min_x, max_x = data_bounds(series)
        x_labels = x_axis_labels(series, resolve_x_labels(data, x) if data else None)

        super().__init__(
            groups=groups,
            width=width,
            height=height,
            expand=use_container_width or None,
            group_spacing=group_spacing,
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
                    [
                        ftc.ChartAxisLabel(value=v, label=text)
                        for v, text in x_labels
                    ]
                    if show_x_labels
                    else []
                ),
                label_size=x_axis_label_size(x_labels),
                show_min=False,
                show_max=False,
            ),
            horizontal_grid_lines=(
                ftc.ChartGridLines(
                    color=ft.Colors.with_opacity(0.1, ft.Colors.GREY_700),
                    width=0.5,
                )
                if show_grid
                else None
            ),
            tooltip=ftc.BarChartTooltip(
                bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.GREY_900),
                border_radius=8,
                padding=10,
            )
            if tooltip
            else None,
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
    def _build_rod(
        series_index: int,
        value: float,
        color: str,
        width_value: int,
        stacked: bool,
        border_radius: int | float,
    ) -> ftc.BarChartRod:
        """构建单个柱体。"""
        if stacked:
            return ftc.BarChartRod(
                to_y=value,
                width=width_value,
                color=color,
                border_radius=border_radius
                if series_index == 0
                else ft.BorderRadius.only(top_left=0, top_right=0),
                tooltip=f"{value:g}",
            )
        return ftc.BarChartRod(
            to_y=value,
            width=width_value,
            color=color,
            border_radius=border_radius,
            tooltip=f"{value:g}",
        )


# ======================================================================
# 声明式示例 (ft.component)
# ======================================================================


@ft.component
def App() -> ft.Column:
    """BarChart 组件运行示例。"""

    def heading(text: str) -> ft.Text:
        return ft.Text(text, size=16, weight=ft.FontWeight.BOLD, color="#1f2937")

    def subtitle(text: str) -> ft.Text:
        return ft.Text(text, size=12, color="#6b7280")

    return ft.Column(
        controls=[
            ft.Text(
                "BarChart 柱状图组件",
                size=28,
                weight=ft.FontWeight.BOLD,
                color="#1f2937",
            ),
            ft.Text("支持分组、堆叠，自动配色与标签", size=14, color="#6b7280"),
            ft.Divider(),
            heading("1. 数值列表"),
            subtitle("data=[12, 18, 9, 22, 15]"),
            BarChart(data=[12, 18, 9, 22, 15], height=240, color=CHART_COLORS[0]),
            ft.Divider(),
            heading("2. 多组并列"),
            subtitle("data={'月份':[...], '销量A':[...], '销量B':[...]}"),
            BarChart(
                data={
                    "月份": [1, 2, 3, 4, 5],
                    "销量A": [3, 5, 2, 7, 4],
                    "销量B": [4, 6, 3, 8, 5],
                },
                x="月份",
                y=["销量A", "销量B"],
                height=260,
            ),
            ft.Divider(),
            heading("3. 堆叠柱状"),
            subtitle("stacked=True"),
            BarChart(
                data={
                    "季度": [1, 2, 3, 4],
                    "线上": [12, 18, 15, 22],
                    "线下": [8, 6, 10, 9],
                },
                x="季度",
                y=["线上", "线下"],
                stacked=True,
                height=260,
                color=["#1f6feb", "#10b981"],
            ),
        ],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
