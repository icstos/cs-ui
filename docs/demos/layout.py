"""布局与容器组件演示。"""

from __future__ import annotations

import flet as ft

from docs.demos._helpers import BORDER, MUTED, build_data_table, swatch
from docs.kit import cell, demo_card, demo_grid, doc_page, stat_card
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
    Table,
    Timeline,
    TimelineItem,
    use_t,
)


@ft.component
def layout_page() -> ft.Control:
    tr = use_t()

    flex = demo_card(
        title=tr("layout.flex.title"),
        hint=tr("layout.flex.hint"),
        icon=ft.Icons.VIEW_COLUMN_OUTLINED,
        body=[
            ft.Row(
                wrap=True,
                spacing=8,
                run_spacing=8,
                controls=[
                    swatch(ft.Colors.ERROR),
                    swatch(ft.Colors.TERTIARY),
                    swatch(ft.Colors.PRIMARY),
                    swatch(ft.Colors.SECONDARY),
                    ft.VerticalDivider(width=16, thickness=1, color=BORDER),
                    Column(
                        spacing=8,
                        controls=[
                            swatch(ft.Colors.ERROR, 140, 28),
                            swatch(ft.Colors.TERTIARY, 140, 28),
                            swatch(ft.Colors.PRIMARY, 140, 28),
                        ],
                    ),
                    Container(
                        bgcolor=ft.Colors.PRIMARY_CONTAINER,
                        padding=14,
                        border_radius=8,
                        content=ft.Text(
                            tr("layout.flex.container"),
                            size=13,
                            color=ft.Colors.ON_PRIMARY_CONTAINER,
                        ),
                    ),
                    Stack(
                        controls=[
                            Container(
                                width=72,
                                height=72,
                                border_radius=36,
                                bgcolor=ft.Colors.SECONDARY_CONTAINER,
                                alignment=ft.Alignment.CENTER,
                                content=ft.Icon(
                                    ft.Icons.PERSON,
                                    size=36,
                                    color=ft.Colors.PRIMARY,
                                ),
                            ),
                            Container(
                                bgcolor=ft.Colors.ERROR,
                                border_radius=10,
                                padding=ft.Padding.symmetric(
                                    vertical=1, horizontal=6
                                ),
                                right=0,
                                bottom=4,
                                content=ft.Text(
                                    "3", size=10, color=ft.Colors.ON_ERROR
                                ),
                            ),
                        ],
                    ),
                ],
            )
        ],
    )

    lists = demo_card(
        title=tr("layout.list.title"),
        hint=tr("layout.list.hint"),
        icon=ft.Icons.VIEW_LIST_OUTLINED,
        stretch=True,
        body=[
            ft.Row(
                spacing=12,
                controls=[
                    Container(
                        height=190,
                        width=260,
                        border_radius=8,
                        bgcolor=ft.Colors.SURFACE,
                        border=ft.Border.all(1, BORDER),
                        content=ListView(
                            expand=True,
                            divider_thickness=0.5,
                            controls=[
                                Container(
                                    padding=ft.Padding.symmetric(
                                        vertical=9, horizontal=12
                                    ),
                                    content=ft.Text(
                                        tr("layout.list.item", n=index + 1),
                                        size=13,
                                    ),
                                )
                                for index in range(20)
                            ],
                        ),
                    ),
                    Container(
                        height=190,
                        expand=True,
                        border_radius=8,
                        bgcolor=ft.Colors.SURFACE,
                        border=ft.Border.all(1, BORDER),
                        padding=8,
                        content=GridView(
                            expand=True,
                            runs_count=5,
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
                                        size=13,
                                        color=ft.Colors.ON_PRIMARY_CONTAINER,
                                    ),
                                )
                                for index in range(15)
                            ],
                        ),
                    ),
                ],
            )
        ],
    )

    expanders = demo_card(
        title=tr("layout.expander.title"),
        hint=tr("layout.expander.hint"),
        icon=ft.Icons.EXPAND_MORE,
        stretch=True,
        body=[
            Expander(
                title=tr("layout.expander.basic"),
                subtitle=tr("layout.expander.basic_sub"),
                controls=[
                    ft.Text(tr("layout.expander.basic_body1"), size=13),
                    Divider(color=BORDER),
                    ft.Text(
                        tr("layout.expander.basic_body2"),
                        size=12,
                        color=MUTED,
                    ),
                ],
            ),
            Expander(
                variant="filled",
                title=tr("layout.expander.filled"),
                subtitle=tr("layout.expander.filled_sub"),
                leading=ft.Icons.FOLDER_OPEN,
                accent="warning",
                controls=[ft.Text(tr("layout.expander.filled_body"), size=13)],
            ),
            Expander(
                variant="plain",
                density="compact",
                title=tr("layout.expander.plain"),
                trailing=ft.Text("3", size=12, color=MUTED),
                controls=[
                    ft.Text(
                        tr("layout.expander.plain_body"),
                        size=12,
                        color=MUTED,
                    )
                ],
            ),
        ],
    )

    timeline = demo_card(
        title=tr("layout.timeline.title"),
        hint=tr("layout.timeline.hint"),
        icon=ft.Icons.TIMELINE,
        stretch=True,
        body=[
            Timeline(
                items=[
                    TimelineItem(
                        tr("layout.timeline.t1"),
                        "09:12",
                        tr("layout.timeline.d1"),
                        done=True,
                    ),
                    TimelineItem(
                        tr("layout.timeline.t2"),
                        "10:30",
                        tr("layout.timeline.d2"),
                        type="warning",
                    ),
                    TimelineItem(
                        tr("layout.timeline.t3"),
                        "14:05",
                        tr("layout.timeline.d3"),
                        type="info",
                    ),
                    TimelineItem(
                        tr("layout.timeline.t4"),
                        "—",
                        tr("layout.timeline.d4"),
                    ),
                ],
                pending=tr("layout.timeline.pending"),
            ),
            Timeline(
                mode="alternate",
                line_fade=True,
                density="compact",
                time_position="hidden",
                items=[
                    TimelineItem("", "", tr("layout.timeline.alt1"), type="info"),
                    TimelineItem("", "", tr("layout.timeline.alt2"), done=True),
                    TimelineItem("", "", tr("layout.timeline.alt3"), done=True),
                ],
            ),
        ],
    )

    table = demo_card(
        title=tr("layout.table.title"),
        hint=tr("layout.table.hint"),
        icon=ft.Icons.TABLE_CHART,
        stretch=True,
        body=[Table(data_table=build_data_table(tr), rows_per_page=8)],
    )

    page_layout = demo_card(
        title=tr("layout.page.title"),
        hint=tr("layout.page.hint"),
        icon=ft.Icons.SPACE_DASHBOARD,
        stretch=True,
        body=[
            Container(
                height=280,
                border=ft.Border.all(1, BORDER),
                border_radius=10,
                content=PageLayout(
                    title=tr("layout.page.user_title"),
                    subtitle=tr("layout.page.user_subtitle"),
                    padding=16,
                    actions=[
                        Button(tr("layout.page.export")),
                        Button(tr("layout.page.create"), icon=ft.Icons.ADD),
                    ],
                    controls=[
                        Row(
                            spacing=10,
                            wrap=True,
                            controls=[
                                Container(
                                    width=112,
                                    content=stat_card(
                                        value="1,286",
                                        label=tr("layout.page.stat_total"),
                                        icon=ft.Icons.PEOPLE_OUTLINE,
                                    ),
                                ),
                                Container(
                                    width=112,
                                    content=stat_card(
                                        value="942",
                                        label=tr("layout.page.stat_active"),
                                        icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
                                    ),
                                ),
                                Container(
                                    width=112,
                                    content=stat_card(
                                        value="37",
                                        label=tr("layout.page.stat_pending"),
                                        icon=ft.Icons.SCHEDULE,
                                    ),
                                ),
                            ],
                        ),
                        ft.Text(tr("layout.page.content"), size=12, color=MUTED),
                    ],
                ),
            )
        ],
    )

    return doc_page(
        "layout",
        [
            demo_grid(
                cell(flex, span=6),
                cell(expanders, span=6),
                cell(lists, span=12),
                cell(timeline, span=12),
                cell(table, span=12),
                cell(page_layout, span=12),
            )
        ],
    )
