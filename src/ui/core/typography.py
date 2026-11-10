"""排印系统 (Typography) —— 字阶、行高、字距、字重的唯一出处。

字号在 :mod:`ui.core.tokens` 的 :data:`~ui.core.tokens.FONT_SIZE` 里（11/12/14/16/
20/24/28/36），但**字号只是一半**：同样 14px 的两行字，行高 1.4 与 1.7 的阅读
速度能差一成，字距 0 与 -0.8px 的 36px 标题看起来像两个字体。本模块把"另外一半"
补上，并给出可断言的规律，而不是一堆手挑的数字。

三条来源
--------

**1. 行高由黄金比例起算，逐档收紧。** 小字的行间距要相对宽松（否则上下行粘连），
大标题则要收紧（否则字与字之间出现"洞"）。所以行高倍数不是一个常数，而是一条
关于字号的线性律::

    leading(size) = φ - 0.018 × (size - 14)        φ = 1.618

    11px → 1.672      14px → 1.618（正文锚点）      20px → 1.510
    24px → 1.438      28px → 1.366               36px → 1.222

正文 14px 拿到 φ = 1.618，正是长文最舒服的那一档（中文 1.6~1.75、西文 1.5~1.65
的共识区间）；36px 收到 1.222，接近标题专用的 1.2。斜率 0.018 的来历：让 36px
落在 1.22（φ 每档收紧的幅度刚好在这 22px 的跨度上用完），不是拟合出来的。

**2. 字距是光学补偿，不是审美偏好。** 字号越小，字形内部的负空间越少，笔画会
挤在一起 → 加一点字距；字号越大，字间空白被同比放大 → 收一点字距。补偿量按
em 记，落在 ±0.025em 内（超出这个范围就不是"补偿"而是"另一个字体"）::

    caption  11px  +0.20px (+0.018em)      headline   20px  -0.20px (-0.010em)
    small    12px  +0.12px (+0.010em)      headline_lg 24px -0.36px (-0.015em)
    body     14px   0                     display    28px  -0.56px (-0.020em)
    title    16px  -0.08px (-0.005em)     display_lg 36px  -0.80px (-0.022em)

不在字阶上的字号（13px 的行内代码、30px 的自定义标题）不会掉回 0：:func:`tracking`
以 em 为轴在相邻两档之间插值 —— em 是唯一与字号无关的度量，拿 px 插值会在两个
档位之间出现方向相反的偏差。

**3. 字重按"字号越大越敢用粗"分配。** 11px 的 400 在 100% 缩放下笔画会断，所以
小字反而要 500；正文 400 最耐读（500 会让整段发灰）；标题 600/700 才撑得起层级。
CJK 字体常常只有 400/500/700 三档真实字形，600 会在部分字体上被合成 —— 这是
有意的取舍：层级靠"字号 × 字重"两个维度一起说，单独把字重降到 500 会让 H3 与 H4
在视觉上分不开。

与 4px 网格的关系
-----------------

**行高是比例，不是像素。** 量化为 4 的倍数会跟上面那条律打架（正文 22.65px 夹在
20 与 24 之间，选哪个都偏离 φ 一档），所以网格只管**间距**（:data:`~ui.core.tokens.
SPACE` 与 :data:`RHYTHM`），行高保持精确比例、由 Flutter 做亚像素排版。反过来，
块与块之间留多少空，是排印节奏的另一半 —— 见 :data:`RHYTHM` 的 φ 梯级。

用法::

    from ui.core.typography import text_style, RHYTHM, SPLIT, cols

    ft.Text("正文", style=text_style("body"))          # 14 / 1.618 / 0
    ft.Text("标题", style=text_style("headline_lg"))   # 24 / 1.438 / -0.36
    ft.Column(spacing=RHYTHM["paragraph"])             # 12，段与段
    ft.ResponsiveRow(controls=[main, aside], **cols("thirds"))
"""

from __future__ import annotations

from dataclasses import dataclass

import flet as ft

from ui.core.tokens import FONT_SIZE, FONT_WEIGHT

__all__ = [
    "BODY",
    "GRID",
    "LEADING_CODE",
    "LEADING_PROSE",
    "HEADING",
    "HEADING_WEIGHT",
    "LEADING_SLOPE",
    "MAX_TRACKING",
    "PHI",
    "RHYTHM",
    "ROLES",
    "SPLIT",
    "Role",
    "cols",
    "leading",
    "line_box",
    "ratio_cols",
    "role",
    "split",
    "text_style",
    "tracking",
]

