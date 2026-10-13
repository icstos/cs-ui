"""设计令牌 (Design Tokens)。

组件里**不要**再出现裸色值（``"#6B7280"``）、裸圆角（``8``）、裸字号（``13``）——
一律走本模块。理由不是洁癖，而是三条硬需求：

1. **明暗主题**：Flet / Flutter 的颜色串支持 ``"<角色名>,<透明度>"``（由
   :func:`flet.Colors.with_opacity` 生成，如 ``"onsurface,0.06"``），
   **由 Flutter 在运行时按当前 ``ColorScheme`` 解析**。把 ``ft.Colors.ON_SURFACE``
   交给 Flutter，明暗切换是零成本且必然正确的；把 ``"#6B7280"`` 写死，暗色下必瞎。
2. **主色可切**：``ft.Theme(color_scheme_seed=...)`` 让 Flutter 从一个品牌色种子
   推导整套 M3 色板（见 :mod:`ui.core.theme`），组件只引用角色、不引用具体色值。
3. **一处修改全局生效**：圆角 / 间距 / 字号改一个数，全框架跟着走。

令牌分两类，用途不同，不要混：

* **主题感知令牌**（本模块上半部分）—— 直接就是 :class:`flet.Colors` 的**角色枚举**，
  原样传给 Flutter 即可，明暗与主色全自动跟随。
* **框架解析令牌**（:data:`SEMANTIC`）—— Material 3 **没有** ``success`` /
  ``warning`` / ``info`` / ``neutral`` 这几个语义角色，而桌面端的状态提示离不开它们。
  它们由本模块按当前模式给出一对具体色值（见 :func:`semantic`）。

用法::

    from ui.core.tokens import SPACE, RADIUS, overlay, semantic

    ft.Container(
        bgcolor=ft.Colors.SURFACE_CONTAINER,
        border_radius=RADIUS["lg"],
        padding=SPACE["3"],
    )
    ft.Text("已保存", color=semantic("success"))
"""

from __future__ import annotations

import flet as ft

__all__ = [
    "SPACE",
    "SPACE_STEPS",
    "RADIUS",
    "FONT_SIZE",
    "FONT_WEIGHT",
    "DURATION",
    "SEMANTIC",
    "SEMANTIC_ON",
    "SEMANTIC_TEXT",
    "SEMANTIC_ROLES",
    "ELEVATION",
    "PRIMARY_SEEDS",
    "semantic",
    "on_semantic",
    "semantic_text",
    "overlay",
    "scrim",
    "elevation",
    "focus_border",
    "hairline",
]

# ---------------------------------------------------------------------------
# 间距：4px 基准网格，键是"步数"（0 / 1 / 2 / 3 …），值是逻辑像素。
# 键用字符串是因为步数可以 >9（``SPACE["12"]``），用 int 键会和枚举混淆。
# ---------------------------------------------------------------------------
SPACE_STEPS: tuple[int, ...] = (0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 24, 32, 40)

SPACE: dict[str, int] = {
    str(step): step * 4 for step in SPACE_STEPS
}  # 0 / 4 / 8 / 12 / 16 / 20 / 24 / 32 / 40 / 48 / 64 / 80 / 96 / 128 / 160

#: 常用间距的语义别名（读代码时比记数字清楚）
GAP_TIGHT = SPACE["1"]  # 4  同行元素
GAP = SPACE["2"]  # 8   控件内元素
GAP_LOOSE = SPACE["4"]  # 16  组之间
PAD = SPACE["3"]  # 12  面板内边距
PAD_LOOSE = SPACE["6"]  # 24  卡片内边距

# ---------------------------------------------------------------------------
# 圆角
# ---------------------------------------------------------------------------
RADIUS: dict[str, int] = {
    "none": 0,
    "xs": 2,
    "sm": 4,  # 小色块 / 徽标
    "md": 6,  # 输入框 / 按钮
    "lg": 8,  # 面板 / 卡片
    "xl": 12,  # 大容器
    "full": 999,  # 胶囊 / 头像
}

# ---------------------------------------------------------------------------
# 字号：与 Material 3 的 type scale 对齐的桌面端档位
# ---------------------------------------------------------------------------
FONT_SIZE: dict[str, int] = {
    "caption": 11,  # 标签 / 计数 / 单位
    "small": 12,  # 次要说明 / 脚注
    "body": 13,  # 正文、表单值（本框架默认）
    "subtitle": 14,  # 列表主行
    "title": 16,  # 卡片标题
    "headline": 20,  # 分区标题
    "display": 28,  # 空状态 / 结果页
}

