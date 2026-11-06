"""``data/api.json`` 的查询层 + 文本渲染。

设计取舍：
- **默认返回签名式文本**（每个成员一行），不是 JSON —— 同样的信息量，
  少 40% 以上字符，而工具输出会进对话历史、每次调用都要重付一遍 token；
  需要结构化时用 ``format="json"``。
- 成员 docstring 在列表里只留第一句，下钻用 ``member=`` 取全文。
- **继承成员不在组件条目里重复存**，而是通过 ``bases`` 链在查询时合并 ——
  数据结构小，且 `flet.Button` 的成员只有一份。
"""

from __future__ import annotations

import json
import re
from typing import Any

from ui_mcp import paths
from ui_mcp.search import score

_MEMBER_SECTIONS = ("properties", "events", "methods")
_MEMBER_KIND = {"properties": "property", "events": "event", "methods": "method"}

_SUMMARY_CHARS = 130

_SEARCH_WEIGHTS = {
    "name": 10.0,
    "aliases": 7.0,
    "demo_sections": 3.0,
    "summary": 6.0,
    "docstring": 3.0,
    "categories": 3.0,
    "property_names": 4.0,
    "snippets": 2.0,
}

# 事件类型：flet 1.x 写成 Callable[[Event[X]] | Any] | None，也有 EventHandler[X]
_EVENT_INNER_RE = re.compile(r"Event\[([^\[\]]+)\]")


def _first_sentence(text: str | None, limit: int = _SUMMARY_CHARS) -> str:
    if not text:
        return ""
    head = text.strip().split("\n\n", 1)[0].strip()
    for sep in ("。", ". "):
        idx = head.find(sep)
        if 0 < idx < limit:
            head = head[: idx + 1]
            break
    head = " ".join(head.split())
    return head if len(head) <= limit else head[: limit - 1] + "…"


def _member_line(section: str, entry: dict[str, Any]) -> str:
    name = entry.get("name", "")
    if section == "methods":
        line = entry.get("signature") or f"{name}()"
        if entry.get("async"):
            line = "async " + line
    elif section == "events":
        payload = _event_payload(entry.get("type") or "")
        line = f"{name}({payload})" if payload else name
    else:
        line = f"{name}: {entry.get('type') or '?'}"
        if entry.get("default") is not None:
            line += f" = {entry['default']}"
    doc = entry.get("doc") or ""
    if doc:
        line += f" — {_first_sentence(doc)}"
    else:
        docstring = entry.get("docstring") or ""
        if docstring:
            line += f" — {_first_sentence(docstring)}"
    return line


def _event_payload(type_str: str, limit: int = 46) -> str:
    """事件回调收到的参数类型。

    `Callable[[Event[Button]] | Any] | None` 这种声明对调用者是噪音 ——
    有用的只有"回调会被传进来一个 Event[Button]"。取不出来就退回短类型串。
    """
    match = _EVENT_INNER_RE.search(type_str)
    if match:
        return f"Event[{match.group(1)}]"
    for simple in ("ControlEvent", "TapEvent", "ScrollEvent", "RouteChangeEvent"):
        if simple in type_str:
            return simple
    if len(type_str) <= limit:
        return type_str
    return type_str[: limit - 1] + "…"


