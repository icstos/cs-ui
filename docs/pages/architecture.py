"""架构指南。"""

from __future__ import annotations

import flet as ft

from docs.content.snippets import (
    COMPONENT_STATE,
    DUAL_PARADIGM,
    PROVIDERS,
    ROUTER,
)
from docs.kit import bullets, callout, code_block, doc_page, section
from ui import use_t


@ft.component
def architecture_page() -> ft.Control:
    tr = use_t()
    site = "site.architecture"

    layers = section(
        tr(f"{site}.overview.title"),
        tr(f"{site}.overview.desc"),
        bullets(tr.list(f"{site}.overview.points")),
    )

    paradigm = section(
        tr(f"{site}.paradigm.title"),
        tr(f"{site}.paradigm.desc"),
        code_block(DUAL_PARADIGM, filename="components.py"),
        code_block(COMPONENT_STATE, filename="form.py"),
        callout(
            "warning",
            tr(f"{site}.paradigm.note"),
            title=tr(f"{site}.paradigm.note_title"),
        ),
    )

    providers = section(
        tr(f"{site}.providers.title"),
        tr(f"{site}.providers.desc"),
        code_block(PROVIDERS, filename="app.py", height=300),
    )

    routing = section(
        tr(f"{site}.routing.title"),
        tr(f"{site}.routing.desc"),
        code_block(ROUTER, filename="routes.py", height=300),
        callout(
            "danger",
            tr(f"{site}.routing.note"),
            title=tr(f"{site}.routing.note_title"),
        ),
    )

    state = section(
        tr(f"{site}.state.title"),
        tr(f"{site}.state.desc"),
        bullets(tr.list(f"{site}.state.points")),
    )

    performance = section(
        tr(f"{site}.performance.title"),
        tr(f"{site}.performance.desc"),
        bullets(tr.list(f"{site}.performance.points")),
    )

    return doc_page(
        "architecture",
        [layers, paradigm, providers, routing, state, performance],
    )
