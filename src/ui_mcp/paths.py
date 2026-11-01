"""路径解析：源码根目录、数据目录、索引文件位置。

构建期（``ui-mcp build``）需要读 ``src/ui`` 与 ``examples/``；
服务期只读 ``ui_mcp/data/*.json``，不碰源码、不 import ``ui``。
"""

from __future__ import annotations

import os
from pathlib import Path

_MARKERS = ("pyproject.toml", "src/ui", "examples")


def data_dir() -> Path:
    """随包分发的数据目录（构建产物落在里面）。"""
    return Path(__file__).resolve().parent / "data"


def api_json() -> Path:
    return data_dir() / "api.json"


def examples_json() -> Path:
    return data_dir() / "examples.json"


def docs_json() -> Path:
    return data_dir() / "docs.json"


def ui_source_dir() -> Path | None:
    """``ui`` 包的源码目录（``import ui`` 能解析时才返回）。"""
    try:
        import ui
    except Exception:
        return None
    paths = list(getattr(ui, "__path__", []) or [])
    return Path(paths[0]) if paths else None


def project_root(explicit: str | Path | None = None) -> Path | None:
    """cs-ui 仓库根目录（含 ``src/ui`` 与 ``examples``）。

    解析顺序：显式参数 → ``UI_MCP_ROOT`` 环境变量 → 从 ``ui`` 源码目录上溯
    → 从本文件上溯（``src/ui_mcp/paths.py`` → 仓库根）。
    """
    if explicit is not None:
        return Path(explicit).resolve()
    env = os.getenv("UI_MCP_ROOT")
    if env:
        return Path(env).resolve()

    candidates: list[Path] = []
    src = ui_source_dir()
    if src is not None:
        # src/ui -> 仓库根
        candidates.extend([src.parent.parent, src.parent])
    here = Path(__file__).resolve()
    # src/ui_mcp -> src -> 仓库根
    candidates.extend([here.parent.parent.parent, here.parent.parent])

    for cand in candidates:
        if all((cand / marker).exists() for marker in _MARKERS):
            return cand
    for cand in candidates:
        if (cand / "examples").is_dir():
            return cand
    return None
