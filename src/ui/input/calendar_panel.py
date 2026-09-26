"""月历视图混入 (CalendarPanel)：``DateInput`` / ``DateTimeInput`` 共用的日历。

抽这一层的理由很直接：日期选择器和日期时间选择器用的是**同一张月历** ——
头部翻页、星期表头、6 × 7 日期网格、年月网格、悬停 / 选中 / 禁用配色，逐像素一致。
差异只有四处，宿主类覆写对应的"钩子"即可：

======================  ==========================  ==============================
钩子                     ``DateInput``               ``DateTimeInput``
======================  ==========================  ==============================
``_cal_bounds()``        ``min_date`` .. ``max_date``  ``min_datetime`` .. ``max_datetime``
``_cal_is_selected(d)``  ``d == value``               ``d == value.date()``
``_cal_day_enabled(d)``  默认（按 ``_cal_bounds``）  默认
``_cal_pick(d)``         选中并收起                  只改日期部分，面板保持展开
======================  ==========================  ==============================

宿主须提供以下字段 / 方法（本混入只读不写）：

- ``_view_year`` / ``_view_month``：面板正在显示的年月；
- ``_mode``：``"day"`` 月历 / ``"month"`` 年月网格；
- ``_hover``：当前悬停元素的 key；
- ``first_day_weekday`` / ``weekday_labels``：星期排布（见 :data:`WEEKDAYS`）；
- ``_hover_key(key, hovering)`` / ``notify()``：由 ``@ft.observable`` 提供；
- 输入框相关：``value`` / ``disabled`` / ``clearable`` / ``is_open`` /
  ``_invalid`` / ``_anchor`` / ``_field_w`` / ``_field_h`` / ``float_panel``。

栅格常量也集中在这里：两个组件必须用同一套尺寸，否则并排放在表单里会有
1~2 像素的高度差。
"""

from __future__ import annotations

import datetime
from collections.abc import Callable

import flet as ft

from ui.core.float_layer import overlay_usable

__all__ = ["CalendarPanel", "WEEKDAYS", "place_panel"]

# ---------------------------------------------------------------------------
# 尺寸
# ---------------------------------------------------------------------------
FIELD_WIDTH = 240  # 输入框默认宽度
FIELD_HEIGHT = 40  # 输入框高度
FIELD_RADIUS = 8  # 输入框 / 面板圆角
FIELD_PAD_H = 10  # 输入框左右内边距

PANEL_PAD = 8  # 面板内边距
PANEL_GAP = 4  # 面板与输入框之间的间距
CELL_W = 34  # 日期格宽
CELL_H = 32  # 日期格高
GRID_ROWS = 6  # 月历固定 6 行（容纳跨月的 42 天）
HEADER_H = 38  # 面板头部（翻页 + 年月标题）
WEEKDAY_H = 26  # 星期行
FOOTER_H = 34  # 面板页脚
NAV_SIZE = 26  # 翻页按钮
MONTH_H = 48  # 年月网格的单格高（4 × 48 = 192 = 6 × CELL_H）
NAV_RADIUS = 6  # 小按钮圆角
CELL_RADIUS = 6  # 日期格圆角

CAL_GRID_W = CELL_W * 7  # 月历栅格宽
CAL_GRID_H = WEEKDAY_H + CELL_H * GRID_ROWS  # 月历栅格高（星期行 + 6 行日期）
CAL_W = PANEL_PAD * 2 + CAL_GRID_W + 2  # 只放月历时面板的宽（含 1px 边框 ×2）
PANEL_H = PANEL_PAD * 2 + 2 + HEADER_H + CAL_GRID_H + 1 + FOOTER_H  # 面板高

TEXT_SIZE = 13
SMALL_SIZE = 12
LABEL_SIZE = 11

SCREEN_MARGIN = 8  # 面板与窗口边缘的最小间距

# ---------------------------------------------------------------------------
# 配色（全部走主题色，明暗主题下都可用）
# ---------------------------------------------------------------------------
HOVER_BG = ft.Colors.with_opacity(0.06, ft.Colors.ON_SURFACE)  # 悬停底色
TODAY_BG = ft.Colors.with_opacity(0.10, ft.Colors.PRIMARY)  # "今天"淡色底
SELECTED_BG = ft.Colors.PRIMARY  # 选中填色
DISABLED_FG = ft.Colors.with_opacity(0.38, ft.Colors.ON_SURFACE)  # 越界禁用字色

