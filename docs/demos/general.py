"""通用组件演示。"""

from __future__ import annotations

import flet as ft

from docs.demos._helpers import BORDER, LOGO_FILE, MUTED, use_stable
from docs.kit import cell, code_block, demo_card, demo_grid, doc_page
from ui import (
    Button,
    ButtonShape,
    Chip,
    Column,
    Divider,
    Header_1,
    Header_2,
    Header_3,
    Header_4,
    Header_5,
    Image,
    Json,
    Link,
    Markdown,
    Quote,
    StyleType,
    Text,
    use_t,
)

_IMPORT_SNIPPET = """from ui import Button, Card, Column, Row, Text

Row(
    spacing=10,
    controls=[
        Button("保存", is_primary=True),
        Button("取消", plain=True),
    ],
)"""


@ft.component
def general_page() -> ft.Control:
    tr = use_t()

    chip_single = use_stable(
        lambda: Chip(
            label=tr("general.chip.single"),
            options=tr.list("general.chip.options"),
        )
    )
    chip_multi = use_stable(
        lambda: Chip(
            label=tr("general.chip.multi"),
            options=tr.list("general.chip.multi_options"),
            multi_select=True,
            selected_values=tr.list("general.chip.multi_options")[1:2],
        )
    )

    typography = demo_card(
        title=tr("general.text.title"),
        hint=tr("general.text.hint"),
        icon=ft.Icons.TEXT_FIELDS,
        stretch=True,
        body=[
            Column(
                spacing=4,
                controls=[
                    Header_1("Header_1"),
                    Header_2("Header_2"),
                    Header_3("Header_3"),
                    Header_4("Header_4"),
                    Header_5("Header_5"),
                ],
            ),
            Text(tr("general.text.body"), size=14),
            Quote(tr("general.text.quote"), size=14),
            Link(tr("general.text.link"), link="https://flet.dev"),
        ],
    )

    buttons = demo_card(
        title=tr("general.button.title"),
        hint=tr("general.button.hint"),
        icon=ft.Icons.SMART_BUTTON,
        body=[
            ft.Row(
                wrap=True,
                spacing=10,
                run_spacing=10,
                controls=[Button(style.name, style_type=style) for style in StyleType],
            ),
            ft.Row(
                wrap=True,
                spacing=10,
                run_spacing=10,
                controls=[
                    Button(
                        tr("general.button.plain", name=style.name),
                        style_type=style,
                        plain=True,
                    )
                    for style in StyleType
                ],
            ),
            ft.Row(
                wrap=True,
                spacing=10,
                run_spacing=10,
                controls=[
                    Button(
                        tr("general.button.round"),
                        shape=ButtonShape.ROUND,
                        plain=True,
                    ),
                    Button(
                        tr("general.button.rect"),
                        shape=ButtonShape.RECTANGLE,
                        plain=True,
                    ),
                    Button(
                        tr("general.button.pill"),
                        shape=ButtonShape.CIRCLE,
                        plain=True,
                    ),
                    Button(tr("general.button.primary"), is_primary=True),
                    Button(tr("general.button.icon"), icon=ft.Icons.ADD),
                    Button(tr("general.button.disabled"), disabled=True),
                ],
            ),
        ],
    )

    icons = demo_card(
        title=tr("general.icon.title"),
        hint=tr("general.icon.hint"),
        icon=ft.Icons.EMOJI_EMOTIONS_OUTLINED,
        body=[
            ft.Row(
                spacing=16,
                wrap=True,
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.FAVORITE,
                        icon_color=ft.Colors.ERROR,
                        tooltip=tr("general.icon.love"),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE,
                        icon_color=MUTED,
                        tooltip=tr("general.icon.delete"),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.ADD_CIRCLE,
                        icon_color=ft.Colors.TERTIARY,
                        tooltip=tr("general.icon.add"),
                    ),
                    ft.FilledIconButton(icon=ft.Icons.MAIL, badge=ft.Badge(label="5")),
                    ft.FilledIconButton(
                        icon=ft.Icons.NOTIFICATIONS,
                        badge=ft.Badge(label="99+"),
                    ),
                    ft.Container(
                        padding=ft.Padding.symmetric(vertical=8, horizontal=14),
                        border_radius=8,
                        bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
                        border=ft.Border.all(1, BORDER),
                        content=ft.Text(
                            tr("general.icon.rich"),
                            size=13,
                            color=ft.Colors.PRIMARY,
                        ),
                        tooltip=ft.Tooltip(
                            message=tr("general.icon.rich_msg"),
                            padding=8,
                        ),
                    ),
                ],
            )
        ],
    )

    chips = demo_card(
        title=tr("general.chip.title"),
        hint=tr("general.chip.hint"),
        icon=ft.Icons.SELL_OUTLINED,
        body=[chip_single.ui(), chip_multi.ui()],
    )

    image_card = demo_card(
        title=tr("general.image.title"),
        hint=tr("general.image.hint"),
        icon=ft.Icons.IMAGE_OUTLINED,
        body=[
            ft.Row(
                spacing=12,
                controls=[
                    Image(
                        src=str(LOGO_FILE),
                        width=120,
                        height=90,
                        border_radius=8,
                        fit=ft.BoxFit.CONTAIN,
                    ),
                    ft.Column(
                        expand=True,
                        spacing=4,
                        controls=[
                            ft.Text(tr("general.image.top"), size=13),
                            Divider(color=BORDER),
                            ft.Text(tr("general.image.bottom"), size=13),
                            Divider(color=BORDER, leading_indent=40),
                            ft.Text(tr("general.image.indent"), size=12, color=MUTED),
                        ],
                    ),
                ],
            )
        ],
    )

    markdown_card = demo_card(
        title=tr("general.markdown.title"),
        hint=tr("general.markdown.hint"),
        icon=ft.Icons.CODE,
        stretch=True,
        body=[
            Markdown(
                "### Markdown\n"
                "\n"
                "- **Bold**, *italic*, `inline code`\n"
                "- Ordered / unordered lists\n"
                "- [Links](https://flet.dev) and fenced code\n"
                "\n"
                "```python\n"
                'print("hello, cs-ui")\n'
                "```\n"
            ),
            Json(value='{"name": "cs-ui", "version": "0.1.1", "flet": ">=1.0.5"}'),
        ],
    )

    return doc_page(
        "general",
        [
            ft.Column(
                spacing=18,
                controls=[
                    demo_grid(
                        cell(typography, span=6),
                        cell(buttons, span=6),
                        cell(icons, span=4),
                        cell(chips, span=4),
                        cell(image_card, span=4),
                        cell(markdown_card, span=12),
                    )
                ],
            ),
            code_block(_IMPORT_SNIPPET, filename="imports.py"),
        ],
    )
