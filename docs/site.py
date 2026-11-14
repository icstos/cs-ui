"""站点静态数据：版本、路径、页面注册表与组件目录。

这一层**只有数据、没有控件**，所以路由、侧边栏、搜索索引与页面渲染可以共享
同一份事实来源；改一处导航，三处同时生效。

组件的分类与清单不在这里维护 —— 它们来自 :mod:`ui.core.catalog`（库自己的
登记表）。站点只负责把「分类 / 组件」翻译成「路由 + 页面元数据」，因此组件
增删时只有库侧那一份表要改。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final, Literal, Protocol

import flet as ft

from ui.core import catalog
from ui.version import FLET_VERSION
from ui.version import __version__ as _ui_version

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
PYTHON_VERSION: Final[str] = "3.12+"
LICENSE_NAME: Final[str] = "MIT"


def _detect_version() -> str:
    """站点展示的 cs-ui 版本 —— 直接取库里的那一份，不再自己探测。

    以前这里重复了一遍 ``importlib.metadata`` 逻辑并写了个 ``"0.1.1"`` 兜底，
    结果 ``pyproject`` 是 ``0.1.1``、``ui.__version__`` 是 ``0.0.5``、页脚又是
    另一个数 —— 三处都要改，必然漏。现在只有 :mod:`ui.version` 一个来源。
    """
    return _ui_version


PACKAGE_VERSION: Final[str] = _detect_version()

# ---------------------------------------------------------------------------
# 页面注册表
# ---------------------------------------------------------------------------
type Group = Literal["start", "guide", "components", "project"]
type Kind = Literal["page", "category", "component"]


@dataclass(frozen=True, slots=True)
class PageMeta:
    """一个页面。

    普通页与分类页的标题 / 摘要走语言包 ``nav.<key>.*``；组件页的标题是导入名
    （``Pagination``，语言中性）、摘要是实现文件里那句 ``SPEC.summary`` ——
    所以这里留 ``name`` / ``brief`` 两个原文字段，由 :meth:`title` /
    :meth:`desc` 统一出口，外壳就不用分支判断了。
    """

    key: str
    route: str
    group: Group
    icon: ft.IconData
    kind: Kind = "page"
    #: 组件页：导入名（``"Pagination"``）
    name: str = ""
    #: 组件页：一句话摘要，来自 ``SPEC.summary``（可能为空，页面自己再取）
    brief: str = ""
    #: 组件页 / 分类页：所属分类键
    parent: str = ""

    @property
    def title_key(self) -> str:
        return f"nav.{self.key}.title"

    @property
    def desc_key(self) -> str:
        return f"nav.{self.key}.desc"

    def title(self, tr: Any) -> str:
        return self.name or tr(self.title_key)

    def desc(self, tr: Any) -> str:
        return self.brief or tr(self.desc_key)

    @property
    def is_component(self) -> bool:
        return self.kind == "component"


@dataclass(frozen=True, slots=True)
class NavGroup:
    """侧边栏的一组（``items`` 已是"分类 + 组件"交错展开后的顺序）。"""

    key: Group
    label_key: str
    items: tuple[PageMeta, ...] = field(default_factory=tuple)


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
_RESPONSIVE = _PAGE(
    "responsive", "/docs/responsive", "guide", ft.Icons.ASPECT_RATIO_OUTLINED
)
_ABOUT = _PAGE("about", "/about", "project", ft.Icons.INFO_OUTLINE)

#: 组件总览（九宫格）
_COMPONENTS = _PAGE(
    "components", "/components", "components", ft.Icons.VIEW_QUILT_OUTLINED
)

# ---------------------------------------------------------------------------
# 组件目录 → 分类页 + 组件页
# ---------------------------------------------------------------------------
_CATEGORY_PAGES: Final[dict[str, PageMeta]] = {
    category.key: PageMeta(
        category.key,
        f"/components/{category.key}",
        "components",
        category.icon,
        kind="category",
    )
    for category in catalog.GROUPS
}

_COMPONENT_PAGES: Final[dict[str, PageMeta]] = {
    item.key: PageMeta(
        item.key,
        catalog.route(item.key),
        "components",
        catalog.group(catalog.GROUP_OF[item.key]).icon
        if catalog.group(catalog.GROUP_OF[item.key])
        else ft.Icons.WIDGETS_OUTLINED,
        kind="component",
        name=item.name,
        parent=catalog.GROUP_OF[item.key],
    )
    for category in catalog.GROUPS
    for item in category.visible
}

#: 组件组在侧边栏里的顺序：总览 → 分类 → 该分类下的全部组件 → 下一个分类 …
_COMPONENT_NAV: Final[tuple[PageMeta, ...]] = tuple(
    page
    for category in catalog.GROUPS
    for page in (
        _CATEGORY_PAGES[category.key],
        *(
            _COMPONENT_PAGES[item.key]
            for item in category.visible
            if item.key in _COMPONENT_PAGES
        ),
    )
)

NAV_GROUPS: Final[tuple[NavGroup, ...]] = (
    NavGroup("start", "nav.group.start", (_QUICKSTART,)),
    NavGroup(
        "guide",
        "nav.group.guide",
        (_ARCHITECTURE, _THEMING, _I18N, _RESPONSIVE),
    ),
    NavGroup(
        "components",
        "nav.group.components",
        (_COMPONENTS, *_COMPONENT_NAV),
    ),
    NavGroup("project", "nav.group.project", (_ABOUT,)),
)

#: 侧边栏顺序即"上一页 / 下一页"的顺序（首页不进正文流）。
READING_ORDER: Final[tuple[PageMeta, ...]] = tuple(
    page for group in NAV_GROUPS for page in group.items
)

PAGES: Final[dict[str, PageMeta]] = {page.key: page for page in (HOME, *READING_ORDER)}

#: 键必须唯一：组件键与页面键撞了会静默丢页，这里直接炸在导入期。
if len(PAGES) != len(READING_ORDER) + 1:  # pragma: no cover - 结构性断言
    seen: dict[str, int] = {}
    for page in READING_ORDER:
        seen[page.key] = seen.get(page.key, 0) + 1
    dup = [key for key, times in seen.items() if times > 1]
    raise RuntimeError(f"页面键重复：{dup}")

PAGE_BY_ROUTE: Final[dict[str, PageMeta]] = {
    page.route: page for page in PAGES.values()
}

# ---------------------------------------------------------------------------
# 分类的展示数据（总览页、分类页、搜索共用）
# ---------------------------------------------------------------------------
CATEGORIES: Final[tuple[str, ...]] = catalog.CATEGORIES

COMPONENT_COUNTS: Final[dict[str, int]] = {
    category.key: len(category.visible) for category in catalog.GROUPS
}

COMPONENT_TOTAL: Final[int] = catalog.COMPONENT_TOTAL

SAMPLE_NAMES: Final[dict[str, tuple[str, ...]]] = {
    category.key: tuple(item.name for item in category.visible[:4])
    for category in catalog.GROUPS
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
    "upload": "info",
}


def category_page(key: str) -> PageMeta:
    """取分类页元数据；``key`` 必须来自 :data:`CATEGORIES`。"""
    return _CATEGORY_PAGES[key]


def group_entries(key: str) -> tuple[PageMeta, ...]:
    """某个分类下的组件页，按侧边栏顺序。"""
    return tuple(
        _COMPONENT_PAGES[item.key]
        for item in (catalog.group(key).visible if catalog.group(key) else ())
        if item.key in _COMPONENT_PAGES
    )


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
    """构建搜索索引：普通页 + 分类 + 组件名。

    组件摘要不进来：那要把全部实现模块 import 一遍（图表会拖进 matplotlib），
    而搜索命中的是**名字**，摘要只在卡片上读。
    """
    hits: list[Hit] = [
        Hit(
            title=page.title(tr),
            detail=page.desc(tr),
            route=page.route,
            category="site.search.pages",
            icon=page.icon,
        )
        for page in PAGES.values()
        if page.kind != "component"
    ]
    hits.extend(
        Hit(
            title=item.name,
            detail=tr(f"nav.{catalog.GROUP_OF[item.key]}.title"),
            route=catalog.route(item.key),
            category="site.search.components",
            icon=_COMPONENT_PAGES[item.key].icon,
        )
        for category in catalog.GROUPS
        for item in category.visible
    )
    return tuple(hits)


__all__ = [
    "CATEGORIES",
    "CATEGORY_ROLE",
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
    "Kind",
    "NavGroup",
    "PageMeta",
    "build_index",
    "category_page",
    "group_entries",
    "page_after",
    "page_before",
    "page_for_route",
]
