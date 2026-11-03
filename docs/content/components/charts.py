"""图表：折线、面积、柱状、散点。"""

from __future__ import annotations

import math

import flet as ft

from docs.blocks import Doc, demo, h2, note, p
from docs.content.components._shared import chart_data
from ui import PRIMARY_SEEDS, AreaChart, BarChart, LineChart, ScatterChart, use_t

_CHART_CODE = '''LineChart(
    data={
        "Month": ["Jan", "Feb", "Mar", "Apr"],
        "Online": [120, 152, 141, 179],
        "Offline": [86, 92, 105, 118],
    },
    x="Month",
    y=["Online", "Offline"],
    height=280,
    show_points=True,
)'''


@ft.component
def _lines() -> ft.Control:
    tr = use_t()
    month, data = chart_data()
    return ft.Column(
        spacing=16,
        controls=[
            LineChart(
                data=data,
                x=month,
                y=[tr("demo.chart.online"), tr("demo.chart.offline")],
                height=260,
                show_points=True,
            ),
            AreaChart(
                data=data,
                x=month,
                y=[tr("demo.chart.online")],
                height=240,
                color=PRIMARY_SEEDS["green"],
            ),
        ],
    )


@ft.component
def _bars() -> ft.Control:
    tr = use_t()
    month, data = chart_data()
    return ft.Column(
        spacing=16,
        controls=[
            BarChart(
                data=data,
                x=month,
                y=[tr("demo.chart.online"), tr("demo.chart.offline")],
                height=250,
            ),
            BarChart(
                data=data,
                x=month,
                y=[tr("demo.chart.online"), tr("demo.chart.offline")],
                stacked=True,
                height=250,
            ),
        ],
    )


@ft.component
def _scatter() -> ft.Control:
    points = [
        (round(math.cos(index * 0.4) * 10 + 20, 2), round(math.sin(index * 0.7) * 8 + 15, 2))
        for index in range(40)
    ]
    return ScatterChart(data=points, height=260, color=PRIMARY_SEEDS["violet"])


CHARTS: Doc = (
    p("cat.charts.intro"),
    h2("cat.charts.line.title"),
    demo(_lines, hint_key="cat.charts.line.hint", code=_CHART_CODE),
    h2("cat.charts.bar.title"),
    demo(_bars, hint_key="cat.charts.bar.hint"),
    h2("cat.charts.scatter.title"),
    demo(_scatter, hint_key="cat.charts.scatter.hint"),
    note("cat.charts.tip", "cat.charts.tip_title"),
)
