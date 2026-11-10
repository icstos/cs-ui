"""文本组的纯逻辑单测（不需要窗口）。

覆盖：Quote 的结构不变量（竖条靠 STRETCH 拉满，因而**必须**开 intrinsic_height）、
引文与署名的分层、位置参数兼容、重复 init 不丢内容、底色的默认与覆盖。

用法::

    python scripts/_text_logic.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import flet as ft

from ui.core import typography
from ui.core.tokens import FONT_SIZE, RADIUS, SPACE
from ui.display.text import (
    Header_1,
    Header_2,
    Header_3,
    Header_4,
    Header_5,
    Header_6,
    Quote,
    SubTitle,
    Title,
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


def check_true(name: str, ok: bool, detail: str = "") -> None:
    global _passed
    if ok:
        _passed += 1
        print(f"PASS  {name}{('  ' + detail) if detail else ''}")
    else:
        _fails.append(f"{name}{('  ' + detail) if detail else ''}")
        print(f"FAIL  {name}{('  ' + detail) if detail else ''}")


# ---------------------------------------------------------------------------
section("Quote：竖条 + 正文的结构")
q = Quote("引文正文", attribution="出处 · 作者")
row = q.content
check("正文容器是 Row", type(row).__name__, "Row")
# 这条断言守的是一个渲染期的坑：Row 在 Column 里高度无界，STRETCH 会把
# 「无限高」的紧约束塞给竖条，Flutter 断言失败后整棵渲染树退回错误态 ——
# 现象是整页控件缩成 0 高、全部叠在左上角，而 Python 侧一切正常。
# intrinsic_height 先量出固有高度再拉伸，是唯一解法。
check("Row 开了 intrinsic_height", row.intrinsic_height, True)
check("Row 纵向 STRETCH", row.vertical_alignment, ft.CrossAxisAlignment.STRETCH)
check("竖条 + 正文两列", len(row.controls), 2)

bar, body = row.controls
check("竖条宽 3px", bar.width, 3)
check("竖条没有显式高度（靠拉伸）", bar.height, None)
check("竖条是主色", bar.bgcolor, ft.Colors.PRIMARY)
check("竖条圆角取满档", bar.border_radius, RADIUS["full"])
check("正文占满剩余宽度", body.expand, True)

lines = body.content
check("正文用 Column 串行", type(lines).__name__, "Column")
check("引文 + 署名两行", len(lines.controls), 2)
quote_text, sign = lines.controls
# 引文的三件套现在都在 style 里（字号 / 行高 / 字距），控件上的 size/color 反而是 None。
check("引文斜体", quote_text.style.italic, True)
check("引文字号取正文档", quote_text.style.size, FONT_SIZE["body"])
check("引文用次要文字色", quote_text.style.color, ft.Colors.ON_SURFACE_VARIANT)
check(
    "引文行高取长文档（比 UI 正文松）",
    quote_text.style.height,
    typography.LEADING_PROSE,
)
check_true("引文行高确实比正文松", typography.LEADING_PROSE > typography.ROLES["body"].leading)
check("署名带破折号前缀", sign.value, "—— 出处 · 作者")
check("署名比引文小一档", sign.style.size, FONT_SIZE["small"])

# ---------------------------------------------------------------------------
section("Quote：入参数种写法")
check("位置参数落进 value", Quote("一句话").value, "一句话")
check("关键字参数", Quote(value="a", attribution="b").value, "a")
check("不传 attribution 时只有一行", len(Quote("a").content.controls[1].content.controls), 1)
check(
    "多行引文原样保留",
    Quote("第一行\n第二行").content.controls[1].content.controls[0].value,
    "第一行\n第二行",
)

# init 被再次调用（重建 / 重新挂载）时内容不能丢
q2 = Quote("原话", attribution="某人")
q2.init()
check("重复 init 后引文仍在", q2.value, "原话")
check("重复 init 后署名仍在", q2.content.controls[1].content.controls[-1].value, "—— 某人")

# ---------------------------------------------------------------------------
section("Quote：底色与内边距")
check(
    "默认底色 = 主色 5%",
    q.bgcolor,
    ft.Colors.with_opacity(0.05, ft.Colors.PRIMARY),
)
check("默认圆角", q.border_radius, RADIUS["sm"])
check("默认内边距左右 16", q.padding.left, SPACE["4"])
check("默认内边距上下 12", q.padding.top, SPACE["3"])
custom = Quote("a", bgcolor=ft.Colors.ERROR, border_radius=12)
check("调用方给的底色不被覆盖", custom.bgcolor, ft.Colors.ERROR)
check("调用方给的圆角不被覆盖", custom.border_radius, 12)

# ---------------------------------------------------------------------------
section("Heading：别名与六档层级")
check("Title 就是 Header_1", Title is Header_1, True)
check("SubTitle 就是 Header_2", SubTitle is Header_2, True)

heads = [cls() for cls in (Header_1, Header_2, Header_3, Header_4, Header_5, Header_6)]
sizes = [h.size for h in heads]
# 这一条曾经是红的：H2 走 M3 的 headline_large 槽、H3 走 headline_medium，而主题把
# 两个槽钉到 24 / 28 —— H2 比 H3 还小，层级在视觉上反了。
check_true("六档字号严格递减", all(a > b for a, b in zip(sizes, sizes[1:])), str(sizes))
check("H1 = display_lg 档", sizes[0], typography.ROLES["display_lg"].size)
check("H6 = 正文大小（靠字重站住）", sizes[-1], FONT_SIZE["body"])
check_true(
    "字重也逐级不增",
    all(
        int(a.weight.value[1:]) >= int(b.weight.value[1:])
        for a, b in zip(heads, heads[1:])
    ),
)
check_true(
    "每档行高都跟自己的字号走（不是同一个数）",
    len({h.style.height for h in heads}) >= 4,
    str([h.style.height for h in heads]),
)
check_true(
    "大字收紧字距、小字放宽",
    heads[0].style.letter_spacing < 0 < heads[-1].style.letter_spacing + 0.001,
)
check("调用方覆盖字号后行高重算", Header_3(size=30).style.height, typography.leading(30))

# ---------------------------------------------------------------------------
print(f"\n{_passed} passed, {len(_fails)} failed")
if _fails:
    for f in _fails:
        print("  -", f)
    raise SystemExit(1)
