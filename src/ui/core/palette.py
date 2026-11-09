"""色板引擎：把「一套配色」变成可以复算的规则。

:mod:`ui.core.color` 管的是**色彩数学**（OKLCH 换算、对比度、色域裁剪），
本模块管的是**配色设计**：给定一个品牌色，产出 Material 3 的整套
:class:`flet.ColorScheme`。

为什么不直接把种子交给 ``color_scheme_seed``
----------------------------------------------
``ft.Theme(color_scheme_seed=...)`` 会让 Flutter 用 M3 的 tonalSpot 算法推导
整套色板。这件事本身没问题，问题在于它推导出来的**不是品牌色**：种子
``#1F6FEB`` 最终落在 ``#465D91`` —— 蓝被抽掉一半彩度，变成灰扑扑的钢蓝。
原因是 tonalSpot 会把种子映射到固定的 tone 40 并大幅降彩度，而品牌色恰好是
设计稿里最不该被改动的一个值。

于是有两套做法可选：

* **完全照抄一张手写色表** —— 颜色可控，但"换主色"就死了：色表是死的，
  种子只影响少数几个由 Flutter 推导的角色，结果是一半跟着变、一半不变。
* **用规则重算一套**（本模块）—— 保住种子的色相与彩度性格，只在明度上按
  可读性解算。换任何种子都能得到同构的一套色板。

本模块选后者，规则只有四条：

1. **色相不动，只动明度**。品牌色是设计资产，可以被压暗（为了扛住白字），
   但不该被改色相。
2. **明度按对比度解算**，不是按"第几档"拍数字。白字压在实底上要 >= 4.5:1，
   这是 WCAG AA 的硬指标；同样的 tone 40，黄色和蓝色压在白底上的对比度能差
   三倍，所以"等 tone"不等于"等可读"。
3. **中性色带一点品牌色相**（彩度 0.005~0.02）。Slate 之所以显高级，是因为
   它的灰不是死灰 —— 掺了一丝蓝。纯中性灰（sRGB 三通道相等）在屏幕上发闷。
   掺多少由 ``surfaces`` 策略决定，色相跟着品牌走，所以换主色时整体是协调的。
4. **顺序色阶等步长**。50~950 十一档的 OKLab 明度间隔约 0.075，除首档（近白，
   需要与底色拉开距离但不必与底色"看起来一样重"）外基本均匀。这是"深浅看得出
   阶梯"的前提。

本模块不 import flet：色板是纯数据，装配成 :class:`flet.ColorScheme` 的活
在 :func:`ui.core.theme.build_theme` 里做。这样 ``_palette_logic.py`` 能脱离
窗口直接验证配色，而不是"跑起来看看"。
"""

from __future__ import annotations

from functools import lru_cache

from ui.core import color

__all__ = [
    "SEMANTIC_HUES",
    "TONES",
    "build_scheme",
    "neutral",
    "semantic_scale",
    "tonal",
]


# ---------------------------------------------------------------------------
# 十一档色阶
# ---------------------------------------------------------------------------
#: 标准色阶的档位名。与 Tailwind / Radix / M3 的习惯一致，读代码的人不必学新词。
TONES: tuple[int, ...] = (50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950)

#: 每一档的 OKLab 明度。除首档外相邻差约 0.075 —— 这个间距下"相邻两档"肉眼
#: 可辨，但又不至于让十一档看起来像十一种颜色。首档（50）刻意离 100 近一些：
#: 它的职责是"几乎就是底色"，只用来做极淡的底纹与悬停。
_TONE_L: dict[int, float] = {
    50: 0.978,
    100: 0.936,
    200: 0.877,
    300: 0.798,
    400: 0.716,
    500: 0.638,
    600: 0.562,
    700: 0.484,
    800: 0.402,
    900: 0.330,
    950: 0.262,
}

#: 彩度包络：中段最艳，两端收窄。
#:
#: 不做这件事会怎样：色阶的亮端（50/100）如果要维持种子的彩度，sRGB 根本装不
#: 下，:func:`ui.core.color.from_oklch` 会一路降彩度兜底 —— 结果同样能看，但
#: 相邻档的彩度落差是"撞墙式"的。显式给一条钟形曲线，让淡色端是"淡而有色"
#: 而不是"淡到发灰"，深色端是"沉而不浊"。
_CHROMA_ENV: dict[int, float] = {
    50: 0.10,
    100: 0.18,
    200: 0.36,
    300: 0.58,
    400: 0.80,
    500: 1.00,
    600: 0.97,
    700: 0.88,
    800: 0.75,
    900: 0.62,
    950: 0.50,
}

