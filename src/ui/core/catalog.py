"""组件目录 —— 全部组件、所属分类与实现模块的**唯一登记处**。

这一层只有数据：不 import 任何组件模块。所以文档站启动时可以立刻拿到
"有多少组件、分别叫什么、在哪一组"，而真正的 :class:`~ui.core.doc.Spec`
只在该组件页面被访问时才 import 进来（图表会拖进 matplotlib，不能进首帧）。

新增组件时改这里一处：侧边栏两级菜单、路由、搜索索引、首页统计、分类页
全部跟着变 —— 它们读的都是这份表。

约定：``key`` 与实现文件的模块名一致（``ui.input.number_input`` → ``number_input``），
``scripts/_doc_check.py`` 会校验这一点，防止侧边栏点进去是空的。
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from typing import Any, Final

import flet as ft

from ui.core.doc import Spec

__all__ = [
    "CATEGORIES",
    "COMPONENT_TOTAL",
    "ENTRIES",
    "GROUP_OF",
    "GROUPS",
    "Category",
    "Entry",
    "count",
    "entry",
    "group",
    "load",
    "route",
]


@dataclass(frozen=True, slots=True)
class Entry:
    """目录里的一个组件。

    Args:
        key: 路由键，与实现文件名一致（``"number_input"``）。
        name: 展示名，与导入名一致（``"NumberInput"``）。
        module: 实现模块的完整路径，用来按需 import。
        hidden: 不进侧边栏（内部组件、或与别的条目合并说明时用）。
    """

    key: str
    name: str
    module: str
    hidden: bool = False

    @property
    def attr(self) -> str:
        """组件在模块里的导入名（``Header_1`` 这类会被 ``name`` 覆盖）。"""
        return self.name.split(" ")[0]

    @property
    def file(self) -> str:
        """源码路径（相对仓库根），文档页脚与搜索用。"""
        return "src/" + self.module.replace(".", "/") + ".py"


@dataclass(frozen=True, slots=True)
class Category:
    """一个分类：一个图标 + 一组组件，顺序即侧边栏顺序。"""

    key: str
    icon: ft.IconData
    entries: tuple[Entry, ...] = field(default_factory=tuple)

    @property
    def visible(self) -> tuple[Entry, ...]:
        return tuple(item for item in self.entries if not item.hidden)

    @property
    def label_key(self) -> str:
        """分类名走站点语言包 ``nav.<key>.title``（与页面标题共用一份翻译）。"""
        return f"nav.{self.key}.title"


def _make(key: str, icon: ft.IconData, *items: tuple[str, str, str]) -> Category:
    """``_make("form", ICON, ("input", "Input", "ui.input.input"), ...)``"""
    return Category(key, icon, tuple(Entry(*item) for item in items))


# ---------------------------------------------------------------------------
# 目录本体：九个分类，组内顺序 = 学习顺序（先常用、后专业）
# ---------------------------------------------------------------------------
GROUPS: Final[tuple[Category, ...]] = (
    _make(
        "general",
        ft.Icons.WIDGETS_OUTLINED,
        ("text", "Text", "ui.display.text"),
        ("heading", "Heading", "ui.display.text"),
        ("quote", "Quote", "ui.display.text"),
        ("link", "Link", "ui.display.text"),
        ("markdown", "Markdown", "ui.display.text"),
        ("code", "Code", "ui.display.text"),
        ("json", "Json", "ui.display.text"),
        ("button", "Button", "ui.input.button"),
        ("chip", "Chip", "ui.input.chip"),
        ("tag", "Tag", "ui.display.tag"),
        ("image", "Image", "ui.display.image"),
        ("divider", "Divider", "ui.layout.divider"),
    ),
    _make(
        "layout",
        ft.Icons.DASHBOARD_CUSTOMIZE_OUTLINED,
        ("card", "Card", "ui.layout.card"),
        ("metric_card", "MetricCard", "ui.layout.metric_card"),
        ("form_row", "FormRow", "ui.layout.form_row"),
        ("container", "Container", "ui.layout.container"),
        ("row", "Row", "ui.layout.row"),
        ("column", "Column", "ui.layout.column"),
        ("stack", "Stack", "ui.layout.stack"),
        ("list_view", "ListView", "ui.layout.list_view"),
        ("grid_view", "GridView", "ui.layout.grid_view"),
        ("grid", "Grid", "ui.layout.grid"),
        ("expander", "Expander", "ui.layout.expander"),
        ("step", "Step", "ui.layout.step"),
        ("table", "Table", "ui.layout.table"),
        ("tabs", "Tabs", "ui.layout.tabs"),
        ("page_layout", "PageLayout", "ui.layout.page"),
    ),
    _make(
        "navigation",
        ft.Icons.EXPLORE_OUTLINED,
        ("app_bar", "AppBar", "ui.navigation.app_bar"),
        ("menu_bar", "MenuBar", "ui.navigation.menu_bar"),
        ("status_bar", "StatusBar", "ui.navigation.status_bar"),
        ("bread_crumb", "BreadCrumb", "ui.navigation.bread_crumb"),
        ("menu", "Menu", "ui.navigation.menu"),
        ("pagination", "Pagination", "ui.navigation.pagination"),
    ),
    _make(
        "form",
        ft.Icons.EDIT_NOTE,
        ("input", "Input", "ui.input.input"),
        ("number_input", "NumberInput", "ui.input.number_input"),
        ("checkbox", "Checkbox", "ui.input.checkbox"),
        ("switch", "Switch", "ui.input.switch"),
        ("radio", "Radio", "ui.input.radio"),
        ("select_box", "SelectBox", "ui.input.select_box"),
        ("multi_select", "MultiSelect", "ui.input.multi_select"),
        ("cascader", "Cascader", "ui.input.cascader"),
        ("transfer", "Transfer", "ui.input.transfer"),
        ("slider", "Slider", "ui.input.slider"),
        ("rating", "Rating", "ui.input.rating"),
        ("segmented_button", "SegmentedButton", "ui.input.segmented_button"),
        ("date_input", "DateInput", "ui.input.date_input"),
        ("datetime_input", "DateTimeInput", "ui.input.datetime_input"),
        ("color_picker", "ColorPicker", "ui.input.color_picker"),
        ("search_bar", "SearchBar", "ui.input.search_bar"),
    ),
    _make(
        "feedback",
        ft.Icons.FEEDBACK_OUTLINED,
        ("message", "Message", "ui.feedback.message"),
        ("notification", "Notification", "ui.feedback.notification"),
        ("alert_dialog", "AlertDialog", "ui.feedback.alert_dialog"),
        ("progress_bar", "ProgressBar", "ui.feedback.progress_bar"),
        ("loading", "Loading", "ui.feedback.loading"),
    ),
    _make(
        "display",
        ft.Icons.TABLE_CHART_OUTLINED,
        ("list_tile", "ListTile", "ui.display.list_tile"),
        ("descriptions", "Descriptions", "ui.display.descriptions"),
        ("kbd", "Kbd", "ui.display.kbd"),
        ("carousel", "Carousel", "ui.display.carousel"),
        ("calendar", "Calendar", "ui.display.calendar"),
        ("heatmap", "Heatmap", "ui.display.heatmap"),
        ("number_animation", "NumberAnimation", "ui.display.number_animation"),
        ("image_grid_view", "ImageGridView", "ui.display.image_gridview"),
        ("tree", "Tree", "ui.display.tree"),
        ("log_container", "LogContainer", "ui.display.log_container"),
        ("code_editor", "CodeEditor", "ui.utils.code_editor"),
        ("code_view", "CodeView", "ui.utils.code_view"),
    ),
    _make(
        "charts",
        ft.Icons.INSERT_CHART_OUTLINED,
        ("line_chart", "LineChart", "ui.chart.line_chart"),
        ("area_chart", "AreaChart", "ui.chart.area_chart"),
        ("bar_chart", "BarChart", "ui.chart.bar_chart"),
        ("scatter_chart", "ScatterChart", "ui.chart.scatter_chart"),
    ),
    _make(
        "upload",
        ft.Icons.UPLOAD_FILE_OUTLINED,
        ("file_picker", "FilePicker", "ui.input.file_picker"),
        ("file_dialog", "FileDialog", "ui.input.file_picker"),
        ("dir_picker", "DirPicker", "ui.input.file_picker"),
        ("file_saver", "FileSaver", "ui.input.file_picker"),
        ("image_picker", "ImagePicker", "ui.input.image_picker"),
    ),
)

CATEGORIES: Final[tuple[str, ...]] = tuple(item.key for item in GROUPS)

ENTRIES: Final[dict[str, Entry]] = {
    item.key: item for category in GROUPS for item in category.entries
}

GROUP_OF: Final[dict[str, str]] = {
    item.key: category.key for category in GROUPS for item in category.entries
}

COMPONENT_TOTAL: Final[int] = len(ENTRIES)


# ---------------------------------------------------------------------------
# 查询
# ---------------------------------------------------------------------------
def group(key: str) -> Category | None:
    for category in GROUPS:
        if category.key == key:
            return category
    return None


def entry(key: str) -> Entry | None:
    return ENTRIES.get(key)


def count(key: str) -> int:
    found = group(key)
    return len(found.visible) if found else 0


def route(key: str) -> str:
    """组件页路由：``/components/<分类>/<组件>``。"""
    category = GROUP_OF.get(key)
    return f"/components/{category}/{key}" if category else f"/components/{key}"


# ---------------------------------------------------------------------------
# 按需加载
# ---------------------------------------------------------------------------
def _fallback(item: Entry, module: Any) -> Spec:
    """模块还没写 ``SPEC`` 时的兜底说明。

    有 docstring 就用它当定义、用 ``__all__`` 里的类当内省对象 —— 至少不会
    在侧边栏里点出一张白页。写完 ``SPEC`` 后这份兜底自动让位。
    """
    doc = (getattr(module, "__doc__", "") or "").strip()
    definition = doc.split("\n\n", 1)[0].replace("\n", " ").strip()
    target = getattr(module, item.attr, None)
    return Spec(
        name=item.name,
        summary=definition or f"{item.name} 组件。",
        definition=definition,
        target=target if isinstance(target, type) else None,
        examples=(),
        notes=(),
    )


def _spec_from(module: Any, item: Entry) -> Spec | None:
    """从模块里取这个组件自己的说明。

    一个文件可以写多个组件（``display/text.py`` 里就有 Text / Heading / Quote …），
    这时模块要提供 ``SPECS: dict[str, Spec]``（键 = 目录键）。只有一个组件时
    直接用模块级 ``SPEC``，但**必须确认名字对得上** —— 否则共模块的其他条目
    会被同一个说明串台，页面上出现"点 Heading 看到 Text"。
    """
    specs = getattr(module, "SPECS", None)
    if isinstance(specs, dict) and item.key in specs:
        found = specs[item.key]
        return found if isinstance(found, Spec) else None

    spec = getattr(module, "SPEC", None)
    if isinstance(spec, Spec) and spec.name.split(" ")[0] == item.attr:
        return spec
    return None


def load(key: str) -> Spec:
    """取组件说明：先读模块里的 ``SPECS`` / ``SPEC``，没有就用 docstring 兜底。

    主题、路由、源码路径都在这里补齐（``bound``），所以实现文件里的 ``SPEC``
    只需要写内容，不用重复声明自己在哪一组、路由键叫什么。
    """
    item = ENTRIES.get(key)
    if item is None:
        raise KeyError(f"组件目录里没有 {key!r}")

    module = importlib.import_module(item.module)
    spec = _spec_from(module, item) or _fallback(item, module)
    return spec.bound(key=item.key, group=GROUP_OF[item.key], source=item.file)
