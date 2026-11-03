"""演示页共用的数据与小组件。"""

from __future__ import annotations

import flet as ft

from docs.core.assets import LOGO_FILE
from docs.core.state import use_stable
from ui import semantic_text

# 演示区配色一律走 Material 3 角色色，明暗主题自动跟随。
MUTED = ft.Colors.ON_SURFACE_VARIANT
BORDER = ft.Colors.OUTLINE_VARIANT
ACCENT = ft.Colors.PRIMARY

SAMPLE_AUDIO = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
SAMPLE_VIDEO = "https://flutter.github.io/assets-for-api-docs/assets/videos/bee.mp4"
SAMPLE_VIDEO_2 = (
    "https://flutter.github.io/assets-for-api-docs/assets/videos/butterfly.mp4"
)
SAMPLE_PDF = (
    "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
)

__all__ = [
    "ACCENT",
    "BORDER",
    "LOGO_FILE",
    "MUTED",
    "SAMPLE_AUDIO",
    "SAMPLE_PDF",
    "SAMPLE_VIDEO",
    "SAMPLE_VIDEO_2",
    "build_data_table",
    "labeled",
    "panel",
    "swatch",
    "use_stable",
]


def panel(
    *controls: ft.Control,
    padding: int = 12,
    height: int | None = None,
) -> ft.Control:
    """描边面板，用于承载表格、列表等需要视觉边界的控件。"""
    return ft.Container(
        bgcolor=ft.Colors.SURFACE,
        border=ft.Border.all(1, BORDER),
        border_radius=10,
        padding=padding,
        height=height,
        content=ft.Column(spacing=10, controls=list(controls)),
    )


def swatch(
    color: ft.ColorValue,
    width: int = 56,
    height: int = 36,
    radius: int = 6,
) -> ft.Control:
    return ft.Container(
        bgcolor=color,
        width=width,
        height=height,
        border_radius=radius,
        alignment=ft.Alignment.CENTER,
    )


def labeled(label: str, control: ft.Control) -> ft.Control:
    return ft.Column(
        spacing=4,
        controls=[
            ft.Text(label, size=12, color=MUTED),
            control,
        ],
    )


def build_data_table(tr) -> ft.DataTable:
    """演示用表格；数据固定，保证重渲染时不会跳动。"""
    rows = [
        ft.DataRow(
            cells=[
                ft.DataCell(ft.Text(tr("layout.table.user", n=f"{index + 1:02d}"))),
                ft.DataCell(ft.Text(f"user{index + 1:02d}@cstos.com")),
                ft.DataCell(ft.Text(str(20 + (index * 7) % 41))),
                ft.DataCell(
                    ft.Text(
                        tr("layout.table.enabled")
                        if index % 3
                        else tr("layout.table.disabled"),
                        color=(
                            ft.Colors.TERTIARY if index % 3 else ft.Colors.ERROR
                        ),
                    )
                ),
            ]
        )
        for index in range(46)
    ]
    return ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text(tr("layout.table.name"))),
            ft.DataColumn(ft.Text(tr("layout.table.email"))),
            ft.DataColumn(ft.Text(tr("layout.table.age")), numeric=True),
            ft.DataColumn(ft.Text(tr("layout.table.status"))),
        ],
        rows=rows,
    )


def sales(tr) -> dict[str, list]:
    """图表演示数据；列名即图例，所以跟着语言走。"""
    return {
        tr("charts.month"): tr.list("charts.months"),
        tr("charts.online"): [120, 152, 141, 179, 210, 245, 268, 302],
        tr("charts.offline"): [86, 92, 105, 118, 124, 121, 138, 149],
    }


def status_color(kind: str) -> ft.ColorValue:
    return semantic_text(kind)
