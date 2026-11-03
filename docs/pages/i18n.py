"""多语言指南。"""

from __future__ import annotations

from datetime import date

import flet as ft

from docs.content.snippets import I18N_FORMAT, I18N_REGISTER, I18N_USE
from docs.core.state import use_stable
from docs.kit import (
    bullets,
    callout,
    code_block,
    demo_card,
    doc_page,
    section,
)
from ui import (
    Input,
    LanguageSwitcher,
    format_date,
    format_number,
    use_t,
)


def _sample_date() -> date:
    return date(2026, 9, 26)


@ft.component
def i18n_page() -> ft.Control:
    tr = use_t()
    site = "site.i18n"
    sample = _sample_date()

    name_input = use_stable(
        lambda: Input(
            label=tr(f"{site}.live.input"),
            value=tr(f"{site}.live.input_value"),
            width=260,
        )
    )

    live = demo_card(
        title=tr(f"{site}.live.title"),
        hint=tr(f"{site}.live.hint"),
        icon=ft.Icons.TRANSLATE,
        stretch=True,
        body=[
            ft.Row(
                spacing=12,
                wrap=True,
                controls=[
                    LanguageSwitcher(),
                    ft.Container(
                        padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                        border_radius=999,
                        bgcolor=ft.Colors.PRIMARY_CONTAINER,
                        content=ft.Text(
                            tr(f"{site}.live.current", locale=tr.locale),
                            size=11,
                            weight=ft.FontWeight.W_600,
                            color=ft.Colors.ON_PRIMARY_CONTAINER,
                        ),
                    ),
                ],
            ),
            ft.Container(height=1, bgcolor=ft.Colors.OUTLINE_VARIANT),
            name_input.ui(),
            ft.Column(
                spacing=6,
                controls=[
                    ft.Text(tr(f"{site}.live.sample"), size=14),
                    ft.Text(
                        tr(
                            f"{site}.live.date",
                            value=format_date(sample, long=True),
                        ),
                        size=13,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                    ft.Text(
                        tr(
                            f"{site}.live.number",
                            value=format_number(1286),
                        ),
                        size=13,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                ],
            ),
        ],
    )

    overview = section(
        tr(f"{site}.overview.title"),
        tr(f"{site}.overview.desc"),
        bullets(tr.list(f"{site}.overview.points")),
    )

    register = section(
        tr(f"{site}.register.title"),
        tr(f"{site}.register.desc"),
        code_block(I18N_REGISTER, filename="messages.py", height=300),
        callout(
            "info",
            tr(f"{site}.register.note"),
            title=tr(f"{site}.register.note_title"),
        ),
    )

    usage = section(
        tr(f"{site}.use.title"),
        tr(f"{site}.use.desc"),
        code_block(I18N_USE, filename="toolbar.py"),
    )

    formatting = section(
        tr(f"{site}.format.title"),
        tr(f"{site}.format.desc"),
        code_block(I18N_FORMAT, filename="format.py"),
        bullets(tr.list(f"{site}.format.points")),
    )

    fallback = section(
        tr(f"{site}.fallback.title"),
        tr(f"{site}.fallback.desc"),
        bullets(tr.list(f"{site}.fallback.points")),
    )

    persist = section(
        tr(f"{site}.persist.title"),
        tr(f"{site}.persist.desc"),
    )

    return doc_page(
        "i18n",
        [live, overview, register, usage, formatting, fallback, persist],
    )
