"""示例索引：把 ``examples/demo.py`` 拆成可检索的示例，并回填每个组件的真实用法。

对 AI agent 来说，**一段能跑的调用**比十条属性说明都值钱。所以这里做两件事：

1. 按顶层函数把 demo 切页（``demo/FormPage`` 等），保留源码、路由、用到的组件；
2. 反向扫一遍所有示例文件里的构造调用，给每个组件挂上
   ``usage_sites``（示例 id + 行号 + 调用片段），让 ``get_api("SelectBox")``
   直接能看到"别人是怎么用的"。

纯 AST 解析，不 import 示例文件 —— 示例会调 ``ft.run``，导入即挂窗口。
"""

from __future__ import annotations

import ast
import json
import re
import textwrap
from pathlib import Path
from typing import Any

from ui_mcp import paths
from ui_mcp.search import rank

MAX_SNIPPET_LINES = 12
MAX_USAGE_SITES = 3
MAX_FILE_EXAMPLE_LINES = 400

_ROUTE_RE = re.compile(
    r"ft\.Route\(\s*(?:(?:index\s*=\s*True[^)]*component\s*=\s*(\w+))"
    r"|(?:path\s*=\s*[\"']([^\"']+)[\"'][^)]*component\s*=\s*(\w+)))",
    re.S,
)

# demo 里用这些包装函数给一组控件写中文标题：
#   section("按钮", "说明", Button(...), Chip(...))
# 把标题当作组件的中文关键词收集起来 —— 这是"按钮"能搜到 Button 的唯一线索。
_LABEL_WRAPPERS = {"section", "panel", "labeled", "showcase", "group"}

_EXAMPLE_WEIGHTS = {
    "title": 8.0,
    "summary": 5.0,
    "docstring": 4.0,
    "components": 5.0,
    "route": 3.0,
    "code": 1.0,
}


# ---------------------------------------------------------------------------
# 构建
# ---------------------------------------------------------------------------


def _routes(source: str) -> dict[str, str]:
    """从 ``ROUTES = [ft.Route(...)]`` 里抠出「组件名 → 路由」。"""
    mapping: dict[str, str] = {}
    for match in _ROUTE_RE.finditer(source):
        index_component, path, component = match.groups()
        if index_component:
            mapping[index_component] = "/"
        elif component:
            mapping[component] = "/" + (path or "")
    return mapping


def _called_names(node: ast.AST) -> list[str]:
    names: list[str] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            func = child.func
            if isinstance(func, ast.Name):
                names.append(func.id)
            elif isinstance(func, ast.Attribute):
                names.append(func.attr)
    return names


def _snippet(source_lines: list[str], call: ast.Call) -> str:
    start = call.lineno - 1
    end = getattr(call, "end_lineno", call.lineno)
    lines = source_lines[start:end]
    if len(lines) > MAX_SNIPPET_LINES:
        lines = lines[:MAX_SNIPPET_LINES] + ["    …"]
    return textwrap.dedent("\n".join(lines)).rstrip()


def _top_level_nodes(tree: ast.Module) -> list[ast.AST]:
    return [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    ]


def _node_start(node: ast.AST) -> int:
    decorators = getattr(node, "decorator_list", []) or []
    starts = [node.lineno] + [d.lineno for d in decorators]
    return min(starts)


def _is_component(node: ast.AST) -> bool:
    for dec in getattr(node, "decorator_list", []) or []:
        target = dec.func if isinstance(dec, ast.Call) else dec
        name = target.attr if isinstance(target, ast.Attribute) else getattr(target, "id", "")
        if name == "component":
            return True
    return False


