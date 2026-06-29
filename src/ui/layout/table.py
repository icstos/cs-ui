"""10
Table:
"""

import flet as ft
import copy
import random
from ui.layout import page
from ui.navigation.paging import Paging, PagingState


@ft.control
class Table(ft.Column):
    DEFAULT_ROW_PER_PAGE: int = 10  # 默认每页行数
    data_table: ft.DataTable | None = None  # 输入的 DataTable 对象
    rows_per_page: int = DEFAULT_ROW_PER_PAGE  # 每页显示的行数
    with_paged: bool = True  # 是否启用分页
    init_width: int | None = None  # 初始宽度
    with_number: bool = True  # 是否显示编号列

    def init(self):
        # 深拷贝输入的 DataTable，避免外部数据被修改
        self.input_data_table = copy.deepcopy(self.data_table)
        self.init_data_per_page_nums = self.rows_per_page
        self.current_page = 1

        # 分页控件的边距
        self.paged_padding_left = 20
        self.paged_padding_right = 20
        self.paged_padding_top = 10
        self.paged_padding_bottom = 10
        self.paging_state = PagingState(
            sum_data_nums=self.num_rows, on_change_page=self.set_page
        )
        self.v_paging = Paging(self.paging_state)
        # sum_data_nums=self.num_rows,
        # on_change_page=self.set_page,
        # on_row_per_page_change=self,
        # )

        self.v_data_table = ft.DataTable(
            columns=self.input_data_table.columns,
            rows=self.build_rows(),
            heading_row_color="#f4f4f4",
            sort_column_index=2,
            horizontal_lines=ft.BorderSide(1, "#EDEEF4"),
            border=ft.Border.all(1, "#eeeeee"),
            expand=self.expand,
            width=10000,
        )

        self.v_row_table = ft.Card(
            ft.Container(
                content=self.v_data_table,
                bgcolor=ft.Colors.WHITE,
                border=ft.Border.all(1, ft.Colors.GREY_400),
            )
        )

        if self.with_paged:
            self.ui_view = ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [self.v_row_table, self.v_paging], scroll=ft.ScrollMode.AUTO
                    ),
                    padding=ft.Padding.only(
                        left=self.paged_padding_left,
                        right=self.paged_padding_right,
                        top=self.paged_padding_top,
                        bottom=self.paged_padding_bottom,
                    ),
                    bgcolor=ft.Colors.WHITE,
                ),
                elevation=2,
            )
        else:
            self.ui_view = self.v_row_table

        self.controls = [self.ui_view]

    @property
    def data_per_page_nums(self) -> int:
        return self.paging_state.data_per_page_nums

    @property
    def num_rows(self) -> int:
        return len(self.input_data_table.rows)

    @property
    def num_pages(self) -> int:
        return self.paging_state.sum_page_nums

    @property
    def data_columns(self):
        return self.v_data_table.columns

    @property
    def data_rows(self):
        return self.input_data_table.rows

    def update_data_table(self, data_table=None):

        if data_table is not None:
            self.input_data_table = data_table
        self.v_data_table.columns = self.input_data_table.columns

        if (
            self.with_number
            and len(self.v_data_table.columns) >= 1
            and self.v_data_table.columns[0].label.value != "编号"
        ):
            self.v_data_table.columns.insert(0, ft.DataColumn(label=ft.Text("编号")))
        self.v_data_table.rows = self.build_rows()

    def set_page(self, page: str | int | None = None, delta: int = 0):

        if page is not None:
            try:
                page_int = int(page)
                self.current_page = page_int if 1 <= page_int <= self.num_pages else 1
            except ValueError:
                self.current_page = 1
        elif delta:
            self.current_page += delta
        else:
            return
        self.v_data_table.rows = self.build_rows()
        # TODO: bad design: need add TableState
        self.update()

    def build_rows(self) -> list:

        if self.with_paged:
            index_start = (self.current_page - 1) * self.data_per_page_nums
            index_end = self.current_page * self.data_per_page_nums
        else:
            index_start = 0
            index_end = -1

        rst_rows = []
        # 遍历当前页的数据行
        for idx, row in enumerate(
            self.input_data_table.rows[slice(index_start, index_end)]
        ):
            # 自动补充编号列
            if self.with_number and (
                len(row.cells) < len(self.input_data_table.columns)
            ):
                row.cells.insert(0, ft.DataCell(ft.Text(index_start + idx + 1)))
            # 设置悬浮颜色
            row.color = {
                ft.ControlState.HOVERED: ft.Colors.with_opacity(0.1, ft.Colors.BLUE)
            }
            # 行选中事件（可自定义）
            row.on_select_changed = lambda e: e
            rst_rows.append(row)
        return rst_rows

    # def refresh_data(self):
    #     self.v_paging.update_sum_data_nums(value=self.num_rows)

    def did_mount(self):
        self.update_data_table(self.input_data_table)


def pandas_to_datatable(dataframe):
    import pandas as pd

    dataframe: pd.DataFrame
    datatable = ft.DataTable(
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
    return datatable


@ft.component
def App():
    page = ft.context.page
    page.scroll = ft.ScrollMode.AUTO
    rows = []
    for i in range(200):
        rows.append(
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text("John")),
                    ft.DataCell(ft.Text("Smith")),
                    ft.DataCell(ft.Text(str(random.random()))),
                ]
            )
        )
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
