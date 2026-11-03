"""文档站外壳：顶栏、侧边栏、页面骨架与页脚。"""

from __future__ import annotations

from collections.abc import Sequence

import flet as ft

from docs.core.assets import LOGO_FILE
from docs.kit.blocks import BORDER, MUTED, PAGE_BG, eyebrow
from docs.kit.cards import next_card, version_chip
from docs.site import (
    FLET_VERSION,
    GITHUB_URL,
    NAV_GROUPS,
    PACKAGE_VERSION,
    PAGE_BY_KEY,
    PYTHON_VERSION,
    PageMeta,
    page_after,
    page_before,
)
from ui import PRIMARY_SEEDS, LanguageSwitcher, use_t
from ui.core.theme import use_theme

TOPBAR_HEIGHT = 64
SIDEBAR_WIDTH = 256


def _is_active(location: str, route: str) -> bool:
    if route == "/":
        return location in ("", "/")
    return location.rstrip("/") == route.rstrip("/")


@ft.component
def _primary_menu() -> ft.Control:
    theme = use_theme()
    tr = use_t()
    items = [
        ft.PopupMenuItem(
            content=ft.Row(
                spacing=8,
                controls=[
                    ft.Container(
                        width=12,
                        height=12,
                        border_radius=3,
                        bgcolor=seed,
                        border=ft.Border.all(
                            1,
                            ft.Colors.ON_SURFACE
                            if theme.primary.lower() == seed.lower()
                            else ft.Colors.TRANSPARENT,
                        ),
                    ),
                    ft.Text(name.capitalize(), size=12),
                ],
            ),
            on_click=lambda _e, value=seed: theme.set_primary(value),
        )
        for name, seed in PRIMARY_SEEDS.items()
    ]
    return ft.PopupMenuButton(
        icon=ft.Icons.PALETTE,
        icon_color=ft.Colors.ON_SURFACE_VARIANT,
        icon_size=20,
        tooltip=tr("site.theme.primary"),
        items=items,
    )


@ft.component
def _theme_toggle() -> ft.Control:
    theme = use_theme()
    tr = use_t()
    dark = theme.mode_name == "dark"
    return ft.IconButton(
        icon=ft.Icons.LIGHT_MODE if dark else ft.Icons.DARK_MODE,
        icon_color=ft.Colors.ON_SURFACE_VARIANT,
        icon_size=20,
        tooltip=tr("site.theme.toggle"),
        on_click=lambda _: theme.toggle_mode(),
    )


def _search_button(tr) -> ft.Control:
    page = ft.context.page

    def open_search(_: ft.Event[ft.Container]) -> None:
        page.navigate("/search")

    return ft.Container(
        width=236,
        height=36,
        padding=ft.Padding.symmetric(horizontal=10),
        border_radius=9,
        bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
        border=ft.Border.all(1, BORDER),
        on_click=open_search,
        ink=True,
        content=ft.Row(
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(ft.Icons.SEARCH, size=16, color=MUTED),
                ft.Text(
                    tr("site.search.placeholder"),
                    size=12,
                    color=MUTED,
                    expand=True,
                ),
            ],
        ),
    )


def _nav_link(label: str, route: str, *, active: bool) -> ft.Control:
    page = ft.context.page
    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=12, vertical=6),
        border_radius=8,
        bgcolor=ft.Colors.PRIMARY_CONTAINER if active else None,
        on_click=lambda _: page.navigate(route),
        ink=True,
        content=ft.Text(
            label,
            size=13,
            weight=ft.FontWeight.W_600 if active else ft.FontWeight.W_400,
            color=(
                ft.Colors.ON_PRIMARY_CONTAINER
                if active
                else ft.Colors.ON_SURFACE_VARIANT
            ),
        ),
    )


