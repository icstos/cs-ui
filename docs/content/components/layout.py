"""布局组件：容器、列表、折叠面板、时间线、表格与页面骨架。"""

from __future__ import annotations

import flet as ft

from docs import kit
from docs.blocks import Doc, demo, h2, note, p, ul
from docs.content.components._shared import contact_table, panel, swatch
from ui import (
    Button,
    Column,
    Container,
    Divider,
    Expander,
    GridView,
    ListView,
    PageLayout,
    Row,
    Stack,
    Timeline,
    TimelineItem,
    use_t,
)

_TABLE_CODE = '''Table(data_table=ft.DataTable(columns=[...], rows=[...]), rows_per_page=8)'''

_TIMELINE_CODE = '''Timeline(
    items=[
        TimelineItem("Deploy", "09:12", "Build finished", done=True),
        TimelineItem("Review", "10:30", "Waiting for approval", type="warning"),
        TimelineItem("Release", "14:05", "Scheduled"),
    ],
    pending="In progress",
)'''


@ft.component
def _flex() -> ft.Control:
    tr = use_t()
    return Row(
        wrap=True,
        spacing=10,
        run_spacing=10,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            swatch(ft.Colors.ERROR),
            swatch(ft.Colors.TERTIARY),
            swatch(ft.Colors.PRIMARY),
            swatch(ft.Colors.SECONDARY),
            ft.VerticalDivider(width=14, thickness=1, color=kit.BORDER),
            Column(
                spacing=6,
                controls=[
                    swatch(ft.Colors.ERROR, 120, 24),
                    swatch(ft.Colors.PRIMARY, 120, 24),
                ],
            ),
            Container(
                bgcolor=ft.Colors.PRIMARY_CONTAINER,
                padding=ft.Padding.symmetric(horizontal=14, vertical=10),
                border_radius=9,
                content=ft.Text(
                    tr("cat.layout.flex.container"),
                    size=12.5,
                    color=ft.Colors.ON_PRIMARY_CONTAINER,
                ),
            ),
            Stack(
                controls=[
                    Container(
                        width=64,
                        height=64,
                        border_radius=32,
                        bgcolor=ft.Colors.SECONDARY_CONTAINER,
                        alignment=ft.Alignment.CENTER,
                        content=ft.Icon(ft.Icons.PERSON, size=30, color=ft.Colors.PRIMARY),
                    ),
                    Container(
                        bgcolor=ft.Colors.ERROR,
                        border_radius=999,
                        padding=ft.Padding.symmetric(vertical=1, horizontal=7),
                        right=0,
                        bottom=2,
                        content=ft.Text("3", size=10, color=ft.Colors.ON_ERROR),
                    ),
                ],
            ),
        ],
    )


@ft.component
def _lists() -> ft.Control:
    tr = use_t()
    return Row(
        spacing=12,
        controls=[
            Container(
                height=196,
                width=250,
                border_radius=9,
                bgcolor=ft.Colors.SURFACE,
                border=ft.Border.all(1, kit.BORDER),
                content=ListView(
                    expand=True,
                    divider_thickness=0.5,
                    controls=[
                        Container(
                            padding=ft.Padding.symmetric(vertical=8, horizontal=12),
                            content=ft.Text(
                                tr("cat.layout.list.item", n=index + 1), size=12.5
                            ),
                        )
                        for index in range(20)
                    ],
                ),
            ),
            Container(
                height=196,
                expand=True,
                border_radius=9,
                bgcolor=ft.Colors.SURFACE,
                border=ft.Border.all(1, kit.BORDER),
                padding=8,
                content=GridView(
                    expand=True,
                    runs_count=6,
                    spacing=8,
                    run_spacing=8,
                    child_aspect_ratio=1.6,
                    controls=[
                        Container(
                            bgcolor=ft.Colors.PRIMARY_CONTAINER,
                            border_radius=6,
                            alignment=ft.Alignment.CENTER,
                            content=ft.Text(
                                str(index + 1),
                                size=12,
                                color=ft.Colors.ON_PRIMARY_CONTAINER,
                            ),
                        )
                        for index in range(18)
                    ],
                ),
            ),
        ],
    )


