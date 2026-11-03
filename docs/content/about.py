"""关于：版本、设计原则与相关链接。"""

from __future__ import annotations

import flet as ft

from docs import kit
from docs.blocks import Custom, Doc, h2, p, ul
from docs.site import (
    COMPONENT_TOTAL,
    FLET_URL,
    FLET_VERSION,
    GITHUB_URL,
    LICENSE_NAME,
    PACKAGE_VERSION,
    PYTHON_VERSION,
)
from ui import use_t


@ft.component
def _runtime() -> ft.Control:
    tr = use_t()
    rows: tuple[tuple[str, str], ...] = (
        ("about.row.version", f"v{PACKAGE_VERSION}"),
        ("about.row.flet", FLET_VERSION),
        ("about.row.python", PYTHON_VERSION),
        ("about.row.license", LICENSE_NAME),
        ("about.row.components", str(COMPONENT_TOTAL)),
    )
    return ft.Container(
        border_radius=kit.RADIUS_CARD,
        bgcolor=kit.SURFACE,
        border=ft.Border.all(1, kit.BORDER),
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        content=ft.Column(
            spacing=0,
            controls=[
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=18, vertical=11),
                    border=ft.Border(bottom=ft.BorderSide(1, kit.BORDER)),
                    content=ft.Row(
                        spacing=10,
                        controls=[
                            ft.Text(key, size=12.5, color=kit.MUTED, expand=True),
                            ft.Text(
                                value,
                                size=12.5,
                                weight=ft.FontWeight.W_600,
                                selectable=True,
                            ),
                        ],
                    ),
                )
                for key, value in ((tr(k), v) for k, v in rows)
            ],
        ),
    )


@ft.component
def _links() -> ft.Control:
    tr = use_t()
    page = ft.context.page
    entries: tuple[tuple[str, str, ft.IconData], ...] = (
        ("about.link.github", GITHUB_URL, ft.Icons.CODE),
        ("about.link.flet", FLET_URL, ft.Icons.OPEN_IN_NEW),
        ("about.link.license", f"{GITHUB_URL}/blob/main/LICENSE", ft.Icons.GAVEL),
    )
    return ft.Column(
        spacing=10,
        controls=[
            kit.hover_card(
                on_click=lambda _e, url=url: page.launch_url(url),
                padding=14,
                content=ft.Row(
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        kit.icon_tile(icon, tone="primary", size=32, icon_size=16),
                        ft.Column(
                            spacing=1,
                            expand=True,
                            controls=[
                                ft.Text(tr(key), size=13, weight=ft.FontWeight.W_600),
                                ft.Text(url, size=11, color=kit.MUTED),
                            ],
                        ),
                        ft.Icon(ft.Icons.ARROW_OUTWARD, size=15, color=kit.MUTED),
                    ],
                ),
            )
            for key, url, icon in entries
        ],
    )


ABOUT: Doc = (
    p("about.intro"),
    h2("about.runtime.title"),
    Custom(_runtime),
    h2("about.principles.title"),
    p("about.principles.desc"),
    ul(
        "about.principle1",
        "about.principle2",
        "about.principle3",
        "about.principle4",
    ),
    h2("about.links.title"),
    Custom(_links),
)
