"""ui-mcp 服务端：FastMCP 工具集合。

工具分五组，用环境变量在启动时开关（值和 flet-mcp 一致，认 ``1/true/yes``）：

======================  =========================  ======
组                      变量                        默认
======================  =========================  ======
API                      UI_MCP_ENABLE_API          on
icons（图标）             UI_MCP_ENABLE_ICONS        on
examples（demo 示例）     UI_MCP_ENABLE_EXAMPLES     on
docs（Markdown 文档）     UI_MCP_ENABLE_DOCS         on
guide（经验条款）          UI_MCP_ENABLE_GUIDE        on
======================  =========================  ======

分组的理由是**上下文预算**：每个工具的 schema 都要进系统提示词。默认全开是因为
cs-ui 只有 12 个工具（flet-mcp 是 9 个），装得下；真要瘦身就关掉 icons/docs。

大小预算：单次响应控制在 ~2 万字符内。超长的示例/文档段会截断并给下钻提示 ——
工具输出会进对话历史，每次调用都要重付 token。
"""

from __future__ import annotations

import os
from typing import Optional, Union

from fastmcp import FastMCP

from ui_mcp import guidelines
from ui_mcp.__about__ import __version__
from ui_mcp.docs import DocsIndex
from ui_mcp.examples import ExamplesIndex
from ui_mcp.store import api_store, render_text

EXAMPLES_BUDGET = 24_000


def _enabled(name: str, default: str = "1") -> bool:
    return os.getenv(f"UI_MCP_ENABLE_{name}", default).lower() in ("1", "true", "yes")


_API_ON = _enabled("API")
_ICONS_ON = _enabled("ICONS")
_EXAMPLES_ON = _enabled("EXAMPLES")
_DOCS_ON = _enabled("DOCS")
_GUIDE_ON = _enabled("GUIDE")

_GROUPS = [
    label
    for label, on in (
        ("API", _API_ON),
        ("icons", _ICONS_ON),
        ("examples", _EXAMPLES_ON),
        ("docs", _DOCS_ON),
        ("guide", _GUIDE_ON),
    )
    if on
]

_META = api_store.meta
_COUNTS = _META.get("counts", {})

mcp = FastMCP(
    "ui-mcp",
    version=__version__,
    instructions=(
        "cs-ui（Python 包名 `ui`，基于 flet 1.x）的组件库 API 服务，"
        f"索引版本 ui {_META.get('version', '?')} / flet {_META.get('flet', '?')}"
        f"（{_COUNTS.get('components', 0)} 个组件、{_COUNTS.get('functions', 0)} 个函数）。"
        f"本次启用的工具组：{', '.join(_GROUPS)}。\n"
        "工作方式：\n"
        "1. 心里有类名就先 get_api(name) —— 这是最便宜的验证，'not found' 是确定结论；\n"
        "2. 每条的 `pattern:` 行决定怎么写：static=直接构造，"
        "observable=数据对象，**必须调用 .ui()** 且用 state()/use_ref 固定实例，"
        "function=函数组件直接当控件用；\n"
        "3. 继承来的属性用 get_api(name, query='on_') 或 get_api('flet.Button') 查；\n"
        "4. 写代码前先 get_guidelines('overview')：frozen 树、page.render、颜色串格式"
        "这些坑查 API 查不出来，写错必炸；\n"
        "5. 想看真实写法用 search_examples(query) → get_example(id)。\n"
        "所有组件都能 `from ui import X` 导入。"
    ),
)

_examples = ExamplesIndex()
_docs = DocsIndex()


# ---------------------------------------------------------------------------
# API 组
# ---------------------------------------------------------------------------


