"""文档站路由与根组件。"""

from __future__ import annotations

import flet as ft

from docs.core.assets import I18N_DIR, SITE_I18N_DIR
from docs.demos import (
    charts_page,
    display_page,
    feedback_page,
    form_page,
    general_page,
    layout_page,
    media_page,
    navigation_page,
    upload_page,
)
from docs.kit import docs_layout
from docs.pages import (
    about_page,
    architecture_page,
    components_page,
    getting_started_page,
    home_page,
    i18n_page,
    not_found_page,
    search_page,
    theming_page,
)
from ui import I18nProvider, ThemeProvider, load_catalogs

#: 文案在导入期装好，首帧就是正确语言，不会先闪默认语言。
load_catalogs(I18N_DIR)
load_catalogs(SITE_I18N_DIR)

ROUTES: list[ft.Route] = [
    ft.Route(
        component=docs_layout,
        children=[
            ft.Route(index=True, component=home_page),
            ft.Route(path="docs/getting-started", component=getting_started_page),
            ft.Route(path="docs/architecture", component=architecture_page),
            ft.Route(path="docs/theming", component=theming_page),
            ft.Route(path="docs/i18n", component=i18n_page),
            ft.Route(path="components", component=components_page),
            ft.Route(path="components/general", component=general_page),
            ft.Route(path="components/layout", component=layout_page),
            ft.Route(path="components/navigation", component=navigation_page),
            ft.Route(path="components/form", component=form_page),
            ft.Route(path="components/feedback", component=feedback_page),
            ft.Route(path="components/display", component=display_page),
            ft.Route(path="components/charts", component=charts_page),
            ft.Route(path="components/media", component=media_page),
            ft.Route(path="components/upload", component=upload_page),
            ft.Route(path="search", component=search_page),
            ft.Route(path="about", component=about_page),
        ],
    )
]


def _router() -> ft.Control:
    return ft.Router(ROUTES, not_found=not_found_page, manage_views=False)


def _themed() -> ft.Control:
    return ThemeProvider(build=_router)


@ft.component
def App() -> ft.Control:
    """根组件：语言最外层，主题次之，路由最内层。

    语言 Provider 要在首帧之前确定语言（持久化选择 / 系统语言），
    所以放在最外层；主题 Provider 负责写 ``page.theme``，放在路由外层可避免
    "切换模式时闪一帧旧配色"。
    """
    return I18nProvider(build=_themed)
