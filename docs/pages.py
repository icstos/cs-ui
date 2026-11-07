"""页面组件：文档页、分类页、组件页与 404。

三种页面共用同一个外壳（页头 + 正文 + 上下页 + 页脚），差别只在"正文是什么"：

* ``page`` —— 内容块（``docs.blocks``），用于快速开始 / 架构 / 主题这类文章；
* ``category`` —— 该分类下全部组件的卡片墙；
* ``component`` —— 实现文件里那份 ``SPEC`` 渲染成的完整说明（定义、构成、
  何时使用、示例、API、备注）与实现文件**同源**。
"""

from __future__ import annotations

from collections.abc import Sequence

import flet as ft

from docs import kit, search
from docs.content import DOCS
from docs.render import BlocksView
from docs.shell import page_header, register_scroller, site_footer, step_nav
from docs.site import COMPONENT_COUNTS, PAGES, PageMeta, group_entries
from ui import Button, use_t
from ui.core import catalog
from ui.core import doc as doc_kit


@ft.component
def _frame(
    meta: PageMeta,
    body: Sequence[ft.Control],
    *,
    badges: Sequence[ft.Control] = (),
    trail: Sequence[tuple[str, str]] = (),
    desc: str | None = None,
) -> ft.Control:
    """统一外壳：滚动容器 + 页头 + 正文 + 上下页 + 页脚。"""
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
                        page_header(meta, badges=badges, trail=trail, desc=desc),
                        *body,
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
def DocView(page_key: str) -> ft.Control:
    """按页面类型分发 —— 路由表只认这一个入口。"""
    meta = PAGES[page_key]
    if meta.kind == "component":
        return ComponentView(meta)
    if meta.kind == "category":
        return CategoryView(meta)
    return _article(meta)


@ft.component
def _article(meta: PageMeta) -> ft.Control:
    """文章页：内容块全部来自 ``DOCS``（纯数据，换皮不用改内容）。"""
    tr = use_t()
    badges: list[ft.Control] = []
    if meta.key in COMPONENT_COUNTS:
        badges.append(
            kit.badge(
                tr("comp.count", n=COMPONENT_COUNTS[meta.key]),
                tone="primary",
                icon=ft.Icons.WIDGETS_OUTLINED,
            )
        )
    return _frame(meta, [BlocksView(DOCS[meta.key])], badges=badges)


# ---------------------------------------------------------------------------
# 组件页
# ---------------------------------------------------------------------------
@ft.component
def _run_hint(spec: doc_kit.Spec) -> ft.Control:
    """「在独立窗口里打开」—— 把要求 1 与要求 2 连起来的那一行。

    每个组件都能单独跑起来看：这一行给出准确的命令，省掉读者去猜模块路径。
    """
    tr = use_t()
    command = f"python {spec.source}" if spec.source else ""
    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=14, vertical=10),
        border_radius=10,
        bgcolor=kit.RAISED,
        border=ft.Border.all(1, kit.BORDER),
        content=ft.Row(
            spacing=9,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(ft.Icons.TERMINAL, size=15, color=kit.MUTED),
                ft.Text(tr("comp.run"), size=12, color=kit.MUTED),
                ft.Container(
                    expand=True,
                    content=ft.Text(
                        command,
                        size=12,
                        color=ft.Colors.ON_SURFACE,
                        selectable=True,
                        no_wrap=True,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                ),
                ft.IconButton(
                    icon=ft.Icons.CONTENT_COPY,
                    icon_size=14,
                    icon_color=kit.MUTED,
                    tooltip=tr("site.copy"),
                    action=ft.CopyToClipboard(command),
                ),
            ],
        ),
    )


@ft.component
def ComponentView(meta: PageMeta) -> ft.Control:
    """组件页：内容就是实现文件里那份 ``SPEC``。"""
    tr = use_t()
    spec = catalog.load(meta.key)

    badges: list[ft.Control] = [
        kit.badge(
            tr(f"nav.{meta.parent}.title"),
            tone="primary",
            icon=ft.Icons.FOLDER_OUTLINED,
        )
    ]
    if spec.examples:
        badges.append(
            kit.badge(
                tr("comp.examples", n=len(spec.examples)),
                tone="info",
                icon=ft.Icons.PLAY_CIRCLE_OUTLINE,
            )
        )
    if spec.since:
        badges.append(kit.badge(f"v{spec.since}", tone="neutral"))

    body: list[ft.Control] = [
        ft.Column(
            spacing=28,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=doc_kit.sections(spec),
        ),
        _run_hint(spec),
    ]

    return _frame(
        meta,
        body,
        badges=badges,
        trail=[(tr(f"nav.{meta.parent}.title"), f"/components/{meta.parent}")],
        desc=spec.summary,
    )


# ---------------------------------------------------------------------------
# 分类页
# ---------------------------------------------------------------------------
@ft.component
def _component_card(meta: PageMeta) -> ft.Control:
    page = ft.context.page
    spec = catalog.load(meta.key)
    return ft.Container(
        col={"xs": 12, "md": 6},
        content=kit.hover_card(
            on_click=lambda _e: page.navigate(meta.route),
            padding=16,
            content=ft.Column(
                spacing=7,
                controls=[
                    ft.Row(
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text(
                                meta.name,
                                size=14.5,
                                weight=ft.FontWeight.W_700,
                                expand=True,
                                no_wrap=True,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            ft.Icon(
                                ft.Icons.ARROW_FORWARD,
                                size=14,
                                color=ft.Colors.PRIMARY,
                            ),
                        ],
                    ),
                    ft.Text(
                        spec.summary,
                        size=12,
                        color=kit.MUTED,
                        style=ft.TextStyle(height=1.6),
                        max_lines=3,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                ],
            ),
        ),
    )


@ft.component
def CategoryView(meta: PageMeta) -> ft.Control:
    """分类页：本组组件的卡片墙，点进去就是该组件的完整说明。"""
    tr = use_t()
    entries = group_entries(meta.key)
    badges = [
        kit.badge(
            tr("comp.count", n=len(entries)),
            tone="primary",
            icon=ft.Icons.WIDGETS_OUTLINED,
        )
    ]
    body: list[ft.Control] = [
        ft.ResponsiveRow(
            columns=12,
            spacing=12,
            run_spacing=12,
            controls=[_component_card(item) for item in entries],
        )
    ]
    return _frame(meta, body, badges=badges)


# ---------------------------------------------------------------------------
# 404
# ---------------------------------------------------------------------------
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


__all__ = ["CategoryView", "ComponentView", "DocView", "not_found_page"]
