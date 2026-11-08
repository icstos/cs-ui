"""数据表格 (Table) —— 表头 + 斑马纹 + 分页，一行行比对结构化数据。

Table 在 ``ft.DataTable`` 外面补三件日常必需的东西：可选的「编号」列、按页切片、
底部的分页器。它**不解析数据** —— 列定义、对齐、单元格内容都由调用方传进来的
``DataTable`` 决定，Table 只负责把「当前这一页的行」拼出来。所以排序、格式化、
自定义单元格都能照常写在 ``DataTable`` 里。

表格按内容宽度排布：列窄时不会硬撑满卡片，列宽超出容器时整张表横向滚动，
表头跟着一起走 —— 表头与内容是同一个控件，不会错位。

.. note::
   **本组件经历过一次范式迁移。** 早期是 ``@ft.control`` 子类，在 ``set_page()``
   里调 ``self.update()`` 换页。但 demo 走的是 ``page.render(App)`` 根视图路径，
   flet 1.x 会把整棵树标记为 **frozen**，``update()`` 第一件事就查 ``_frozen``
   → ``RuntimeError: Frozen control cannot be updated.``（点击「下一页」必崩）。

   现在改为 ``@ft.component`` 函数组件：页码是 ``use_state``，行数据由页码**派生**，
   回调只改状态、不碰控件树。这才是声明式的正确姿势，也顺带解决了
   「状态改了但界面不重绘」这类问题。

用法::

    table = Table(data_table=my_datatable, rows_per_page=10, zebra=True)
    # 或先拿状态句柄（需要在外部读页码 / 换页时）：
    state = TableState(data_table=my_datatable, rows_per_page=10)
    table = Table(state=state)
"""

from __future__ import annotations

from dataclasses import dataclass, field

import flet as ft

from ui.core.doc import Api, Example, Spec, info, run, tip, warn
from ui.core.i18n import t, use_t
from ui.core.tokens import FONT_SIZE, FONT_WEIGHT, SPACE, overlay
from ui.navigation.pagination import Pagination, PaginationState

__all__ = ["Table", "TableState", "pandas_to_datatable"]

#: 悬停行底色（角色名 → 明暗自适应）
ROW_HOVER = ft.Colors.with_opacity(0.08, ft.Colors.PRIMARY)

#: 斑马纹底色：比悬停更轻，只用来分行、不抢内容
ROW_STRIPE = overlay(0.03)

#: 表头 / 网格线 / 外框 —— 全部用 M3 角色名，不再写死 M2 硬色
HEADING_ROW_COLOR = ft.Colors.SURFACE_CONTAINER_LOW
HORIZONTAL_LINE = ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)
TABLE_BORDER = ft.Border.all(1, ft.Colors.OUTLINE_VARIANT)

#: 「编号」列的兜底文案。真实文案走 ``ui.table.number``（英文是 ``#``），
#: 这里保留常量只为兼容老代码的 ``from ui.layout.table import NUMBER_COLUMN_LABEL``。
NUMBER_COLUMN_LABEL = "编号"

_MUTED = ft.Colors.ON_SURFACE_VARIANT