#: 两个**绝对色**：白与黑。它们不参与任何推导，只在"这里必须是最亮/最暗"
#: 的位置出现（实底上的白字、M3 规定的 shadow/scrim）。写成具名常量而不是
#: 散在字面量里，是因为"绝对"本身要能在评审时一眼看见。
_WHITE: str = "#FFFFFF"
_BLACK: str = "#000000"

#: 中性语义色的色相（冷灰）。固定 260°，不跟品牌色走：neutral 的职责是
#: "没有立场"，跟着主色变会让"中性提示"在换主色时悄悄变味。
_NEUTRAL_HUE: float = 260.0

#: 品牌色的彩度上限。种子 ``#1F6FEB`` 的 OKLCH 彩度是 0.202，直接铺开是一块
#: 电子屏蓝 —— 亮、但不"高级"。压到 0.175（约等于 Tailwind blue-500 的彩度）
#: 之后仍然一眼是品牌蓝，却收敛了刺眼感。这是"低饱和高级感"在 OKLCH 里的
#: 量化写法：不是把饱和度按 HSL 打个百分比（那会把不同色相压得轻重不一），
#: 而是给感知彩度一个共同的上限。
CHROMA_CAP: float = 0.175


# ---------------------------------------------------------------------------
# 结构色阶：界面结构需要的档位比 50~950 更细
# ---------------------------------------------------------------------------
#: 同一个中性色相上的十四个停靠点。为什么不复用 :data:`_TONE_L`：界面里
#: "卡片底"与"页面底"要差 0.02 个明度（差 0.075 就是两块不同的灰），这种
#: 细分档位不属于对外色阶。
_LIGHT_STOPS: dict[str, float] = {
    "lowest": 0.998,  # 浮得最高的那一层：菜单、气泡
    "bright": 0.996,
    "surface": 0.982,  # 卡片 / 面板
    "low": 0.966,  # 次级背景、斑马行、内嵌面板
    "container": 0.952,  # 应用外壳
    "high": 0.930,  # 比外壳再深一档
    "highest": 0.908,
    "dim": 0.930,  # 遮罩后的页面（对话框背后）
    "ink": 0.232,  # 一级文字
    "ink_soft": 0.500,  # 二级文字
    "outline": 0.705,  # 可见边框（约 2.5:1）
    "hairline": 0.884,  # 分隔线（装饰性，不需要 3:1）
    "inverse": 0.240,  # 反色面（snackbar、tooltip）
    "inverse_ink": 0.955,
}

_DARK_STOPS: dict[str, float] = {
    "lowest": 0.172,  # 深色下"浮得更高"= 更暗，与浅色正好相反
    "bright": 0.340,
    "surface": 0.196,
    "low": 0.226,
    "container": 0.252,
    "high": 0.282,
    "highest": 0.316,
    "dim": 0.162,
    "ink": 0.935,
    "ink_soft": 0.772,
    "outline": 0.545,  # 约 3:1
    "hairline": 0.330,
    "inverse": 0.930,
    "inverse_ink": 0.205,
}

#: 中性色的品牌色相掺入量（OKLab 彩度）。
#:
#: ``neutral`` 只掺一丝（几乎看不出色，但比纯灰"活"）；``tonal`` 掺到能明显
#: 看出偏色（旧版 M3 的着色表面）。两者都远低于"能被叫作彩色"的门槛 ——
#: 中性色的职责是托住内容，不是自己出场。
_TINT: dict[str, float] = {"neutral": 0.006, "tonal": 0.014}

#: 文字用的中性色掺得比背景多一点：纯黑字压在浅底上边缘发硬，掺一点品牌色相
#: 之后与主色同族，整页看起来才像一套。上限 0.020 是"再高就开始像深蓝而不是
#: 近黑"的位置。
_INK_TINT: float = 0.020


