"""CS UI —— 基于 flet 的组件库。

导入策略（**改前先读**，这里的取舍是实测结论）：

``import ui`` 只加载 ``flet`` 本身，组件在第一次被访问时才导入所属子包。
历史写法是 ``from .ft_init import *`` + ``from flet import *`` + 各子包 star-import，
实测总耗时 1.4~1.6s，其中绝大部分是「用不到也得付」的钱：

- ``ui.chart`` → ``flet_charts`` → matplotlib + plotly                  ~0.62s
- ``ft_init`` 的 536 个 ``ft.X = ...`` 逐属性反射（触发 flet 懒导入全部子模块） ~0.59s
- 其余子包（display / feedback / input / layout / navigation / utils）  ~0.18s

而 ``import flet`` 本身只要 0.19s。也就是说，「用一次 ui 就要先烧掉 1.4s」对一个
桌面应用的启动关键路径是灾难（CSearch 实测首帧因此晚约 1.4s）。

现在改成 PEP 562 模块级 ``__getattr__``：

1. ``ui.X`` 首次被访问 → 按 ``_registry.COMPONENT_MODULES`` 导入所属子包并缓存到
   ``globals()``，此后就是普通属性查找；
2. ``ui.<子包名>`` → 直接返回 ui 自己的子模块（**必须先于 flet 判断**：flet 的
   ``__all__`` 里也有 ``utils`` / ``input`` / ``icons`` 这类同名项，覆盖顺序必须和
   原来的 star-import 一致：ui 的子包赢）；
3. 其余交给 ``flet`` —— 等价于原先 ``ft_init`` 提供的 536 个别名，但只在用到时反射。

``dir(ui)`` 仍返回完整名字表（含未加载的），IDE 补全与 ``from ui import *`` 行为不变。
新增 / 删除组件后必须重新生成注册表：``python scripts/gen_ui_registry.py``。
"""

from __future__ import annotations

import importlib
from typing import Any as _Any

import flet as flet

from ._registry import COMPONENT_MODULES as _COMPONENT_MODULES
from .version import FLET_MIN as FLET_MIN
from .version import FLET_SERIES as FLET_SERIES
from .version import FLET_VERSION as FLET_VERSION
from .version import require_flet as require_flet

#: 公共别名：README 里 ``from ui import ft`` 取的就是 flet 模块本身
ft = flet

# 版本守卫：装错 flet 时把问题说清楚，而不是在若干层之后抛 AttributeError。
# 这里用 ``strict=False`` —— 跨版本系列只警告不中断（同系列补丁版行为一致），
# 需要硬门槛的应用自己调 ``require_flet()``。
require_flet(strict=False)

#: ui 自己的子模块（``ui.layout`` 等）。必须显式登记：flet 的 ``__all__`` 里也有
#: 同名项（``utils`` / ``icons`` / ``padding`` …），不能靠「flet 没有再试子模块」判定。
_SUBMODULES: tuple[str, ...] = (
    "app",
    "chart",
    "cli",
    "components",
    "core",
    "display",
    "feedback",
    "ft_init",
    "input",
    "layout",
    "navigation",
    "utils",
)

#: 不属于任何子包 ``__all__``、但曾经由 star-import 暴露出来的名字
_EXTRA_LAZY: dict[str, str] = {"App": "ui.app"}

#: 惰性求值的模块级属性。``__version__`` 要读安装元数据（首次约 37ms），
#: 而 `import ui` 本身并不需要它 —— 只有显示版本号的地方（关于页 / CLI）才触发。
#: 不进 ``__all__``：star-import 一直不带下划线名字，这里保持原样。
_LATE_ATTRS: dict[str, str] = {"__version__": "ui.version"}

#: flet 的**子模块**（不是 ``__all__`` 里的名字，`getattr(flet, ...)` 拿不到）。
#: 原先用 ``from flet import canvas`` 显式导入，光这一行就要 85ms（flet.canvas 会拖进
#: 一整套绘图控件），改成用到时再导入。
_FLET_SUBMODULES: tuple[str, ...] = ("canvas",)


def __getattr__(name: str) -> _Any:
    """按需加载 ``ui.<name>``（PEP 562）。

    顺序不可调换：ui 子模块 → ui 组件 → flet 名字。调换会让 ``ui.utils`` 变成
    ``flet.utils``、``ui.input`` 变成 ``flet.input``（flet 的 ``__all__`` 就带着这些
    子模块名），而这两个名字在改造前指向的是 ui 自己的子包。
    """
    if name in _SUBMODULES:
        value: _Any = importlib.import_module(f"{__name__}.{name}")
    elif name in _FLET_SUBMODULES:
        value = importlib.import_module(f"flet.{name}")
    else:
        module_path = (
            _COMPONENT_MODULES.get(name)
            or _EXTRA_LAZY.get(name)
            or _LATE_ATTRS.get(name)
        )
        if module_path is not None:
            value = getattr(importlib.import_module(module_path), name)
        else:
            try:
                value = getattr(flet, name)
            except AttributeError:
                raise AttributeError(
                    f"module {__name__!r} has no attribute {name!r}"
                ) from None
    globals()[name] = value  # 缓存：后续访问不再走 __getattr__
    return value


def __dir__() -> list[str]:
    """完整名字表（含尚未加载的），供 IDE 补全与 ``from ui import *`` 使用。"""
    return sorted(
        {
            *globals(),
            *_COMPONENT_MODULES,
            *_EXTRA_LAZY,
            *_SUBMODULES,
            *_FLET_SUBMODULES,
            *flet.__all__,
        }
    )


# ``from ui import *`` 的导出面 = 改造前 star-import 的并集：
# flet 全部公开名 + ft_init 的 536 个别名（⊆ flet.__all__）+ 各子包 __all__
# + 子模块名 + 'ft'
# 由几份来源拼成并集，ruff 静态看不到里面的元素类型
__all__ = [  # noqa: PLE0604
    *sorted(
        {
            *flet.__all__,
            *_COMPONENT_MODULES,
            *_EXTRA_LAZY,
            *_SUBMODULES,
            *_FLET_SUBMODULES,
            "ft",
        }
    )
]


# 手动
# ⚠️ 不要在这里写 `__name__ = "cs-ui"`。
# `from ui import X` 在 X 不存在时，CPython 的 _handle_fromlist 会用
# `f"{module.__name__}.{X}"` 去 import 子模块；一旦 __name__ 被改成 "cs-ui"，
# 报错就变成极具误导性的 `ModuleNotFoundError: No module named 'cs-ui'`，
# 真正缺失的名字（例如已下线的 ECharts）完全看不出来。
# 产品名放独立字段，别占用 __name__。
__pkg_name__ = "cs-ui"
# ``__version__`` / ``FLET_VERSION`` / ``FLET_MIN`` 由 ``ui.version`` 提供（见文件顶部
# 的导入）—— 版本只允许有一个事实源，别在这里再写一遍字面量。
__author__ = "Shawn Chen"
__email__ = "cs@cstos.com"
__copyright__ = "Shawn Chen"
__description__ = ""
__url__ = "https://github.com/icstos/cs-ui"
