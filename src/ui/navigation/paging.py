from dataclasses import field

import flet as ft
from collections.abc import Callable
from enum import Enum


class BorderRadiusSize(Enum):
    # https://fluent2.microsoft.design/shapes
    NONE = 0
    S = 2
    M = 4
    L = 8
    X = 12


ICON_WIDTH = 36
ICON_HEIGHT = 32
ICON_DEFAULT_COLOR = ft.Colors.BLUE
ICON_HOVER_COLOR = ft.Colors.BLUE_100


@ft.control
class NowPageButton(ft.Button):
    width: int = ICON_WIDTH
    height: int = ICON_HEIGHT
    style: ft.ButtonStyle = field(
        default_factory=lambda: ft.ButtonStyle(
            color=ft.Colors.BLUE_800,
            bgcolor={ft.ControlState.DEFAULT: ft.Colors.BLUE_100},
            side={ft.ControlState.HOVERED: ft.BorderSide(1, ft.Colors.BLUE)},
            shape=ft.RoundedRectangleBorder(radius=BorderRadiusSize.M.value),
            elevation=0,
            padding=0,
        )
    )


@ft.control
class OtherPageButton(ft.Button):
    width: int = ICON_WIDTH
    height: int = ICON_HEIGHT
    style: ft.ButtonStyle = field(
        default_factory=lambda: ft.ButtonStyle(
            color={ft.ControlState.DEFAULT: ft.Colors.BLACK},
            bgcolor=ft.Colors.WHITE,
            side={ft.ControlState.HOVERED: ft.BorderSide(1, ft.Colors.BLUE)},
            shape=ft.RoundedRectangleBorder(radius=BorderRadiusSize.M.value),
            elevation=0,
            padding=0,
        )
    )


@ft.control
class PrevNextPageButton(ft.IconButton):
    icon_size: int = 20
    width: int = ICON_WIDTH
    height: int = ICON_HEIGHT
    style: ft.ButtonStyle = field(
        default_factory=lambda: ft.ButtonStyle(
            color={
                ft.ControlState.DEFAULT: ft.Colors.BLUE,
                ft.ControlState.HOVERED: ft.Colors.BLUE,
            },
            bgcolor={ft.ControlState.HOVERED: ft.Colors.WHITE},
            side={ft.ControlState.HOVERED: ft.BorderSide(1, ft.Colors.BLUE_300)},
            shape=ft.RoundedRectangleBorder(radius=BorderRadiusSize.M.value),
            padding=0,
        )
    )


def get_center_page_list(current_page: int, sum_page_nums: int) -> list:
    """
    根据当前页码和总页数生成分页按钮的页码列表。
    - 页数少于等于6时，全部显示。
    - 页数较多时，显示部分页码和省略号（-1 代表省略号）。
    """
    match (sum_page_nums, current_page):
        case (s, _) if s <= 6:
            return list(range(1, s + 1))
        case (s, c) if c < 5:
            return list(range(1, 6)) + [-1, s]
        case (s, c) if s - 5 < c <= s:
            return [1, -1] + list(range(s - 4, s + 1))
        case (s, c):
            return [1, -1] + list(range(c - 2, c + 3)) + [-1, s]


