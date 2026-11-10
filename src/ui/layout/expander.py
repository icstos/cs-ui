"""可展开 / 折叠卡片 (Expander)。

"标题行 + 可折叠内容区"是桌面端最常用的容器之一：设置项分组、代码片段、
高级筛选、日志详情都靠它省地方。本组件对齐 Ant Design ``Collapse``、
Element Plus ``ElCollapse``、MUI ``Accordion``、Vuetify ``v-expansion-panels``
与 Windows 11 ``Expander`` 的**共识形态**，并收敛成桌面端的直觉：

- **整条标题都是点击区**（不只是文字），悬停与点击水波纹交给 Flutter 的
  Material ink 绘制 —— Python 侧不回写颜色，大列表里也不掉帧；
- **展开箭头在尾部**，展开时由 Material 平滑翻转 180°；需要"文件树"那种
  箭头在前的形态用 ``chevron_leading=True``；
- **两行式标题**：主标题 14px 中等字重，副标题 12px 次要色，永远左对齐、
  与内容区左边缘对齐（不是和箭头对齐）；
- **展开态靠一条 1px 分隔线交代层次**，而不是给标题行加底色 —— 桌面端
  卡片里再加一层色块会让边界糊掉（``divider=False`` 可关）；
- **三种外观**：``card``（默认，1px 描边卡片）/ ``filled``（无描边的浅色块，
  用于嵌套分组）/ ``plain``（完全无边框，用于列表里成组的折叠行）；
- **三档密度**：``compact`` / ``default`` / ``comfortable``，标题高度 36 / 44 / 52；
- **语义强调色**：``accent`` 决定 ``leading`` 图标的染色 —— 图标自动落到一个
  10% 透明度底色的圆角小方块里（Vuetify / Ant Design 的 prefix icon 形态）；
- **禁用态**：``expandable=False`` 时箭头消失、文字置灰、不再响应点击。

.. note::
    组件继承 :class:`flet.Container`（外框：底色 / 描边 / 圆角 / 裁剪），
    里面挂一个 :class:`flet.ExpansionTile` 负责"点开 / 收起"和高度动画。
    这样拆分是因为 ``ExpansionTile`` 的 ``shape`` 只能画**闭合矩形边框**，
    做不出"一张卡片套住标题 + 内容"的效果；交给外层 Container 才干净。

.. note::
    标题与内容之间的分隔线由本组件自绘：``controls_padding`` 置 0，内容区
    顶部铺一条通宽的 ``OUTLINE_VARIANT`` 1px 细线。交给 Material 画的话
    颜色取自主题、flet 侧不可配，也没法保证通宽（会跟着内容内边距缩进）。

.. note::
    ``@ft.control`` 构建出的控件树是 **frozen** 的，组件里不做任何
    ``control.update()``；展开态由 Flutter 侧持有，切换不会触发 Python 重渲染，
    也不会丢内容区里输入框已填的值。

用法::

    Expander(
        title="高级设置",
        subtitle="仅在需要时调整",
        leading=ft.Icons.TUNE,
        controls=[ft.Text("……")],
    )
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import field
from typing import Any

import flet as ft

from ui.core.doc import Api, Example, Spec, info, run, tip, warn
from ui.core.tokens import (
    DURATION,
    FONT_SIZE,
    FONT_WEIGHT,
    RADIUS,
    SEMANTIC_TINT,
    SPACE,
    accent_text,
)

__all__ = ["DENSITIES", "VARIANTS", "Expander"]

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------
#: 三档密度。``min_h`` 标题行最小高度，``pad_x`` 标题左右内边距，
#: ``body_y`` 内容区上下内边距，``gap`` 图标与文字 / 内容行的间距，
#: ``chip`` 前置图标的染色方块边长，``title`` / ``sub`` 主副标题字号。
DENSITIES: dict[str, dict[str, int]] = {
    "compact": {
        "min_h": 36,
        "pad_x": SPACE["3"],
        "body_y": SPACE["2"],
        "gap": SPACE["2"],
        "chip": 24,
        "title": FONT_SIZE["body"],
        "sub": FONT_SIZE["caption"],
    },
    "default": {
        "min_h": 44,
        "pad_x": SPACE["4"] - 2,
        "body_y": SPACE["3"],
        "gap": SPACE["2"],
        "chip": 28,
        "title": FONT_SIZE["body"],
        "sub": FONT_SIZE["small"],
    },
    "comfortable": {
        "min_h": 52,
        "pad_x": SPACE["4"],
        "body_y": SPACE["4"],
        "gap": SPACE["3"],
        "chip": 32,
        "title": FONT_SIZE["title"],
        "sub": FONT_SIZE["small"],
    },
}

VARIANTS = ("card", "filled", "plain")

#: 外观预设：``bg`` 底色、``border`` 描边色（``None`` 表示不描边）。
_VARIANT_STYLE: dict[str, dict[str, Any]] = {
    # 卡片：与 demo 里其它卡片一致 —— 底色 SURFACE、1px OUTLINE_VARIANT 描边
    "card": {"bg": ft.Colors.SURFACE, "border": ft.Colors.OUTLINE_VARIANT},
    # 浅色块：靠底色区分，不再描边（嵌套分组里比再画一层框干净）
    "filled": {"bg": ft.Colors.SURFACE_CONTAINER_LOW, "border": None},
    # 纯行：完全融入页面，用于列表里的成组折叠行
    "plain": {"bg": ft.Colors.TRANSPARENT, "border": None},
}

#: 展开 / 收起的时长与曲线（取 DURATION 的 normal 档：再慢就跟不上点击节奏）。
_ANIM = ft.AnimationStyle(
    duration=DURATION["normal"], curve=ft.AnimationCurve.EASE_OUT_CUBIC
)

MUTED_FG = ft.Colors.with_opacity(0.38, ft.Colors.ON_SURFACE)
DIVIDER_COLOR = ft.Colors.OUTLINE_VARIANT


@ft.control
class Expander(ft.Container):
    """可展开 / 折叠卡片，继承自 :class:`flet.Container`。

    Args:
        title: 标题文本，或任意控件（传控件时原样放在标题行）。
        controls: 展开后显示的内容控件列表。
        subtitle: 副标题，排在标题下方一行；``None``（默认）则单行标题。
        leading: 前置图标 —— 传 ``ft.Icons.XXX``（或图标名字符串）时自动落到
            一个 ``accent`` 色的圆角淡底方块里；传其它控件则原样使用、不染色。
        trailing: 尾部附加控件（计数、徽标、状态点…），排在标题右侧、箭头左侧；
            旋转箭头永远独占最右一格，不会被它挤掉。
        expanded: 初始是否展开，默认 ``False``。
        expandable: 置 ``False`` 为禁用态 —— 箭头消失、文字置灰、点击无反应。
        variant: 外观 —— ``card``（默认）/ ``filled`` / ``plain``。
        density: 密度 —— ``compact`` / ``default`` / ``comfortable``。
        accent: 前置图标的强调色 —— ``primary``（默认）/ ``success`` /
            ``warning`` / ``danger`` / ``info`` / ``neutral``。
        chevron: 是否显示展开箭头，默认 ``True``。
        chevron_leading: 箭头放在标题左侧（文件树 / Windows 设置那种形态）。
        divider: 展开内容上方是否画 1px 分隔线，默认 ``True``。
        spacing: 内容区各控件之间的行距，默认 8。
        content_padding: 内容区内边距，覆盖 ``density`` 算出的默认值。
        on_change: 展开状态变化回调，收到新的展开状态（``bool``）。
        border_radius: 外框圆角，默认 :data:`ui.core.tokens.RADIUS` 的 ``lg``（8）。

    其余参数（``bgcolor`` / ``border`` / ``margin`` / ``width`` …）沿用
    :class:`flet.Container` 的语义；显式传 ``bgcolor`` / ``border`` 会覆盖
    ``variant`` 的预设。
    """

    # ---- 内容 ---------------------------------------------------------
    title: ft.StrOrControl = ""
    controls: list[ft.Control] = field(default_factory=list)
    subtitle: ft.StrOrControl | None = None
    leading: ft.IconDataOrControl | None = None
    trailing: ft.Control | None = None

    # ---- 状态 ---------------------------------------------------------
    expanded: bool = False
    expandable: bool = True
    on_change: Callable[[bool], None] | None = None

    # ---- 外观 ---------------------------------------------------------
    variant: str = "card"
    density: str = "default"
    accent: str = "primary"
    chevron: bool = True
    chevron_leading: bool = False
    divider: bool = True
    spacing: int = SPACE["2"]
    content_padding: ft.PaddingValue | None = None

    def init(self) -> None:
        """flet 生命周期：把外框样式与内部标题 / 内容树一次性搭好。"""
        d = self._density()
        radius = self._radius()
        style = (
            _VARIANT_STYLE.get(self.variant if self.variant in VARIANTS else "card")
            or _VARIANT_STYLE["card"]
        )

        self._apply_frame(style, radius)
        self.content = (
            self._build_tile(d, radius) if self.expandable else self._build_static(d)
        )

    # ------------------------------------------------------------------
    # 外框
    # ------------------------------------------------------------------
    def _apply_frame(self, style: dict[str, Any], radius: float) -> None:
        """底色 / 描边 / 圆角 / 裁剪。显式传入的值优先于 ``variant`` 预设。"""
        if self.bgcolor is None:
            self.bgcolor = style["bg"]
        if self.border is None and style["border"] is not None:
            self.border = ft.Border.all(1, style["border"])
        if self.border_radius is None:
            self.border_radius = radius
        if self.padding is None:
            self.padding = 0
        # 圆角要真的剪出来：否则展开瞬间内容与标题行的 ink 会从四角溢出。
        self.clip_behavior = ft.ClipBehavior.ANTI_ALIAS

    def _density(self) -> dict[str, int]:
        """解析密度档位；未知档位落到 ``default``。"""
        return DENSITIES.get(self.density, DENSITIES["default"])

    def _radius(self) -> float:
        """外框圆角（px）。``border_radius`` 可能是数字，也可能是 ``BorderRadius``。"""
        value = self.border_radius
        if value is None:
            return float(RADIUS["lg"])
        if isinstance(value, (int, float)):
            return float(value)
        return float(getattr(value, "top_left", 0) or 0)

    # ------------------------------------------------------------------
    # 标题行
    # ------------------------------------------------------------------
    def _accent_color(self) -> ft.ColorValue:
        """强调色。走 :func:`ui.core.tokens.accent_text` —— ``primary``
        得到主题角色（换主色自动跟随），其余得到语义色的文字档。"""
        role = self.accent or "primary"
        if role == "neutral":
            # 中性档要的是**结构性**的灰（描边色），不是语义上的"无状态"灰：
            # 前者由主题解析、深色下自动变浅，后者是固定 hex。
            return ft.Colors.OUTLINE
        return accent_text(role)

    def _build_leading(
        self, d: dict[str, int], *, muted: bool = False
    ) -> ft.Control | None:
        """前置元素。图标字符串 → 染色圆角方块；其它控件原样返回。"""
        lead = self.leading
        if lead is None:
            return None
        # ``ft.Icons`` 是 ``IconData``（IntEnum）的枚举成员，**不是** str 子类，
        # 所以这里必须判 IconData 而不是 str，否则图标会被当成"控件"原样透传。
        if not isinstance(lead, (str, ft.IconData)):
            return lead

        color = ft.Colors.OUTLINE if muted else self._accent_color()
        chip = d["chip"]
        return ft.Container(
            width=chip,
            height=chip,
            border_radius=ft.BorderRadius.all(RADIUS["md"]),
            bgcolor=ft.Colors.with_opacity(SEMANTIC_TINT, color),
            alignment=ft.Alignment.CENTER,
            content=ft.Icon(lead, size=round(chip * 0.62), color=color),
        )

    def _build_title(self, d: dict[str, int], *, muted: bool = False) -> ft.Control:
        """标题 +（可选）副标题。两行都不折行 —— 折行会把标题行撑高，
        同组几个 Expander 的行高就参差了。"""
        title = self.title
        if isinstance(title, str):
            title = ft.Text(
                title,
                size=d["title"],
                weight=FONT_WEIGHT["medium"],
                color=MUTED_FG if muted else ft.Colors.ON_SURFACE,
                no_wrap=True,
                overflow=ft.TextOverflow.ELLIPSIS,
            )

        subtitle = self.subtitle
        if subtitle is None:
            return title
        if isinstance(subtitle, str):
            subtitle = ft.Text(
                subtitle,
                size=d["sub"],
                color=MUTED_FG if muted else ft.Colors.ON_SURFACE_VARIANT,
                no_wrap=True,
                overflow=ft.TextOverflow.ELLIPSIS,
            )
        return ft.Column(spacing=0, tight=True, controls=[title, subtitle])

    def _build_title_row(self, d: dict[str, int], *, muted: bool = False) -> ft.Control:
        """标题行 = ``[前置图标] + 标题块 + [尾部控件]``。

        前置图标**不走** ``ExpansionTile.leading``：ListTile 会给 leading 固定
        ``min_leading_width=40`` 的槽位、再加 ``horizontal_title_gap=16``，
        图标因此被推到离左边 20px 的地方，标题也跟着右移一截 —— 既和内容区的
        左边缘对不上，也让整个标题行显得松散。自己拼一行，间距就完全可控：
        图标紧贴 ``pad_x``，标题紧跟图标 ``gap``，内容区再按同样的缩进对齐。

        尾部控件同样**不走** ``ExpansionTile.trailing``：那个槽位与旋转箭头
        挤在同一条尾巴上，一旦尾部控件有点宽度，箭头就会被挤出卡片右边缘
        并被 ``clip_behavior`` 裁掉（实测真的会消失）。放进标题行右侧，
        箭头永远独占它那一格。
        """
        lead = self._build_leading(d, muted=muted)
        title = self._build_title(d, muted=muted)
        if lead is None and self.trailing is None:
            return title

        cells: list[ft.Control] = []
        if lead is not None:
            cells.append(lead)
        cells.append(ft.Container(expand=True, content=title))
        if self.trailing is not None:
            cells.append(self.trailing)
        return ft.Row(
            spacing=d["gap"],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=cells,
        )

    def _body_indent(self, d: dict[str, int]) -> int:
        """内容区左缩进 —— 与标题文字的左边缘对齐（有前置元素时让开那一列）。"""
        if self.leading is None:
            return d["pad_x"]
        return d["pad_x"] + self._lead_width(d) + d["gap"]

    def _lead_width(self, d: dict[str, int]) -> int:
        """前置元素占的宽度。

        图标字符串会被包进 ``chip`` 大小的方块；用户直接给控件时按它的
        ``width`` / ``Icon.size`` 估算 —— 估不准就退回 ``chip``，
        宁可差几像素，也不要让内容区缩进到莫名其妙的深度。
        """
        lead = self.leading
        if lead is None:
            return 0
        if isinstance(lead, (str, ft.IconData)):
            return d["chip"]
        width = getattr(lead, "width", None)
        if isinstance(width, (int, float)):
            return int(width)
        if isinstance(lead, ft.Icon):
            return int(lead.size or 24)
        return d["chip"]

    # ------------------------------------------------------------------
    # 内容区
    # ------------------------------------------------------------------
    def _build_body(self, d: dict[str, int]) -> ft.Control:
        """内容区：1px 分隔线 + 内边距 + 用户控件。

        分隔线单独占一行、撑满整宽（MUI ``Accordion`` / Windows 11 的做法），
        比"给标题行加底色"更清楚，也不会和卡片描边抢注意力。
        """
        inset = self._body_indent(d)
        pad = self.content_padding or ft.Padding.only(
            left=inset,
            right=d["pad_x"],
            top=d["body_y"],
            bottom=d["body_y"],
        )
        block = ft.Container(
            padding=pad,
            content=ft.Column(
                controls=list(self.controls),
                spacing=self.spacing,
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.START,
            ),
        )
        if not self.divider:
            return block
        return ft.Column(
            spacing=0,
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[
                ft.Container(height=1, bgcolor=DIVIDER_COLOR),
                block,
            ],
        )

    # ------------------------------------------------------------------
    # 展开 / 收起
    # ------------------------------------------------------------------
    def _build_tile(self, d: dict[str, int], radius: float) -> ft.ExpansionTile:
        """交给 Material 的 ``ExpansionTile`` 持有展开状态与高度动画。"""
        tile = ft.ExpansionTile(
            title=self._build_title_row(d),
            controls=[self._build_body(d)],
            # 内容区自己管内边距，Material 的默认 padding 会让分隔线缩进。
            controls_padding=0,
            tile_padding=ft.Padding.symmetric(horizontal=d["pad_x"], vertical=0),
            min_tile_height=d["min_h"],
            affinity=(
                ft.TileAffinity.LEADING
                if self.chevron_leading
                else ft.TileAffinity.TRAILING
            ),
            expanded=self.expanded,
            expanded_alignment=ft.Alignment.TOP_LEFT,
            # 内容要撑满整宽（分隔线得通到卡片两侧描边）
            expanded_cross_axis_alignment=ft.CrossAxisAlignment.STRETCH,
            # 标题行底色保持透明：卡片底色统一，靠分隔线分层
            bgcolor=ft.Colors.TRANSPARENT,
            collapsed_bgcolor=ft.Colors.TRANSPARENT,
            # 收起时不销毁内容：ExpansionTile 默认每次展开都重建子树，
            # 输入框里填过的值会跟着消失 —— 折叠面板不该有这种副作用。
            maintain_state=True,
            text_color=ft.Colors.ON_SURFACE,
            collapsed_text_color=ft.Colors.ON_SURFACE,
            icon_color=ft.Colors.OUTLINE,
            collapsed_icon_color=ft.Colors.OUTLINE,
            # 只画圆角、不画边框（边框由外层 Container 负责）——
            # 这样标题行的 ink 高亮才会被圆角裁住，不会从四角溢出。
            shape=ft.RoundedRectangleBorder(
                radius=ft.BorderRadius.only(top_left=radius, top_right=radius)
            ),
            collapsed_shape=ft.RoundedRectangleBorder(
                radius=ft.BorderRadius.all(radius)
            ),
            show_trailing_icon=self.chevron,
            animation_style=_ANIM,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            on_change=self._handle_change,
        )
        return tile

    def _build_static(self, d: dict[str, int]) -> ft.Control:
        """禁用态：不出箭头、不给内容、关掉水波纹。

        仍然复用 ``ExpansionTile`` 而不是自绘一行 —— 行高、图标的垂直居中、
        ``tile_padding`` 全部由它算好，置灰后与可用的兄弟项**逐像素对齐**。
        """
        return ft.ExpansionTile(
            title=self._build_title_row(d, muted=True),
            controls=[],
            tile_padding=ft.Padding.symmetric(horizontal=d["pad_x"], vertical=0),
            min_tile_height=d["min_h"],
            bgcolor=ft.Colors.TRANSPARENT,
            collapsed_bgcolor=ft.Colors.TRANSPARENT,
            text_color=MUTED_FG,
            collapsed_text_color=MUTED_FG,
            shape=ft.RoundedRectangleBorder(radius=ft.BorderRadius.all(self._radius())),
            collapsed_shape=ft.RoundedRectangleBorder(
                radius=ft.BorderRadius.all(self._radius())
            ),
            show_trailing_icon=False,
            enable_feedback=False,
        )

    def _handle_change(self, e: ft.ControlEvent) -> None:
        """把 flet 的 ControlEvent 归一成 ``bool`` 再抛给调用方。"""
        callback = self.on_change
        if callback is None:
            return
        data = e.data
        expanded = data if isinstance(data, bool) else str(data).lower() == "true"
        callback(expanded)


# ---------------------------------------------------------------------------
# 示例（也是本组件的视觉验收页）
# ---------------------------------------------------------------------------
_MUTED = ft.Colors.ON_SURFACE_VARIANT


def _lines(head: str, note: str) -> list[ft.Control]:
    """内容区的示意文本：一行正文 + 一行次要说明。"""
    return [
        ft.Text(head, size=FONT_SIZE["body"]),
        ft.Text(note, size=FONT_SIZE["small"], color=_MUTED),
    ]


@ft.component
def _basic() -> ft.Control:
    """单个面板：默认展开，收起再展开内容还在。"""
    opened, set_opened = ft.use_state(True)
    return ft.Column(
        spacing=12,
        controls=[
            Expander(
                title="高级设置",
                subtitle="仅在需要时调整，改动立即生效",
                leading=ft.Icons.TUNE,
                expanded=True,
                on_change=set_opened,
                controls=_lines(
                    "请求超时 30 秒，失败自动重试 2 次。",
                    "展开态由 Flutter 持有，收起再展开不会重建内容。",
                ),
            ),
            ft.Text(
                f"on_change：{'展开' if opened else '收起'}",
                size=FONT_SIZE["small"],
                color=_MUTED,
            ),
        ],
    )


_PANELS = (
    ("基础信息", "名称、描述与负责人", ft.Icons.BADGE_OUTLINED, "primary"),
    ("通知", "邮件、短信与站内信", ft.Icons.NOTIFICATIONS_NONE, "info"),
    ("危险操作", "删除后无法恢复", ft.Icons.WARNING_AMBER_ROUNDED, "danger"),
)


@ft.component
def _accordion() -> ft.Control:
    """三个面板同时只开一个。"""
    opened, set_opened = ft.use_state(0)

    def toggle(index: int, is_open: bool) -> None:
        set_opened(index if is_open else -1)

    panels = [
        Expander(
            # 展开态由 Flutter 侧持有，改 key 才会按新的 expanded 重新挂载 ——
            # 联动开合只能这么做到，代价是切换时不播展开动画。
            key=f"acc-{index}-{opened}",
            title=title,
            subtitle=subtitle,
            leading=icon,
            accent=accent,
            expanded=index == opened,
            on_change=lambda value, index=index: toggle(index, value),
            controls=_lines(
                f"{title}的内容放在这里。",
                "展开另一个面板时，这一个会自动收起。",
            ),
        )
        for index, (title, subtitle, icon, accent) in enumerate(_PANELS)
    ]
    current = _PANELS[opened][0] if opened >= 0 else "无"
    return ft.Column(
        spacing=12,
        controls=[
            *panels,
            ft.Text(f"当前展开：{current}", size=FONT_SIZE["small"], color=_MUTED),
        ],
    )


@ft.component
def _variants() -> ft.Control:
    """三种外观、两档密度与禁用态并排看。"""
    return ft.Column(
        spacing=10,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        controls=[
            Expander(
                title="card",
                subtitle="1px 描边 + 表面底色，页面里的独立卡片",
                controls=_lines("默认外观。", "展开后靠一条 1px 分隔线分层。"),
            ),
            Expander(
                variant="filled",
                title="filled",
                subtitle="无描边的浅色块，用在嵌套分组里",
                leading=ft.Icons.FILTER_ALT,
                accent="success",
                expanded=True,
                controls=_lines("已选 3 项筛选条件。", "再画一层框会和外层卡片打架。"),
            ),
            Expander(
                variant="plain",
                density="compact",
                chevron_leading=True,
                title="plain · compact",
                subtitle="箭头在左、标题 36 高，列表里的折叠行",
                leading=ft.Icons.FOLDER_OPEN_OUTLINED,
                trailing=ft.Text("12", size=FONT_SIZE["small"], color=_MUTED),
                controls=_lines(
                    "src/ui/layout 下的 12 个文件。", "尾部控件排在箭头左侧。"
                ),
            ),
            Expander(
                title="团队协作",
                subtitle="当前套餐不支持",
                leading=ft.Icons.GROUPS_OUTLINED,
                expandable=False,
            ),
        ],
    )


_BASIC_CODE = """Expander(
    title="高级设置",
    subtitle="仅在需要时调整",
    leading=ft.Icons.TUNE,
    expanded=False,              # 只是初始值，之后由 Flutter 持有
    on_change=lambda open_: print("展开" if open_ else "收起"),
    controls=[ft.Text("超时 30 秒"), ft.Text("重试 2 次")],
)"""

_ACCORDION_CODE = """opened, set_opened = ft.use_state(0)      # -1 = 全部收起

