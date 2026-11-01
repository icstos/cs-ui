"""ui-mcp —— 给 cs-ui 组件库用的 MCP 服务。

定位与 ``flet-mcp`` 相同：模型对 cs-ui 的记忆必然是过期的、而且是编造的。
本包把**当前安装版本**的 cs-ui API 索引成数据文件，通过 MCP 工具喂给
AI agent，把"猜 API"变成"查 API"。

对外只导出两样东西：

- :data:`mcp` —— FastMCP 实例，可被 ``fastmcp.Client`` 或
  ``pydantic_ai.MCPToolset`` 进程内直接消费；
- :func:`main` —— 命令行入口（``ui-mcp`` / ``python -m ui_mcp``）。

注意：包名 ``ui_mcp`` 与产品名 "ui-mcp" 分开写，理由同 ``ui/__init__.py``
里那条注释 —— 别把产品名塞进 ``__name__``，否则 import 报错会误导人。
"""

from ui_mcp.__about__ import __pkg_name__, __version__
from ui_mcp.server import mcp

__all__ = ["mcp", "main", "__pkg_name__", "__version__"]


def main(argv: list[str] | None = None) -> int:
    """命令行入口（懒导入，避免 ``import ui_mcp`` 时拖进 argparse 等）。"""
    from ui_mcp.cli import main as _main

    return _main(argv)
