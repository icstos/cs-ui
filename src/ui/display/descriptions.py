"""描述列表组件 (Descriptions)。

"一条记录有十几个字段，怎么摆得整齐又不浪费空间" —— 描述列表用一张**可跨列
的网格**回答这个问题，参考 Element UI ``el-descriptions`` 的能力集：

- **默认带边框、横向**：标签格淡底色、内容格浅色底，1px 细线分隔，外框圆角
  8 —— 看上去就是一张表，但没有表头，行高由内容决定；
- **``column`` 网格**：一行放几个字段；``span`` 让某个字段跨列，长地址、备注
  这类内容最需要它。某行没排满时**最后一项吃掉剩余列**，边框里不会留空洞；
- **``direction="vertical"``**：标签在上、内容在下，适合窄容器里的字段卡片；
- **无边框模式**：``bordered=False`` 时按列对齐排布、标签后自动补冒号，适合
  嵌在已有卡片里，不与外框"画两道线"；
- **无状态**：纯展示控件，布局在 :meth:`init` 里一次算完，重绘不产生额外开销。

.. note::
    flet 没有带 ``rowspan`` 的表格原语。这里用 ``Row`` + ``expand=span`` 的
    权重做列宽：**同一行的权重之和恒等于 ``column``**，于是各行的列宽天然对齐
    —— 既不需要测量像素，也不依赖固定宽度，窗口缩放时自动跟着走。

.. note::
    边框只画"需要的那一条边"：单元格只画右 / 下两条，外框交给外层容器。
    这样既不出现双线，也不要求相邻单元格严丝合缝（差 1px 就露缝）。

.. note::
    ``label`` 的颜色 / 底色都在这里定死，是为了让"标签格 / 内容格"这道
    视觉分界在任何主题下都成立；要更强的内容表达（状态徽标、链接、按钮），
    把控件直接放进 ``value`` 即可。

用法::

    Descriptions(
        title="用户信息",
        items=[
            DescriptionsItem("用户名", "kooriookami"),
            DescriptionsItem("手机号", "18100000000"),
            DescriptionsItem("联系地址", "江苏省苏州市吴中区吴中大道 1188 号", span=2),
        ],
        column=3,
    )
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import flet as ft

from ui.core.doc import Api, Example, Spec, info, run, tip, warn
from ui.core.empty import empty_line
from ui.core.responsive import resolve, size_class, viewport
from ui.core.i18n import t
from ui.core.tokens import FONT_SIZE, RADIUS, SPACE, semantic_text

__all__ = ["Descriptions", "DescriptionsItem"]

#: 三档各自的行切分上限 —— 只用于文档与测试断言（列数由调用方给）。
_TIERS: dict[str, int] = {"compact": 1, "medium": 2, "expanded": 3}

# ---------------------------------------------------------------------------
# 视觉常量
# ---------------------------------------------------------------------------
LINE_W = 1
LINE: ft.ColorValue = ft.Colors.OUTLINE_VARIANT
LABEL_BG: ft.ColorValue = ft.Colors.SURFACE_CONTAINER_HIGH
SURFACE: ft.ColorValue = ft.Colors.SURFACE
MUTED: ft.ColorValue = ft.Colors.ON_SURFACE_VARIANT

#: 表格外框圆角：与面板 / 卡片同档
TABLE_RADIUS = RADIUS["lg"]
LABEL_W = 92  # 横向模式的标签列宽（固定像素，标签因此跨行对齐）

#: 尺寸档位 → (水平内边距, 垂直内边距, 字号)
SIZES: dict[str, tuple[int, int, float]] = {
    "default": (12, 8, 13.0),
    "small": (8, 5, 12.5),
}

#: 兼容 Element 的档位命名，避免迁移时踩空。
_SIZE_ALIASES = {"medium": "default", "large": "default", "mini": "small"}

#: 「画哪两条边」只有四种组合，边线值也就只有一条 —— 建一次共享到底。
#: ``ft.Border`` 是纯值对象（序列化出去就完事），共享实例不会互相影响。
#: 不画的那一边必须**显式传 None**：``ft.Border()`` 的字段默认值是
#: ``BorderSide(width=0, style=NONE)``，画出来同样是无线，但语义是"有边、宽度 0"。
_EDGE_SIDE = ft.BorderSide(LINE_W, LINE)
_EDGES: dict[tuple[bool, bool], ft.Border] = {
    (True, True): ft.Border(right=_EDGE_SIDE, bottom=_EDGE_SIDE),
    (True, False): ft.Border(right=_EDGE_SIDE, bottom=None),
    (False, True): ft.Border(right=None, bottom=_EDGE_SIDE),
    (False, False): ft.Border(right=None, bottom=None),
}


@dataclass
class DescriptionsItem:
    """一个字段：标签 + 内容。

    Args:
        label: 字段名。留空则只占内容位（例如需要在网格里插一条长说明）。
        value: 字段内容。字符串直接渲染，其它值按 ``str()`` 处理；也可以传任意
            :class:`flet.Control`（徽标、链接、一行按钮），组件原样放进内容格。
        span: 跨几列，默认 1；超过 ``column`` 会被夹到 ``column``。
        icon: 标签前的图标（可选）。
    """

    label: str = ""
    value: Any = ""
    span: int = 1
    icon: ft.IconData | None = None


@ft.control
class Descriptions(ft.Container):
    """描述列表，继承自 :class:`flet.Container`。

    Args:
        items: :class:`DescriptionsItem` 列表，也接受
            ``{"label": ..., "value": ..., "span": ...}`` 这种字典写法。
        column: 一行放几个字段，默认 3。也可以按断点给：
            ``{"compact": 1, "medium": 2, "expanded": 3}`` —— 组件按**自身宽度**
            **在构建时**选档（换档 = 换行切分，属于结构变化；见下方 Notes）。
        direction: ``horizontal``（标签在左，默认）或 ``vertical``（标签在上）。
        bordered: 是否带边框与分隔线，**默认 ``True``**。
        size: ``default`` / ``small``，只影响内边距与字号；``medium`` / ``mini``
            按 Element 的写法也能用。
        title: 左上角标题。
        extra: 右上角操作区，字符串或任意控件。
        colon: 无边框模式是否给标签补冒号（带边框时不补 —— 底色已经分开了）。
        label_width: 横向模式标签列宽，默认 92。

    Notes:
        内容可以是任意控件，所以"值"的表现力不受限，组件只管格子怎么排。

        标签列宽固定（``label_width``）是为了换行时**每一行都对得齐**；代价是极窄容器
        （约 < 400px）里标签与内容会互相挤压 —— 这时减少 ``column`` 或调小
        ``label_width`` 比让组件去猜宽度更可控。

        ``column`` 给字典时，档位在**构建时**按自身宽度选定。跨档换列数等于换一套
        行切分（结构变化），flet 1.1.2 对已挂载子树的结构补丁不保证上屏，所以
        运行期不重排 —— 要跟着窗口走，就把本组件建在组件里、在组件里
        ``use_responsive()``，档位变化时整页重渲染即可（见 RESPONSIVE 指南）。
    """

    items: list[DescriptionsItem | dict[str, Any]] = field(default_factory=list)
    column: int | dict[str, int] = 3
    direction: str = "horizontal"
    bordered: bool = True
    size: str = "default"
    title: str = ""
    extra: str | ft.Control | None = None
    colon: bool = True
    label_width: int = LABEL_W

    #: 用户给的原始 column（可能是个断点字典，解析后就地替换成 int 了）
    #:
    #: 这两个刻意**不带类型注解**：``@ft.control`` 会把注解变成 dataclass 字段，
    #: 而 flet 序列化时会遍历所有字段 —— 运行时状态一旦成为字段，就会随每次 patch
    #: 上线路（``_column_spec`` 里那个断点字典尤其没必要）。不带注解的类属性
    #: 不参与 dataclass，也就永远不会被序列化。
    _column_spec = None  # Any
    _cls = "expanded"

    def init(self):
        self._items: list[DescriptionsItem] = [_as_item(i) for i in self.items]
        self._pad_h, self._pad_v, self._font = _size_metrics(self.size)
        # 列数可以按断点给（``{"compact": 1, "medium": 2, "expanded": 3}``）：
        # 字段格子是"排出来的"，窄容器里三列会把标签和内容挤成两行。
        self._column_spec = self.column
        self._cls = size_class(viewport().width)
        self.column = int(resolve(self._column_spec, viewport().width))
        self.padding = 0

        # 列数（以及由此决定的"行切分"）在**构建期**定下来。
        #
        # 换列数是结构变化：一行的格子数与切分方式都变了。flet 1.1.2 对已挂载
        # 子树的替换补丁不保证上屏（换成新 Column、整列换新列表、甚至切
        # ``visible`` 都实测不生效），所以这里不去赌运行期能重排 —— 需要跟随窗口
        # 跨档的页面，把 Descriptions 建在组件里并在组件里 ``use_responsive()``，
        # 档位一变 flet 会重渲染整页（见 docs 的 RESPONSIVE 指南）。
        #
        # 连续变化（格子跟着拉伸）本来就交给渲染层，不需要这里做任何事。
        self._host = ft.Column(
            spacing=0,
            controls=[b for b in (self._header(), self._table()) if b is not None],
        )
        self.content = self._host

    # ------------------------------------------------------------------
    # 网格：把字段切成行，算出每格占几列
    # ------------------------------------------------------------------
    def _rows(self, columns: int | None = None) -> list[list[tuple[DescriptionsItem, int]]]:
        """按 ``span`` 把字段打包成行。

        规则只有两条：放不下就换行；末行没排满时**最后一项吃掉剩余列**。
        后者是"表"与"列表"的分界 —— 留着空格子，边框会像漏了一块。
        """
        total = max(1, self.column if columns is None else columns)
        rows: list[list[tuple[DescriptionsItem, int]]] = []
        row: list[tuple[DescriptionsItem, int]] = []
        used = 0

        for item in self._items:
            span = min(max(1, item.span), total)
            if row and used + span > total:  # 本行放不下 → 换行
                rows.append(row)
                row, used = [], 0
            row.append((item, span))
            used += span
            if used >= total:
                rows.append(row)
                row, used = [], 0

        if row:
            rows.append(row)

        if rows:
            used = sum(span for _, span in rows[-1])
            if used < total:
                item, span = rows[-1][-1]
                rows[-1][-1] = (item, span + total - used)
        return rows

    # ------------------------------------------------------------------
    # 组装
    # ------------------------------------------------------------------
    def _header(self) -> ft.Control | None:
        """标题 / 操作区。两者都没有就不占位。"""
        if not self.title and self.extra is None:
            return None
        left: ft.Control = (
            ft.Text(
                self.title,
                size=FONT_SIZE["body"],
                weight=ft.FontWeight.W_600,
                color=ft.Colors.ON_SURFACE,
            )
            if self.title
            else ft.Container()
        )
        right = self.extra
        if isinstance(right, str):
            right = ft.Text(right, size=self._font, color=MUTED)
        elif right is None:
            right = ft.Container()
        return ft.Container(
            padding=ft.Padding.only(bottom=10),
            content=ft.Row(
                controls=[left, ft.Container(expand=True), right],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def _table(self, columns: int | None = None) -> ft.Control:
        rows = self._rows(columns)
        if rows:
            last = len(rows) - 1
            cells: list[ft.Control] = []
            for index, row in enumerate(rows):
                tail = index == last
                if self.direction == "vertical":
                    cells.extend(self._vertical_row(row, last_row=tail))
                else:
                    cells.append(self._horizontal_row(row, last_row=tail))
            grid: ft.Control = ft.Column(spacing=0, controls=cells)
        else:
            # 没有字段时留一行占位：整块缩成 0 高，调用方会以为是没渲染出来。
            grid = empty_line(
                t("ui.common.empty"),
                height=None,
                size=self._font,
                padding=ft.Padding.symmetric(
                    horizontal=self._pad_h, vertical=self._pad_v * 2
                ),
            )
        if not self.bordered:
            return grid
        return ft.Container(
            bgcolor=SURFACE,
            border=ft.Border.all(LINE_W, LINE),
            border_radius=TABLE_RADIUS,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=grid,
        )

    def _horizontal_row(
        self, row: list[tuple[DescriptionsItem, int]], *, last_row: bool
    ) -> ft.Control:
        cells: list[ft.Control] = []
        for pos, (item, span) in enumerate(row):
            cells.append(
                self._horizontal_cell(
                    item, span, last_col=pos == len(row) - 1, last_row=last_row
                )
            )
        return ft.Row(
            spacing=0,
            # intrinsic_height + STRETCH：先按内容量出整行高度，再把每格拉满。
            # 少了 intrinsic_height，STRETCH 会在"父级高度无界"时断言失败
            # （整块直接不渲染，且不报 Python 异常 —— 极难查）。
            intrinsic_height=True,
            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=cells,
        )

    def _vertical_row(
        self, row: list[tuple[DescriptionsItem, int]], *, last_row: bool
    ) -> list[ft.Control]:
        """垂直方向：一行字段拆成"标签行 + 内容行"，两行的 ``span`` 完全一致，
        列线因此上下对齐。"""
        if not self.bordered:
            cells = [
                ft.Container(
                    expand=span,
                    padding=ft.Padding.only(
                        right=self._pad_h, top=self._pad_v, bottom=self._pad_v
                    ),
                    content=ft.Column(
                        spacing=4,
                        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                        controls=[self._label_content(item), self._value_content(item)],
                    ),
                )
                for item, span in row
            ]
            return [
                ft.Row(
                    spacing=0,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=cells,
                )
            ]

        labels: list[ft.Control] = []
        values: list[ft.Control] = []
        for pos, (item, span) in enumerate(row):
            last_col = pos == len(row) - 1
            labels.append(
                ft.Container(
                    expand=span,
                    padding=ft.Padding.symmetric(
                        horizontal=self._pad_h, vertical=max(2, self._pad_v - 2)
                    ),
                    bgcolor=LABEL_BG,
                    alignment=ft.Alignment.CENTER_LEFT,
                    border=self._edge(right=not last_col, bottom=True),
                    content=self._label_content(item),
                )
            )
            values.append(
                ft.Container(
                    expand=span,
                    padding=ft.Padding.symmetric(
                        horizontal=self._pad_h, vertical=self._pad_v
                    ),
                    alignment=ft.Alignment.CENTER_LEFT,
                    border=self._edge(right=not last_col, bottom=not last_row),
                    content=self._value_content(item),
                )
            )
        return [
            ft.Row(
                spacing=0,
                intrinsic_height=True,
                vertical_alignment=ft.CrossAxisAlignment.STRETCH,
                controls=labels,
            ),
            ft.Row(
                spacing=0,
                intrinsic_height=True,
                vertical_alignment=ft.CrossAxisAlignment.STRETCH,
                controls=values,
            ),
        ]

    def _horizontal_cell(
        self,
        item: DescriptionsItem,
        span: int,
        *,
        last_col: bool,
        last_row: bool,
    ) -> ft.Control:
        """横向的一格：标签固定宽 + 内容占满剩余，整格占 ``span`` 份宽度。

        ``label`` 留空（且没有 icon）时不画标签格 —— 否则 92px 的淡色空格白占
        一段宽度，还多竖一条分隔线，和文档里「只占内容位」的说法正好相反。
        """
        has_label = bool(item.label) or item.icon is not None
        if not self.bordered:
            cells: list[ft.Control] = []
            if has_label:
                cells.append(
                    ft.Container(
                        width=self.label_width,
                        padding=ft.Padding.only(
                            right=8, top=self._pad_v, bottom=self._pad_v
                        ),
                        alignment=ft.Alignment.TOP_LEFT,
                        content=self._label_content(item),
                    )
                )
            cells.append(
                ft.Container(
                    expand=True,
                    padding=ft.Padding.only(
                        right=self._pad_h, top=self._pad_v, bottom=self._pad_v
                    ),
                    content=self._value_content(item),
                )
            )
            return ft.Row(
                spacing=0,
                expand=span,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=cells,
            )
        if not has_label:
            return ft.Container(
                expand=span,
                padding=ft.Padding.symmetric(
                    horizontal=self._pad_h, vertical=self._pad_v
                ),
                alignment=ft.Alignment.CENTER_LEFT,
                border=self._edge(right=not last_col, bottom=not last_row),
                content=self._value_content(item),
            )
        return ft.Row(
            spacing=0,
            expand=span,
            intrinsic_height=True,
            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[
                ft.Container(
                    width=self.label_width,
                    padding=ft.Padding.symmetric(
                        horizontal=self._pad_h, vertical=self._pad_v
                    ),
                    bgcolor=LABEL_BG,
                    alignment=ft.Alignment.CENTER_LEFT,
                    border=self._edge(right=True, bottom=not last_row),
                    content=self._label_content(item),
                ),
                ft.Container(
                    expand=True,
                    padding=ft.Padding.symmetric(
                        horizontal=self._pad_h, vertical=self._pad_v
                    ),
                    alignment=ft.Alignment.CENTER_LEFT,
                    border=self._edge(right=not last_col, bottom=not last_row),
                    content=self._value_content(item),
                ),
            ],
        )

    # ------------------------------------------------------------------
    # 单元格内容
    # ------------------------------------------------------------------
    def _label_content(self, item: DescriptionsItem) -> ft.Control:
        text = ft.Text(
            _label_text(item.label, colon=self.colon and not self.bordered),
            size=self._font,
            weight=ft.FontWeight.W_500 if self.bordered else None,
            color=ft.Colors.ON_SURFACE if self.bordered else MUTED,
            no_wrap=True,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        if item.icon is None:
            return text
        return ft.Row(
            spacing=6,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(item.icon, size=self._font + 2, color=MUTED),
                text,
            ],
        )

    def _value_content(self, item: DescriptionsItem) -> ft.Control:
        value = item.value
        if isinstance(value, ft.Control):
            # 用 Row(tight=True) 兜一层：容器默认会把紧约束透给子控件，
            # 徽标 / 按钮这类"有自身尺寸"的控件会被拉满整格；Row 只让它们
            # 靠左排布，尺寸仍由控件自己决定（纵向排布时也一样）。
            return ft.Row(
                spacing=0,
                tight=True,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[value],
            )
        return ft.Text(
            "" if value is None else str(value),
            size=self._font,
            color=ft.Colors.ON_SURFACE,
        )

    def _edge(self, *, right: bool, bottom: bool) -> ft.Border:
        """只画右 / 下两条边，外框由外层容器负责 —— 永远不会出现双线。

        四种组合共享同一批 :class:`flet.Border` 值（见 :data:`_EDGES`）：
        ``ft.Border(...)`` 每建一个要验一遍颜色、再造 ``BorderSide``，实测 7µs ——
        与新建一个 :class:`flet.Container` 同价。一张 24 字段的表有 48 个格子，
        逐格新建就把 0.35ms 花在了"同一条灰线"上。
        """
        return _EDGES[(right, bottom)]

    # ------------------------------------------------------------------
    # 运行时更新
    # ------------------------------------------------------------------
    def set_items(self, items: list[DescriptionsItem | dict[str, Any]]) -> None:
        """替换字段列表并就地刷新。

        注意：这一条是**结构变化**，属于 flet 1.1.2 上不保证上屏的那一类
        （见 :meth:`init` 的说明）。数据模型一定会更新，界面在下次重建时跟上。
        """
        self.items = list(items)
        self._items = [_as_item(i) for i in self.items]
        try:
            self._host.controls[-1] = self._table()  # 表格永远在最后一格
            self._host.update()
        except Exception:  # noqa: BLE001, S110 - 尚未挂到页面时不需要刷新
            pass


# ---------------------------------------------------------------------------
# 小工具
# ---------------------------------------------------------------------------
def _as_item(raw: DescriptionsItem | dict[str, Any]) -> DescriptionsItem:
    if isinstance(raw, DescriptionsItem):
        return raw
    if isinstance(raw, (tuple, list)) and len(raw) == 2:
        return DescriptionsItem(str(raw[0]), raw[1])
    return DescriptionsItem(**raw)


def _label_text(label: str, *, colon: bool) -> str:
    if not colon or not label:
        return label
    return f"{label}:"


def _size_metrics(size: str) -> tuple[int, int, float]:
    key = _SIZE_ALIASES.get(size, size)
    return SIZES.get(key, SIZES["default"])


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
def _paid() -> ft.Control:
    """值可以是任意控件：图标与颜色由调用方定，格子只负责对齐与边框。"""
    return ft.Row(
        spacing=6,
        tight=True,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Icon(ft.Icons.CHECK_CIRCLE, size=14, color=semantic_text("success")),
            ft.Text("已支付", size=FONT_SIZE["body"]),
        ],
    )


@ft.component
def _basic() -> ft.Control:
    """两列键值：7 个字段排成 4 行，地址跨两列吃掉整行。"""
    return ft.Container(
        width=680,
        content=Descriptions(
            title="订单详情",
            extra="更新于 10:12",
            column=2,
            items=[
                DescriptionsItem("订单号", "SO-20261107-0142"),
                DescriptionsItem("状态", _paid()),
                DescriptionsItem("创建时间", "2026-11-07 10:12:03"),
                DescriptionsItem("金额", "¥1,280.00"),
                DescriptionsItem("支付方式", "微信支付 · 尾号 4021"),
                DescriptionsItem("收货人", "林一舟 · 138****6042"),
                DescriptionsItem(
                    "收货地址",
                    "江苏省苏州市吴中区吴中大道 1188 号 3 号楼 502",
                    span=2,
                ),
            ],
        ),
    )


@ft.component
def _narrow() -> ft.Control:
    """窄容器：左边单列横向（标签在左），右边单列纵向（标签在上）。"""
    return ft.Row(
        spacing=SPACE["4"],
        vertical_alignment=ft.CrossAxisAlignment.START,
        controls=[
            ft.Container(
                width=300,
                content=Descriptions(
                    title="会员卡",
                    column=1,
                    size="small",
                    items=[
                        DescriptionsItem("卡号", "6222 0210 0088 8102"),
                        DescriptionsItem("等级", "金卡 · 全场 8 折"),
                        DescriptionsItem("有效期", "2028-06-30"),
                        DescriptionsItem("积分", "12,480"),
                    ],
                ),
            ),
            ft.Container(
                width=300,
                content=Descriptions(
                    title="收货信息",
                    column=1,
                    size="small",
                    direction="vertical",
                    items=[
                        DescriptionsItem("收货人", "林一舟 138****6042"),
                        DescriptionsItem(
                            "地址",
                            "江苏省苏州市吴中区吴中大道 1188 号 3 号楼 502",
                        ),
                    ],
                ),
            ),
        ],
    )


@ft.component
def _blank() -> ft.Control:
    """空值用「—」占位；末行 label 留空，内容直接吃掉整行。"""
    return ft.Container(
        width=680,
        content=Descriptions(
            title="发票信息",
            column=2,
            size="small",
            items=[
                DescriptionsItem("发票类型", "—"),
                DescriptionsItem("抬头", "—"),
                DescriptionsItem("税号", "—"),
                DescriptionsItem("开户行", "—"),
                DescriptionsItem(
                    "",
                    "发票在付款后 24 小时内开出，可在「订单详情 → 发票」下载；"
                    "跨月订单需联系客服补开。",
                    span=2,
                ),
            ],
        ),
    )


# ---------------------------------------------------------------------------
# 示例源码（“查看代码”面板）
# ---------------------------------------------------------------------------
_BASIC_CODE = """Descriptions(
    title="订单详情",
    extra="更新于 10:12",                    # 字符串直接渲染成右上角说明
    column=2,
    items=[
        DescriptionsItem("订单号", "SO-20261107-0142"),
        DescriptionsItem("状态", Row([                     # 值可以是任意控件
            Icon(Icons.CHECK_CIRCLE, size=14), Text("已支付")], spacing=6)),
        DescriptionsItem("金额", "¥1,280.00"),
        DescriptionsItem("收货地址", "江苏省苏州市吴中区吴中大道 1188 号", span=2),
    ],
)"""

_NARROW_CODE = """# 窄容器：column=1，标签列仍是 92px，逐行对齐
Descriptions(
    column=1,
    size="small",
    items=[DescriptionsItem("卡号", "6222 0210 0088 8102")],
)