@ft.component
def _expanders() -> ft.Control:
    tr = use_t()
    return Column(
        spacing=10,
        controls=[
            Expander(
                title=tr("cat.layout.expander.basic"),
                subtitle=tr("cat.layout.expander.basic_sub"),
                controls=[
                    ft.Text(tr("cat.layout.expander.body1"), size=13),
                    Divider(color=kit.BORDER),
                    ft.Text(tr("cat.layout.expander.body2"), size=12, color=kit.MUTED),
                ],
            ),
            Expander(
                variant="filled",
                title=tr("cat.layout.expander.filled"),
                subtitle=tr("cat.layout.expander.filled_sub"),
                leading=ft.Icons.FOLDER_OPEN,
                accent="warning",
                controls=[ft.Text(tr("cat.layout.expander.body1"), size=13)],
            ),
            Expander(
                variant="plain",
                density="compact",
                title=tr("cat.layout.expander.plain"),
                trailing=ft.Text("3", size=12, color=kit.MUTED),
                controls=[
                    ft.Text(tr("cat.layout.expander.body2"), size=12, color=kit.MUTED)
                ],
            ),
        ],
    )


@ft.component
def _timeline() -> ft.Control:
    tr = use_t()
    return Column(
        spacing=18,
        controls=[
            Timeline(
                items=[
                    TimelineItem(
                        tr("cat.layout.timeline.t1"), "09:12",
                        tr("cat.layout.timeline.d1"), done=True,
                    ),
                    TimelineItem(
                        tr("cat.layout.timeline.t2"), "10:30",
                        tr("cat.layout.timeline.d2"), type="warning",
                    ),
                    TimelineItem(
                        tr("cat.layout.timeline.t3"), "14:05",
                        tr("cat.layout.timeline.d3"), type="info",
                    ),
                    TimelineItem(
                        tr("cat.layout.timeline.t4"), "—",
                        tr("cat.layout.timeline.d4"),
                    ),
                ],
                pending=tr("cat.layout.timeline.pending"),
            ),
            Timeline(
                mode="alternate",
                line_fade=True,
                density="compact",
                time_position="hidden",
                items=[
                    TimelineItem("", "", tr("cat.layout.timeline.alt1"), type="info"),
                    TimelineItem("", "", tr("cat.layout.timeline.alt2"), done=True),
                    TimelineItem("", "", tr("cat.layout.timeline.alt3"), done=True),
                ],
            ),
        ],
    )


@ft.component
def _table() -> ft.Control:
    return panel(contact_table())


@ft.component
def _page_layout() -> ft.Control:
    tr = use_t()

    def stat(value: str, label: str, icon: ft.IconData, role: str) -> ft.Control:
        return Container(
            width=128,
            padding=12,
            border_radius=10,
            bgcolor=ft.Colors.SURFACE,
            border=ft.Border.all(1, kit.BORDER),
            content=Column(
                spacing=6,
                controls=[
                    kit.icon_tile(icon, tone=role, size=30, icon_size=15),
                    ft.Text(value, size=19, weight=ft.FontWeight.W_700),
                    ft.Text(label, size=11, color=kit.MUTED),
                ],
            ),
        )

    return Container(
        height=300,
        border=ft.Border.all(1, kit.BORDER),
        border_radius=10,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        content=PageLayout(
            title=tr("cat.layout.page.name"),
            subtitle=tr("cat.layout.page.subtitle"),
            padding=16,
            actions=[
                Button(tr("cat.layout.page.export")),
                Button(tr("cat.layout.page.create"), icon=ft.Icons.ADD),
            ],
            controls=[
                Row(
                    spacing=10,
                    wrap=True,
                    controls=[
                        stat("1,286", tr("cat.layout.page.total"), ft.Icons.PEOPLE_OUTLINE, "primary"),
                        stat("942", tr("cat.layout.page.active"), ft.Icons.CHECK_CIRCLE_OUTLINE, "success"),
                        stat("37", tr("cat.layout.page.pending"), ft.Icons.SCHEDULE, "warning"),
                    ],
                ),
                ft.Text(tr("cat.layout.page.content"), size=12, color=kit.MUTED),
            ],
        ),
    )


LAYOUT: Doc = (
    p("cat.layout.intro"),
    h2("cat.layout.flex.title"),
    demo(_flex, hint_key="cat.layout.flex.hint"),
    h2("cat.layout.list.title"),
    demo(_lists, hint_key="cat.layout.list.hint"),
    h2("cat.layout.expander.title"),
    demo(_expanders, hint_key="cat.layout.expander.hint"),
    h2("cat.layout.timeline.title"),
    demo(_timeline, hint_key="cat.layout.timeline.hint", code=_TIMELINE_CODE),
    h2("cat.layout.table.title"),
    demo(_table, hint_key="cat.layout.table.hint", code=_TABLE_CODE, padded=False),
    h2("cat.layout.page.title"),
    demo(_page_layout, hint_key="cat.layout.page.hint", padded=False),
    ul("cat.layout.note1", "cat.layout.note2", "cat.layout.note3"),
    note("cat.layout.tip", "cat.layout.tip_title"),
)