# ---------------------------------------------------------------------------
# 语义色：色相固定，明度按对比度解算
# ---------------------------------------------------------------------------
#: 五个语义角色在 OKLCH 里的色相锚点。**固定值，不随品牌色变化** ——
#: "成功"在任何品牌下都必须是绿的，否则语义就失效了。
#:
#: 取的是各色系里最"标准"的那个色相：翡翠绿 165°、琥珀 50°、正红 27°、
#: 天蓝 243°。数字本身不重要，重要的是它们**彼此相距足够远**（最小间距 47°），
#: 并排放在一起时不会认错。
#:
#: 琥珀取 50° 而不是色卡上的 70°：**在 4.5:1 的约束下，70° 出来是橄榄黄**
#: （#9C6300），不像"警告"像"脏"。同一对比度下把色相往橙端挪 20°，得到的是
#: 正琥珀色（#B45300）—— 这不是审美偏好，是色域边界决定的：越接近黄色，
#: 同等明度下的相对亮度越高，要压到 AA 就必须更深，深到一定程度就失去色相。
SEMANTIC_HUES: dict[str, float] = {
    "success": 165.0,
    "warning": 50.0,
    "danger": 27.0,
    "info": 243.0,
}

#: 各语义色的彩度。**逐角色给值**而不是一个统一数字：同一个彩度下，绿的观感
#: 已经很艳，红却还是砖色 —— 红要 C 到 0.19 才"是红的"，而绿到 0.19 就荧光了。
#: 这跟 HSL 里"饱和度 80%"能一视同仁是两件事：OKLCH 的 C 是绝对感知彩度，
#: 不是一个相对百分比。
SEMANTIC_CHROMA: dict[str, float] = {
    "success": 0.130,
    "warning": 0.150,
    "danger": 0.190,
    "info": 0.120,
}

#: 实底对底色的目标对比度。取 5.0 而不是刚好 4.5：字体渲染、缩放、半透明叠加
#: 都会吃掉一点，留 10% 余量。四个角色**解到同一个对比度**，于是"成功"和
#: "警告"在界面上的视觉重量一样 —— 这比"都取 tone 600"科学得多：同样 tone
#: 600，黄色和蓝色的相对亮度能差两倍。
SEMANTIC_FILL_CONTRAST: float = 5.0

#: 深色模式下实底对深色表面的目标对比度。深色底上要更亮才"跳得出来"。
SEMANTIC_FILL_CONTRAST_DARK: float = 7.0

#: 计算语义色时参照的底色。用固定的参照值（而不是实际表面色）是为了让语义色
#: **与品牌无关**：换了主色，中性表面最多偏移 1~2 个 RGB 单位，对 5.0 的目标
#: 对比度影响小于 1%，没必要让"警告色"跟着主色微调。
_REF_SURFACE = {"light": "#FFFFFF", "dark": "#171A1F"}


# ---------------------------------------------------------------------------
# 派生
# ---------------------------------------------------------------------------
@lru_cache(maxsize=64)
def tonal(seed: str, *, chroma_scale: float = 1.0, cap: float | None = None) -> dict[int, str]:
    """由基色派生十一档色阶（保持色相，按 :data:`_TONE_L` 走明度）。

    Args:
        seed: 基色（``"#1F6FEB"``）。非法值会被 :func:`ui.core.color.oklch`
            当成中性灰处理，不会抛。
        chroma_scale: 整体彩度缩放。次要色（secondary）用它压到 0.34，
            仍与主色同色相但明显更"退后"。
        cap: 彩度上限，``None`` 表示用 :data:`CHROMA_CAP`。中性色阶传一个很小
            的值即可复用本函数。

    Returns:
        ``{50: "#…", …, 950: "#…"}``，明度严格单调递减。
    """
    _, base_c, hue = color.oklch(seed)
    chroma = min(base_c * chroma_scale, CHROMA_CAP if cap is None else cap)
    return {
        tone: color.from_oklch(lightness, chroma * _CHROMA_ENV[tone], hue)
        for tone, lightness in _TONE_L.items()
    }


def _hue_scale(hue: float, chroma: float) -> dict[int, str]:
    """:func:`tonal` 的"按色相"版本 —— 语义色只有色相锚点，没有种子色串。"""
    return {
        tone: color.from_oklch(lightness, chroma * _CHROMA_ENV[tone], hue)
        for tone, lightness in _TONE_L.items()
    }


