"""页面组件：通用文档页与 404。"""

from __future__ import annotations

import flet as ft

from docs import kit, search
from docs.content import DOCS
from docs.render import BlocksView
from docs.shell import page_header, register_scroller, site_footer, step_nav
from docs.site import COMPONENT_COUNTS, PAGES
from ui import Button, use_t


@ft.component
def DocView(page_key: str) -> ft.Control:
    """一页文档：页头 + 内容块 + 上下页 + 页脚。

    所有文档页共用这一个组件 —— 差异全在 ``DOCS[page_key]`` 的数据里。
    """
    tr = use_t()
    meta = PAGES[page_key]
    blocks = DOCS[page_key]

    badges: list[ft.Control] = []
    if page_key in COMPONENT_COUNTS:
        badges.append(
            kit.badge(
                tr("comp.count", n=COMPONENT_COUNTS[page_key]),
                tone="primary",
                icon=ft.Icons.WIDGETS_OUTLINED,
            )
        )

    scroller = ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        spacing=0,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        controls=[
            ft.Container(
                padding=ft.Padding.only(left=44, right=44, top=26, bottom=34),
                content=ft.Column(
                    spacing=26,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                    controls=[
                        page_header(meta, badges=badges),
                        BlocksView(blocks),
                        step_nav(meta),
                        site_footer(),
                    ],
                ),
            )
        ],
    )
    register_scroller(scroller)
    return ft.Container(expand=True, bgcolor=kit.PAGE_BG, content=scroller)


@ft.component
def not_found_page() -> ft.Control:
    tr = use_t()
    page = ft.context.page
    return ft.Container(
        expand=True,
        bgcolor=kit.PAGE_BG,
        alignment=ft.Alignment.CENTER,
        content=ft.Column(
            spacing=14,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(
                    "404",
                    size=64,
                    weight=ft.FontWeight.W_800,
                    color=ft.Colors.with_opacity(0.16, ft.Colors.PRIMARY),
                    style=ft.TextStyle(letter_spacing=-2),
                ),
                ft.Text(tr("site.notfound.title"), size=20, weight=ft.FontWeight.W_700),
                ft.Text(
                    tr("site.notfound.desc"),
                    size=13.5,
                    color=kit.MUTED,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Row(
                    spacing=10,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        Button(
                            tr("site.notfound.home"),
                            is_primary=True,
                            icon=ft.Icons.HOME_OUTLINED,
                            on_click=lambda _e: page.navigate("/"),
                        ),
                        Button(
                            tr("site.notfound.search"),
                            icon=ft.Icons.SEARCH,
                            on_click=lambda _e: search.open_search(),
                        ),
                    ],
                ),
            ],
        ),
    )


__all__ = ["DocView", "not_found_page"]