#: 星期标签，索引与 ``datetime.date.weekday()`` 一致：0 = 周一 … 6 = 周日。
WEEKDAYS = ("一", "二", "三", "四", "五", "六", "日")


# ---------------------------------------------------------------------------
# 纯函数工具
# ---------------------------------------------------------------------------
def _is_leap_year(year: int) -> bool:
    """判断是否为闰年。"""
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


def _get_days_in_month(year: int, month: int) -> int:
    """根据年月获取该月天数，自动处理闰年二月。"""
    if month == 2:
        return 29 if _is_leap_year(year) else 28
    if month in (4, 6, 9, 11):
        return 30
    return 31


def _truthy(value: object) -> bool:
    """把 hover 事件载荷归一成布尔（可能是 bool，也可能是 ``"true"`` 字符串）。"""
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def place_panel(
    page: ft.Page,
    anchor: tuple[float, float] | None,
    field_h: float,
    panel_w: float,
    panel_h: float,
) -> tuple[float, float | None, float | None]:
    """面板定位：返回 ``(left, top, bottom)``，``top`` / ``bottom`` 二选一。

    默认从锚点（输入框）下沿往下弹；下方放不下就向上翻转、改用 ``bottom`` 锚定
    —— 这样面板多高都能自动贴住输入框上沿（``top`` 方式要求预先知道面板高度，
    高度估算的误差会变成一条可见的缝）。左右方向做边界收拢。

    两个都放不下时保持"向下弹"，让面板溢出到窗口外，也好过盖住输入框。
    """
    ax, ay = anchor or (0.0, 0.0)
    page_w = float(getattr(page, "width", 0) or 0)
    page_h = float(getattr(page, "height", 0) or 0)

    left = ax
    if page_w and left + panel_w > page_w - SCREEN_MARGIN:
        left = max(SCREEN_MARGIN, page_w - panel_w - SCREEN_MARGIN)

    top = ay + field_h + PANEL_GAP
    if page_h and top + panel_h > page_h - SCREEN_MARGIN:
        if ay - panel_h - PANEL_GAP >= SCREEN_MARGIN:
            return left, None, page_h - ay + PANEL_GAP
    return left, top, None


