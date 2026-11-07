"""分页器 (Pagination) —— 总数、页码、跳页与每页条数。


布局：总数在左，页码 / 跳页 / 条数依次靠右。但**弹性给了页码那条**
而不是总数 —— 它 ``expand=1`` 且可横向滚动：宽容器里吃掉中间空档（页码靠右），
窄容器里被压到 0 之后自己滚，总数和右侧两组永远是完整的。这比"先把总数省略成
``共 1,28…``"更耐窄。总页数为 0 时整排翻页控件不出现 —— 对着"共 0 项"
摆一排禁用按钮，只是噪声。

用法::

    state = PaginationState(sum_data_nums=1_286, on_change_page=load)
    Column([Pagination(state)])

``use_t()`` 是本组件唯一的订阅点：语言一变重绘，外部持有的
:class:`PaginationState` 不受影响（页码、每页条数都不丢）。
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

import flet as ft

from ui.core.doc import Api, Example, Spec, info, run, tip, warn
from ui.core.format import format_number
from ui.core.i18n import t, use_t
from ui.core.styles import outline_input
from ui.core.tokens import FONT_SIZE, FONT_WEIGHT, RADIUS, SPACE, overlay

__all__ = ["Pagination", "PaginationState", "get_center_pages"]

_log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 尺寸：控件基线取本框架的 36（见模块文档第 5 条）
# ---------------------------------------------------------------------------
BTN = 32  # 页码 / 翻页按钮边长
BTN_RADIUS = RADIUS["sm"]  # 4px
PAGER_GAP = SPACE["2"]  # 8   相邻页码之间
GROUP_GAP = SPACE["4"]  # 16  组与组之间
ICON_SIZE = 18  # 翻页箭头
TEXT_PAD = 8  # 页码文字的左右留白
JUMP_W = 48  # 跳页输入框宽度
SIZE_W = 84  # 每页条数下拉宽度

# ---------------------------------------------------------------------------
# 颜色：全部是角色或"角色 + 透明度"，随明暗主题与主色自动解析
# ---------------------------------------------------------------------------
#: 翻页箭头：默认次要文字，悬停提亮到正文
NAV_FG = ft.Colors.ON_SURFACE_VARIANT
NAV_FG_HOVER = ft.Colors.ON_SURFACE
NAV_BG_HOVER = overlay(0.06)

#: 页码格子：透明底 + 发丝描边，文字同翻页箭头（一排里不该有两种灰度）
PAGE_FG = ft.Colors.ON_SURFACE_VARIANT
PAGE_FG_HOVER = ft.Colors.PRIMARY
PAGE_BORDER = ft.Colors.OUTLINE_VARIANT
PAGE_BORDER_HOVER = ft.Colors.PRIMARY

#: 当前页：主色实底 + 反白字。深色主题下 PRIMARY 变浅、ON_PRIMARY 变深，
#: 对比度仍然成立 —— 这正是走角色而不是写死 #0052D9 的理由。
CURRENT_FG = ft.Colors.ON_PRIMARY
CURRENT_BG = ft.Colors.PRIMARY

#: 禁用 / 省略号：两档更弱的灰，靠透明度拉开层次
FG_DISABLED = overlay(0.38)
FG_MUTED = ft.Colors.OUTLINE

#: 标签类文字（"前往""每页""项"）与总数同色
LABEL_FG = ft.Colors.ON_SURFACE_VARIANT


def _page_width(label: str) -> int:
    """页码格子宽度：两位数以内是正方形，三位数起按字数往外让。

    写死 32 的话，页数上千时 ``1000`` 会被裁成 ``10…``；无限放宽又会让
    两位数页码显得空荡。按字符数算，多一位加 8px，够用且可预期。
    """
    return max(BTN, TEXT_PAD * 2 + 8 * len(label))


def _hover_handler(key: str, set_hovered: Callable) -> Callable:
    """把"悬停开 / 关"折成一次 ``use_state`` 写入。

    ``e.data`` 是 ``"true"`` / ``"false"`` 字符串（不是 bool）。

    为什么不用"改控件属性 + ``control.update()``"这条更省的路：
    ``@ft.component`` 渲染出来的控件是**冻结**的，回调和进去赋值会抛
    ``Frozen controls cannot be updated``（真机踩到）。走 state 就绕开了
    冻结，代价是重绘整条分页器 —— 十几个扁平 ``Container``，实测无感。
    """

    def handler(e, _key=key, _set=set_hovered):
        on = str(e.data).strip().lower() == "true"
        _set(_key if on else "")

    return handler


# ---------------------------------------------------------------------------
# 渲染片段：格子 / 箭头 / 省略号
# ---------------------------------------------------------------------------
def _page_cell(
    page: int,
    current: bool,
    width: int,
    *,
    hovered: bool,
    on_click: Callable,
    on_hover: Callable | None,
) -> ft.Container:
    """一个页码格子。当前页是实心主色，其余是透明底 + 发丝描边。"""
    lit = hovered and not current
    return ft.Container(
        width=width,
        height=BTN,
        border_radius=BTN_RADIUS,
        alignment=ft.Alignment.CENTER,
        # bgcolor 留 None 才是透明（写 Colors.TRANSPARENT 会得到一块灰底）
        bgcolor=CURRENT_BG if current else None,
        border=ft.Border.all(
            1,
            CURRENT_BG if current else (PAGE_BORDER_HOVER if lit else PAGE_BORDER),
        ),
        content=ft.Text(
            str(page),
            size=FONT_SIZE["subtitle"],
            weight=FONT_WEIGHT["medium"] if current else None,
            color=CURRENT_FG if current else (PAGE_FG_HOVER if lit else PAGE_FG),
        ),
        data=page,
        on_click=on_click,
        on_hover=on_hover,
        tooltip=t("ui.pagination.page", n=page),
    )


def _arrow(
    *,
    icon: str,
    tooltip: str,
    data: int,
    disabled: bool,
    hovered: bool,
    on_click: Callable,
    on_hover: Callable | None,
) -> ft.Container:
    """翻页箭头：无描边，悬停一层浅灰底。禁用时连指针都不响应。"""
    if disabled:
        fg, bg = FG_DISABLED, None
    elif hovered:
        fg, bg = NAV_FG_HOVER, NAV_BG_HOVER
    else:
        fg, bg = NAV_FG, None
    return ft.Container(
        width=BTN,
        height=BTN,
        border_radius=BTN_RADIUS,
        alignment=ft.Alignment.CENTER,
        bgcolor=bg,
        content=ft.Icon(icon, size=ICON_SIZE, color=fg),
        data=data,
        tooltip=tooltip,
        on_click=None if disabled else on_click,
        on_hover=on_hover,
    )


def _more_dot() -> ft.Control:
    """省略号。不可点，所以**没有**悬停反馈（有反馈就是在暗示能点）。"""
    return ft.Container(
        width=BTN,
        height=BTN,
        alignment=ft.Alignment.CENTER,
        content=ft.Icon(ft.Icons.MORE_HORIZ, size=ICON_SIZE, color=FG_MUTED),
    )


def _pager(
    state: PaginationState,
    total_pages: int,
    current: int,
    hovered: str,
    make_hover: Callable[[str], Callable],
) -> ft.Row:
    """首页 … 页码 … 尾页 一排。间距固定 8px，换页时按钮不位移。"""
    click = state.click_update_page

    def arrow(key: str, icon: str, tip: str, data: int, disabled: bool) -> ft.Container:
        return _arrow(
            icon=icon,
            tooltip=tip,
            data=data,
            disabled=disabled,
            hovered=hovered == key,
            on_click=click,
            on_hover=None if disabled else make_hover(key),
        )

    at_start = current == 1
    at_end = current >= total_pages
    controls: list[ft.Control] = [
        arrow(
            "first",
            ft.Icons.KEYBOARD_DOUBLE_ARROW_LEFT,
            t("ui.pagination.first"),
            1,
            at_start,
        ),
        arrow(
            "prev",
            ft.Icons.KEYBOARD_ARROW_LEFT,
            t("ui.pagination.prev"),
            current - 1,
            at_start,
        ),
    ]

    for page in get_center_pages(current, total_pages):
        if page == -1:
            controls.append(_more_dot())
        else:
            key = f"p{page}"
            controls.append(
                _page_cell(
                    page,
                    page == current,
                    _page_width(str(page)),
                    hovered=hovered == key,
                    on_click=click,
                    # 当前页本来就没得"再选一次"，不给悬停反馈
                    on_hover=None if page == current else make_hover(key),
                )
            )

    controls.append(
        arrow(
            "next",
            ft.Icons.KEYBOARD_ARROW_RIGHT,
            t("ui.pagination.next"),
            current + 1,
            at_end,
        )
    )
    controls.append(
        arrow(
            "last",
            ft.Icons.KEYBOARD_DOUBLE_ARROW_RIGHT,
            t("ui.pagination.last"),
            total_pages,
            at_end,
        )
    )
    # ``expand`` + 横向滚动：宽容器里它吃掉中间的空档（页码靠右）
    # 窄容器里被压到 0 之后**自己滚**，而不是把右边的跳页/条数挤出屏幕。
    return ft.Row(
        expand=1,
        scroll=ft.ScrollMode.AUTO,
        alignment=ft.MainAxisAlignment.END,
        spacing=PAGER_GAP,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=controls,
    )


def _label(text: str) -> ft.Text:
    """分页器里的说明文字（"前往""每页""项"）：与总数同色同号。"""
    return ft.Text(text, size=FONT_SIZE["body"], color=LABEL_FG)


def _jumper(state: PaginationState) -> ft.Row:
    """「前往 [__] 页」。英文没有"页"这个后缀，语言包给空串时不渲染那个字。"""
    page_unit = t("ui.pagination.page_unit")
    return ft.Row(
        spacing=SPACE["1"],
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            _label(t("ui.pagination.goto")),
            ft.TextField(
                width=JUMP_W,
                height=BTN,
                text_size=FONT_SIZE["body"],
                text_align=ft.TextAlign.CENTER,
                content_padding=ft.Padding.symmetric(horizontal=0, vertical=6),
                on_submit=state.handle_goto_page_submit,
                border=outline_input(
                    BTN_RADIUS, ft.Colors.OUTLINE_VARIANT, ft.Colors.PRIMARY
                ),
            ),
            *([_label(page_unit)] if page_unit else []),
        ],
    )


def _size_picker(state: PaginationState, unit: str) -> ft.Row:
    """「每页 [10] 项」。候选里**必须包含当前值**，否则 Flutter 侧匹配不到
    ``value``，下拉框显示空白且点不开（真机踩到：Table 用 rows_per_page=8，
    而候选只有 5/10/15/20/30/40/50）。"""
    options = [5, 10, 15, 20, 30, 40, 50]
    current = state.data_per_page_nums
    if current not in options:
        options = sorted({*options, current})

    return ft.Row(
        # 标签与控件之间留 8：英文的 "Rows per page" 比中文的"每页"长得多，
        # 4px 会让它和下拉框贴在一起。
        spacing=SPACE["2"],
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            _label(t("ui.pagination.per_page")),
            ft.Dropdown(
                options=[ft.DropdownOption(str(n)) for n in options],
                value=str(current),
                width=SIZE_W,
                text_size=FONT_SIZE["body"],
                dense=True,
                content_padding=ft.Padding.symmetric(horizontal=6, vertical=6),
                border=outline_input(
                    BTN_RADIUS, ft.Colors.OUTLINE_VARIANT, ft.Colors.PRIMARY
                ),
                on_select=state.handle_change_per_page_nums,
            ),
            _label(unit),
        ],
    )


# ---------------------------------------------------------------------------
# 状态
# ---------------------------------------------------------------------------
@ft.observable
@dataclass
class PaginationState:
    sum_data_nums: int = 0  # 总数据条数
    on_change_page: Callable[[int], None] | None = None  # 页码变更回调
    on_change_per_page_nums: Callable[[int], None] | None = None  # 每页条数变更回调
    data_per_page_nums: int = 10  # 每页数据条数
    current_page: int = 1  # 当前页码
    #: 数据单位。留空表示跟随界面语言（"项 / 項 / items"），
    #: 需要"条 / 行 / 人"这类业务量词时再显式传。
    data_unit: str = ""

    @property
    def sum_page_nums(self) -> int:
        # 每页条数为 0 时直接除零，这里兜一层 —— 分页器崩掉不该是调用方的锅
        per_page = max(1, self.data_per_page_nums)
        num_page, num_page_over = divmod(max(0, self.sum_data_nums), per_page)
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
        """跳页输入框回车。非法输入直接忽略 —— 输入框随重绘回到空。"""
        try:
            page = int(str(e.control.value).strip())
        except (TypeError, ValueError):
            _log.debug("跳页输入无法解析：%r", e.control.value)
            return
        if 1 <= page <= self.sum_page_nums:
            self.current_page = page
            if self.on_change_page:
                self.on_change_page(self.current_page)

    def click_update_page(self, e):
        """点击页码或前后页按钮事件"""
        page = int(e.control.data)
        if 1 <= page <= self.sum_page_nums:
            self.current_page = page
            if self.on_change_page:
                self.on_change_page(self.current_page)


def get_center_pages(current_page: int, sum_page_nums: int) -> list:
    """根据当前页码和总页数生成分页按钮的页码列表。

    - 页数少于等于 6 时，全部显示。
    - 页数较多时，显示部分页码和省略号（``-1`` 代表省略号）。
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


