"""导航组件：面包屑、标签页、分页器、菜单与应用外壳。"""

from __future__ import annotations

import flet as ft

from docs import kit
from docs.blocks import Doc, code, demo, h2, note, p, tip, ul
from docs.content.components._shared import panel
from ui import (
    BreadCrumb,
    Column,
    Crumb,
    Menu,
    MenuGroup,
    MenuItem,
    Pagination,
    PaginationState,
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
def _pagination() -> ft.Control:
    state = kit.use_stable(lambda: PaginationState(sum_data_nums=1_286, data_per_page_nums=10))
    return panel(Pagination(state))


_MENU_CODE = '''Menu(
    items=[
        MenuItem("home", "概览", icon=ft.Icons.DASHBOARD_OUTLINED),
        MenuGroup("运维", [
            MenuItem(
                "host", "主机", icon=ft.Icons.DNS_OUTLINED,
                children=[                       # 非空即可展开，本身不可选中
                    MenuItem("hl", "主机列表"),
                    MenuItem("hg", "主机分组"),
                    MenuItem("ht", "标签管理", badge="12"),
                ],
            ),
        ]),
    ],
    selected_key="hl",          # 选中项（外部改它即重绘）
    expanded_keys=("host",),    # 默认展开哪几组
    show_collapse_arrow=True,   # 底部折叠按钮
    on_select=lambda item: ...,  # 叶子项被点中
)'''


def _menu_items(tr) -> list:
    """菜单演示数据：文案跟着语言走，所以每项都取 ``tr``。"""
    return [
        MenuItem("home", tr("demo.menu.home"), icon=ft.Icons.DASHBOARD_OUTLINED),
        MenuItem(
            "monitor", tr("demo.menu.monitor"), icon=ft.Icons.MONITOR_HEART_OUTLINED
        ),
        MenuGroup(
            tr("demo.menu.group"),
            [
                MenuItem(
                    "host",
                    tr("demo.menu.host"),
                    icon=ft.Icons.DNS_OUTLINED,
                    children=[
                        MenuItem("hl", tr("demo.menu.host_list"), dot=True),
                        MenuItem("hg", tr("demo.menu.host_group")),
                        MenuItem("ht", tr("demo.menu.host_tag"), badge="12"),
                    ],
                ),
                MenuItem(
                    "net",
                    tr("demo.menu.net"),
                    icon=ft.Icons.LAN_OUTLINED,
                    children=[
                        MenuItem("vpc", tr("demo.menu.vpc")),
                        MenuItem("eip", tr("demo.menu.eip")),
                    ],
                ),
            ],
        ),
        MenuItem("setting", tr("demo.menu.setting"), icon=ft.Icons.SETTINGS_OUTLINED),
        MenuItem(
            "audit",
            tr("demo.menu.audit"),
            icon=ft.Icons.RECEIPT_LONG_OUTLINED,
            disabled=True,
        ),
    ]


@ft.component
def _menu() -> ft.Control:
    tr = use_t()
    full = kit.use_stable(
        lambda: Menu(
            items=_menu_items(tr),
            selected_key="hl",
            expanded_keys=("host",),
            width=228,
            show_collapse_arrow=True,
        )
    )
    mini = kit.use_stable(
        lambda: Menu(
            items=_menu_items(tr),
            selected_key="hl",
            expanded_keys=("host",),
            collapsed=True,
        )
    )

    def frame(control: ft.Control, width: int) -> ft.Control:
        return ft.Container(
            width=width,
            padding=8,
            bgcolor=ft.Colors.SURFACE,
            border=ft.Border.all(1, kit.BORDER),
            border_radius=10,
            content=control,
        )

    return ft.Row(
        spacing=16,
        vertical_alignment=ft.CrossAxisAlignment.START,
        controls=[frame(full.ui(), 244), frame(mini.ui(), 64)],
    )


NAVIGATION: Doc = (
    p("cat.navigation.intro"),
    h2("cat.navigation.crumb.title"),
    demo(_breadcrumb, hint_key="cat.navigation.crumb.hint"),
    h2("cat.navigation.tabs.title"),
    demo(_tabs, hint_key="cat.navigation.tabs.hint", code=_TABS_CODE, padded=False),
    h2("cat.navigation.pagination.title"),
    demo(_pagination, hint_key="cat.navigation.pagination.hint", padded=False),
    h2("cat.navigation.menu.title"),
    demo(_menu, hint_key="cat.navigation.menu.hint", code=_MENU_CODE, padded=False),
    h2("cat.navigation.shell.title"),
    p("cat.navigation.shell.desc"),
    code(_SHELL_CODE, "shell.py"),
    tip("cat.navigation.shell.tip", "cat.navigation.shell.tip_title"),
    ul("cat.navigation.note1", "cat.navigation.note2"),
    note("cat.navigation.tip", "cat.navigation.tip_title"),
)
