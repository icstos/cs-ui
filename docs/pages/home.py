"""官网首页。"""

from __future__ import annotations

import flet as ft

from docs.content.snippets import QUICK_START
from docs.core.state import use_stable
from docs.kit import (
    category_card,
    cell,
    code_block,
    demo_card,
    demo_grid,
    feature_card,
    icon_tile,
    scroll_area,
    site_footer,
    stat_card,
    version_chip,
)
from docs.site import (
    CATEGORY_COUNTS,
    CATEGORY_KEYS,
    CATEGORY_ROUTES,
    COMPONENT_TOTAL,
    GITHUB_URL,
    PAGE_BY_KEY,
)
from ui import (
    Button,
    Checkbox,
    Input,
    Switch,
    toast_success,
    use_t,
)

_FEATURE_ICONS = (
    ("reactive", ft.Icons.BOLT_OUTLINED, ft.Colors.PRIMARY),
    ("themed", ft.Icons.PALETTE_OUTLINED, ft.Colors.TERTIARY),
    ("i18n", ft.Icons.TRANSLATE, ft.Colors.SECONDARY),
    ("typed", ft.Icons.DATA_OBJECT, ft.Colors.ERROR),
    ("modular", ft.Icons.EXTENSION_OUTLINED, ft.Colors.PRIMARY),
    ("desktop", ft.Icons.DESKTOP_WINDOWS_OUTLINED, ft.Colors.TERTIARY),
)


