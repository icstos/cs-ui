"""构建索引：``ui-mcp build`` 的实现。

产物三份（都落在 ``src/ui_mcp/data/``）：

- ``api.json``      组件 / 数据类 / 函数 / 枚举 + 外部祖先类的成员表
- ``examples.json`` demo 拆页 + 每个组件的真实用法片段
- ``docs.json``     Markdown 切段

构建期会 import ``ui``（拿到当前安装版本的真实签名），服务期只读 JSON。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ui_mcp import aliases, docs, examples, introspect, paths


def _write(path: Path, data: dict[str, Any]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    path.write_text(text, encoding="utf-8")
    return len(text)


def build(
    root: Path | None = None,
    *,
    with_examples: bool = True,
    with_docs: bool = True,
) -> dict[str, Any]:
    """重建全部索引，返回一份摘要（供 CLI 打印 / 单测断言）。"""
    project = root or paths.project_root()
    if project is None:
        raise RuntimeError(
            "找不到 cs-ui 仓库根目录（需要同时存在 src/ui 与 examples/）。"
            "用 --root 指定，或设置 UI_MCP_ROOT。"
        )

    api = introspect.scan()
    known = {
        entry["name"]
        for bucket in ("components", "types", "functions", "enums")
        for entry in api[bucket]
    }

    # 中文别名：手写表 + 源码里的别名（`Title = Header_1`）
    for bucket in ("components", "types", "functions", "enums"):
        for entry in api[bucket]:
            extra = aliases.for_name(entry["name"])
            if extra:
                merged = list(dict.fromkeys([*(entry.get("aliases") or []), *extra]))
                entry["aliases"] = merged

    summary: dict[str, Any] = {"root": str(project), "files": {}}

    if with_examples:
        example_data = examples.build(project, known)
        usage = example_data["usage"]
        for bucket in ("components", "types", "functions", "enums"):
            for entry in api[bucket]:
                sites = usage.get(entry["name"])
                if not sites:
                    continue
                entry["usage_sites"] = sites
                labels = [s["label"] for s in sites if s.get("label")]
                if labels:
                    entry["demo_sections"] = list(dict.fromkeys(labels))[:6]
        summary["files"]["examples.json"] = _write(paths.examples_json(), example_data)
        summary["examples"] = len(example_data["examples"])
        summary["usage_components"] = len(usage)

    if with_docs:
        doc_data = docs.build(project)
        summary["files"]["docs.json"] = _write(paths.docs_json(), doc_data)
        summary["docs"] = len(doc_data["sections"])

    summary["files"]["api.json"] = _write(paths.api_json(), api)
    summary["meta"] = api["meta"]
    return summary


def staleness(root: Path | None = None) -> dict[str, Any]:
    """索引是否落后于源码（只比 mtime，够用且极快）。"""
    project = root or paths.project_root()
    api_path = paths.api_json()
    if not api_path.exists():
        return {"ok": False, "reason": "data/api.json 还没生成，先跑 `ui-mcp build`"}
    if project is None:
        return {"ok": True, "reason": "找不到仓库根目录，跳过新鲜度检查"}

    index_mtime = api_path.stat().st_mtime
    watched: list[Path] = []
    for pattern in ("src/ui/**/*.py", "examples/demo.py", "README_CN.md", "README.md"):
        watched.extend(project.glob(pattern))
    stale = [
        path.relative_to(project).as_posix()
        for path in watched
        if path.is_file() and path.stat().st_mtime > index_mtime
    ]
    return {
        "ok": not stale,
        "index_mtime": api_path.stat().st_mtime,
        "stale_sources": stale[:10],
        "reason": (
            "索引已是最新"
            if not stale
            else f"{len(stale)} 个文件比索引新，建议重跑 `ui-mcp build`"
        ),
    }
