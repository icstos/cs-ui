"""可复用的文档排版块：页头、代码块、提示框、表格、步骤。"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import flet as ft
import flet_code_editor as fce

from ui import Code, semantic, semantic_text, use_t
from ui.core.theme import use_theme

MUTED = ft.Colors.ON_SURFACE_VARIANT
BORDER = ft.Colors.OUTLINE_VARIANT
CARD_BG = ft.Colors.SURFACE
PAGE_BG = ft.Colors.SURFACE_CONTAINER_LOWEST
ACCENT = ft.Colors.PRIMARY

_CODE_LINE_HEIGHT = 24
_CODE_PADDING = 8

_LANGUAGES: dict[str, fce.CodeLanguage] = {
    "python": fce.CodeLanguage.PYTHON,
    "bash": fce.CodeLanguage.BASH,
    "shell": fce.CodeLanguage.SHELL,
    "json": fce.CodeLanguage.JSON,
    "yaml": fce.CodeLanguage.YAML,
    "text": fce.CodeLanguage.PLAINTEXT,
}

_CALLOUT_ROLE: dict[str, tuple[str, ft.IconData]] = {
    "info": ("info", ft.Icons.INFO_OUTLINE),
    "success": ("success", ft.Icons.CHECK_CIRCLE_OUTLINE),
    "warning": ("warning", ft.Icons.WARNING_AMBER_ROUNDED),
    "danger": ("danger", ft.Icons.ERROR_OUTLINE),
}


def eyebrow(text: str) -> ft.Control:
    return ft.Text(
        text.upper(),
        size=11,
        weight=ft.FontWeight.W_700,
        color=ft.Colors.PRIMARY,
        style=ft.TextStyle(letter_spacing=1.4),
    )


def paragraph(text: str, *, muted: bool = False) -> ft.Control:
    return ft.Text(
        text,
        size=14,
        color=MUTED if muted else ft.Colors.ON_SURFACE,
        style=ft.TextStyle(height=1.72),
    )


def bullets(items: Sequence[str], *, color: ft.ColorValue = ft.Colors.PRIMARY) -> ft.Control:
    rows = [
        ft.Row(
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                ft.Container(
                    width=6,
                    height=6,
                    border_radius=3,
                    bgcolor=color,
                    margin=ft.Margin.only(top=8),
                ),
                ft.Text(
                    item,
                    size=14,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                    style=ft.TextStyle(height=1.65),
                    expand=True,
                ),
            ],
        )
        for item in items
    ]
    return ft.Column(spacing=8, controls=rows)


def section(
    title: str,
    description: str | None = None,
    *controls: ft.Control,
    spacing: int = 14,
) -> ft.Control:
    body: list[ft.Control] = [
        ft.Text(title, size=21, weight=ft.FontWeight.W_700),
    ]
    if description:
        body.append(paragraph(description, muted=True))
    body.extend(controls)
    return ft.Column(spacing=spacing, controls=body)


def page_header(
    *,
    eyebrow_text: str,
    title: str,
    description: str,
    badges: Sequence[ft.Control] = (),
) -> ft.Control:
    controls: list[ft.Control] = [
        eyebrow(eyebrow_text),
        ft.Text(title, size=36, weight=ft.FontWeight.W_800),
        ft.Container(
            padding=ft.Padding.only(right=40),
            content=ft.Text(
                description,
                size=16,
                color=ft.Colors.ON_SURFACE_VARIANT,
                style=ft.TextStyle(height=1.7),
            ),
        ),
    ]
    if badges:
        controls.append(ft.Row(spacing=8, wrap=True, controls=list(badges)))
    return ft.Column(spacing=12, controls=controls)


def badge(text: str, *, role: str = "primary") -> ft.Control:
    if role == "primary":
        fg = ft.Colors.ON_PRIMARY_CONTAINER
        bg = ft.Colors.PRIMARY_CONTAINER
    else:
        fg = semantic_text(role)
        bg = ft.Colors.with_opacity(0.12, semantic(role))
    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=10, vertical=4),
        border_radius=999,
        bgcolor=bg,
        content=ft.Text(text, size=11, color=fg, weight=ft.FontWeight.W_600),
    )


def kbd(text: str) -> ft.Control:
    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=5, vertical=2),
        border_radius=4,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        content=ft.Text(text, size=10, color=MUTED),
    )


@ft.component
def code_block(
    code: str,
    *,
    language: str = "python",
    filename: str | None = None,
    height: int | None = None,
) -> ft.Control:
    """带标题栏与复制按钮的只读代码块，跟随明暗主题切换配色。"""
    theme = use_theme()
    tr = use_t()
    code_language = _LANGUAGES.get(language, fce.CodeLanguage.PYTHON)
    code_theme = (
        fce.CodeTheme.ATOM_ONE_DARK if theme.is_dark else fce.CodeTheme.ATOM_ONE_LIGHT
    )
    lines = code.count("\n") + 1
    # Code 控件每行约 24px；高度按行边界取整，避免最后一行被截成半行。
    requested = height or min(520, lines * _CODE_LINE_HEIGHT + _CODE_PADDING)
    resolved_height = max(
        _CODE_LINE_HEIGHT + _CODE_PADDING,
        (requested - _CODE_PADDING) // _CODE_LINE_HEIGHT * _CODE_LINE_HEIGHT
        + _CODE_PADDING,
    )
    label = filename or language.upper()

    return ft.Container(
        border=ft.Border.all(1, BORDER),
        border_radius=12,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        bgcolor=ft.Colors.SURFACE,
        content=ft.Column(
            spacing=0,
            controls=[
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=14, vertical=6),
                    bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
                    border=ft.Border(bottom=ft.BorderSide(1, BORDER)),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text(
                                label,
                                size=11,
                                color=MUTED,
                                weight=ft.FontWeight.W_600,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.CONTENT_COPY,
                                icon_size=15,
                                icon_color=MUTED,
                                tooltip=tr("site.copy"),
                                padding=4,
                                action=ft.CopyToClipboard(code),
                            ),
                        ],
                    ),
                ),
                Code(
                    value=code,
                    language=code_language,
                    code_theme=code_theme,
                    height=resolved_height,
                    read_only=True,
                ),
            ],
        ),
    )


@ft.component
def callout(kind: str, body: str, *, title: str | None = None) -> ft.Control:
    role, icon = _CALLOUT_ROLE.get(kind, _CALLOUT_ROLE["info"])
    color = semantic_text(role)
    controls: list[ft.Control] = [
        ft.Icon(icon, size=18, color=color),
        ft.Column(
            expand=True,
            spacing=3,
            controls=[
                *(
                    [ft.Text(title, size=13, weight=ft.FontWeight.W_700)]
                    if title
                    else []
                ),
                ft.Text(
                    body,
                    size=13,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                    style=ft.TextStyle(height=1.6),
                ),
            ],
        ),
    ]
    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=16, vertical=13),
        border_radius=10,
        bgcolor=ft.Colors.with_opacity(0.08, semantic(role)),
        border=ft.Border(left=ft.BorderSide(3, semantic(role))),
        content=ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=controls,
        ),
    )


@dataclass(frozen=True, slots=True)
class PropRow:
    name: str
    type: str
    description: str


def prop_table(rows: Sequence[PropRow], *, headers: tuple[str, str, str]) -> ft.Control:
    header = ft.Row(
        spacing=16,
        controls=[
            ft.Text(headers[0], size=11, color=MUTED, weight=ft.FontWeight.W_700, width=150),
            ft.Text(headers[1], size=11, color=MUTED, weight=ft.FontWeight.W_700, width=170),
            ft.Text(headers[2], size=11, color=MUTED, weight=ft.FontWeight.W_700, expand=True),
        ],
    )
    body_rows: list[ft.Control] = [header]
    for row in rows:
        body_rows.append(
            ft.Container(
                padding=ft.Padding.symmetric(vertical=9),
                border=ft.Border(top=ft.BorderSide(1, BORDER)),
                content=ft.Row(
                    spacing=16,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        ft.Text(
                            row.name,
                            size=12,
                            weight=ft.FontWeight.W_600,
                            font_family="monospace",
                            width=150,
                            selectable=True,
                        ),
                        ft.Text(
                            row.type,
                            size=11,
                            color=ft.Colors.PRIMARY,
                            font_family="monospace",
                            width=170,
                            selectable=True,
                        ),
                        ft.Text(
                            row.description,
                            size=12,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                            style=ft.TextStyle(height=1.5),
                            expand=True,
                        ),
                    ],
                ),
            )
        )
    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=16, vertical=12),
        border=ft.Border.all(1, BORDER),
        border_radius=10,
        bgcolor=CARD_BG,
        content=ft.Column(spacing=0, controls=body_rows),
    )


def steps(items: Sequence[tuple[str, str]]) -> ft.Control:
    rows: list[ft.Control] = []
    for index, (title, description) in enumerate(items, start=1):
        rows.append(
            ft.Row(
                spacing=14,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.Container(
                        width=28,
                        height=28,
                        border_radius=14,
                        bgcolor=ft.Colors.PRIMARY_CONTAINER,
                        alignment=ft.Alignment.CENTER,
                        content=ft.Text(
                            str(index),
                            size=12,
                            weight=ft.FontWeight.W_700,
                            color=ft.Colors.ON_PRIMARY_CONTAINER,
                        ),
                    ),
                    ft.Column(
                        expand=True,
                        spacing=3,
                        controls=[
                            ft.Text(title, size=14, weight=ft.FontWeight.W_600),
                            ft.Text(
                                description,
                                size=13,
                                color=MUTED,
                                style=ft.TextStyle(height=1.6),
                            ),
                        ],
                    ),
                ],
            )
        )
    return ft.Column(spacing=18, controls=rows)


def hairline() -> ft.Control:
    return ft.Container(height=1, bgcolor=BORDER)
