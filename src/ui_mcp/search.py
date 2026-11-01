"""轻量检索：分词 + 加权打分。

索引只有几百条（84 个组件、11 个示例页、几十个文档段），用不上 SQLite FTS：
内存里算一次分数就是微秒级，还省掉了随包分发二进制库文件。

中文没有空格，词表也无法预知，所以做法是 **ASCII 词 + 单个汉字 + 汉字二元组**
一起进索引：查 "表格分页" 时，二元组「表格」「格分」「分页」都能命中，
不会因为用户没写全整句而搜不到。
"""

from __future__ import annotations

import re
from typing import Any, Iterable

_ASCII_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_.]*|\d+")
_CJK_RE = re.compile(r"[\u4e00-\u9fff]")
_STOPWORDS = {
    "the", "a", "an", "of", "to", "for", "and", "or", "in", "on", "is", "it",
    "how", "do", "i", "use", "with", "my", "me", "what", "which", "this", "that",
    "的", "了", "是", "在", "和", "与", "怎", "么", "样", "如", "何",
}


def tokens(text: str) -> list[str]:
    """分词：ASCII 词（小写）+ 汉字单字 + 汉字相邻二元组。"""
    if not text:
        return []
    lowered = text.lower()
    out: list[str] = [t for t in _ASCII_RE.findall(lowered)]
    cjk = _CJK_RE.findall(lowered)
    out.extend(cjk)
    out.extend(a + b for a, b in zip(cjk, cjk[1:]))
    return [t for t in out if t not in _STOPWORDS]


def score(query: str, entry: dict[str, Any], weights: dict[str, float]) -> float:
    """按 ``weights``（字段名 → 权重）给单条记录打分，0 表示不相关。"""
    q_tokens = tokens(query)
    if not q_tokens:
        return 0.0
    total = 0.0
    for field, weight in weights.items():
        value = entry.get(field)
        if not value:
            continue
        if isinstance(value, (list, tuple)):
            haystack = " ".join(str(v) for v in value)
        else:
            haystack = str(value)
        field_tokens = set(tokens(haystack))
        hits = sum(1 for t in q_tokens if t in field_tokens)
        if not hits:
            # 子串兜底：查 "ColorPicker" 这种完整标识符时，分词可能错过长词
            if query.lower() in haystack.lower():
                total += weight * len(q_tokens) * 0.5
            continue
        total += weight * hits / len(q_tokens)
    return total


def rank(
    query: str,
    entries: Iterable[dict[str, Any]],
    weights: dict[str, float],
    limit: int,
    *,
    tiebreak: str | None = None,
) -> list[tuple[float, dict[str, Any]]]:
    """打分排序，返回 ``[(score, entry)]``；同分时按 ``tiebreak`` 字段名排序。"""
    scored = [(score(query, e, weights), e) for e in entries]
    scored = [(s, e) for s, e in scored if s > 0]
    scored.sort(
        key=lambda pair: (
            -pair[0],
            str(pair[1].get(tiebreak or "name", "")).lower(),
        )
    )
    return scored[:limit]
