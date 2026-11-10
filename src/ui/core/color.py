"""配色引擎：把「色彩和谐」变成可计算的约束。

为什么需要单独一个模块：图表要 8 条能互相区分的系列色，热力图要 4 级同色相
的深浅，状态胶囊要淡底 —— 这些都不是 Material 3 的 ``ColorScheme`` 角色能
直接给出的（角色只有"主色/次色/表面"那二十来个，推不出"第 3 级绿"）。在各组件里
手抄十六进制的后果是同一个"绿"有四个值：消息条里是 ``#047857``、按钮里是
``ft.Colors.GREEN``、图表里是 ``#10B981``、热力图里是 ``#216E39``。

本模块只做一件事：**给定一个基色，按感知均匀的规则推出其余颜色**。

* :func:`categorical` —— 分类色。同亮度、同彩度、等间隔色相，第一条就是品牌色。
  等亮度的意义是"没有哪条曲线比别的更抢眼"，这是分类配色的第一原则。
* :func:`ramp` —— 顺序色阶。固定色相，只走明度，末级正好落在基色上，
  于是"热力图最深的那格"与"成功徽标的绿"是同一个绿。
* :func:`contrast` —— WCAG 对比度，给断言用。

底层走 **OKLCH** 而不是 HSL：HSL 里 ``hsl(60, 100%, 50%)`` 的明黄和
``hsl(240, 100%, 50%)`` 的深蓝人眼看来亮度差了 3 倍，所谓"同亮度"根本不成立；
OKLab 是 CIE 的感知均匀空间，同 L 就是真的一样亮。桌面端对比度问题大多来自
"按 HSL 配出来的颜色有一半看不清"，这里从根上避开。

纯函数、不 import flet —— 逻辑测试可以脱离窗口直接跑。
"""

from __future__ import annotations

import math
from functools import lru_cache

__all__ = [
    "categorical",
    "contrast",
    "from_oklch",
    "is_hex",
    "luminance",
    "mix",
    "oklch",
    "parse",
    "ramp",
    "to_hex",
]


# ---------------------------------------------------------------------------
# 解析与输出
# ---------------------------------------------------------------------------
def _digits(color: str) -> str:
    """抽出纯十六进制数字（去掉 ``#``），不合法时返回空串。"""
    text = str(color).strip().removeprefix("#")
    if "," in text:  # "primary,0.12" 这类角色串没有具体数值
        return ""
    if len(text) == 3:
        text = "".join(ch * 2 for ch in text)
    elif len(text) == 8:
        text = text[:6]
    if len(text) != 6:
        return ""
    return text if all(ch in "0123456789abcdefABCDEF" for ch in text) else ""


def is_hex(color: object) -> bool:
    """是不是一个能取到具体数值的颜色串（``#RRGGBB`` / ``#RGB`` / 裸六位）。"""
    return isinstance(color, str) and bool(_digits(color))


def parse(color: str) -> tuple[float, float, float]:
    """``"#RRGGBB"`` / ``"#RGB"`` / ``"RRGGBB"`` → ``(r, g, b)``，分量 0..1。

    flet 的色串还可能是 ``"primary,0.12"`` 这种"角色 + 透明度"。那**不是**具体
    颜色，本模块拿不到数值，退回中性灰而不是抛异常 —— 配色是装饰性问题，
    不该让页面起不来。要区分"中性灰"和"非法输入"，先问 :func:`is_hex`。
    """
    text = _digits(color)
    if not text:
        return (0.5, 0.5, 0.5)
    return tuple(int(text[i : i + 2], 16) / 255 for i in (0, 2, 4))  # type: ignore[return-value]


def to_hex(rgb: tuple[float, float, float]) -> str:
    """``(r, g, b)``（0..1）→ ``"#RRGGBB"``（大写，与全框架的写法一致）。"""
    parts = (round(min(max(c, 0.0), 1.0) * 255) for c in rgb)
    return "#" + "".join(f"{v:02X}" for v in parts)


# ---------------------------------------------------------------------------
# 色彩空间换算
# ---------------------------------------------------------------------------
def _srgb_to_linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _linear_to_srgb(c: float) -> float:
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def _rgb_to_oklab(rgb: tuple[float, float, float]) -> tuple[float, float, float]:
    """线性 sRGB → OKLab（Björn Ottosson 的矩阵）。"""
    r, g, b = (_srgb_to_linear(c) for c in rgb)
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l_, m_, s_ = (math.copysign(abs(v) ** (1 / 3), v) for v in (l, m, s))
    return (
        0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_,
        1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_,
        0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_,
    )