# 更窄的侧栏：标签挪到内容上方，省掉 92px 的标签列
Descriptions(column=1, direction="vertical", items=[...])"""

_BLANK_CODE = """# 空值不会自动变占位符：None 渲染成空串，要占位就显式传 "—"
Descriptions(column=2, items=[
    DescriptionsItem("税号", "—"),
    # label 留空 = 不画标签格，内容占满整行
    DescriptionsItem("", "发票在付款后 24 小时内开出。", span=2),
])"""


# ---------------------------------------------------------------------------
# 组件说明
# ---------------------------------------------------------------------------
SPEC = Spec(
    name="Descriptions",
    summary="把一条记录的字段摆成带边框的网格：键值成对、可跨列，像表但没有表头。",
    definition=(
        "描述列表回答的是「详情页里十几个字段怎么摆」。它按 column 把字段切成行，"
        "用固定宽度的标签列保证每一行对得齐，末行不足时最后一项自动吃掉剩余列宽 ——"
        "边框因此不会缺一块。它只负责排格子：值是字符串还是徽标、链接、按钮，"
        "都由调用方决定，组件不替内容做任何取舍。"
    ),
    anatomy=[
        (
            "标题 / 操作区",
            "title 在左上、extra 在右上（字符串自动转成说明文字）；两者都没有时整块不占位。",
        ),
        (
            "标签格",
            "淡底的固定宽格（label_width，默认 92px）。跨行对齐全靠它，过长收省略号。",
        ),
        (
            "内容格",
            "占满剩余宽度；字符串折行显示，传控件时按自身尺寸靠左，不被拉满整格。",
        ),
        (
            "跨列",
            "span 让一项占多列，长地址与备注用它；超过 column 会被夹到 column。",
        ),
        (
            "边框",
            "单元格只画右 / 下两条边，外框交给容器 —— 不会出现双线，也不怕差 1px。",
        ),
        (
            "空态",
            "没有字段时留一行「暂无数据」，整块不会缩成 0 高。",
        ),
    ],
    when=[
        "详情页的字段区：订单、用户、设备，一眼看完一条记录",
        "字段长短不一，需要标签逐行对齐（地址、备注要跨列）",
        "同一张表里既要文字，也要状态徽标或链接",
    ],
    avoid=[
        "字段少且都很短：用 Text 拼一行更省一层网格，也少一圈边框",
        "数据要排序、筛选、分页或勾选：用 Table，描述列表没有列头与行为",
        "每行字段数都不同、需要复杂合并：手写 Column / GridView 更直接",
    ],
    examples=[
        Example(
            "基础用法",
            _basic,
            hint="两列共 7 个字段；状态是控件，地址 span=2 吃掉整行。",
            code=_BASIC_CODE,
        ),
        Example(
            "窄容器",
            _narrow,
            hint="300px 宽的两块：左边单列横向、右边单列纵向，标签都不挤内容。",
            code=_NARROW_CODE,
        ),
        Example(
            "空值与无标签项",
            _blank,
            hint="缺的字段用「—」占位；最后一行 label 留空，说明文字占满整行。",
            code=_BLANK_CODE,
        ),
    ],
    api=[
        Api(
            "items",
            "list[DescriptionsItem | dict]",
            "[]",
            "字段列表；每项是 DescriptionsItem(label, value, span, icon)，也可传字典",
        ),
        Api(
            "column",
            "int | dict[str, int]",
            "3",
            "一行放几个字段；也可以按断点给（compact/medium/expanded），构建时按自身宽度选档",
        ),
        Api(
            "direction",
            "str",
            "'horizontal'",
            "horizontal 标签在左，vertical 标签在上",
        ),
        Api("bordered", "bool", "True", "边框与分隔线；嵌进已有卡片时关掉"),
        Api("size", "str", "'default'", "default / small，只改内边距与字号"),
        Api("title", "str", "''", "左上角标题；留空不占位"),
        Api(
            "extra",
            "str | Control | None",
            "None",
            "右上角操作区；传字符串时自动变成说明文字",
        ),
        Api("colon", "bool", "True", "无边框模式是否给标签补冒号"),
        Api(
            "label_width",
            "int",
            "92",
            "横向模式的标签列宽；换行时每行靠它对齐",
        ),
        Api(
            "set_items(items)",
            "Callable",
            "—",
            "就地替换字段并刷新（已挂载时生效）",
        ),
    ],
    notes=[
        tip(
            "某一项 label 留空时，横向模式不再保留 92px 的标签格，内容直接占满整格 ——"
            "这条跨列说明放进去不会多出一条分隔线。"
        ),
        warn(
            "label_width 是固定像素：容器窄到 400px 以下还开 column=3，标签与内容会互相"
            "挤压。减少 column、切 vertical，或调小 label_width，比让组件去猜宽度可控。"
        ),
        info(
            "没有字段时整块给一行「暂无数据」，不会缩成 0 高；但单个字段的空值不会被"
            "自动替换 —— value=None 渲染成空串，要占位就传「—」，组件分不清"
            "「还没填」和「本来就没有」。"
        ),
    ],
    tags=("描述列表", "详情", "字段", "descriptions", "键值"),
)


if __name__ == "__main__":
    run(SPEC)
