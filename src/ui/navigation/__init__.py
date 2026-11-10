"""导航类组件：应用栏、状态栏、面包屑、菜单、分页。

门面惰性（见 :mod:`ui._lazy`）：``from ui.navigation import Menu`` 只加载 ``menu``，
不会把应用栏 / 面包屑 / 分页一起拖进来。
"""

from ui._lazy import lazy_exports

lazy_exports(
    globals(),
    {
        "AppBar": ".app_bar",
        "BreadCrumb": ".bread_crumb",
        "Crumb": ".bread_crumb",
        "Menu": ".menu",
        "MenuGroup": ".menu",
        "MenuItem": ".menu",
        "Pagination": ".pagination",
        "PaginationState": ".pagination",
        "StatusBar": ".status_bar",
    },
    __name__,
)
