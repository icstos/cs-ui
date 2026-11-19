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
        name: 展示名，格式是「英文导入名 中文名」（``"NumberInput 数字输入"``）。
            :attr:`attr` 取空格前的英文作为真正的导入名，中文仅给人看。
        module: 实现模块的完整路径，用来按需 import。
        hidden: 不进侧边栏（内部组件、或与别的条目合并说明时用）。
    """

    key: str
    name: str
    module: str
    hidden: bool = False

    @property
    def attr(self) -> str:
        """组件在模块里的导入名：``name`` 里空格前的英文部分。

        ``name`` 现在是「英文名 中文名」的展示形式（``"Row 行"``），真正的
        导入名取第一段（``"Row"``）。``Header_1`` 这类大小写特殊的名字也靠它覆盖 key。
        """
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
        ("text", "Text 文本", "ui.display.text"),
        ("heading", "Heading 标题", "ui.display.text"),
        ("quote", "Quote 引用", "ui.display.text"),
        ("link", "Link 链接", "ui.display.text"),
        ("markdown", "Markdown 富文本", "ui.display.text"),
        ("button", "Button 按钮", "ui.input.button"),
        ("chip", "Chip 标签片", "ui.input.chip"),
        ("tag", "Tag 标签", "ui.display.tag"),
        ("image", "Image 图片", "ui.display.image"),
        ("divider", "Divider 分隔线", "ui.layout.divider"),
    ),
    _make(
        "layout",
        ft.Icons.DASHBOARD_CUSTOMIZE_OUTLINED,
        ("card", "Card 卡片", "ui.layout.card"),
        ("metric_card", "MetricCard 指标卡", "ui.layout.metric_card"),
        ("form_row", "FormRow 表单行", "ui.layout.form_row"),
        ("container", "Container 容器", "ui.layout.container"),
        ("row", "Row 行", "ui.layout.row"),
        ("column", "Column 列", "ui.layout.column"),
        ("stack", "Stack 堆叠", "ui.layout.stack"),
        ("list_view", "ListView 列表视图", "ui.layout.list_view"),
        ("grid_view", "GridView 网格视图", "ui.layout.grid_view"),
        ("grid", "Grid 自适应网格", "ui.layout.grid"),
        ("expander", "Expander 折叠面板", "ui.layout.expander"),
        ("step", "Step 步骤条", "ui.layout.step"),
        ("table", "Table 表格", "ui.layout.table"),
        ("tabs", "Tabs 标签页", "ui.layout.tabs"),
        ("page_layout", "PageLayout 页面布局", "ui.layout.page"),
    ),
    _make(
        "navigation",
        ft.Icons.EXPLORE_OUTLINED,
        ("app_bar", "AppBar 应用栏", "ui.navigation.app_bar"),
        ("menu_bar", "MenuBar 菜单栏", "ui.navigation.menu_bar"),
        ("status_bar", "StatusBar 状态栏", "ui.navigation.status_bar"),
        ("bread_crumb", "BreadCrumb 面包屑", "ui.navigation.bread_crumb"),
        ("menu", "Menu 菜单", "ui.navigation.menu"),
        ("pagination", "Pagination 分页", "ui.navigation.pagination"),
    ),
    _make(
        "form",
        ft.Icons.EDIT_NOTE,
        ("input", "Input 输入框", "ui.input.input"),
        ("number_input", "NumberInput 数字输入", "ui.input.number_input"),
        ("checkbox", "Checkbox 复选框", "ui.input.checkbox"),
        ("switch", "Switch 开关", "ui.input.switch"),
        ("radio", "Radio 单选框", "ui.input.radio"),
        ("select_box", "SelectBox 下拉框", "ui.input.select_box"),
        ("multi_select", "MultiSelect 多选下拉", "ui.input.multi_select"),
        ("cascader", "Cascader 级联选择", "ui.input.cascader"),
        ("transfer", "Transfer 穿梭框", "ui.input.transfer"),
        ("slider", "Slider 滑块", "ui.input.slider"),
        ("rating", "Rating 评分", "ui.input.rating"),
        ("segmented_button", "SegmentedButton 分段按钮", "ui.input.segmented_button"),
        ("date_input", "DateInput 日期选择", "ui.input.date_input"),
        ("datetime_input", "DateTimeInput 日期时间选择", "ui.input.datetime_input"),
        ("color_picker", "ColorPicker 取色器", "ui.input.color_picker"),
        ("search_bar", "SearchBar 搜索框", "ui.input.search_bar"),
        ("search_field", "SearchField 行内搜索框", "ui.input.search_field"),
    ),
    _make(
        "feedback",
        ft.Icons.FEEDBACK_OUTLINED,
        ("message", "Message 消息条", "ui.feedback.message"),
        ("notification", "Notification 通知", "ui.feedback.notification"),
        ("alert_dialog", "AlertDialog 对话框", "ui.feedback.alert_dialog"),
        ("progress_bar", "ProgressBar 进度条", "ui.feedback.progress_bar"),
        ("loading", "Loading 加载", "ui.feedback.loading"),
    ),
    _make(
        "display",
        ft.Icons.TABLE_CHART_OUTLINED,
        ("list_tile", "ListTile 列表项", "ui.display.list_tile"),
        ("descriptions", "Descriptions 描述列表", "ui.display.descriptions"),
        ("kbd", "Kbd 快捷键", "ui.display.kbd"),
        ("carousel", "Carousel 轮播", "ui.display.carousel"),
        ("calendar", "Calendar 日历", "ui.display.calendar"),
        ("heatmap", "Heatmap 热力图", "ui.display.heatmap"),
        ("number_animation", "NumberAnimation 数值动画", "ui.display.number_animation"),
        ("image_grid_view", "ImageGridView 图片网格", "ui.display.image_gridview"),
        ("tree", "Tree 树", "ui.display.tree"),
        ("log_container", "LogContainer 日志容器", "ui.display.log_container"),
    ),
    _make(
        "charts",
        ft.Icons.INSERT_CHART_OUTLINED,
        ("line_chart", "LineChart 折线图", "ui.chart.line_chart"),
        ("area_chart", "AreaChart 面积图", "ui.chart.area_chart"),
        ("bar_chart", "BarChart 柱状图", "ui.chart.bar_chart"),
        ("scatter_chart", "ScatterChart 散点图", "ui.chart.scatter_chart"),
    ),
    _make(
        "upload",
        ft.Icons.UPLOAD_FILE_OUTLINED,
        ("file_picker", "FilePicker 文件选择", "ui.input.file_picker"),
        ("file_dialog", "FileDialog 文件对话框", "ui.input.file_picker"),
        ("dir_picker", "DirPicker 目录选择", "ui.input.file_picker"),
        ("file_saver", "FileSaver 文件保存", "ui.input.file_picker"),
        ("image_picker", "ImagePicker 图片选择", "ui.input.image_picker"),
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
