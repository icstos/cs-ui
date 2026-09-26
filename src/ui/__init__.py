from .ft_init import *
from flet import *
from flet import canvas

from .chart import *
from .core import *
from .display import *
from .feedback import *
from .input import *
from .layout import *
from .navigation import *
from .utils import *

from .app import App


# 手动
# ⚠️ 不要在这里写 `__name__ = "cs-ui"`。
# `from ui import X` 在 X 不存在时，CPython 的 _handle_fromlist 会用
# `f"{module.__name__}.{X}"` 去 import 子模块；一旦 __name__ 被改成 "cs-ui"，
# 报错就变成极具误导性的 `ModuleNotFoundError: No module named 'cs-ui'`，
# 真正缺失的名字（例如已下线的 ECharts）完全看不出来。
# 产品名放独立字段，别占用 __name__。
__pkg_name__ = "cs-ui"
__version__ = "0.0.5"
__author__ = "Shawn Chen"
__email__ = "cs@cstos.com"
__copyright__ = "Shawn Chen"
__description__ = ""
__url__ = "https://github.com/icstos/cs-ui"
