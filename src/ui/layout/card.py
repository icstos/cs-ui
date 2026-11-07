"""卡片 (Card) —— 把一组相关内容收进一块有边界、有层级的面板。

卡片只提供「盒子」：背景、圆角、投影。标题、正文、操作按钮这些结构由
``content`` 里的 :class:`flet.Column` / :class:`flet.Row` 组合出来 —— 组件不预设
版式，所以同一套外观既能装统计数字，也能装一张确认单。

点击与悬停也不在 Card 上（flet 的 Card 没有这两个事件）：需要交互时把 Card
包进一个 ``Container(on_click=..., on_hover=...)``，让外层当热区。

用法::

    Card(
        content=Container(
            padding=16,
            content=Column([Text("本月账单"), Text("¥ 8,420.00")]),
        )
    )
"""

from __future__ import annotations

import flet as ft

from ui.core.doc import Api, Example, Spec, info, run, tip, warn
from ui.core.tokens import FONT_SIZE, FONT_WEIGHT, RADIUS, SPACE

__all__ = ["Card"]

_MUTED = ft.Colors.ON_SURFACE_VARIANT
_LINE = ft.Colors.OUTLINE_VARIANT


@ft.control
class Card(ft.Card):
    """内容面板：主题底色 + 8px 圆角 + 一层浅投影。

    ``border_radius`` 是给圆角留的简写 —— flet 1.x 的 Card 只认 ``shape``，
    这里在 :meth:`init` 里把它翻成 :class:`flet.RoundedRectangleBorder`；
    显式传了 ``shape`` 就以 ``shape`` 为准。
    """

    bgcolor: ft.ColorValue = ft.Colors.SURFACE_CONTAINER_LOW
    border_radius: int = RADIUS["lg"]

    def init(self):
        super().init()
        if self.shape is None:
            self.shape = ft.RoundedRectangleBorder(radius=self.border_radius)


# ---------------------------------------------------------------------------
# 示例零件
# ---------------------------------------------------------------------------
def _caption(text: str) -> ft.Control:
    return ft.Text(text, size=FONT_SIZE["small"], color=_MUTED)


def _pad(content: ft.Control, space: int = SPACE["4"]) -> ft.Control:
    """卡片内边距：Card 自己不带 padding，内容要自己留白。"""
    return ft.Container(padding=space, content=content)


def _badge(text: str) -> ft.Control:
    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=SPACE["2"], vertical=2),
        border_radius=RADIUS["full"],
        bgcolor=ft.Colors.SECONDARY_CONTAINER,
        content=ft.Text(
            text,
            size=FONT_SIZE["caption"],
            color=ft.Colors.ON_SECONDARY_CONTAINER,
        ),
    )


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
@ft.component
def _basic() -> ft.Control:
    """最常用的一屏：标题 + 说明 + 主数值，三层字重拉开层次。"""
    return ft.Column(
        spacing=SPACE["3"],
        controls=[
            Card(
                width=320,
                content=_pad(
                    ft.Column(
                        spacing=SPACE["2"],
                        controls=[
                            ft.Text(
                                "本月账单",
                                size=FONT_SIZE["title"],
                                weight=FONT_WEIGHT["semibold"],
                            ),
                            ft.Text(
                                "截至 11 月 6 日，已出账 12 笔",
                                size=FONT_SIZE["body"],
                                color=_MUTED,
                            ),
                            ft.Text(
                                "¥ 8,420.00",
                                size=FONT_SIZE["display"],
                                weight=FONT_WEIGHT["bold"],
                            ),
                        ],
                    )
                ),
            ),
            _caption(
                "卡片只画边界和投影；标题、正文、数值都是 content 里的 Column 排的。"
            ),
        ],
    )


