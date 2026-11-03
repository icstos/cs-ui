"""导航组件演示。"""

from __future__ import annotations

import flet as ft

from docs.demos._helpers import ACCENT, BORDER, panel, use_stable
from docs.kit import cell, demo_card, demo_grid, doc_page
from ui import (
    BreadCrumb,
    Button,
    Column,
    Crumb,
    Paging,
    PagingState,
    Tab,
    TabBar,
    TabBarView,
    Tabs,
    use_t,
)


@ft.component
def navigation_page() -> ft.Control:
    tr = use_t()
    page = ft.context.page

    breadcrumb = demo_card(
        title=tr("navigation.breadcrumb.title"),
        hint=tr("navigation.breadcrumb.hint"),
        icon=ft.Icons.CHEVRON_RIGHT,
        stretch=True,
        body=[
            BreadCrumb(
                items=[
                    Crumb(tr("navigation.breadcrumb.home"), route="/"),
                    Crumb(
                        tr("navigation.breadcrumb.nav"),
                        route="/components/navigation",
                    ),
                    Crumb(tr("navigation.breadcrumb.current")),
                ],
            ),
            BreadCrumb(
                items=[
                    tr("navigation.breadcrumb.str"),
                    (tr("navigation.breadcrumb.route"), "/components/general"),
                    tr("navigation.breadcrumb.cur"),
                ],
                active_color=ACCENT,
            ),
        ],
    )

    tabs = demo_card(
        title=tr("navigation.tabs.title"),
        hint=tr("navigation.tabs.hint"),
        icon=ft.Icons.TAB,
        stretch=True,
        body=[
            ft.Container(
                height=220,
                border_radius=10,
                bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
                border=ft.Border.all(1, BORDER),
                content=Tabs(
                    length=3,
                    content=Column(
                        controls=[
                            TabBar(
                                tabs=[
                                    Tab(
                                        text=tr("navigation.tabs.overview"),
                                        icon=ft.Icons.DASHBOARD,
                                    ),
                                    Tab(
                                        text=tr("navigation.tabs.detail"),
                                        icon=ft.Icons.LIST_ALT,
                                    ),
                                    Tab(
                                        text=tr("navigation.tabs.settings"),
                                        icon=ft.Icons.SETTINGS,
                                    ),
                                ]
                            ),
                            TabBarView(
                                expand=True,
                                height=150,
                                controls=[
                                    ft.Container(
                                        padding=16,
                                        content=ft.Text(
                                            tr("navigation.tabs.overview_body"),
                                            size=14,
                                        ),
                                    ),
                                    ft.Container(
                                        padding=16,
                                        content=ft.Text(
                                            tr("navigation.tabs.detail_body"),
                                            size=14,
                                        ),
                                    ),
                                    ft.Container(
                                        padding=16,
                                        content=ft.Text(
                                            tr("navigation.tabs.settings_body"),
                                            size=14,
                                        ),
                                    ),
                                ],
                            ),
                        ]
                    ),
                ),
            )
        ],
    )

    bars = demo_card(
        title=tr("navigation.navbar.title"),
        hint=tr("navigation.navbar.hint"),
        icon=ft.Icons.NAVIGATION_OUTLINED,
        stretch=True,
        body=[
            ft.Row(
                spacing=16,
                wrap=True,
                run_spacing=16,
                controls=[
                    ft.Container(
                        width=360,
                        bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
                        border_radius=10,
                        border=ft.Border.all(1, BORDER),
                        content=ft.NavigationBar(
                            selected_index=1,
                            destinations=[
                                ft.NavigationBarDestination(
                                    icon=ft.Icons.HOME_OUTLINED,
                                    label=tr("navigation.navbar.home"),
                                ),
                                ft.NavigationBarDestination(
                                    icon=ft.Icons.SEARCH,
                                    label=tr("navigation.navbar.search"),
                                ),
                                ft.NavigationBarDestination(
                                    icon=ft.Icons.PERSON_OUTLINE,
                                    label=tr("navigation.navbar.mine"),
                                ),
                            ],
                        ),
                    ),
                    ft.Container(
                        width=140,
                        height=200,
                        bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
                        border_radius=10,
                        border=ft.Border.all(1, BORDER),
                        content=ft.NavigationRail(
                            selected_index=0,
                            label_type=ft.NavigationRailLabelType.ALL,
                            destinations=[
                                ft.NavigationRailDestination(
                                    icon=ft.Icons.DASHBOARD_OUTLINED,
                                    label=tr("navigation.navbar.board"),
                                ),
                                ft.NavigationRailDestination(
                                    icon=ft.Icons.ARTICLE_OUTLINED,
                                    label=tr("navigation.navbar.article"),
                                ),
                                ft.NavigationRailDestination(
                                    icon=ft.Icons.SETTINGS_OUTLINED,
                                    label=tr("navigation.navbar.settings"),
                                ),
                            ],
                        ),
                    ),
                ],
            )
        ],
    )

    paging_state = use_stable(
        lambda: PagingState(
            sum_data_nums=137,
            data_per_page_nums=10,
            on_change_page=lambda page_number: print(
                f"[Paging] page={page_number}"
            ),
        )
    )

    paging = demo_card(
        title=tr("navigation.paging.title"),
        hint=tr("navigation.paging.hint"),
        icon=ft.Icons.PAGES_OUTLINED,
        stretch=True,
        body=[panel(Paging(paging_state))],
    )

    jump = demo_card(
        title=tr("navigation.jump.title"),
        hint=tr("navigation.jump.hint"),
        icon=ft.Icons.OPEN_IN_NEW,
        body=[
            Button(
                tr("navigation.jump.to_about"),
                is_primary=True,
                on_click=lambda _: page.navigate("/about"),
            )
        ],
    )

    return doc_page(
        "navigation",
        [
            demo_grid(
                cell(breadcrumb, span=6),
                cell(tabs, span=6),
                cell(bars, span=12),
                cell(paging, span=6),
                cell(jump, span=6),
            )
        ],
    )