#: 黄金比例。行高律的起点，也是 :data:`RHYTHM` 与 :data:`SPLIT` 的比值来源。
PHI: float = 1.618

#: 间距基准网格（与 :data:`ui.core.tokens.SPACE` 同源）。**只管间距，不管行高**。
GRID: int = 4

#: 正文锚点：整套排印从这里长出来。
BODY: str = "body"

#: 行高律的斜率：字号每大 1px，行高倍数收 0.018（见模块说明的推导）。
LEADING_SLOPE: float = 0.018

#: 长文正文的行高：比 UI 正文（1.618）再松一档。
#:
#: 界面里的段落通常两三行、扫一眼就过，1.618 够；文档正文是**连续阅读**，眼睛
#: 要在一行结束时准确回到下一行的行首，行距太紧会串行。1.75 是中文长文的常见
#: 取值（Word 的"1.5 倍行距"约等于此），也是本框架文档站的实测选择。
LEADING_PROSE: float = 1.75

#: 代码块的行高：等宽字形没有西文那种下伸部拥挤，1.55 最紧凑且不粘。
LEADING_CODE: float = 1.55


def leading(size: float) -> float:
    """该字号的行高**倍数**（``TextStyle.height`` 要的就是它）。

    正文 14px 得 φ（1.618），往上逐档收紧到 36px 的 1.222，往下小幅放宽到 11px
    的 1.672 —— 小字要更松、大字要更紧，这是阅读时眼睛回行的距离决定的。

    Args:
        size: 字号（px）。

    Returns:
        行高倍数，保留三位小数（够 Flutter 亚像素排版用，也方便断言）。
    """
    return round(PHI - LEADING_SLOPE * (float(size) - FONT_SIZE[BODY]), 3)


#: 字距补偿的上限（em）。既是模块说明第 2 条的律，也是外推的安全边界 ——
#: 字阶之外的字号插值出来后要夹回这里，否则 48px 的标题会收到 -0.03em，
#: 那就不是"补偿"而是"把字挤到一起"了。
MAX_TRACKING: float = 0.025

#: 各档字距（px）。按 em 记的补偿量换算成 px，直接给 ``TextStyle.letter_spacing``。
#: 数值来源见模块说明第 2 条 —— 保证 ``|字距 / 字号| <= MAX_TRACKING``。
_TRACKING: dict[str, float] = {
    "caption": 0.20,
    "small": 0.12,
    "body": 0.0,
    "title": -0.08,
    "headline": -0.20,
    "headline_lg": -0.36,
    "display": -0.56,
    "display_lg": -0.80,
}

#: 字阶按字号升序排好（``FONT_SIZE`` 是 dict，顺序不可依赖），插值按它对折线取点。
_STEPS: list[tuple[float, str]] = sorted(
    ((float(size), name) for name, size in FONT_SIZE.items()),
    key=lambda step: step[0],
)

#: 各档默认字重。小字 500（防断笔）、正文 400（耐读）、标题 600/700（撑层级）。
_WEIGHT: dict[str, ft.FontWeight] = {
    "caption": FONT_WEIGHT["medium"],
    "small": FONT_WEIGHT["regular"],
    "body": FONT_WEIGHT["regular"],
    "title": FONT_WEIGHT["medium"],
    "headline": FONT_WEIGHT["semibold"],
    "headline_lg": FONT_WEIGHT["semibold"],
    "display": FONT_WEIGHT["bold"],
    "display_lg": FONT_WEIGHT["bold"],
}


def _tracking_em(size: float) -> float:
    """字阶之外的字距（em）：在 (字号, em) 折线上取点，两端沿最近一段线性外推。

    插值必须在 em 轴上做。拿 px 插值的话，12px(+0.12) 与 16px(-0.08) 之间会在
    14px 处给出 +0.02px —— 而正文本该是 0，方向都错了。
    """
    points = [(step, _TRACKING[name] / step) for step, name in _STEPS]
    if size <= points[0][0]:
        low, high = points[0], points[1]
    elif size >= points[-1][0]:
        low, high = points[-2], points[-1]
    else:
        low, high = next(
            (lo, hi) for lo, hi in zip(points, points[1:]) if lo[0] <= size <= hi[0]
        )
    em = low[1] + (high[1] - low[1]) / (high[0] - low[0]) * (size - low[0])
    return max(-MAX_TRACKING, min(MAX_TRACKING, em))


