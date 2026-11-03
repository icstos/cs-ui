"""文档站的卡片组件。"""

from __future__ import annotations

from collections.abc import Sequence

import flet as ft

from docs.site import CATEGORY_ROLE, PACKAGE_VERSION, PageMeta
from ui import semantic_text, use_t
from ui.core.theme import use_theme

MUTED = ft.Colors.ON_SURFACE_VARIANT
BORDER = ft.Colors.OUTLINE_VARIANT
CARD_BG = ft.Colors.SURFACE


def category_color(key: str) -> ft.ColorValue:
    role = CATEGORY_ROLE.get(key, "primary")
    return ft.Colors.PRIMARY if role == "primary" else semantic_text(role)


def icon_tile(icon: ft.IconData, color: ft.ColorValue, *, size: int = 42) -> ft.Control:
    return ft.Container(
        width=size,
        height=size,
        border_radius=size / 3.2,
        bgcolor=ft.Colors.with_opacity(0.12, color),
        alignment=ft.Alignment.CENTER,
        content=ft.Icon(icon, size=size * 0.52, color=color),
    )


@ft.component
def feature_card(
    *,
    icon: ft.IconData,
    title: str,
    description: str,
    accent: ft.ColorValue = ft.Colors.PRIMARY,
) -> ft.Control:
    hovered, set_hovered = ft.use_state(False)
    return ft.Container(
        padding=22,
        border_radius=16,
        bgcolor=CARD_BG,
        border=ft.Border.all(1, ft.Colors.PRIMARY if hovered else BORDER),
        animate=ft.Animation(160, ft.AnimationCurve.EASE_OUT),
        on_hover=lambda e: set_hovered(bool(e.data)),
        content=ft.Column(
            spacing=14,
            controls=[
                icon_tile(icon, accent),
                ft.Text(title, size=15, weight=ft.FontWeight.W_700),
                ft.Text(
                    description,
                    size=13,
                    color=MUTED,
                    style=ft.TextStyle(height=1.6),
                ),
            ],
        ),
    )


@ft.component
def category_card(
    *,
    category: str,
    route: str,
    icon: ft.IconData,
    title: str,
    description: str,
    count: int,
) -> ft.Control:
    use_theme()
    page = ft.context.page
    tr = use_t()
    color = category_color(category)
    hovered, set_hovered = ft.use_state(False)

    return ft.Container(
        border_radius=16,
        bgcolor=CARD_BG,
        border=ft.Border.all(1, ft.Colors.PRIMARY if hovered else BORDER),
        animate=ft.Animation(160, ft.AnimationCurve.EASE_OUT),
        on_hover=lambda e: set_hovered(bool(e.data)),
        on_click=lambda _: page.navigate(route),
        ink=True,
        content=ft.Container(
            padding=18,
            content=ft.Column(
                spacing=12,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                        controls=[
                            icon_tile(icon, color, size=38),
                            ft.Container(
                                padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                                border_radius=999,
                                bgcolor=ft.Colors.with_opacity(0.10, color),
                                content=ft.Text(
                                    tr("site.components.count", count=count),
                                    size=10,
                                    color=color,
                                    weight=ft.FontWeight.W_700,
                                ),
                            ),
                        ],
                    ),
                    ft.Text(title, size=15, weight=ft.FontWeight.W_700),
                    ft.Text(
                        description,
                        size=12,
                        color=MUTED,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                        style=ft.TextStyle(height=1.55),
                    ),
                    ft.Row(
                        spacing=4,
                        controls=[
                            ft.Text(
                                tr("site.components.open"),
                                size=11,
                                color=color,
                                weight=ft.FontWeight.W_600,
                            ),
                            ft.Icon(ft.Icons.ARROW_FORWARD, size=13, color=color),
                        ],
                    ),
                ],
            ),
        ),
    )


@ft.component
def stat_card(
    *,
    value: str,
    label: str,
    icon: ft.IconData | None = None,
    color: ft.ColorValue = ft.Colors.PRIMARY,
) -> ft.Control:
    use_theme()
    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=18, vertical=14),
        border_radius=14,
        bgcolor=CARD_BG,
        border=ft.Border.all(1, BORDER),
        content=ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                *(
                    [ft.Icon(icon, size=20, color=color)]
                    if icon is not None
                    else []
                ),
                ft.Column(
                    spacing=0,
                    controls=[
                        ft.Text(
                            value,
                            size=22,
                            weight=ft.FontWeight.W_800,
                            color=ft.Colors.ON_SURFACE,
                        ),
                        ft.Text(label, size=11, color=MUTED),
                    ],
                ),
            ],
        ),
    )


