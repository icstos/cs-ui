"""Step 纯逻辑单测（不需要窗口）。

覆盖：状态推导（active 位置关系 / 越界夹取 / 钉死 status / 别名）、连接线按段着色、
三种排布的控件结构（横向等宽 + 半段线占位、垂直轴轨、简洁单行）、点击切换与回调、
空数据与字典入参。

用法::

    python scripts/_step_logic.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import flet as ft  # noqa: E402

from ui.layout.step import Step, StepItem  # noqa: E402

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


ITEMS = [StepItem("一"), StepItem("二"), StepItem("三"), StepItem("四")]

# ---------------------------------------------------------------------------
section("状态推导：active 与位置关系")
for active, want in (
    (-1, ["wait", "wait", "wait", "wait"]),
    (0, ["process", "wait", "wait", "wait"]),
    (1, ["finish", "process", "wait", "wait"]),
    (3, ["finish", "finish", "finish", "process"]),
    (99, ["finish", "finish", "finish", "process"]),  # 越界夹到末步
):
    step = Step(steps=ITEMS, active=active)
    check(f"active={active}", [step._status(i) for i in range(4)], want)

check("空数据当前步为 -1", Step()._current, -1)

# ---------------------------------------------------------------------------
section("状态推导：显式覆盖与别名")
pinned = Step(steps=[StepItem("a", status="fail"), StepItem("b")], active=0)
check("status='fail' 归一为 error", pinned._status(0), "error")
check("未钉死的仍按 active 推导", pinned._status(1), "wait")

swapped = Step(steps=ITEMS, active=1, process_status="error", finish_status="error")
check("process_status 可整体改写", swapped._status(1), "error")
check("finish_status 可整体改写", swapped._status(0), "error")

bogus = Step(steps=ITEMS, active=1, process_status="nonsense")
check("非法状态名回落 process", bogus._status(1), "process")

check("status='success' 归一为 finish",
      Step(steps=[StepItem("a", status="success")], active=0)._status(0), "finish")

# ---------------------------------------------------------------------------
section("连接线：只给走过的段上色")
step = Step(steps=ITEMS, active=2)
check("首步左侧无段（None）", step._line_color(0), None)
check("段1 已完成 → 主色", step._line_color(1), ft.Colors.PRIMARY)
check("段2 已完成 → 主色", step._line_color(2), ft.Colors.PRIMARY)
check("段3 未走到 → 灰", step._line_color(3), ft.Colors.OUTLINE_VARIANT)
check("末步右侧无段（None）", step._line_color(4), None)

fresh = Step(steps=ITEMS, active=-1)
check("active=-1 时所有段都是灰", fresh._line_color(1), ft.Colors.OUTLINE_VARIANT)

# ---------------------------------------------------------------------------
section("横向：等宽格 + 半段线占位")
h = Step(steps=ITEMS, active=1)
check("横向根是 Row", type(h.content).__name__, "Row")
check("每步一格", len(h.content.controls), 4)
check("每格都是 flex 子项（等宽的前提）",
      [c.expand for c in h.content.controls], [True] * 4)

head = h.content.controls[0].content.controls[0]
check("头部一行 = 左线 + 圆点 + 右线", len(head.controls), 3)
check("首步左线透明但占位", head.controls[0].bgcolor, ft.Colors.TRANSPARENT)
check("首步右线（段1）是主色", head.controls[2].bgcolor, ft.Colors.PRIMARY)
check("格内文字默认居中", h._centered, True)

left = Step(steps=ITEMS, active=1, align_center=False)
check("align_center=False 时左对齐", left._centered, False)

# ---------------------------------------------------------------------------
section("垂直：轴轨 + 首行对齐")
v = Step(steps=ITEMS, active=1, direction="vertical")
check("垂直根是 Column", type(v.content).__name__, "Column")
check("垂直不居中文字", v._centered, False)
first_row = v.content.controls[0]
check("一行 = 轴轨 + 内容（STRETCH 需要 intrinsic_height）",
      (type(first_row).__name__, first_row.intrinsic_height), ("Row", True))
rail, body = first_row.controls
check("轴轨宽度 = 圆点直径", rail.width, v.dot_size)
check("轴轨里是线 + 圆点", len(rail.controls), 2)
check("首步线从圆点中心起画", rail.controls[0].top, v.dot_size / 2)
check("内容列占满剩余宽度", body.expand, True)

# ---------------------------------------------------------------------------
section("简洁模式：单行 + 横向滚动")
s = Step(steps=ITEMS, active=1, simple=True)
check("简洁根是 Row", type(s.content).__name__, "Row")
check("不换行（wrap 会在松约束下塌成一项一行）", s.content.wrap, False)
check("溢出可横向滚动", s.content.scroll, ft.ScrollMode.AUTO)
check("步骤之间插箭头：4 步 → 7 个控件", len(s.content.controls), 7)

# ---------------------------------------------------------------------------
section("点击：就地更新 + 只回调一次")
calls: list[int] = []
clickable = Step(steps=ITEMS, active=0, simple=True, on_change=calls.append)
check("接了 on_change 才可交互", clickable._interactive(), True)
clickable._select(2)
check("点击后 active 更新", clickable.active, 2)
check("点击后状态跟着变", [clickable._status(i) for i in range(3)],
      ["finish", "finish", "process"])
check("回调收到下标", calls, [2])
clickable._select(2)
check("重复点当前步不重复回调", calls, [2])

plain = Step(steps=ITEMS, active=0)
check("没接 on_change 时不可交互", plain._interactive(), False)

# ---------------------------------------------------------------------------
section("入参与边界")
by_dict = Step(steps=[{"title": "A"}, {"title": "B", "description": "说明"}], active=0)
check("字典入参可归一", by_dict._items[1].description, "说明")
check("空 steps 给空 Row", type(Step().content).__name__, "Row")
one = Step(steps=[StepItem("唯一一步")], active=0)
check("单步：左右线都无段", (one._line_color(0), one._line_color(1)), (None, None))

# ---------------------------------------------------------------------------
print(f"\nRESULT: {'ALL PASS' if not _fails else f'{len(_fails)} FAILED'}"
      f"  (passed={_passed})")
for f in _fails:
    print("  FAIL", f)
sys.exit(1 if _fails else 0)
