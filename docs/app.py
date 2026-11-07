"""路由表与根组件。

语言 Provider 在最外层（首帧就要拿到正确文案），主题其次（避免切换时闪一帧
旧配色），路由最内层。
"""

from __future__ import annotations

from collections.abc import Callable

import flet as ft

from docs.content import DOCS
from docs.home import home_page
from docs.pages import DocView, not_found_page
from docs.shell import site_layout
from docs.site import I18N_DIR, READING_ORDER
from ui import I18nProvider, ThemeProvider, load_catalogs

#: 文案在导入期装好，首帧就是正确语言（不会先闪默认语言）。
load_catalogs(I18N_DIR)


def _doc_route(key: str) -> Callable[[], ft.Control]:
    """给路由用的零参组件：把 ``DocView`` 固定到一个页面 key。"""

    @ft.component
    def page() -> ft.Control:
        return DocView(key)

    page.__name__ = f"{key}_page"
    page.__qualname__ = page.__name__
    return page


#: 子路由直接从导航数据生成 —— 加一页只需在 ``site.py`` 里加一条 PageMeta。
#: 文章页的内容在 ``DOCS`` 里；分类页 / 组件页的内容来自 ``ui.core.catalog``，
#: 所以这里只按"有没有内容"过滤文章页。
CHILDREN: list[ft.Route] = [
    ft.Route(index=True, component=home_page),
    *[
        ft.Route(path=page.route.lstrip("/"), component=_doc_route(page.key))
        for page in READING_ORDER
        if page.kind != "page" or page.key in DOCS
    ],
]

ROUTES: list[ft.Route] = [ft.Route(component=site_layout, children=CHILDREN)]


def _router() -> ft.Control:
    return ft.Router(ROUTES, not_found=not_found_page, manage_views=False)


def _themed() -> ft.Control:
    return ThemeProvider(build=_router)


@ft.component
def App() -> ft.Control:
    """根组件：默认简体中文，用户切过语言后按持久化选择恢复。"""
    return I18nProvider(locale="zh-CN", detect=False, build=_themed)


__all__ = ["CHILDREN", "ROUTES", "App"]