@ft.control
class Paging(ft.Row):
    sum_data_nums: int = 0  # 总数据条数
    on_change_page: Callable[[int], None] | None = None  # 页码变更回调
    on_change_per_page_nums: Callable[[int], None] | None = None  # 每页数据条数变更回调
    data_per_page_nums: int = 10  # 每页数据条数
    current_page: int = 1  # 当前页码
    data_unit: str = '项'  # 数据单位
    alignment: ft.MainAxisAlignment = ft.MainAxisAlignment.SPACE_BETWEEN
    expand: bool = True

    def init(self):
        self.v_count = ft.Text(value=f'共 {self.sum_data_nums} {self.data_unit}')
        self.v_now_page = ft.Row()
        self.v_goto_page = ft.TextField(
            on_submit=self.handle_goto_page_submit,
            width=40,
            height=32,
            text_align=ft.TextAlign.CENTER,
            content_padding=0,
            border_color=ft.Colors.GREY_300,
        )
        self.v_num_of_row_changer_field = ft.Dropdown(
            options=[ft.DropdownOption(_) for _ in [5, 10, 15, 20, 30, 40, 50]],
            value=str(self.data_per_page_nums),
            width=88,
            dense=True,
            content_padding=0,
            border_color=ft.Colors.GREY_300,
            scale=0.9,
            on_select=self.handle_change_per_page_nums,
        )
        self.controls = [
            self.v_count,
            ft.Row(
                controls=[
                    self.v_now_page,
                    ft.Text('前往'),
                    self.v_goto_page,
                    ft.Text('页'),
                ],
                spacing=6,
            ),
            ft.Row(
                controls=[
                    ft.Text('每页'),
                    self.v_num_of_row_changer_field,
                    ft.Text(self.data_unit),
                ]
            ),
        ]
        self._update()

    @property
    def sum_page_nums(self) -> int:
        num_page, num_page_over = divmod(self.sum_data_nums, self.data_per_page_nums)
        return num_page + (1 if num_page_over else 0)

    def handle_change_per_page_nums(self, e):
        self.data_per_page_nums = int(e.control.value)
        self.current_page = 1  # 切换每页条数时回到首页
        self._update()
        if self.on_change_page:
            self.on_change_page(self.current_page)
        if self.on_change_per_page_nums:
            self.on_change_per_page_nums(self.data_per_page_nums)

    def handle_update(self):
        self.v_count.value = f'共 {self.sum_data_nums} {self.data_unit}'
        self._update()

    def update_sum_data_nums(self, value: int):
        self.sum_data_nums = value
        self.handle_update()

    def handle_goto_page_submit(self, e):
        try:
            page = int(e.control.value)
            if 1 <= page <= self.sum_page_nums:
                self.current_page = page
                if self.on_change_page:
                    self.on_change_page(self.current_page)
                self._update()
        except Exception:
            pass  # 非法输入忽略

    def _update(self):
        rst_control_list = []
        first_page_btn = PrevNextPageButton(
            icon=ft.Icons.KEYBOARD_DOUBLE_ARROW_LEFT,
            on_click=self.click_update_page,
            tooltip='首页',
            data=1,
            disabled=(self.current_page == 1),
            icon_color=ft.Colors.GREY if (self.current_page == 1) else None,
        )
        rst_control_list.append(first_page_btn)
        prev_page_btn = PrevNextPageButton(
            icon=ft.Icons.KEYBOARD_ARROW_LEFT,
            on_click=self.click_update_page,
            tooltip='上一页',
            data=self.current_page - 1,
            disabled=(self.current_page == 1),
            icon_color=ft.Colors.GREY if (self.current_page == 1) else None,
        )
        rst_control_list.append(prev_page_btn)

        for _page in get_center_page_list(self.current_page, self.sum_page_nums):
            if _page == -1:
                rst_control_list.append(ft.Text('...'))
            elif _page == self.current_page:
                # 当前页
                rst_control_list.append(
                    NowPageButton(
                        content=str(_page),
                        on_click=self.click_update_page,
                        tooltip=f'第 {_page} 页',
                        data=_page,
                    )
                )

            else:
                # 其他页
                rst_control_list.append(
                    OtherPageButton(
                        content=str(_page),
                        on_click=self.click_update_page,
                        tooltip=f'第 {_page} 页',
                        data=_page,
                    )
                )

        # 下一页按钮
        next_page_btn = PrevNextPageButton(
            icon=ft.Icons.KEYBOARD_ARROW_RIGHT,
            on_click=self.click_update_page,
            tooltip='下一页',
            data=self.current_page + 1,
            disabled=self.current_page >= self.sum_page_nums,
            icon_color=ft.Colors.GREY
            if self.current_page >= self.sum_page_nums
            else None,
        )
        rst_control_list.append(next_page_btn)
        last_page_btn = PrevNextPageButton(
            icon=ft.Icons.KEYBOARD_DOUBLE_ARROW_RIGHT,
            on_click=self.click_update_page,
            tooltip='尾页',
            data=self.sum_page_nums,
            disabled=(self.current_page >= self.sum_page_nums),
            icon_color=ft.Colors.GREY
            if (self.current_page >= self.sum_page_nums)
            else None,
        )
        rst_control_list.append(last_page_btn)
        self.v_now_page.controls = rst_control_list

    def click_update_page(self, e):
        """点击页码或前后页按钮事件"""
        page = int(e.control.data)
        if 1 <= page <= self.sum_page_nums:
            self.current_page = page
            if self.on_change_page:
                self.on_change_page(self.current_page)
            self._update()


def main(page: ft.Page):
    def on_change_page(data):
        print(f'当前页码: {data}')

    page.add(Paging(sum_data_nums=123, on_change_page=on_change_page))


if __name__ == "__main__":
    ft.run(main)