def demo_card(
    *,
    title: str,
    hint: str,
    body: Sequence[ft.Control],
    stretch: bool = False,
    icon: ft.IconData | None = None,
) -> ft.Control:
    header: list[ft.Control] = [
        ft.Text(title, size=17, weight=ft.FontWeight.W_700),
    ]
    if icon is not None:
        header.insert(
            0,
            ft.Container(
                width=30,
                height=30,
                border_radius=9,
                bgcolor=ft.Colors.PRIMARY_CONTAINER,
                alignment=ft.Alignment.CENTER,
                content=ft.Icon(icon, size=16, color=ft.Colors.ON_PRIMARY_CONTAINER),
            ),
        )
    return ft.Container(
        padding=20,
        border_radius=16,
        bgcolor=CARD_BG,
        border=ft.Border.all(1, BORDER),
        content=ft.Column(
            spacing=12,
            horizontal_alignment=(
                ft.CrossAxisAlignment.STRETCH
                if stretch
                else ft.CrossAxisAlignment.START
            ),
            controls=[
                ft.Row(spacing=10, controls=header),
                ft.Text(
                    hint,
                    size=12,
                    color=MUTED,
                    style=ft.TextStyle(height=1.55),
                ),
                ft.Container(height=1, bgcolor=BORDER),
                ft.Column(
                    spacing=12,
                    horizontal_alignment=(
                        ft.CrossAxisAlignment.STRETCH
                        if stretch
                        else ft.CrossAxisAlignment.START
                    ),
                    controls=list(body),
                ),
            ],
        ),
    )


def cell(control: ft.Control, *, span: int = 6) -> ft.Control:
    """把卡片放进 12 栏栅格；``span=12`` 即整行。"""
    narrow = 12 if span >= 12 else 6
    return ft.Container(content=control, col={"xs": narrow, "md": span})


def demo_grid(*cells: ft.Control, spacing: int = 14) -> ft.Control:
    return ft.ResponsiveRow(
        columns=12,
        spacing=spacing,
        run_spacing=spacing,
        controls=list(cells),
    )


@ft.component
def component_chip(name: str, route: str) -> ft.Control:
    page = ft.context.page
    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=10, vertical=5),
        border_radius=7,
        bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
        border=ft.Border.all(1, BORDER),
        on_click=lambda _: page.navigate(route),
        ink=True,
        content=ft.Text(
            name,
            size=11,
            color=ft.Colors.ON_SURFACE_VARIANT,
            font_family="monospace",
        ),
    )


@ft.component
def next_card(page_meta: PageMeta, *, forward: bool) -> ft.Control:
    tr = use_t()
    page = ft.context.page
    title = tr(page_meta.title_key)
    direction = tr("site.next") if forward else tr("site.prev")
    return ft.Container(
        expand=True,
        padding=16,
        border_radius=12,
        bgcolor=CARD_BG,
        border=ft.Border.all(1, BORDER),
        on_click=lambda _: page.navigate(page_meta.route),
        ink=True,
        content=ft.Column(
            spacing=4,
            horizontal_alignment=(
                ft.CrossAxisAlignment.END if forward else ft.CrossAxisAlignment.START
            ),
            controls=[
                ft.Row(
                    spacing=6,
                    alignment=(
                        ft.MainAxisAlignment.END
                        if forward
                        else ft.MainAxisAlignment.START
                    ),
                    controls=[
                        *(
                            [ft.Icon(ft.Icons.ARROW_BACK, size=13, color=MUTED)]
                            if not forward
                            else []
                        ),
                        ft.Text(direction, size=11, color=MUTED),
                        *(
                            [ft.Icon(ft.Icons.ARROW_FORWARD, size=13, color=MUTED)]
                            if forward
                            else []
                        ),
                    ],
                ),
                ft.Text(
                    title,
                    size=13,
                    weight=ft.FontWeight.W_600,
                    text_align=ft.TextAlign.END if forward else ft.TextAlign.START,
                ),
            ],
        ),
    )


@ft.component
def version_chip() -> ft.Control:
    tr = use_t()
    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=9, vertical=3),
        border_radius=999,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
        content=ft.Text(
            tr("site.version", version=PACKAGE_VERSION),
            size=10,
            color=ft.Colors.ON_SURFACE_VARIANT,
            weight=ft.FontWeight.W_600,
        ),
    )
