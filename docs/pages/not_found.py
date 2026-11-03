"""404 页面。"""

from __future__ import annotations

import flet as ft

from docs.kit import PAGE_BG, top_bar
from ui import Button, use_t


@ft.component
def not_found_page() -> ft.Control:
    tr = use_t()
    page = ft.context.page

    return ft.Container(
        expand=True,
        bgcolor=PAGE_BG,
        content=ft.Column(
            expand=True,
            spacing=0,
            controls=[
                top_bar(),
                ft.Container(
                    expand=True,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=14,
                        controls=[
                            ft.Text(
                                "404",
                                size=88,
                                weight=ft.FontWeight.W_800,
                                color=ft.Colors.OUTLINE_VARIANT,
                            ),
                            ft.Text(
                                tr("notfound.title"),
                                size=20,
                                weight=ft.FontWeight.W_700,
                            ),
                            ft.Text(
                                tr("notfound.body"),
                                size=13,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                            ft.Row(
                                spacing=10,
                                controls=[
                                    Button(
                                        tr("notfound.back"),
                                        is_primary=True,
                                        icon=ft.Icons.HOME,
                                        on_click=lambda _: page.navigate("/"),
                                    ),
                                    Button(
                                        tr("site.notfound.search"),
                                        icon=ft.Icons.SEARCH,
                                        on_click=lambda _: page.navigate("/search"),
                                    ),
                                ],
                            ),
                        ],
                    ),
                ),
            ],
        ),
    )
