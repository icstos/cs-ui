"""文档索引：把仓库里的 Markdown 拆成可检索的段落。

为什么不用 FTS/向量库：cs-ui 的文档体量是"几份 Markdown + 示例模块 docstring"，
几百个段落；内存里按标题/正文打分就够快，而且不用在包里塞
SQLite 文件。

段落的 ``location`` 采用 ``文件#一级#二级`` 的形式（如
``README_CN.md#设计令牌与主题#三、令牌``）—— 既是稳定 id，也是人眼能读的路径。
"""

from __future__ import annotations

import json
import re
import textwrap
from pathlib import Path
from typing import Any

from ui_mcp import paths
from ui_mcp.search import rank, tokens

DOC_CHARS_BUDGET = 12_000
_HEADING_RE = re.compile(r"^(#{1,4})\s+(.+?)\s*$")

# 仓库里值得索引的 Markdown（顺序即优先级）
MARKDOWN_FILES = ("README_CN.md", "README.md", "TODO-Roadmap.md")
EXTRA_MARKDOWN_GLOBS = (".workbuddy/memory/*.md", "docs/*.md")

_DOC_WEIGHTS = {"title": 6.0, "path": 4.0, "content": 1.0}


def _slug(title: str) -> str:
    return re.sub(r"\s+", " ", title.strip())


def split_markdown(text: str, relpath: str) -> list[dict[str, Any]]:
    """按标题切段，父子标题拼进 location。"""
    sections: list[dict[str, Any]] = []
    stack: list[tuple[int, str]] = []
    buffer: list[str] = []
    current: dict[str, Any] | None = None

    def flush() -> None:
        nonlocal current, buffer
        if current is None:
            return
        body = "\n".join(buffer).strip()
        if body:
            current["content"] = body
            sections.append(current)
        buffer = []

    for line in text.splitlines():
        match = _HEADING_RE.match(line)
        if match:
            flush()
            level = len(match.group(1))
            title = _slug(match.group(2))
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, title))
            path_parts = [t for _, t in stack]
            current = {
                "location": f"{relpath}#" + "#".join(path_parts),
                "file": relpath,
                "title": title,
                "path": path_parts,
                "level": level,
                "lines": 0,
                "chars": 0,
            }
        else:
            buffer.append(line)

    flush()
    for section in sections:
        section["chars"] = len(section["content"])
        section["lines"] = section["content"].count("\n") + 1
    return sections


def build(root: Path) -> dict[str, Any]:
    sections: list[dict[str, Any]] = []
    files: list[str] = []

    for name in MARKDOWN_FILES:
        path = root / name
        if not path.exists():
            continue
        files.append(name)
        sections.extend(split_markdown(path.read_text(encoding="utf-8"), name))

    for pattern in EXTRA_MARKDOWN_GLOBS:
        for path in sorted(root.glob(pattern)):
            relpath = path.relative_to(root).as_posix()
            if relpath in files:
                continue
            files.append(relpath)
            sections.extend(split_markdown(path.read_text(encoding="utf-8"), relpath))

    # 示例文件的模块 docstring 是"这个例子在演示什么"的原始出处，
    # 但它不在任何 Markdown 里 —— 单独收一段（demo.py 已按主题拆成多个文件）。
    for demo in sorted((root / "examples").glob("*.py")):
        relpath = demo.relative_to(root).as_posix()
        if relpath in files:
            continue
        doc = _module_docstring(demo.read_text(encoding="utf-8"))
        if not doc:
            continue
        files.append(relpath)
        sections.append(
            {
                "location": f"{relpath}#模块 docstring",
                "file": relpath,
                "title": f"{demo.stem} 模块 docstring",
                "path": ["模块 docstring"],
                "level": 1,
                "content": doc,
                "chars": len(doc),
                "lines": doc.count("\n") + 1,
            }
        )

    return {
        "meta": {"generated_by": "ui-mcp", "files": files, "sections": len(sections)},
        "sections": sections,
    }


def _module_docstring(source: str) -> str:
    import ast

    try:
        return (ast.get_docstring(ast.parse(source)) or "").strip()
    except SyntaxError:
        return ""


def _snippet(content: str, query: str, width: int = 400) -> str:
    """取命中行附近的片段；没命中就取开头。"""
    q = set(tokens(query))
    lines = content.splitlines()
    if q:
        for idx, line in enumerate(lines):
            if q & set(tokens(line)):
                start = max(idx - 1, 0)
                chunk = "\n".join(lines[start : start + 6])
                return textwrap.shorten(chunk, width=width, placeholder=" …")
    return textwrap.shorten(content.replace("\n", " "), width=width, placeholder=" …")


class DocsIndex:
    """``data/docs.json`` 的只读查询层。"""

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        self._data = data

    def _load(self) -> dict[str, Any]:
        if self._data is None:
            path = paths.docs_json()
            self._data = (
                json.loads(path.read_text(encoding="utf-8"))
                if path.exists()
                else {"sections": [], "meta": {}}
            )
        return self._data

    def all(self) -> list[dict[str, Any]]:
        return self._load().get("sections", [])

    def outline(self) -> list[dict[str, Any]]:
        return [
            {
                "location": s["location"],
                "title": s["title"],
                "level": s["level"],
                "chars": s["chars"],
            }
            for s in self.all()
        ]

    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        if not query.strip():
            return self.outline()[:limit]
        hits = rank(query, self.all(), _DOC_WEIGHTS, limit, tiebreak="location")
        return [
            {
                "location": s["location"],
                "title": s["title"],
                "file": s["file"],
                "snippet": _snippet(s.get("content") or "", query),
            }
            for _, s in hits
        ]

    def get(self, location: str) -> dict[str, Any]:
        wanted = location.strip().lstrip("#")
        for section in self.all():
            if section["location"] == wanted:
                return self._render(section, section["content"])
        # 容错：允许只给标题（"组件概况"）或只给尾部路径
        loose = [
            s
            for s in self.all()
            if s["title"] == wanted or s["location"].endswith("#" + wanted)
        ]
        if loose:
            return self._render(loose[0], loose[0]["content"])
        candidates = [
            s["location"]
            for s in self.all()
            if wanted.lower() in s["location"].lower()
        ]
        return {
            "error": f"文档段落 '{location}' 不存在",
            "similar": candidates[:10] or [s["location"] for s in self.all()[:10]],
        }

    @staticmethod
    def _render(section: dict[str, Any], content: str) -> dict[str, Any]:
        result = {
            "location": section["location"],
            "title": section["title"],
            "path": section.get("path"),
            "content": content[:DOC_CHARS_BUDGET],
        }
        if len(content) > DOC_CHARS_BUDGET:
            result["note"] = (
                f"已截断：全文 {len(content):,} 字符，这里只给前 "
                f"{DOC_CHARS_BUDGET:,}。改用 search_docs() 缩小范围，"
                "或 get_doc(<更深的 location>) 读子段落。"
            )
        return result