def tracking(size: float, name: str | None = None) -> float:
    """该字号的字距（px）。字阶上用档位的精确值，字阶外按 em 插值。

    组件里几乎总该用 :func:`text_style`；这个函数是给"不在字阶上、但仍要光学
    补偿"的地方用的（例如 13px 的行内代码、18px 的自定义标题）。

    落在字阶上时**直接返回档位值**，不走插值 —— 两套口径算同一个字号，必然在
    某一档上打架（36px 走表是 -0.80、走旧公式是 -1.27，同一个 36px 两个字距）。

    Args:
        size: 字号（px）。
        name: 档位名。给了就用它在表里的值，跳过插值。

    Returns:
        字距（px），保留两位小数。
    """
    if name is not None and name in _TRACKING:
        return _TRACKING[name]
    size = float(size)
    for step, step_name in _STEPS:
        if abs(step - size) < 1e-9:
            return _TRACKING[step_name]
    return round(_tracking_em(size) * size, 2)


@dataclass(frozen=True)
class Role:
    """一个排印档位的完整度量。

    字号之外的三项（行高、字距、字重）**必须成套使用**：只改字号会让行高与字号
    脱节，而脱节的行高比"字号偏 1px"难看得多。
    """

    name: str
    size: int
    leading: float
    tracking: float
    weight: ft.FontWeight

    @property
    def line_box(self) -> float:
        """行盒高度（px）= 字号 × 行高。需要给容器定高时用它，别再自己乘一遍。"""
        return round(self.size * self.leading, 1)

    @property
    def em_tracking(self) -> float:
        """字距换算成 em —— 与字号无关的度量，方便跨档比较与断言。"""
        return round(self.tracking / self.size, 4)


def _build_roles() -> dict[str, Role]:
    return {
        name: Role(
            name=name,
            size=size,
            leading=leading(size),
            tracking=_TRACKING[name],
            weight=_WEIGHT[name],
        )
        for name, size in FONT_SIZE.items()
    }


#: 全部排印档位，键与 :data:`~ui.core.tokens.FONT_SIZE` 一一对应。
ROLES: dict[str, Role] = _build_roles()


def role(name: str = BODY) -> Role:
    """取档位度量。非法名字退回正文 —— 排印错一档不该让整页崩掉。"""
    return ROLES.get(name, ROLES[BODY])


def line_box(name: str = BODY) -> float:
    """该档位的行盒高度（px）。"""
    return role(name).line_box


def text_style(
    name: str = BODY,
    *,
    color: ft.ColorValue | None = None,
    weight: ft.FontWeight | None = None,
    size: int | None = None,
    leading: float | None = None,
    tracking: float | None = None,
    italic: bool | None = None,
) -> ft.TextStyle:
    """构造某档位的 :class:`flet.TextStyle`（字号 / 行高 / 字距 / 字重四件套）。

    这是组件侧**唯一**该用来排字的入口：写 ``ft.Text("x", size=14)`` 会丢掉
    行高与字距，同一段话放进卡片和表格就会有两种行间距。

    Args:
        name: 档位名（见 :data:`ROLES`）。
        color: 文字颜色（角色色，如 ``ft.Colors.ON_SURFACE_VARIANT``）。
        weight: 覆盖字重。层级靠字号，字重只做微调 —— 整段加粗等于没有加粗。
        size: 覆盖字号。**只在字阶之外的尺寸上使用**（如 13px 的行内代码）。
        leading: 覆盖行高倍数。多行引文、长文段落偶尔要更松，见 ``Quote``。
        tracking: 覆盖字距（px）。
        italic: 斜体。

    Returns:
        :class:`flet.TextStyle`，可直接交给 ``ft.Text(style=...)``。
    """
    spec = role(name)
    return ft.TextStyle(
        size=size if size is not None else spec.size,
        height=leading if leading is not None else spec.leading,
        weight=weight if weight is not None else spec.weight,
        letter_spacing=tracking if tracking is not None else spec.tracking,
        color=color,
        italic=italic,
    )


# ---------------------------------------------------------------------------
# 层级
# ---------------------------------------------------------------------------
#: 六级标题 → 排印档位。**相邻两级必须真的差一档**：若 H2 走 M3 的
#: ``headline_large`` 槽、H3 走 ``headline_medium``，而主题把这两个槽分别钉到
#: 24 与 28，H2 就比 H3 还小，层级在视觉上反了。这里直接指到字阶，
#: 类名与像素一一对应，不经过主题槽位这道中转。
HEADING: dict[int, str] = {
    1: "display_lg",  # 36
    2: "display",  # 28
    3: "headline_lg",  # 24
    4: "headline",  # 20
    5: "title",  # 16
    6: "body",  # 14，与正文同号、只靠字重区分
}

