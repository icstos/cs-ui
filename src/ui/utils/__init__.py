"""工具类组件：代码编辑器、代码查看器。

门面惰性（见 :mod:`ui._lazy`）：``CodeView`` 是纯 flet 实现，不该陪着
``flet_code_editor`` 一起加载。
"""

from ui._lazy import lazy_exports

lazy_exports(
    globals(),
    {
        "CodeEditor": ".code_editor",
        "CodeView": ".code_view",
    },
    __name__,
)