@ft.component
def Pagination(state: PaginationState):
    """分页器：总数 + 页码 + 跳页 + 每页条数。"""
    use_t()
    #: 当前悬停的控件键（"" / "p3" / "prev" …）。用 state 而不是直接改控件 ——
    #: component 渲染出的控件是冻结的，见 :func:`_hover_handler`。
    hovered, set_hovered = ft.use_state("")

    unit = state.data_unit or t("ui.pagination.unit")
    total_pages = state.sum_page_nums
    # state 里的页码可能因为数据变少而越界；渲染用夹紧后的值，回调仍走 state
    current = min(max(state.current_page, 1), max(1, total_pages))

    total = ft.Text(
        t("ui.pagination.total", n=format_number(state.sum_data_nums), unit=unit),
        size=FONT_SIZE["body"],
        color=LABEL_FG,
        # 总数目然宽度、不参与弹性分配。弹性空间交给页码那条 ——
        # 它被压扁时自己滚，总数和右侧两组永远是完整的（见 _pager）。
        no_wrap=True,
        overflow=ft.TextOverflow.ELLIPSIS,
    )

    controls: list[ft.Control] = [total]
    if total_pages:
        controls.append(
            _pager(
                state,
                total_pages,
                current,
                hovered,
                lambda k: _hover_handler(k, set_hovered),
            )
        )
        controls.append(_jumper(state))
    controls.append(_size_picker(state, unit))

    # 单行、不换行：``wrap`` 会让 expand 撑满整行，把右侧控件全挤到下一行去。
    # 窄容器靠 ``total`` 的柔性收缩兜底（它带 ELLIPSIS，能被压到很小）。
    return ft.Row(
        spacing=GROUP_GAP,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=controls,
    )


