"""主题与设计令牌指南。"""

from __future__ import annotations

import flet as ft

from docs.content.snippets import THEME_STATE, TOKENS
from docs.core.state import use_stable
from docs.kit import (
    PropRow,
    badge,
    bullets,
    callout,
    code_block,
    demo_card,
    doc_page,
    prop_table,
    section,
)
from ui import (
    PRIMARY_SEEDS,
    Button,
    Input,
    StyleType,
    on_semantic,
    semantic,
    semantic_text,
    use_t,
    use_theme,
)

_MODE_NAMES = ("system", "light", "dark")
_SEMANTIC_ROLES = ("success", "warning", "danger", "info", "neutral")


@ft.component
def theming_page() -> ft.Control:
    tr = use_t()
    theme = use_theme()
    site = "site.theming"

    preview_input = use_stable(
        lambda: Input(
            label=tr(f"{site}.live.input"),
            value=tr(f"{site}.live.input_value"),
            width=260,
        )
    )

    mode_buttons = ft.Row(
        spacing=8,
        wrap=True,
        controls=[
            Button(
                tr(f"{site}.live.mode_{name}"),
                style_type=(
                    StyleType.PRIMARY if theme.mode == name else StyleType.DEFAULT
                ),
                on_click=lambda _, value=name: theme.set_mode(value),
            )
            for name in _MODE_NAMES
        ],
    )

    seed_swatches = ft.Row(
        spacing=8,
        wrap=True,
        controls=[
            ft.Container(
                width=28,
                height=28,
                border_radius=8,
                bgcolor=seed,
                tooltip=name,
                border=ft.Border.all(
                    2,
                    (
                        ft.Colors.ON_SURFACE
                        if theme.primary.lower() == seed.lower()
                        else ft.Colors.TRANSPARENT
                    ),
                ),
                on_click=lambda _, value=seed: theme.set_primary(value),
                ink=True,
            )
            for name, seed in PRIMARY_SEEDS.items()
        ],
    )

    live = demo_card(
        title=tr(f"{site}.live.title"),
        hint=tr(f"{site}.live.hint"),
        icon=ft.Icons.PALETTE,
        stretch=True,
        body=[
            ft.Text(tr(f"{site}.live.mode"), size=12, weight=ft.FontWeight.W_600),
            mode_buttons,
            ft.Text(tr(f"{site}.live.primary"), size=12, weight=ft.FontWeight.W_600),
            seed_swatches,
            ft.Container(height=1, bgcolor=ft.Colors.OUTLINE_VARIANT),
            ft.Container(
                padding=20,
                border_radius=12,
                bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
                content=ft.Column(
                    spacing=12,
                    controls=[
                        ft.Text(
                            tr(f"{site}.preview.title"),
                            size=18,
                            weight=ft.FontWeight.W_700,
                        ),
                        ft.Text(
                            tr(f"{site}.preview.body"),
                            size=13,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        preview_input.ui(),
                        ft.Row(
                            spacing=8,
                            controls=[
                                Button(tr(f"{site}.preview.primary")),
                                Button(
                                    tr(f"{site}.preview.secondary"),
                                    plain=True,
                                ),
                            ],
                        ),
                    ],
                ),
            ),
        ],
    )

    semantic_card = demo_card(
        title=tr(f"{site}.semantic.title"),
        hint=tr(f"{site}.semantic.desc"),
        icon=ft.Icons.CIRCLE_OUTLINED,
        stretch=True,
        body=[
            ft.Row(
                spacing=8,
                wrap=True,
                controls=[
                    ft.Container(
                        padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                        border_radius=999,
                        bgcolor=semantic(role),
                        content=ft.Text(
                            tr(f"{site}.semantic.{role}"),
                            size=11,
                            weight=ft.FontWeight.W_700,
                            color=on_semantic(role),
                        ),
                    )
                    for role in _SEMANTIC_ROLES
                ],
            ),
            ft.Row(
                spacing=8,
                wrap=True,
                controls=[
                    ft.Container(
                        padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                        border_radius=999,
                        bgcolor=ft.Colors.with_opacity(0.12, semantic(role)),
                        content=ft.Text(
                            tr(f"{site}.semantic.{role}"),
                            size=11,
                            weight=ft.FontWeight.W_600,
                            color=semantic_text(role),
                        ),
                    )
                    for role in _SEMANTIC_ROLES
                ],
            ),
        ],
    )

    tokens_table = prop_table(
        [
            PropRow(
                "SPACE",
                "dict[str, int]",
                tr(f"{site}.tokens.space"),
            ),
            PropRow(
                "RADIUS",
                "dict[str, int]",
                tr(f"{site}.tokens.radius"),
            ),
            PropRow(
                "FONT_SIZE",
                "dict[str, int]",
                tr(f"{site}.tokens.font"),
            ),
            PropRow(
                "elevation(level)",
                "BoxShadow",
                tr(f"{site}.tokens.elevation"),
            ),
            PropRow(
                "overlay(opacity)",
                "str",
                tr(f"{site}.tokens.overlay"),
            ),
            PropRow(
                "semantic(role)",
                "str",
                tr(f"{site}.tokens.semantic"),
            ),
        ],
        headers=(
            tr(f"{site}.table.name"),
            tr(f"{site}.table.type"),
            tr(f"{site}.table.desc"),
        ),
    )

    tokens = section(
        tr(f"{site}.tokens.title"),
        tr(f"{site}.tokens.desc"),
        tokens_table,
        code_block(TOKENS, filename="tokens.py"),
    )

    modes = section(
        tr(f"{site}.modes.title"),
        tr(f"{site}.modes.desc"),
        code_block(THEME_STATE, filename="theme.py"),
        bullets(tr.list(f"{site}.modes.points")),
    )

    trap = callout(
        "warning",
        tr(f"{site}.trap.desc"),
        title=tr(f"{site}.trap.title"),
    )

    return doc_page(
        "theming",
        [live, modes, tokens, semantic_card, trap],
        badges=[
            badge("Material 3"),
            badge("Dark mode", role="info"),
            badge("WCAG AA", role="success"),
        ],
    )
