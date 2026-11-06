"""ui-mcp 索引与查询逻辑单测（本项目范式：scripts/_<模块>_logic.py）。

断言四件事：

1. **索引完整性** —— 每个组件都有 kind/pattern/module，且范式与代码一致
   （`observable` 的类真的有 `ui()`，`static` 的真的是 flet 控件）；
2. **建索引用到的内省技巧** —— 字段只取本类声明的（`@ft.observable` 代理链、
   `@ft.control` 拍平都不该让字段丢失或串味）；
3. **查询层** —— 名称/别名/继承链/枚举/不存在符号的行为；
4. **中文检索** —— "按钮"必须命中 Button（这条最容易回归，因为依赖手写别名表）。

跑法：``python scripts/_ui_mcp_logic.py``
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import inspect

import flet as ft

from ui_mcp import paths
from ui_mcp.docs import DocsIndex
from ui_mcp.examples import ExamplesIndex
from ui_mcp.store import api_store, render_text

PASSED = 0


def check(label: str, got, want) -> None:
    global PASSED
    if got == want:
        PASSED += 1
        print(f"PASS  {label}: got={got!r}")
    else:
        print(f"FAIL  {label}: got={got!r} want={want!r}")
        raise SystemExit(1)


def check_true(label: str, cond: bool) -> None:
    global PASSED
    if cond:
        PASSED += 1
        print(f"PASS  {label}")
    else:
        print(f"FAIL  {label}")
        raise SystemExit(1)


# ---------------------------------------------------------------- 索引产物
print("=== 索引产物存在 ===")
for path in (paths.api_json(), paths.examples_json(), paths.docs_json()):
    check_true(f"{path.name} 已生成", path.exists())

meta = api_store.meta
check_true("meta 里有 ui 版本", bool(meta.get("version")))
check_true("meta 里有 flet 版本", bool(meta.get("flet")))
check_true("组件数 > 60", meta["counts"]["components"] > 60)
check_true("外部祖先数 > 20", meta["counts"]["ancestors"] > 20)

print()
print("=== 每个组件条目字段完整 ===")
required = ("name", "module", "kind", "pattern", "exported", "bases")
broken = [
    e["name"]
    for bucket in ("components", "types", "functions", "enums")
    for e in api_store.entries(bucket)
    if any(key not in e for key in required if bucket != "functions")
]
check("缺字段的条目", broken, [])

names = {e["name"] for e in api_store.entries("components")}
check("别名导致的重复 Header_1 已合并", len([n for n in names if n == "Header_1"]), 1)

# ---------------------------------------------------------------- 内省正确性
print()
print("=== 内省：字段归属 ===")
import ui

button = api_store.get("Button")
check("Button 自家字段数（height/style_type/shape/plain/is_primary）", len(button["properties"]), 5)
check("Button 基类", button["bases"], ["flet.Button"])
check(
    "Button.plain 的行尾注释被捞出来",
    next(p for p in button["properties"] if p["name"] == "plain").get("doc"),
    "中心是否镂空",
)

input_entry = api_store.get("Input")
input_names = [p["name"] for p in input_entry["properties"]]
check_true("Input 不含继承来的 label 字段", "label" not in input_names)
check_true("Input 含自家 value 字段", "value" in input_names)
check("Input 继承块", [b["from"] for b in input_entry["inherited"]], ["Label"])

# 范式与真实代码一致
for entry in api_store.entries("components"):
    if entry["pattern"] == "observable" and entry["kind"] == "component":
        cls = getattr(ui, entry["name"], None)
        check_true(f"{entry['name']} 是 observable 且真有 ui()", callable(getattr(cls, "ui", None)))
        break

for entry in api_store.entries("components"):
    if entry["pattern"] == "static":
        cls = getattr(ui, entry["name"], None)
        if inspect.isclass(cls):
            check_true(
                f"{entry['name']} 是 static 且真是 flet 控件",
                issubclass(cls, ft.BaseControl),
            )
        break

print()
print("=== 内省：枚举与函数 ===")
style = api_store.get_enum("StyleType")
check("StyleType 成员数", len(style["members"]), 6)
check_true("StyleType 首个成员名", style["members"][0]["name"] == "DEFAULT")
check("枚举成员值不是『4 项』这种空话", "tuple(4 项)" in str(style["members"][0]["value"]), False)

table = api_store.get("Table")
check("Table 是函数组件", (table["kind"], table["pattern"]), ("component", "function"))
check_true("Table 签名含 rows_per_page", "rows_per_page" in table["signature"])
check("库内 demo 入口 App/main 未进索引", [e["name"] for e in api_store.entries("functions") if e["name"] in ("App", "main")], [])

# ---------------------------------------------------------------- 查询层
print()
print("=== 查询层 ===")
check("不存在符号返回 None", api_store.get("NopeWidget"), None)
check("别名 Title 解析到 Header_1", api_store.get("Title")["name"], "Header_1")
check("模块限定名可查", api_store.get("ui.input.button.Button")["name"], "Button")
check("外部基类可查", api_store.get("flet.Button")["kind"], "control")

inherited_hit = api_store.get("Button", query="on_")
check_true("继承链能搜到 on_click", "on_click" in render_text(inherited_hit))

member = api_store.get("SelectBox", member="ui")
check("成员下钻 member_kind", member["member_kind"], "method")
check_true("成员下钻渲染含签名", "ui()" in render_text(member))

missing_member = api_store.get("Button", member="nonexistent")
check_true("成员不存在时给可用列表", "error" in missing_member and missing_member["available_members"])

check("枚举成员搜索排序（前缀优先）", api_store.search_enum_members("StyleType", "P")[0], "PRIMARY")
check("枚举成员存在性", api_store.enum_has_member("StyleType", "primary"), True)
check("枚举成员不存在性", api_store.enum_has_member("StyleType", "NOPE"), False)

print()
print("=== 文本渲染 ===")
text = render_text(api_store.get("Button"))
check_true("渲染含 import 行", "import: from ui import Button" in text)
check_true("渲染含继承摘要", "inherited from flet.Button" in text)
check_true("渲染含真实用法", "real usage —" in text)
check_true("渲染不含 JSON 花括号", "{" not in text)
check_true("函数组件渲染含 signature", "signature: Table(" in render_text(api_store.get("Table")))

# ---------------------------------------------------------------- 中文检索
print()
print("=== 中文检索（依赖手写别名表）===")
cases = {
    "按钮": "Button",
    "下拉选择": "SelectBox",
    "表格": "Table",
    "取色器": "ColorPicker",
    "评分": "Rating",
    "面包屑": "BreadCrumb",
    "开关": "Switch",
    "输入框": "Input",
}
for query, expected in cases.items():
    hits = api_store.search(query, limit=3)
    check(f"搜『{query}』首位", hits[0]["name"] if hits else None, expected)

check("搜英文名也首位命中", api_store.search("ColorPicker", limit=1)[0]["name"], "ColorPicker")

# ---------------------------------------------------------------- 示例 / 文档
print()
print("=== 示例与文档 ===")
examples = ExamplesIndex()
pages = {e["id"] for e in examples.all()}
# examples/demo.py 早已拆成 examples/test_*.py，这里跟到现存的表单示例
check_true("test_form/App 已索引", "test_form/App" in pages)
form = examples.get("test_form/App")
check_true("示例带源码", "def App" in form["code"])
check_true("示例带路由字段", "route" in form)
page_slice = examples.get("test_form/App", start_line=1, max_lines=20)
check_true("示例支持分页读", page_slice["total_lines"] > 20 and len(page_slice["code"].splitlines()) <= 20)
check_true("用法回填存在", bool(examples.usage.get("SelectBox")))
check("未知示例给候选列表", "error" in examples.get("nope/nothing"), True)

docs = DocsIndex()
sections = {s["location"] for s in docs.all()}
check_true("README 段落已索引", any(s.startswith("README_CN.md#") for s in sections))
check_true("文档搜索命中", bool(docs.search("令牌")))
check("不存在段落给相似候选", "error" in docs.get("不存在#的段落"), True)
outline = docs.search("")
check_true("空 query 返回大纲", bool(outline) and all("location" in item for item in outline))

print()
print(f"RESULT: ALL PASS  (passed={PASSED})")