class CalendarPanel:
    """月历视图混入。见模块 docstring 的钩子表。"""

    # ---- 宿主契约（由宿主类提供；这里列出便于对照） ----
    #   _view_year / _view_month / _mode / _hover / first_day_weekday /
    #   weekday_labels / value / disabled / clearable / is_open / _invalid /
    #   _anchor / _field_w / _field_h / float_panel
    #   notify() / _hover_key()

    # ------------------------------------------------------------------
    # 钩子：宿主覆写
    # ------------------------------------------------------------------
    def _cal_bounds(self) -> tuple[datetime.date, datetime.date]:
        """可选日期范围（含端点）。宿主必须覆写，否则一切皆可选。"""
        return datetime.date.min, datetime.date.max

    def _cal_is_selected(self, day: datetime.date) -> bool:
        """``day`` 是否为"已选中"（决定填色高亮）。"""
        return getattr(self, "value", None) == day

    def _cal_is_month_selected(self, month: int) -> bool:
        """年月网格里该月是否命中当前值（``date`` / ``datetime`` 都可用）。"""
        value = getattr(self, "value", None)
        if value is None:
            return False
        return value.year == self._view_year and value.month == month

    def _cal_day_enabled(self, day: datetime.date) -> bool:
        """``day`` 是否可选。"""
        lo, hi = self._cal_bounds()
        return lo <= day <= hi

    def _cal_pick(self, day: datetime.date) -> None:
        """用户点了某一天。宿主决定"选完收起"还是"只改日期部分"。"""
        raise NotImplementedError

    # ------------------------------------------------------------------
    # 状态迁移
    # ------------------------------------------------------------------
    def _hover_key(self, key: str, hovering: bool) -> None:
        """更新悬停元素（同一 key 重复进入 / 离开时提前返回，避免抖动）。"""
        if (self._hover == key) == hovering:
            return
        self._hover = key if hovering else None
        self.notify()  # type: ignore[attr-defined]

    def _cal_shift_month(self, delta: int) -> None:
        """面板月份 ±N（自动跨年）。"""
        y, m = self._view_year, self._view_month + delta
        y += (m - 1) // 12
        self._view_year, self._view_month = y, (m - 1) % 12 + 1
        self._hover = None
        self.notify()  # type: ignore[attr-defined]

    def _cal_shift_year(self, delta: int) -> None:
        """面板年份 ±N（年月网格视图用）。"""
        self._view_year += delta
        self._hover = None
        self.notify()  # type: ignore[attr-defined]

    def _cal_toggle_mode(self) -> None:
        """月历 ⇄ 年月网格。"""
        self._mode = "month" if self._mode == "day" else "day"
        self._hover = None
        self.notify()  # type: ignore[attr-defined]

    def _cal_select_month(self, month: int) -> None:
        """在年月网格里选中某月，回到月历。"""
        self._view_month = month
        self._mode = "day"
        self._hover = None
        self.notify()  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # 面板头部
    # ------------------------------------------------------------------
    def _cal_header(self) -> ft.Control:
        """面板头部：翻页箭头 + 可点击的年月标题（点它切年月网格）。"""
        if self._mode == "month":
            title: str = f"{self._view_year} 年"
            unit = "年"
            prev = lambda: self._cal_shift_year(-1)  # noqa: E731
            nxt = lambda: self._cal_shift_year(1)  # noqa: E731
        else:
            title = f"{self._view_year} 年 {self._view_month} 月"
            unit = "月"
            prev = lambda: self._cal_shift_month(-1)  # noqa: E731
            nxt = lambda: self._cal_shift_month(1)  # noqa: E731

        title_btn = ft.Container(
            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
            border_radius=ft.BorderRadius.all(NAV_RADIUS),
            bgcolor=HOVER_BG if self._hover == "title" else None,
            on_click=lambda _e: self._cal_toggle_mode(),
            on_hover=lambda e: self._hover_key("title", _truthy(e.data)),
            content=ft.Row(
                tight=True,
                spacing=2,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text(
                        title,
                        size=TEXT_SIZE,
                        weight=ft.FontWeight.W_600,
                        color=ft.Colors.ON_SURFACE,
                    ),
                    ft.Icon(
                        ft.Icons.ARROW_DROP_UP
                        if self._mode == "month"
                        else ft.Icons.ARROW_DROP_DOWN,
                        size=16,
                        color=ft.Colors.OUTLINE,
                    ),
                ],
            ),
        )

        return ft.Container(
            height=HEADER_H,
            content=ft.Row(
                spacing=0,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    self._nav_button("prev", ft.Icons.CHEVRON_LEFT, prev, f"上一{unit}"),
                    ft.Container(
                        expand=True, alignment=ft.Alignment.CENTER, content=title_btn
                    ),
                    self._nav_button("next", ft.Icons.CHEVRON_RIGHT, nxt, f"下一{unit}"),
                ],
            ),
        )

    def _nav_button(
        self,
        key: str,
        icon: ft.IconData,
        on_click: Callable[[], None],
        tooltip: str,
    ) -> ft.Control:
        """面板里的方形图标按钮（翻页 / 跳值）。"""
        return ft.Container(
            width=NAV_SIZE,
            height=NAV_SIZE,
            alignment=ft.Alignment.CENTER,
            border_radius=ft.BorderRadius.all(NAV_RADIUS),
            bgcolor=HOVER_BG if self._hover == key else None,
            on_click=lambda _e: on_click(),
            on_hover=lambda e, k=key: self._hover_key(k, _truthy(e.data)),
            tooltip=ft.Tooltip(message=tooltip),
            content=ft.Icon(icon, size=18, color=ft.Colors.ON_SURFACE_VARIANT),
        )

    # ------------------------------------------------------------------
    # 月历
    # ------------------------------------------------------------------
    def _cal_body(self) -> ft.Control:
        """月历主体；年月网格视图下换成 4 × 3。"""
        if self._mode == "month":
            return self._cal_months()
        return ft.Column(
            spacing=0, controls=[self._cal_weekdays(), self._cal_days()]
        )

    def _cal_weekday_sequence(self) -> list[str]:
        """按 ``first_day_weekday`` 旋转后的星期标签（长度恒为 7）。

        ``WEEKDAYS[i]`` 对应 ``weekday() == i``；首列要放 ``first_day_weekday``，
        所以序列从该下标开始绕一圈。
        """
        labels = [str(x) for x in self.weekday_labels][:7] or list(WEEKDAYS)
        offset = int(self.first_day_weekday) % 7
        return labels[offset:] + labels[:offset]

    def _cal_weekdays(self) -> ft.Control:
        """星期表头。"""
        return ft.Container(
            height=WEEKDAY_H,
            content=ft.Row(
                spacing=0,
                controls=[
                    ft.Container(
                        width=CELL_W,
                        alignment=ft.Alignment.CENTER,
                        content=ft.Text(
                            label, size=LABEL_SIZE, color=ft.Colors.ON_SURFACE_VARIANT
                        ),
                    )
                    for label in self._cal_weekday_sequence()
                ],
            ),
        )

    def _cal_grid_start(self) -> datetime.date:
        """网格第一格对应的日期（可能落在上月）。"""
        first = datetime.date(self._view_year, self._view_month, 1)
        offset = (first.weekday() - int(self.first_day_weekday)) % 7
        return first - datetime.timedelta(days=offset)

    def _cal_days(self) -> ft.Control:
        """6 × 7 日期网格，固定 6 行 —— 面板高度不随月份跳动。"""
        start = self._cal_grid_start()
        rows: list[ft.Control] = []
        for r in range(GRID_ROWS):
            rows.append(
                ft.Row(
                    spacing=0,
                    controls=[
                        self._cal_day_cell(start + datetime.timedelta(days=r * 7 + c))
                        for c in range(7)
                    ],
                )
            )
        return ft.Container(
            height=CELL_H * GRID_ROWS,
            content=ft.Column(spacing=0, controls=rows),
        )

    def _cal_day_cell(self, day: datetime.date) -> ft.Control:
        """单个日期格：选中填主色、"今天"淡色底、越界灰字禁用。"""
        key = day.isoformat()
        in_month = (day.year, day.month) == (self._view_year, self._view_month)
        enabled = self._cal_day_enabled(day)
        selected = enabled and self._cal_is_selected(day)
        is_today = day == datetime.date.today()
        hovered = enabled and self._hover == key

        bgcolor: ft.ColorValue | None
        color: ft.ColorValue
        if selected:
            bgcolor, color = SELECTED_BG, ft.Colors.ON_PRIMARY
        elif not enabled:
            bgcolor, color = None, DISABLED_FG
        elif hovered:
            bgcolor = HOVER_BG
            color = ft.Colors.ON_SURFACE if in_month else ft.Colors.OUTLINE
        elif is_today:
            bgcolor, color = TODAY_BG, ft.Colors.PRIMARY
        elif not in_month:
            bgcolor, color = None, ft.Colors.OUTLINE
        else:
            bgcolor, color = None, ft.Colors.ON_SURFACE

        return ft.Container(
            width=CELL_W,
            height=CELL_H,
            alignment=ft.Alignment.CENTER,
            border_radius=ft.BorderRadius.all(CELL_RADIUS),
            bgcolor=bgcolor,
            on_click=None if not enabled else (lambda _e, d=day: self._cal_pick(d)),
            on_hover=None
            if not enabled
            else (lambda e, k=key: self._hover_key(k, _truthy(e.data))),
            content=ft.Text(
                str(day.day),
                size=TEXT_SIZE,
                color=color,
                weight=ft.FontWeight.W_600
                if (selected or (is_today and enabled))
                else ft.FontWeight.NORMAL,
            ),
        )

    def _cal_months(self) -> ft.Control:
        """4 × 3 年月网格，高度与月历区一致（面板不跳动）。"""
        pad = max(0, (CAL_GRID_H - MONTH_H * 4) // 2)
        rows: list[ft.Control] = []
        for r in range(4):
            rows.append(
                ft.Row(
                    spacing=0,
                    expand=True,
                    controls=[
                        self._cal_month_cell(r * 3 + c + 1) for c in range(3)
                    ],
                )
            )
        return ft.Container(
            height=CAL_GRID_H,
            padding=ft.Padding.symmetric(vertical=pad),
            content=ft.Column(spacing=0, expand=True, controls=rows),
        )

    def _cal_month_cell(self, month: int) -> ft.Control:
        """年月网格里的单个月份。"""
        key = f"m{month}"
        selected = self._cal_is_month_selected(month)
        enabled = self._cal_month_enabled(month)
        hovered = enabled and self._hover == key

        bgcolor: ft.ColorValue | None
        color: ft.ColorValue
        if selected:
            bgcolor, color = SELECTED_BG, ft.Colors.ON_PRIMARY
        elif not enabled:
            bgcolor, color = None, DISABLED_FG
        elif hovered:
            bgcolor, color = HOVER_BG, ft.Colors.ON_SURFACE
        else:
            bgcolor, color = None, ft.Colors.ON_SURFACE

        return ft.Container(
            height=MONTH_H,
            expand=True,
            alignment=ft.Alignment.CENTER,
            border_radius=ft.BorderRadius.all(CELL_RADIUS),
            bgcolor=bgcolor,
            on_click=None
            if not enabled
            else (lambda _e, m=month: self._cal_select_month(m)),
            on_hover=None
            if not enabled
            else (lambda e, k=key: self._hover_key(k, _truthy(e.data))),
            content=ft.Text(
                f"{month} 月",
                size=TEXT_SIZE,
                color=color,
                weight=ft.FontWeight.W_600 if selected else ft.FontWeight.NORMAL,
            ),
        )

    def _cal_month_enabled(self, month: int) -> bool:
        """该月的任意一天在可选范围内即可选。"""
        lo, hi = self._cal_bounds()
        first = datetime.date(self._view_year, month, 1)
        last = datetime.date(
            self._view_year, month, _get_days_in_month(self._view_year, month)
        )
        return last >= lo and first <= hi

    # ------------------------------------------------------------------
    # 页脚
    # ------------------------------------------------------------------
    def _link_button(
        self,
        key: str,
        label: str,
        on_click: Callable[[], None],
        enabled: bool = True,
    ) -> ft.Control:
        """页脚的文字按钮。"""
        if not enabled:
            return ft.Container(
                padding=ft.Padding.symmetric(horizontal=6, vertical=4),
                content=ft.Text(label, size=SMALL_SIZE, color=DISABLED_FG),
            )
        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=6, vertical=4),
            border_radius=ft.BorderRadius.all(CELL_RADIUS),
            bgcolor=HOVER_BG if self._hover == key else None,
            on_click=lambda _e: on_click(),
            on_hover=lambda e, k=key: self._hover_key(k, _truthy(e.data)),
            content=ft.Text(label, size=SMALL_SIZE, color=ft.Colors.PRIMARY),
        )

    # ------------------------------------------------------------------
    # 面板外壳
    # ------------------------------------------------------------------
    @staticmethod
    def _divider() -> ft.Control:
        """面板内的 1px 分隔线。"""
        return ft.Container(height=1, bgcolor=ft.Colors.OUTLINE_VARIANT)

    def _panel_shell(self, width: float, body: ft.Control) -> ft.Control:
        """面板外壳：白底 + 1px 描边 + 圆角 + 阴影 + 统一内边距。

        两个组件的面板只在**内容**上不同（一个只有月历，一个还要摆时间列），
        外壳逐像素一致。
        """
        return ft.Container(
            width=width,
            bgcolor=ft.Colors.SURFACE,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=ft.BorderRadius.all(FIELD_RADIUS),
            padding=ft.Padding.symmetric(vertical=PANEL_PAD, horizontal=PANEL_PAD),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            shadow=ft.BoxShadow(
                blur_radius=12,
                color=ft.Colors.with_opacity(0.10, ft.Colors.BLACK),
                offset=ft.Offset(0, 3),
            ),
            content=body,
        )

    # ------------------------------------------------------------------
    # 输入框（两个组件的折叠态长得一样，只有内部文本与尾图标不同）
    # ------------------------------------------------------------------
    @property
    def _fg(self) -> ft.ColorValue:
        """框内文字色：禁用时压灰。"""
        return ft.Colors.OUTLINE if self.disabled else ft.Colors.ON_SURFACE

    @property
    def _border_color(self) -> ft.ColorValue:
        """框体边框色：非法 > 展开 > 常态。"""
        if self.disabled:
            return ft.Colors.OUTLINE_VARIANT
        if self._invalid:
            return ft.Colors.ERROR
        if self.is_open:
            return ft.Colors.PRIMARY
        return ft.Colors.OUTLINE_VARIANT

    def _show_clear(self) -> bool:
        """是否显示框内 ×：可清空、未禁用、且当前有值。"""
        return self.clearable and not self.disabled and self.value is not None

    def _clear_button(self) -> ft.Control:
        """框内清空按钮。

        用 ``GestureDetector`` 而不是 ``Container.on_click``：后者在内层时会被
        外层 ``GestureDetector`` 抢走（真机实测，点 × 变成开合面板），同类型的
        tap 识别器才会按"内层优先"决出胜者。
        """
        return ft.GestureDetector(
            on_tap=lambda _e: self.clear(),
            content=ft.Container(
                padding=ft.Padding.all(3),
                border_radius=ft.BorderRadius.all(4),
                bgcolor=HOVER_BG if self._hover == "clear" else None,
                on_hover=lambda e: self._hover_key("clear", _truthy(e.data)),
                tooltip=ft.Tooltip(message="清除"),
                content=ft.Icon(ft.Icons.CLOSE, size=14, color=ft.Colors.OUTLINE),
            ),
        )

    def _build_field(self, text_field: ft.Control, trailing: ft.Control) -> ft.Control:
        """折叠态输入框 = 文本框 + 可选 × + 尾图标，整体可点。

        关键在 ``_text_field()`` 的 ``ignore_pointers``：收起时必须让输入框不吃
        指针事件，否则外层 ``GestureDetector`` 永远收不到点击（flet 1.0 实测）。
        """
        controls: list[ft.Control] = [
            ft.Container(expand=True, content=text_field)
        ]
        if self._show_clear():
            controls.append(self._clear_button())
        controls.append(trailing)

        box = ft.Container(
            width=self.width,
            height=self.height,
            bgcolor=ft.Colors.SURFACE_CONTAINER
            if self.disabled
            else ft.Colors.SURFACE,
            border=ft.Border.all(1, self._border_color),
            border_radius=ft.BorderRadius.all(FIELD_RADIUS),
            padding=ft.Padding.symmetric(horizontal=FIELD_PAD_H),
            on_size_change=None if self.disabled else self._on_field_size,
            size_change_interval=0,
            content=ft.Row(
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=controls,
            ),
        )
        if self.disabled:
            return box
        # 收起时整框都是"可点开面板"，展开后交回输入框自己的 I 形光标。
        return ft.GestureDetector(
            on_tap=self._on_field_tap,
            mouse_cursor=None if self.is_open else ft.MouseCursor.CLICK,
            content=box,
        )

    def _on_field_tap(self, e: ft.TapEvent) -> None:
        """记录输入框位置（浮层据此定位），再切换展开态。

        坐标只能从 ``GestureDetector`` 拿：``Container.on_click`` 的事件不带位置，
        而 ``TextField`` 的 ``on_click`` 同样如此。``global - local`` 就是控件
        左上角在页面客户区里的坐标。
        """
        gp = getattr(e, "global_position", None)
        lp = getattr(e, "local_position", None)
        if gp is not None and lp is not None:
            self._anchor = (gp.x - lp.x, gp.y - lp.y)
        self.toggle_open()

    def _on_field_size(self, e: ft.LayoutSizeChangeEvent) -> None:
        """记录输入框实测尺寸，浮层定位与遮罩挖洞都要用。"""
        w = getattr(e, "width", None)
        h = getattr(e, "height", None)
        changed = False
        if w and abs(w - self._field_w) > 0.5:
            self._field_w = float(w)
            changed = True
        if h and abs(h - self._field_h) > 0.5:
            self._field_h = float(h)
            changed = True
        if changed:
            self.notify()  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # 浮层
    # ------------------------------------------------------------------
    def _should_float(self, page: ft.Page) -> bool:
        """面板是否走页面浮层（``float_panel`` 显式指定优先）。"""
        if self.float_panel is not None:
            return self.float_panel
        return overlay_usable(page)

    def _hole(self) -> tuple[float, float, float, float] | None:
        """遮罩上给输入框挖的洞。"""
        if self._anchor is None:
            return None
        return (self._anchor[0], self._anchor[1], self._field_w, self._field_h)

    def _with_label(self, body: ft.Control) -> ft.Control:
        """按 ``v_label`` / ``is_vertical`` 把标签摆到内容旁。"""
        if self.v_label is None:
            return body
        if self.is_vertical:
            return ft.Column(
                controls=[self.v_label, body],
                spacing=self.spacing,
                horizontal_alignment=ft.CrossAxisAlignment.START,
            )
        return ft.Row(
            controls=[self.v_label, body],
            spacing=self.spacing,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