@ft.observable
@dataclass
class TableState:
    """表格的分页状态。

    抽出成独立对象有两个理由：

    1. 调用方能在组件外读页码、主动翻页（``@ft.component`` 的返回值拿不到内部 state）；
    2. 它是 ``@ft.observable`` 的，所以页码变化会**通知订阅者** —— 否则表格翻页了、
       旁边读着 ``state.current_page`` 的标题还停在旧值（这不是假设，是真机踩到过）。

    Args:
        data_table: 数据源。本组件会深拷贝一份，不改动传入对象。
        rows_per_page: 每页行数，默认 10。
        with_number: 是否自动补「编号」列，默认 True。
        with_paged: 是否启用分页，默认 True。
        current_page: 初始页码，默认 1。
        zebra: 是否给奇数行铺一层淡底，默认 False。
    """

    data_table: ft.DataTable
    rows_per_page: int = 10
    with_number: bool = True
    with_paged: bool = True
    current_page: int = 1
    zebra: bool = False

    #: 数据源引用。``init=False`` 因为它由 ``data_table`` 推导，不该被外部传。
    _source: ft.DataTable = field(init=False, repr=False)

    def __post_init__(self) -> None:
        # 曾经这里是 ``copy.deepcopy(self.data_table)``，理由是"build_rows 会插入
        # 编号列，别污染调用方的数据"。但这条理由不成立：``build_rows`` 里
        # ``cells = list(row.cells)`` 已经先复制了列表，``columns()`` 也是
        # ``list(self._source.columns)`` —— 插入只发生在**副本**上，数据源一个字节
        # 都没被改。而 ``Table`` 是组件，``_default_state`` 每次重绘都跑一遍，
        # 深拷贝于是变成了"每帧复制整张表"：实测 200×6 的表光这一行就要 15ms，
        # 行数越多样越慢（1000 行 ~75ms），翻页时整页都会卡一下。
        # 现在只留引用。若将来真要就地改数据源，请改那份副本，别改这里。
        self._source = self.data_table

    @property
    def num_rows(self) -> int:
        return len(self._source.rows)

    @property
    def num_pages(self) -> int:
        if self.rows_per_page <= 0:
            return 1
        pages, rest = divmod(self.num_rows, self.rows_per_page)
        return max(1, pages + (1 if rest else 0))

    def clamp_page(self, page: int) -> int:
        return page if 1 <= page <= self.num_pages else 1

    def page_slice(self, page: int) -> tuple[list[ft.DataRow], int]:
        """返回 (本页行, 本页首行的全局下标)。下标用于编号。"""
        rows = self._source.rows
        if not self.with_paged:
            return list(rows), 0
        start = (page - 1) * self.rows_per_page
        return list(rows[start : start + self.rows_per_page]), start

    def columns(self) -> list[ft.DataColumn]:
        """列定义；``with_number`` 时在最前面补一列「编号」。

        ``DataTable`` 要求至少有一列可见，所以连表头都没有时补一列占位 ——
        否则 ``Table(with_number=False)`` 传空数据会在构造 DataTable 时抛错。
        """
        cols = list(self._source.columns)
        if self.with_number:
            cols.insert(0, ft.DataColumn(label=ft.Text(t("ui.table.number"))))
        if not cols:
            cols.append(ft.DataColumn(label=ft.Text(t("ui.table.number"))))
        return cols

    def build_rows(self, page: int) -> list[ft.DataRow]:
        """按页码生成行。这是**纯函数** —— 同样的输入必得同样的输出。

        斑马纹按**全局行号**着色，翻页后条纹不会重新从第一行开始，否则同一个
        业务行在两页里一会儿有底、一会儿没底。
        """
        window, offset = self.page_slice(page)
        has_number = self.with_number and len(self._source.columns) >= 1
        rows: list[ft.DataRow] = []
        for idx, row in enumerate(window):
            cells = list(row.cells)
            if has_number:
                cells.insert(0, ft.DataCell(ft.Text(str(offset + idx + 1))))
            color: dict[ft.ControlState, ft.ColorValue] = {
                ft.ControlState.HOVERED: ROW_HOVER
            }
            if self.zebra and (offset + idx) % 2:
                color[ft.ControlState.DEFAULT] = ROW_STRIPE
            rows.append(ft.DataRow(cells=cells, color=color))
        return rows


def _default_state(
    data_table: ft.DataTable | None,
    rows_per_page: int,
    with_number: bool,
    with_paged: bool,
    zebra: bool,
) -> TableState:
    # ft.DataTable 的 columns 是必填位置参数，空表也给一列占位
    empty = ft.DataTable(columns=[ft.DataColumn(ft.Text(t("ui.table.number")))])
    return TableState(
        data_table=data_table if data_table is not None else empty,
        rows_per_page=rows_per_page,
        with_number=with_number,
        with_paged=with_paged,
        zebra=zebra,
    )