def render_text(hit: dict[str, Any]) -> str:
    """把 ``get()`` 的结果渲染成紧凑文本。"""
    name = hit.get("name", "")
    lines: list[str] = []

    # 单成员下钻
    if "member" in hit and "member_kind" in hit:
        entry = hit["member"]
        section = next(
            (s for s, k in _MEMBER_KIND.items() if k == hit["member_kind"]),
            "properties",
        )
        lines.append(f"{name}.{entry.get('name')} ({hit['member_kind']})")
        lines.append(_member_line(section, {**entry, "doc": None, "docstring": None}))
        if entry.get("doc"):
            lines.append(entry["doc"])
        elif entry.get("docstring"):
            lines.append(entry["docstring"])
        return "\n".join(lines)

    kind = hit.get("kind", "")
    pattern = hit.get("pattern")
    suffix = f" · {pattern}" if pattern and pattern != kind else ""
    header = f"{name} ({kind}{suffix})"
    summary = hit.get("summary") or _first_sentence(hit.get("docstring"))
    if summary:
        header += f" — {summary}"
    lines.append(header)

    module = hit.get("module")
    if module:
        lines.append(f"module: {module}")
        if hit.get("kind") == "ancestor":
            package = hit.get("package") or module.split(".")[0]
            lines.append(f"import: from {package} import {name}")
        elif hit.get("exported"):
            lines.append(f"import: from ui import {name}")
        else:
            lines.append(f"import: from {module} import {name}")
    if hit.get("aliases"):
        lines.append("aliases: " + ", ".join(hit["aliases"]))
    if hit.get("demo_sections"):
        lines.append("demo 分组: " + "、".join(hit["demo_sections"]))
    if hit.get("internal"):
        lines.append("note: 内部符号（私有模块里的实现细节），一般不该直接用。")

    bases = hit.get("bases")
    if bases:
        lines.append("bases: " + ", ".join(bases))
    if hit.get("deprecated"):
        lines.append(f"DEPRECATED: {hit['deprecated']}")

    # 函数 / 函数组件：签名里的默认值已经足够，不再重复列一遍 args
    if hit.get("kind") in ("function", "component", "hook") and hit.get("signature"):
        lines.append(f"signature: {hit['signature']}")

    # 枚举
    members = hit.get("members")
    if members:
        lines.append(f"members ({len(members)}):")
        for member in members:
            if isinstance(member, dict):
                lines.append(f"  {member.get('name')} = {member.get('value')}")
            else:
                lines.append(f"  {member}")

    usage = hit.get("usage")
    if usage:
        lines.append("usage:")
        lines.extend("  " + line for line in usage.splitlines())

    sites = hit.get("usage_sites") or []
    if sites:
        site = sites[0]
        snippet = (site.get("snippet") or "").strip()
        lines.append(f"real usage — {site['example']} ({site['file']}:{site['line']}):")
        lines.extend("  " + line for line in snippet.splitlines())
        if len(sites) > 1:
            others = ", ".join(s["example"] for s in sites[1:])
            lines.append(f"  (另有 {others} 的用法，见 search_examples)")

    for section in _MEMBER_SECTIONS:
        entries = hit.get(section)
        if not entries:
            continue
        lines.append(f"{section} ({len(entries)}):")
        for entry in entries:
            lines.append("  " + _member_line(section, entry))

    for block in hit.get("inherited") or []:
        if block.get("summary") is not None:
            lines.append(f"from {block['from']}:")
            for section in _MEMBER_SECTIONS:
                for entry in block.get(section) or []:
                    lines.append("  " + _member_line(section, entry))
            continue
        lines.append(
            f"inherited from {block['from']}: "
            f"{block.get('properties', 0)} properties, "
            f"{block.get('events', 0)} events, "
            f"{block.get('methods', 0)} methods"
        )

    notes = hit.get("notes") or []
    for note in notes:
        lines.append(f"note: {note}")

    if hit.get("note"):
        lines.append(f"note: {hit['note']}")
    return "\n".join(lines)