def _oklab_to_rgb(lab: tuple[float, float, float]) -> tuple[float, float, float]:
    """OKLab → 线性 sRGB（可能越界，调用方负责裁剪）。"""
    lightness, a, b = lab
    l_ = lightness + 0.3963377774 * a + 0.2158037573 * b
    m_ = lightness - 0.1055613458 * a - 0.0638541728 * b
    s_ = lightness - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_**3, m_**3, s_**3
    return (
        4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
        -1.2684380046 * l + 2.6097574011 * m - 0.3413193765 * s,
        -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s,
    )


def oklch(color: str) -> tuple[float, float, float]:
    """色串 → ``(L, C, h°)``。``L`` 0..1（0 黑 1 白），``h`` 是角度。"""
    lightness, a, b = _rgb_to_oklab(parse(color))
    chroma = math.hypot(a, b)
    hue = math.degrees(math.atan2(b, a)) % 360
    return (lightness, chroma, hue)


def from_oklch(lightness: float, chroma: float, hue: float) -> str:
    """``(L, C, h°)`` → ``"#RRGGBB"``，**超出 sRGB 色域时降彩度而不是裁分量**。

    直接裁 RGB 分量会把色相改掉（想配一个亮黄，裁完变成土黄），而"这个色相的
    最鲜艳版本"应该由降低彩度得到 —— 色相保住，观感才是同一个家族。
    """
    rad = math.radians(hue)
    lightness = min(max(lightness, 0.0), 1.0)
    cos_h, sin_h = math.cos(rad), math.sin(rad)

    def rgb_at(c: float) -> tuple[float, float, float] | None:
        lin = _oklab_to_rgb((lightness, c * cos_h, c * sin_h))
        if all(-1e-4 <= v <= 1 + 1e-4 for v in lin):
            return tuple(_linear_to_srgb(min(max(v, 0.0), 1.0)) for v in lin)  # type: ignore[return-value]
        return None

    got = rgb_at(chroma)
    if got is not None:
        return to_hex(got)
    lo, hi = 0.0, chroma
    for _ in range(24):
        mid = (lo + hi) / 2
        if rgb_at(mid) is None:
            hi = mid
        else:
            lo = mid
    return to_hex(rgb_at(lo) or rgb_at(0.0) or (0.5, 0.5, 0.5))


# ---------------------------------------------------------------------------
# 对比度
# ---------------------------------------------------------------------------
def luminance(color: str) -> float:
    """WCAG 相对亮度。"""
    r, g, b = (_srgb_to_linear(c) for c in parse(color))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    """两色的 WCAG 对比度（1..21）。正文要求 >= 4.5，大字/图形 >= 3。"""
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


# ---------------------------------------------------------------------------
# 派生
# ---------------------------------------------------------------------------
#: 分类色的亮度 / 彩度**允许区间**：整张表取种子自己的 L/C，再夹进这个区间。
#:
#: 取种子而不是写死绝对值，是为了让调色板"带着品牌色的性格"：蓝种子推出来偏
#: 冷、橙种子偏暖。夹区间则兜住极端种子 —— 近黑的 slate 若原样进图表，某一条
#: 曲线会比别的重一倍；近白的浅黄压在白底上则根本看不见。
#:
#: 下界 0.56 / 上界 0.66：在这个亮度带里，任意色相压在 ``#FFFFFF`` 上都有
#: 3:1 以上（图形可读），压在 ``#141414`` 上也够亮。
_SERIES_BAND = {
    "light": {"l": (0.56, 0.66), "c": (0.11, 0.18)},
    "dark": {"l": (0.66, 0.80), "c": (0.10, 0.18)},
}


def _clamp(value: float, lo: float, hi: float) -> float:
    return min(max(value, lo), hi)