# ---------------------------------------------------------------------------
# 独立运行：组件介绍 + 示例 + API
# ---------------------------------------------------------------------------
@ft.component
def _echo(state: PaginationState) -> ft.Control:
    """把状态读出来 —— 说明这个分页器是**受控**的：页码只是状态，数据归调用方。"""
    unit = state.data_unit or t("ui.pagination.unit")
    return ft.Text(
        f"第 {state.current_page} 页 · 每页 {state.data_per_page_nums} 条 "
        f"· 共 {format_number(state.sum_data_nums)} {unit}",
        size=FONT_SIZE["body"],
        color=ft.Colors.ON_SURFACE_VARIANT,
    )


@ft.component
def _basic() -> ft.Control:
    state = ft.use_memo(lambda: PaginationState(sum_data_nums=1_286), [])
    return ft.Column(spacing=14, controls=[Pagination(state), _echo(state)])


@ft.component
def _few_pages() -> ft.Control:
    """45 条 = 5 页：页码全展开，没有省略号。"""
    state = ft.use_memo(lambda: PaginationState(sum_data_nums=45), [])
    return ft.Column(spacing=14, controls=[Pagination(state), _echo(state)])


@ft.component
def _deep() -> ft.Control:
    """240 页、停在第 120 页：两侧都折叠成省略号，当前页始终居中。"""
    state = ft.use_memo(
        lambda: PaginationState(
            sum_data_nums=12_000, data_per_page_nums=50, current_page=120
        ),
        [],
    )
    return ft.Column(spacing=14, controls=[Pagination(state), _echo(state)])


