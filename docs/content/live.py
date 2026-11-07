"""指南页里的实时演示：主题切换、语言切换、令牌速查。

这些演示都直接读写框架的全局状态（``use_theme()`` / ``use_i18n()``），
所以正文里说"切换后立即生效"是可以当场验证的。
"""

from __future__ import annotations

import datetime as dt

import flet as ft

from docs import kit
from ui import (
    PRIMARY_SEEDS,
    RADIUS,
    SPACE,
    Button,
    Input,
    format_date,
    format_list,
    format_number,
    semantic,
    use_i18n,
    use_t,
)
from ui.core.theme import use_theme

_MODES: tuple[str, ...] = ("system", "light", "dark")


def _pill(label: str, *, active: bool, on_click) -> ft.Control:
    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=11, vertical=5),
        border_radius=8,
        bgcolor=ft.Colors.PRIMARY_CONTAINER if active else kit.RAISED,
        border=ft.Border.all(1, ft.Colors.TRANSPARENT if active else kit.BORDER),
        on_click=on_click,
        ink=True,
        content=ft.Text(
            label,
            size=12,
            weight=ft.FontWeight.W_600 if active else ft.FontWeight.W_400,
            color=ft.Colors.ON_PRIMARY_CONTAINER if active else kit.MUTED,
        ),
    )


@ft.component
def theme_playground() -> ft.Control:
    """模式 + 主色 + 一块跟随变色的预览。"""
    theme = use_theme()
    tr = use_t()
    name = kit.use_stable(
        lambda: Input(
            label=tr("theme.live.input"), value=tr("theme.live.value"), width=240
        )
    )

    swatches = ft.Row(
        spacing=8,
        wrap=True,
        controls=[
            ft.Container(
                width=24,
                height=24,
                border_radius=7,
                bgcolor=seed,
                tooltip=tr(f"ui.theme.seeds.{key}"),
                border=ft.Border.all(
                    2,
                    ft.Colors.ON_SURFACE
                    if theme.primary.lower() == seed.lower()
                    else ft.Colors.TRANSPARENT,
                ),
                on_click=lambda _e, value=seed: theme.set_primary(value),
            )
            for key, seed in PRIMARY_SEEDS.items()
        ],
    )

    return kit.surface(
        padding=18,
        content=ft.Column(
            spacing=16,
            controls=[
                ft.Row(
                    spacing=6,
                    controls=[
                        _pill(
                            tr(f"theme.mode.{mode}"),
                            active=theme.mode == mode,
                            on_click=lambda _e, value=mode: theme.set_mode(value),
                        )
                        for mode in _MODES
                    ],
                ),
                ft.Column(
                    spacing=7,
                    controls=[
                        ft.Text(tr("theme.live.primary"), size=11, color=kit.MUTED),
                        swatches,
                    ],
                ),
                kit.hairline(),
                name.ui(),
                ft.Row(
                    spacing=8,
                    controls=[
                        Button(tr("theme.live.action"), is_primary=True),
                        Button(tr("theme.live.secondary"), plain=True),
                    ],
                ),
            ],
        ),
    )


@ft.component
def locale_playground() -> ft.Control:
    """语言 + 三种格式化输出 + 一个"切语言不丢内容"的输入框。"""
    i18n = use_i18n()
    tr = use_t()
    name = kit.use_stable(
        lambda: Input(
            label=tr("i18n.live.input"), value=tr("i18n.live.value"), width=240
        )
    )

    today = dt.date(2026, 9, 26)
    rows: tuple[tuple[str, str], ...] = (
        ("i18n.live.date", format_date(today, long=True)),
        ("i18n.live.number", format_number(1_287_640)),
        ("i18n.live.list", format_list(["A", "B", "C"])),
        ("i18n.live.time", format_date(today)),
    )

    return kit.surface(
        padding=18,
        content=ft.Column(
            spacing=16,
            controls=[
                ft.Row(
                    spacing=6,
                    wrap=True,
                    controls=[
                        _pill(
                            language.native_name,
                            active=language.code == i18n.locale,
                            on_click=lambda _e, code=language.code: i18n.set_locale(
                                code
                            ),
                        )
                        for language in i18n.languages()
                    ],
                ),
                ft.Column(
                    spacing=8,
                    controls=[
                        ft.Row(
                            spacing=10,
                            controls=[
                                ft.Text(tr(key), size=11.5, color=kit.MUTED, width=96),
                                ft.Text(
                                    value,
                                    size=12.5,
                                    weight=ft.FontWeight.W_500,
                                    selectable=True,
                                ),
                            ],
                        )
                        for key, value in rows
                    ],
                ),
                kit.hairline(),
                name.ui(),
            ],
        ),
    )


@ft.component
def semantic_palette() -> ft.Control:
    """语义色：深浅模式下都保证可读的一组状态色。"""
    tr = use_t()
    roles = ("success", "warning", "danger", "info", "neutral")
    return ft.Row(
        spacing=8,
        wrap=True,
        controls=[
            ft.Container(
                width=92,
                padding=ft.Padding.symmetric(vertical=10),
                border_radius=10,
                bgcolor=ft.Colors.with_opacity(0.12, semantic(role)),
                border=ft.Border.all(1, ft.Colors.with_opacity(0.28, semantic(role))),
                content=ft.Column(
                    spacing=6,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(
                            width=26,
                            height=4,
                            border_radius=2,
                            bgcolor=semantic(role),
                        ),
                        ft.Text(
                            tr(f"theme.role.{role}"),
                            size=11.5,
                            weight=ft.FontWeight.W_600,
                        ),
                    ],
                ),
            )
            for role in roles
        ],
    )


@ft.component
def token_scales() -> ft.Control:
    """间距与圆角刻度：不用背数字，看一眼就知道该用哪一档。"""
    tr = use_t()
    spaces = ("1", "2", "3", "4", "6", "8")
    radii = ("xs", "sm", "md", "lg", "xl")
    return ft.Column(
        spacing=14,
        controls=[
            ft.Column(
                spacing=6,
                controls=[
                    ft.Text(tr("theme.token.space"), size=11.5, color=kit.MUTED),
                    ft.Row(
                        spacing=10,
                        wrap=True,
                        controls=[
                            ft.Column(
                                spacing=3,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Container(
                                        width=SPACE[key],
                                        height=SPACE[key],
                                        bgcolor=ft.Colors.PRIMARY,
                                        border_radius=2,
                                    ),
                                    ft.Text(key, size=9.5, color=kit.MUTED),
                                ],
                            )
                            for key in spaces
                        ],
                    ),
                ],
            ),
            ft.Column(
                spacing=6,
                controls=[
                    ft.Text(tr("theme.token.radius"), size=11.5, color=kit.MUTED),
                    ft.Row(
                        spacing=10,
                        controls=[
                            ft.Container(
                                width=46,
                                height=34,
                                bgcolor=ft.Colors.SECONDARY_CONTAINER,
                                border_radius=RADIUS[key],
                                alignment=ft.Alignment.CENTER,
                                content=ft.Text(key, size=10, color=kit.MUTED),
                            )
                            for key in radii
                        ],
                    ),
                ],
            ),
        ],
    )


__all__ = [
    "locale_playground",
    "semantic_palette",
    "theme_playground",
    "token_scales",
]
