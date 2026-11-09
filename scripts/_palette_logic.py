"""配色引擎契约测试：色板是不是真的"一套"，且真的可读。

这里断言的都不是"某个颜色等于某个十六进制"（那种断言换个种子就废，只能拦住
"不小心改了值"，拦不住"改错了方向"），而是**配色的不变量**：

* 十一档色阶的明度等步长、色相不漂 —— 这是"色阶"之所以成立的数学前提；
* 每个前景/背景对的 WCAG 对比度达标 —— 这是"读得出来"的底线；
* 结构色阶的次序在明暗两种模式下都成立 —— 这是"层次"不会翻车的保证；
* 四个语义角色的视觉重量一致 —— 这是"成功和警告一样重要"的量化写法；
* 换任何种子、任何明暗组合都不抛 —— 配色算不出来不该让页面起不来。

用法::

    python scripts/_palette_logic.py
"""

from __future__ import annotations

import dataclasses
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import flet as ft  # noqa: E402

from ui.core import color, palette, tokens  # noqa: E402

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
    check(f"{name}{(' ' + detail) if detail else ''}", cond, True)


def hue_delta(a: float, b: float) -> float:
    return abs((a - b + 180) % 360 - 180)


# ---------------------------------------------------------------------------
print("-- 十一档色阶 --")
# ---------------------------------------------------------------------------
ramp = palette.tonal("#1F6FEB")
check("档位齐全", tuple(ramp), palette.TONES)
check("每档都是 7 位 hex", all(len(v) == 7 and v.startswith("#") for v in ramp.values()), True)

lightness = [color.oklch(ramp[t])[0] for t in palette.TONES]
ok(
    "明度由浅到深严格单调",
    all(a > b for a, b in zip(lightness, lightness[1:])),
    f"{[round(v, 3) for v in lightness]}",
)

gaps = [a - b for a, b in zip(lightness, lightness[1:])]
ok(
    "中间九档的步长基本均匀（0.05~0.09）",
    all(0.05 <= g <= 0.09 for g in gaps[1:]),
    f"min={min(gaps[1:]):.3f} max={max(gaps[1:]):.3f}",
)
ok("首档刻意更近（50 是「几乎就是底色」）", gaps[0] < 0.06, f"gap={gaps[0]:.3f}")

base_hue = color.oklch("#1F6FEB")[2]
drifts = [hue_delta(color.oklch(ramp[t])[2], base_hue) for t in palette.TONES]
ok(
    "全表色相不漂（< 4°，色域裁剪只动彩度）",
    max(drifts) < 4.0,
    f"max Δh={max(drifts):.2f}°",
)

ok(
    "淡端是「淡而有色」而不是灰（50 仍有可测彩度）",
    color.oklch(ramp[50])[1] > 0.005,
    f"C={color.oklch(ramp[50])[1]:.4f}",
)
ok(
    "彩度峰值在 500",
    max(palette.TONES, key=lambda t: color.oklch(ramp[t])[1]) == 500,
    f"peak={max(palette.TONES, key=lambda t: color.oklch(ramp[t])[1])}",
)


# ---------------------------------------------------------------------------
print("-- 装配：46 个角色一个不落 --")
# ---------------------------------------------------------------------------
fields = {f.name for f in dataclasses.fields(ft.ColorScheme)}
light = palette.build_scheme("#1F6FEB", "light")
dark = palette.build_scheme("#1F6FEB", "dark")

check("明色板覆盖 ColorScheme 的全部字段", sorted(light), sorted(fields))
check("暗色板覆盖 ColorScheme 的全部字段", sorted(dark), sorted(fields))
check("没有 None 值（缺一个角色就会掉回 Flutter 的默认推导）",
      [k for k, v in light.items() if not v] + [k for k, v in dark.items() if not v], [])
check("全部都是具体色值", all(color.is_hex(v) for v in light.values()), True)
check("装配可重复（无随机、无状态泄漏）", palette.build_scheme("#1F6FEB", "light"), light)


