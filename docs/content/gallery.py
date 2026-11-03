"""组件总览：九张分类卡片 + 规模感。"""

from __future__ import annotations

import flet as ft

from docs import kit, search
from docs.blocks import Custom, Doc, p
from docs.site import (
    CATEGORIES,
    CATEGORY_ROLE,
    COMPONENT_COUNTS,
    COMPONENT_TOTAL,
    PAGES,
    SAMPLE_NAMES,
)
from ui import use_t


def _stat(value: str, label: str) -> ft.Control:
    return ft.Column(
        spacing=2,
        controls=[
            ft.Text(value, size=22, weight=ft.FontWeight.W_700),
            ft.Text(label, size=11.5, color=kit.MUTED),
        ],
    )


@ft.component
def _stats() -> ft.Control:
    tr = use_t()
    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=20, vertical=16),
        border_radius=kit.RADIUS_CARD,
        bgcolor=kit.SURFACE,
        border=ft.Border.all(1, kit.BORDER),
        content=ft.Row(
            spacing=36,
            wrap=True,
            run_spacing=18,
            controls=[
                _stat(str(COMPONENT_TOTAL), tr("comp.stats.components")),
                _stat(str(len(CATEGORIES)), tr("comp.stats.categories")),
                _stat("3", tr("comp.stats.languages")),
                _stat("100%", tr("comp.stats.typed")),
                _stat("3.12+", tr("comp.stats.python")),
            ],
        ),
    )


@ft.component
def _card(slug: str) -> ft.Control:
    tr = use_t()
    page = ft.context.page
    meta = PAGES[slug]
    role = CATEGORY_ROLE[slug]
    return ft.Container(
        col={"xs": 12, "sm": 6, "lg": 4},
        content=kit.hover_card(
            on_click=lambda _e: page.navigate(meta.route),
            padding=18,
            content=ft.Column(
                spacing=10,
                controls=[
                    ft.Row(
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            kit.icon_tile(meta.icon, tone=role),
                            ft.Container(expand=True),
                            ft.Container(
                                padding=ft.Padding.symmetric(
                                    horizontal=7, vertical=1
                                ),
                                border_radius=999,
                                bgcolor=kit.RAISED,
                                content=ft.Text(
                                    str(COMPONENT_COUNTS[slug]),
                                    size=10,
                                    color=kit.MUTED,
                                    weight=ft.FontWeight.W_700,
                                ),
                            ),
                        ],
                    ),
                    ft.Text(tr(meta.title_key), size=15, weight=ft.FontWeight.W_700),
                    ft.Text(
                        tr(meta.desc_key),
                        size=12,
                        color=kit.MUTED,
                        style=ft.TextStyle(height=1.6),
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Text(
                        " · ".join(SAMPLE_NAMES[slug]),
                        size=10.5,
                        color=kit.MUTED,
                        style=ft.TextStyle(letter_spacing=0.1),
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                ],
            ),
        ),
    )


@ft.component
def _grid() -> ft.Control:
    return ft.ResponsiveRow(
        columns=12,
        spacing=14,
        run_spacing=14,
        controls=[_card(slug) for slug in CATEGORIES],
    )


@ft.component
def _search_cta() -> ft.Control:
    tr = use_t()
    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=22, vertical=18),
        border_radius=kit.RADIUS_CARD,
        bgcolor=ft.Colors.PRIMARY_CONTAINER,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            wrap=True,
            run_spacing=14,
            controls=[
                ft.Column(
                    spacing=4,
                    controls=[
                        ft.Text(
                            tr("comp.search.title"),
                            size=15,
                            weight=ft.FontWeight.W_700,
                            color=ft.Colors.ON_PRIMARY_CONTAINER,
                        ),
                        ft.Text(
                            tr("comp.search.desc"),
                            size=12,
                            color=ft.Colors.ON_PRIMARY_CONTAINER,
                        ),
                    ],
                ),
                ft.FilledButton(
                    tr("comp.search.button"),
                    icon=ft.Icons.SEARCH,
                    on_click=lambda _e: search.open_search(),
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.ON_PRIMARY_CONTAINER,
                        color=ft.Colors.PRIMARY_CONTAINER,
                    ),
                ),
            ],
        ),
    )


GALLERY: Doc = (
    p("comp.intro"),
    Custom(_stats),
    Custom(_grid),
    Custom(_search_cta),
)