FONT_WEIGHT: dict[str, ft.FontWeight] = {
    "regular": ft.FontWeight.W_400,
    "medium": ft.FontWeight.W_500,
    "semibold": ft.FontWeight.W_600,
    "bold": ft.FontWeight.W_700,
}

# ---------------------------------------------------------------------------
# 动效时长（毫秒）：够短到"跟手"，够长到"看得见"
# ---------------------------------------------------------------------------
DURATION: dict[str, int] = {
    "instant": 0,
    "fast": 120,
    "normal": 200,
    "slow": 320,
}

# ---------------------------------------------------------------------------
# 语义色：Material 3 没有的角色，由框架补齐，明暗各一套。
#
# 每个角色给**三档**（与 M3 的 primary / on-primary / primary-container 同构）——
# 一个色值不可能同时当"填充"和"文字"，实测差得很远：
#   ``#10B981`` 对白底只有 2.54:1，``#F59E0B`` 只有 2.15:1，
#   在它们上面压白字同样只有 2.54 / 2.15 —— 徽标上的字是**读不出来**的。
# 所以：填充色必须深到扛得住白字（>= 4.5:1），文字色另取。
#
#   SEMANTIC      填充：徽标实底 / 状态点 / 进度段
#   SEMANTIC_ON   该填充上的前景（徽标里的文字与图标）
#   SEMANTIC_TEXT 该角色作为页面文字 / 图标 / 细边框时的颜色
#
# 下表所有取值都在浅底 ``#FFFFFF`` 与深底 ``#141414`` 上过了 WCAG 对比度：
# 填充 >= 4.5:1、on >= 4.5:1、text >= 4.5:1（scripts/_theme_logic.py 有断言守着）。
# ---------------------------------------------------------------------------
SEMANTIC: dict[str, dict[str, str]] = {
    "success": {"light": "#047857", "dark": "#34D399"},
    "warning": {"light": "#B45309", "dark": "#FBBF24"},
    "danger": {"light": "#DC2626", "dark": "#F87171"},
    "info": {"light": "#0369A1", "dark": "#38BDF8"},
    "neutral": {"light": "#4B5563", "dark": "#D1D5DB"},
}

#: 铺在语义色**实底**上的前景色（徽标 / 状态胶囊里的文字与图标）
SEMANTIC_ON: dict[str, dict[str, str]] = {
    "success": {"light": "#FFFFFF", "dark": "#04231A"},
    "warning": {"light": "#FFFFFF", "dark": "#2B1A03"},
    "danger": {"light": "#FFFFFF", "dark": "#2E0707"},
    "info": {"light": "#FFFFFF", "dark": "#032234"},
    "neutral": {"light": "#FFFFFF", "dark": "#1A1E24"},
}

#: 语义色作为**页面上的文字 / 图标 / 细边框**时的取值（不做背景）
SEMANTIC_TEXT: dict[str, dict[str, str]] = {
    "success": {"light": "#047857", "dark": "#34D399"},
    "warning": {"light": "#B45309", "dark": "#FBBF24"},
    "danger": {"light": "#DC2626", "dark": "#F87171"},
    "info": {"light": "#0369A1", "dark": "#38BDF8"},
    # 次要信息在深底上要比填充更收敛一档，否则整屏都在喊
    "neutral": {"light": "#6B7280", "dark": "#9CA3AF"},
}

SEMANTIC_ROLES: tuple[str, ...] = tuple(SEMANTIC)

# ---------------------------------------------------------------------------
# 预设品牌色种子：喂给 ``ft.Theme(color_scheme_seed=...)``，
# Flutter 会由此推导出整套 M3 色板（primary / secondary / surface / outline …）。
# ---------------------------------------------------------------------------
PRIMARY_SEEDS: dict[str, str] = {
    "blue": "#1F6FEB",
    "indigo": "#4F46E5",
    "violet": "#7C3AED",
    "teal": "#0D9488",
    "green": "#16A34A",
    "orange": "#EA580C",
    "red": "#DC2626",
    "slate": "#475569",
}

