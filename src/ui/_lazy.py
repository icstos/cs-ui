"""子包门面的惰性化（PEP 562）—— 一份实现，各子包共用。

为什么门面必须惰性
------------------
``import ui.navigation.menu`` 会**先执行** ``ui/navigation/__init__.py``。门面里写着
``from .app_bar import AppBar``，于是「拿一个菜单」被迫把应用栏、面包屑、分页一起
加载 —— 实测 ``ui.navigation`` 门面 95ms 里有 74ms 花在调用方根本没碰的模块上。

``__getattr__`` 把导入推迟到**第一次真正取值**：

* ``from ui.navigation import Menu`` → 只导入 ``ui.navigation.menu``；
* ``from ui.navigation import *`` → 仍按 ``__all__`` 逐个取值（真要全部时才付钱）；
* ``dir()`` / IDE 补全 → 名字齐全：``__dir__`` 看的是**登记表**，不是"已加载"。

约束
----
``__all__`` 由登记表推导，**不再手写**。手写两份必然漂移，本项目已经漂过一次
（``ui/theme.py`` 删掉后 ``_SUBMODULES`` 里还留着它）。新增组件只改登记表一处。
"""

from __future__ import annotations

import importlib
from typing import Any

__all__ = ["lazy_exports"]


def lazy_exports(
    namespace: dict[str, Any],
    origin: dict[str, str],
    package: str,
) -> None:
    """把 ``origin``（名字 → 子模块相对路径）装成模块级惰性导出。

    Args:
        namespace: 子包 ``__init__`` 的 ``globals()``。函数会往里面写
            ``__getattr__`` / ``__dir__`` / ``__all__``。
        origin: ``{"Menu": ".menu", ...}``。值是 ``importlib`` 的相对模块路径。
        package: 子包自身的 ``__name__``（``"ui.navigation"``）。

    取值成功后会把结果**缓存在子包命名空间**里，之后的访问是一次普通属性查找，
    不再经过 ``__getattr__`` —— 惰性只付第一次的钱。
    """
    cache: dict[str, Any] = namespace

    def __getattr__(name: str) -> Any:
        relative = origin.get(name)
        if relative is not None:
            value: Any = getattr(importlib.import_module(relative, package), name)
        else:
            # 兜底：``ui.navigation.menu`` 这种"取子模块本身"的写法。
            try:
                value = importlib.import_module(f".{name}", package)
            except ModuleNotFoundError:
                raise AttributeError(
                    f"module {package!r} has no attribute {name!r}"
                ) from None
        cache[name] = value
        return value

    def __dir__() -> list[str]:
        return sorted({*cache, *origin})

    namespace["__getattr__"] = __getattr__
    namespace["__dir__"] = __dir__
    namespace["__all__"] = sorted(origin)
