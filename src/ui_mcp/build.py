"""构建索引：``ui-mcp build`` 的实现。

产物三份（都落在 ``src/ui_mcp/data/``）：

- ``api.json``      组件 / 数据类 / 函数 / 枚举 / 令牌常量 + 外部祖先类的成员表
- ``examples.json`` demo 拆页 + 每个组件的真实用法片段
- ``docs.json``     Markdown 切段

构建期会 import ``ui``（拿到当前安装版本的真实签名），服务期只读 JSON。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ui_mcp import aliases, docs, examples, introspect, paths

#: 索引的输入：任一文件比 ``api.json`` 新，索引就算过期。
#: ``examples/**`` 必须整目录盯住 —— 示例早已从单个 demo.py 拆成 test_*.py，
#: 只盯 ``examples/demo.py``（那个文件已经不存在）等于没盯。
WATCHED_GLOBS = (
    "src/ui/**/*.py",
    "examples/**/*.py",
    "README_CN.md",
    "README.md",
    "TODO-Roadmap.md",
    ".workbuddy/memory/*.md",
)


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
    for bucket in ("components", "types", "functions", "enums", "constants"):
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


def _runtime_versions() -> dict[str, str]:
    """当前环境里 ``ui`` / ``flet`` 的版本（导入失败就留空）。"""
    versions: dict[str, str] = {}
    try:
        # 只在 check 时导入，服务期不需要
        import ui

        versions["ui"] = str(getattr(ui, "__version__", "") or "")
    except Exception:
        versions["ui"] = ""
    try:
        import flet as ft

        versions["flet"] = str(getattr(ft, "__version__", "") or "")
    except Exception:
        versions["flet"] = ""
    return versions


def staleness(root: Path | None = None) -> dict[str, Any]:
    """索引是否落后于源码（mtime）+ 版本是否漂移（ui / flet）。

    两件事都要查：``pip install -e`` 的源码改动会改 mtime，但**升级 flet**
    换的是 site-packages，仓库里的文件一个都没动 —— 只比 mtime 会漏掉
    "索引按 1.1.0 生成、运行时是 1.1.2"这种最隐蔽的过期。
    """
    project = root or paths.project_root()
    api_path = paths.api_json()
    if not api_path.exists():
        return {"ok": False, "reason": "data/api.json 还没生成，先跑 `ui-mcp build`"}
    if project is None:
        return {"ok": True, "reason": "找不到仓库根目录，跳过新鲜度检查"}

    index_mtime = api_path.stat().st_mtime
    watched: list[Path] = []
    for pattern in WATCHED_GLOBS:
        watched.extend(project.glob(pattern))
    stale = sorted(
        path.relative_to(project).as_posix()
        for path in watched
        if path.is_file() and path.stat().st_mtime > index_mtime
    )

    meta = json.loads(api_path.read_text(encoding="utf-8")).get("meta", {})
    indexed = {"ui": str(meta.get("version") or ""), "flet": str(meta.get("flet") or "")}
    runtime = _runtime_versions()
    drift = {
        name: (indexed.get(name), runtime.get(name))
        for name in ("ui", "flet")
        if runtime.get(name) and indexed.get(name) != runtime.get(name)
    }

    reasons = []
    if stale:
        reasons.append(f"{len(stale)} 个文件比索引新")
    if drift:
        reasons.append(
            "版本漂移：" + "、".join(f"{k} 索引 {a} / 运行 {b}" for k, (a, b) in drift.items())
        )
    return {
        "ok": not stale and not drift,
        "index_mtime": index_mtime,
        "stale_sources": stale[:10],
        "versions": {"index": indexed, "runtime": runtime},
        "version_drift": drift,
        "reason": "索引已是最新" if not reasons else "；".join(reasons) + "，建议重跑 `ui-mcp build`",
    }