class ApiStore:
    """懒加载 + 名称索引的 API 查询器。"""

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        self._data = data
        self._by_name: dict[str, list[tuple[str, dict[str, Any]]]] | None = None
        self._ancestors: dict[str, dict[str, Any]] | None = None

    # -- 加载 ---------------------------------------------------------

    def _load(self) -> dict[str, Any]:
        if self._data is None:
            path = paths.api_json()
            if not path.exists():
                self._data = {
                    "meta": {"error": "data/api.json 不存在，先跑 ui-mcp build"},
                    "components": [],
                    "types": [],
                    "functions": [],
                    "enums": [],
                    "ancestors": [],
                    "categories": {},
                }
            else:
                self._data = json.loads(path.read_text(encoding="utf-8"))
        if self._by_name is None:
            by_name: dict[str, list[tuple[str, dict[str, Any]]]] = {}
            for bucket in ("components", "types", "functions", "enums"):
                for entry in self._data.get(bucket, []):
                    by_name.setdefault(entry["name"].lower(), []).append((bucket, entry))
            # 别名（`Title` → Header_1、`单选` → Radio）追加在真名之后：
            # 真名永远优先命中，别名只在没撞车时生效。
            for bucket in ("components", "types", "functions", "enums"):
                for entry in self._data.get(bucket, []):
                    for alias in entry.get("aliases") or []:
                        bucket_list = by_name.setdefault(alias.lower(), [])
                        if not any(e is entry for _, e in bucket_list):
                            bucket_list.append((bucket, entry))
            self._by_name = by_name
            self._ancestors = {
                entry["key"].lower(): entry for entry in self._data.get("ancestors", [])
            }
        return self._data

    @property
    def meta(self) -> dict[str, Any]:
        return self._load().get("meta", {})

    @property
    def categories(self) -> dict[str, list[str]]:
        return self._load().get("categories", {})

    def entries(self, bucket: str) -> list[dict[str, Any]]:
        self._load()
        return self._data.get(bucket, [])  # type: ignore[union-attr]

    # -- 浏览 / 检索 --------------------------------------------------

    def list_components(
        self,
        category: str | None = None,
        pattern: str | None = None,
        kind: str | None = None,
        query: str | None = None,
        limit: int = 60,
        include_internal: bool = False,
    ) -> list[dict[str, Any]]:
        items = self.entries("components") + self.entries("types")
        # 函数组件（Table / Pagination / ThemeProvider …）跟类组件一样是"能直接放进
        # controls 的组件"，浏览时不该漏掉。
        items += [f for f in self.entries("functions") if f.get("kind") == "component"]
        out = []
        for entry in items:
            if not include_internal and entry.get("internal"):
                continue
            if kind and entry.get("kind") != kind:
                continue
            if pattern and entry.get("pattern") != pattern:
                continue
            if category and category.lower() not in [c.lower() for c in entry.get("categories", [])]:
                continue
            if query:
                haystack = " ".join(
                    [entry["name"], entry.get("summary") or "", " ".join(entry.get("categories") or [])]
                ).lower()
                if query.lower() not in haystack:
                    continue
            out.append(
                {
                    "name": entry["name"],
                    "kind": entry.get("kind"),
                    "pattern": entry.get("pattern"),
                    "categories": entry.get("categories", []),
                    "summary": entry.get("summary") or "",
                    "module": entry.get("module"),
                }
            )
            if len(out) >= limit:
                break
        return out

    def search(self, query: str, limit: int = 8) -> list[dict[str, Any]]:
        items = []
        for bucket in ("components", "types", "functions", "enums"):
            for entry in self.entries(bucket):
                item = dict(entry)
                item["_bucket"] = bucket
                props = entry.get("properties") or []
                item["property_names"] = " ".join(p.get("name", "") for p in props)
                item["demo_sections"] = " ".join(entry.get("demo_sections") or [])
                # 别名既要参与打分（拼成串），又要留原件供精确命中加分
                item["raw_aliases"] = entry.get("aliases") or []
                item["aliases"] = " ".join(item["raw_aliases"])
                item["snippets"] = " ".join(
                    site.get("snippet", "") for site in entry.get("usage_sites") or []
                )
                items.append(item)

        # 精确命中名字/别名时给硬加分：搜"按钮"必须先把 Button 顶上来，
        # 而不是某个恰好 docstring 里写了"分页按钮"的辅助函数。
        wanted = query.strip().lower()

        def boost(entry: dict[str, Any]) -> float:
            names = [entry["name"].lower()] + [a.lower() for a in entry["raw_aliases"]]
            if wanted in names:
                return 20.0
            if any(name.startswith(wanted) for name in names):
                return 6.0
            return 0.0

        hits = []
        for entry in items:
            base = score(query, entry, _SEARCH_WEIGHTS)
            if base <= 0:
                continue
            hits.append((base + boost(entry), entry))
        hits.sort(key=lambda pair: (-pair[0], pair[1]["name"].lower()))
        return [
            {
                "name": e["name"],
                "kind": e.get("kind"),
                "pattern": e.get("pattern"),
                "module": e.get("module"),
                "summary": e.get("summary") or "",
                "aliases": e["raw_aliases"][:4],
                "internal": bool(e.get("internal")),
                "score": round(score_value, 2),
            }
            for score_value, e in hits[:limit]
        ]

    # -- 单点查询 -----------------------------------------------------

    def _candidates(self, name: str) -> list[tuple[str, dict[str, Any]]]:
        self._load()
        assert self._by_name is not None and self._ancestors is not None
        lowered = name.strip().lower()
        if lowered in self._by_name:
            return self._by_name[lowered]
        if lowered in self._ancestors:
            return [("ancestors", self._ancestors[lowered])]
        # 模块限定名：ui.input.button.Button / flet.Button
        if "." in name:
            prefix, _, cls = name.rpartition(".")
            for bucket, entry in self._by_name.get(cls.lower(), []):
                if (entry.get("module") or "").lower().endswith(prefix.lower()):
                    return [(bucket, entry)]
            for key, entry in self._ancestors.items():
                if key.endswith(lowered):
                    return [("ancestors", entry)]
        return []

    def get(
        self,
        name: str,
        member: str | None = None,
        query: str | None = None,
        include_inherited: bool = True,
    ) -> dict[str, Any] | None:
        cands = self._candidates(name)
        if not cands:
            return None
        bucket, entry = cands[0]
        hit = dict(entry)

        if bucket == "enums":
            if member or query:
                term = member or query or ""
                matches = self.search_enum_members(hit["name"], term, limit=20)
                return {
                    "name": hit["name"],
                    "kind": "enum",
                    "note": (
                        f"{hit['name']} 里匹配 '{term}' 的成员"
                        if matches
                        else f"{hit['name']} 没有匹配 '{term}' 的成员"
                    ),
                    "members": [{"name": m, "value": None} for m in matches],
                }
            return hit

        if member is not None:
            found = self._find_member(hit, member)
            if found is not None:
                return found
            available = [
                e.get("name")
                for section in _MEMBER_SECTIONS
                for e in hit.get(section) or []
            ]
            return {
                "error": f"'{hit['name']}' 没有成员 '{member}'",
                "available_members": available,
            }

        if query is not None:
            hit = self._filter_members(hit, name, query, include_inherited)

        if len(cands) > 1:
            others = "; ".join(
                f"{e.get('module')}.{e.get('name')}" for _, e in cands[1:]
            )
            hit["note"] = f"同名符号还有: {others}（用模块限定名查询）"
        return hit

    def _find_member(self, hit: dict[str, Any], member: str) -> dict[str, Any] | None:
        for section in _MEMBER_SECTIONS:
            for entry in hit.get(section) or []:
                if entry.get("name") == member:
                    return {
                        "name": hit["name"],
                        "kind": hit.get("kind"),
                        "member_kind": _MEMBER_KIND[section],
                        "member": entry,
                    }
        # 继承链里找
        for base_key in hit.get("bases") or []:
            base = self._lookup_base(base_key)
            if base is None:
                continue
            for section in _MEMBER_SECTIONS:
                for entry in base.get(section) or []:
                    if entry.get("name") == member:
                        return {
                            "name": hit["name"],
                            "kind": hit.get("kind"),
                            "member_kind": _MEMBER_KIND[section],
                            "member": {
                                **entry,
                                "docstring": f"（继承自 {base_key}）{entry.get('docstring') or ''}",
                            },
                        }
        return None

    def _lookup_base(self, key: str) -> dict[str, Any] | None:
        self._load()
        assert self._by_name is not None and self._ancestors is not None
        if key.lower() in self._ancestors:
            return self._ancestors[key.lower()]
        for bucket, entry in self._by_name.get(key.lower(), []):
            if bucket in ("components", "types"):
                return entry
        return None

    def _filter_members(
        self,
        hit: dict[str, Any],
        name: str,
        query: str,
        include_inherited: bool,
    ) -> dict[str, Any]:
        q = query.lower()

        def matches(entry: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
            found: dict[str, list[dict[str, Any]]] = {}
            for section in _MEMBER_SECTIONS:
                found[section] = [
                    e for e in entry.get(section) or [] if q in (e.get("name") or "").lower()
                ]
            return found

        out = dict(hit)
        own = matches(hit)
        total = sum(len(v) for v in own.values())
        out.update(own)

        if include_inherited:
            inherited_blocks: list[dict[str, Any]] = []
            visited: set[str] = set()
            queue = list(hit.get("bases") or [])
            while queue:
                key = queue.pop(0)
                if key.lower() in visited:
                    continue
                visited.add(key.lower())
                base = self._lookup_base(key)
                if base is None:
                    continue
                found = matches(base)
                if any(found.values()):
                    inherited_blocks.append({"from": key, "summary": "", **found})
                    total += sum(len(v) for v in found.values())
                queue.extend(base.get("bases") or [])
            if inherited_blocks:
                out["inherited"] = inherited_blocks

        if not total:
            return {
                "error": f"'{name}' 没有名字含 '{query}' 的成员",
                "available_members": [
                    e.get("name") for section in _MEMBER_SECTIONS for e in hit.get(section) or []
                ],
                "hint": "继承来的成员也可以查；实在没有就去 get_guidelines('overview') 看范式。",
            }
        out["note"] = (
            f"只显示名字含 '{query}' 的成员（含继承）。要看全部：get_api('{name}')"
        )
        return out

    # -- 枚举 ---------------------------------------------------------

    def get_enum(self, name: str) -> dict[str, Any] | None:
        for entry in self.entries("enums"):
            if entry["name"].lower() == name.lower():
                return entry
        return None

    def search_enum_members(self, name: str, query: str, limit: int = 10) -> list[str]:
        enum = self.get_enum(name)
        if enum is None:
            return []
        q = query.lower()
        names = [m["name"] for m in enum.get("members") or []]
        matched = [n for n in names if q in n.lower()]

        def tier(n: str) -> tuple[int, int, str]:
            lowered = n.lower()
            rank_ = 0 if lowered == q else 1 if lowered.startswith(q) else 2
            return (rank_, len(n), n)

        return sorted(matched, key=tier)[:limit]

    def enum_has_member(self, name: str, member: str) -> bool:
        enum = self.get_enum(name)
        if enum is None:
            return False
        target = member.lower()
        return any(m["name"].lower() == target for m in enum.get("members") or [])


# 模块级单例：服务进程里只读一次 api.json
api_store = ApiStore()
