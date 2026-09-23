"""图表组件。

统一基于 ``flet_charts`` 封装，统一参数风格与默认样式，
并共享 ``ui.chart._data`` 中的数据解析与配色逻辑。
"""

from .bar_chart import BarChart
from .line_chart import LineChart
from .rea_chart import AreaChart
from .scatter_chart import ScatterChart

__all__ = ["AreaChart", "BarChart", "LineChart", "ScatterChart"]