if _API_ON:

    @mcp.tool()
    def get_api(
        name: str,
        member: Optional[str] = None,
        query: Optional[str] = None,
        format: str = "text",
    ) -> Union[str, dict]:
        """查 cs-ui 任一符号：组件、数据类、函数组件、hook、枚举、外部祖先类。

        默认返回紧凑文本，一行一个成员：

            Button (component · static) — 主按钮
            module: ui.input.button
            import: from ui import Button
            bases: flet.Button
            properties (3):
              is_primary: bool = False
            events (1):
              on_click(ControlEvent) — 点击时调用
            inherited from flet.Button: 10 properties, 5 events, 0 methods

        读法：
        * `(kind · pattern)` —— pattern 决定用法，见服务器说明；
        * `?` 省略了，类型里带 `| None` 就是可空；
        * `on_x(SomeEvent)` —— 回调收到的参数类型；
        * `inherited from ...` 只给数量：要具体成员用 `query=` 下钻，或
          `get_api("flet.Button")` 看基类全表；
        * `real usage —` —— 从 examples/demo.py 里抠出来的**能跑的调用**，
          比任何文档都可信。

        下钻 / 过滤：
        * `member="on_click"` —— 单个成员的全文与精确类型；
        * `query="label"` —— 只看名字含该子串的成员（**含继承链**）；
        * `get_api("flet.Button")` —— 外部基类（`包名.类名`）；
        * `format="json"` —— 结构化 dict，供程序消费。

        Args:
            name: 符号名，如 "Button"、"SelectBox"、"Table"、"TableState"、
                "semantic"、"StyleType"、"flet.Button"。
            member: 可选，取单个成员全文。
            query: 可选，按成员名子串过滤（含继承）。
            format: "text"（默认）或 "json"。
        """
        result = api_store.get(name, member=member, query=query)
        if result is None:
            return {
                "error": f"'{name}' 不存在于 cs-ui 索引里",
                "hint": "名字拼错？先 search_components(query) 找一找；"
                "外部 flet 组件请加包名，如 'flet.Button'。",
            }
        if "error" in result or format == "json":
            return result
        return render_text(result)

    @mcp.tool()
    def list_components(
        category: Optional[str] = None,
        pattern: Optional[str] = None,
        kind: Optional[str] = None,
        query: Optional[str] = None,
        limit: int = 60,
    ) -> list[dict]:
        """浏览组件清单（按分类/范式过滤）。

        Args:
            category: 分类，如 "input"、"layout"、"display"、"feedback"、
                "navigation"、"chart"、"core"、"utils"、"media"。
            pattern: 范式，"static"（构造即用）、"observable"（必须调 .ui()）、
                "function"（函数组件）、"mixin"、"dataclass"。
            kind: "control" / "component" / "type"。
            query: 名字/摘要里含该子串。
            limit: 最多返回条数。
        """
        return api_store.list_components(
            category=category, pattern=pattern, kind=kind, query=query, limit=limit
        )

    @mcp.tool()
    def search_components(query: str, limit: int = 8) -> list[dict]:
        """按自然语言/关键词搜组件（名字、摘要、文档、属性名、真实用法一起评分）。

        适合"要一个能翻页的表格"、"颜色选择器"、"想显示日志"这种模糊需求。

        Args:
            query: 关键词，中英文都行。
            limit: 最多返回条数。
        """
        return api_store.search(query, limit=limit)

    @mcp.tool()
    def get_enum(name: str, query: Optional[str] = None, limit: int = 20) -> dict:
        """查枚举定义（cs-ui 的 StyleType / ButtonShape / FeedbackStyle …）。

        Args:
            name: 枚举名，如 "StyleType"、"ButtonShape"、"FormValueType"。
            query: 可选，只列名字含该子串的成员。
            limit: query 时的最大条数。
        """
        enum = api_store.get_enum(name)
        if enum is None:
            return {"error": f"枚举 '{name}' 不存在"}
        if query:
            matches = api_store.search_enum_members(name, query, limit=limit)
            return {
                "name": enum["name"],
                "module": enum.get("module"),
                "matches": matches,
                "total": len(enum.get("members") or []),
            }
        return enum

    @mcp.tool()
    def search_enum_members(name: str, query: str, limit: int = 10) -> dict:
        """按名字子串搜枚举成员（排序：完全匹配 → 前缀 → 子串）。

        Args:
            name: 枚举名。
            query: 子串，如 "PRIMARY"。
            limit: 最多返回条数。
        """
        return {
            "enum": name,
            "matches": api_store.search_enum_members(name, query, limit=limit),
        }

    @mcp.tool()
    def enum_has_member(name: str, member: str) -> dict:
        """确认枚举成员是否存在（写代码前先验证，比猜省事）。

        Args:
            name: 枚举名。
            member: 成员名，如 "PRIMARY"。
        """
        return {
            "enum": name,
            "member": member,
            "exists": api_store.enum_has_member(name, member),
        }