@ft.component
def Table(
    data_table: ft.DataTable | None = None,
    rows_per_page: int = 10,
    with_number: bool = True,
    with_paged: bool = True,
    zebra: bool = False,
    *,
    state: TableState | None = None,
    expand: bool = True,
) -> ft.Control:
    """数据表格。

    Args:
        data_table: 数据源。与 `state` 二选一；都不给则渲染空表。
        rows_per_page: 每页行数，默认 10。
        with_number: 是否自动补「编号」列，默认 True。
        with_paged: 是否启用分页，默认 True。
        zebra: 奇数行是否铺淡底，默认 False。
        state: 外部持有的状态句柄。需要「在组件外读页码 / 主动翻页」时用它。
        expand: 表格是否纵向撑满剩余空间，默认 True。

    Example:
        >>> Table(data_table=dt, rows_per_page=10)  # doctest: +SKIP
    """
    # 订阅语言：表头「编号 / #」与分页器文案都要跟着切
    use_t()
    table_state = state or _default_state(
        data_table, rows_per_page, with_number, with_paged, zebra
    )
    # 页码的真源是内部 state。`use_state` 的初值参数**每次渲染都会被求值**，
    # 所以绝不能让它跟着 external 漂移 —— 用 use_ref 把首次的值锁死。
    initial_page = ft.use_ref(table_state.current_page).current
    page, set_page = ft.use_state(initial_page)

    # 单向回写：内部页码 → 外部 state，供旁读 state.current_page 的组件更新。
    # ① 必须在 use_effect 里（渲染期写 observable 会立刻触发新一轮渲染）；
    # ② 只在真的不同值时写 —— 无条件写会让 observable 每次都发通知，
    #    而外部订阅者一重渲染就会带动本组件重建，形成"翻页自己往上跳"的循环。
    def _sync() -> None:
        if state is not None and state.current_page != page:
            state.current_page = page

    ft.use_effect(_sync, [page])

    def goto(new_page: int) -> None:
        target = table_state.clamp_page(int(new_page))
        if target != page:
            set_page(target)

    data_table_ctl = ft.DataTable(
        columns=table_state.columns(),
        rows=table_state.build_rows(page),
        heading_row_color=HEADING_ROW_COLOR,
        horizontal_lines=HORIZONTAL_LINE,
        border=TABLE_BORDER,
        expand=expand,
    )

    # 横向滚动：宽度交给内容算，列一多就横向滚，而不是撑破卡片被裁掉。
    # 外面包一层 Container 是必要的 —— DataTable 若直接挂在滚动 Row 下，
    # `expand` 会被当成 Expanded 塞进无界宽度，布局直接失败。
    table_card = ft.Card(
        ft.Container(
            content=ft.Row(
                scroll=ft.ScrollMode.AUTO,
                controls=[ft.Container(content=data_table_ctl)],
            ),
            bgcolor=ft.Colors.SURFACE,
            border=ft.Border.all(1, ft.Colors.OUTLINE),
        )
    )

    if not table_state.with_paged:
        return table_card

    pagination = Pagination(
        PaginationState(
            sum_data_nums=table_state.num_rows,
            data_per_page_nums=table_state.rows_per_page,
            current_page=page,
            on_change_page=goto,
        )
    )
    return ft.Card(
        content=ft.Container(
            content=ft.Column([table_card, pagination], scroll=ft.ScrollMode.AUTO),
            padding=ft.Padding.only(left=20, right=20, top=10, bottom=10),
            bgcolor=ft.Colors.SURFACE,
        ),
        elevation=2,
    )


def pandas_to_datatable(dataframe):
    """把 pandas DataFrame 转成 ``ft.DataTable``。"""
    dataframe.columns  # noqa: B018 - 触发属性访问以便未导入时早失败
    return ft.DataTable(
        columns=[ft.DataColumn(ft.Text(str(col))) for col in dataframe.columns],
        rows=[
            ft.DataRow(
                [
                    ft.DataCell(ft.Text(str(dataframe.at[index, col])))
                    for col in dataframe.columns
                ]
            )
            for index in dataframe.index
        ],
    )


# ---------------------------------------------------------------------------
# 示例零件
# ---------------------------------------------------------------------------
def _head(label: str, *, numeric: bool = False) -> ft.DataColumn:
    return ft.DataColumn(
        label=ft.Text(
            label,
            size=FONT_SIZE["small"],
            weight=FONT_WEIGHT["semibold"],
            color=_MUTED,
        ),
        numeric=numeric,
    )