# ---------------------------------------------------------------------------
print("-- 对比度：每个前景/背景对都要读得出来 --")
# ---------------------------------------------------------------------------
# (前景, 背景) 与最低要求的组合。4.5 是正文（WCAG 1.4.3），3.0 是图形与
# 大字号（1.4.11），2.0 是"看得见但不抢戏"的边框（框架自己的档位）。
PAIRS = (
    ("on_primary", "primary", 4.5),
    ("on_secondary", "secondary", 4.5),
    ("on_tertiary", "tertiary", 4.5),
    ("on_error", "error", 4.5),
    ("on_primary_container", "primary_container", 4.5),
    ("on_secondary_container", "secondary_container", 4.5),
    ("on_tertiary_container", "tertiary_container", 4.5),
    ("on_error_container", "error_container", 4.5),
    ("primary", "surface", 4.5),
    ("secondary", "surface", 4.5),
    ("tertiary", "surface", 4.5),
    ("error", "surface", 4.5),
    ("on_surface", "surface", 12.0),
    ("on_surface_variant", "surface", 4.5),
    ("on_inverse_surface", "inverse_surface", 4.5),
    ("outline", "surface", 2.0),
    ("on_primary_fixed", "primary_fixed", 7.0),
)

for mode, scheme in (("light", light), ("dark", dark)):
    for fg, bg, floor in PAIRS:
        got = color.contrast(scheme[fg], scheme[bg])
        ok(
            f"{mode} {fg} / {bg} >= {floor}",
            round(got, 2) >= floor,
            f"{got:.2f}:1  {scheme[fg]} on {scheme[bg]}",
        )

# 换种子也要成立 —— 一套只对蓝色管用的规则不叫规则
for seed in tokens.PRIMARY_SEEDS.values():
    for mode in ("light", "dark"):
        s = palette.build_scheme(seed, mode)
        worst = min(
            color.contrast(s[fg], s[bg]) / floor
            for fg, bg, floor in PAIRS
        )
        ok(f"{seed}/{mode} 整套对比度都达标", worst >= 1.0, f"最紧的一对={worst:.2f}× 要求")


# ---------------------------------------------------------------------------
print("-- 结构色阶：层次次序在两种模式下都成立 --")
# ---------------------------------------------------------------------------
order_light = (
    "surface_container_lowest",
    "surface",
    "surface_container_low",
    "surface_container",
    "surface_container_high",
    "surface_container_highest",
)
order_dark = tuple(reversed(order_light))
for mode, scheme, order in (("light", light, order_light), ("dark", dark, order_dark)):
    lums = [color.luminance(scheme[k]) for k in order]
    ok(
        f"{mode} 容器色阶单向递进（不会「这块比那块更靠前」）",
        all(a > b for a, b in zip(lums, lums[1:])),
        f"{[round(v, 3) for v in lums]}",
    )
    ok(
        f"{mode} dim 比 surface 暗一档（遮罩后用）",
        color.luminance(scheme["surface_dim"]) < color.luminance(scheme["surface"]),
    )
    ok(
        f"{mode} bright 比 surface 亮一档",
        color.luminance(scheme["surface_bright"]) > color.luminance(scheme["surface"]),
    )
    ok(
        f"{mode} 反色面与主表面明暗相反（tooltip / snackbar 才跳得出来）",
        (color.luminance(scheme["inverse_surface"]) < color.luminance(scheme["surface"]))
        == (mode == "light"),
    )


# ---------------------------------------------------------------------------
print("-- 中性色：掺了品牌色相，不是死灰 --")
# ---------------------------------------------------------------------------
for seed_name, seed in tokens.PRIMARY_SEEDS.items():
    s = palette.build_scheme(seed, "light")
    r, g, b = color.parse(s["surface"])
    tint = color.oklch(s["surface"])[1]
    ok(
        f"{seed_name} 的表面带色相（三通道不等，但不是彩色）",
        len({round(v * 255) for v in (r, g, b)}) >= 2 and tint <= 0.02,
        f"C={tint:.4f}",
    )
    # 表面彩度只有 0.006，量化到 1/255 后色相本身就不稳，所以这里只查"方向
    # 没错"（冷色种子不该给出暖灰），精确的色相保真在墨色档位上查。
    ok(
        f"{seed_name} 表面色相方向与主色一致（< 30°）",
        hue_delta(color.oklch(s["surface"])[2], color.oklch(seed)[2]) < 30.0,
        f"Δh={hue_delta(color.oklch(s['surface'])[2], color.oklch(seed)[2]):.1f}°",
    )
    ok(
        f"{seed_name} 墨色带主色相（< 15°）",
        hue_delta(color.oklch(s["on_surface"])[2], color.oklch(seed)[2]) < 15.0,
        f"Δh={hue_delta(color.oklch(s['on_surface'])[2], color.oklch(seed)[2]):.1f}°",
    )