def _parent_map(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    parents: dict[ast.AST, ast.AST] = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node
    return parents


def _enclosing_label(call: ast.Call, parents: dict[ast.AST, ast.AST]) -> str | None:
    """往上找最近的 ``section("标题", ...)`` 之类的包装，取它的中文标题。"""
    node = parents.get(call)
    for _ in range(8):
        if node is None:
            return None
        if isinstance(node, ast.Call):
            func = node.func
            name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", "")
            if name in _LABEL_WRAPPERS and node.args:
                first = node.args[0]
                if isinstance(first, ast.Constant) and isinstance(first.value, str):
                    return first.value.strip()
        node = parents.get(node)
    return None


def build(root: Path, known_names: set[str]) -> dict[str, Any]:
    """扫描 ``examples/`` 目录，生成示例索引 + 组件用法回填表。"""
    examples: list[dict[str, Any]] = []
    usage: dict[str, list[dict[str, Any]]] = {}
    files: list[Path] = []

    demo = root / "examples" / "demo.py"
    if demo.exists():
        files.append(demo)
    for path in sorted((root / "examples").glob("*.py")):
        if path.name != "demo.py":
            files.append(path)

    for path in files:
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (OSError, SyntaxError):
            continue
        lines = source.splitlines()
        relpath = path.relative_to(root).as_posix()
        routes = _routes(source) if path.name == "demo.py" else {}

        nodes = _top_level_nodes(tree)
        for node in nodes:
            start, end = _node_start(node), getattr(node, "end_lineno", node.lineno)
            code = "\n".join(lines[start - 1 : end])
            docstring = ast.get_docstring(node) or ""
            name = getattr(node, "name", "")
            called = [n for n in _called_names(node) if n in known_names]
            unique_called = list(dict.fromkeys(called))
            route = routes.get(name)
            kind = (
                "app"
                if name in ("App", "main")
                else "page"
                if route or name.endswith("Page")
                else "helper"
            )
            examples.append(
                {
                    "id": f"{path.stem}/{name}",
                    "title": name,
                    "kind": kind,
                    "file": relpath,
                    "line": start,
                    "route": route,
                    "summary": _first_line(docstring),
                    "docstring": docstring,
                    "components": unique_called,
                    "tags": [c.lower() for c in unique_called][:20],
                    "count": len(called),
                    "code": code,
                }
            )

        # 用法回填：只认 cs-ui 组件/函数的构造调用
        parents = _parent_map(tree)
        for call in [n for n in ast.walk(tree) if isinstance(n, ast.Call)]:
            func = call.func
            target = func.id if isinstance(func, ast.Name) else None
            if target not in known_names:
                continue
            sites = usage.setdefault(target, [])
            example_id = _enclosing_example(examples, relpath, call.lineno)
            if example_id is None or any(s["example"] == example_id for s in sites):
                continue
            if len(sites) >= MAX_USAGE_SITES:
                continue
            sites.append(
                {
                    "example": example_id,
                    "file": relpath,
                    "line": call.lineno,
                    "label": _enclosing_label(call, parents),
                    "snippet": _snippet(lines, call),
                }
            )

        # 独立的小脚本整文件作为一个示例（>400 行的不收，价值低于成本）
        if path.name != "demo.py" and len(lines) <= MAX_FILE_EXAMPLE_LINES:
            examples.append(
                {
                    "id": f"file/{path.name}",
                    "title": path.stem,
                    "kind": "script",
                    "file": relpath,
                    "line": 1,
                    "route": None,
                    "summary": _first_line(ast.get_docstring(tree) or ""),
                    "docstring": ast.get_docstring(tree) or "",
                    "components": sorted(
                        {n for n in _called_names(tree) if n in known_names}
                    )[:20],
                    "tags": [],
                    "count": 0,
                    "code": source,
                }
            )

    return {
        "meta": {
            "generated_by": "ui-mcp",
            "files": [p.relative_to(root).as_posix() for p in files],
            "examples": len(examples),
            "usage_components": len(usage),
        },
        "examples": examples,
        "usage": usage,
    }


def _first_line(text: str) -> str:
    return (text.strip().splitlines() or [""])[0].strip()


def _enclosing_example(
    examples: list[dict[str, Any]], relpath: str, line: int
) -> str | None:
    best: dict[str, Any] | None = None
    for example in examples:
        if example["file"] != relpath:
            continue
        span = example["code"].count("\n") + 1
        if example["line"] <= line < example["line"] + span:
            if best is None or example["line"] > best["line"]:
                best = example
    return best["id"] if best else None


# ---------------------------------------------------------------------------
# 查询
# ---------------------------------------------------------------------------


class ExamplesIndex:
    """``data/examples.json`` 的只读查询层（懒加载）。"""

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        self._data = data

    def _load(self) -> dict[str, Any]:
        if self._data is None:
            path = paths.examples_json()
            self._data = (
                json.loads(path.read_text(encoding="utf-8"))
                if path.exists()
                else {"examples": [], "usage": {}, "meta": {}}
            )
        return self._data

    @property
    def usage(self) -> dict[str, list[dict[str, Any]]]:
        return self._load().get("usage", {})

    def all(self) -> list[dict[str, Any]]:
        return self._load().get("examples", [])

    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        hits = rank(query, self.all(), _EXAMPLE_WEIGHTS, limit, tiebreak="title")
        return [
            {
                "id": e["id"],
                "title": e["title"],
                "kind": e["kind"],
                "route": e.get("route"),
                "file": f"{e['file']}:{e['line']}",
                "summary": e.get("summary") or "",
                "components": e.get("components", [])[:8],
                "chars": len(e.get("code") or ""),
            }
            for _, e in hits
        ]

    def get(
        self,
        example_id: str,
        start_line: int | None = None,
        max_lines: int | None = None,
    ) -> dict[str, Any]:
        """取示例源码；长示例可用 ``start_line`` 起、``max_lines`` 行分页读。"""
        for example in self.all():
            if example["id"].lower() != example_id.lower():
                continue
            code = example.get("code") or ""
            lines = code.splitlines()
            if start_line or max_lines:
                first = max((start_line or 1) - 1, 0)
                window = lines[first : first + (max_lines or len(lines))]
                return {
                    **{k: v for k, v in example.items() if k != "code"},
                    "start_line": first + 1,
                    "total_lines": len(lines),
                    "code": "\n".join(window),
                    "note": (
                        f"第 {first + 1}-{first + len(window)} 行 / 共 {len(lines)} 行。"
                        "继续读请再调 get_example(start_line=...) 或先看组件级用法。"
                    ),
                }
            return {k: v for k, v in example.items()}
        return {
            "error": f"示例 '{example_id}' 不存在",
            "available": [e["id"] for e in self.all()][:20],
        }