def _table(
    headers: tuple[str, ...],
    rows: tuple[tuple[str, ...], ...],
    *,
    numeric: tuple[int, ...] = (),
) -> ft.DataTable:
    """按表头 + 元组数据拼一张 DataTable；``numeric`` 里的列右对齐。"""
    return ft.DataTable(
        columns=[
            _head(name, numeric=index in numeric) for index, name in enumerate(headers)
        ],
        rows=[
            ft.DataRow(
                cells=[
                    ft.DataCell(
                        ft.Text(
                            value,
                            size=FONT_SIZE["body"],
                            text_align=ft.TextAlign.RIGHT
                            if index in numeric
                            else ft.TextAlign.LEFT,
                        )
                    )
                    for index, value in enumerate(values)
                ]
            )
            for values in rows
        ],
    )


#: 订单表：(订单号, 客户, 金额, 状态, 下单时间)
_ORDERS: tuple[tuple[str, ...], ...] = (
    ("SO-24815", "杭州云栖科技", "¥ 12,480.00", "已发货", "11-06 14:32"),
    ("SO-24814", "上海砺行贸易", "¥ 3,260.00", "待付款", "11-06 14:08"),
    ("SO-24813", "成都青棠文化", "¥ 18,900.00", "已签收", "11-06 13:47"),
    ("SO-24812", "深圳前海智造", "¥ 6,720.00", "已发货", "11-06 11:25"),
    ("SO-24811", "北京同衡设计", "¥ 2,180.00", "已退款", "11-06 10:56"),
    ("SO-24810", "武汉江岸物流", "¥ 9,450.00", "已签收", "11-06 10:12"),
    ("SO-24809", "南京雨花软件", "¥ 27,600.00", "待发货", "11-06 09:38"),
    ("SO-24808", "广州南沙电子", "¥ 4,980.00", "已发货", "11-06 09:05"),
)

#: 渠道表：(渠道, 曝光, 点击, 点击率, 转化, 收入)
_CHANNELS: tuple[tuple[str, ...], ...] = (
    ("自然搜索", "128,400", "9,860", "7.68%", "412", "¥ 186,240"),
    ("信息流", "96,300", "4,120", "4.28%", "186", "¥ 92,480"),
    ("应用商店", "54,200", "3,650", "6.73%", "204", "¥ 71,300"),
    ("老客复购", "31,800", "2,940", "9.25%", "238", "¥ 118,760"),
    ("联盟推广", "44,600", "1,780", "3.99%", "96", "¥ 38,920"),
    ("社交媒体", "72,100", "2,260", "3.13%", "84", "¥ 26,470"),
    ("邮件唤醒", "18,400", "1,320", "7.17%", "72", "¥ 31,880"),
    ("消息推送", "26,900", "1,540", "5.72%", "88", "¥ 34,600"),
    ("短视频", "88,700", "5,420", "6.11%", "246", "¥ 104,520"),
    ("线下扫码", "12,600", "980", "7.78%", "64", "¥ 22,140"),
)

#: 宽表：10 列，用来演示横向滚动
_WIDE_HEADERS: tuple[str, ...] = (
    "订单号",
    "客户",
    "产品线",
    "区域",
    "数量",
    "单价",
    "金额",
    "状态",
    "下单时间",
    "负责人",
)

