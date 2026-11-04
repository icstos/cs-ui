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

__all__ = ["Descriptions", "DescriptionsItem"]

# ---------------------------------------------------------------------------
# 视觉常量
# ---------------------------------------------------------------------------
LINE_W = 1
LINE: ft.ColorValue = ft.Colors.OUTLINE_VARIANT
LABEL_BG: ft.ColorValue = ft.Colors.SURFACE_CONTAINER_HIGH
SURFACE: ft.ColorValue = ft.Colors.SURFACE
MUTED: ft.ColorValue = ft.Colors.ON_SURFACE_VARIANT

RADIUS = 8
LABEL_W = 92  # 横向模式的标签列宽（固定像素，标签因此跨行对齐）

#: 尺寸档位 → (水平内边距, 垂直内边距, 字号)
SIZES: dict[str, tuple[int, int, float]] = {
    "default": (12, 8, 13.0),
    "small": (8, 5, 12.5),
}

#: 兼容 Element 的档位命名，避免迁移时踩空。
_SIZE_ALIASES = {"medium": "default", "large": "default", "mini": "small"}


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
        column: 一行放几个字段，默认 3。
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
    """

    items: list[DescriptionsItem | dict[str, Any]] = field(default_factory=list)
    column: int = 3
    direction: str = "horizontal"
    bordered: bool = True
    size: str = "default"
    title: str = ""
    extra: str | ft.Control | None = None
    colon: bool = True
    label_width: int = LABEL_W

    def init(self):
        self._items: list[DescriptionsItem] = [_as_item(i) for i in self.items]
        self._pad_h, self._pad_v, self._font = _size_metrics(self.size)
        self.padding = 0
        self.content = self._build()

    # ------------------------------------------------------------------
    # 网格：把字段切成行，算出每格占几列
    # ------------------------------------------------------------------
    def _rows(self) -> list[list[tuple[DescriptionsItem, int]]]:
        """按 ``span`` 把字段打包成行。

        规则只有两条：放不下就换行；末行没排满时**最后一项吃掉剩余列**。
        后者是"表"与"列表"的分界 —— 留着空格子，边框会像漏了一块。
        """
        total = max(1, self.column)
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
    def _build(self) -> ft.Control:
        blocks = [b for b in (self._header(), self._table()) if b is not None]
        if not blocks:
            return ft.Container()
        return ft.Column(spacing=0, controls=blocks)

    def _header(self) -> ft.Control | None:
        """标题 / 操作区。两者都没有就不占位。"""
        if not self.title and self.extra is None:
            return None
        left: ft.Control = (
            ft.Text(
                self.title,
                size=15,
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

    def _table(self) -> ft.Control | None:
        rows = self._rows()
        if not rows:
            return None
        last = len(rows) - 1
        cells: list[ft.Control] = []
        for index, row in enumerate(rows):
            tail = index == last
            if self.direction == "vertical":
                cells.extend(self._vertical_row(row, last_row=tail))
            else:
                cells.append(self._horizontal_row(row, last_row=tail))
        grid = ft.Column(spacing=0, controls=cells)
        if not self.bordered:
            return grid
        return ft.Container(
            bgcolor=SURFACE,
            border=ft.Border.all(LINE_W, LINE),
            border_radius=RADIUS,
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
        """横向的一格：标签固定宽 + 内容占满剩余，整格占 ``span`` 份宽度。"""
        if not self.bordered:
            return ft.Row(
                spacing=0,
                expand=span,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.Container(
                        width=self.label_width,
                        padding=ft.Padding.only(
                            right=8, top=self._pad_v, bottom=self._pad_v
                        ),
                        alignment=ft.Alignment.TOP_LEFT,
                        content=self._label_content(item),
                    ),
                    ft.Container(
                        expand=True,
                        padding=ft.Padding.only(
                            right=self._pad_h, top=self._pad_v, bottom=self._pad_v
                        ),
                        content=self._value_content(item),
                    ),
                ],
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
        """只画右 / 下两条边，外框由外层容器负责 —— 永远不会出现双线。"""
        return ft.Border(
            right=ft.BorderSide(LINE_W, LINE) if right else None,
            bottom=ft.BorderSide(LINE_W, LINE) if bottom else None,
        )

    # ------------------------------------------------------------------
    # 运行时更新
    # ------------------------------------------------------------------
    def set_items(self, items: list[DescriptionsItem | dict[str, Any]]) -> None:
        """替换字段列表并就地刷新（已挂载时生效；未挂载则只更新模型）。"""
        self.items = list(items)
        self._items = [_as_item(i) for i in self.items]
        try:
            self.content = self._build()
            self.update()
        except Exception:  # noqa: BLE001 - 尚未挂到页面时不需要刷新
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
