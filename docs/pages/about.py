"""关于 cs-ui。"""

from __future__ import annotations

import flet as ft

from docs.content.snippets import RUN_DOCS, SMOKE_DOCS
from docs.kit import (
    bullets,
    cell,
    code_block,
    demo_card,
    demo_grid,
    doc_page,
    section,
    stat_card,
)
from docs.site import (
    FLET_URL,
    FLET_VERSION,
    GITHUB_URL,
    PACKAGE_VERSION,
    PYTHON_VERSION,
)
from ui import Button, Markdown, use_t

_MIGRATION_TABLE = (
    "| Legacy (0.x) | Current (1.x) |\n"
    "| --- | --- |\n"
    "| `ft.app(main)` | `ft.run(main)` |\n"
    "| `page.add(...)` | `page.render(Component)` |\n"
    "| `page.views.append(...)` | `ft.Router(ROUTES, manage_views=False)` + `page.render` |\n"
    "| `page.go(route)` | `page.navigate(route)` |\n"
    "| `page.overlay.append(dlg)` | `page.show_dialog(dlg)` |\n"
    "| `ft.View(appbar=...)` | `Container` + custom top bar |\n"
    "| `TextField(border_radius=...)` | `TextField(border=ft.OutlineInputBorder(...))` |\n"
    "| `Tooltip(content=...)` | `control.tooltip = ft.Tooltip(message=...)` |\n"
    "| `Badge(badge_value=...)` | `Badge(label=...)` |\n"
)


@ft.component
def about_page() -> ft.Control:
    tr = use_t()

    runtime = demo_grid(
        cell(
            stat_card(
                value=PACKAGE_VERSION,
                label=tr("site.about.runtime.version"),
                icon=ft.Icons.LOCAL_OFFER_OUTLINED,
            ),
            span=3,
        ),
        cell(
            stat_card(
                value=FLET_VERSION,
                label=tr("site.about.runtime.flet"),
                icon=ft.Icons.LAYERS_OUTLINED,
                color=ft.Colors.TERTIARY,
            ),
            span=3,
        ),
        cell(
            stat_card(
                value=PYTHON_VERSION,
                label=tr("site.about.runtime.python"),
                icon=ft.Icons.CODE,
                color=ft.Colors.SECONDARY,
            ),
            span=3,
        ),
        cell(
            stat_card(
                value="MIT",
                label=tr("site.about.runtime.license"),
                icon=ft.Icons.GAVEL,
                color=ft.Colors.ERROR,
            ),
            span=3,
        ),
    )

    principles = section(
        tr("about.design.title"),
        tr("about.design.hint"),
        bullets([tr(f"about.design.p{index}") for index in range(1, 5)]),
    )

    i18n = section(
        tr("about.i18n.title"),
        tr("about.i18n.hint"),
        bullets([tr(f"about.i18n.p{index}") for index in range(1, 5)]),
    )

    migration = demo_card(
        title=tr("about.migration.title"),
        hint=tr("about.migration.hint"),
        icon=ft.Icons.SWAP_HORIZ,
        stretch=True,
        body=[Markdown(_MIGRATION_TABLE)],
    )

    run = section(
        tr("about.run.title"),
        tr("about.run.hint"),
        code_block(RUN_DOCS, language="bash", filename="run"),
        code_block(SMOKE_DOCS, language="bash", filename="smoke"),
    )

    links = demo_card(
        title=tr("site.about.links.title"),
        hint=tr("site.about.links.hint"),
        icon=ft.Icons.LINK,
        body=[
            ft.Row(
                spacing=10,
                wrap=True,
                run_spacing=10,
                controls=[
                    Button(
                        tr("site.about.links.github"),
                        icon=ft.Icons.HUB,
                        action=ft.OpenUrl(GITHUB_URL, target=ft.UrlTarget.BLANK),
                    ),
                    Button(
                        tr("site.about.links.flet"),
                        icon=ft.Icons.OPEN_IN_NEW,
                        action=ft.OpenUrl(FLET_URL, target=ft.UrlTarget.BLANK),
                    ),
                ],
            )
        ],
    )

    return doc_page(
        "about",
        [
            runtime,
            principles,
            i18n,
            migration,
            run,
            links,
        ],
    )