_WIDE_ROWS: tuple[tuple[str, ...], ...] = (
    (
        "SO-24815",
        "杭州云栖科技",
        "企业版",
        "华东",
        "48",
        "260.00",
        "12,480.00",
        "已发货",
        "11-06 14:32",
        "周航",
    ),
    (
        "SO-24814",
        "上海砺行贸易",
        "标准版",
        "华东",
        "20",
        "163.00",
        "3,260.00",
        "待付款",
        "11-06 14:08",
        "林一舟",
    ),
    (
        "SO-24813",
        "成都青棠文化",
        "企业版",
        "西南",
        "70",
        "270.00",
        "18,900.00",
        "已签收",
        "11-06 13:47",
        "杨帆",
    ),
    (
        "SO-24812",
        "深圳前海智造",
        "专业版",
        "华南",
        "24",
        "280.00",
        "6,720.00",
        "已发货",
        "11-06 11:25",
        "陈可",
    ),
    (
        "SO-24811",
        "北京同衡设计",
        "标准版",
        "华北",
        "10",
        "218.00",
        "2,180.00",
        "已退款",
        "11-06 10:56",
        "王砚",
    ),
    (
        "SO-24810",
        "武汉江岸物流",
        "专业版",
        "华中",
        "35",
        "270.00",
        "9,450.00",
        "已签收",
        "11-06 10:12",
        "刘沐",
    ),
    (
        "SO-24809",
        "南京雨花软件",
        "企业版",
        "华东",
        "92",
        "300.00",
        "27,600.00",
        "待发货",
        "11-06 09:38",
        "赵思远",
    ),
    (
        "SO-24808",
        "广州南沙电子",
        "标准版",
        "华南",
        "30",
        "166.00",
        "4,980.00",
        "已发货",
        "11-06 09:05",
        "孙泊",
    ),
    (
        "SO-24807",
        "西安高新材料",
        "专业版",
        "西北",
        "18",
        "255.00",
        "4,590.00",
        "待发货",
        "11-05 17:42",
        "周航",
    ),
    (
        "SO-24806",
        "青岛港湾食品",
        "标准版",
        "华北",
        "26",
        "148.00",
        "3,848.00",
        "已签收",
        "11-05 16:20",
        "林一舟",
    ),
    (
        "SO-24805",
        "长沙麓谷传媒",
        "企业版",
        "华中",
        "55",
        "310.00",
        "17,050.00",
        "待付款",
        "11-05 15:04",
        "杨帆",
    ),
    (
        "SO-24804",
        "厦门环岛旅游",
        "专业版",
        "华南",
        "12",
        "265.00",
        "3,180.00",
        "已发货",
        "11-05 14:36",
        "陈可",
    ),
)

_ORDER_HEADERS: tuple[str, ...] = ("订单号", "客户", "金额", "状态", "下单时间")


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
@ft.component
def _basic() -> ft.Control:
    """5 列订单表、每页 5 行；编号与分页都是 Table 自己补的。"""
    return Table(
        data_table=_table(_ORDER_HEADERS, _ORDERS, numeric=(2,)),
        rows_per_page=5,
    )


@ft.component
def _zebra() -> ft.Control:
    """数字列右对齐 + 斑马纹；10 行分两页，条纹按全局行号算。"""
    return Table(
        data_table=_table(
            ("渠道", "曝光", "点击", "点击率", "转化", "收入"),
            _CHANNELS,
            numeric=(1, 2, 3, 4, 5),
        ),
        rows_per_page=5,
        zebra=True,
    )


@ft.component
def _wide() -> ft.Control:
    """10 列宽表：按内容排布，超出卡片宽度时整张表横向滚动。"""
    return Table(
        data_table=_table(
            _WIDE_HEADERS,
            _WIDE_ROWS,
            numeric=(4, 5, 6),
        ),
        rows_per_page=5,
        with_number=False,
    )


@ft.component
def _empty() -> ft.Control:
    """0 行：表头与「共 0 项」照常出现，空态文案由调用方补。"""
    return ft.Column(
        spacing=SPACE["2"],
        controls=[
            Table(data_table=_table(_ORDER_HEADERS, ()), rows_per_page=5),
            ft.Text(
                "还没有订单，新的订单会出现在这里。",
                size=FONT_SIZE["small"],
                color=_MUTED,
            ),
        ],
    )


_BASIC_CODE = """dt = DataTable(
    columns=[
        DataColumn(Text("订单号")),
        DataColumn(Text("金额"), numeric=True),   # 表头与单元格一起右对齐
        DataColumn(Text("状态")),
    ],
    rows=[
        DataRow([DataCell(Text(o.no)), DataCell(Text(o.amount)), DataCell(Text(o.state))])
        for o in orders
    ],
)

Table(data_table=dt, rows_per_page=10, zebra=True)"""


