"""命令面板：一处输入框，搜遍页面与组件。

做成浮层而不是独立页面 —— 桌面端"按一下就出来、选完就消失"更符合直觉，
也省掉一次路由往返。
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

import flet as ft

from docs import kit
from docs.site import Hit, build_index
from ui import use_t

_PANEL_WIDTH = 560

#: 由外壳登记"打开面板"的方法，页面就不用知道面板挂在哪一层。
_open: Callable[[], None] | None = None


def bind(opener: Callable[[], None]) -> None:
    """登记打开命令面板的方法（外壳渲染时调用一次）。"""
    global _open
    _open = opener


def open_search() -> None:
    """打开命令面板。没有外壳时静默忽略。"""
    if _open is not None:
        _open()


def _matches(hits: Sequence[Hit], query: str) -> list[Hit]:
    """空格分词的 AND 匹配：``date input`` 也能命中 ``DateInput``。"""
    terms = [term for term in query.lower().split() if term]
    if not terms:
        return list(hits)
    return [
        hit
        for hit in hits
        if all(term in f"{hit.title} {hit.detail}".lower() for term in terms)
    ]


@ft.component
def SearchPalette(*, on_close: Callable[[], None]) -> ft.Control:
    tr = use_t()
    page = ft.context.page
    query, set_query = ft.use_state("")
    hits = ft.use_memo(lambda: build_index(tr), [tr.locale])
    found = _matches(hits, query)

    def select(route: str) -> None:
        on_close()
        page.navigate(route)

    def submit(_event: ft.Event[ft.TextField]) -> None:
        if found:
            select(found[0].route)

    rows: list[ft.Control] = []
    for hit in found[:12]:
        rows.append(
            ft.Container(
                padding=ft.Padding.symmetric(horizontal=12, vertical=9),
                border_radius=9,
                on_click=lambda _e, route=hit.route: select(route),
                ink=True,
                content=ft.Row(
                    spacing=11,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        kit.icon_tile(hit.icon, tone="primary", size=30, icon_size=15),
                        ft.Text(hit.title, size=13.5, weight=ft.FontWeight.W_500),
                        ft.Container(expand=True),
                        ft.Text(
                            tr(hit.category),
                            size=11,
                            color=kit.MUTED,
                        ),
                    ],
                ),
            )
        )

    if not rows:
        rows.append(
            ft.Container(
                padding=ft.Padding.symmetric(horizontal=12, vertical=22),
                content=ft.Column(
                    spacing=4,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(ft.Icons.SEARCH_OFF, size=22, color=kit.MUTED),
                        ft.Text(
                            tr("site.search.empty", query=query),
                            size=12.5,
                            color=kit.MUTED,
                        ),
                    ],
                ),
            )
        )

    card = ft.Container(
        width=_PANEL_WIDTH,
        border_radius=16,
        bgcolor=kit.SURFACE,
        border=ft.Border.all(1, kit.BORDER),
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        shadow=ft.BoxShadow(
            blur_radius=44,
            spread_radius=-10,
            color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK),
            offset=ft.Offset(0, 18),
        ),
        content=ft.Column(
            spacing=0,
            controls=[
                ft.Container(
                    padding=ft.Padding.only(left=14, right=8, top=8, bottom=8),
                    border=ft.Border(bottom=ft.BorderSide(1, kit.BORDER)),
                    content=ft.Row(
                        spacing=6,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.TextField(
                                autofocus=True,
                                value=query,
                                hint_text=tr("site.search.placeholder"),
                                border=ft.InputBorder.NONE,
                                dense=True,
                                text_size=14,
                                prefix_icon=ft.Icons.SEARCH,
                                content_padding=ft.Padding.symmetric(vertical=10),
                                expand=True,
                                on_change=lambda e: set_query(e.control.value),
                                on_submit=submit,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                icon_size=16,
                                icon_color=kit.MUTED,
                                tooltip=tr("site.search.close"),
                                on_click=lambda _e: on_close(),
                            ),
                        ],
                    ),
                ),
                ft.Container(
                    padding=ft.Padding.all(6),
                    height=min(384, 46 * len(rows) + 12),
                    content=ft.Column(
                        spacing=0,
                        scroll=ft.ScrollMode.AUTO,
                        controls=rows,
                    ),
                ),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=14, vertical=7),
                    bgcolor=kit.RAISED,
                    border=ft.Border(top=ft.BorderSide(1, kit.BORDER)),
                    content=ft.Row(
                        spacing=10,
                        controls=[
                            kit.kbd("Enter"),
                            ft.Text(
                                tr("site.search.enter"), size=10.5, color=kit.MUTED
                            ),
                            ft.Container(expand=True),
                            ft.Text(
                                tr("site.search.count", n=len(found)),
                                size=10.5,
                                color=kit.MUTED,
                            ),
                        ],
                    ),
                ),
            ],
        ),
    )

    # 遮罩与面板做兄弟节点：点遮罩关闭，点面板不会传下去。
    return ft.Stack(
        expand=True,
        controls=[
            ft.Container(
                left=0,
                top=0,
                right=0,
                bottom=0,
                bgcolor=ft.Colors.with_opacity(0.42, ft.Colors.BLACK),
                on_click=lambda _e: on_close(),
            ),
            ft.Container(
                left=0,
                right=0,
                top=76,
                alignment=ft.Alignment.TOP_CENTER,
                content=card,
            ),
        ],
    )


__all__ = ["SearchPalette", "bind", "open_search"]
