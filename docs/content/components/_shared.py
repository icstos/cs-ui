"""组件演示共用的小道具：面板、色块、示例数据。"""

from __future__ import annotations

from collections.abc import Sequence

import flet as ft

from docs import kit
from ui import Table, use_t

_BORDER = kit.BORDER
_MUTED = kit.MUTED


def panel(
    *controls: ft.Control,
    padding: int = 12,
    height: int | None = None,
) -> ft.Control:
    """描边面板：给表格、列表这类需要视觉边界的控件一个"窗口"。"""
    return ft.Container(
        bgcolor=ft.Colors.SURFACE,
        border=ft.Border.all(1, _BORDER),
        border_radius=10,
        padding=padding,
        height=height,
        content=ft.Column(spacing=10, controls=list(controls)),
    )


def swatch(color: ft.ColorValue, width: int = 54, height: int = 32) -> ft.Control:
    return ft.Container(
        bgcolor=color,
        width=width,
        height=height,
        border_radius=6,
    )


def caption(text: str) -> ft.Control:
    return ft.Text(text, size=11, color=_MUTED)


def row_of(items: Sequence[ft.Control], *, spacing: int = 10) -> ft.Control:
    return ft.Row(spacing=spacing, wrap=True, run_spacing=spacing, controls=list(items))


def contact_table(rows: int = 24) -> ft.Control:
    """分页表格：用户名是固定格式，所以只有表头跟语言走。"""
    tr = use_t()
    data = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text(tr("demo.col.name"))),
            ft.DataColumn(ft.Text(tr("demo.col.email"))),
            ft.DataColumn(ft.Text(tr("demo.col.age")), numeric=True),
            ft.DataColumn(ft.Text(tr("demo.col.status"))),
        ],
        rows=[
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(f"user{index + 1:02d}")),
                    ft.DataCell(ft.Text(f"user{index + 1:02d}@example.com")),
                    ft.DataCell(ft.Text(str(22 + (index * 7) % 39))),
                    ft.DataCell(
                        ft.Text(
                            tr("demo.col.active")
                            if index % 4
                            else tr("demo.col.paused"),
                            color=ft.Colors.TERTIARY if index % 4 else _MUTED,
                        )
                    ),
                ]
            )
            for index in range(rows)
        ],
    )
    return Table(data_table=data, rows_per_page=8)


def chart_data() -> tuple[str, dict[str, list]]:
    """图表演示数据：列名即图例，所以跟着语言走。"""
    tr = use_t()
    month = tr("demo.chart.month")
    return month, {
        month: tr.list("demo.chart.months"),
        tr("demo.chart.online"): [120, 152, 141, 179, 210, 245, 268, 302],
        tr("demo.chart.offline"): [86, 92, 105, 118, 124, 121, 138, 149],
    }


__all__ = [
    "caption",
    "chart_data",
    "contact_table",
    "panel",
    "row_of",
    "swatch",
]