@ft.component
def home_page() -> ft.Control:
    tr = use_t()
    page = ft.context.page
    site = "site.home"

    name = use_stable(
        lambda: Input(
            label=tr(f"{site}.playground.input"),
            value=tr(f"{site}.playground.input_value"),
            width=260,
        )
    )
    agree = use_stable(
        lambda: Checkbox(label=tr(f"{site}.playground.checkbox"), value=True)
    )
    notify = use_stable(
        lambda: Switch(label=tr(f"{site}.playground.switch"), value=True)
    )

    hero = ft.Container(
        padding=ft.Padding.symmetric(horizontal=40, vertical=36),
        border_radius=24,
        bgcolor=ft.Colors.SURFACE,
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        content=ft.ResponsiveRow(
            columns=12,
            spacing=40,
            run_spacing=28,
            controls=[
                ft.Container(
                    col={"xs": 12, "md": 5},
                    content=ft.Column(
                        spacing=18,
                        controls=[
                        ft.Row(
                            spacing=10,
                            controls=[
                                ft.Container(
                                    padding=ft.Padding.symmetric(
                                        horizontal=10, vertical=4
                                    ),
                                    border_radius=999,
                                    bgcolor=ft.Colors.PRIMARY_CONTAINER,
                                    content=ft.Text(
                                        tr(f"{site}.eyebrow"),
                                        size=11,
                                        weight=ft.FontWeight.W_700,
                                        color=ft.Colors.ON_PRIMARY_CONTAINER,
                                    ),
                                ),
                                version_chip(),
                            ],
                        ),
                        ft.Text(
                            tr(f"{site}.headline"),
                            size=48,
                            weight=ft.FontWeight.W_800,
                            style=ft.TextStyle(height=1.08),
                        ),
                        ft.Text(
                            tr(f"{site}.subline"),
                            size=16,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                            style=ft.TextStyle(height=1.7),
                        ),
                        ft.Row(
                            spacing=10,
                            wrap=True,
                            controls=[
                                Button(
                                    tr(f"{site}.cta.start"),
                                    is_primary=True,
                                    icon=ft.Icons.ROCKET_LAUNCH,
                                    on_click=lambda _: page.navigate(
                                        "/docs/getting-started"
                                    ),
                                ),
                                Button(
                                    tr(f"{site}.cta.components"),
                                    icon=ft.Icons.VIEW_QUILT,
                                    on_click=lambda _: page.navigate("/components"),
                                ),
                                Button(
                                    tr(f"{site}.cta.github"),
                                    plain=True,
                                    icon=ft.Icons.HUB,
                                    action=ft.OpenUrl(
                                        GITHUB_URL,
                                        target=ft.UrlTarget.BLANK,
                                    ),
                                ),
                            ],
                        ),
                        ft.Row(
                            spacing=14,
                            wrap=True,
                            controls=[
                                ft.Row(
                                    spacing=6,
                                    controls=[
                                        ft.Icon(
                                            ft.Icons.CHECK_CIRCLE,
                                            size=15,
                                            color=ft.Colors.PRIMARY,
                                        ),
                                        ft.Text(
                                            tr(f"{site}.hero.point1"),
                                            size=12,
                                            color=ft.Colors.ON_SURFACE_VARIANT,
                                        ),
                                    ],
                                ),
                                ft.Row(
                                    spacing=6,
                                    controls=[
                                        ft.Icon(
                                            ft.Icons.CHECK_CIRCLE,
                                            size=15,
                                            color=ft.Colors.PRIMARY,
                                        ),
                                        ft.Text(
                                            tr(f"{site}.hero.point2"),
                                            size=12,
                                            color=ft.Colors.ON_SURFACE_VARIANT,
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
                ),
                ft.Container(
                    col={"xs": 12, "md": 7},
                    content=ft.Column(
                        spacing=10,
                        controls=[
                        ft.Row(
                            spacing=8,
                            controls=[
                                icon_tile(
                                    ft.Icons.CODE,
                                    ft.Colors.PRIMARY,
                                    size=32,
                                ),
                                ft.Text(
                                    tr(f"{site}.hero.code_title"),
                                    size=13,
                                    weight=ft.FontWeight.W_600,
                                ),
                            ],
                        ),
                        code_block(
                            QUICK_START,
                            filename="main.py",
                            height=400,
                        ),
                        ],
                    ),
                ),
            ],
        ),
    )

    stats = demo_grid(
        cell(
            stat_card(
                value=str(COMPONENT_TOTAL),
                label=tr(f"{site}.stats.components"),
                icon=ft.Icons.WIDGETS,
            ),
            span=3,
        ),
        cell(
            stat_card(
                value=str(len(CATEGORY_KEYS)),
                label=tr(f"{site}.stats.categories"),
                icon=ft.Icons.CATEGORY_OUTLINED,
                color=ft.Colors.TERTIARY,
            ),
            span=3,
        ),
        cell(
            stat_card(
                value="3",
                label=tr(f"{site}.stats.languages"),
                icon=ft.Icons.TRANSLATE,
                color=ft.Colors.SECONDARY,
            ),
            span=3,
        ),
        cell(
            stat_card(
                value="100%",
                label=tr(f"{site}.stats.typed"),
                icon=ft.Icons.DATA_OBJECT,
                color=ft.Colors.ERROR,
            ),
            span=3,
        ),
    )

    features = ft.Column(
        spacing=16,
        controls=[
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.END,
                controls=[
                    ft.Column(
                        spacing=6,
                        controls=[
                            ft.Text(
                                tr(f"{site}.features.title"),
                                size=24,
                                weight=ft.FontWeight.W_700,
                            ),
                            ft.Text(
                                tr(f"{site}.features.hint"),
                                size=13,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                        ],
                    ),
                ],
            ),
            demo_grid(
                *[
                    cell(
                        feature_card(
                            icon=icon,
                            title=tr(f"{site}.features.{key}.title"),
                            description=tr(f"{site}.features.{key}.desc"),
                            accent=accent,
                        ),
                        span=4,
                    )
                    for key, icon, accent in _FEATURE_ICONS
                ]
            ),
        ],
    )

    catalog = ft.Column(
        spacing=16,
        controls=[
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.END,
                controls=[
                    ft.Column(
                        spacing=6,
                        controls=[
                            ft.Text(
                                tr(f"{site}.catalog.title"),
                                size=24,
                                weight=ft.FontWeight.W_700,
                            ),
                            ft.Text(
                                tr(f"{site}.catalog.hint"),
                                size=13,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                        ],
                    ),
                    Button(
                        tr(f"{site}.catalog.all"),
                        plain=True,
                        icon=ft.Icons.ARROW_FORWARD,
                        on_click=lambda _: page.navigate("/components"),
                    ),
                ],
            ),
            demo_grid(
                *[
                    cell(
                        category_card(
                            category=key,
                            route=CATEGORY_ROUTES[key],
                            icon=PAGE_BY_KEY[key].icon,
                            title=tr(PAGE_BY_KEY[key].title_key),
                            description=tr(PAGE_BY_KEY[key].desc_key),
                            count=CATEGORY_COUNTS[key],
                        ),
                        span=4,
                    )
                    for key in CATEGORY_KEYS
                ]
            ),
        ],
    )

    playground = demo_card(
        title=tr(f"{site}.playground.title"),
        hint=tr(f"{site}.playground.hint"),
        icon=ft.Icons.SCIENCE_OUTLINED,
        stretch=True,
        body=[
            ft.Row(
                spacing=24,
                wrap=True,
                run_spacing=16,
                controls=[
                    name.ui(),
                    ft.Column(
                        spacing=10,
                        controls=[agree.ui(), notify.ui()],
                    ),
                    Button(
                        tr(f"{site}.playground.toast"),
                        is_primary=True,
                        icon=ft.Icons.NOTIFICATIONS_ACTIVE_OUTLINED,
                        on_click=lambda _: toast_success(
                            tr(f"{site}.playground.toast_text"),
                            page=page,
                        ),
                    ),
                ],
            )
        ],
    )

    why = ft.Container(
        padding=ft.Padding.symmetric(horizontal=28, vertical=24),
        border_radius=20,
        bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        content=ft.ResponsiveRow(
            columns=12,
            spacing=28,
            run_spacing=20,
            controls=[
                ft.Container(
                    col={"xs": 12, "md": 5},
                    content=ft.Column(
                        spacing=12,
                        controls=[
                        ft.Text(
                            tr(f"{site}.why.title"),
                            size=22,
                            weight=ft.FontWeight.W_700,
                        ),
                        ft.Text(
                            tr(f"{site}.why.desc"),
                            size=13,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                            style=ft.TextStyle(height=1.7),
                        ),
                        ft.Column(
                            spacing=8,
                            controls=[
                                ft.Row(
                                    spacing=8,
                                    controls=[
                                        ft.Icon(
                                            ft.Icons.CHEVRON_RIGHT,
                                            size=15,
                                            color=ft.Colors.PRIMARY,
                                        ),
                                        ft.Text(
                                            tr(f"{site}.why.point{n}"),
                                            size=13,
                                            color=ft.Colors.ON_SURFACE_VARIANT,
                                        ),
                                    ],
                                )
                                for n in (1, 2, 3, 4)
                            ],
                        ),
                    ],
                    ),
                ),
                ft.Container(
                    col={"xs": 12, "md": 7},
                    content=code_block(
                        """from ui import Card, Column, Text

Card(
    content=Column(
        spacing=12,
        controls=[
            Text("声明式", size=18, weight="bold"),
            Text("状态驱动，而不是手动 update。"),
        ],
    ),
)""",
                        filename="card.py",
                    ),
                ),
            ],
        ),
    )

    cta = ft.Container(
        padding=ft.Padding.symmetric(horizontal=32, vertical=28),
        border_radius=20,
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
                            tr(f"{site}.cta.title"),
                            size=22,
                            weight=ft.FontWeight.W_800,
                            color=ft.Colors.ON_PRIMARY_CONTAINER,
                        ),
                        ft.Text(
                            tr(f"{site}.cta.desc"),
                            size=13,
                            color=ft.Colors.ON_PRIMARY_CONTAINER,
                        ),
                    ],
                ),
                Button(
                    tr(f"{site}.cta.button"),
                    is_primary=True,
                    icon=ft.Icons.ARROW_FORWARD,
                    on_click=lambda _: page.navigate("/docs/getting-started"),
                ),
            ],
        ),
    )

    content = ft.Column(
        spacing=44,
        controls=[
            hero,
            stats,
            features,
            catalog,
            playground,
            why,
            cta,
            site_footer(),
        ],
    )
    return scroll_area(content, horizontal=56)
