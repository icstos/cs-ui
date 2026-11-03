"""站点外壳：顶栏、侧边栏、本页目录、页脚与整体布局。

外壳只认 :mod:`docs.site` 的数据与 :mod:`docs.kit` 的视觉件，不认具体页面；
页面通过 :func:`site_layout` 的 ``outlet`` 进来。
"""

from __future__ import annotations

from collections.abc import Sequence

import flet as ft

from docs import kit
from docs import search as search_api
from docs.render import outline
from docs.search import SearchPalette
from docs.site import (
    DOCS_ROOT,
    FLET_VERSION,
    GITHUB_URL,
    LOGO_FILE,
    NAV_GROUPS,
    PACKAGE_VERSION,
    PYTHON_VERSION,
    PageMeta,
    page_after,
    page_before,
    page_for_route,
)
from ui import LanguageSwitcher, use_t
from ui.core.theme import use_theme

TOPBAR_HEIGHT = 60
SIDEBAR_WIDTH = 252
OUTLINE_WIDTH = 196

_MUTED = kit.MUTED
_BORDER = kit.BORDER

_CRUMB: dict[str, tuple[str, str]] = {
    "start": ("site.crumb.docs", "/docs/quickstart"),
    "guide": ("site.crumb.docs", "/docs/quickstart"),
    "components": ("site.crumb.components", "/components"),
    "project": ("site.crumb.docs", "/docs/quickstart"),
}


# ---------------------------------------------------------------------------
# 本页滚动：目录点击 → 平滑滚到锚点
# ---------------------------------------------------------------------------


class _Scroller:
    """当前文档页的滚动容器。

    目录与正文是两棵独立的控件树，靠模块级引用连接，比在控件树里逐层找
    scrollable 祖先更稳也更快。
    """

    control: ft.Column | None = None

    @classmethod
    def register(cls, control: ft.Column) -> None:
        cls.control = control

    @classmethod
    async def jump(cls, anchor: str) -> None:
        if cls.control is not None:
            await cls.control.scroll_to(scroll_key=anchor, duration=280)


def register_scroller(control: ft.Column) -> None:
    """由文档页在渲染时登记滚动容器。"""
    _Scroller.register(control)


# ---------------------------------------------------------------------------
# 顶栏
# ---------------------------------------------------------------------------


@ft.component
def _nav_item(label: str, route: str, *, active: bool) -> ft.Control:
    page = ft.context.page
    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=11, vertical=5),
        border_radius=8,
        bgcolor=kit.RAISED if active else None,
        on_click=lambda _e: page.navigate(route),
        ink=True,
        content=ft.Text(
            label,
            size=13,
            weight=ft.FontWeight.W_600 if active else ft.FontWeight.W_400,
            color=ft.Colors.ON_SURFACE if active else _MUTED,
        ),
    )


@ft.component
def _search_trigger(*, on_click) -> ft.Control:
    tr = use_t()
    return ft.Container(
        width=206,
        height=32,
        padding=ft.Padding.symmetric(horizontal=9),
        border_radius=9,
        bgcolor=kit.RAISED,
        border=ft.Border.all(1, _BORDER),
        ink=True,
        tooltip=tr("site.search.tooltip"),
        on_click=on_click,
        content=ft.Row(
            spacing=7,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(ft.Icons.SEARCH, size=15, color=_MUTED),
                ft.Text(tr("site.search.placeholder"), size=12, color=_MUTED),
            ],
        ),
    )


@ft.component
def _theme_button() -> ft.Control:
    theme = use_theme()
    tr = use_t()
    dark = theme.is_dark
    return ft.IconButton(
        icon=ft.Icons.LIGHT_MODE_OUTLINED if dark else ft.Icons.DARK_MODE_OUTLINED,
        icon_color=_MUTED,
        icon_size=19,
        tooltip=tr("site.theme.to_light") if dark else tr("site.theme.to_dark"),
        on_click=lambda _e: theme.toggle_mode(),
    )


@ft.component
def _github_link() -> ft.Control:
    """顶栏源码入口：Material 图标集没有品牌图标，改用描边胶囊 + 代码图标。"""
    tr = use_t()
    return ft.Container(
        height=30,
        padding=ft.Padding.symmetric(horizontal=10),
        border_radius=8,
        border=ft.Border.all(1, _BORDER),
        ink=True,
        tooltip=tr("site.github"),
        action=ft.OpenUrl(GITHUB_URL, target=ft.UrlTarget.BLANK),
        content=ft.Row(
            spacing=6,
            tight=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(ft.Icons.CODE, size=15, color=_MUTED),
                ft.Text(
                    "GitHub",
                    size=12.5,
                    weight=ft.FontWeight.W_600,
                    color=_MUTED,
                ),
            ],
        ),
    )