@ft.component
def top_bar() -> ft.Control:
    tr = use_t()
    location = ft.use_route_location()
    page = ft.context.page

    brand = ft.Row(
        spacing=10,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Image(src=str(LOGO_FILE), width=30, height=30, fit=ft.BoxFit.CONTAIN),
            ft.Text("cs-ui", size=18, weight=ft.FontWeight.W_800),
            version_chip(),
        ],
    )

    tabs = ft.Row(
        spacing=2,
        controls=[
            _nav_link(
                tr("site.tab.docs"),
                "/docs/getting-started",
                active=location.startswith("/docs"),
            ),
            _nav_link(
                tr("site.tab.components"),
                "/components",
                active=location.startswith("/components"),
            ),
            _nav_link(
                tr("site.tab.about"),
                "/about",
                active=location.startswith("/about"),
            ),
        ],
    )

    actions = ft.Row(
        spacing=2,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            _search_button(tr),
            ft.Container(width=6),
            LanguageSwitcher(compact=True),
            _primary_menu(),
            _theme_toggle(),
            ft.IconButton(
                icon=ft.Icons.HUB,
                icon_color=ft.Colors.ON_SURFACE_VARIANT,
                icon_size=20,
                tooltip=tr("site.github"),
                action=ft.OpenUrl(GITHUB_URL, target=ft.UrlTarget.BLANK),
            ),
        ],
    )

    return ft.Container(
        height=TOPBAR_HEIGHT,
        bgcolor=ft.Colors.SURFACE,
        padding=ft.Padding.symmetric(horizontal=18),
        border=ft.Border(bottom=ft.BorderSide(1, BORDER)),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(
                    spacing=26,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(
                            on_click=lambda _: page.navigate("/"),
                            ink=True,
                            border_radius=8,
                            padding=ft.Padding.symmetric(horizontal=4, vertical=4),
                            content=brand,
                        ),
                        tabs,
                    ],
                ),
                actions,
            ],
        ),
    )


def _sidebar_item(meta: PageMeta, title: str, *, active: bool) -> ft.Control:
    page = ft.context.page
    foreground = (
        ft.Colors.ON_PRIMARY_CONTAINER if active else ft.Colors.ON_SURFACE_VARIANT
    )
    return ft.Container(
        height=34,
        padding=ft.Padding.symmetric(horizontal=10),
        border_radius=8,
        bgcolor=ft.Colors.PRIMARY_CONTAINER if active else None,
        on_click=lambda _: page.navigate(meta.route),
        ink=True,
        content=ft.Row(
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(meta.icon, size=17, color=foreground),
                ft.Text(
                    title,
                    size=13,
                    color=foreground,
                    weight=ft.FontWeight.W_600 if active else ft.FontWeight.W_400,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
            ],
        ),
    )


@ft.component
def sidebar() -> ft.Control:
    tr = use_t()
    location = ft.use_route_location()

    groups: list[ft.Control] = []
    for group in NAV_GROUPS:
        items = [
            _sidebar_item(item, tr(item.title_key), active=_is_active(location, item.route))
            for item in group.items
        ]
        groups.append(
            ft.Column(
                spacing=2,
                controls=[
                    ft.Container(
                        padding=ft.Padding.only(left=10, top=14, bottom=6),
                        content=ft.Text(
                            tr(group.title_key).upper(),
                            size=10,
                            color=MUTED,
                            weight=ft.FontWeight.W_700,
                            style=ft.TextStyle(letter_spacing=1.1),
                        ),
                    ),
                    *items,
                ],
            )
        )

    footer = ft.Container(
        margin=ft.Margin.only(top=18),
        padding=12,
        border_radius=10,
        bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
        border=ft.Border.all(1, BORDER),
        content=ft.Column(
            spacing=3,
            controls=[
                ft.Row(
                    spacing=6,
                    controls=[
                        ft.Text("cs-ui", size=12, weight=ft.FontWeight.W_700),
                        ft.Text(
                            tr("site.version", version=PACKAGE_VERSION),
                            size=10,
                            color=MUTED,
                        ),
                    ],
                ),
                ft.Text(
                    tr(
                        "site.sidebar.runtime",
                        flet=FLET_VERSION,
                        python=PYTHON_VERSION,
                    ),
                    size=10,
                    color=MUTED,
                ),
            ],
        ),
    )

    return ft.Container(
        width=SIDEBAR_WIDTH,
        bgcolor=ft.Colors.SURFACE,
        border=ft.Border(right=ft.BorderSide(1, BORDER)),
        padding=ft.Padding.symmetric(horizontal=12, vertical=8),
        content=ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=2,
            controls=[*groups, footer],
        ),
    )


