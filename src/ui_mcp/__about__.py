"""包元信息（单独一个模块，避免 ``ui_mcp.server`` 与 ``ui_mcp.__init__`` 循环导入）。

版本不在这里写死：``ui-mcp`` 与 ``cs-ui`` 由同一个 ``pyproject.toml`` 发版，
各自维护一个 ``__version__`` 字面量必然漂移（曾经就是 ``ui 0.0.5`` /
``cs-ui 0.1.1`` / ``ui-mcp 0.1.1`` 三个数并存）。统一从 :mod:`ui.version` 取。
"""

from __future__ import annotations

from ui.version import __version__

__pkg_name__ = "ui-mcp"

__all__ = ["__pkg_name__", "__version__"]