@ft.component
def top_bar(*, on_search) -> ft.Control:
    tr = use_t()
    location = ft.use_route_location()
    page = ft.context.page

    brand = ft.Container(
        on_click=lambda _e: page.navigate("/"),
        ink=True,
        border_radius=8,
        padding=ft.Padding.symmetric(horizontal=4, vertical=4),
        content=ft.Row(
            spacing=9,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Image(
                    src=str(LOGO_FILE), width=24, height=24, fit=ft.BoxFit.CONTAIN
                ),
                ft.Text("cs-ui", size=15.5, weight=ft.FontWeight.W_800),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=7, vertical=1),
                    border_radius=999,
                    border=ft.Border.all(1, _BORDER),
                    content=ft.Text(
                        f"v{PACKAGE_VERSION}",
                        size=10,
                        color=_MUTED,
                        weight=ft.FontWeight.W_600,
                    ),
                ),
            ],
        ),
    )

    return ft.Container(
        height=TOPBAR_HEIGHT,
        padding=ft.Padding.symmetric(horizontal=18),
        bgcolor=ft.Colors.SURFACE,
        border=ft.Border(bottom=ft.BorderSide(1, _BORDER)),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(
                    spacing=22,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        brand,
                        ft.Row(
                            spacing=2,
                            controls=[
                                _nav_item(
                                    tr("site.tab.docs"),
                                    "/docs/quickstart",
                                    active=location.startswith("/docs"),
                                ),
                                _nav_item(
                                    tr("site.tab.components"),
                                    "/components",
                                    active=location.startswith("/components"),
                                ),
                                _nav_item(
                                    tr("site.tab.about"),
                                    "/about",
                                    active=location.startswith("/about"),
                                ),
                            ],
                        ),
                    ],
                ),
                ft.Row(
                    spacing=2,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        _search_trigger(on_click=on_search),
                        ft.Container(width=4),
                        LanguageSwitcher(compact=True),
                        _theme_button(),
                        _github_link(),
                    ],
                ),
            ],
        ),
    )


# ---------------------------------------------------------------------------
# 侧边栏
# ---------------------------------------------------------------------------


def _is_active(location: str, route: str) -> bool:
    if route == "/":
        return location in ("", "/")
    return location.rstrip("/") == route.rstrip("/")


@ft.component
def _side_item(meta: PageMeta, *, active: bool) -> ft.Control:
    tr = use_t()
    page = ft.context.page
    foreground = ft.Colors.ON_PRIMARY_CONTAINER if active else _MUTED
    return ft.Container(
        height=31,
        padding=ft.Padding.symmetric(horizontal=9),
        border_radius=8,
        bgcolor=ft.Colors.PRIMARY_CONTAINER if active else None,
        on_click=lambda _e: page.navigate(meta.route),
        ink=True,
        content=ft.Row(
            spacing=9,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(meta.icon, size=16, color=foreground),
                ft.Text(
                    tr(meta.title_key),
                    size=12.5,
                    color=foreground,
                    weight=ft.FontWeight.W_600 if active else ft.FontWeight.W_400,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
            ],
        ),
    )


@ft.component
def sidebar() -> ft.Control:
    tr = use_t()
    location = ft.use_route_location()

    groups: list[ft.Control] = [
        ft.Column(
            spacing=1,
            controls=[
                ft.Container(
                    padding=ft.Padding.only(left=9, top=16, bottom=5),
                    content=ft.Text(
                        tr(group.label_key).upper(),
                        size=10,
                        color=_MUTED,
                        weight=ft.FontWeight.W_700,
                        style=ft.TextStyle(letter_spacing=1.1),
                    ),
                ),
                *[
                    _side_item(item, active=_is_active(location, item.route))
                    for item in group.items
                ],
            ],
        )
        for group in NAV_GROUPS
    ]

    footer = ft.Container(
        margin=ft.Margin.only(top=20),
        padding=ft.Padding.symmetric(horizontal=11, vertical=10),
        border_radius=10,
        bgcolor=kit.RAISED,
        border=ft.Border.all(1, _BORDER),
        content=ft.Column(
            spacing=2,
            controls=[
                ft.Text(
                    tr(
                        "site.sidebar.runtime",
                        flet=FLET_VERSION,
                        python=PYTHON_VERSION,
                    ),
                    size=10.5,
                    color=_MUTED,
                ),
                ft.Text(tr("site.sidebar.license"), size=10.5, color=_MUTED),
            ],
        ),
    )

    return ft.Container(
        width=SIDEBAR_WIDTH,
        bgcolor=ft.Colors.SURFACE,
        border=ft.Border(right=ft.BorderSide(1, _BORDER)),
        padding=ft.Padding.only(left=12, right=12, top=4, bottom=12),
        content=ft.Column(
            expand=True,
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            controls=[*groups, footer],
        ),
    )


