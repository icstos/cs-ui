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

from dataclasses import field
from typing import Any, Callable

import flet as ft

from ui.core.tokens import FONT_SIZE, FONT_WEIGHT, RADIUS, SPACE, semantic_text

__all__ = ["Expander", "DENSITIES", "VARIANTS"]

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
        "title": FONT_SIZE["subtitle"],
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

#: 展开 / 收起的时长与曲线（Material 自己也在用，200ms 左右最跟手）。
_ANIM = ft.AnimationStyle(duration=220, curve=ft.AnimationCurve.EASE_OUT_CUBIC)

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
        dense: 兼容旧参数；``True`` 等价于 ``density="compact"``。
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
    dense: bool = False
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
        """解析密度档位（``dense=True`` 视作 ``compact``）。"""
        name = "compact" if self.dense else self.density
        return DENSITIES.get(name, DENSITIES["default"])

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
        """强调色。``primary`` 走主题角色（换主色自动跟随），
        其余语义色走 :func:`ui.core.tokens.semantic_text`。"""
        role = self.accent or "primary"
        if role == "primary":
            return ft.Colors.PRIMARY
        if role == "neutral":
            return ft.Colors.OUTLINE
        return semantic_text(role)

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
            bgcolor=ft.Colors.with_opacity(0.10, color),
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
# 运行示例（也是本组件的视觉验收页）
# ---------------------------------------------------------------------------


def _body_text() -> list[ft.Control]:
    return [
        ft.Text("内容区任意控件都可以放：表单、表格、代码块……", size=13),
        ft.Text(
            "展开状态由 Flutter 持有，切换不会丢输入内容。",
            size=12,
            color=ft.Colors.ON_SURFACE_VARIANT,
        ),
    ]


@ft.component
def App() -> ft.Control:
    """Expander 运行示例：各种外观 / 密度 / 状态。"""
    return ft.Container(
        padding=24,
        bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
        expand=True,
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=24,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[
                ft.Column(
                    spacing=4,
                    controls=[
                        ft.Text(
                            "Expander 折叠卡片", size=20, weight=ft.FontWeight.BOLD
                        ),
                        ft.Text(
                            "整条标题可点、尾部箭头翻转、展开态靠 1px 分隔线分层。",
                            size=13,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                    ],
                ),
                ft.Text(
                    "card（默认）· 标题 / 副标题 / 前置图标",
                    size=15,
                    weight=ft.FontWeight.W_600,
                ),
                Expander(
                    title="高级设置",
                    subtitle="仅在需要时调整，改动会立即生效",
                    leading=ft.Icons.TUNE,
                    controls=_body_text(),
                ),
                Expander(
                    title="通知",
                    subtitle="邮件、短信与站内信",
                    leading=ft.Icons.NOTIFICATIONS_NONE,
                    accent="info",
                    expanded=True,
                    on_change=lambda v: print(f"[Expander] 通知 -> {v}"),
                    controls=_body_text(),
                ),
                Expander(
                    title="危险操作",
                    subtitle="删除后无法恢复",
                    leading=ft.Icons.WARNING_AMBER_ROUNDED,
                    accent="danger",
                    controls=_body_text(),
                ),
                ft.Text(
                    "filled（浅色块，无描边）· 嵌套分组用",
                    size=15,
                    weight=ft.FontWeight.W_600,
                ),
                Expander(
                    variant="filled",
                    title="筛选条件",
                    subtitle="已选 3 项",
                    leading=ft.Icons.FILTER_ALT,
                    expanded=True,
                    controls=_body_text(),
                ),
                ft.Text(
                    "plain（无边框）· 列表里成组的折叠行",
                    size=15,
                    weight=ft.FontWeight.W_600,
                ),
                Expander(
                    variant="plain",
                    title="日志详情",
                    leading=ft.Icons.ARTICLE_OUTLINED,
                    controls=_body_text(),
                ),
                Expander(
                    variant="plain",
                    title="运行环境",
                    controls=_body_text(),
                ),
                ft.Text(
                    "compact 密度 + 箭头在左 + 尾部附加控件",
                    size=15,
                    weight=ft.FontWeight.W_600,
                ),
                Expander(
                    density="compact",
                    chevron_leading=True,
                    title="src/ui/layout",
                    subtitle="3 个折叠项",
                    trailing=ft.Text("12", size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                    controls=_body_text(),
                ),
                ft.Text(
                    "禁用态（expandable=False）", size=15, weight=ft.FontWeight.W_600
                ),
                Expander(
                    title="团队协作",
                    subtitle="当前套餐不支持",
                    leading=ft.Icons.GROUPS_OUTLINED,
                    expandable=False,
                    controls=_body_text(),
                ),
            ],
        ),
    )


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
