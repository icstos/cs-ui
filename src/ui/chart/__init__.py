"""图表组件。

统一基于 ``flet_charts`` 封装，统一参数风格与默认样式，
并共享 ``ui.chart._data`` 中的数据解析与配色逻辑。

门面惰性（见 :mod:`ui._lazy`）。这里尤其要紧：``flet_charts`` 的 ``__init__`` 会
连着导入 Matplotlib / Plotly 两个后端（实测多付约 700ms），而我们只用它的
charts 原生 API。惰性门面保证「不用图表就不付这笔钱」。
"""

from ui._lazy import lazy_exports

lazy_exports(
    globals(),
    {
        "AreaChart": ".area_chart",
        "BarChart": ".bar_chart",
        "LineChart": ".line_chart",
        "ScatterChart": ".scatter_chart",
    },
    __name__,
)