SPEC = Spec(
    name="Table",
    summary="表头、斑马纹与分页打包好的数据表格：列对齐、行悬停、宽表横向滚动。",
    definition=(
        "Table 是「逐行逐列比对」的默认选择：它把 flet 的 DataTable 按页切开，"
        "补上连号的「编号」列和底部分页器，并给每一行加悬停底色。数据仍然是调用方"
        "手里的 DataTable —— 列宽、排序、数字对齐、单元格里放什么，全由那份定义决定；"
        "Table 只保证「这一页该显示哪几行」，不碰业务数据。"
    ),
    anatomy=[
        (
            "表头",
            "来自 DataTable.columns，底色 SURFACE_CONTAINER_LOW；numeric=True 的列连同表头一起右对齐。",
        ),
        (
            "编号列",
            "with_number=True 时插在最前，跨页连续（第 2 页从 6 开始），不写回源数据。",
        ),
        (
            "数据行",
            "按 rows_per_page 切片；悬停叠 8% 主色，斑马纹是 3% 的 on_surface，条纹不会盖住悬停。",
        ),
        (
            "横向滚动",
            (
                "列宽取表头与单元格里较宽的那个（DataTable 没有固定列宽参数），列多时横向滚动；"
                "表头与数据在同一个滚动区，不会错位。"
            ),
        ),
        (
            "分页器",
            "复用 Pagination：总条数取源表行数，切页只换行，不重新请求数据。",
        ),
    ],
    when=[
        "结构化数据要逐行比对：订单、账单、指标明细",
        "列数固定、需要表头说明每一列的含义",
        "行数超过一屏，但用户要能定位到「第几页」",
    ],
    avoid=[
        "只有一两列的简单列表：ListTile / ListView 更轻，也不会有横向滚动",
        "每项形态差异很大（大图、长文、整块操作区）：用卡片流，DataTable 会强行对齐网格",
        "需要就地编辑、列冻结、分组折叠：DataTable 不支持，换 flet-datatable2 或自绘",
    ],
    examples=[
        Example(
            "基础表格",
            _basic,
            hint="5 列订单、每页 5 行；编号与分页由 Table 补上，金额列右对齐。",
            code=_BASIC_CODE,
            padded=False,
            height=380,
        ),
        Example(
            "斑马纹与数字对齐",
            _zebra,
            hint="numeric=True 让表头和数据一起右对齐；斑马纹按全局行号着色，翻页后不会从第一行重来。",
            padded=False,
            height=380,
        ),
        Example(
            "宽表横向滚动",
            _wide,
            hint="10 列、去掉编号列：表格保持内容宽度，超出部分横向滚动，表头跟着走。",
            padded=False,
            height=380,
        ),
        Example(
            "空表",
            _empty,
            hint="0 行时只留表头与「共 0 项」；「暂无订单」这类文案由调用方在 Table 外补。",
            padded=False,
            height=240,
        ),
    ],
    api=[
        Api("data_table", "DataTable", "", "数据源；与 state 二选一，都不给则渲染空表"),
        Api("rows_per_page", "int", "10", "每页行数；决定分页器的总页数"),
        Api("with_number", "bool", "True", "是否在最前面自动补「编号」列"),
        Api("with_paged", "bool", "True", "关掉后一次性渲染全部行，不出现分页器"),
        Api("zebra", "bool", "False", "奇数行铺一层淡底，便于横向读长行"),
        Api(
            "state",
            "TableState | None",
            "None",
            "外部状态句柄；要在组件外读页码 / 翻页时用",
        ),
        Api("expand", "bool", "True", "表格是否纵向撑满剩余空间（父级有界时生效）"),
        Api(
            "current_page",
            "int",
            "1",
            "TableState 的初始页码，1 起；越界会被夹回第 1 页",
        ),
    ],
    notes=[
        info(
            "表格不再给 DataTable 写死宽度，改成按内容排布 + 横向滚动：写死 10000 会把"
            "窄表撑出大片空白，宽表又被卡片裁掉，两种情况都读不下去。"
        ),
        tip(
            "斑马纹按全局行号着色，不是按当前页的第几行 —— 否则同一张订单在第 1 页"
            "有底、翻到第 2 页就没了。颜色走 3% 的 on_surface 叠加，明暗主题都成立。"
        ),
        warn(
            "空表只保留表头与「共 0 项」，组件不猜业务文案。要插画或「暂无订单」提示，"
            "在 Table 外面自己加一段 —— 见「空表」示例。"
        ),
    ],
    tags=("表格", "table", "datatable", "斑马纹", "分页", "数据"),
)


if __name__ == "__main__":
    run(SPEC)