@ft.component
def _custom_unit() -> ft.Control:
    """业务量词：日志说「条」，人说说「人」，都可以显式指定。"""
    state = ft.use_memo(
        lambda: PaginationState(sum_data_nums=268, data_per_page_nums=20, data_unit="条"),
        [],
    )
    return ft.Column(spacing=14, controls=[Pagination(state), _echo(state)])


_BASIC_CODE = '''state = PaginationState(sum_data_nums=1_286)

Column([
    Pagination(state),          # 只负责"第几页"，数据自己取
    Text(f"第 {state.current_page} 页"),
])

# 需要接管分页时挂回调（服务端分页就是这样）：
state = PaginationState(
    sum_data_nums=1_286,
    on_change_page=load_page,           # (page: int) -> None
    on_change_per_page_nums=load_size,  # (size: int) -> None
)'''

_UNIT_CODE = '''PaginationState(sum_data_nums=268, data_per_page_nums=20, data_unit="条")'''


SPEC = Spec(
    name="Pagination",
    summary="把长列表切成可控的页：左边总数、中间页码、右边跳页与每页条数。",
    definition=(
        "分页器解决的是「一屏放不下」。它不做翻页本身 —— 只把「现在第几页、"
        "一共有多少、每页几条」这三个数说清楚，并在用户改动其中任何一个时回调，"
        "数据由调用方去取。所以它同时适配内存里的大列表和只有总数的服务端分页。"
    ),
    anatomy=[
        (
            "总数",
            "最左边「共 1,286 项」：给出规模感，也是「还剩多少」的唯一线索。",
        ),
        (
            "页码条",
            "首/末页 + 前后页 + 页码 + 省略号。它是唯一吃弹性的部分：宽了靠右，"
            "窄了被压到自己横向滚动，而总数与右侧两组永远是完整的。",
        ),
        ("当前页", "主色实底 + 反白字。一排里只有它是实心的，扫一眼就知道在哪。"),
        ("跳页", "「前往 [__] 页」，回车生效；非法输入直接忽略，输入框随重绘清空。"),
        (
            "每页条数",
            "「每页 [10] 项」。一改动就回到第 1 页 —— 每页条数变了还停在第 7 页，"
            "用户找不到刚才那条数据。",
        ),
    ],
    when=[
        "数据超过一屏，且用户需要知道「一共多少」",
        "需要在页与页之间来回对照（翻回去找刚看过的那条）",
        "服务端分页：后端只给总数，数据按页取",
    ],
    avoid=[
        "十几行数据：一屏能看完，分页只多了一次点击",
        "时间流、聊天记录：追加式加载（无限滚动）更贴合阅读习惯",
        "只需要「加载更多」：用按钮或滚动触发，别摆一排页码",
    ],
    examples=[
        Example(
            "基础用法",
            _basic,
            hint="1,286 条、每页 10 条。改动页码或条数都会回写到 PaginationState。",
            code=_BASIC_CODE,
        ),
        Example(
            "页数不多",
            _few_pages,
            hint="5 页以内全部展开，不出现省略号 —— 能一次看全就别折叠。",
        ),
        Example(
            "上百页",
            _deep,
            hint="240 页、停在第 120 页：两侧各收成省略号，当前页始终居中。",
        ),
        Example(
            "自定义量词",
            _custom_unit,
            hint="data_unit 换掉「项」；留空则跟随界面语言（项 / 項 / items）。",
            code=_UNIT_CODE,
        ),
    ],
    api=[
        Api("state", "PaginationState", "", "Pagination 的唯一参数：受控状态"),
        Api("sum_data_nums", "int", "0", "总条数。决定总页数，也显示在左边"),
        Api("data_per_page_nums", "int", "10", "每页条数；改动后自动回到第 1 页"),
        Api("current_page", "int", "1", "当前页码（1 起）。越界时渲染会夹紧"),
        Api("data_unit", "str", "''", "单位量词（条 / 人 / 行）；留空跟随语言"),
        Api(
            "on_change_page",
            "Callable[[int], None] | None",
            "None",
            "页码变化回调，服务端分页在这里取数据",
        ),
        Api(
            "on_change_per_page_nums",
            "Callable[[int], None] | None",
            "None",
            "每页条数变化回调",
        ),
        Api("sum_page_nums", "int", "—", "只读属性：总页数 = ⌈总条数 / 每页条数⌉"),
    ],
    notes=[
        tip(
            "悬停与点击都写回 state，而不是直接改控件。@ft.component 渲染出来的控件是"
            "冻结的，回调和进去赋值会抛 Frozen controls cannot be updated。"
        ),
        info(
            "总页数为 0 时整排翻页控件不出现，只留「共 0 项」与每页条数 —— 对着"
            "「共 0 项」摆一排禁用按钮，只是噪声。"
        ),
        warn(
            "每页条数的候选里必须包含当前值，否则 Flutter 侧匹配不到 value，下拉框会"
            "显示空白且点不开。组件已自动补齐，自定义候选时别漏。"
        ),
    ],
    tags=("分页", "翻页", "pager", "page size"),
)


if __name__ == "__main__":
    run(SPEC)
