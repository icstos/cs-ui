"""排印系统契约测试（不需要窗口）。

:mod:`ui.core.typography` 的价值不在"数字好看"，而在**每条数字都能追溯到一个
可断言的规律**。所以这里测的不是具体像素，而是规律本身：

1. **行高律** —— 正文恰好 φ（1.618），字号越大行高越紧，且全程落在 1.2~1.75；
2. **光学字距** —— 按 em 记在 ±0.025 内（超出就不是补偿而是换字体），且随字号
   单调收紧；等宽场景能一键归零；
3. **字重梯度** —— 正文 400、标题 600、显示级 700，小字不低于 500（防断笔）；
4. **四种度量成套** —— 每个档位都有字号 / 行高 / 字距 / 字重，缺一项就会让字号
   与行高脱节（曾经的 H2 比 H3 小即是此病）；
5. **节奏与分栏** —— RHYTHM 全在 4px 网格上且相邻比接近 φ；三分法则在 12 栏
   网格上确实是 8+4，黄金分割是 7+5；
6. **对比度** —— 正文 / 次要文字 / 边框对**每一层表面**都达标本项目的目标值
   （AA 4.5 留余量 5.0、图形 2.2），七个品牌色 × 明暗两种模式全跑一遍。

用法::

    python scripts/_typography_logic.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import flet as ft  # noqa: E402

from ui.core import color, palette, typography  # noqa: E402
from ui.core.theme import text_theme  # noqa: E402
from ui.core.tokens import FONT_SIZE, PRIMARY_SEEDS  # noqa: E402

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


def check_true(name: str, ok: bool, detail: str = "") -> None:
    global _passed
    if ok:
        _passed += 1
        print(f"PASS  {name}{('  ' + detail) if detail else ''}")
    else:
        _fails.append(f"{name}{('  ' + detail) if detail else ''}")
        print(f"FAIL  {name}{('  ' + detail) if detail else ''}")


def section(title: str) -> None:
    print(f"\n== {title} ==")


# ---------------------------------------------------------------------------
section("行高律：正文 φ，大字收紧")
check("正文行高 = φ", typography.ROLES["body"].leading, 1.618)
check("正文锚点 14px", FONT_SIZE["body"], 14)
leadings = [typography.ROLES[n].leading for n in FONT_SIZE]
check_true("字号越大行高越紧（严格单调）", all(a > b for a, b in zip(leadings, leadings[1:])))
check_true(
    "行高全程落在 1.2~1.75（低于 1.2 会粘连，高于 1.75 段落散架）",
    all(1.2 <= v <= 1.75 for v in leadings),
    str(leadings),
)
check("36px 收到 1.222（接近标题专用 1.2）", typography.ROLES["display_lg"].leading, 1.222)
check("11px 放到 1.672（小字要更松）", typography.ROLES["caption"].leading, 1.672)
check("行盒 = 字号 × 行高", typography.ROLES["body"].line_box, 22.7)
check_true(
    "行盒随字号单调增大",
    all(
        typography.ROLES[a].line_box < typography.ROLES[b].line_box
        for a, b in zip(FONT_SIZE, list(FONT_SIZE)[1:])
    ),
)
check_true("长文行高比 UI 正文松", typography.LEADING_PROSE > typography.ROLES["body"].leading)
check_true("代码行高比正文紧", typography.LEADING_CODE < typography.ROLES["body"].leading)

# ---------------------------------------------------------------------------
section("光学字距：按 em 记，随字号单调收紧")
for name in FONT_SIZE:
    em = typography.ROLES[name].em_tracking
    check_true(f"{name} 字距在 ±0.025em 内", abs(em) <= 0.025, f"{em:+.4f}em")
ems = [typography.ROLES[n].em_tracking for n in FONT_SIZE]
check_true("字号越大字距越紧（em 单调递减）", all(a > b for a, b in zip(ems, ems[1:])), str(ems))
check("正文字距为 0（中文正文加字距会散）", typography.ROLES["body"].tracking, 0.0)
check_true("最小字号放宽字距", typography.ROLES["caption"].tracking > 0)
check_true("最大字号收紧字距", typography.ROLES["display_lg"].tracking < 0)
check("等宽场景可归零", typography.text_style("body", tracking=0).letter_spacing, 0)
# 字阶内不许有两套口径：tracking(size) 必须与档位表逐项相等。
# 这条曾经红过 —— 旧实现无论字号在哪都走 -0.0016em/px 外推，36px 得 -1.27，
# 而档位表里 display_lg 是 -0.80，同一个 36px 两个字距。
_by_size = sorted(FONT_SIZE.items(), key=lambda kv: kv[1])
check(
    "字阶上的字号取档位值（同一字号不许两个字距）",
    [typography.tracking(size) for _, size in _by_size],
    [typography.ROLES[name].tracking for name, _ in _by_size],
)
check("正文处不出现负零", typography.tracking(14), 0.0)
# 字阶外按 em 插值，两端沿最近一段外推，并夹在 MAX_TRACKING 内。
_offscale = (10, 13, 18, 22, 30, 40, 48, 64)
check_true(
    "字阶外的字距仍在 ±MAX_TRACKING 内",
    all(
        abs(typography.tracking(size) / size) <= typography.MAX_TRACKING + 1e-9
        for size in _offscale
    ),
    str([(s, round(typography.tracking(s) / s, 4)) for s in _offscale]),
)
check_true(
    "字阶外随字号单调收紧",
    all(
        typography.tracking(a) / a > typography.tracking(b) / b
        for a, b in zip(_offscale, _offscale[1:])
    ),
)
check_true(
    "13px 行内代码插值后比正文松一点（不是掉回 0）",
    typography.tracking(13) > typography.tracking(14),
    f"{typography.tracking(13):+.2f}px",
)

# ---------------------------------------------------------------------------
section("字重：正文 400，标题 600，显示 700")
check("正文 400", typography.ROLES["body"].weight, ft.FontWeight.W_400)
check("标题 600", typography.ROLES["headline"].weight, ft.FontWeight.W_600)
check("显示级 700", typography.ROLES["display_lg"].weight, ft.FontWeight.W_700)
check("小字不低于 500（防断笔）", typography.ROLES["caption"].weight, ft.FontWeight.W_500)
check(
    "六级标题字重只在两档之间（避免合成粗体过多）",
    {typography.HEADING_WEIGHT[i] for i in range(1, 7)},
    {"bold", "semibold"},
)

# ---------------------------------------------------------------------------
section("四件套齐全 + text_style 覆盖")
for name, spec in typography.ROLES.items():
    check_true(
        f"{name} 有字号 / 行高 / 字距 / 字重",
        all(
            (
                spec.size > 0,
                spec.leading > 0,
                isinstance(spec.tracking, float),
                spec.weight is not None,
            )
        ),
    )
st = typography.text_style("headline_lg", color=ft.Colors.PRIMARY)
check("text_style 带颜色", st.color, ft.Colors.PRIMARY)
check("text_style 带行高", st.height, typography.ROLES["headline_lg"].leading)
check("text_style 带字距", st.letter_spacing, typography.ROLES["headline_lg"].tracking)
check("text_style 带字号", st.size, 24)
check("覆盖行高", typography.text_style("body", leading=2.0).height, 2.0)
check("覆盖字号", typography.text_style("body", size=13).size, 13)
check("非法档位退回正文", typography.role("nope").name, "body")

# ---------------------------------------------------------------------------
section("节奏：4px 网格 + φ 梯级")
values = [typography.RHYTHM[k] for k in ("hair", "block", "paragraph", "group", "section", "page")]
check_true("全部落在 4px 网格", all(v % typography.GRID == 0 for v in values), str(values))
check_true("严格递增", all(a < b for a, b in zip(values, values[1:])))
ratios = [b / a for a, b in zip(values, values[1:])]
check_true(
    "相邻比在 1.4~2.1（贴着 φ 上下）",
    all(1.4 <= r <= 2.1 for r in ratios),
    str([round(r, 2) for r in ratios]),
)

# ---------------------------------------------------------------------------
section("三分法则：12 栏上的分栏")
main, aside = typography.cols("thirds")
check("三分法则 = 8 + 4", (main["md"], aside["md"]), (8, 4))
check("两栏在 xs 上堆叠", (main["xs"], aside["xs"]), (12, 12))
main_g, aside_g = typography.cols("golden")
check("黄金分割 = 7 + 5（7.42 取整）", (main_g["md"], aside_g["md"]), (7, 5))
check("每栏之和恒为 12", {m["md"] + a["md"] for m, a in (typography.cols(n) for n in typography.SPLIT)}, {12})
check("非法分栏名退回三分法则", typography.split("nope"), (2, 1))

# ---------------------------------------------------------------------------
section("对比度：所有品牌色 × 明暗 × 所有表面")
SURFACES = ("lowest", "bright", "surface", "low", "container", "high", "highest", "dim")
TARGETS = {"ink": 7.0, "ink_soft": 4.5, "outline": 2.2}
worst: dict[str, float] = {k: 99.0 for k in TARGETS}
for seed in PRIMARY_SEEDS.values():
    for mode in ("light", "dark"):
        n = palette.neutral(seed)
        for role, target in TARGETS.items():
            for stop in SURFACES:
                ratio = color.contrast(n[f"{mode}.{role}"], n[f"{mode}.{stop}"])
                worst[role] = min(worst[role], ratio)
        check_true(
            f"{seed} {mode} 二级文字达标",
            min(
                color.contrast(n[f"{mode}.ink_soft"], n[f"{mode}.{s}"]) for s in SURFACES
            )
            >= 4.8,
        )
for role, target in TARGETS.items():
    check_true(
        f"{role} 最差值 >= {target}",
        worst[role] >= target,
        f"{worst[role]:.2f}",
    )
check_true(
    "二级文字的余量够（AA 4.5 之上再留 0.3）",
    worst["ink_soft"] >= 4.8,
    f"{worst['ink_soft']:.2f}",
)

# ---------------------------------------------------------------------------
section("主题槽位：与字阶一致且 H1 > … > H6")
theme = text_theme()
# 只看"标题性质"的四个槽位：title_large 与 headline_small 在 M3 里本来就是同一档
# （都是 20），把两者放进同一条链上比较会把"同值"误判成"层级反了"。
slots = [
    theme.display_small,
    theme.headline_large,
    theme.headline_medium,
    theme.headline_small,
    theme.title_medium,
]
slot_sizes = [s.size for s in slots]
check_true(
    "标题槽位字号严格递减（曾经 H2 比 H3 小）",
    all(a > b for a, b in zip(slot_sizes, slot_sizes[1:])),
    str(slot_sizes),
)
check_true(
    "内建控件里 title_large 不小于 headline_small（同为 20，不会倒挂）",
    theme.title_large.size >= theme.headline_small.size,
)
check("display_small = 36", slots[0].size, 36)
check("headline_large = 28", slots[1].size, 28)
for name in ("display_small", "body_medium", "label_small"):
    style = getattr(theme, name)
    check_true(
        f"{name} 四件套齐全",
        all((style.size, style.height, style.color is not None)),
    )
check("body_medium 行高 = φ", theme.body_medium.height, 1.618)
check_true("label_small 字距为正", theme.label_small.letter_spacing > 0)
check_true(
    "每个槽位都带颜色（不给就会画成透明）",
    all(getattr(theme, name).color is not None for name in (
        "display_small", "headline_large", "headline_medium", "headline_small",
        "title_large", "title_medium", "title_small", "body_large", "body_medium",
        "body_small", "label_large", "label_medium", "label_small",
    )),
)

# ---------------------------------------------------------------------------
print(f"\n{_passed} passed, {len(_fails)} failed")
if _fails:
    for f in _fails:
        print("  -", f)
    raise SystemExit(1)
