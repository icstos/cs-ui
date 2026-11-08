"""Descriptions 纯逻辑单测（不需要窗口）。

覆盖：列打包与末行补齐、span 夹取、横 / 纵两种排布的控件结构（边框只画右/下、
标签格底色、控件值不被拉满）、尺寸档位与别名、冒号规则、空数据与多种入参写法。

用法::

    python scripts/_descriptions_logic.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import flet as ft  # noqa: E402

from ui.display.descriptions import (  # noqa: E402
    LABEL_BG,
    Descriptions,
    DescriptionsItem,
)

_fails: list[str] = []
_passed = 0


def check(name: str, got: object, want: object) -> None:
    global _passed
    if got == want:
        _passed += 1
        print(f"PASS  {name}: got={got!r}")
    else:
        _fails.append(f"{name}: got={got!r} want={want!r}")
        print(f"FAIL  {name}: got={got!r} want={want!r}")


def section(title: str) -> None:
    print(f"\n== {title} ==")


def layout(desc: Descriptions) -> list[list[int]]:
    """把行结构压成"每行各格的 span"的二维表，便于断言。"""
    return [[span for _, span in row] for row in desc._rows()]


def grid(desc: Descriptions) -> ft.Column:
    """取表格本体（``bordered`` 时外面多一层描边容器）。"""
    block = desc.content.controls[-1]
    return block.content if isinstance(block, ft.Container) else block


def first_cell(desc: Descriptions) -> ft.Row:
    return grid(desc).controls[0].controls[0]


ITEMS = [DescriptionsItem(f"字段{i}", f"值{i}") for i in range(7)]

# ---------------------------------------------------------------------------
section("列打包：span 与换行")
check("3 列 7 项 → 3 行", [len(r) for r in layout(Descriptions(items=ITEMS, column=3))], [3, 3, 1])
check("末行不满时最后一项吃掉剩余列", layout(Descriptions(items=ITEMS, column=3))[-1], [3])
check("正好排满时不做补齐", layout(Descriptions(items=ITEMS[:6], column=3)), [[1, 1, 1], [1, 1, 1]])
check(
    "span 挤走后续项",
    layout(
        Descriptions(
            items=[
                DescriptionsItem("a", span=2),
                DescriptionsItem("b"),
                DescriptionsItem("c"),
                DescriptionsItem("d"),
            ],
            column=3,
        )
    ),
    [[2, 1], [1, 2]],
)
check(
    "span 超过 column 被夹取",
    layout(Descriptions(items=[DescriptionsItem("a", span=9), DescriptionsItem("b")], column=3)),
    [[3], [3]],
)
check("column 非法值兜底为 1", layout(Descriptions(items=ITEMS[:2], column=0)), [[1], [1]])
check("空列表不产生行", layout(Descriptions(items=[])), [])
check("单列每项独占一行", layout(Descriptions(items=ITEMS[:3], column=1)), [[1], [1], [1]])

# ---------------------------------------------------------------------------
section("带边框横向：结构")
d = Descriptions(items=[DescriptionsItem("用户名", "shawn"), DescriptionsItem("手机号", "181")], column=2)
block = d.content.controls[0]
check("外层是描边容器", type(block).__name__, "Container")
check("外框圆角裁剪", block.clip_behavior, ft.ClipBehavior.ANTI_ALIAS)
check("表格用 Column 串行", type(block.content).__name__, "Column")
row = grid(d).controls[0]
check("每行是 Row", type(row).__name__, "Row")
check("行高按内容量出（intrinsic_height）", row.intrinsic_height, True)
check("行内纵向拉满", row.vertical_alignment, ft.CrossAxisAlignment.STRETCH)
cell = first_cell(d)
check("一格 = 标签 + 内容", (type(cell).__name__, len(cell.controls)), ("Row", 2))
label, value = cell.controls
check("标签格底色", label.bgcolor, LABEL_BG)
check("标签格固定宽", label.width, d.label_width)
check("标签格只画右边线", (label.border.right.width, label.border.top.width, label.border.left.width), (1, 0, 0))
check("内容格占满剩余宽度", value.expand, True)
check("带边框不补冒号", label.content.value, "用户名")
check("末列内容格不画右边线", row.controls[-1].controls[1].border.right, None)
check(
    "末行不画下边线",
    grid(Descriptions(items=ITEMS[:4], column=2)).controls[-1].controls[0].controls[0].border.bottom,
    None,
)

# ---------------------------------------------------------------------------
section("无边框横向：结构")
d = Descriptions(items=[DescriptionsItem("用户名", "shawn")], column=2, bordered=False)
check("无边框不包外框", type(d.content.controls[0]).__name__, "Column")
label, value = first_cell(d).controls
check("无边框补冒号", label.content.value, "用户名:")
check("无边框标签不上底色", label.bgcolor, None)
check("无边框无右边线", label.border, None)
check(
    "colon=False 不补冒号",
    first_cell(Descriptions(items=[DescriptionsItem("用户名", "x")], bordered=False, colon=False))
    .controls[0]
    .content.value,
    "用户名",
)

# ---------------------------------------------------------------------------
section("垂直方向：标签行 + 内容行")
d = Descriptions(
    items=[DescriptionsItem("用户名", "shawn"), DescriptionsItem("手机号", "181")],
    column=2,
    direction="vertical",
)
rows = grid(d).controls
check("一行字段拆成两行（标签行 + 内容行）", len(rows), 2)
check("两行的格数一致", [len(r.controls) for r in rows], [2, 2])
check("标签格有底色", rows[0].controls[0].bgcolor, LABEL_BG)
check("标签行与内容行之间有下边线", rows[0].controls[0].border.bottom.width, 1)
check("末行内容格无下边线", rows[1].controls[0].border.bottom, None)

d = Descriptions(items=[DescriptionsItem("用户名", "shawn")], direction="vertical", bordered=False)
col = grid(d).controls[0].controls[0].content
check("无边框垂直 = 标签在上、内容在下", (type(col).__name__, len(col.controls)), ("Column", 2))

# ---------------------------------------------------------------------------
section("内容：控件值不被拉满")
tag = ft.Container(content=ft.Text("学校"))
d = Descriptions(items=[DescriptionsItem("备注", tag)])
value = first_cell(d).controls[1]
check("控件值外面包一层 Row", type(value.content).__name__, "Row")
check("Row 用 tight，控件保持自身尺寸", value.content.tight, True)
check("控件原样保留", value.content.controls[0] is tag, True)
check(
    "非字符串值按 str 渲染",
    first_cell(Descriptions(items=[DescriptionsItem("a", 12)])).controls[1].content.value,
    "12",
)

# ---------------------------------------------------------------------------
section("标题 / 操作区")
d = Descriptions(title="用户信息", extra="全部", items=ITEMS[:1])
head = d.content.controls[0]
check("有标题时多一块表头", len(d.content.controls), 2)
check("表头是三段式 Row", len(head.content.controls), 3)
check("标题字号", head.content.controls[0].size, 15)
check("操作区按字符串渲染", type(head.content.controls[2]).__name__, "Text")
check("无标题无操作区不占位", len(Descriptions(items=ITEMS[:1]).content.controls), 1)
check(
    "只有操作区也绘表头",
    len(Descriptions(extra=ft.Icon(ft.Icons.ADD), items=ITEMS[:1]).content.controls),
    2,
)

# ---------------------------------------------------------------------------
section("尺寸与入参")
check("默认档位内边距", (Descriptions()._pad_h, Descriptions()._pad_v), (12, 8))
check("small 档位内边距", (Descriptions(size="small")._pad_h, Descriptions(size="small")._pad_v), (8, 5))
check("Element 的 mini 别名", Descriptions(size="mini")._pad_h, 8)
check("Element 的 medium 别名", Descriptions(size="medium")._pad_h, 12)
check("非法档位兜底 default", Descriptions(size="huge")._pad_h, 12)
check("字典入参", Descriptions(items=[{"label": "a", "value": "b"}])._items[0].value, "b")
check("二元组入参", Descriptions(items=[("a", "b")])._items[0].label, "a")
# 空数据**不再**缩成空容器：整块塌成 0 高时，调用方会以为组件没渲染出来。
# 现在的行为是留一行「暂无数据」占位 —— 断言就照着这个行为写。
_empty = Descriptions()
check("空数据 → 一块占位行", type(_empty.content).__name__, "Column")
check("空数据 → 占位行里有文案", len(_empty.content.controls), 1)
check(
    "只有标题、没有字段 → 表头 + 占位行",
    len(Descriptions(title="T").content.controls),
    2,
)

d = Descriptions(items=ITEMS[:1])
d.set_items([DescriptionsItem("x", "y"), DescriptionsItem("z", "w")])
check("set_items 换数据后重建", len(d._items), 2)
check("set_items 后行结构同步（2 项 + 默认 3 列）", layout(d), [[1, 2]])

# ---------------------------------------------------------------------------
print(f"\n{_passed} passed, {len(_fails)} failed")
if _fails:
    for f in _fails:
        print("  -", f)
    raise SystemExit(1)
