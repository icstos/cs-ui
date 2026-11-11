"""布局类组件：容器、栅格、标签页、步骤条、页面骨架等。

门面惰性（见 :mod:`ui._lazy`）：拿一个 ``Card`` 不会连带加载表格、标签页、步骤条。
"""

from ui._lazy import lazy_exports

lazy_exports(
    globals(),
    {
        "Card": ".card",
        "Column": ".column",
        "Container": ".container",
        "Divider": ".divider",
        "VerticalDivider": ".divider",
        "Expander": ".expander",
        "FormRow": ".form_row",
        "GridView": ".grid_view",
        "Grid": ".grid",
        "ListView": ".list_view",
        "MetricCard": ".metric_card",
        "PageLayout": ".page",
        "Row": ".row",
        "Stack": ".stack",
        "Step": ".step",
        "StepItem": ".step",
        "Table": ".table",
        "TableState": ".table",
        "Tab": ".tabs",
        "TabBar": ".tabs",
        "TabBarView": ".tabs",
        "Tabs": ".tabs",
    },
    __name__,
)
