"""数据展示组件演示。"""

from __future__ import annotations

import asyncio

import flet as ft

from docs.demos._helpers import BORDER, LOGO_FILE, panel, use_stable
from docs.kit import cell, demo_card, demo_grid, doc_page
from ui import (
    Button,
    CodeEditor,
    CodeView,
    Divider,
    ImageGridView,
    ListTile,
    LogContainer,
    use_t,
)


@ft.component
def display_page() -> ft.Control:
    tr = use_t()
    page = ft.context.page

    logs = use_stable(
        lambda: LogContainer(
            logs=[
                tr("display.log.boot"),
                tr("display.log.db"),
                tr("display.log.theme"),
                tr("display.log.cache"),
            ],
            height=180,
        )
    )

    def push_logs(_: ft.Event[Button]) -> None:
        async def run() -> None:
            await logs.add(tr("display.log.sync_start"))
            await asyncio.sleep(0.25)
            await logs.add(tr("display.log.sync_done"))
            await asyncio.sleep(0.25)
            await logs.add(tr("display.log.sync_skip"))

        page.run_task(run)

    gallery = use_stable(
        lambda: ImageGridView(
            title=tr("display.gallery.grid_title"),
            img_file_paths=[str(LOGO_FILE) for _ in range(23)],
            num_item_per_page=6,
            img_size=120,
            grid_height=300,
        )
    )

    tiles = demo_card(
        title=tr("display.listtile.title"),
        hint=tr("display.listtile.hint"),
        icon=ft.Icons.VIEW_AGENDA_OUTLINED,
        stretch=True,
        body=[
            panel(
                ListTile(
                    title=tr("display.listtile.users"),
                    subtitle=tr("display.listtile.users_sub"),
                    leading=ft.Icon(ft.Icons.PEOPLE_OUTLINE, color=ft.Colors.PRIMARY),
                    trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT),
                ),
                Divider(height=1, color=BORDER),
                ListTile(
                    title=tr("display.listtile.settings"),
                    subtitle=tr("display.listtile.settings_sub"),
                    leading=ft.Icon(
                        ft.Icons.SETTINGS_OUTLINED, color=ft.Colors.TERTIARY
                    ),
                    trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT),
                ),
                Divider(height=1, color=BORDER),
                ListTile(
                    title=tr("display.listtile.logs"),
                    subtitle=tr("display.listtile.logs_sub"),
                    leading=ft.Icon(ft.Icons.HISTORY, color=ft.Colors.SECONDARY),
                    trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT),
                ),
            )
        ],
    )

    log_card = demo_card(
        title=tr("display.log.title"),
        hint=tr("display.log.hint"),
        icon=ft.Icons.TERMINAL,
        stretch=True,
        body=[
            logs.ui(),
            ft.Row(
                spacing=10,
                controls=[
                    Button(tr("display.log.append"), on_click=push_logs),
                    Button(tr("display.log.clear"), on_click=lambda _: logs.clear()),
                ],
            ),
        ],
    )

    code_card = demo_card(
        title=tr("display.code.title"),
        hint=tr("display.code.hint"),
        icon=ft.Icons.CODE,
        stretch=True,
        body=[
            CodeEditor(
                value="def add(a: int, b: int) -> int:\n    return a + b\n",
                language="python",
                height=140,
            ),
            CodeView(
                code=(
                    f'Button("{tr("display.code.run")}", '
                    "is_primary=True)"
                ),
                component=Button(tr("display.code.run"), is_primary=True),
            ),
        ],
    )

    gallery_card = demo_card(
        title=tr("display.gallery.title"),
        hint=tr("display.gallery.hint"),
        icon=ft.Icons.PHOTO_LIBRARY_OUTLINED,
        stretch=True,
        body=[gallery.ui()],
    )

    return doc_page(
        "display",
        [
            demo_grid(
                cell(tiles, span=6),
                cell(log_card, span=6),
                cell(code_card, span=12),
                cell(gallery_card, span=12),
            )
        ],
    )
