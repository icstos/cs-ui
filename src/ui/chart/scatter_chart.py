"""散点图 (ScatterChart) —— 用点的分布看相关性。

基于 ``flet_charts.ScatterChart`` 封装，数据格式与柱状图一致。与折线图最大的
区别是**不连线**：每个观测独立落点，位置同时编码两个数值，所以适合回答
「x 变大时 y 会不会跟着变」，而不是「第 3 个月比第 2 个月高多少」。

散点没有自带图例（flet_charts 的 ScatterChart 也没有图例位），多组对照时由
调用方在图表上方放一行色点说明。

用法::

    ScatterChart(
        data={"花费": [12, 18, 25], "转化率": [2.1, 2.8, 3.4]},
        x="花费",
        y="转化率",
        height=280,
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

__all__ = ["ScatterChart"]


def _legend(names: list[str], colors: list[str]) -> ft.Control:
    """多组散点的图例：由调用方摆，组件本身不占这块空间。"""
    return ft.Row(
        spacing=18,
        controls=[
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
        ],
    )


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
        radius: 散点半径，所有点共用，默认 6。
        show_grid: 是否显示网格线，默认 True。
        tooltip: 是否显示悬停提示（多组时带组名），默认 True。
        show_x_labels: 是否显示 x 轴标签，默认 True。
        **kwargs: 其他传递给 :class:`flet_charts.ScatterChart` 的参数。
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
        radius: float = 6,
        show_grid: bool = True,
        tooltip: bool = True,
        show_x_labels: bool = True,
        **kwargs,
    ) -> None:
        series, names = parse_data(data, x, y) if data is not None else ([], [])
        colors = resolve_colors(color, max(len(names), 1))
        multi = len(series) > 1

        spots = [
            ftc.ScatterChartSpot(
                x=px,
                y=py,
                radius=radius,
                color=colors[s_index % len(colors)],
                tooltip=(f"{name} ({px:g}, {py:g})" if multi else f"({px:g}, {py:g})"),
            )
            for s_index, (name, points) in enumerate(series)
            for px, py in points
        ]

        x_labels = x_axis_labels(
            series, resolve_x_labels(data, x) if data is not None else None
        )

        super().__init__(
            spots=spots,
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
                label_size=x_axis_label_size(x_labels),
                show_min=False,
                show_max=False,
            ),
            horizontal_grid_lines=self._grid_lines(show_grid),
            vertical_grid_lines=self._grid_lines(show_grid),
            tooltip=(
                ftc.ScatterChartTooltip(
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
        """网格线走角色色，避免深色主题下淡到看不见。"""
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
    """单组：广告花费与转化率的正相关，右上角是值得复盘的样本。"""
    return ScatterChart(
        data={
            "花费": [8, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31, 34, 37, 41],
            "转化率": [
                1.9,
                2.1,
                2.4,
                2.2,
                2.6,
                2.9,
                3.1,
                3.0,
                3.4,
                3.6,
                3.5,
                3.9,
                4.2,
                4.4,
                4.9,
            ],
        },
        x="花费",
        y="转化率",
        height=280,
    )


def _bubbles() -> ft.Control:
    """多组 + 大半径：两组样本在同一坐标系里比较分布范围。"""
    return ft.Column(
        spacing=8,
        controls=[
            _legend(["新客", "老客"], CHART_COLORS[:2]),
            ScatterChart(
                data={
                    "客单价": [120, 138, 151, 166, 174, 189, 203, 218, 236, 251],
                    "新客复购率": [12, 15, 14, 19, 18, 23, 21, 26, 25, 29],
                    "老客复购率": [31, 35, 33, 38, 41, 39, 44, 47, 46, 52],
                },
                x="客单价",
                y=["新客复购率", "老客复购率"],
                height=280,
                radius=10,
            ),
        ],
    )


def _quadrant() -> ft.Control:
    """负值区间：x / y 同时出现负数时，原点落在图中间而不是角上。"""
    return ScatterChart(
        data=[
            (-8.2, -3.1),
            (-6.4, -2.2),
            (-5.1, -1.4),
            (-3.8, -0.6),
            (-2.2, 0.8),
            (-0.9, 1.6),
            (0.6, 2.1),
            (1.8, 3.4),
            (3.2, 4.1),
            (4.7, 4.8),
            (6.1, 5.9),
            (7.4, 6.2),
        ],
        height=260,
        radius=5,
        color=CHART_COLORS[4],
        show_grid=False,
    )


_BASIC_CODE = """ScatterChart(
    data={
        "花费": [8, 13, 19, 25, 31],
        "转化率": [1.9, 2.4, 2.9, 3.4, 3.9],
    },
    x="花费",
    y="转化率",
    height=280,
)

