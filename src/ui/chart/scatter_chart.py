"""散点图组件 (ScatterChart)

基于 ``flet_charts.ScatterChart`` 封装，参考 Streamlit ``st.scatter_chart`` 的
参数风格，提供更简洁、美观的散点图绘制能力。

支持：
- 单组/多组散点
- 字典、列表、元组多种数据格式
- 每个点可自定义颜色与半径
- 自动坐标轴标签
"""

from __future__ import annotations

import flet as ft
import flet_charts as ftc

from ui.chart._data import (
    CHART_COLORS,
    DataInput,
    axis_labels,
    data_bounds,
    parse_data,
    resolve_colors,
    x_axis_label_size,
    y_axis_label_size,
)

__all__ = ["ScatterChart"]


class ScatterChart(ftc.ScatterChart):
    """散点图组件，继承自 :class:`flet_charts.ScatterChart`。

    Args:
        data: 散点数据，支持字典列表 / 列字典 / 数值列表 / 元组列表，
            格式与 :class:`~ui.chart.bar_chart.BarChart` 一致。
        x: 用作 x 轴的列名。
        y: 用作 y 轴的列名，可传列表绘制多组散点。
        height: 图表高度，默认 400。
        width: 图表宽度，默认由容器决定。
        use_container_width: 是否撑满容器宽度，默认 True。
        color: 散点颜色，可传列表按组配色。
        radius: 散点半径，默认 6。
        show_grid: 是否显示网格线，默认 True。
        tooltip: 是否显示悬停提示，默认 True。
        show_x_labels: 是否显示 x 轴标签，默认 True。
        **kwargs: 其他传递给 ``flet_charts.ScatterChart`` 的参数。
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
        radius: int | float = 6,
        show_grid: bool = True,
        tooltip: bool = True,
        show_x_labels: bool = True,
        **kwargs,
    ) -> None:
        series, names = parse_data(data, x, y) if data is not None else ([], [])
        colors = resolve_colors(color, max(len(names), 1))

        spots = [
            ftc.ScatterChartSpot(
                x=px,
                y=py,
                radius=radius,
                color=colors[s_index % len(colors)],
                tooltip=f"{name}: ({px:g}, {py:g})",
            )
            for s_index, (name, points) in enumerate(series)
            for px, py in points
        ]

        min_x, max_x = data_bounds(series)

        super().__init__(
            spots=spots,
            width=width,
            height=height,
            expand=use_container_width or None,
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
                        ftc.ChartAxisLabel(value=v, label=f"{v:g}")
                        for v, _ in axis_labels(min_x, max_x, 6)
                    ]
                    if show_x_labels
                    else []
                ),
                label_size=x_axis_label_size(axis_labels(min_x, max_x, 6)),
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
            vertical_grid_lines=(
                ftc.ChartGridLines(
                    color=ft.Colors.with_opacity(0.1, ft.Colors.GREY_700),
                    width=0.5,
                )
                if show_grid
                else None
            ),
            tooltip=ftc.ScatterChartTooltip(
                bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.GREY_900),
                border_radius=8,
                padding=10,
            )
            if tooltip
            else None,
            **kwargs,
        )


# ======================================================================
# 声明式示例 (ft.component)
# ======================================================================


@ft.component
def App() -> ft.Column:
    """ScatterChart 组件运行示例。"""
    import math

    def heading(text: str) -> ft.Text:
        return ft.Text(text, size=16, weight=ft.FontWeight.BOLD, color="#1f2937")

    def subtitle(text: str) -> ft.Text:
        return ft.Text(text, size=12, color="#6b7280")

    return ft.Column(
        controls=[
            ft.Text(
                "ScatterChart 散点图组件",
                size=28,
                weight=ft.FontWeight.BOLD,
                color="#1f2937",
            ),
            ft.Text("支持多组散点、自定义半径与配色", size=14, color="#6b7280"),
            ft.Divider(),
            heading("1. 元组列表"),
            subtitle("data=[(1,3), (2,5), (3,2), (4,7), (5,4)]"),
            ScatterChart(
                data=[(1, 3), (2, 5), (3, 2), (4, 7), (5, 4)],
                height=240,
                color="#8b5cf6",
            ),
            ft.Divider(),
            heading("2. 多组散点"),
            subtitle("按组自动配色"),
            ScatterChart(
                data={
                    "x": list(range(20)),
                    "组A": [10 + 5 * math.sin(i * 0.5) for i in range(20)],
                    "组B": [6 + 4 * math.cos(i * 0.7) for i in range(20)],
                },
                x="x",
                y=["组A", "组B"],
                height=280,
                radius=5,
                color=["#1f6feb", "#ef4444"],
            ),
        ],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