def panel(i, title):
    return Expander(
        key=f"p{i}-{opened}",              # 改 key 才会按新的 expanded 重新挂载
        title=title,
        expanded=opened == i,
        on_change=lambda is_open: set_opened(i if is_open else -1),
        controls=[...],
    )

Column([panel(0, "通知"), panel(1, "危险操作")])"""

SPEC = Spec(
    name="Expander",
    summary="一条标题行收住一整块内容，点开才占地方。",
    definition=(
        "折叠面板把「偶尔要用、但不能没有」的内容收在标题后面，页面上只留一行。"
        "Expander 在标题行上解决了三件容易做歪的事：整条都可点、箭头永远独占最右一格、"
        "内容区的左边缘与标题文字对齐。外观分 card / filled / plain 三档，对应页面里的"
        "独立卡片、嵌套分组和列表里的折叠行。"
    ),
    anatomy=[
        (
            "标题行",
            (
                "整条都是点击区，36 / 44 / 52 三档高度；悬停与点击的水波纹交给"
                " Material ink，不经过 Python。"
            ),
        ),
        (
            "前置图标",
            "传图标时自动落进 accent 色的 10% 淡底圆角方块；传其它控件则原样使用、不染色。",
        ),
        (
            "副标题",
            "标题下方一行 12px 次要色，交代「里面是什么」。标题与副标题都不折行，超长省略。",
        ),
        (
            "尾部与箭头",
            "trailing 排在标题右侧，旋转箭头独占最右一格 —— 尾部控件再宽也挤不掉它。",
        ),
        (
            "内容区",
            "展开后顶部一条通宽 1px 分隔线，再按标题文字的缩进排内容；关掉 divider 就只剩内边距分层。",
        ),
    ],
    when=[
        "设置页把十几个选项分成「基础 / 通知 / 危险操作」几组",
        "高级筛选、大段说明这类低频但必须能查到的内容",
        "长表单按段收纳，让用户一次只面对一屏",
    ],
    avoid=[
        "几块内容要互相对照：用 Tabs 平铺，别让用户反复点开又收起",
        "内容只有一两行：直接摆出来，多一次点击并没有换回空间",
        (
            "需要程序统一控制开合（全部展开 / 联动收起）：展开态在 Flutter 侧，"
            "成组控制得靠重建控件，会丢掉动画与已输入的值"
        ),
    ],
    examples=[
        Example(
            "基础用法",
            _basic,
            hint="一个默认展开的面板，on_change 把新的开合状态回写到 state。",
            code=_BASIC_CODE,
        ),
        Example(
            "手风琴",
            _accordion,
            hint="三个面板同时只开一个：点开哪个就只留哪个，再点当前项则全部收起。",
            code=_ACCORDION_CODE,
        ),
        Example(
            "外观、密度与禁用",
            _variants,
            hint="card / filled / plain 三种外观，compact 密度与箭头在左，最后一条是 expandable=False。",
        ),
    ],
    api=[
        Api("title", "ft.StrOrControl", "''", "标题文本；传控件则原样放进标题行"),
        Api(
            "subtitle",
            "ft.StrOrControl | None",
            "None",
            "标题下方一行说明，留空即单行标题",
        ),
        Api("controls", "list[ft.Control]", "[]", "展开后显示的内容"),
        Api(
            "leading",
            "ft.IconDataOrControl | None",
            "None",
            "前置图标（自动染色）或任意控件",
        ),
        Api("expanded", "bool", "False", "初始是否展开；之后由 Flutter 持有"),
        Api(
            "expandable", "bool", "True", "置 False 为禁用态：无箭头、文字置灰、点不动"
        ),
        Api(
            "variant",
            "str",
            '"card"',
            "外观：card 描边卡片 / filled 浅色块 / plain 无框行",
        ),
        Api(
            "density",
            "str",
            '"default"',
            "标题行高度：compact 36 / default 44 / comfortable 52",
        ),
        Api(
            "accent",
            "str",
            '"primary"',
            "前置图标染色：primary / success / warning / danger / info / neutral",
        ),
        Api(
            "on_change",
            "Callable[[bool], None] | None",
            "None",
            "开合回调，参数是新状态",
        ),
    ],
    notes=[
        tip(
            "展开态由 Flutter 的 ExpansionTile 持有，组件不做 control.update()，切换开合"
            "不会重渲染 Python 侧；展开时长收到 DURATION 的 normal 档（200ms）。内部开了"
            " maintain_state，收起再展开不会重建内容 —— 输入框里填过的值不会丢。"
        ),
        info(
            "expanded 只是挂载时的初值。要让「同时只开一个」这类联动生效，得把目标状态"
            "编进 key 让面板重新挂载（手风琴示例），代价是切换时没有展开动画。"
        ),
        warn(
            "expandable=False 时不渲染 controls：它表达的是「这块现在不可用」，不是"
            "「内容藏起来」。真要藏内容，用 expanded=False 的普通面板。"
        ),
    ],
    tags=("折叠", "折叠面板", "手风琴", "collapse", "accordion"),
)


if __name__ == "__main__":
    run(SPEC)