#: 六级标题的字重：前两级 700，其余 600（H6 与正文同号，必须靠字重站住）。
HEADING_WEIGHT: dict[int, str] = {
    1: "bold",
    2: "bold",
    3: "semibold",
    4: "semibold",
    5: "semibold",
    6: "semibold",
}


# ---------------------------------------------------------------------------
# 节奏：块与块之间留多少空
# ---------------------------------------------------------------------------
#: 竖向节奏的五档，全部落在 4px 网格上，而**相邻档的比值贴着 φ**
#: （2.0 / 1.5 / 1.67 / 1.6 / 1.63）：间距这层可以量化到网格，行高那层不行。
#:
#:   hair       4   同一行里的图文缝隙、图标与标签
#:   block      8   控件内部、标题与它的副标题
#:   paragraph 12   段与段（比一个行盒松半个行盒，读者才分得清"同一段"）
#:   group     20   一组控件与下一组
#:   section   32   分区之间（卡片、表格、示例）
#:   page      52   页面级分段（大标题区与正文）
RHYTHM: dict[str, int] = {
    "hair": 4,
    "block": 8,
    "paragraph": 12,
    "group": 20,
    "section": 32,
    "page": 52,
}


# ---------------------------------------------------------------------------
# 三分法则：宽度的分配
# ---------------------------------------------------------------------------
#: 二栏布局的两条常见分法。**不是所有分法都该用 1:1** —— 一页"主内容 + 侧栏"
#: 用 2:1（三分法则）时，两侧的视觉重量差刚好能让眼睛立刻分出主次；1:1 会让
#: 读者先找入口。黄金分割 1.618:1 更含蓄，适合图文混排。
SPLIT: dict[str, tuple[float, float]] = {
    "thirds": (2, 1),  # 主内容在左，占三分之二
    "aside": (1, 2),  # 说明在左、演示在右：视线先落在三分之一，再展开正文
    "golden": (PHI, 1),  # 黄金分割：正文与插图
    "even": (1, 1),  # 对照：两栏同等重要（并排比较）
    "wide": (3, 1),  # 正文旁只放目录 / 操作
}

#: ``ft.ResponsiveRow`` 的 12 栏网格宽度。
_COLUMNS = 12


def split(name: str | tuple[float, float] = "thirds") -> tuple[float, float]:
    """取分栏比例。可以直接传一个 ``(左, 右)`` 比例元组。

    非法名字退回三分法则 —— 分栏算错一档的代价远小于让整页崩掉。
    """
    if isinstance(name, tuple) and len(name) == 2:
        left, right = float(name[0]), float(name[1])
        return (left, right) if left > 0 and right > 0 else SPLIT["thirds"]
    return SPLIT.get(name, SPLIT["thirds"])


def cols(
    name: str | tuple[float, float] = "thirds",
    *,
    breakpoint: str = "md",
    total: int = _COLUMNS,
) -> tuple[dict[str, int], dict[str, int]]:
    """把分栏比例翻译成 ``ft.ResponsiveRow`` 的 ``col`` 参数。

    三分法则在 12 栏网格上是 ``8 + 4``，黄金分割是 ``7 + 5``（7.42 取整）。
    窄屏（xs / sm）一律整行堆叠 —— 两栏在手机宽度上并排，两边都读不了。

    用法::

        main_col, aside_col = cols("thirds")
        ft.ResponsiveRow(controls=[
            ft.Container(main, col=main_col),
            ft.Container(aside, col=aside_col),
        ])

    Returns:
        ``(主栏 col, 从栏 col)``，两个都是 ``{断点: 列数}`` 字典，直接交给控件。
    """
    left, right = split(name)
    main = max(1, min(total - 1, round(left / (left + right) * total)))
    aside = total - main
    # 窄屏（xs / sm）整行堆叠；到 breakpoint 才并排。
    return (
        {"xs": total, "sm": total, breakpoint: main},
        {"xs": total, "sm": total, breakpoint: aside},
    )


def ratio_cols(
    ratio: tuple[int, int], *, breakpoint: str = "lg", total: int = _COLUMNS
) -> tuple[dict[str, int], dict[str, int]]:
    """:func:`cols` 的比例版：直接给 ``(5, 7)`` 这样的字面比例。

    文档 DSL 里的 ``Split(ratio=...)`` 就是这么用的 —— 作者写"左边 5 份、右边 7 份"，
    不必先给这个比例起个名字。
    """
    return cols(ratio, breakpoint=breakpoint, total=total)