@ft.component
def _with_actions() -> ft.Control:
    """徽标跟在标题后面，操作沉到底部并靠右 —— 一眼能看出「这是什么、能做什么」。"""
    return Card(
        width=460,
        content=_pad(
            ft.Column(
                spacing=SPACE["3"],
                controls=[
                    ft.Row(
                        spacing=SPACE["2"],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text(
                                "语义化发布",
                                size=FONT_SIZE["title"],
                                weight=FONT_WEIGHT["semibold"],
                            ),
                            _badge("草稿"),
                        ],
                    ),
                    ft.Text(
                        "3 个页面、1 个组件有改动，发布后 5 分钟内生效。",
                        size=FONT_SIZE["body"],
                        color=_MUTED,
                    ),
                    ft.Container(height=1, bgcolor=_LINE),
                    ft.Row(
                        spacing=SPACE["2"],
                        alignment=ft.MainAxisAlignment.END,
                        controls=[
                            ft.TextButton("取消"),
                            ft.FilledButton("查看差异"),
                        ],
                    ),
                ],
            )
        ),
    )


_ENTRIES = (
    ("dash", "仪表盘", "8 个指标，每分钟刷新", ft.Icons.SPACE_DASHBOARD_OUTLINED),
    ("member", "成员", "24 人，3 个待审批", ft.Icons.GROUP_OUTLINED),
    ("audit", "审计日志", "保留最近 90 天", ft.Icons.HISTORY),
)


@ft.component
def _wall() -> ft.Control:
    """三列可点卡片：悬停抬升投影，选中描主色边。"""
    hovered, set_hovered = ft.use_state("")
    picked, set_picked = ft.use_state("")

    def tile(key: str, title: str, desc: str, icon: ft.IconData) -> ft.Control:
        active = picked == key
        lit = hovered == key

        def on_hover(e, k=key):
            set_hovered(k if str(e.data).strip().lower() == "true" else "")

        def on_click(_e, k=key):
            set_picked("" if active else k)

        return ft.Container(
            expand=1,
            border_radius=RADIUS["lg"],
            on_click=on_click,
            on_hover=on_hover,
            content=Card(
                elevation=4 if lit else 1,
                bgcolor=(
                    ft.Colors.SURFACE_CONTAINER_HIGH
                    if lit or active
                    else ft.Colors.SURFACE_CONTAINER_LOW
                ),
                shape=ft.RoundedRectangleBorder(
                    radius=RADIUS["lg"],
                    side=ft.BorderSide(2, ft.Colors.PRIMARY) if active else None,
                ),
                content=_pad(
                    ft.Column(
                        spacing=SPACE["2"],
                        controls=[
                            ft.Icon(icon, size=20, color=ft.Colors.PRIMARY),
                            ft.Text(
                                title,
                                size=FONT_SIZE["subtitle"],
                                weight=FONT_WEIGHT["semibold"],
                            ),
                            ft.Text(desc, size=FONT_SIZE["small"], color=_MUTED),
                            *(
                                [
                                    ft.Text(
                                        "已选中",
                                        size=FONT_SIZE["caption"],
                                        color=ft.Colors.PRIMARY,
                                    )
                                ]
                                if active
                                else []
                            ),
                        ],
                    )
                ),
            ),
        )

    return ft.Column(
        spacing=SPACE["3"],
        controls=[
            ft.Row(
                spacing=SPACE["3"],
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[tile(k, t, d, i) for k, t, d, i in _ENTRIES],
            ),
            _caption(
                "Card 本身不接点击；外面那层透明 Container 才是热区。悬停只改 "
                "elevation 与底色，选中才描主色边 —— 三种状态别用同一种视觉。"
            ),
        ],
    )


_BASIC_CODE = """Card(
    content=Container(
        padding=16,
        content=Column(
            spacing=8,
            controls=[
                Text("本月账单", size=16, weight=ft.FontWeight.W_600),
                Text("已出账 12 笔", size=13, color=ft.Colors.ON_SURFACE_VARIANT),
                Text("¥ 8,420.00", size=28, weight=ft.FontWeight.W_700),
            ],
        ),
    ),
)

# 点击 / 悬停交给外面一层：
Container(
    on_click=open_detail,
    on_hover=lift_card,
    content=Card(content=...),
)"""