# ---------------------------------------------------------------------------
# 高度：阴影 = 模糊半径 + Y 偏移 + 黑色透明度
# ---------------------------------------------------------------------------
_ELEVATION: dict[int, tuple[float, float, float]] = {
    0: (0.0, 0.0, 0.00),
    1: (2.0, 1.0, 0.06),
    2: (6.0, 2.0, 0.08),
    3: (12.0, 4.0, 0.10),
    4: (24.0, 8.0, 0.12),
}
ELEVATION = tuple(sorted(_ELEVATION))


# ---------------------------------------------------------------------------
# 取值函数
# ---------------------------------------------------------------------------
def _opt_mode(mode: str | None) -> str:
    """把模式归一成 ``"light"`` / ``"dark"``（非法值退回浅色）。

    ``mode=None`` 时取**当前全局主题**解析出的实际模式 —— 这样调用方写
    ``semantic("success")`` 就能自动跟随主题，不必到处传参。
    """
    if mode in ("light", "dark"):
        return mode
    if mode is None:
        # 延迟导入：theme 依赖 tokens，反向依赖会成环
        from ui.core.theme import current_mode

        return current_mode()
    return "light"


def semantic(role: str, mode: str | None = None) -> str:
    """取语义色**填充**（``success`` / ``warning`` / ``danger`` / ``info`` / ``neutral``）。

    用于徽标实底、状态点、进度段这类"要压住内容"的地方 —— 取值保证与白字
    对比度 >= 4.5:1，所以 :func:`on_semantic` 给的白字一定读得出来。

    要给**文字 / 图标 / 细边框**用，请改 :func:`semantic_text`。

    Args:
        role: 语义角色名。非法值退回 ``neutral``（不给调用方抛异常的机会 ——
            状态色错一次的代价远小于让整页崩掉）。
        mode: ``"light"`` / ``"dark"``；``None`` 表示跟随当前主题。

    Returns:
        ``"#RRGGBB"`` 形式的色串。
    """
    return SEMANTIC.get(role, SEMANTIC["neutral"])[_opt_mode(mode)]


def on_semantic(role: str, mode: str | None = None) -> str:
    """取语义色**实底上的前景色**（配 :func:`semantic` 用）。"""
    return SEMANTIC_ON.get(role, SEMANTIC_ON["neutral"])[_opt_mode(mode)]


def semantic_text(role: str, mode: str | None = None) -> str:
    """取语义色作为**页面文字 / 图标 / 细边框**时的取值（不做背景）。"""
    return SEMANTIC_TEXT.get(role, SEMANTIC_TEXT["neutral"])[_opt_mode(mode)]


def overlay(alpha: float, *, role: str = ft.Colors.ON_SURFACE) -> str:
    """主题感知的半透明覆盖色 —— 悬停底色 / 按下态 / 选中底都用它。

    产出 ``"onsurface,0.06"`` 这类**角色名 + 透明度**串，Flutter 会按当前
    ``ColorScheme`` 解析，所以明暗主题下都正确，不需要框架侧做任何事。
    """
    return ft.Colors.with_opacity(alpha, role)


def scrim(alpha: float = 0.32) -> str:
    """浮层遮罩色（点面板外部收起时铺的那层）。基于 ``on_surface`` 而非纯黑，
    这样深色主题下遮罩是"压暗"而不是"加一层灰纱"。"""
    return ft.Colors.with_opacity(alpha, ft.Colors.ON_SURFACE)


def elevation(level: int = 1) -> ft.BoxShadow:
    """按档位取阴影。``level`` 越高层数越高，超界夹到最近的一档。"""
    blur, dy, alpha = _ELEVATION[min(max(level, 0), max(ELEVATION))]
    if level <= 0:
        return ft.BoxShadow(blur_radius=0, spread_radius=0, color=ft.Colors.TRANSPARENT)
    return ft.BoxShadow(
        blur_radius=blur,
        spread_radius=0,
        color=ft.Colors.with_opacity(alpha, ft.Colors.SHADOW),
        offset=ft.Offset(0, dy),
    )


def focus_border(width: float = 2.0) -> ft.BorderSide:
    """聚焦描边（键盘 Tab 走焦用）。用主色 + 2px，与 Material 规范一致。"""
    return ft.BorderSide(width, ft.Colors.PRIMARY)


def hairline() -> ft.BorderSide:
    """1px 分隔线。走 ``OUTLINE_VARIANT`` 而不是固定灰 —— 这是"统一风格"里
    最容易被忽略、但明暗主题下最刺眼的一处。"""
    return ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)