def scroll_area(content: ft.Control, *, horizontal: int = 44) -> ft.Control:
    return ft.Container(
        expand=True,
        content=ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[
                ft.Container(
                    padding=ft.Padding.symmetric(
                        horizontal=horizontal, vertical=34
                    ),
                    content=content,
                )
            ],
        ),
    )


def _breadcrumb(tr, title: str) -> ft.Control:
    page = ft.context.page
    return ft.Row(
        spacing=6,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                on_click=lambda _: page.navigate("/docs/getting-started"),
                content=ft.Text(tr("site.breadcrumb.docs"), size=11, color=MUTED),
            ),
            ft.Icon(ft.Icons.CHEVRON_RIGHT, size=13, color=MUTED),
            ft.Text(title, size=11, color=ft.Colors.ON_SURFACE_VARIANT),
        ],
    )


@ft.component
def site_footer() -> ft.Control:
    tr = use_t()
    return ft.Container(
        margin=ft.Margin.only(top=18),
        padding=ft.Padding.only(top=22),
        border=ft.Border(top=ft.BorderSide(1, BORDER)),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Column(
                    spacing=4,
                    controls=[
                        ft.Text("cs-ui", size=13, weight=ft.FontWeight.W_700),
                        ft.Text(tr("site.footer.tagline"), size=11, color=MUTED),
                    ],
                ),
                ft.Text(
                    tr(
                        "site.footer.copyright",
                        version=PACKAGE_VERSION,
                    ),
                    size=11,
                    color=MUTED,
                ),
            ],
        ),
    )


@ft.component
def doc_page(
    page_key: str,
    sections: Sequence[ft.Control],
    *,
    badges: Sequence[ft.Control] = (),
) -> ft.Control:
    tr = use_t()
    meta = PAGE_BY_KEY[page_key]
    title = tr(meta.title_key)
    previous = page_before(meta.route)
    following = page_after(meta.route)

    next_row: list[ft.Control] = []
    if previous is not None or following is not None:
        next_row.append(
            ft.Row(
                spacing=12,
                controls=[
                    next_card(previous, forward=False)
                    if previous is not None
                    else ft.Container(expand=True),
                    next_card(following, forward=True)
                    if following is not None
                    else ft.Container(expand=True),
                ],
            )
        )

    content = ft.Column(
        spacing=30,
        controls=[
            _breadcrumb(tr, title),
            ft.Column(
                spacing=12,
                controls=[
                    eyebrow(tr(f"site.group.{meta.group}")),
                    ft.Text(title, size=36, weight=ft.FontWeight.W_800),
                    ft.Container(
                        padding=ft.Padding.only(right=40),
                        content=ft.Text(
                            tr(meta.desc_key),
                            size=16,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                            style=ft.TextStyle(height=1.7),
                        ),
                    ),
                    *(
                        [ft.Row(spacing=8, wrap=True, controls=list(badges))]
                        if badges
                        else []
                    ),
                ],
            ),
            *sections,
            *next_row,
            site_footer(),
        ],
    )
    return scroll_area(content)


@ft.component
def docs_layout() -> ft.Control:
    outlet = ft.use_route_outlet()
    location = ft.use_route_location()
    is_home = location in ("", "/")

    body = ft.Row(
        expand=True,
        spacing=0,
        vertical_alignment=ft.CrossAxisAlignment.STRETCH,
        controls=[
            *([] if is_home else [sidebar()]),
            ft.Container(expand=True, bgcolor=PAGE_BG, content=outlet),
        ],
    )

    return ft.Container(
        expand=True,
        bgcolor=PAGE_BG,
        content=ft.Column(
            expand=True,
            spacing=0,
            controls=[top_bar(), body],
        ),
    )
