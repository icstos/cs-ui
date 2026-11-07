"""网格布局 (GridView) —— 把一组等宽格子铺成二维网格，超出视口自己滚。

列数有两条路：``runs_count`` 写死几列，或 ``max_extent`` 给一个单元格上限、
让列数跟着容器宽度算。两条路都只决定**宽度** —— 高度由
``child_aspect_ratio`` 从宽度推出来，所以同一张网格里的格子必然一样大，
内容不会把某一行撑高。

用法::

    GridView(
        runs_count=3,               # 固定 3 列
        child_aspect_ratio=1.9,     # 宽 / 高
        height=360,                 # 滚动容器：必须有界高度
        controls=[Card(...), Card(...)],
    )
"""

from __future__ import annotations

import flet as ft

from ui.core.doc import Api, Example, Spec, info, run, tip, warn
from ui.core.tokens import FONT_SIZE, RADIUS, SPACE

__all__ = ["GridView"]

_MUTED = ft.Colors.ON_SURFACE_VARIANT
_LINE = ft.Colors.OUTLINE_VARIANT


@ft.control
class GridView(ft.GridView):
    """等宽格子的二维网格。默认间距取 4px 网格上的 12（flet 原生是 10）。

    ``clip_behavior`` 从 flet 的 ``HARD_EDGE`` 改成 ``ANTI_ALIAS``：格子多为圆角
    卡片，滚到视口边缘时硬边裁剪会留下锯齿。
    """

    spacing: int = SPACE["3"]
    run_spacing: int = SPACE["3"]
    clip_behavior: ft.ClipBehavior = ft.ClipBehavior.ANTI_ALIAS


# ---------------------------------------------------------------------------
# 示例零件
# ---------------------------------------------------------------------------
def _caption(text: str) -> ft.Control:
    return ft.Text(text, size=FONT_SIZE["small"], color=_MUTED)


def _panel(content: ft.Control) -> ft.Container:
    """示例用的卡片底座：主题底色 + 发丝描边，明暗主题都成立。"""
    return ft.Container(
        padding=SPACE["3"],
        bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
        border=ft.Border.all(1, _LINE),
        border_radius=RADIUS["lg"],
        content=content,
    )


#: 基础示例的指标卡：(图标, 名称, 数值, 变化)
_METRICS: tuple[tuple[ft.IconData, str, str, str], ...] = (
    (ft.Icons.RECEIPT_LONG_OUTLINED, "今日订单", "1,284 单", "较昨日 +6.2%"),
    (ft.Icons.PAYMENTS_OUTLINED, "成交金额", "¥ 216,480", "较昨日 +4.8%"),
    (ft.Icons.PERCENT, "退款率", "1.2%", "较上周 -0.3pt"),
    (ft.Icons.PERSON_ADD_ALT_1_OUTLINED, "新增客户", "342 人", "较昨日 +18.0%"),
    (ft.Icons.LOCAL_SHIPPING_OUTLINED, "在途包裹", "96 件", "平均 18.4 小时"),
    (ft.Icons.SUPPORT_AGENT_OUTLINED, "待处理工单", "27 张", "最长等待 3 小时"),
)


def _metric(icon: ft.IconData, name: str, value: str, delta: str) -> ft.Control:
    return _panel(
        ft.Column(
            spacing=SPACE["1"],
            controls=[
                ft.Row(
                    spacing=SPACE["1"],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(icon, size=16, color=ft.Colors.PRIMARY),
                        ft.Text(
                            name,
                            size=FONT_SIZE["small"],
                            color=_MUTED,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                            expand=True,
                        ),
                    ],
                ),
                ft.Text(value, size=FONT_SIZE["headline"], weight=ft.FontWeight.W_700),
                ft.Text(
                    delta,
                    size=FONT_SIZE["caption"],
                    color=_MUTED,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
            ],
        )
    )


#: 自适应示例的服务项：(图标, 名称, 状态)
_SERVICES: tuple[tuple[ft.IconData, str, str], ...] = (
    (ft.Icons.DNS_OUTLINED, "API 网关", "正常"),
    (ft.Icons.STORAGE_OUTLINED, "主库", "正常"),
    (ft.Icons.CLOUD_QUEUE_OUTLINED, "消息队列", "延迟"),
    (ft.Icons.CACHED_OUTLINED, "缓存集群", "正常"),
    (ft.Icons.SEARCH_OUTLINED, "搜索", "正常"),
    (ft.Icons.BACKUP_OUTLINED, "备份", "运行中"),
    (ft.Icons.MONITOR_HEART_OUTLINED, "监控", "正常"),
    (ft.Icons.SECURITY_OUTLINED, "鉴权", "正常"),
)

