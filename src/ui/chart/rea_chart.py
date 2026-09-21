"""面积图组件 (AreaChart)

基于 ``flet_charts.LineChart`` 的“线下填充”能力封装，参考 Streamlit
``st.area_chart`` 的参数风格，提供更简洁、美观的面积图绘制能力。

面积图与折线图共用同一套数据解析逻辑，只是额外为每条序列填充
线条与基准线之间的区域。
"""

from __future__ import annotations

import flet as ft
import flet_charts as ftc

from ui.chart._data import (
    DataInput,
    parse_data,
    resolve_colors,
    resolve_x_labels,
    x_axis_label_size,
    x_axis_labels,
    y_axis_label_size,
)

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
        opacity: 填充区域的透明度（0~1），默认 0.22。
        curved: 是否使用平滑曲线，默认 True。
        gradient: 是否使用自上而下的渐变填充，默认 True。
        show_grid: 是否显示网格线，默认 True。
        tooltip: 是否显示悬停提示，默认 True。
        stroke_width: 线条粗细，默认 2.0。
        show_points: 是否显示数据点，默认 False。
        **kwargs: 其他传递给 ``flet_charts.LineChart`` 的参数。
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
        opacity: float = 0.22,
        curved: bool = True,
        gradient: bool = True,
        show_grid: bool = True,
        tooltip: bool = True,
        stroke_width: int | float = 2.0,
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
                                stroke_color=ft.Colors.WHITE,
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
                            ft.Colors.with_opacity(opacity * 1.6, colors[i % len(colors)]),
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
                title=None,
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
            vertical_grid_lines=(
                ftc.ChartGridLines(
                    color=ft.Colors.with_opacity(0.1, ft.Colors.GREY_700),
                    width=0.5,
                )
                if show_grid
                else None
            ),
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


# ======================================================================
# 声明式示例 (ft.component)
# ======================================================================


@ft.component
def App() -> ft.Column:
    """AreaChart 组件运行示例。"""
    import math

    def heading(text: str) -> ft.Text:
        return ft.Text(text, size=16, weight=ft.FontWeight.BOLD, color="#1f2937")

    def subtitle(text: str) -> ft.Text:
        return ft.Text(text, size=12, color="#6b7280")

    return ft.Column(
        controls=[
            ft.Text(
                "AreaChart 面积图组件",
                size=28,
                weight=ft.FontWeight.BOLD,
                color="#1f2937",
            ),
            ft.Text("折线 + 区域填充，支持渐变与多层叠加", size=14, color="#6b7280"),
            ft.Divider(),
            heading("1. 数值列表"),
            subtitle("data=[3, 7, 5, 9, 6, 11, 8]"),
            AreaChart(data=[3, 7, 5, 9, 6, 11, 8], height=240, color="#1f6feb"),
            ft.Divider(),
            heading("2. 多层面积"),
            subtitle("y=['访问量', '转化量']"),
            AreaChart(
                data={
                    "日期": list(range(1, 13)),
                    "访问量": [20 + 6 * math.sin(i * 0.6) for i in range(12)],
                    "转化量": [10 + 3 * math.cos(i * 0.5) for i in range(12)],
                },
                x="日期",
                y=["访问量", "转化量"],
                height=280,
                show_points=True,
                color=["#1f6feb", "#10b981"],
            ),
            ft.Divider(),
            heading("3. 纯色填充（无渐变）"),
            subtitle("gradient=False, opacity=0.35"),
            AreaChart(
                data=[(1, 3), (2, 6), (3, 4), (4, 8), (5, 5)],
                height=240,
                color="#f59e0b",
                gradient=False,
                opacity=0.35,
            ),
        ],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