@lru_cache(maxsize=64)
def neutral(seed: str, *, tint: float = _TINT["neutral"]) -> dict[str, str]:
    """由品牌色派生中性色阶（十四个结构档位）。

    色相跟着种子，彩度压在 ``tint`` 一档 —— 于是灰永远是"带一点品牌味的灰"，
    而不是三个通道相等的死灰。深色模式下淡档位会自动变成深档位，由
    :func:`build_scheme` 选表。
    """
    hue = color.oklch(seed)[2]
    out: dict[str, str] = {}
    for mode, stops in (("light", _LIGHT_STOPS), ("dark", _DARK_STOPS)):
        for name, lightness in stops.items():
            # 文字档掺得多一点（见 _INK_TINT），其余档保持一致
            chroma = min(tint * 3.4, _INK_TINT) if name.startswith(("ink", "inverse_ink")) else tint
            out[f"{mode}.{name}"] = color.from_oklch(lightness, chroma, hue)
    return out


@lru_cache(maxsize=64)
def _at_contrast(hue: float, chroma: float, ratio: float, bg: str, *, lighter: bool) -> str:
    """解出一个明度，使该色相对 ``bg`` 的对比度恰好达到 ``ratio``。

    ``lighter=False`` 在底色**之下**找（浅色模式：实底要比白底暗），
    ``lighter=True`` 在底色**之上**找（深色模式：实底要比深底亮）。

    对比度关于明度是单调的，所以二分。返回的永远是**刚好达标的那一端**：

    * 浅色模式取"仍然达标的最亮值"—— 再亮一点就掉到 4.5 以下了，所以这是
      在合规范围内尽量保留品牌色鲜艳度的那一档；
    * 深色模式取"仍然达标的最暗值"—— 同理，是在合规范围内最不刺眼的一档。

    解不出来（目标超出该色相能到达的范围）时停在边界上，把该色相能给的最大
    对比度交出去，绝不抛 —— 配色算不出理想值不该让页面起不来。
    """
    bg_lightness = color.oklch(bg)[0]
    lo, hi = (bg_lightness, 1.0) if lighter else (0.0, bg_lightness)
    # 16 次二分把区间收到 1.5e-5 —— 比十六进制能表达的 1/255 细两个数量级，
    # 再多算就是纯粹的浪费（这条路径在 import 时会被走十次）。
    for _ in range(16):
        mid = (lo + hi) / 2
        ok = color.contrast(color.from_oklch(mid, chroma, hue), bg) >= ratio
        if ok == lighter:
            # 深色模式达标 -> 还能更暗；浅色模式达标 -> 还能更亮
            hi = mid
        else:
            lo = mid
    return color.from_oklch(hi if lighter else lo, chroma, hue)


@lru_cache(maxsize=64)
def semantic_scale(role: str, mode: str) -> tuple[str, str, str]:
    """语义角色的（实底, 实底上的前景, 压在表面上的文字色）。

    三个值同出一源，所以"成功按钮的绿"与"成功提示条的绿"逐字节相同。
    实底解到目标的对比度（浅色 5.0 / 深色 7.0），前景取同色相的深/浅极端值，
    文字色与实底同值 —— 一个色相在浅底上"能当文字"和"能当实底"的门槛本来就
    差不多，多给一个档位只会让调用方纠结用哪个。
    """
    if role == "neutral":
        # 中性不是"彩色"，它要的是中性文字色，不参与色相解算。
        # 固定 260°：中性档的职责是"没有立场"，跟着品牌色走反而会让
        # "neutral 的提示"在换主色时悄悄变味。
        stops = (
            _LIGHT_STOPS if mode == "light" else _DARK_STOPS
        )
        ink = color.from_oklch(stops["ink_soft"], _TINT["neutral"], _NEUTRAL_HUE)
        on = (
            _WHITE
            if mode == "light"
            else color.from_oklch(0.215, 0.012, _NEUTRAL_HUE)
        )
        return (ink, on, ink)

    hue = SEMANTIC_HUES.get(role, SEMANTIC_HUES["info"])
    chroma = SEMANTIC_CHROMA.get(role, 0.13)
    ratio = SEMANTIC_FILL_CONTRAST_DARK if mode == "dark" else SEMANTIC_FILL_CONTRAST
    fill = _at_contrast(hue, chroma, ratio, _REF_SURFACE[mode], lighter=mode == "dark")
    # 前景：浅色模式白字，深色模式取同色相的深墨（白字压在浅绿上会糊成一片）
    on = _WHITE if mode == "light" else color.from_oklch(0.215, chroma * 0.55, hue)
    return (fill, on, fill)