SPEC = Spec(
    name="Card",
    summary="把一组相关信息收进一块带底色、圆角和投影的面板。",
    definition=(
        "卡片是「一块内容」的最小边界：它用背景色和投影把相关信息从页面里切出来，"
        "让人一眼看出哪些东西属于同一件事、哪几块是可以并列比较的。它刻意不提供"
        "标题、操作、点击这些结构 —— 版式由 content 里的 Column / Row 组合，"
        "所以同一套外观既能装统计数字，也能装一张待确认的单据。"
    ),
    anatomy=[
        (
            "面板",
            "主题底色 + 8px 圆角（RADIUS['lg']）+ 一层浅投影；投影高度由 elevation 控制，默认 1。",
        ),
        (
            "内容槽",
            "唯一的 content。Card 不带内边距，标题与正文要自己包 Container(padding=16)，否则文字贴着边。",
        ),
        (
            "版式",
            "标题、徽标、正文、操作都由 Column / Row 排；组件不替你决定谁是标题。",
        ),
        (
            "轮廓",
            "shape 决定圆角与描边；border_radius 是圆角简写，init 里翻成 RoundedRectangleBorder。",
        ),
        (
            "交互",
            "Card 没有 on_click / on_hover。要点击就把 Card 包进 Container(on_click=...)，由外层当热区。",
        ),
    ],
    when=[
        "同一主题的多块内容并排比较（指标卡、功能入口、成员卡）",
        "一块内容要和页面背景分开，但还没重到值得开新页面或弹窗",
        "列表里每一项都是可独立阅读的实体，需要明确的边界",
    ],
    avoid=[
        "只是给一块区域换底色：用 Container，别凭空多一层投影和圆角语义",
        "整屏只有一个内容块：直接排版或用 Container，卡片的边界反而画蛇添足",
        "内容需要展开/收起：用 Expander，卡片不负责折叠",
    ],
    examples=[
        Example(
            "基础卡",
            _basic,
            hint="标题、说明、主数值三层字重；间距 8 让三行属于同一块。",
            code=_BASIC_CODE,
        ),
        Example(
            "操作与徽标",
            _with_actions,
            hint="徽标跟在标题右侧，操作沉底靠右，中间用 1px 发丝线分开。",
        ),
        Example(
            "可点卡片墙",
            _wall,
            hint="三列等宽：悬停抬投影、点击选中描边；热区来自外层的 Container。",
        ),
    ],
    api=[
        Api("content", "Control | None", "None", "卡片内容；多块内容先包 Column / Row"),
        Api(
            "bgcolor",
            "ColorValue",
            "SURFACE_CONTAINER_LOW",
            "面板底色；默认取主题容器色，明暗主题自动跟随",
        ),
        Api(
            "elevation",
            "Number | None",
            "None",
            "投影高度，默认按主题取 1；悬停可抬到 3-4",
        ),
        Api(
            "variant",
            "CardVariant",
            "ELEVATED",
            "ELEVATED / FILLED / OUTLINED 三种形态",
        ),
        Api("shape", "OutlinedBorder | None", "None", "轮廓与描边；给了它就以它为准"),
        Api("border_radius", "int", "8", "圆角简写；未传 shape 时用它生成轮廓"),
        Api("shadow_color", "ColorValue | None", "None", "投影颜色；默认跟随主题"),
        Api("clip_behavior", "ClipBehavior | None", "None", "内容超出圆角时是否裁剪"),
    ],
    notes=[
        info(
            "卡片不提供 title / actions / on_click：这些是版式与交互，不是盒子的一部分。"
            "标题用 Text、操作用 Row、点击包一层 Container —— 组合出来的卡片才装得下"
            "各种内容，而不是被固定的三段式卡死。"
        ),
        tip(
            "默认底色是 SURFACE_CONTAINER_LOW 而不是透明。透明卡只剩一圈投影，"
            "铺在同色面板上时几乎看不见边界；真要嵌进同色区域，再显式传 bgcolor。"
        ),
        warn(
            "border_radius 不是 flet 1.x Card 的原生属性（原生只有 shape）。本组件在 "
            "init 里把它翻成 RoundedRectangleBorder；同时传 shape 时以 shape 为准，"
            "两个都改会得到意料之外的圆角。"
        ),
    ],
    tags=("卡片", "card", "面板", "panel", "容器"),
)


if __name__ == "__main__":
    run(SPEC)