# ---------------------------------------------------------------------------
# 图标组
# ---------------------------------------------------------------------------

# 中文概念 → flet Icons 里的英文关键词。查 "删除" 命中 DELETE，省一次试错。
_ICON_SYNONYMS: dict[str, str] = {
    "添加": "add plus",
    "新增": "add",
    "删除": "delete remove",
    "编辑": "edit create",
    "修改": "edit",
    "保存": "save",
    "下载": "download",
    "上传": "upload cloud_upload",
    "搜索": "search",
    "查找": "search find",
    "设置": "settings",
    "配置": "settings tune",
    "用户": "person account user",
    "账号": "account person",
    "首页": "home",
    "返回": "arrow_back",
    "前进": "arrow_forward",
    "关闭": "close cancel",
    "取消": "cancel close",
    "确认": "check done",
    "成功": "check_circle done",
    "错误": "error",
    "警告": "warning",
    "提示": "info",
    "信息": "info",
    "刷新": "refresh",
    "菜单": "menu",
    "更多": "more_horiz",
    "列表": "list",
    "表格": "table grid",
    "图片": "image photo",
    "文件": "file folder",
    "文件夹": "folder",
    "播放": "play",
    "暂停": "pause",
    "停止": "stop",
    "时间": "schedule access_time",
    "日期": "calendar",
    "通知": "notifications",
    "邮件": "mail email",
    "电话": "phone call",
    "地图": "map location",
    "位置": "location_on place",
    "锁": "lock",
    "可见": "visibility",
    "隐藏": "visibility_off",
    "打印": "print",
    "复制": "content_copy",
    "粘贴": "content_paste",
    "撤销": "undo",
    "重做": "redo",
    "排序": "sort",
    "过滤": "filter",
    "全屏": "fullscreen",
    "退出": "logout exit_to_app",
}

_icon_cache: list[str] | None = None


def _icon_names() -> list[str]:
    global _icon_cache
    if _icon_cache is None:
        try:
            import flet as ft

            _icon_cache = [m.name for m in ft.Icons]
        except Exception:
            _icon_cache = []
    return _icon_cache


if _ICONS_ON:

    @mcp.tool()
    def find_icon(query: str, limit: int = 10) -> dict:
        """按概念搜 flet 的 Material 图标名（返回 `ft.Icons.XXX` 的 XXX 部分）。

        支持中文关键词（内置常见概念的映射，如"删除"→ DELETE）。

        Args:
            query: 概念词，如 "删除"、"user"、"arrow back"、"file"。
            limit: 最多返回条数。
        """
        names = _icon_names()
        if not names:
            return {"error": "当前环境没装 flet，无法列出图标"}
        lowered = query.lower().strip()
        terms = [lowered] + [t for t in (lowered.split()) if t]
        for cjk, mapped in _ICON_SYNONYMS.items():
            if cjk in query:
                terms.extend(mapped.split())
        prefixes = {t.upper() for t in terms if t}
        matched = [
            name
            for name in names
            if any(name.upper() == p or p in name.upper() for p in prefixes)
        ]

        def tier(name: str) -> tuple[int, int, int, str]:
            upper = name.upper()
            rank_ = 0 if upper in prefixes else 1 if any(
                upper.startswith(p + "_") for p in prefixes
            ) else 2
            # 同时命中更多关键词的更相关：查 "arrow back" 时 ARROW_BACK
            # 应该排在只命中 back 的 BACK_HAND 前面。
            hits = sum(1 for p in prefixes if p in upper)
            return (rank_, -hits, len(name), name)

        matched.sort(key=tier)
        # Material 的 _OUTLINED/_ROUNDED/_SHARP 只是样式变体：基础名已经命中时
        # 折叠掉，否则 10 个结果位会被同一个图标占满。
        present = set(matched)
        collapsed = []
        for name in matched:
            base = next(
                (name[: -len(s)] for s in ("_OUTLINED", "_ROUNDED", "_SHARP") if name.endswith(s)),
                None,
            )
            if base and base in present:
                continue
            collapsed.append(name)
        return {
            "query": query,
            "icons": [f"Icons.{name}" for name in collapsed[:limit]],
            "note": "用法：ft.Icon(icon=ft.Icons.XXX, size=18)；样式变体加 _OUTLINED/_ROUNDED/_SHARP。",
        }


