"""设计令牌契约测试（不需要窗口）。

一致性不是"看起来差不多"，而是**可断言的约束**。本脚本把
:mod:`ui.core.tokens` 的隐含契约钉成断言，任何一次"顺手改个数"都会被拦下：

1. **单一事实源** —— ``tokens.__all__`` 里每个名字都能从 ``ui.core`` 取到；
   反向，``ui.core`` 登记的每个令牌名字都必须来自 ``tokens``。
   历史上 ``DURATION`` 就漏登记过：组件里 ``from ui.core import DURATION``
   直接 AttributeError，而 ``from ui.core.tokens import DURATION`` 却正常 ——
   同一个东西两个入口、两条路，这类漂移只能靠测试守。
2. **刻度单调** —— 字号 / 图标 / 控件高 / 圆角 / 时长 / 间距，档位必须严格递增。
   乱序的刻度等于没有刻度（"更大一档"到底该取哪个？）。
3. **状态层递进** —— ``hover < focus <= pressed < dragged``，且都在 (0, 1) 内。
   这是 Material 3 的规范关系，破了就会出现"划过比选中还重"。
4. **兜底不抛** —— 非法状态名 / 非法语义角色必须静默退回默认档。
   状态色错一档的代价远小于让整页崩掉。
5. **同源引用** —— ``constants.DEFAULT_FORM_HEIGHT`` /
   ``styles.INPUT_HEIGHT`` / ``panel_field.FIELD_HEIGHT`` 必须**指向**同一个
   令牌值，而不是各自抄一个最近的数字。实测这些手抄副本曾让同一行表单里
   并存 34 / 36 / 40 / 42 四种高度。
6. **不重复定义** —— 除 ``tokens.py`` 之外，禁止任何模块重新定义刻度常量。

用法::

    python scripts/_tokens_logic.py
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

import flet as ft  # noqa: E402

import ui.core as core  # noqa: E402
from ui.core import tokens  # noqa: E402

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


def strictly_increasing(values) -> bool:
    vals = list(values)
    return all(a < b for a, b in zip(vals, vals[1:]))


def parse_layer(value: str) -> tuple[str, float]:
    """把 ``"onsurface,0.08"`` 拆成 ``("onsurface", 0.08)``。"""
    role, _, alpha = str(value).partition(",")
    return role, float(alpha)


# ---------------------------------------------------------------------------
section("单一事实源：tokens.__all__ ↔ ui.core 门面")
for name in tokens.__all__:
    check_true(f"tokens.{name} 存在于模块", hasattr(tokens, name))
    check_true(f"ui.core.{name} 可取到", hasattr(core, name))
    check_true(
        f"ui.core._ORIGIN[{name!r}] 指向 .tokens",
        core._ORIGIN.get(name) == ".tokens",
        f"got={core._ORIGIN.get(name)!r}",
    )

# 反向：ui.core 里登记为 .tokens 的名字必须都在 __all__ 里（否则 dir() 骗人）
asserted = {n for n, origin in core._ORIGIN.items() if origin == ".tokens"}
check("ui.core 的令牌登记数 == tokens.__all__ 数", len(asserted), len(tokens.__all__))
check("无遗漏登记", sorted(asserted - set(tokens.__all__)), [])
check("无多余登记", sorted(set(tokens.__all__) - asserted), [])

# ---------------------------------------------------------------------------
section("刻度单调：字号 / 图标 / 控件高 / 圆角 / 时长")
check_true("FONT_SIZE 严格递增", strictly_increasing(tokens.FONT_SIZE.values()),
           str(list(tokens.FONT_SIZE.values())))
check_true("FONT_SIZE 全是整数（无半像素）",
           all(isinstance(v, int) for v in tokens.FONT_SIZE.values()))
check_true("FONT_SIZE 落在桌面端合理区间 10..40",
           all(10 <= v <= 40 for v in tokens.FONT_SIZE.values()))

check_true("ICON_SIZE 严格递增", strictly_increasing(tokens.ICON_SIZE.values()),
           str(list(tokens.ICON_SIZE.values())))
# 图标与字号是两套刻度：同行图标要比正文文字略大才"站得稳"
check_true("ICON_SIZE['md'] > FONT_SIZE['body']",
           tokens.ICON_SIZE["md"] > tokens.FONT_SIZE["body"],
           f"{tokens.ICON_SIZE['md']} > {tokens.FONT_SIZE['body']}")

check_true("CONTROL_HEIGHT 严格递增", strictly_increasing(tokens.CONTROL_HEIGHT.values()),
           str(list(tokens.CONTROL_HEIGHT.values())))
check_true("CONTROL_HEIGHT['md'] 能容下 body 文字 + 上下 8px",
           tokens.CONTROL_HEIGHT["md"] >= tokens.FONT_SIZE["body"] + 2 * tokens.SPACE["2"])

radius = tokens.RADIUS
check_true("RADIUS 除 full 外严格递增",
           strictly_increasing(list(radius.values())[:-1]),
           str(list(radius.values())[:-1]))
check_true("RADIUS['full'] 是哨兵值（>= 100）", radius["full"] >= 100, str(radius["full"]))
check_true("RADIUS['none'] == 0", radius["none"] == 0)

check_true("DURATION 严格递增", strictly_increasing(tokens.DURATION.values()),
           str(list(tokens.DURATION.values())))
check_true("DURATION['instant'] == 0", tokens.DURATION["instant"] == 0)
check_true("DURATION 全部 <= 500ms（超过就'不跟手'）",
           max(tokens.DURATION.values()) <= 500)

# ---------------------------------------------------------------------------
section("间距：4px 基准网格")
check_true("SPACE_STEPS 严格递增", strictly_increasing(tokens.SPACE_STEPS))
check("SPACE 与 SPACE_STEPS 数量一致", len(tokens.SPACE), len(tokens.SPACE_STEPS))
check_true("SPACE[str(step)] == step * 4",
           all(tokens.SPACE[str(s)] == s * 4 for s in tokens.SPACE_STEPS))
check_true("SPACE 键覆盖全部步数",
           set(tokens.SPACE) == {str(s) for s in tokens.SPACE_STEPS})

check("别名 GAP_TIGHT", tokens.GAP_TIGHT, tokens.SPACE["1"])
check("别名 GAP", tokens.GAP, tokens.SPACE["2"])
check("别名 GAP_LOOSE", tokens.GAP_LOOSE, tokens.SPACE["4"])
check("别名 PAD", tokens.PAD, tokens.SPACE["3"])
check("别名 PAD_LOOSE", tokens.PAD_LOOSE, tokens.SPACE["6"])
check_true("别名顺序 GAP_TIGHT < GAP < GAP_LOOSE",
           tokens.GAP_TIGHT < tokens.GAP < tokens.GAP_LOOSE)

# ---------------------------------------------------------------------------
section("字重：名称 → ft.FontWeight")
check("FONT_WEIGHT 名称表", sorted(tokens.FONT_WEIGHT),
      ["bold", "medium", "regular", "semibold"])
check_true("FONT_WEIGHT 全部是 ft.FontWeight",
           all(isinstance(v, ft.FontWeight) for v in tokens.FONT_WEIGHT.values()))
check_true("FONT_WEIGHT 数值严格递增",
           strictly_increasing(int(str(v.value).lstrip("w")) for v in tokens.FONT_WEIGHT.values()))

# ---------------------------------------------------------------------------
section("状态层：递进关系与兜底")
STATE = tokens.STATE
check_true("hover < focus", STATE["hover"] < STATE["focus"],
           f"{STATE['hover']} < {STATE['focus']}")
check_true("focus <= pressed（M3：同权重）", STATE["focus"] <= STATE["pressed"])
check_true("pressed < dragged", STATE["pressed"] < STATE["dragged"])
check_true("状态层透明度都在 (0, 1) 内", all(0 < v < 1 for v in STATE.values()))
check("状态名集合", sorted(STATE), ["dragged", "focus", "hover", "pressed"])

check("state_layer() 默认取 hover", tokens.state_layer(), tokens.state_layer("hover"))
check("state_layer 解析出的角色", parse_layer(tokens.state_layer())[0], "onsurface")
check("state_layer 解析出的透明度", parse_layer(tokens.state_layer())[1], STATE["hover"])
check("state_layer 未知值退回 hover", tokens.state_layer("nope"), tokens.state_layer("hover"))
check("state_layer 可换打底色", parse_layer(tokens.state_layer("hover", role=ft.Colors.PRIMARY))[0],
      "primary")

check_true("SELECTED_OPACITY subtle < normal",
           tokens.SELECTED_OPACITY["subtle"] < tokens.SELECTED_OPACITY["normal"])
# 选中与走焦同权重：否则"点到的那行"还不如"Tab 走过的那行"显眼
check("选中 normal == 走焦层", tokens.SELECTED_OPACITY["normal"], STATE["focus"])
check("selected_layer() 默认 normal", tokens.selected_layer(), tokens.selected_layer("normal"))
check("selected_layer 未知值退回 normal", tokens.selected_layer("zzz"),
      tokens.selected_layer("normal"))
check("selected_layer strong 走主色容器", tokens.selected_layer("strong"),
      ft.Colors.PRIMARY_CONTAINER)
check("selected_layer 默认打底主色", parse_layer(tokens.selected_layer())[0], "primary")

# --- 禁用态 ---------------------------------------------------------------
check("禁用档名称表", sorted(tokens.DISABLED_OPACITY), ["container", "label"])
check_true("container < label（容器灰淡于标签灰）",
           tokens.DISABLED_OPACITY["container"] < tokens.DISABLED_OPACITY["label"],
           f"{tokens.DISABLED_OPACITY['container']} < {tokens.DISABLED_OPACITY['label']}")
check("disabled_layer() 默认 label", tokens.disabled_layer(), "onsurface,0.38")
check("disabled_layer('container')", tokens.disabled_layer("container"), "onsurface,0.12")
check("disabled_layer 未知档退回 label", tokens.disabled_layer("nope"), tokens.disabled_layer())

# ---------------------------------------------------------------------------
section("半透明覆盖：格式与取值")
check("overlay 的串格式", tokens.overlay(0.06), "onsurface,0.06")
check("overlay 可换角色", parse_layer(tokens.overlay(0.1, role=ft.Colors.PRIMARY))[0], "primary")
check("scrim 默认透明度", parse_layer(tokens.scrim())[1], 0.32)
check_true("scrim 基于 on_surface（不是纯黑）", parse_layer(tokens.scrim())[0] == "onsurface")

# ---------------------------------------------------------------------------
section("语义色：角色对齐与兜底")
check("语义角色集合", tokens.SEMANTIC_ROLES,
      ("success", "warning", "danger", "info", "neutral"))
for table_name in ("SEMANTIC", "SEMANTIC_ON", "SEMANTIC_TEXT"):
    table = getattr(tokens, table_name)
    check(f"{table_name} 角色与 SEMANTIC_ROLES 对齐", sorted(table), sorted(tokens.SEMANTIC_ROLES))
    check(f"{table_name} 明暗两套齐全",
          sorted({m for pair in table.values() for m in pair}), ["dark", "light"])

for role in tokens.SEMANTIC_ROLES:
    for mode in ("light", "dark"):
        for fn, table in (
            (tokens.semantic, tokens.SEMANTIC),
            (tokens.on_semantic, tokens.SEMANTIC_ON),
            (tokens.semantic_text, tokens.SEMANTIC_TEXT),
        ):
            value = fn(role, mode)
            check_true(
                f"{fn.__name__}({role!r}, {mode!r}) 是 #RRGGBB",
                isinstance(value, str) and len(value) == 7 and value.startswith("#"),
                repr(value),
            )

for fn in (tokens.semantic, tokens.on_semantic, tokens.semantic_text):
    check(f"{fn.__name__} 未知角色退回 neutral", fn("nope", "light"),
          fn("neutral", "light"))

check_true("浅色语义色与深色语义色不同（否则明暗切换白做）",
           all(tokens.semantic(r, "light") != tokens.semantic(r, "dark")
               for r in tokens.SEMANTIC_ROLES))

# ---------------------------------------------------------------------------
section("强调角色四联：主色与语义色走同一个入口")
# ---------------------------------------------------------------------------
check("ACCENT_ROLES = M3 三角色 + 五个语义角色", tokens.ACCENT_ROLES,
      ("primary", "secondary", "tertiary") + tokens.SEMANTIC_ROLES)

# primary / secondary / tertiary 必须落到 **M3 角色**上，而不是某个色值：
# 角色由 Flutter 在渲染时从 ColorScheme 解析，换主色不用重建控件。
check("primary 的实底是 M3 角色", tokens.accent_fill("primary"), ft.Colors.PRIMARY)
check("primary 的实底前景是 M3 角色", tokens.accent_on("primary"), ft.Colors.ON_PRIMARY)
check("primary 的文字色是 M3 角色", tokens.accent_text("primary"), ft.Colors.PRIMARY)
check("tertiary 的实底是 M3 角色", tokens.accent_fill("tertiary"), ft.Colors.TERTIARY)

# 语义角色必须落到 SEMANTIC 系列上 —— 这是"按钮的绿 == 提示条的绿"的同源保证。
for role in tokens.SEMANTIC_ROLES:
    check(f"{role} 的实底取自 SEMANTIC", tokens.accent_fill(role), tokens.semantic(role))
    check(f"{role} 的实底前景取自 SEMANTIC_ON",
          tokens.accent_on(role), tokens.on_semantic(role))
    check(f"{role} 的文字色取自 SEMANTIC_TEXT",
          tokens.accent_text(role), tokens.semantic_text(role))

# 淡底两档：小面积 12%，大面积 8%。两档都必须真的"很淡"——
# 压过 20% 就不再是淡底，而是一块彩色面板。
check("SEMANTIC_TINT 是 12%", tokens.SEMANTIC_TINT, 0.12)
check("SEMANTIC_WASH 是 8%", tokens.SEMANTIC_WASH, 0.08)
check_true("淡底比大面积淡底更浓（面积越大越要淡）",
           tokens.SEMANTIC_TINT > tokens.SEMANTIC_WASH)
# 淡底的底色取自 accent_text，accent_text 又取自 SEMANTIC —— 这里不写死色值，
# 只断言"两层确实是同一个色串 + 同一个透明度"。写死的话，语义色一改就红。
check("accent_soft 是 12% 覆盖",
      tokens.accent_soft("success"),
      ft.Colors.with_opacity(0.12, tokens.accent_text("success", "light")))
check("accent_wash 是 8% 覆盖",
      tokens.accent_wash("success"),
      ft.Colors.with_opacity(0.08, tokens.accent_text("success", "light")))

for role in tokens.SEMANTIC_ROLES:
    check(f"accent_* 未知角色等同 neutral",
          (tokens.accent_fill("nope"), tokens.accent_on("nope"), tokens.accent_text("nope")),
          (tokens.accent_fill("neutral"), tokens.accent_on("neutral"),
           tokens.accent_text("neutral")))

# 实底必须扛得住它自己的前景：这是"按钮上的字读不读得出来"的硬指标。
# 走 tokens 而不是 ft.Colors，因为后者的取值只在 Flutter 里。
def _luminance(hex_color: str) -> float:
    def lin(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (lin(int(hex_color[i : i + 2], 16) / 255) for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast(a: str, b: str) -> float:
    la, lb = _luminance(a), _luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


for role in tokens.SEMANTIC_ROLES:
    for mode in ("light", "dark"):
        check_true(f"{mode} 的 {role}：实底上的前景 >= 4.5:1",
                   _contrast(tokens.accent_fill(role, mode),
                             tokens.accent_on(role, mode)) >= 4.5,
                   f"{tokens.accent_fill(role, mode)} / {tokens.accent_on(role, mode)}")

# ---------------------------------------------------------------------------
section("文字主题：正文 14 必须由令牌说了算，而不是 Flutter 默认值")

from ui.core.theme import text_theme  # noqa: E402

check_true("FONT_SIZE 里没有 subtitle（与 body 同值的档位只会让人纠结选哪个）",
           "subtitle" not in tokens.FONT_SIZE, str(list(tokens.FONT_SIZE)))
check("正文基准", tokens.FONT_SIZE["body"], 14)
check_true("ICON_SIZE['md']（16）比正文大 2px：同行图标才站得稳",
           tokens.ICON_SIZE["md"] == tokens.FONT_SIZE["body"] + 2)

# TextTheme 每个槽位都必须落在 FONT_SIZE 的值域里 —— 这样"正文 14"是唯一的
# 事实源，改 tokens 一处，未写 size 的文字与 flet 内置控件（ListTile / Dropdown /
# Tooltip / DatePicker）一起跟着走。
_tt = text_theme()
_slots = {
    name: getattr(_tt, name)
    for name in dir(_tt)
    if name.startswith(("display_", "headline_", "title_", "body_", "label_"))
    and getattr(_tt, name) is not None
}
check_true("text_theme 至少铺满 13 个槽位", len(_slots) >= 13, str(len(_slots)))
outside = {
    name: style.size
    for name, style in _slots.items()
    if style.size not in tokens.FONT_SIZE.values()
}
check("text_theme 无越界字号", outside, {})
check("body_medium 就是正文档", _slots["body_medium"].size, tokens.FONT_SIZE["body"])
check("body_small 是次要档", _slots["body_small"].size, tokens.FONT_SIZE["small"])
check("label_small 是标签档", _slots["label_small"].size, tokens.FONT_SIZE["caption"])
check("title_medium 是卡片标题档", _slots["title_medium"].size, tokens.FONT_SIZE["title"])

# 颜色不是可有可无：flet 下发 TextStyle 时是**替换**而非合并，只写 size 会把颜色
# 一并清空 —— 所有没显式给 color 的文字都变成透明。查一遍，别再犯。
_no_color = [name for name, style in _slots.items() if style.color in (None, "")]
check("text_theme 每个槽位都带颜色（否则文字透明）", _no_color, [])
check("text_theme 的前景色是 ON_SURFACE",
      {style.color for style in _slots.values()}, {ft.Colors.ON_SURFACE})

# ---------------------------------------------------------------------------
section("阴影：档位单调与越界夹取")
check("ELEVATION 档位", tokens.ELEVATION, (0, 1, 2, 3, 4))
blurs = [tokens.elevation(level).blur_radius for level in tokens.ELEVATION]
check_true("阴影模糊半径随档位递增", strictly_increasing(blurs), str(blurs))
check("elevation(0) 无模糊", tokens.elevation(0).blur_radius, 0)
check("elevation(0) 透明", tokens.elevation(0).color, ft.Colors.TRANSPARENT)
check("elevation 越界夹到最高档", tokens.elevation(99).blur_radius,
      tokens.elevation(tokens.ELEVATION[-1]).blur_radius)
check("elevation 负数夹到 0 档", tokens.elevation(-5).blur_radius, 0)

# ---------------------------------------------------------------------------
section("同源引用：控件高度只有一个来源")
from ui.core import constants, styles  # noqa: E402
from ui.input import cascader, multi_select, panel_field, select_box  # noqa: E402

check("CONTROL_HEIGHT['md']", tokens.CONTROL_HEIGHT["md"], 36)
check("constants.DEFAULT_FORM_HEIGHT", constants.DEFAULT_FORM_HEIGHT,
      tokens.CONTROL_HEIGHT["md"])
check("styles.INPUT_HEIGHT", styles.INPUT_HEIGHT, tokens.CONTROL_HEIGHT["md"])
check("panel_field.FIELD_HEIGHT", panel_field.FIELD_HEIGHT, tokens.CONTROL_HEIGHT["md"])
check("select_box.INPUT_HEIGHT", select_box.INPUT_HEIGHT, tokens.CONTROL_HEIGHT["md"])

check("styles.INPUT_RADIUS", styles.INPUT_RADIUS, tokens.RADIUS["md"])

# 组件自己的字号常量必须**赋自**令牌而不是抄数字：抄的那天"正文 14"就跟它无关了，
# 而且这类常量绕过审计（AST 只认 ``Text(size=N)`` 里的字面量）。
check("cascader.ITEM_SIZE", cascader.ITEM_SIZE, tokens.FONT_SIZE["body"])
check("multi_select.TEXT_SIZE", multi_select.TEXT_SIZE, tokens.FONT_SIZE["body"])
check("multi_select.CHIP_TEXT_SIZE", multi_select.CHIP_TEXT_SIZE,
      tokens.FONT_SIZE["small"])
check("panel_field 三档",
      (panel_field.TEXT_SIZE, panel_field.SMALL_SIZE, panel_field.LABEL_SIZE),
      (tokens.FONT_SIZE["body"], tokens.FONT_SIZE["small"], tokens.FONT_SIZE["caption"]))
check("select_box.TEXT_SIZE", select_box.TEXT_SIZE, tokens.FONT_SIZE["body"])

# ---------------------------------------------------------------------------
section("不重复定义：刻度只能在 tokens.py 出现一次")
SCALE_NAMES = {
    "SPACE", "SPACE_STEPS", "RADIUS", "FONT_SIZE", "FONT_WEIGHT", "ICON_SIZE",
    "CONTROL_HEIGHT", "DURATION", "STATE", "SELECTED_OPACITY", "ELEVATION",
    "SEMANTIC", "SEMANTIC_ON", "SEMANTIC_TEXT", "SEMANTIC_ROLES", "PRIMARY_SEEDS",
}
TOKENS_FILE = (SRC / "ui" / "core" / "tokens.py").resolve()

redefinitions: list[str] = []
for path in sorted((SRC / "ui").rglob("*.py")):
    if path.resolve() == TOKENS_FILE:
        continue
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:  # 语法错误另有工具兜住，这里不重复报
        _fails.append(f"无法解析 {path.relative_to(SRC)}: {exc}")
        continue
    for node in tree.body:  # 只看模块顶层：函数内的局部名无害
        targets: list[str] = []
        if isinstance(node, ast.Assign):
            targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            targets = [node.target.id]
        for name in targets:
            if name in SCALE_NAMES:
                redefinitions.append(f"{path.relative_to(SRC)}:{node.lineno} 重新定义了 {name}")
check("无模块重新定义刻度常量", redefinitions, [])

# ---------------------------------------------------------------------------
section("交互态采纳：同名意图必须是同一档")

# 这一节检查的是**采纳率**，不是令牌本身。上一轮把 ``state_layer`` /
# ``selected_layer`` 写进令牌后，全框架只有 tree.py 一个组件在用，其余二十多处
# 仍在手抄 ``overlay(0.06)`` —— 悬停于是同时存在 6% 与 8% 两种轻重。
# 令牌没人用，等于没有令牌。
#
# 判定方式：遍历组件的**模块级常量**，按名字里的意图词检查取值。
# 只比"透明度 + 打底角色"，不管写法 —— 只要视觉结果一致就放过，
# 这样以后换实现方式也不会误报。
import importlib  # noqa: E402
import pkgutil  # noqa: E402

import ui as ui_pkg  # noqa: E402

_HOVER_OK = tokens.state_layer("hover")
_DISABLED_OK = {tokens.disabled_layer(), tokens.disabled_layer("container")}
_SELECTED_OK = {
    tokens.selected_layer("subtle"),
    tokens.selected_layer(),
    ft.Colors.PRIMARY_CONTAINER,
}
_COMPONENT_PACKAGES = {"input", "display", "navigation", "layout", "feedback"}

drifted: list[str] = []
adopted = 0
for info in pkgutil.walk_packages(ui_pkg.__path__, prefix="ui."):
    if info.name.split(".")[1] not in _COMPONENT_PACKAGES:
        continue
    module = importlib.import_module(info.name)
    for name, value in vars(module).items():
        if name.startswith("_") or not name.isupper():
            continue
        if not isinstance(value, str) or "," not in value:
            continue  # 实底色（PRIMARY / SURFACE_*）不参与状态层检查
        if "HOVER" in name:
            # 悬停允许换打底色（表格行用主色托一下），但**透明度必须是同一档**
            adopted += 1
            if parse_layer(value)[1] != parse_layer(_HOVER_OK)[1]:
                drifted.append(f"{info.name}.{name} = {value!r}，透明度应为 {_HOVER_OK!r}")
        elif "DISABLED" in name or name in ("FAINT", "DIMMED"):
            adopted += 1
            if value not in _DISABLED_OK:
                drifted.append(f"{info.name}.{name} = {value!r}，应取禁用两档之一")
        elif "SELECTED" in name or "PICKED" in name:
            adopted += 1
            if value not in _SELECTED_OK:
                drifted.append(f"{info.name}.{name} = {value!r}，应取选中三档之一")

check("交互态常量与令牌同值", drifted, [])
check_true("扫描到的交互态常量数 >= 14", adopted >= 14, str(adopted))

# ---------------------------------------------------------------------------
section("惰性门面：导入 tokens 不应拖入 i18n / logger")
probe = subprocess.run(
    [
        sys.executable,
        "-c",
        "import sys; sys.path.insert(0, r'%s');"
        "import ui.core.tokens;"
        "heavy = [m for m in ('ui.core.i18n', 'ui.core.logger') if m in sys.modules];"
        "print(','.join(heavy) or '-')" % str(SRC),
    ],
    capture_output=True,
    text=True,
    timeout=120,
)
check("导入 ui.core.tokens 的附带模块", (probe.stdout or "").strip(), "-")
check_true("探针子进程正常退出", probe.returncode == 0, probe.stderr.strip()[:200])

# ---------------------------------------------------------------------------
print(f"\nRESULT: {'ALL PASS' if not _fails else f'{len(_fails)} FAILED'}"
      f"  (passed={_passed})")
for f in _fails:
    print("  FAIL", f)
sys.exit(1 if _fails else 0)
