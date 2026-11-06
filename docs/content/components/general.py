"""通用组件：文本、按钮、图标、标签、代码与 Markdown。"""

from __future__ import annotations

import flet as ft

from docs import kit
from docs.blocks import Doc, demo, h2, note, p, ul
from docs.content.components._shared import panel, row_of
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
    Json,
    Link,
    Markdown,
    Quote,
    StyleType,
    Text,
    use_t,
)

_BUTTON_CODE = '''Button("Save", is_primary=True)
Button("Cancel", plain=True)
Button("Export", icon=ft.Icons.DOWNLOAD, style_type=StyleType.INFO)
Button("Round", shape=ButtonShape.CIRCLE)'''

_CHIP_CODE = '''Chip(label="Tags", options=["A", "B", "C"])
Chip(label="Stack", options=["Python", "Flet"], multi_select=True)'''


@ft.component
def _typography() -> ft.Control:
    tr = use_t()
    return Column(
        spacing=6,
        controls=[
            Header_1("Header_1"),
            Header_2("Header_2"),
            Header_3("Header_3"),
            Header_4("Header_4"),
            Header_5("Header_5"),
            ft.Container(height=4),
            Text(tr("cat.general.typo.body"), size=14),
            Quote(tr("cat.general.typo.quote"), size=13.5),
            Link(tr("cat.general.typo.link"), link="https://flet.dev"),
        ],
    )


@ft.component
def _buttons() -> ft.Control:
    return Column(
        spacing=14,
        controls=[
            row_of([Button(style.name, style_type=style) for style in StyleType]),
            row_of(
                [
                    Button(f"{style.name} · plain", style_type=style, plain=True)
                    for style in (
                        StyleType.DEFAULT,
                        StyleType.PRIMARY,
                        StyleType.INFO,
                    )
                ]
            ),
            row_of(
                [
                    Button("Circle", shape=ButtonShape.CIRCLE, plain=True),
                    Button("Rect", shape=ButtonShape.RECTANGLE, plain=True),
                    Button("Pill", shape=ButtonShape.ROUND, plain=True),
                    Button("Icon", icon=ft.Icons.ADD),
                    Button("Disabled", disabled=True),
                ]
            ),
        ],
    )


@ft.component
def _chips() -> ft.Control:
    tr = use_t()
    single = kit.use_stable(
        lambda: Chip(
            label=tr("cat.general.chip.single"),
            options=tr.list("demo.options"),
        )
    )
    multi = kit.use_stable(
        lambda: Chip(
            label=tr("cat.general.chip.multi"),
            options=tr.list("demo.stack"),
            multi_select=True,
            selected_values=tr.list("demo.stack")[:2],
        )
    )
    return Column(spacing=14, controls=[single.ui(), multi.ui()])


@ft.component
def _icons() -> ft.Control:
    tr = use_t()
    return ft.Row(
        spacing=14,
        wrap=True,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.IconButton(
                icon=ft.Icons.FAVORITE,
                icon_color=ft.Colors.ERROR,
                tooltip=tr("cat.general.icon.love"),
            ),
            ft.IconButton(
                icon=ft.Icons.DELETE_OUTLINE,
                icon_color=kit.MUTED,
                tooltip=tr("cat.general.icon.delete"),
            ),
            ft.FilledIconButton(icon=ft.Icons.MAIL_OUTLINE, badge=ft.Badge(label="5")),
            ft.FilledIconButton(
                icon=ft.Icons.NOTIFICATIONS_OUTLINED, badge=ft.Badge(label="99+")
            ),
            ft.Container(
                padding=ft.Padding.symmetric(horizontal=12, vertical=7),
                border_radius=9,
                bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
                border=ft.Border.all(1, kit.BORDER),
                content=ft.Row(
                    spacing=7,
                    controls=[
                        ft.Icon(ft.Icons.INFO_OUTLINE, size=15, color=ft.Colors.PRIMARY),
                        ft.Text(
                            tr("cat.general.icon.rich"),
                            size=12.5,
                            color=ft.Colors.PRIMARY,
                        ),
                    ],
                ),
                tooltip=ft.Tooltip(message=tr("cat.general.icon.rich_tip"), padding=8),
            ),
        ],
    )


@ft.component
def _markdown() -> ft.Control:
    return panel(
        Markdown(
            "#### Markdown\n"
            "\n"
            "- **Bold**, *italic*, `inline code`\n"
            "- Ordered and unordered lists\n"
            "- [Links](https://flet.dev) and fenced code\n"
            "\n"
            "```python\n"
            'print("hello, cs-ui")\n'
            "```\n"
        ),
        Divider(color=kit.BORDER),
        Json(value='{"name": "cs-ui", "flet": "1.1.0", "python": ">=3.12"}'),
    )


GENERAL: Doc = (
    p("cat.general.intro"),
    h2("cat.general.type.title"),
    demo(_typography, hint_key="cat.general.type.hint"),
    h2("cat.general.button.title"),
    demo(_buttons, hint_key="cat.general.button.hint", code=_BUTTON_CODE),
    h2("cat.general.chip.title"),
    demo(_chips, hint_key="cat.general.chip.hint", code=_CHIP_CODE),
    h2("cat.general.icon.title"),
    demo(_icons, hint_key="cat.general.icon.hint"),
    h2("cat.general.md.title"),
    demo(_markdown, hint_key="cat.general.md.hint"),
    ul("cat.general.note1", "cat.general.note2", "cat.general.note3"),
    note("cat.general.tip", "cat.general.tip_title"),
)