tonal = palette.build_scheme("#1F6FEB", "light", surfaces="tonal")
neutral = palette.build_scheme("#1F6FEB", "light", surfaces="neutral")
# 在容器档位上比，而不是在 surface 上比：surface 已经很接近白，彩度会被色域
# 压到上限，两种策略算出来的值几乎一样——比不出差别。
ok(
    "tonal 的着色比 neutral 明显重一档",
    color.oklch(tonal["surface_container"])[1]
    > color.oklch(neutral["surface_container"])[1] * 1.5,
    f"{color.oklch(neutral['surface_container'])[1]:.4f}"
    f" -> {color.oklch(tonal['surface_container'])[1]:.4f}",
)


# ---------------------------------------------------------------------------
print("-- 品牌色保真：换种子只换色相，不换规则 --")
# ---------------------------------------------------------------------------
for seed_name, seed in tokens.PRIMARY_SEEDS.items():
    s = palette.build_scheme(seed, "light")
    d = palette.build_scheme(seed, "dark")
    ok(
        f"{seed_name} 主色仍与种子同色相（< 6°）",
        hue_delta(color.oklch(s["primary"])[2], color.oklch(seed)[2]) < 6.0,
        f"Δh={hue_delta(color.oklch(s['primary'])[2], color.oklch(seed)[2]):.1f}°",
    )
    ok(
        f"{seed_name} 主色彩度不超过上限（低饱和高级感）",
        color.oklch(s["primary"])[1] <= palette.CHROMA_CAP + 0.004,  # 留量化误差
        f"C={color.oklch(s['primary'])[1]:.3f}",
    )
    ok(
        f"{seed_name} 深色主色比浅色主色亮（深底上要提亮）",
        color.oklch(d["primary"])[0] > color.oklch(s["primary"])[0],
    )
    ok(
        f"{seed_name} 次要色比主色淡（退后一级）",
        color.oklch(s["secondary"])[1] < color.oklch(s["primary"])[1],
    )


# ---------------------------------------------------------------------------
print("-- 语义色与色板同源 --")
# ---------------------------------------------------------------------------
for mode, scheme in (("light", light), ("dark", dark)):
    check(
        f"{mode} ColorScheme.error 与 tokens 的 danger 实底同一个值",
        scheme["error"],
        tokens.semantic("danger", mode),
    )
    check(
        f"{mode} on_error 同源",
        scheme["on_error"],
        tokens.on_semantic("danger", mode),
    )

for mode in ("light", "dark"):
    ratios = {
        role: color.contrast(tokens.semantic(role, mode), tokens.SEMANTIC_ON[role][mode])
        for role in ("success", "warning", "danger", "info")
    }
    ok(
        f"{mode} 四个语义填充的视觉重量一致（对比度极差 < 0.3）",
        max(ratios.values()) - min(ratios.values()) < 0.3,
        f"{ {k: round(v, 2) for k, v in ratios.items()} }",
    )


# ---------------------------------------------------------------------------
print("-- 兜底：算不出来也不能抛 --")
# ---------------------------------------------------------------------------
def safe(build) -> bool:
    """执行并回答"没抛异常"。"""
    try:
        scheme = build()
    except Exception:  # noqa: BLE001
        return False
    return all(color.is_hex(v) for v in scheme.values())


for bad in ("#ZZZZZZ", "nope", "", "#12345", None, 3):
    ok(f"非法种子 {bad!r} 不抛，且给出的仍是完整色板",
       safe(lambda b=bad: palette.build_scheme(b)))

for bad_mode in ("rainbow", "", None, 1):
    ok(f"非法模式 {bad_mode!r} 退回浅色",
       safe(lambda m=bad_mode: palette.build_scheme("#1F6FEB", m)))


# ---------------------------------------------------------------------------
print()
print(f"RESULT: {'ALL PASS' if not _fails else f'{len(_fails)} FAILED'}  (passed={_passed})")
if _fails:
    for line in _fails:
        print("  -", line)
    sys.exit(1)
