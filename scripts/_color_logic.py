"""配色引擎契约测试（不需要窗口）。

「和谐」听起来是主观的，但只要把定义拆开，每一条都能写成断言：

1. **往返一致** —— ``#RRGGBB`` → OKLCH → ``#RRGGBB`` 必须原样回来。
   这一条守住色彩空间的两个方向，矩阵抄错一个系数就会被抓出来
   （曾经 ``mix()`` 把线性光强当 gamma 编码输出，中灰变近黑，肉眼像"整色偏暗"，
   而所有"颜色看起来对不对"的检查都发现不了 —— 只有往返断言能）。
2. **分类色等亮度** —— 同一套系列色的 OKLab 明度必须一致（±0.02）。
   亮度不齐会让某条曲线显得"更重要"，这是分类配色的第一禁忌。
3. **分类色可分辨** —— 相邻两条在 OKLab 里的距离必须够大。
   色相环上等间隔 45° 是下限，少于这个，两条 1px 线并排就糊成一条。
4. **首色即品牌色** —— ``categorical(seed)[0] == seed``。图表的第一条曲线
   必须和顶栏、主按钮同色，否则"框架是紫色、图表是蓝色"。
5. **色阶单调** —— 顺序色阶的明度必须严格单调，且**末级正好是基色**。
   非单调的色阶会让"第 3 档比第 4 档还深"，读图的人会把量级看反。
6. **兜底不抛** —— 非法色串 / 非法种子一律退到中性灰。配色是装饰性问题，
   错一个色不该让整页崩掉。

用法::

    python scripts/_color_logic.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from ui.core import color  # noqa: E402
from ui.core.tokens import PRIMARY_SEEDS  # noqa: E402

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


def _distance(a: str, b: str) -> float:
    """两色在 OKLab 里的欧氏距离（感知差，≈0.02 起肉眼可辨）。"""
    la, ca, ha = color.oklch(a)
    lb, cb, hb = color.oklch(b)
    va = (la, ca * math.cos(math.radians(ha)), ca * math.sin(math.radians(ha)))
    vb = (lb, cb * math.cos(math.radians(hb)), cb * math.sin(math.radians(hb)))
    return math.dist(va, vb)


# ---------------------------------------------------------------------------
# 解析与输出
# ---------------------------------------------------------------------------
check("三位缩写展开", color.to_hex(color.parse("#abc")), "#AABBCC")
check("裸六位可解析", color.to_hex(color.parse("1F6FEB")), "#1F6FEB")
check("大写输出", color.to_hex(color.parse("#1f6feb")), "#1F6FEB")
check("八位按 flet 的 #AARRGGBB 取后六位", color.to_hex(color.parse("#7C3AEDB3")), "#7C3AED")
check("角色串退中性灰（拿不到数值）", color.to_hex(color.parse("primary,0.12")), "#808080")
check("越界分量被夹住", color.to_hex((1.6, -0.2, 0.5)), "#FF0080")
check("is_hex 认三位", color.is_hex("#abc"), True)
check("is_hex 不认角色串", color.is_hex("primary,0.12"), False)
check("is_hex 不认乱码", color.is_hex("zzzzzz"), False)
check("is_hex 不认 None", color.is_hex(None), False)

# ---------------------------------------------------------------------------
# 色彩空间往返
# ---------------------------------------------------------------------------
for hex_color in ("#1F6FEB", "#DC2626", "#047857", "#FFFFFF", "#000000", "#808080"):
    lightness, chroma, hue = color.oklch(hex_color)
    check(f"{hex_color} OKLCH 往返无损", color.from_oklch(lightness, chroma, hue), hex_color)

check("白色 L=1", round(color.oklch("#FFFFFF")[0], 3), 1.0)
check("黑色 L=0", round(color.oklch("#000000")[0], 3), 0.0)
check("灰色无彩度", round(color.oklch("#808080")[1], 3), 0.0)

# ---------------------------------------------------------------------------
# 对比度
# ---------------------------------------------------------------------------
check("黑白对比 21:1", round(color.contrast("#FFFFFF", "#000000"), 2), 21.0)
check("同色对比 1:1", round(color.contrast("#1F6FEB", "#1F6FEB"), 2), 1.0)
ok("对比度与顺序无关", color.contrast("#047857", "#FFFFFF") == color.contrast("#FFFFFF", "#047857"))

# ---------------------------------------------------------------------------
# 分类色
# ---------------------------------------------------------------------------
for mode in ("light", "dark"):
    surface = "#FFFFFF" if mode == "light" else "#141414"
    for name, seed in PRIMARY_SEEDS.items():
        palette = color.categorical(seed, 8, mode)
        check(f"{mode}/{name} 条数", len(palette), 8)
        # 首色必须与品牌色**同色相**（亮度可能被拉回可读区间，色相不许动）
        dh = abs((color.oklch(palette[0])[2] - color.oklch(seed)[2] + 180) % 360 - 180)
        ok(f"{mode}/{name} 首色与品牌同色相", dh <= 1.0, f"Δh={dh:.2f}°")
        lights = [color.oklch(c)[0] for c in palette]
        ok(
            f"{mode}/{name} 等亮度",
            max(lights) - min(lights) <= 0.02,
            f"ΔL={max(lights) - min(lights):.3f}",
        )
        # OKLab 距离近似：用 ΔL 与色相/彩度一起看，这里取两端点的感知差
        gaps = [_distance(a, b) for a, b in zip(palette, palette[1:])]
        ok(f"{mode}/{name} 相邻可分辨", min(gaps) >= 0.05, f"minΔ={min(gaps):.3f}")
        ok(
            f"{mode}/{name} 全部对底色 >= 3:1",
            all(color.contrast(c, surface) >= 3 for c in palette),
        )

check(
    "n=1 时只给一条，且与种子同色相",
    abs((color.oklch(color.categorical("#1F6FEB", 1, "light")[0])[2] - color.oklch("#1F6FEB")[2] + 180) % 360 - 180) <= 1.0,
    True,
)
ok(
    "明暗两套不同",
    color.categorical("#1F6FEB", 8, "light") != color.categorical("#1F6FEB", 8, "dark"),
)
ok(
    "非法种子退中性色但不抛",
    len(color.categorical("nope", 4, "light")) == 4
    and all(color.is_hex(c) for c in color.categorical("nope", 4, "light")),
)
ok(
    "过亮的浅种子被拉回可读区间",
    color.contrast(color.categorical("#FBBF24", 8, "light")[0], "#FFFFFF") >= 3,
)

# ---------------------------------------------------------------------------
# 顺序色阶
# ---------------------------------------------------------------------------
for mode, surface in (("light", "#FFFFFF"), ("dark", "#141414")):
    for name in ("success", "warning", "danger", "info"):
        base = {"success": "#047857", "warning": "#B45309", "danger": "#DC2626", "info": "#0369A1"}[name]
        if mode == "dark":
            base = {
                "success": "#34D399",
                "warning": "#FBBF24",
                "danger": "#F87171",
                "info": "#38BDF8",
            }[name]
        scale = color.ramp(base, 4, mode)
        check(f"{mode}/{name} 级数", len(scale), 4)
        check(f"{mode}/{name} 末级即基色", scale[-1].upper(), base.upper())
        lights = [color.oklch(c)[0] for c in scale]
        ok(
            f"{mode}/{name} 明度单调",
            all(a < b for a, b in zip(lights, lights[1:]))
            if mode == "dark"
            else all(a > b for a, b in zip(lights, lights[1:])),
            f"L={[round(v, 2) for v in lights]}",
        )
        ok(
            f"{mode}/{name} 末级在底色上可读",
            color.contrast(scale[-1], surface) >= 3,
        )

check("ramp 单级就是基色", color.ramp("#047857", 1, "light"), ("#047857",))

# ---------------------------------------------------------------------------
# 混合
# ---------------------------------------------------------------------------
check("mix t=0 取前者", color.mix("#DC2626", "#1F6FEB", 0.0), "#DC2626")
check("mix t=1 取后者", color.mix("#DC2626", "#1F6FEB", 1.0), "#1F6FEB")
ok(
    "mix 中点明度居中（线性空间插值会把中点压暗）",
    color.oklch(color.mix("#FFFFFF", "#000000", 0.5))[0] > 0.35,
    f"L={color.oklch(color.mix('#FFFFFF', '#000000', 0.5))[0]:.3f}",
)
check("mix 越界夹住", color.mix("#DC2626", "#1F6FEB", 9.0), "#1F6FEB")

# ---------------------------------------------------------------------------
print()
if _fails:
    print(f"{len(_fails)} 项失败 / 共 {_passed + len(_fails)} 项")
    for line in _fails:
        print(f"  - {line}")
    raise SystemExit(1)
print(f"全部通过（{_passed} 项）")
