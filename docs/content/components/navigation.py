"""导航组件：面包屑、标签页、分页器与应用外壳。"""

from __future__ import annotations

import flet as ft

from docs import kit
from docs.blocks import Doc, code, demo, h2, note, p, tip, ul
from docs.content.components._shared import panel
from ui import (
    BreadCrumb,
    Column,
    Crumb,
    Paging,
    PagingState,
    Tab,
    TabBar,
    TabBarView,
    Tabs,
    use_t,
)

_SHELL_CODE = '''@ft.component
def shell() -> ft.Control:
    outlet = ft.use_route_outlet()        # 子路由渲染在这里
    return Row(
        controls=[
            NavigationRail(selected_index=0, destinations=[...]),
            Column(expand=True, controls=[AppBar(title="cs-ui"), outlet]),
        ],
    )'''

_TABS_CODE = '''Tabs(
    length=3,
    content=Column(
        controls=[
            TabBar(tabs=[Tab(text="Overview"), Tab(text="Detail")]),
            TabBarView(controls=[overview, detail]),
        ],
    ),
)'''


@ft.component
def _breadcrumb() -> ft.Control:
    tr = use_t()
    return Column(
        spacing=12,
        controls=[
            BreadCrumb(
                items=[
                    Crumb(tr("cat.navigation.crumb.home"), route="/"),
                    Crumb(tr("cat.navigation.crumb.components"), route="/components"),
                    Crumb(tr("cat.navigation.crumb.current")),
                ],
            ),
            BreadCrumb(
                items=[tr("cat.navigation.crumb.a"), tr("cat.navigation.crumb.b")],
                active_color=ft.Colors.PRIMARY,
            ),
        ],
    )


@ft.component
def _tabs() -> ft.Control:
    tr = use_t()
    pages = (
        ("cat.navigation.tabs.overview", ft.Icons.DASHBOARD_OUTLINED, "cat.navigation.tabs.overview_body"),
        ("cat.navigation.tabs.detail", ft.Icons.LIST_ALT, "cat.navigation.tabs.detail_body"),
        ("cat.navigation.tabs.settings", ft.Icons.SETTINGS_OUTLINED, "cat.navigation.tabs.settings_body"),
    )
    return ft.Container(
        height=210,
        border_radius=10,
        bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
        border=ft.Border.all(1, kit.BORDER),
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        content=Tabs(
            length=len(pages),
            content=Column(
                controls=[
                    TabBar(
                        tabs=[
                            Tab(text=tr(key), icon=icon) for key, icon, _ in pages
                        ]
                    ),
                    TabBarView(
                        expand=True,
                        height=140,
                        controls=[
                            ft.Container(
                                padding=16,
                                content=ft.Text(tr(body), size=13.5),
                            )
                            for _, _, body in pages
                        ],
                    ),
                ]
            ),
        ),
    )


@ft.component
def _paging() -> ft.Control:
    state = kit.use_stable(lambda: PagingState(sum_data_nums=1_286, data_per_page_nums=10))
    return panel(Paging(state))


NAVIGATION: Doc = (
    p("cat.navigation.intro"),
    h2("cat.navigation.crumb.title"),
    demo(_breadcrumb, hint_key="cat.navigation.crumb.hint"),
    h2("cat.navigation.tabs.title"),
    demo(_tabs, hint_key="cat.navigation.tabs.hint", code=_TABS_CODE, padded=False),
    h2("cat.navigation.paging.title"),
    demo(_paging, hint_key="cat.navigation.paging.hint", padded=False),
    h2("cat.navigation.shell.title"),
    p("cat.navigation.shell.desc"),
    code(_SHELL_CODE, "shell.py"),
    tip("cat.navigation.shell.tip", "cat.navigation.shell.tip_title"),
    ul("cat.navigation.note1", "cat.navigation.note2"),
    note("cat.navigation.tip", "cat.navigation.tip_title"),
)
