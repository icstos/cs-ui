"""快速开始。"""

from __future__ import annotations

import flet as ft

from docs.content.snippets import (
    INSTALL_PIP,
    INSTALL_SOURCE,
    INSTALL_UV,
    PROJECT_TREE,
    QUICK_START,
    RUN_APP,
    RUN_WATCH,
)
from docs.kit import badge, bullets, callout, code_block, doc_page, section
from ui import use_t


@ft.component
def getting_started_page() -> ft.Control:
    tr = use_t()
    site = "site.getting_started"

    requirements = section(
        tr(f"{site}.requirements.title"),
        tr(f"{site}.requirements.desc"),
        callout(
            "info",
            tr(f"{site}.requirements.note"),
            title=tr(f"{site}.requirements.note_title"),
        ),
        bullets(
            [
                tr(f"{site}.requirements.python"),
                tr(f"{site}.requirements.flet"),
                tr(f"{site}.requirements.deps"),
                tr(f"{site}.requirements.os"),
            ]
        ),
    )

    install = section(
        tr(f"{site}.install.title"),
        tr(f"{site}.install.desc"),
        ft.Text(tr(f"{site}.install.pip"), size=13, weight=ft.FontWeight.W_600),
        code_block(INSTALL_PIP, language="bash", filename="pip"),
        ft.Text(tr(f"{site}.install.uv"), size=13, weight=ft.FontWeight.W_600),
        code_block(INSTALL_UV, language="bash", filename="uv"),
        ft.Text(tr(f"{site}.install.source"), size=13, weight=ft.FontWeight.W_600),
        code_block(INSTALL_SOURCE, language="bash", filename="git"),
    )

    quick_start = section(
        tr(f"{site}.quickstart.title"),
        tr(f"{site}.quickstart.desc"),
        code_block(QUICK_START, filename="main.py", height=470),
    )

    run = section(
        tr(f"{site}.run.title"),
        tr(f"{site}.run.desc"),
        code_block(RUN_APP, language="bash", filename="run"),
        code_block(RUN_WATCH, language="bash", filename="watch"),
    )

    project = section(
        tr(f"{site}.project.title"),
        tr(f"{site}.project.desc"),
        code_block(PROJECT_TREE, language="text", filename="tree"),
    )

    return doc_page(
        "getting_started",
        [
            requirements,
            install,
            quick_start,
            run,
            project,
            callout(
                "success",
                tr(f"{site}.next.desc"),
                title=tr(f"{site}.next.title"),
            ),
        ],
        badges=[
            badge("Python 3.12+"),
            badge("Flet 1.0.5"),
            badge("MIT", role="success"),
        ],
    )