# ---------------------------------------------------------------------------
# 示例组
# ---------------------------------------------------------------------------


if _EXAMPLES_ON:

    @mcp.tool()
    def search_examples(query: str, limit: int = 5) -> list[dict]:
        """搜 demo 里的示例页/辅助函数（按标题、docstring、涉及组件、源码评分）。

        返回 id 与摘要；用 get_example(id) 读源码。

        Args:
            query: 关键词，如 "表单"、"分页表格"、"通知"、"上传"。
            limit: 最多返回条数。
        """
        return _examples.search(query, limit=limit)

    @mcp.tool()
    def get_example(
        example_id: str,
        start_line: Optional[int] = None,
        max_lines: Optional[int] = None,
    ) -> dict:
        """取示例源码。长示例（一页常有 200+ 行）可分段读。

        Args:
            example_id: search_examples() 返回的 id，如 "demo/FormPage"。
            start_line: 从第几行开始（1 起）。
            max_lines: 本次最多返回多少行。
        """
        result = _examples.get(example_id, start_line=start_line, max_lines=max_lines)
        code = result.get("code")
        if isinstance(code, str) and len(code) > EXAMPLES_BUDGET and not start_line:
            lines = code.splitlines()
            keep = EXAMPLES_BUDGET // 40
            result["code"] = "\n".join(lines[:keep])
            result["note"] = (
                f"示例共 {len(lines)} 行，这里只给前 {keep} 行。"
                f"分段读：get_example({example_id!r}, start_line=..., max_lines=...)"
            )
        return result


# ---------------------------------------------------------------------------
# 文档组
# ---------------------------------------------------------------------------


if _DOCS_ON:

    @mcp.tool()
    def search_docs(query: str, limit: int = 5) -> list[dict]:
        """搜项目文档段落（README / TODO / 项目记忆）。

        空 query 返回目录大纲。

        Args:
            query: 关键词，如 "令牌"、"主题"、"frozen"、"验收"。
            limit: 最多返回条数。
        """
        return _docs.search(query, limit=limit)

    @mcp.tool()
    def get_doc(location: str) -> dict:
        """按 location 读整段文档（location 形如 ``README_CN.md#设计令牌与主题#三、令牌``）。

        也接受只给标题（"组件概况"）。

        Args:
            location: search_docs() 返回的 location。
        """
        return _docs.get(location)


# ---------------------------------------------------------------------------
# 经验条款组
# ---------------------------------------------------------------------------


if _GUIDE_ON:

    @mcp.tool()
    def get_guidelines(topic: Optional[str] = None) -> dict:
        """读项目"经验条款"——查 API 查不到、但写错必炸的范式。

        无参数时返回条款清单（topic/title/tags）。建议一开始就读
        ``get_guidelines("overview")``。

        现有 topic：overview、rendering（page.render / Router / View 不能当控件）、
        frozen（禁止 update()）、state-components（.ui() 与 state()）、
        selectors（PanelField 家族）、table、layout（expand 陷阱）、
        colors（#AARRGGBB）、tokens、theme、verify（改完跑哪些脚本）。

        Args:
            topic: 条款名；不给则列出全部。
        """
        return guidelines.get(topic)


__all__ = ["mcp"]
