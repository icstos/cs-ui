import os
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum

import flet as ft

from ui.core.format import format_number
from ui.core.i18n import t, use_t
from ui.core.styles import outline_input


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
    # width/height 在基类中是 kw_only 字段；重新声明时必须显式 kw_only=True，
    # 否则会变成第 0 个位置参数，抢占 content 的位置（详见 ui.input.button.Button）。
    width: int = field(default=ICON_WIDTH, kw_only=True)
    height: int = field(default=ICON_HEIGHT, kw_only=True)
    style: ft.ButtonStyle = field(
        default_factory=lambda: ft.ButtonStyle(
            color=ft.Colors.BLUE,
            bgcolor={ft.ControlState.DEFAULT: ft.Colors.WHITE},
            side={
                ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.BLUE),
            },
            shape=ft.RoundedRectangleBorder(radius=BorderRadiusSize.M.value),
            elevation=0,
            padding=0,
        )
    )


@ft.control
class OtherPageButton(ft.Button):
    width: int = field(default=ICON_WIDTH, kw_only=True)
    height: int = field(default=ICON_HEIGHT, kw_only=True)
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
    width: int = field(default=ICON_WIDTH, kw_only=True)
    height: int = field(default=ICON_HEIGHT, kw_only=True)
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


def get_center_pages(current_page: int, sum_page_nums: int) -> list:
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


@ft.observable
@dataclass
class PagingState:
    sum_data_nums: int = 0  # 总数据条数
    on_change_page: Callable[[int], None] | None = None  # 页码变更回调
    on_change_per_page_nums: Callable[[int], None] | None = None  # 每页数据条数变更回调
    data_per_page_nums: int = 10  # 每页数据条数
    current_page: int = 1  # 当前页码
    #: 数据单位。留空表示跟随界面语言（"项 / 項 / items"），
    #: 需要"条 / 行 / 人"这类业务量词时再显式传。
    data_unit: str = ""

    @property
    def sum_page_nums(self) -> int:
        num_page, num_page_over = divmod(self.sum_data_nums, self.data_per_page_nums)
        return num_page + (1 if num_page_over else 0)

    def handle_change_per_page_nums(self, e):
        self.data_per_page_nums = int(e.control.value)
        self.current_page = 1  # 切换每页条数时回到首页
        if self.on_change_page:
            self.on_change_page(self.current_page)
        if self.on_change_per_page_nums:
            self.on_change_per_page_nums(self.data_per_page_nums)

    def update_sum_data_nums(self, value: int):
        self.sum_data_nums = value

    def handle_goto_page_submit(self, e):
        try:
            page = int(e.control.value)
            if 1 <= page <= self.sum_page_nums:
                self.current_page = page
                if self.on_change_page:
                    self.on_change_page(self.current_page)
        except Exception:
            pass  # 非法输入忽略

    def click_update_page(self, e):
        """点击页码或前后页按钮事件"""
        page = int(e.control.data)
        if 1 <= page <= self.sum_page_nums:
            self.current_page = page
            if self.on_change_page:
                self.on_change_page(self.current_page)


