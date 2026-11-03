"""站内搜索。"""

from __future__ import annotations

import flet as ft

from docs.kit import (
    BORDER,
    MUTED,
    cell,
    component_chip,
    demo_grid,
    doc_page,
    section,
)
from docs.site import ALL_PAGES, CATEGORY_ROUTES, COMPONENTS
from ui import use_t


@ft.component
def search_page() -> ft.Control:
    tr = use_t()
    page = ft.context.page
    query, set_query = ft.use_state("")
    needle = query.strip().lower()

    page_hits = [
        meta
        for meta in ALL_PAGES
        if needle
        and (
            needle in tr(meta.title_key).lower()
            or needle in tr(meta.desc_key).lower()
            or needle in meta.route.lower()
            or needle in meta.key.lower()
        )
    ]
    component_hits = [
        item
        for item in COMPONENTS
        if needle
        and (
            needle in item.name.lower()
            or needle in tr(f"nav.{item.category}.title").lower()
        )
    ]

    def open_page(route: str) -> None:
        page.navigate(route)

    def result_row(
        title: str,
        description: str,
        route: str,
        icon: ft.IconData,
    ) -> ft.Control:
        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=14, vertical=12),
            border_radius=10,
            bgcolor=ft.Colors.SURFACE,
            border=ft.Border.all(1, BORDER),
            on_click=lambda _: open_page(route),
            ink=True,
            content=ft.Row(
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(icon, size=18, color=ft.Colors.PRIMARY),
                    ft.Column(
                        spacing=2,
                        expand=True,
                        controls=[
                            ft.Text(title, size=14, weight=ft.FontWeight.W_600),
                            ft.Text(
                                description,
                                size=12,
                                color=MUTED,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                        ],
                    ),
                    ft.Icon(ft.Icons.CHEVRON_RIGHT, size=18, color=MUTED),
                ],
            ),
        )

    field = ft.TextField(
        key="docs-search",
        value=query,
        autofocus=True,
        hint_text=tr("site.search.placeholder"),
        prefix_icon=ft.Icons.SEARCH,
        border=ft.InputBorder.NONE,
        filled=True,
        fill_color=ft.Colors.SURFACE_CONTAINER_LOW,
        border_radius=12,
        content_padding=ft.Padding.symmetric(horizontal=14, vertical=14),
        on_change=lambda event: set_query(event.control.value),
    )

    body: list[ft.Control] = [
        ft.Container(
            padding=ft.Padding.symmetric(horizontal=2),
            content=field,
        )
    ]

    if not needle:
        body.append(
            ft.Column(
                spacing=14,
                controls=[
                    ft.Text(
                        tr("site.search.empty_title"),
                        size=18,
                        weight=ft.FontWeight.W_700,
                    ),
                    ft.Text(
                        tr("site.search.empty_hint"),
                        size=13,
                        color=MUTED,
                    ),
                    demo_grid(
                        *[
                            cell(
                                result_row(
                                    tr(meta.title_key),
                                    tr(meta.desc_key),
                                    meta.route,
                                    meta.icon,
                                ),
                                span=6,
                            )
                            for meta in ALL_PAGES
                            if meta.key not in ("home", "search")
                        ]
                    ),
                ],
            )
        )
    elif not page_hits and not component_hits:
        body.append(
            ft.Column(
                spacing=10,
                controls=[
                    ft.Text(
                        tr("site.search.no_results_title", query=query),
                        size=18,
                        weight=ft.FontWeight.W_700,
                    ),
                    ft.Text(
                        tr("site.search.no_results_hint"),
                        size=13,
                        color=MUTED,
                    ),
                ],
            )
        )
    else:
        if page_hits:
            body.append(
                section(
                    tr("site.search.pages"),
                    tr("site.search.result_count", count=len(page_hits)),
                    ft.Column(
                        spacing=8,
                        controls=[
                            result_row(
                                tr(meta.title_key),
                                tr(meta.desc_key),
                                meta.route,
                                meta.icon,
                            )
                            for meta in page_hits
                        ],
                    ),
                )
            )
        if component_hits:
            categories = []
            seen: set[str] = set()
            for item in component_hits:
                if item.category in seen:
                    continue
                seen.add(item.category)
                names = [
                    entry.name
                    for entry in component_hits
                    if entry.category == item.category
                ]
                categories.append(
                    section(
                        tr(f"nav.{item.category}.title"),
                        tr(f"nav.{item.category}.desc"),
                        ft.Row(
                            spacing=8,
                            run_spacing=8,
                            wrap=True,
                            controls=[
                                component_chip(
                                    name,
                                    CATEGORY_ROUTES[item.category],
                                )
                                for name in names
                            ],
                        ),
                    )
                )
            body.append(
                section(
                    tr("site.search.components"),
                    tr("site.search.result_count", count=len(component_hits)),
                    *categories,
                )
            )

    return doc_page("search", body)