# ---------------------------------------------------------------------------
# 本页目录
# ---------------------------------------------------------------------------


@ft.component
def outline_rail(headings: Sequence[tuple[str, str]]) -> ft.Control:
    """``headings`` 是 ``(锚点, 文案键)``；翻译在这里做，语言切换自动跟随。"""
    tr = use_t()
    page = ft.context.page

    def jump(anchor: str):
        async def handler(_: ft.Event[ft.Container]) -> None:
            await _Scroller.jump(anchor)

        return handler

    return ft.Container(
        width=OUTLINE_WIDTH,
        padding=ft.Padding.only(left=6, right=16, top=26, bottom=16),
        content=ft.Column(
            expand=True,
            spacing=2,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Container(
                    padding=ft.Padding.only(left=9, bottom=6),
                    content=ft.Text(
                        tr("site.on_this_page").upper(),
                        size=10,
                        color=_MUTED,
                        weight=ft.FontWeight.W_700,
                        style=ft.TextStyle(letter_spacing=1.1),
                    ),
                ),
                *[
                    ft.Container(
                        padding=ft.Padding.symmetric(horizontal=9, vertical=5),
                        border_radius=7,
                        on_click=jump(anchor),
                        ink=True,
                        content=ft.Text(
                            tr(key),
                            size=12,
                            color=_MUTED,
                            max_lines=2,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                    )
                    for anchor, key in headings
                ],
                ft.Container(
                    margin=ft.Margin.only(top=14, left=9),
                    on_click=lambda _e: page.launch_url(
                        f"{GITHUB_URL}/blob/main/{DOCS_ROOT.name}"
                    ),
                    content=ft.Text(tr("site.edit_page"), size=11.5, color=_MUTED),
                ),
            ],
        ),
    )


# ---------------------------------------------------------------------------
# 页头 / 上下页 / 页脚
# ---------------------------------------------------------------------------


@ft.component
def page_header(meta: PageMeta, *, badges: Sequence[ft.Control] = ()) -> ft.Control:
    tr = use_t()
    page = ft.context.page
    crumb_key, crumb_route = _CRUMB[meta.group]
    return ft.Column(
        spacing=12,
        controls=[
            ft.Row(
                spacing=5,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        on_click=lambda _e: page.navigate(crumb_route),
                        content=ft.Text(tr(crumb_key), size=11.5, color=_MUTED),
                    ),
                    ft.Icon(ft.Icons.CHEVRON_RIGHT, size=12, color=_MUTED),
                    ft.Text(tr(meta.title_key), size=11.5, color=ft.Colors.ON_SURFACE),
                ],
            ),
            ft.Text(
                tr(meta.title_key),
                size=32,
                weight=ft.FontWeight.W_800,
                style=ft.TextStyle(letter_spacing=-0.6, height=1.2),
            ),
            ft.Container(
                padding=ft.Padding.only(right=24),
                content=ft.Text(
                    tr(meta.desc_key),
                    size=15,
                    color=_MUTED,
                    style=ft.TextStyle(height=1.75),
                ),
            ),
            *([ft.Row(spacing=8, wrap=True, controls=list(badges))] if badges else []),
        ],
    )


