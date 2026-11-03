"""文档站的导航、页面与组件索引（纯数据）。"""

from __future__ import annotations

from dataclasses import dataclass

import flet as ft

from docs.core.assets import PACKAGE_VERSION

SITE_NAME = "cs-ui"
FLET_VERSION = "1.0.5"
PYTHON_VERSION = "3.12+"
GITHUB_URL = "https://github.com/icstos/cs-ui"
FLET_URL = "https://flet.dev"


@dataclass(frozen=True, slots=True)
class PageMeta:
    """一个文档页面。标题与描述都从语言包的 ``site.nav.<key>`` 读取。"""

    key: str
    route: str
    group: str
    icon: ft.IconData

    @property
    def title_key(self) -> str:
        return f"site.nav.{self.key}.title"

    @property
    def desc_key(self) -> str:
        return f"site.nav.{self.key}.desc"


@dataclass(frozen=True, slots=True)
class NavGroup:
    key: str
    items: tuple[PageMeta, ...]

    @property
    def title_key(self) -> str:
        return f"site.group.{self.key}"


@dataclass(frozen=True, slots=True)
class ComponentMeta:
    """搜索索引里的单个组件条目。"""

    name: str
    category: str


_PAGE = PageMeta

_START = (
    _PAGE("home", "/", "start", ft.Icons.HOME),
    _PAGE("getting_started", "/docs/getting-started", "start", ft.Icons.ROCKET_LAUNCH),
)

_GUIDE = (
    _PAGE("architecture", "/docs/architecture", "guide", ft.Icons.ACCOUNT_TREE),
    _PAGE("theming", "/docs/theming", "guide", ft.Icons.PALETTE),
    _PAGE("i18n", "/docs/i18n", "guide", ft.Icons.TRANSLATE),
)

_COMPONENTS = (
    _PAGE("components", "/components", "components", ft.Icons.VIEW_QUILT),
    _PAGE("general", "/components/general", "components", ft.Icons.WIDGETS),
    _PAGE("layout", "/components/layout", "components", ft.Icons.DASHBOARD_CUSTOMIZE),
    _PAGE("navigation", "/components/navigation", "components", ft.Icons.EXPLORE),
    _PAGE("form", "/components/form", "components", ft.Icons.EDIT_NOTE),
    _PAGE("feedback", "/components/feedback", "components", ft.Icons.FEEDBACK_OUTLINED),
    _PAGE("display", "/components/display", "components", ft.Icons.TABLE_CHART),
    _PAGE("charts", "/components/charts", "components", ft.Icons.INSERT_CHART_OUTLINED),
    _PAGE("media", "/components/media", "components", ft.Icons.PLAY_CIRCLE_OUTLINE),
    _PAGE("upload", "/components/upload", "components", ft.Icons.UPLOAD_FILE),
)

_PROJECT = (_PAGE("about", "/about", "project", ft.Icons.INFO_OUTLINE),)

NAV_GROUPS: tuple[NavGroup, ...] = (
    NavGroup("start", _START),
    NavGroup("guide", _GUIDE),
    NavGroup("components", _COMPONENTS),
    NavGroup("project", _PROJECT),
)

ALL_PAGES: tuple[PageMeta, ...] = tuple(
    page for group in NAV_GROUPS for page in group.items
)
#: 搜索页不在侧边栏出现，但需要和其他页面共用页头与文案。
SEARCH_PAGE = PageMeta("search", "/search", "start", ft.Icons.SEARCH)
PAGE_BY_KEY: dict[str, PageMeta] = {
    **{page.key: page for page in ALL_PAGES},
    "search": SEARCH_PAGE,
}

_COMPONENT_GROUPS: dict[str, tuple[str, ...]] = {
    "general": (
        "Text",
        "Header_1",
        "Header_2",
        "Header_3",
        "Header_4",
        "Header_5",
        "Quote",
        "Link",
        "Button",
        "IconButton",
        "Chip",
        "Image",
        "Badge",
        "Divider",
        "Markdown",
        "Json",
    ),
    "layout": (
        "Card",
        "Container",
        "Row",
        "Column",
        "Stack",
        "ListView",
        "GridView",
        "Expander",
        "Timeline",
        "TimelineItem",
        "Table",
        "Tabs",
        "TabBar",
        "TabBarView",
        "PageLayout",
    ),
    "navigation": (
        "BreadCrumb",
        "Crumb",
        "Paging",
        "PagingState",
        "AppBar",
        "NavigationRail",
        "NavigationBar",
    ),
    "form": (
        "Input",
        "Checkbox",
        "CheckboxGroup",
        "Switch",
        "Radio",
        "SelectBox",
        "MultiSelect",
        "Slider",
        "RangeSlider",
        "Rating",
        "SegmentedButton",
        "DateInput",
        "DateTimeInput",
        "ColorPicker",
        "SearchBar",
    ),
    "feedback": (
        "Toast",
        "Message",
        "AlertDialog",
        "ProgressBar",
        "Loading",
        "snackbar",
    ),
    "display": (
        "ListTile",
        "LogContainer",
        "CodeEditor",
        "CodeView",
        "ImageGridView",
        "Markdown",
    ),
    "charts": ("LineChart", "AreaChart", "BarChart", "ScatterChart"),
    "media": ("Audio", "AudioPlayer", "Video", "Pdf"),
    "upload": ("FilePicker", "DirPicker", "FileSaver", "ImagePicker"),
}

COMPONENTS: tuple[ComponentMeta, ...] = tuple(
    ComponentMeta(name, category)
    for category, names in _COMPONENT_GROUPS.items()
    for name in names
)

CATEGORY_KEYS: tuple[str, ...] = tuple(_COMPONENT_GROUPS)
CATEGORY_ROUTES: dict[str, str] = {
    key: f"/components/{key}" for key in CATEGORY_KEYS
}
CATEGORY_COUNTS: dict[str, int] = {
    key: len(names) for key, names in _COMPONENT_GROUPS.items()
}

#: 分类图标的强调色角色。``primary`` 直接使用 M3 主色，其余落到语义色。
CATEGORY_ROLE: dict[str, str] = {
    "general": "primary",
    "layout": "success",
    "navigation": "warning",
    "form": "info",
    "feedback": "danger",
    "display": "primary",
    "charts": "success",
    "media": "warning",
    "upload": "info",
}

COMPONENT_TOTAL = len(COMPONENTS)
CATEGORY_TOTAL = len(CATEGORY_KEYS)


def page_after(route: str) -> PageMeta | None:
    for index, page in enumerate(ALL_PAGES):
        if page.route == route and index + 1 < len(ALL_PAGES):
            return ALL_PAGES[index + 1]
    return None


def page_before(route: str) -> PageMeta | None:
    for index, page in enumerate(ALL_PAGES):
        if page.route == route and index > 0:
            return ALL_PAGES[index - 1]
    return None


__all__ = [
    "ALL_PAGES",
    "CATEGORY_COUNTS",
    "CATEGORY_KEYS",
    "CATEGORY_ROLE",
    "CATEGORY_ROUTES",
    "CATEGORY_TOTAL",
    "COMPONENTS",
    "COMPONENT_TOTAL",
    "FLET_URL",
    "FLET_VERSION",
    "GITHUB_URL",
    "NAV_GROUPS",
    "PACKAGE_VERSION",
    "PAGE_BY_KEY",
    "PYTHON_VERSION",
    "SEARCH_PAGE",
    "SITE_NAME",
    "ComponentMeta",
    "NavGroup",
    "PageMeta",
    "page_after",
    "page_before",
]
