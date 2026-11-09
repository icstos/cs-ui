"""设计令牌 + 主题运行时 纯逻辑单测（不需要窗口）。

覆盖：间距/圆角/字号阶梯的自洽性、语义色明暗取值与降级、主题感知色串的
产出格式（``onsurface,0.06``）、阴影档位夹取、``ThemeState`` 的模式归一 /
``system`` 解析 / ``toggle_mode`` 的"先落到当前可见档"语义 / ``cycle_mode``
三态循环、``build_theme`` 与 ``apply_theme`` 的落值、订阅钩子读了是否登记依赖。

用法::

    python scripts/_theme_logic.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import flet as ft  # noqa: E402

from ui.core import palette as pl  # noqa: E402
from ui.core import theme as theme_mod  # noqa: E402
from ui.core import tokens as tk  # noqa: E402
from ui.core.theme import (  # noqa: E402
    MODES,
    ThemeState,
    apply_theme,
    build_theme,
    current_mode,
    set_system_brightness,
    theme_state,
)
from ui.core.tokens import (  # noqa: E402
    elevation,
    focus_border,
    hairline,
    on_semantic,
    overlay,
    scrim,
    semantic,
    semantic_text,
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


def raiser(fn, *args, **kwargs) -> str:
    """执行并返回异常类名（空串 = 没抛）。"""
    try:
        fn(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001
        return type(exc).__name__
    return ""


def fresh(mode: str = "system", primary: str = "#1F6FEB") -> ThemeState:
    """造一个干净的状态对象（不碰全局单例，避免用例互相污染）。"""
    return ThemeState(mode=mode, primary=primary, platform_brightness="light")


# ---------------------------------------------------------------------------
# 1. 阶梯自洽性
# ---------------------------------------------------------------------------
check("SPACE 是步数 × 4", [tk.SPACE[str(s)] for s in (0, 1, 2, 3, 4)], [0, 4, 8, 12, 16])
check("SPACE 键都是字符串", all(isinstance(k, str) for k in tk.SPACE), True)
check("SPACE_STEPS 递增且无重复",
      list(tk.SPACE_STEPS) == sorted(set(tk.SPACE_STEPS)), True)
check("SPACE 取不存在的键抛 KeyError（不静默给 0）",
      raiser(lambda: tk.SPACE["999"]), "KeyError")
check("语义别名与阶梯一致",
      (tk.GAP_TIGHT, tk.GAP, tk.GAP_LOOSE, tk.PAD, tk.PAD_LOOSE),
      (4, 8, 16, 12, 24))
check("RADIUS 递增", [tk.RADIUS[k] for k in ("none", "xs", "sm", "md", "lg", "xl", "full")],
      [0, 2, 4, 6, 8, 12, 999])
check("FONT_SIZE 递增",
      [tk.FONT_SIZE[k] for k in ("caption", "small", "body", "title",
                                 "headline", "headline_lg", "display", "display_lg")],
      [11, 12, 14, 16, 20, 24, 28, 36])
check("正文是 14（框架默认，也是 TextTheme.bodyMedium 的取值）",
      tk.FONT_SIZE["body"], 14)
check("FONT_WEIGHT 四档齐", len(tk.FONT_WEIGHT), 4)
check("DURATION 递增", [tk.DURATION[k] for k in ("instant", "fast", "normal", "slow")],
      [0, 120, 200, 320])
check("PRIMARY_SEEDS 都是 6 位 hex",
      all(len(v) == 7 and v.startswith("#") for v in tk.PRIMARY_SEEDS.values()), True)
check("PRIMARY_SEEDS 键都是色相名（不是 blue500）",
      all("_" not in k for k in tk.PRIMARY_SEEDS), True)


# ---------------------------------------------------------------------------
# 2. 语义色
# ---------------------------------------------------------------------------
check("SEMANTIC_ROLES 含四个 M3 缺失的角色",
      set(("success", "warning", "danger", "info", "neutral"))
      <= set(tk.SEMANTIC_ROLES), True)
for role in tk.SEMANTIC_ROLES:
    light = semantic(role, "light")
    dark = semantic(role, "dark")
    check(f"{role} 明/暗两套都有值", (len(light), len(dark)), (7, 7))
    check(f"{role} 明暗不同色（否则暗色主题下读不清）", light != dark, True)
    on_light, on_dark = on_semantic(role, "light"), on_semantic(role, "dark")
    check(f"{role} 的前景色两套都有值", (len(on_light), len(on_dark)), (7, 7))

check("semantic 未知角色退回 neutral", semantic("nope", "light"),
      semantic("neutral", "light"))
check("semantic 非法模式退回 light", semantic("success", "rainbow"),
      semantic("success", "light"))
check("on_semantic 未知角色退回 neutral", on_semantic("nope", "dark"),
      on_semantic("neutral", "dark"))
check("semantic_text 未知角色退回 neutral", semantic_text("nope", "light"),
      semantic_text("neutral", "light"))
check("semantic_text 与填充在浅色下同档（省一档认知负担）",
      semantic_text("success", "light"), semantic("success", "light"))


# 对比度：WCAG 2.1 —— 正文 4.5:1（1.4.3），图形/大字 3:1（1.4.11）。
# 本框架把语义色的三档都当"文字级"用，所以一律按 4.5 卡。
def _lin(c: float) -> float:
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _lum(hex_color: str) -> float:
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def _contrast(a: str, b: str) -> float:
    la, lb = _lum(a), _lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


SURFACE = {"light": "#FFFFFF", "dark": "#141414"}
for mode, surface in SURFACE.items():
    for role in tk.SEMANTIC_ROLES:
        check(f"{mode} 的 {role} 填充对底色 >= 4.5",
              round(_contrast(semantic(role, mode), surface), 2) >= 4.5, True)
        check(f"{mode} 的 {role} 前缀色压在自己的填充上 >= 4.5",
              round(_contrast(on_semantic(role, mode), semantic(role, mode)), 2) >= 4.5,
              True)
        check(f"{mode} 的 {role} 文字色对底色 >= 4.5",
              round(_contrast(semantic_text(role, mode), surface), 2) >= 4.5, True)

# 语义色是**按目标对比度解出来的**（见 ui.core.palette.semantic_scale），所以这里
# 断言的是"解出来的结果守住了规则"，而不是几个具体色值 —— 后者换个色相锚点就失效，
# 前者才是真正要保的性质。
for mode in ("light", "dark"):
    ratios = {role: _contrast(semantic(role, mode), SURFACE[mode])
              for role in tk.SEMANTIC_ROLES if role != "neutral"}
    spread = max(ratios.values()) - min(ratios.values())
    check(f"{mode} 四个语义填充的对比度彼此相差 < 0.3（视觉重量一致）",
          round(spread, 2) < 0.3, True)
    check(f"{mode} 语义填充都达到了目标对比度",
          round(min(ratios.values()), 2) >= 4.5, True)

# 深色模式下实底是亮色，前景必须是"同色相的深墨"而不是白字 ——
# 白字压在浅绿/浅黄上对比度只有 1.7 左右，是一块读不出字的色块。
for role in ("success", "warning", "danger", "info"):
    fg, fill = on_semantic(role, "dark"), semantic(role, "dark")
    check(f"深色 {role} 的前景比实底暗得多（深墨而不是白字）",
          _lum(fg) < _lum(fill) / 2, True)


# ---------------------------------------------------------------------------
# 3. 主题感知色串（委托给 Flutter 解析，格式必须对）
# ---------------------------------------------------------------------------
check("overlay 产出角色名+透明度", overlay(0.06), "onsurface,0.06")
check("overlay 可换角色", overlay(0.12, role=ft.Colors.PRIMARY), "primary,0.12")
check("overlay 是 str（能直接当 bgcolor）", isinstance(overlay(0.06), str), True)
check("scrim 默认 0.32", scrim(), "onsurface,0.32")
check("scrim 可调", scrim(0.5), "onsurface,0.5")


# ---------------------------------------------------------------------------
# 4. 阴影与描边
# ---------------------------------------------------------------------------
check("ELEVATION 档位递增", list(tk.ELEVATION), [0, 1, 2, 3, 4])
sh = elevation(3)
check("elevation(3) 参数", (sh.blur_radius, sh.offset.y), (12.0, 4.0))
check("elevation 颜色是主题感知（带 shadow 角色）",
      isinstance(sh.color, str) and sh.color.startswith("shadow,"), True)
check("elevation 超上界夹到最高档", elevation(99).blur_radius, elevation(4).blur_radius)
check("elevation 超下界夹到 0", elevation(-5).blur_radius, 0.0)
check("elevation(0) 是全透明", elevation(0).color, ft.Colors.TRANSPARENT)
check("focus_border 是主色 2px",
      (focus_border().width, focus_border().color), (2.0, ft.Colors.PRIMARY))
check("hairline 是 1px outlinevariant",
      (hairline().width, hairline().color), (1, ft.Colors.OUTLINE_VARIANT))


# ---------------------------------------------------------------------------
# 5. ThemeState
# ---------------------------------------------------------------------------
st = fresh("dark")
check("显式 dark 直接生效", (st.mode, st.mode_name, st.is_dark), ("dark", "dark", True))
st = fresh("light")
check("显式 light 直接生效", (st.mode_name, st.is_dark), ("light", False))
st = fresh("system")
check("system + 系统 light -> light", st.mode_name, "light")
st.platform_brightness = "dark"
check("system + 系统 dark -> dark", st.mode_name, "dark")
st.mode = "dark"
st.platform_brightness = "light"
check("显式 dark 不受系统亮度影响", st.mode_name, "dark")
for bad in ("DARK", " light ", "rainbow", "", None, 3):
    s2 = fresh()
    s2.set_mode(bad)
    check(f"set_mode({bad!r}) 归一到合法值", s2.mode in MODES, True)

s = fresh("dark")
s.toggle_mode()
check("dark --toggle--> light", (s.mode, s.mode_name), ("light", "light"))
s = fresh("light")
s.toggle_mode()
check("light --toggle--> dark", (s.mode, s.mode_name), ("dark", "dark"))
# 关键交互直觉：☀/🌙 按钮无论当前是 system 还是固定档，点一下都必须"看见变化"，
# 所以是切到**当前的反面**，不是"把 system 冻成当前这档"（那会变成点了没反应）。
s = fresh("system")
s.platform_brightness = "light"
s.toggle_mode()
check("system(浅色) --toggle--> dark（画面真的变了）",
      (s.mode, s.mode_name), ("dark", "dark"))
s = fresh("system")
s.platform_brightness = "dark"
s.toggle_mode()
check("system(深色) --toggle--> light", (s.mode, s.mode_name), ("light", "light"))

s = fresh("system")
order = []
for _ in range(4):
    s.cycle_mode()
    order.append(s.mode)
check("cycle_mode 三态循环一轮回到 system", order, ["light", "dark", "system", "light"])

s = fresh()
s.set_primary("  #7C3AED ")
check("set_primary 去空白", s.primary, "#7C3AED")
s.set_primary(None)
check("set_primary(None) 退回默认种子", s.primary, tk.PRIMARY_SEEDS["blue"])
s.set_primary("#ZZZZZZ")
check("非法主色不抛（Flutter 自己会兜底）", s.primary, "#ZZZZZZ")

check("默认状态是 system + 蓝种子",
      (fresh().mode, fresh().primary), ("system", tk.PRIMARY_SEEDS["blue"]))


# ---------------------------------------------------------------------------
# 6. build_theme / apply_theme
# ---------------------------------------------------------------------------
t = build_theme(fresh("dark", "#7C3AED"))
check("build_theme 不再交种子给 Flutter（tonalSpot 会改品牌色）",
      t.color_scheme_seed, None)
check("build_theme 下发的是 palette 解出的整套色板（暗色档）",
      t.color_scheme.primary, pl.build_scheme("#7C3AED", "dark")["primary"])
check("build_theme 的色板与 palette 逐角色一致",
      t.color_scheme.surface, pl.build_scheme("#7C3AED", "dark")["surface"])
check("build_theme 明暗两套不同（不是同一棵树涂两遍）",
      build_theme(fresh("light", "#7C3AED")).color_scheme.primary ==
      t.color_scheme.primary, False)
check("build_theme 走 Material 3", t.use_material3, True)
check("build_theme 装上了滚动条主题（桌面端细滚动条）", t.scrollbar_theme is not None, True)
check("build_theme 路由切换无动画", t.page_transitions.windows, ft.PageTransitionTheme.NONE)
check("build_theme 不写死字体", t.font_family, None)
check("build_theme 给字体就用", build_theme(
    ThemeState(font_family="AlibabaPuHuiTi")).font_family, "AlibabaPuHuiTi")


class FakePage:
    """只提供 apply_theme 会碰到的字段，避免真开窗口。"""

    def __init__(self) -> None:
        self.theme = None
        self.theme_mode = None
        self.platform_brightness = ft.Brightness.DARK
        self.on_platform_brightness_change = None


fp = FakePage()
s = fresh("dark", "#0D9488")
apply_theme(fp, s)
check("apply_theme 写 page.theme（按浅色档算）",
      fp.theme.color_scheme.primary, pl.build_scheme("#0D9488", "light")["primary"])
check("apply_theme 也写 page.dark_theme（flet 深色下用的是这棵）",
      fp.dark_theme.color_scheme.primary, pl.build_scheme("#0D9488", "dark")["primary"])
check("apply_theme 把页面底色接上表面色（否则页面与控件不是同一个色）",
      fp.bgcolor, ft.Colors.SURFACE)
check("apply_theme 写 page.theme_mode=DARK", fp.theme_mode, ft.ThemeMode.DARK)
check("apply_theme 读到平台亮度并落到状态", s.platform_brightness, "dark")
check("apply_theme 挂了平台亮度监听",
      callable(fp.on_platform_brightness_change), True)
handler = fp.on_platform_brightness_change
apply_theme(fp, s)
check("apply_theme 幂等（不重复挂监听）",
      fp.on_platform_brightness_change is handler, True)

ev = ft.PlatformBrightnessChangeEvent(name="x", control=None, brightness=ft.Brightness.LIGHT)
handler(ev)
# 显式档位必须**无视**系统亮度变化（用户已经明确表态了，别再改）
check("系统亮度变化不影响显式 dark",
      (s.mode, s.platform_brightness, s.mode_name), ("dark", "light", "dark"))

fp_sys = FakePage()
s_sys = fresh("system", "#0D9488")
apply_theme(fp_sys, s_sys)
ev_dark = ft.PlatformBrightnessChangeEvent(name="x", control=None,
                                           brightness=ft.Brightness.DARK)
fp_sys.on_platform_brightness_change(ev_dark)
check("system 模式下系统变暗 -> 跟着变暗",
      (s_sys.platform_brightness, s_sys.mode_name), ("dark", "dark"))

fp2 = FakePage()
s2 = fresh("light")
apply_theme(fp2, s2)
check("显式 light 时即使系统是 dark 也照常渲染浅色",
      fp2.theme_mode, ft.ThemeMode.LIGHT)
check("系统亮度仍被如实记录（供 UI 显示「跟随系统 · 深色」）",
      s2.platform_brightness, "dark")

fp3 = FakePage()
fp3.platform_brightness = None
s3 = fresh("system")
apply_theme(fp3, s3)
check("平台亮度未知时不猜，按现有状态走", s3.platform_brightness, "light")

fp4 = FakePage()
s4 = fresh("system")
apply_theme(fp4, s4)
check("apply_theme 覆盖 system", fp4.theme_mode, ft.ThemeMode.SYSTEM)

check("apply_theme 用默认单例也不抛", raiser(apply_theme, FakePage()), "")


# ---------------------------------------------------------------------------
# 7. 全局单例 + 订阅
# ---------------------------------------------------------------------------
check("theme_state() 是单例", theme_state() is theme_state(), True)
g = theme_state()
g.mode, g.platform_brightness = "system", "light"
check("current_mode() 跟随单例", current_mode(), g.mode_name)
set_system_brightness("dark")
check("set_system_brightness 生效", (g.platform_brightness, current_mode()), ("dark", "dark"))
set_system_brightness("light")
check("set_system_brightness 复原", current_mode(), "light")
check("semantic(None) 跟随全局模式", semantic("success"), semantic("success", "light"))
g.mode, g.platform_brightness = "dark", "dark"
check("切到 dark 后 semantic(None) 跟着变", semantic("success"),
      semantic("success", "dark"))
check("theme_context 的默认值就是那个单例（不挂 Provider 也能用）",
      theme_mod.theme_context.default_value is g, True)
check("use_theme 在组件体外调用会明确报错（而不是静默返回）",
      raiser(theme_mod.use_theme), "RuntimeError")
g.mode, g.platform_brightness = "system", "light"  # 复原

check("非法亮度名退回 light", raiser(set_system_brightness, "nope"), "")
set_system_brightness("light")


# ---------------------------------------------------------------------------
print(f"\nRESULT: {'ALL PASS' if not _fails else f'{len(_fails)} FAILED'}"
      f"  (passed={_passed})")
if _fails:
    for line in _fails:
        print("  -", line)
    sys.exit(1)