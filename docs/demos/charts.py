"""图表演示。"""

from __future__ import annotations

import math

import flet as ft

from docs.demos._helpers import sales
from docs.kit import cell, code_block, demo_card, demo_grid, doc_page
from ui import (
    PRIMARY_SEEDS,
    AreaChart,
    BarChart,
    LineChart,
    ScatterChart,
    use_t,
)

_CHART_SNIPPET = """LineChart(
    data={
        "Month": ["Jan", "Feb", "Mar", "Apr"],
        "Online": [120, 152, 141, 179],
        "Offline": [86, 92, 105, 118],
    },
    x="Month",
    y=["Online", "Offline"],
    height=280,
    show_points=True,
)"""


@ft.component
def charts_page() -> ft.Control:
    tr = use_t()
    month = tr("charts.month")
    series = [tr("charts.online"), tr("charts.offline")]
    data = sales(tr)

    line = demo_card(
        title=tr("charts.line.title"),
        hint=tr("charts.line.hint"),
        icon=ft.Icons.SHOW_CHART,
        stretch=True,
        body=[
            LineChart(
                data=data,
                x=month,
                y=series,
                height=280,
                show_points=True,
            )
        ],
    )

    area = demo_card(
        title=tr("charts.area.title"),
        hint=tr("charts.area.hint"),
        icon=ft.Icons.AREA_CHART,
        stretch=True,
        body=[
            AreaChart(
                data=data,
                x=month,
                y=[tr("charts.online")],
                height=280,
                color=PRIMARY_SEEDS["green"],
            )
        ],
    )

    bars = demo_card(
        title=tr("charts.bar.title"),
        hint=tr("charts.bar.hint"),
        icon=ft.Icons.BAR_CHART,
        stretch=True,
        body=[
            BarChart(data=data, x=month, y=series, height=280),
            BarChart(data=data, x=month, y=series, stacked=True, height=280),
        ],
    )

    scatter = demo_card(
        title=tr("charts.scatter.title"),
        hint=tr("charts.scatter.hint"),
        icon=ft.Icons.SCATTER_PLOT,
        stretch=True,
        body=[
            ScatterChart(
                data=[
                    (
                        round(math.cos(index * 0.4) * 10 + 20, 2),
                        round(math.sin(index * 0.7) * 8 + 15, 2),
                    )
                    for index in range(40)
                ],
                height=280,
                color=PRIMARY_SEEDS["violet"],
            )
        ],
    )

    return doc_page(
        "charts",
        [
            demo_grid(
                cell(line, span=12),
                cell(area, span=12),
                cell(bars, span=12),
                cell(scatter, span=12),
            ),
            code_block(_CHART_SNIPPET, filename="chart.py"),
        ],
    )