@ft.component
def Paging(state: PagingState):
    """分页器：总数 + 页码 + 每页条数。

    所有文案与数字格式都取自当前语言（``ui.paging.*``）：中文是
    「共 1,286 项 · 前往 [10] 页 · 每页 [10] 项」，英文是
    「1,286 items · Go to [10] · Rows per page [10]」。语序差异由整句模板吸收，
    这里只负责填参数 —— 不做"拼接词 + 变量 + 拼接词"。

    ``use_t()`` 是本组件唯一的订阅点：语言一变，``Paging`` 重绘，
    外部持有的 :class:`PagingState` 不变（页码、每页条数都不丢）。
    """
    use_t()

    unit = state.data_unit or t("ui.paging.unit")
    rst_controls = []
    if os.environ.get("CS_UI_DEBUG_PAGING"):
        print(
            f"[Paging] render current_page={state.current_page} "
            f"pages={state.sum_page_nums}",
            flush=True,
        )

    rst_controls.append(
        PrevNextPageButton(
            icon=ft.Icons.KEYBOARD_DOUBLE_ARROW_LEFT,
            on_click=state.click_update_page,
            tooltip=t("ui.paging.first"),
            data=1,
            disabled=(state.current_page == 1),
            icon_color=ft.Colors.GREY if (state.current_page == 1) else None,
        )
    )
    rst_controls.append(
        PrevNextPageButton(
            icon=ft.Icons.KEYBOARD_ARROW_LEFT,
            on_click=state.click_update_page,
            tooltip=t("ui.paging.prev"),
            data=state.current_page - 1,
            disabled=(state.current_page == 1),
            icon_color=ft.Colors.GREY if (state.current_page == 1) else None,
        )
    )

    for _page in get_center_pages(state.current_page, state.sum_page_nums):
        if _page == -1:
            rst_controls.append(ft.Text("..."))
        elif _page == state.current_page:
            # 当前页
            rst_controls.append(
                NowPageButton(
                    content=str(_page),
                    on_click=state.click_update_page,
                    tooltip=t("ui.paging.page", n=_page),
                    data=_page,
                )
            )

        else:
            # 其他页
            rst_controls.append(
                OtherPageButton(
                    content=str(_page),
                    on_click=state.click_update_page,
                    tooltip=t("ui.paging.page", n=_page),
                    data=_page,
                )
            )
    # 下一页按钮
    rst_controls.append(
        PrevNextPageButton(
            icon=ft.Icons.KEYBOARD_ARROW_RIGHT,
            on_click=state.click_update_page,
            tooltip=t("ui.paging.next"),
            data=state.current_page + 1,
            disabled=state.current_page >= state.sum_page_nums,
            icon_color=ft.Colors.GREY
            if state.current_page >= state.sum_page_nums
            else None,
        )
    )
    rst_controls.append(
        PrevNextPageButton(
            icon=ft.Icons.KEYBOARD_DOUBLE_ARROW_RIGHT,
            on_click=state.click_update_page,
            tooltip=t("ui.paging.last"),
            data=state.sum_page_nums,
            disabled=(state.current_page >= state.sum_page_nums),
            icon_color=ft.Colors.GREY
            if (state.current_page >= state.sum_page_nums)
            else None,
        )
    )
    v_now_page = ft.Row(controls=rst_controls)
    v_goto_page = ft.TextField(
        on_submit=state.handle_goto_page_submit,
        width=40,
        height=32,
        text_align=ft.TextAlign.CENTER,
        content_padding=0,
        border=outline_input(4, ft.Colors.GREY_300, ft.Colors.BLUE),
    )
    # 每页条数的候选。**当前值不在候选里时要补进去** ——
    # 否则 Flutter 侧匹配不到 value，下拉框显示空白且点不开。
    # （真机踩到：Table 用 rows_per_page=8，Paging 的候选只有 5/10/15/20/30/40/50。）
    per_page_options = [5, 10, 15, 20, 30, 40, 50]
    current_per_page = state.data_per_page_nums
    if current_per_page not in per_page_options:
        per_page_options = sorted({*per_page_options, current_per_page})

    v_num_of_row_changer_field = ft.Dropdown(
        options=[ft.DropdownOption(str(_)) for _ in per_page_options],
        value=str(current_per_page),
        width=88,
        # height=32,
        # text_align=ft.TextAlign.CENTER,
        dense=True,
        content_padding=0,
        border=outline_input(4, ft.Colors.GREY_300, ft.Colors.BLUE),
        scale=0.9,
        on_select=state.handle_change_per_page_nums,
    )
    if os.environ.get("CS_UI_DEBUG_PAGING"):
        print(
            f"[Paging] dropdown value={current_per_page!r} "
            f"options={[o.key for o in v_num_of_row_changer_field.options]}",
            flush=True,
        )
    # 「前往 [x] ___」：有些语言（英文）没有"页"这个后缀，语言包给空串时
    # 直接不渲染那个 Text，免得留下一个孤立的空格。
    page_unit = t("ui.paging.page_unit")
    goto_controls: list[ft.Control] = [
        v_now_page,
        ft.Text(t("ui.paging.goto")),
        v_goto_page,
        *([ft.Text(page_unit)] if page_unit else []),
    ]
    return ft.Row(
        controls=[
            ft.Text(t("ui.paging.total", n=format_number(state.sum_data_nums), unit=unit)),
            ft.Row(controls=goto_controls, spacing=6),
            ft.Row(
                controls=[
                    ft.Text(t("ui.paging.per_page")),
                    v_num_of_row_changer_field,
                    ft.Text(unit),
                ]
            ),
        ]
    )


@ft.component
def App():
    paging_state = PagingState(
        sum_data_nums=123,
        on_change_page=lambda page: print(f"当前页码: {page}"),
        on_change_per_page_nums=lambda per_page_nums: print(
            f"每页条数: {per_page_nums}"
        ),
    )
    # def on_change_page(data):
    # print(f'当前页码: {data}')

    return Paging(paging_state)


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