_TONE: dict[str, ft.ColorValue] = {
    "正常": ft.Colors.PRIMARY,
    "延迟": ft.Colors.ERROR,
    "运行中": ft.Colors.TERTIARY,
}


def _service(icon: ft.IconData, name: str, state: str) -> ft.Control:
    return ft.Container(
        padding=SPACE["2"],
        bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
        border=ft.Border.all(1, _LINE),
        border_radius=RADIUS["md"],
        content=ft.Column(
            spacing=SPACE["1"],
            controls=[
                ft.Icon(icon, size=16, color=ft.Colors.PRIMARY),
                ft.Text(
                    name,
                    size=FONT_SIZE["caption"],
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                ft.Text(state, size=FONT_SIZE["small"], color=_TONE[state]),
            ],
        ),
    )


def _tile(index: int) -> ft.Control:
    """间距对比用的纯色块：没有文字干扰，只看缝有多宽。"""
    return ft.Container(
        alignment=ft.Alignment.CENTER,
        bgcolor=ft.Colors.PRIMARY_CONTAINER,
        border_radius=RADIUS["sm"],
        content=ft.Text(
            str(index),
            size=FONT_SIZE["caption"],
            color=ft.Colors.ON_PRIMARY_CONTAINER,
        ),
    )


def _order(index: int) -> ft.Control:
    """滚动示例里的一格：订单号 + 金额，48 格用来验证滚动。"""
    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=SPACE["2"], vertical=SPACE["1"]),
        bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
        border=ft.Border.all(1, _LINE),
        border_radius=RADIUS["md"],
        content=ft.Column(
            spacing=2,
            controls=[
                ft.Text(
                    f"SO-24{index:03d}",
                    size=FONT_SIZE["small"],
                    weight=ft.FontWeight.W_600,
                ),
                ft.Text(
                    f"¥ {index * 37 + 128:,}",
                    size=FONT_SIZE["caption"],
                    color=_MUTED,
                ),
            ],
        ),
    )


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
@ft.component
def _fixed() -> ft.Control:
    """6 张指标卡、固定 3 列；行高由宽度和 1.9 的宽高比算出来。"""
    return GridView(
        runs_count=3,
        child_aspect_ratio=1.9,
        controls=[_metric(*item) for item in _METRICS],
    )


@ft.component
def _adaptive() -> ft.Control:
    """只给 max_extent：列数由容器宽度决定，窗口一拉就重排。"""
    return GridView(
        max_extent=190,
        child_aspect_ratio=1.25,
        controls=[_service(*item) for item in _SERVICES],
    )


@ft.component
def _gap_compare() -> ft.Control:
    """同一批格子，间距 4 与 16 的对比。"""
    return ft.Column(
        spacing=SPACE["4"],
        controls=[
            ft.Column(
                spacing=SPACE["1"],
                controls=[
                    _caption("spacing=4 / run_spacing=4：格子几乎连成一片"),
                    GridView(
                        height=126,
                        runs_count=6,
                        spacing=SPACE["1"],
                        run_spacing=SPACE["1"],
                        child_aspect_ratio=2.4,
                        controls=[_tile(i) for i in range(1, 13)],
                    ),
                ],
            ),
            ft.Column(
                spacing=SPACE["1"],
                controls=[
                    _caption("spacing=16 / run_spacing=16：每格都能单独读"),
                    GridView(
                        height=130,
                        runs_count=6,
                        spacing=SPACE["4"],
                        run_spacing=SPACE["4"],
                        child_aspect_ratio=2.4,
                        controls=[_tile(i) for i in range(1, 13)],
                    ),
                ],
            ),
        ],
    )


@ft.component
def _many() -> ft.Control:
    """48 格、4 列：网格只构建视口附近的格子，滚动时不会一次性建满。"""
    return GridView(
        runs_count=4,
        child_aspect_ratio=2.6,
        padding=ft.Padding.symmetric(horizontal=SPACE["1"]),
        controls=[_order(index) for index in range(1, 49)],
    )


_BASIC_CODE = """GridView(
    runs_count=3,                 # 固定 3 列
    spacing=12,
    run_spacing=12,
    child_aspect_ratio=1.9,       # 行高 = 格宽 / 1.9
    height=360,                   # 网格自带滚动，必须有界高度
    controls=[metric_card(m) for m in metrics],
)"""

_ADAPTIVE_CODE = """# 不给列数，只给"一格最宽多少"：列数随容器宽度算
GridView(
    max_extent=190,
    child_aspect_ratio=1.25,
    height=380,
    controls=[service_card(s) for s in services],
)"""