# ---------------------------------------------------------------------------
# 装配
# ---------------------------------------------------------------------------
def build_scheme(
    seed: str, mode: str = "light", *, surfaces: str = "neutral"
) -> dict[str, str]:
    """由品牌色产出一整套 :class:`flet.ColorScheme` 的取值（46 个角色，全给）。

    **为什么一个不落地全给**：只给一半、剩下交给 Flutter 推导，等于把两套算法
    缝在一起 —— 我们按对比度解出来的主色，配 Flutter 按 tone 推出来的容器色，
    层次关系就不再受控（也正因如此，以前会出现"主按钮的实底其实没跟着种子走"）。
    全给之后，明暗两种模式的层次是**一次设计好的**，Flutter 只负责画。

    Args:
        seed: 品牌色。
        mode: ``"light"`` / ``"dark"``。
        surfaces: ``"neutral"``（默认，几乎无色的冷灰）/ ``"tonal"``（明显着色）。

    Returns:
        键名与 :class:`flet.ColorScheme` 字段一一对应，可直接
        ``ft.ColorScheme(**build_scheme(...))``。
    """
    dark = mode == "dark"
    mode = "dark" if dark else "light"
    n = neutral(seed, tint=_TINT.get(surfaces, _TINT["neutral"]))

    def stop(name: str) -> str:
        return n[f"{mode}.{name}"]

    surface = stop("surface")
    seed_chroma = min(color.oklch(seed)[1], CHROMA_CAP)
    hue = color.oklch(seed)[2]

    # ---- 三个强调族 ------------------------------------------------------
    # primary 保住品牌色相与彩度，只解明度；secondary 同色相但彩度压到三分之一
    # （"退后一级的强调"）；tertiary 色相转 60°，用于需要"第三个不同色"的场合
    # （状态色、统计卡），这是 M3 的做法，也比自己再挑一个颜色稳妥。
    primary = _at_contrast(
        hue, seed_chroma, SEMANTIC_FILL_CONTRAST, surface, lighter=dark
    )
    secondary = _at_contrast(
        hue, seed_chroma * 0.34, SEMANTIC_FILL_CONTRAST, surface, lighter=dark
    )
    tertiary = _at_contrast(
        (hue + 60) % 360, seed_chroma * 0.62, SEMANTIC_FILL_CONTRAST, surface,
        lighter=dark,
    )
    primary_ramp = _hue_scale(hue, seed_chroma)
    secondary_ramp = _hue_scale(hue, seed_chroma * 0.34)
    tertiary_ramp = _hue_scale((hue + 60) % 360, seed_chroma * 0.62)

    def on_fill(hue_deg: float, chroma: float, fill: str) -> str:
        """实底上的前景。浅色模式一律白字；深色模式解一个深墨出来。

        深色模式**必须解**而不能取固定档：``ramp[950]`` 对蓝够用（4.6+），
        但次要色本身彩度就低、明度又高，配 950 只有 4.2 —— 而这条路径上有
        三个族要过，逐个试档位不如直接按对比度解。
        """
        if not dark:
            return _WHITE
        return _at_contrast(hue_deg, chroma * 0.45, 4.6, fill, lighter=False)

    error_fill, error_on, _ = semantic_scale("danger", mode)

    # ---- 容器档 ----------------------------------------------------------
    # 容器的彩度**不跟着** _CHROMA_ENV 走：包络是给"色阶"用的（淡端要很淡），
    # 而容器的职责是"一块能认出色相、又不抢前景的底"。按包络算到 tone 100 只剩
    # 0.011，选中行会变成一块灰；给它一个固定的小彩度，才既淡又认得出是蓝色。
    # 浅色用 100~200（很淡），深色用 700~800（比底色亮两档）—— "容器比表面更
    # 靠前"这个关系在两种模式下方向相反，所以档位对调，写死一个必然错一半。
    #
    # primary 与 secondary 的容器**刻意错开一档**：同一个色相在 tone 100 上彩度
    # 已经被色域压到上限，两者会算出同一个色值 —— 而它们要表达的是两件不同的
    # 事（主操作 vs 选中）。错开一档之后，深色模式同理。
    c_tone = (800, 900) if dark else (100, 200)
    # 深色模式下"容器上的文字"必须是浅色，所以两个族都取 100；
    # 浅色模式取 900。之前这里误写成 (100, 900)，导致次要容器的
    # 文字色与容器同档 —— 一块看不出上面有字的方块。
    c_on_tone = (100, 100) if dark else (900, 900)

    def container(family: int, hue_deg: float, chroma: float) -> str:
        return color.from_oklch(_TONE_L[c_tone[family]], chroma, hue_deg)

    def on_container(family: int, hue_deg: float, chroma: float) -> str:
        return color.from_oklch(_TONE_L[c_on_tone[family]], chroma, hue_deg)

    return {
        # --- primary ---
        "primary": primary,
        # 深色模式下实底是亮蓝，前景必须**解**出来而不是取 tone 950：
        # 深蓝蓝到 950 时对比度会掉到 4.1，压在亮蓝上仍不够。
        # 目标 4.6 而不是更高：黑字压在中亮蓝上最多也只有 5.9:1，
        # 要 6.0 会解到纯黑（#000002）—— 那是"没解出来"的表现，不是设计。
        "on_primary": on_fill(hue, seed_chroma, primary),
        "primary_container": container(0, hue, 0.055),
        "on_primary_container": on_container(0, hue, 0.075),
        # --- secondary ---
        "secondary": secondary,
        "on_secondary": on_fill(hue, seed_chroma * 0.34, secondary),
        "secondary_container": container(1, hue, 0.050),
        "on_secondary_container": on_container(1, hue, 0.065),
        # --- tertiary ---
        "tertiary": tertiary,
        "on_tertiary": on_fill((hue + 60) % 360, seed_chroma * 0.62, tertiary),
        "tertiary_container": container(1, (hue + 60) % 360, 0.048),
        "on_tertiary_container": on_container(1, (hue + 60) % 360, 0.065),
        # --- error ---
        "error": error_fill,
        "on_error": error_on,
        "error_container": container(0, SEMANTIC_HUES["danger"], 0.052),
        "on_error_container": on_container(0, SEMANTIC_HUES["danger"], 0.070),
        # --- 表面与前景 ---
        "surface": surface,
        "on_surface": stop("ink"),
        "on_surface_variant": stop("ink_soft"),
        "outline": stop("outline"),
        "outline_variant": stop("hairline"),
        "surface_dim": stop("dim"),
        "surface_bright": stop("bright"),
        "surface_container_lowest": stop("lowest"),
        "surface_container_low": stop("low"),
        "surface_container": stop("container"),
        "surface_container_high": stop("high"),
        "surface_container_highest": stop("highest"),
        "surface_tint": primary,
        # --- 反色面（snackbar / tooltip）---
        "inverse_surface": stop("inverse"),
        "on_inverse_surface": stop("inverse_ink"),
        "inverse_primary": primary_ramp[200 if not dark else 400],
        # --- 固定档（M3 要求：切明暗时这几个角色不变）---
        "primary_fixed": primary_ramp[100],
        "primary_fixed_dim": primary_ramp[200],
        "on_primary_fixed": primary_ramp[950],
        "on_primary_fixed_variant": primary_ramp[800],
        "secondary_fixed": secondary_ramp[100],
        "secondary_fixed_dim": secondary_ramp[200],
        "on_secondary_fixed": secondary_ramp[950],
        "on_secondary_fixed_variant": secondary_ramp[800],
        "tertiary_fixed": tertiary_ramp[100],
        "tertiary_fixed_dim": tertiary_ramp[200],
        "on_tertiary_fixed": tertiary_ramp[950],
        "on_tertiary_fixed_variant": tertiary_ramp[800],
        # M3 里 shadow / scrim 恒为中性黑，不参与主题
        "shadow": _BLACK,
        "scrim": _BLACK,
    }
