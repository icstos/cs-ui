"""Table 数据表格。

封装 ``ft.DataTable`` + 分页器，自动补「编号」列并给行加悬停色。

.. note::
   **本组件经历过一次范式迁移。** 早期是 ``@ft.control`` 子类，在 ``set_page()``
   里调 ``self.update()`` 换页。但 demo 走的是 ``page.render(App)`` 根视图路径，
   flet 1.0.4 会把整棵树标记为 **frozen**，``update()`` 第一件事就查 ``_frozen``
   → ``RuntimeError: Frozen control cannot be updated.``（点击「下一页」必崩）。

   现在改为 ``@ft.component`` 函数组件：页码是 ``use_state``，行数据由页码**派生**，
   回调只改状态、不碰控件树。这才是声明式的正确姿势，也顺带解决了
   「状态改了但界面不重绘」这类问题。

用法::

    table = Table(data_table=my_datatable, rows_per_page=10)
    # 或先拿状态句柄（需要在外部读页码 / 换页时）：
    state = TableState(data_table=my_datatable, rows_per_page=10)
    table = Table(state=state)
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field

import flet as ft

from ui.navigation.paging import Paging, PagingState

__all__ = ["Table", "TableState", "pandas_to_datatable"]

#: 悬停行底色（角色名 → 明暗自适应）
ROW_HOVER = ft.Colors.with_opacity(0.08, ft.Colors.PRIMARY)

#: 表头 / 网格线 / 外框 —— 全部用 M3 角色名，不再写死 M2 硬色
HEADING_ROW_COLOR = ft.Colors.SURFACE_CONTAINER_LOW
HORIZONTAL_LINE = ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)
TABLE_BORDER = ft.Border.all(1, ft.Colors.OUTLINE_VARIANT)

NUMBER_COLUMN_LABEL = "编号"


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
    """

    data_table: ft.DataTable
    rows_per_page: int = 10
    with_number: bool = True
    with_paged: bool = True
    current_page: int = 1

    #: 深拷贝后的数据源。`init=False` 因为它由 `data_table` 推导，不该被外部传。
    _source: ft.DataTable = field(init=False, repr=False)

    def __post_init__(self) -> None:
        # 深拷贝：build_rows 会插入编号列，不能污染调用方的数据
        self._source = copy.deepcopy(self.data_table)

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
        """列定义；``with_number`` 时在最前面补一列「编号」。"""
        cols = list(self._source.columns)
        if self.with_number:
            cols.insert(0, ft.DataColumn(label=ft.Text(NUMBER_COLUMN_LABEL)))
        return cols

    def build_rows(self, page: int) -> list[ft.DataRow]:
        """按页码生成行。这是**纯函数** —— 同样的输入必得同样的输出。"""
        window, offset = self.page_slice(page)
        has_number = self.with_number and len(self._source.columns) >= 1
        rows: list[ft.DataRow] = []
        for idx, row in enumerate(window):
            cells = list(row.cells)
            if has_number:
                cells.insert(0, ft.DataCell(ft.Text(str(offset + idx + 1))))
            rows.append(
                ft.DataRow(
                    cells=cells,
                    color={ft.ControlState.HOVERED: ROW_HOVER},
                )
            )
        return rows


def _default_state(
    data_table: ft.DataTable | None,
    rows_per_page: int,
    with_number: bool,
    with_paged: bool,
) -> TableState:
    # ft.DataTable 的 columns 是必填位置参数，空表也给一列占位
    empty = ft.DataTable(columns=[ft.DataColumn(ft.Text(NUMBER_COLUMN_LABEL))])
    return TableState(
        data_table=data_table if data_table is not None else empty,
        rows_per_page=rows_per_page,
        with_number=with_number,
        with_paged=with_paged,
    )


@ft.component
def Table(
    data_table: ft.DataTable | None = None,
    rows_per_page: int = 10,
    with_number: bool = True,
    with_paged: bool = True,
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
        state: 外部持有的状态句柄。需要「在组件外读页码 / 主动翻页」时用它。
        expand: 表格是否纵向撑满剩余空间，默认 True。

    Example:
        >>> Table(data_table=dt, rows_per_page=10)  # doctest: +SKIP
    """
    table_state = state or _default_state(
        data_table, rows_per_page, with_number, with_paged
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
        width=10000,
    )

    table_card = ft.Card(
        ft.Container(
            content=data_table_ctl,
            bgcolor=ft.Colors.SURFACE,
            border=ft.Border.all(1, ft.Colors.OUTLINE),
        )
    )

    if not table_state.with_paged:
        return table_card

    paging = Paging(
        PagingState(
            sum_data_nums=table_state.num_rows,
            data_per_page_nums=table_state.rows_per_page,
            current_page=page,
            on_change_page=goto,
        )
    )
    return ft.Card(
        content=ft.Container(
            content=ft.Column([table_card, paging], scroll=ft.ScrollMode.AUTO),
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


@ft.component
def App():
    """演示 / 审计入口。"""
    import random

    rows = [
        ft.DataRow(
            cells=[
                ft.DataCell(ft.Text("John")),
                ft.DataCell(ft.Text("Smith")),
                ft.DataCell(ft.Text(str(random.random()))),
            ]
        )
        for _ in range(200)
    ]
    data_table = ft.DataTable(
        columns=[
            ft.DataColumn(label=ft.Text("First name")),
            ft.DataColumn(label=ft.Text("Last name")),
            ft.DataColumn(label=ft.Text("Age"), numeric=True),
        ],
        rows=rows,
    )
    print(f"Table: {len(data_table.rows)}")
    return ft.Column([Table(data_table=data_table, rows_per_page=10, with_paged=True)])


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