# 多组：y 传列表，颜色按组分配；散点没有内置图例，需要自己摆一行
ScatterChart(data=rows, x="客单价", y=["新客复购率", "老客复购率"], radius=8)"""

SPEC = Spec(
    name="ScatterChart",
    summary="把成对观测画成点，用分布形状判断相关性。",
    definition=(
        "散点图不连点，因为 x 通常不是时间：每个点同时携带两个数值，读者看的是"
        "「点云往哪边倒」。点越靠右上，说明两个变量越同步增长；少数离群点会被"
        "一眼挑出来。分组时不同颜色的点叠在同一坐标系里，比较的是分布范围而不是"
        "逐点数值，所以多组时必须有图例；组件本身不画，由调用方补一行。"
    ),
    anatomy=[
        (
            "散点",
            "半径由 radius 统一控制，默认 6px；点太大会互相粘连，太小在深色底上会糊。",
        ),
        (
            "分组配色",
            "每组一个颜色，按内置色板分配；多组时同一坐标系里叠放，组间不设偏移。",
        ),
        (
            "坐标轴",
            "两轴默认按数值取刻度；x 传分类值时退化成等距下标，并显示原始文本。",
        ),
        ("网格", "默认横纵都画，帮助读坐标；点云很密时可以关掉，减少背景噪声。"),
        ("悬停提示", "显示坐标；多组时前面带组名，否则看不出这个点属于哪一组。"),
    ],
    when=[
        "判断两个数值变量是否相关（花费与转化率、气温与能耗）",
        "在大量样本里找离群点或分群迹象",
        "同一坐标系里比较两三组样本的分布范围与重叠程度",
    ],
    avoid=[
        "按时间排列的观测：点的先后顺序读不出来，改用 LineChart",
        "类目少、需要精确读值：用柱状图或表格，散点只能靠坐标轴估",
        "要看点的密度分布：本组件不做透明叠加或热力，改用分箱直方图",
    ],
    examples=[
        Example(
            "单组散点",
            _single,
            hint="15 个投放样本：花费越高转化率越高，点云呈右上走向。",
            code=_BASIC_CODE,
        ),
        Example(
            "多组与气泡",
            _bubbles,
            hint="新客 / 老客两组、radius=10 放大成气泡；图例由调用方摆在图表上方。",
        ),
        Example(
            "负值区间",
            _quadrant,
            hint="x、y 都有负值：原点落在图中间，四个象限的关系一眼可见。",
        ),
    ],
    api=[
        Api("data", "DataInput | None", "None", "数据源，格式与 BarChart 相同"),
        Api("x", "str | None", "None", "x 轴列名；留空取第一列"),
        Api("y", "str | list[str] | None", "None", "y 轴列名，传列表画多组散点"),
        Api("color", "str | list[str] | None", "None", "点的颜色，按组分配"),
        Api("radius", "float", "6", "点的半径，所有点共用一个值"),
        Api("show_grid", "bool", "True", "横纵网格线"),
        Api("tooltip", "bool", "True", "悬停提示；多组时带组名"),
        Api("show_x_labels", "bool", "True", "底部刻度标签"),
        Api("height", "float", "400", "图表高度"),
    ],
    notes=[
        tip(
            "底轴改用与折线图相同的标签生成器：分类 x（如「A 班」「B 班」）会显示原文，"
            "此前一律退化成 0、1、2 的数字刻度。"
        ),
        info(
            "radius 是全局的 —— 不能用点的大小编码第三个变量。真要做气泡图，"
            "直接用 ftc.ScatterChart 组装 ScatterChartSpot 列表。"
        ),
        warn(
            "点重叠时没有透明度叠加，密集区域会糊成一块实色。样本多时把 radius 调小，"
            "或先按区间聚合再画。"
        ),
    ],
    tags=("散点图", "scatter", "相关", "分布"),
)


if __name__ == "__main__":
    run(SPEC)
