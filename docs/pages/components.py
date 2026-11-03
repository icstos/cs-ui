"""组件总览。"""

from __future__ import annotations

from collections import defaultdict

import flet as ft

from docs.kit import (
    category_card,
    cell,
    component_chip,
    demo_card,
    demo_grid,
    doc_page,
    section,
    stat_card,
)
from docs.site import (
    CATEGORY_COUNTS,
    CATEGORY_KEYS,
    CATEGORY_ROUTES,
    COMPONENT_TOTAL,
    COMPONENTS,
    PAGE_BY_KEY,
)
from ui import Button, use_t


@ft.component
def components_page() -> ft.Control:
    tr = use_t()
    page = ft.context.page

    by_category: dict[str, list[str]] = defaultdict(list)
    for item in COMPONENTS:
        by_category[item.category].append(item.name)

    stats = demo_grid(
        cell(
            stat_card(
                value=str(COMPONENT_TOTAL),
                label=tr("site.components.total"),
                icon=ft.Icons.WIDGETS,
            ),
            span=3,
        ),
        cell(
            stat_card(
                value=str(len(CATEGORY_KEYS)),
                label=tr("site.components.categories"),
                icon=ft.Icons.CATEGORY_OUTLINED,
                color=ft.Colors.TERTIARY,
            ),
            span=3,
        ),
        cell(
            stat_card(
                value="3",
                label=tr("site.home.stats.languages"),
                icon=ft.Icons.TRANSLATE,
                color=ft.Colors.SECONDARY,
            ),
            span=3,
        ),
        cell(
            stat_card(
                value="100%",
                label=tr("site.home.stats.typed"),
                icon=ft.Icons.DATA_OBJECT,
                color=ft.Colors.ERROR,
            ),
            span=3,
        ),
    )

    catalog = demo_grid(
        *[
            cell(
                category_card(
                    category=key,
                    route=CATEGORY_ROUTES[key],
                    icon=PAGE_BY_KEY[key].icon,
                    title=tr(f"nav.{key}.title"),
                    description=tr(f"nav.{key}.desc"),
                    count=CATEGORY_COUNTS[key],
                ),
                span=4,
            )
            for key in CATEGORY_KEYS
        ]
    )

    groups = [
        section(
            tr(f"nav.{key}.title"),
            tr(f"nav.{key}.desc"),
            ft.Row(
                spacing=8,
                run_spacing=8,
                wrap=True,
                controls=[
                    component_chip(name, CATEGORY_ROUTES[key])
                    for name in by_category[key]
                ],
            ),
        )
        for key in CATEGORY_KEYS
    ]

    search = demo_card(
        title=tr("site.components.search.title"),
        hint=tr("site.components.search.hint"),
        icon=ft.Icons.SEARCH,
        body=[
            Button(
                tr("site.components.search.button"),
                is_primary=True,
                icon=ft.Icons.MANAGE_SEARCH,
                on_click=lambda _: page.navigate("/search"),
            )
        ],
    )

    return doc_page(
        "components",
        [
            stats,
            catalog,
            *groups,
            search,
        ],
    )