@lru_cache(maxsize=128)
def categorical(seed: str, n: int = 8, mode: str = "light") -> tuple[str, ...]:
    """由品牌色派生 ``n`` 条**等亮度**的分类色。

    规则是四条：

    1. **第一条与品牌色同色相**。图表第一条曲线于是永远与顶栏、主按钮同一个
       色相 —— 换主色时整套图跟着换，不再是"框架是紫色、图表第一条是蓝色"。
       它不一定是种子那个字面值：种子偏暗偏亮时会被拉回可读区间（见
       :data:`_SERIES_BAND`），但**色相一度都不动**。
    2. **亮度与彩度全表统一**（都取种子的 L/C 再夹进区间）。这一条最容易
       被忽略：如果绿深黄浅，看图的人会以为绿色那条"更重要"。统一之后，
       强调只由线宽和位置表达。
    3. **色相等间隔绕一圈**（``360 / n``）。相邻相隔 45°（n=8）在 OKLab 里
       的距离约 0.09，是"仍能分辨"的下限；间距再小，两条 1px 曲线并排就
       分不出来了。
    4. 首色之后按色相环 **反向** 排（-45°、-90°…）而不是正向。正向下来
       第一对是"蓝 → 紫"，两条都靠冷端，最需要区分的相邻系列反而最像；
       反向则让第二条落在青绿上，与蓝的差别一眼可见。

    彩度统一会有一个副作用：某些色相（黄、青）在给定彩度下超出 sRGB 色域，
    由 :func:`from_oklch` 降彩度吸收，观感上会略淡一点，但仍然比"手挑八个
    网页安全色"整齐得多。

    Args:
        seed: 品牌色（``"#1F6FEB"``）。非法值退回中性灰的色相，不会抛。
        n: 需要几条，默认 8（框架内图表最多 8 条系列）。
        mode: ``"light"`` / ``"dark"``。深色底上要整体提亮，否则深蓝曲线
            在 ``#141414`` 上几乎看不见。

    Returns:
        长度为 ``n`` 的色串元组。
    """
    band = _SERIES_BAND["dark" if mode == "dark" else "light"]
    base_l, base_c, base_h = oklch(seed)
    lightness = _clamp(base_l, *band["l"])
    chroma = _clamp(base_c, *band["c"])
    step = 360 / max(int(n), 1)
    return tuple(
        from_oklch(lightness, chroma, base_h - i * step) for i in range(int(n))
    )


#: 顺序色阶的起点：最弱一级有多弱。浅色主题接近底色，深色主题接近黑底。
_RAMP_START = {"light": (0.94, 0.020), "dark": (0.30, 0.030)}


@lru_cache(maxsize=128)
def ramp(base: str, steps: int = 4, mode: str = "light") -> tuple[str, ...]:
    """由基色派生 ``steps`` 级顺序色阶（弱 → 强）。

    **末级正好是基色本身**，这是本函数与"随手调四个明度"的区别：热力图最深的
    那格于是与成功徽标、与 ``SEMANTIC['success']`` 是同一个绿。想改整套绿色，
    改一个令牌就够。

    只动明度、不动色相，所以四级永远读得出"同一件事的量多量少"；彩度从很淡
    渐变到基色，弱级才不会变成一块脏灰。

    Args:
        base: 基色（通常是某个语义角色的 ``text`` 取值）。
        steps: 级数，默认 4。
        mode: 浅色主题从"近白"起，深色主题从"近黑"起。

    Returns:
        长度为 ``steps`` 的元组，索引 0 最弱。
    """
    count = max(int(steps), 1)
    lightness0, chroma0 = _RAMP_START["dark" if mode == "dark" else "light"]
    end_l, end_c, hue = oklch(base)
    if count == 1:
        return (base,)
    out: list[str] = []
    for i in range(count):
        t = i / (count - 1)
        # 明度线性走完；彩度用平方根提前长起来，中间几级才不至于灰掉
        out.append(
            from_oklch(
                lightness0 + (end_l - lightness0) * t,
                chroma0 + (end_c - chroma0) * math.sqrt(t),
                hue,
            )
        )
    return tuple(out)


def mix(a: str, b: str, t: float = 0.5) -> str:
    """在 OKLab 里线性插值两色（``t=0`` 取 ``a``，``t=1`` 取 ``b``）。

    比在 sRGB 里插值稳：sRGB 里"红→蓝"的中点是发灰的紫，OKLab 里是干净的紫。
    给"从底色往前景压一层"这类过渡用。
    """
    ra, ga, ba = _rgb_to_oklab(parse(a))
    rb, gb, bb = _rgb_to_oklab(parse(b))
    k = min(max(t, 0.0), 1.0)
    lin = _oklab_to_rgb((ra + (rb - ra) * k, ga + (gb - ga) * k, ba + (bb - ba) * k))
    # ``_oklab_to_rgb`` 给的是**线性**光强，输出前必须转回 gamma 编码的 sRGB，
    # 否则整色偏暗（直接把线性值当 #RRGGBB 用，中灰会变成近黑的 ``#4D214C``）。
    return to_hex(tuple(_linear_to_srgb(min(max(v, 0.0), 1.0)) for v in lin))  # type: ignore[arg-type]