SPEC = Spec(
    name="GridView",
    summary="把一组等宽格子铺成二维网格：固定列数或按最小宽度自适应，超出视口自己滚。",
    definition=(
        "GridView 把子项按「先横后纵」铺成网格。列数由 runs_count 写死，或由 "
        "max_extent 按容器宽度算出来；格子的高度不在内容手里 —— 它等于宽度除以 "
        "child_aspect_ratio。因此同一张网格永远横平竖直、每格一样大，一屏能扫完的"
        "信息量比等高不齐的卡片流更可控。它同时是滚动容器：只构建视口附近的格子，"
        "几十上百项也不会把首屏拖慢。"
    ),
    anatomy=[
        (
            "列数",
            "runs_count 固定几列；改用 max_extent 后列数由容器宽度算，runs_count 不再参与。",
        ),
        (
            "格子",
            "宽高都由网格分配：高度 = 格宽 / child_aspect_ratio，与格子里的内容无关。",
        ),
        (
            "间距",
            "spacing 是同行相邻格的水平缝，run_spacing 是行与行之间的垂直缝，默认都是 12。",
        ),
        (
            "滚动区",
            "网格本身就是滚动视口，没有固有高度；高度必须由父级给（height / expand）。",
        ),
        (
            "裁剪",
            "clip_behavior 默认 ANTI_ALIAS：圆角卡片滚到视口边缘时不出现硬边锯齿。",
        ),
    ],
    when=[
        "一组同类卡片铺成墙：指标、商品、数据集缩略图",
        "希望列数跟着窗口宽度走：宽屏多列、窄屏少列，不用写断点",
        "项数多到需要滚动，但仍要保持严格对齐的网格",
    ],
    avoid=[
        "只有几项、且希望卡片高度随内容变：用 Row(wrap=True)，GridView 的格子只能同一个宽高比",
        "一行两三块的并排布局：Row 更直接，还省掉一层滚动容器",
        "要合并单元格（某张卡片占两格、瀑布流）：GridView 不支持跨行跨列，用 Column + Row 手拼",
    ],
    examples=[
        Example(
            "固定三列",
            _fixed,
            hint="6 张指标卡、runs_count=3；行高由格宽和 1.9 的宽高比算出来，不随内容变。",
            code=_BASIC_CODE,
            height=360,
        ),
        Example(
            "按宽度自适应",
            _adaptive,
            hint="只给 max_extent=190：把窗口拉宽拉窄，列数会自己从 3 变到 5。",
            code=_ADAPTIVE_CODE,
            height=380,
        ),
        Example(
            "间距对比",
            _gap_compare,
            hint="同一批格子，4 与 16 两档间距：窄缝适合缩略图，宽缝适合要逐格阅读的卡片。",
            height=380,
        ),
        Example(
            "大量项滚动",
            _many,
            hint="48 格、固定 4 列：网格只构建视口附近的格子，向下滚动不会卡顿。",
            height=360,
        ),
    ],
    api=[
        Api("controls", "list[Control]", "", "网格项，先横后纵依次填入"),
        Api("runs_count", "int", "1", "固定列数；设了 max_extent 后不再起作用"),
        Api(
            "max_extent",
            "int | None",
            "None",
            "单元格最大宽度；设了就按容器宽度自动分列",
        ),
        Api("spacing", "int", "12", "同行相邻格的水平间距（flet 原生是 10）"),
        Api("run_spacing", "int", "12", "行与行之间的垂直间距（flet 原生是 10）"),
        Api(
            "child_aspect_ratio",
            "float",
            "1.0",
            "格子的宽高比（宽 / 高）：1.0 是正方形，越大越扁",
        ),
        Api("padding", "Padding | int | None", "None", "网格四周内边距"),
        Api("horizontal", "bool", "False", "改成从左往右排、纵向分列并横向滚动"),
        Api(
            "build_controls_on_demand",
            "bool",
            "True",
            "只构建视口附近的格子；长网格不要关掉",
        ),
        Api(
            "clip_behavior",
            "ClipBehavior",
            "ANTI_ALIAS",
            "边界裁剪方式；默认已改为抗锯齿，圆角卡片不出锯齿",
        ),
    ],
    notes=[
        warn(
            "GridView 没有固有高度。放进默认的 Column（高度无界）里算不出视口，格子"
            "不会被画出来 —— 先给 height、expand，或让父级先有界。"
        ),
        tip(
            "行高是被算出来的，不是被内容撑出来的。格子里放长标题时用 max_lines + "
            "ELLIPSIS，别让它换行；内容一旦超出格子，Flutter 会直接画溢出条纹。"
        ),
        info(
            "spacing / run_spacing 的默认值从 flet 的 10 改成 12（4px 网格），"
            "clip_behavior 改成 ANTI_ALIAS；两者都只是默认值，显式传参仍然生效。"
        ),
    ],
    tags=("网格", "grid", "gridview", "卡片墙", "自适应", "瀑布流"),
)


if __name__ == "__main__":
    run(SPEC)
