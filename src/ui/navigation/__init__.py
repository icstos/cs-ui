"""导航类组件：应用栏、菜单栏、状态栏、面包屑、侧边菜单、分页。

门面惰性（见 :mod:`ui._lazy`）：``from ui.navigation import MenuBar`` 只加载
``menu_bar``，不会把侧边菜单 / 面包屑 / 分页一起拖进来。
"""

from ui._lazy import lazy_exports

lazy_exports(
    globals(),
    {
        "AppBar": ".app_bar",
        "BreadCrumb": ".bread_crumb",
        "Crumb": ".bread_crumb",
        "Menu": ".menu",
        "MenuAction": ".menu_bar",
        "MenuBar": ".menu_bar",
        "MenuGroup": ".menu",
        "MenuItem": ".menu",
        "MenuSection": ".menu_bar",
        "action_count": ".menu_bar",
        "find_action": ".menu_bar",
        "iter_actions": ".menu_bar",
        "shortcut_map": ".menu_bar",
        "validate_sections": ".menu_bar",
        "Pagination": ".pagination",
        "PaginationState": ".pagination",
        "StatusBar": ".status_bar",
    },
    __name__,
)