@ft.component
def _step_card(meta: PageMeta, *, forward: bool) -> ft.Control:
    tr = use_t()
    page = ft.context.page
    edge = ft.CrossAxisAlignment.END if forward else ft.CrossAxisAlignment.START
    arrow = ft.Icon(
        ft.Icons.ARROW_FORWARD if forward else ft.Icons.ARROW_BACK,
        size=13,
        color=_MUTED,
    )
    return kit.hover_card(
        on_click=lambda _e: page.navigate(meta.route),
        padding=14,
        content=ft.Column(
            spacing=4,
            horizontal_alignment=edge,
            controls=[
                ft.Row(
                    spacing=6,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        *([] if forward else [arrow]),
                        ft.Text(
                            tr("site.next") if forward else tr("site.prev"),
                            size=10.5,
                            color=_MUTED,
                            weight=ft.FontWeight.W_600,
                        ),
                        *([arrow] if forward else []),
                    ],
                ),
                ft.Text(
                    tr(meta.title_key),
                    size=13.5,
                    weight=ft.FontWeight.W_600,
                    color=ft.Colors.PRIMARY,
                    text_align=ft.TextAlign.END if forward else ft.TextAlign.START,
                ),
            ],
        ),
    )


@ft.component
def step_nav(meta: PageMeta) -> ft.Control:
    previous = page_before(meta.route)
    following = page_after(meta.route)
    return ft.Row(
        spacing=12,
        controls=[
            ft.Container(
                expand=True,
                content=_step_card(previous, forward=False) if previous else None,
            ),
            ft.Container(
                expand=True,
                content=_step_card(following, forward=True) if following else None,
            ),
        ],
    )


@ft.component
def site_footer() -> ft.Control:
    tr = use_t()
    page = ft.context.page
    link = ft.TextStyle(size=12, color=_MUTED)

    def _link(label: str, url: str) -> ft.Control:
        return ft.Container(
            ink=True,
            border_radius=4,
            on_click=lambda _e: page.launch_url(url),
            content=ft.Text(label, style=link),
        )

    return ft.Container(
        margin=ft.Margin.only(top=6),
        padding=ft.Padding.only(top=20),
        border=ft.Border(top=ft.BorderSide(1, _BORDER)),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            wrap=True,
            run_spacing=10,
            controls=[
                ft.Column(
                    spacing=3,
                    controls=[
                        ft.Text("cs-ui", size=12.5, weight=ft.FontWeight.W_700),
                        ft.Text(tr("site.footer.tagline"), size=11.5, color=_MUTED),
                    ],
                ),
                ft.Row(
                    spacing=16,
                    controls=[
                        ft.Text(
                            tr("site.footer.license", version=PACKAGE_VERSION),
                            style=link,
                        ),
                        _link("GitHub", GITHUB_URL),
                        _link("Flet", "https://flet.dev"),
                    ],
                ),
            ],
        ),
    )


# ---------------------------------------------------------------------------
# 整体布局
# ---------------------------------------------------------------------------


@ft.component
def site_layout() -> ft.Control:
    """顶栏 + （侧边栏 | 正文 | 本页目录），外加命令面板浮层。"""
    outlet = ft.use_route_outlet()
    location = ft.use_route_location()
    open_search, set_open_search = ft.use_state(False)

    search_api.bind(lambda: set_open_search(True))

    meta = page_for_route(location)
    is_home = meta is None or meta.key == "home"
    headings = () if is_home or meta is None else outline_of(meta.key)

    body = ft.Row(
        expand=True,
        spacing=0,
        vertical_alignment=ft.CrossAxisAlignment.STRETCH,
        controls=[
            *([] if is_home else [sidebar()]),
            ft.Container(expand=True, bgcolor=kit.PAGE_BG, content=outlet),
            *([] if is_home or not headings else [outline_rail(headings)]),
        ],
    )

    shell = ft.Container(
        expand=True,
        bgcolor=kit.PAGE_BG,
        content=ft.Column(
            expand=True,
            spacing=0,
            controls=[
                top_bar(on_search=lambda _e: set_open_search(True)),
                body,
            ],
        ),
    )

    if not open_search:
        return shell

    return ft.Stack(
        expand=True,
        controls=[
            shell,
            SearchPalette(on_close=lambda: set_open_search(False)),
        ],
    )


def outline_of(key: str) -> tuple[tuple[str, str], ...]:
    """按页面 key 取 ``(锚点, 文案键)``。内容层是纯数据，所以能静态算出来。"""
    from docs.content import DOCS

    return tuple((heading.anchor, heading.key) for heading in outline(DOCS.get(key, ())))


__all__ = [
    "OUTLINE_WIDTH",
    "SIDEBAR_WIDTH",
    "TOPBAR_HEIGHT",
    "outline_of",
    "outline_rail",
    "page_header",
    "register_scroller",
    "sidebar",
    "site_footer",
    "site_layout",
    "step_nav",
    "top_bar",
]
