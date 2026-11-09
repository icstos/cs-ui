"""响应式引擎契约测试：断点、档位、跨档重绘与两个组件的重排行为。

断言的取向与配色那套一致 —— 不写"某个宽度必须得到某个数字"这种一看就懂但
改一次就废的东西，而是写**不变量**：

* 断点表必须与 ``flet.ResponsiveRow`` 的默认表逐项相同 —— 两套边界错位会让
  「栅格已经换列、页面还以为自己是窄屏」，这是最难查的一类布局 bug；
* ``size_class`` 单调不减、边界左闭右开 —— 窗口只能变宽变窄，档位不该来回抖；
* 跨档才通知 —— 拖动窗口时每像素重绘一次会把界面拖成幻灯片；
* 栅格列数永远落在 ``[1, max_cols]``、子项跨度恒为 1 —— 这保证"一行 n 格等宽"；
* 组件在自己的宽度跨档时重排、同档内不重排 —— 前者是需求，后者是性能。

用法::

    python scripts/_responsive_logic.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import flet as ft  # noqa: E402

from ui.core import responsive as r  # noqa: E402
from ui.core import tokens  # noqa: E402
from ui.display.descriptions import Descriptions  # noqa: E402
from ui.layout.grid import Grid, fit_columns  # noqa: E402
from ui.layout.page import PageLayout  # noqa: E402

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


def ok(name: str, cond: bool, detail: str = "") -> None:
    check(f"{name}{(' ' + detail) if detail else ''}", bool(cond), True)


class _Size:
    """假的 LayoutSizeChangeEvent —— 组件只读 width，不需要真的页面。"""

    def __init__(self, width: float) -> None:
        self.width = width
        self.height = 800


def _still(control: object) -> None:
    """把 update 打成空操作：没挂到页面上的控件调用 update 会抛。"""
    control.update = lambda *a, **k: None  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
print("-- 断点表与 flet 同源 --")
# ---------------------------------------------------------------------------
#: flet 的默认断点表（ResponsiveRow.breakpoints 的默认值）。
#: 键是 ``ResponsiveRowBreakpoint`` 枚举，值取 ``.value`` 才是我们用的字符串。
flet_bp = {bp.value: int(px) for bp, px in ft.ResponsiveRow().breakpoints.items()}
check("BREAKPOINT 的键与 flet 完全一致", tuple(tokens.BREAKPOINT), tuple(flet_bp))
check(
    "BREAKPOINT 的值与 flet 逐项相同",
    dict(tokens.BREAKPOINT),
    flet_bp,
)
_bps = list(tokens.BREAKPOINT.values())
ok("断点严格递增（无并列值）", all(b > a for a, b in zip(_bps, _bps[1:])))
check("xs 从 0 开始", tokens.BREAKPOINT["xs"], 0)


# ---------------------------------------------------------------------------
print()
print("-- size_class：三档、单调、边界左闭右开 --")
# ---------------------------------------------------------------------------
check("SIZE_CLASSES 由窄到宽", r.SIZE_CLASSES, ("compact", "medium", "expanded"))
check("COLUMNS 是 M3 的 4 / 8 / 12", r.COLUMNS, {"compact": 4, "medium": 8, "expanded": 12})
check("每个档位都有列数", sorted(r.COLUMNS), sorted(r.SIZE_CLASSES))

md = tokens.BREAKPOINT["md"]
xl = tokens.BREAKPOINT["xl"]
check("md-1 是 compact", r.size_class(md - 1), "compact")
check("md 是 medium（边界归宽的那档）", r.size_class(md), "medium")
check("xl-1 是 medium", r.size_class(xl - 1), "medium")
check("xl 是 expanded", r.size_class(xl), "expanded")

widths = list(range(0, 2000, 7))
classes = [r.SIZE_CLASSES.index(r.size_class(w)) for w in widths]
ok("宽度递增时档位不回头（单调不减）", all(b >= a for a, b in zip(classes, classes[1:])))
ok("三档都能到达", set(classes) == {0, 1, 2})

for bad in (None, "", "abc", -1, float("nan")):
    ok(f"非法宽度 {bad!r} 不抛并退回默认假设",
       r.size_class(bad) == "expanded")


# ---------------------------------------------------------------------------
print()
print("-- pick / resolve：缺档沿窄档继承 --")
# ---------------------------------------------------------------------------
check("窄档取值", r.pick(600, compact=1, medium=2, expanded=3), 1)
check("中档取值", r.pick(900, compact=1, medium=2, expanded=3), 2)
check("宽档取值", r.pick(1400, compact=1, medium=2, expanded=3), 3)
check("没给中档时继承窄档", r.pick(900, compact=1, expanded=3), 1)
check("没给宽档时继承中档", r.pick(1400, compact=1, medium=2), 2)
check("只给窄档就三档同值", r.pick(1400, compact=1), 1)

check("resolve 标量原样返回", r.resolve(2, 1400), 2)
check("resolve 字典取当前档", r.resolve({"compact": 1, "expanded": 3}, 600), 1)
check("resolve 字典取宽档", r.resolve({"compact": 1, "expanded": 3}, 1400), 3)
check("resolve 字典缺档继承", r.resolve({"compact": 1, "expanded": 3}, 900), 1)
check("resolve 大小写与空格容错", r.resolve({" Expanded ": 5}, 1400), 5)


# ---------------------------------------------------------------------------
print()
print("-- at_least --")
# ---------------------------------------------------------------------------
ok("恰好等于断点算达到", r.at_least(tokens.BREAKPOINT["lg"], "lg"))
ok("差 1px 不算达到", not r.at_least(tokens.BREAKPOINT["lg"] - 1, "lg"))
ok("未知断点名返回 False 而不是抛", not r.at_least(2000, "huge"))
ok("断点名大小写不敏感", r.at_least(2000, "LG"))


# ---------------------------------------------------------------------------
print()
print("-- 只在跨档时通知（性能契约） --")
# ---------------------------------------------------------------------------
r.reset()
calls: list[str] = []
_unsub = r.responsive_state().subscribe(lambda *_a: calls.append("notify"))

r.update(1400, 900)
check("同档内多次 update 不通知", len(calls), 0)

r.update(1399, 900)
r.update(1300, 900)
r.update(1250, 900)
check("一路缩到 1250 仍在 expanded，不通知", len(calls), 0)

r.update(1100, 900)
check("跨到 medium 通知一次", len(calls), 1)
check("状态已更新", r.responsive_state().size_class, "medium")

r.update(1090, 900)
r.update(1000, 900)
check("medium 内部继续缩放，不再通知", len(calls), 1)

r.update(700, 900)
check("跨到 compact 再通知一次", len(calls), 2)
check("viewport 反映最新宽度", r.viewport().width, 700)

r.update(700, 500)
check("只改高度不通知", len(calls), 2)
check("高度已记录", r.viewport().height, 500)

_unsub()
r.update(1400, 900)
check("退订后不再通知", len(calls), 2)

r.reset()
check("reset 回到 expanded", r.responsive_state().size_class, "expanded")
check("reset 清掉 viewport", (r.viewport().width, r.viewport().height), (1280, 800))
check("响应式单例是同一个对象", r.responsive_state() is r.responsive_state(), True)


# ---------------------------------------------------------------------------
print()
print("-- fit_columns：放得下几格 --")
# ---------------------------------------------------------------------------
check("窄到只剩一格", fit_columns(200, 260, 16, 4), 1)
check("刚好两格", fit_columns(260 * 2 + 16, 260, 16, 4), 2)
check("差 1px 放不下两格", fit_columns(260 * 2 + 15, 260, 16, 4), 1)
check("上限 max_cols 生效", fit_columns(4000, 260, 16, 4), 4)
check("0 宽也给一格（不是 0）", fit_columns(0, 260, 16, 4), 1)
check("min_col_width 非法时退回 max_cols", fit_columns(800, 0, 16, 3), 3)

counts = [fit_columns(w, 240, 16, 5) for w in range(0, 2400, 10)]
ok("宽度增加时格数不减", all(b >= a for a, b in zip(counts, counts[1:])))
ok("格数始终在 [1, max_cols]", all(1 <= n <= 5 for n in counts))


# ---------------------------------------------------------------------------
print()
print("-- Grid：列数下发、子项跨度 --")
# ---------------------------------------------------------------------------
g = Grid(min_col_width=200, max_cols=4, controls=[ft.Text(str(i)) for i in range(6)])
check("columns 的键覆盖全部断点", tuple(g.columns), tuple(tokens.BREAKPOINT))
check("每档列数都在 [1, max_cols]", all(1 <= n <= 4 for n in g.columns.values()), True)
check("窄屏一格", g.columns["xs"], 1)
ok("宽屏多于窄屏", g.columns["xxl"] > g.columns["xs"])
check("子项全部占一格", [c.col for c in g.controls], [1] * 6)
check("断点表用的是框架那份", g.breakpoints, dict(tokens.BREAKPOINT))
check("间距同时作为行距", (g.spacing, g.run_spacing), (16, 16))

explicit = ft.Container(col=2, content=ft.Text("wide"))
g2 = Grid(min_col_width=160, max_cols=3, controls=[ft.Text("a"), explicit])
check("子项自己声明的跨度不被覆盖", explicit.col, 2)
check("没声明的仍然是 1", g2.controls[0].col, 1)

g3 = Grid(per_row={"compact": 1, "expanded": 3}, controls=[ft.Text("a")])
check("per_row 字典：窄档继承到中档", (g3.columns["xs"], g3.columns["sm"], g3.columns["md"]), (1, 1, 1))
check("per_row 字典：宽档生效", (g3.columns["xl"], g3.columns["xxl"]), (3, 3))

g4 = Grid(per_row={"xs": 2, "lg": 3}, controls=[ft.Text("a")])
check("per_row 也接受断点名", (g4.columns["xs"], g4.columns["lg"]), (2, 3))
check("per_row 整数对所有档位生效", set(Grid(per_row=2, controls=[]).columns.values()), {2})
check("max_cols 小于 1 时也不会出 0 列", min(Grid(min_col_width=100, max_cols=0, controls=[]).columns.values()) >= 1, True)


# ---------------------------------------------------------------------------
print()
print("-- PageLayout：三档的内边距 / 限宽 / 页头排布 --")
# ---------------------------------------------------------------------------
p = PageLayout(title="标题", subtitle="副标题", actions=[ft.Button("操作")], controls=[ft.Text("内容")], max_content_width="content")
_still(p)
_still(p._column)

p._on_self_size(_Size(tokens.BREAKPOINT["xl"] + 100))
check("宽档内边距 32", p.padding, ft.Padding.all(32))
check("宽档页头是 Row（操作在右）", type(p._column.controls[0]).__name__, "Row")
ok("宽档按上限居中", type(p.content).__name__ == "Row")
check("居中容器取 content 档宽度", p.content.controls[0].width, tokens.CONTENT_MAX["content"])

p._on_self_size(_Size(tokens.BREAKPOINT["md"] + 10))
check("中档内边距 24", p.padding, ft.Padding.all(24))

p._on_self_size(_Size(tokens.BREAKPOINT["md"] - 10))
check("窄档内边距 16", p.padding, ft.Padding.all(16))
check("窄档页头折成两行（Column）", type(p._column.controls[0]).__name__, "Column")
# 限宽靠"夹取"而不是"拆掉外壳"：结构在构建期定死，换档只改宽度 ——
# 换外壳意味着整棵子树重挂，那才是真的会掉帧。
check("窄档仍然只有一层外壳", type(p.content).__name__, "Row")
narrow_w = tokens.BREAKPOINT["md"] - 10
check(
    "窄档限宽自动让位到可用宽度（不再溢出）",
    p.content.controls[0].width,
    ((narrow_w - 32) // 8) * 8,
)
ok("窄档的宽度小于上限", int(p.content.controls[0].width) < tokens.CONTENT_MAX["content"])
check("内容一个都没少", len(p.controls), 1)

p._on_self_size(_Size(tokens.BREAKPOINT["xl"] + 400))
check(
    "再放大回上限值",
    p.content.controls[0].width,
    tokens.CONTENT_MAX["content"],
)
ok("限宽取 8px 整数倍（量化，避免每像素重绘）", int(p.content.controls[0].width) % 8 == 0)

explicit_pad = PageLayout(title="t", controls=[], padding=ft.Padding.all(7))
_still(explicit_pad)
_still(explicit_pad._column)
explicit_pad._on_self_size(_Size(500))
check("显式给的内边距不被档位覆盖", explicit_pad.padding, ft.Padding.all(7))

wide_limit = PageLayout(title="t", controls=[], max_content_width="reading")
_still(wide_limit)
_still(wide_limit._column)
check("未量到宽度时先按上限", wide_limit._limit(), tokens.CONTENT_MAX["reading"])
wide_limit._on_self_size(_Size(600))
check(
    "窄容器上上限自然让位（min 的结果，不是特判）",
    wide_limit._limit(),
    ((600 - 32) // 8) * 8,
)
ok("让位后确实小于上限", wide_limit._limit() < tokens.CONTENT_MAX["reading"])


# ---------------------------------------------------------------------------
print()
print("-- Descriptions：按断点给列数 --")
# ---------------------------------------------------------------------------
_spec = {"compact": 1, "medium": 2, "expanded": 3}
_items = [{"label": "a", "value": "1"}, {"label": "b", "value": "2"}]

r.update(1400)
wide = Descriptions(items=_items, column=_spec)
check("宽档构建 → 三列", wide.column, 3)
r.update(900)
mid = Descriptions(items=_items, column=_spec)
check("中档构建 → 两列", mid.column, 2)
r.update(640)
narrow = Descriptions(items=_items, column=_spec)
check("窄档构建 → 一列", narrow.column, 1)
check("换列数是结构变化，不挂运行期监听", narrow.on_size_change, None)
r.update(1280)

static = Descriptions(items=_items, column=2)
check("给 int 的列数原样生效", static.column, 2)
check("给 int 也不挂监听", static.on_size_change, None)

# 行切分必须跟着列数走：6 个字段、2 列 → 3 行，且末行补满
r.update(900)
mid2 = Descriptions(
    items=[{"label": f"L{i}", "value": f"V{i}"} for i in range(6)], column=_spec
)
check("两列时切成 3 行", [len(row) for row in mid2._rows()], [2, 2, 2])
check("一列时切成 6 行", [len(row) for row in mid2._rows(1)], [1] * 6)


# ---------------------------------------------------------------------------
print()
print("-- 私有运行时字段不得成为 dataclass 字段 --")
# ---------------------------------------------------------------------------
# ``@ft.control`` 会把带注解的字段变成本控件的属性，而 flet 序列化时会遍历所有
# ``ft.Control`` 类型的字段 —— 私有控件一旦带注解，就会被当成"另一个子控件"再挂
# 一次。于是 Python 侧状态全对、屏幕纹丝不动（补丁打到了那份看不见的副本上）。
_FLET_FIELDS = {"_values", "_dirty", "_i", "_c", "_internals"}
for _cls in (PageLayout, Descriptions, Grid):
    _bad = [
        f
        for f in _cls.__dataclass_fields__
        if f.startswith("_") and not f.startswith("__") and f not in _FLET_FIELDS
    ]
    check(f"{_cls.__name__} 没有注解型私有字段", _bad, [])


# ---------------------------------------------------------------------------
print()
print(f"RESULT: {'ALL PASS' if not _fails else f'{len(_fails)} FAILED'}  (passed={_passed})")
if _fails:
    for line in _fails:
        print("  -", line)
    sys.exit(1)
