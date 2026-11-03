"""站点静态数据：版本、路径、页面注册表与组件目录。

这一层**只有数据、没有控件**，所以路由、侧边栏、搜索索引与页面渲染可以共享
同一份事实来源；改一处导航，三处同时生效。
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, Final, Literal, Protocol

import flet as ft

# ---------------------------------------------------------------------------
# 路径与版本
# ---------------------------------------------------------------------------

DOCS_ROOT: Final[Path] = Path(__file__).resolve().parent
PROJECT_ROOT: Final[Path] = DOCS_ROOT.parent
UI_ROOT: Final[Path] = PROJECT_ROOT / "src" / "ui"

FONT_FILE: Final[Path] = UI_ROOT / "data" / "fonts" / "AlibabaPuHuiTi-3-55-Regular.otf"
FONT_FAMILY: Final[str] = "AlibabaPuHuiTi"
LOGO_FILE: Final[Path] = UI_ROOT / "data" / "images" / "logo.png"

I18N_DIR: Final[Path] = DOCS_ROOT / "i18n" / "site"

SITE_NAME: Final[str] = "cs-ui"
GITHUB_URL: Final[str] = "https://github.com/icstos/cs-ui"
FLET_URL: Final[str] = "https://flet.dev"
FLET_VERSION: Final[str] = "1.0.5"
PYTHON_VERSION: Final[str] = "3.12+"
LICENSE_NAME: Final[str] = "MIT"


def _detect_version() -> str:
    """优先取已安装包版本，源码运行时退回发布版本。"""
    try:
        return version("cs-ui")
    except PackageNotFoundError:
        return "0.1.1"


PACKAGE_VERSION: Final[str] = _detect_version()

# ---------------------------------------------------------------------------
# 页面注册表
# ---------------------------------------------------------------------------

type Group = Literal["start", "guide", "components", "project"]


@dataclass(frozen=True, slots=True)
class PageMeta:
    """一个页面。标题与摘要都来自语言包 ``nav.<key>.*``。"""

    key: str
    route: str
    group: Group
    icon: ft.IconData

    @property
    def title_key(self) -> str:
        return f"nav.{self.key}.title"

    @property
    def desc_key(self) -> str:
        return f"nav.{self.key}.desc"


@dataclass(frozen=True, slots=True)
class NavGroup:
    """侧边栏的一组。"""

    key: Group
    label_key: str
    items: tuple[PageMeta, ...]


_PAGE = PageMeta

HOME: Final[PageMeta] = _PAGE("home", "/", "start", ft.Icons.HOME_OUTLINED)

_QUICKSTART = _PAGE(
    "quickstart", "/docs/quickstart", "start", ft.Icons.ROCKET_LAUNCH_OUTLINED
)
_ARCHITECTURE = _PAGE(
    "architecture", "/docs/architecture", "guide", ft.Icons.ACCOUNT_TREE_OUTLINED
)
_THEMING = _PAGE("theming", "/docs/theming", "guide", ft.Icons.PALETTE_OUTLINED)
_I18N = _PAGE("i18n", "/docs/i18n", "guide", ft.Icons.TRANSLATE)

_COMPONENTS = _PAGE(
    "components", "/components", "components", ft.Icons.VIEW_QUILT_OUTLINED
)

_CATEGORY_ICONS: Final[dict[str, ft.IconData]] = {
    "general": ft.Icons.WIDGETS_OUTLINED,
    "layout": ft.Icons.DASHBOARD_CUSTOMIZE_OUTLINED,
    "navigation": ft.Icons.EXPLORE_OUTLINED,
    "form": ft.Icons.EDIT_NOTE,
    "feedback": ft.Icons.FEEDBACK_OUTLINED,
    "display": ft.Icons.TABLE_CHART_OUTLINED,
    "charts": ft.Icons.INSERT_CHART_OUTLINED,
    "media": ft.Icons.PLAY_CIRCLE_OUTLINE,
    "upload": ft.Icons.UPLOAD_FILE_OUTLINED,
}

_ABOUT = _PAGE("about", "/about", "project", ft.Icons.INFO_OUTLINE)


# ---------------------------------------------------------------------------
# 组件目录：既是侧边栏来源，也是搜索索引与组件总览页的数据
# ---------------------------------------------------------------------------

_COMPONENT_GROUPS: Final[dict[str, tuple[str, ...]]] = {
    "general": (
        "Text",
        "Header_1 … Header_5",
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
        "Table",
        "Tabs",
        "PageLayout",
    ),
    "navigation": (
        "BreadCrumb",
        "Paging",
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
    ),
    "display": (
        "ListTile",
        "LogContainer",
        "CodeEditor",
        "CodeView",
        "ImageGridView",
    ),
    "charts": ("LineChart", "AreaChart", "BarChart", "ScatterChart"),
    "media": ("Audio", "AudioPlayer", "Video", "Pdf"),
    "upload": ("FilePicker", "DirPicker", "FileSaver", "ImagePicker"),
}

#: 分类图标的强调色角色；``primary`` 直接用主题主色，其余走语义色。
CATEGORY_ROLE: Final[dict[str, str]] = {
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

CATEGORIES: Final[tuple[str, ...]] = tuple(_COMPONENT_GROUPS)

_CATEGORY_PAGES: Final[tuple[PageMeta, ...]] = tuple(
    _PAGE(key, f"/components/{key}", "components", _CATEGORY_ICONS[key])
    for key in CATEGORIES
)

NAV_GROUPS: Final[tuple[NavGroup, ...]] = (
    NavGroup("start", "nav.group.start", (_QUICKSTART,)),
    NavGroup("guide", "nav.group.guide", (_ARCHITECTURE, _THEMING, _I18N)),
    NavGroup(
        "components", "nav.group.components", (_COMPONENTS, *_CATEGORY_PAGES)
    ),
    NavGroup("project", "nav.group.project", (_ABOUT,)),
)

#: 侧边栏顺序即"上一页 / 下一页"的顺序（首页不进正文流）。
READING_ORDER: Final[tuple[PageMeta, ...]] = tuple(
    page for group in NAV_GROUPS for page in group.items
)

PAGES: Final[dict[str, PageMeta]] = {
    page.key: page for page in (HOME, *READING_ORDER)
}

PAGE_BY_ROUTE: Final[dict[str, PageMeta]] = {
    page.route: page for page in PAGES.values()
}

COMPONENT_COUNTS: Final[dict[str, int]] = {
    key: len(names) for key, names in _COMPONENT_GROUPS.items()
}

COMPONENT_TOTAL: Final[int] = sum(COMPONENT_COUNTS.values())
CATEGORY_TOTAL: Final[int] = len(CATEGORIES)

SAMPLE_NAMES: Final[dict[str, tuple[str, ...]]] = {
    key: names[:4] for key, names in _COMPONENT_GROUPS.items()
}


def category_page(key: str) -> PageMeta:
    """取分类页元数据；``key`` 必须来自 :data:`CATEGORIES`。"""
    return PAGES[key]


def page_before(route: str) -> PageMeta | None:
    return _neighbour(route, -1)


def page_after(route: str) -> PageMeta | None:
    return _neighbour(route, 1)


def _neighbour(route: str, step: int) -> PageMeta | None:
    for index, page in enumerate(READING_ORDER):
        if page.route != route:
            continue
        target = index + step
        if 0 <= target < len(READING_ORDER):
            return READING_ORDER[target]
        return None
    return None


def page_for_route(route: str) -> PageMeta | None:
    """路由 → 页面。忽略结尾斜杠，空路径视为首页。"""
    normalized = route.rstrip("/") or "/"
    return PAGE_BY_ROUTE.get(normalized)


# ---------------------------------------------------------------------------
# 搜索索引
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Hit:
    """一条搜索结果。

    ``title`` / ``detail`` 是**已经翻译过**的文本：索引在渲染期构建，
    换语言时重建即可，所以这里不存键。
    """

    title: str
    detail: str
    route: str
    category: str
    icon: ft.IconData


class Translate(Protocol):
    """``use_t()`` 的调用签名（避免把 Translator 类型引进数据层）。"""

    def __call__(self, key: str, /, **params: Any) -> str: ...


def build_index(tr: Translate) -> tuple[Hit, ...]:
    """构建搜索索引：页面 + 组件名。"""
    hits: list[Hit] = [
        Hit(
            title=tr(page.title_key),
            detail=tr(page.desc_key),
            route=page.route,
            category="site.search.pages",
            icon=page.icon,
        )
        for page in PAGES.values()
    ]
    hits.extend(
        Hit(
            title=name,
            detail=tr(PAGES[key].title_key),
            route=f"/components/{key}",
            category="site.search.components",
            icon=_CATEGORY_ICONS[key],
        )
        for key, names in _COMPONENT_GROUPS.items()
        for name in names
    )
    return tuple(hits)


__all__ = [
    "CATEGORIES",
    "CATEGORY_ROLE",
    "CATEGORY_TOTAL",
    "COMPONENT_COUNTS",
    "COMPONENT_TOTAL",
    "DOCS_ROOT",
    "FLET_URL",
    "FLET_VERSION",
    "FONT_FAMILY",
    "FONT_FILE",
    "GITHUB_URL",
    "HOME",
    "I18N_DIR",
    "LICENSE_NAME",
    "LOGO_FILE",
    "NAV_GROUPS",
    "PACKAGE_VERSION",
    "PAGES",
    "PAGE_BY_ROUTE",
    "PROJECT_ROOT",
    "PYTHON_VERSION",
    "READING_ORDER",
    "SAMPLE_NAMES",
    "SITE_NAME",
    "UI_ROOT",
    "Group",
    "Hit",
    "NavGroup",
    "PageMeta",
    "build_index",
    "category_page",
    "page_after",
    "page_before",
    "page_for_route",
]
