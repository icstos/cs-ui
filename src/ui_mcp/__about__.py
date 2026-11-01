"""包元信息（单独一个模块，避免 ``ui_mcp.server`` 与 ``ui_mcp.__init__`` 循环导入）。"""

from __future__ import annotations

__pkg_name__ = "ui-mcp"
__version__ = "0.1.0"
__all__ = ["__pkg_name__", "__version__"]
