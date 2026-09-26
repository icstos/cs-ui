"""日期选择器 (DateInput)。

交互模型对齐主流桌面框架的日期选择器（Element Plus / Ant Design / WinUI
``CalendarDatePicker``）：**一个输入框，点开就挂出一张月历**。

- 折叠态是一个和普通输入框等高的框：左侧格式化日期、右侧日历图标；
- 点击框体的任意位置（含图标）挂出月历面板，**面板不占布局高度、不推下方内容**；
- 月历按"上一月 / 年月标题 / 下一月"组织，点标题切到**年月网格**快速跨年跳转；
- 点某一天即选中并收起；「今天」一键回到今天，「清除」清空（可关）；
- 框内文字可直接键入，支持 ``2026-09-26`` / ``2026/9/26`` / ``2026.9.26`` /
  ``20260926`` / ``2026年9月26日``，回车提交、失焦还原；非法输入框体转红边；
- 超出 ``min_date`` / ``max_date`` / ``year_range`` 的日子以灰字禁用，不可点；
- 点面板外部（全屏透明遮罩）即收起。

.. note::
    面板挂在**页面浮层**（``page.overlay``）上，因此折叠态的高度就是整个组件
    占用布局的高度。浮层需要 ``page.render`` 这条根视图路径；若宿主用的是
    ``page.render_views``（Router 的 ``manage_views=True`` 视图栈），浮层层会被
    视图盖住，此时组件**自动降级为流内展开**（面板会占高度）。也可用
    ``float_panel=False`` 强制走流内展开。判定见 :func:`ui.core.float_layer.overlay_usable`。

.. note::
    ``TextField`` 在 flet 1.0.0 里会吞掉所有指针事件 —— 真机实测外层
    ``GestureDetector`` 完全收不到点击（``read_only`` / ``can_request_focus=False``
    同样如此，只有 ``ignore_pointers=True`` 放行）。因此面板**未展开**时把输入框
    置为 ``ignore_pointers``，让整框的点击都归外层；**展开后**再恢复响应，这样
    点框内文字就能落光标、直接键盘输入。日历图标本身不挂事件，它上面的点击
    自然冒泡到外层 —— 于是同一个图标在收起时"展开"、在展开时"收起"。

用法::

    d = DateInput(label="开始日期", value=datetime.date(2026, 9, 26))
    ...
    container = d.ui()
"""

from __future__ import annotations

import datetime
from collections.abc import Callable
from dataclasses import dataclass

import flet as ft

from ui.core.float_layer import overlay_usable, use_float_layer
from ui.input.input import Label

__all__ = ["DateInput"]

# ---------------------------------------------------------------------------
# 尺寸
# ---------------------------------------------------------------------------
FIELD_WIDTH = 240  # 输入框默认宽度
FIELD_HEIGHT = 40  # 输入框高度
FIELD_RADIUS = 8  # 输入框 / 面板圆角
FIELD_PAD_H = 10  # 输入框左右内边距

PANEL_PAD = 8  # 面板上下内边距（左右内边距同值）
PANEL_GAP = 4  # 面板与输入框之间的间距
CELL_W = 34  # 日期格宽
CELL_H = 32  # 日期格高
GRID_ROWS = 6  # 月历固定 6 行（容纳跨月的 42 天）
HEADER_H = 38  # 面板头部（翻页 + 年月标题）
WEEKDAY_H = 26  # 星期行
FOOTER_H = 34  # 面板页脚
NAV_SIZE = 26  # 翻页按钮
MONTH_H = 48  # 年月网格的单格高（4 行 48 = 192 = 6 * CELL_H）
NAV_RADIUS = 6  # 小按钮 / 日期格圆角
CELL_RADIUS = 6

PANEL_W = PANEL_PAD * 2 + CELL_W * 7 + 2  # 面板宽（含 1px 边框 ×2）
PANEL_H = (
    PANEL_PAD * 2 + 2 + HEADER_H + WEEKDAY_H + CELL_H * GRID_ROWS + 1 + FOOTER_H
)

TEXT_SIZE = 13
SMALL_SIZE = 12
LABEL_SIZE = 11

SCREEN_MARGIN = 8  # 面板与窗口边缘的最小间距

# ---------------------------------------------------------------------------
# 配色（全部走主题色，明暗主题下都可用）
# ---------------------------------------------------------------------------
HOVER_BG = ft.Colors.with_opacity(0.06, ft.Colors.ON_SURFACE)  # 悬停底色
TODAY_BG = ft.Colors.with_opacity(0.10, ft.Colors.PRIMARY)  # "今天"淡色底
SELECTED_BG = ft.Colors.PRIMARY  # 选中日填色
DISABLED_FG = ft.Colors.with_opacity(0.38, ft.Colors.ON_SURFACE)  # 越界禁用字色

#: 星期标签，索引与 ``datetime.date.weekday()`` 一致：0 = 周一 … 6 = 周日。
WEEKDAYS = ("一", "二", "三", "四", "五", "六", "日")


# ---------------------------------------------------------------------------
# 纯函数工具（``datetime_input`` 复用 ``_get_days_in_month``）
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


def _parse_date(text: str | None) -> datetime.date | None:
    """尽力把用户敲的字符串解析成日期，失败返回 ``None``。

    支持 ``2026-09-26`` / ``2026/9/26`` / ``2026.9.26`` / ``20260926`` /
    ``2026年9月26日``（也接受末尾带不带"日"、各部分补不补零）。
    """
    s = (text or "").strip()
    if not s:
        return None
    for ch in ("年", "月", "日", "/", ".", " "):
        s = s.replace(ch, "-")
    parts = [p for p in s.split("-") if p]
    try:
        if len(parts) == 1 and len(parts[0]) == 8 and parts[0].isdigit():
            return datetime.date(
                int(parts[0][:4]), int(parts[0][4:6]), int(parts[0][6:])
            )
        if len(parts) == 3:
            return datetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
    except ValueError:
        return None
    return None


def _truthy(value: object) -> bool:
    """把 hover 事件载荷归一成布尔（可能是 bool，也可能是 ``"true"`` 字符串）。"""
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


@ft.observable
@dataclass
class DateInput(Label):
    """日期选择器：输入框 + 悬浮月历。

    Args:
        value: 当前日期。``None`` 表示未选择（显示 ``placeholder``）。
        min_date: 可选下界（含当天）。``None`` 时取 ``year_range`` 的起始年 1 月 1 日。
        max_date: 可选上界（含当天）。``None`` 时取 ``year_range`` 的结束年 12 月 31 日。
        year_range: 可选的年份范围，默认 ``(1900, 2100)``。
        display_format: 框内日期的 ``strftime`` 格式，默认 ``"%Y-%m-%d"``。
        placeholder: 未选择时的占位文本。
        first_day_weekday: 每周首日，索引与 ``datetime.date.weekday()`` 相同
            —— ``0`` = 周一（默认）、``6`` = 周日。
        weekday_labels: 7 个星期标签，索引同上（``"一"`` 对应周一）。
        width: 输入框宽度，默认 240。
        height: 输入框高度，默认 40。
        clearable: 是否允许清空（框内 × 与页脚「清除」），默认 True。
        disabled: 是否禁用。
        is_open: 面板是否展开（运行期状态，可代码控制）。
        float_panel: 面板是否走页面浮层。``None``（默认）表示自动：浮层可用时
            悬挂，否则退化为流内展开。``True`` / ``False`` 强制指定。
        on_change: 日期变化回调，接收最新的 ``datetime.date | None``。
    """

    value: datetime.date | None = None
    min_date: datetime.date | None = None
    max_date: datetime.date | None = None
    year_range: tuple[int, int] = (1900, 2100)
    display_format: str = "%Y-%m-%d"
    placeholder: str = "请选择日期"
    first_day_weekday: int = 0
    weekday_labels: tuple[str, ...] = WEEKDAYS
    width: int | float = FIELD_WIDTH
    height: int | float = FIELD_HEIGHT
    clearable: bool = True
    disabled: bool = False
    is_open: bool = False
    float_panel: bool | None = None
    on_change: Callable[[datetime.date | None], None] | None = None

    def __post_init__(self) -> None:
        # 运行期状态：下划线开头 => 不参与序列化，变更后靠 notify() 重绘。
        self._hover: str | None = None  # 当前悬停元素的 key
        self._anchor: tuple[float, float] | None = None  # 输入框左上角页面坐标
        self._field_w: float = float(self.width)  # 输入框实测宽（on_size_change 上报）
        self._field_h: float = float(self.height)
        self._text: str | None = None  # 用户正在输入的原文；None = 显示格式化值
        self._invalid: bool = False  # 键入内容非法（框体转红边）
        self._emitted: datetime.date | None = self.value  # 上次广播出去的值
        today = datetime.date.today()
        self._view_year: int = (self.value or today).year  # 面板显示的年份
        self._view_month: int = (self.value or today).month  # 面板显示的月份
        self._mode: str = "day"  # "day" = 月历， "month" = 年月网格

    # ------------------------------------------------------------------
    # 公开操作
    # ------------------------------------------------------------------
    def open(self, focus: datetime.date | None = None) -> None:
        """展开面板；``focus`` 指定面板先跳到的月份（默认跟随当前值 / 今天）。"""
        if self.disabled or self.is_open:
            return
        target = focus or self.value or datetime.date.today()
        self._view_year, self._view_month = target.year, target.month
        self._mode = "day"
        self._invalid = False
        self.is_open = True
        self.notify()  # type: ignore[attr-defined]

    def close(self) -> None:
        """收起面板（放弃未提交的键入内容）。"""
        if not self.is_open:
            return
        self.is_open = False
        self._hover = None
        self._text = None
        self.notify()  # type: ignore[attr-defined]

    def toggle_open(self) -> None:
        """展开 / 收起。"""
        self.close() if self.is_open else self.open()

    def clear(self) -> None:
        """清空已选日期。"""
        if self.value is None:
            return
        self.value = None
        self._text = None
        self._invalid = False
        self._emit()

    def select(self, value: datetime.date, close: bool = True) -> None:
        """选中某个日期；``close=False`` 时保持面板展开。"""
        if not self._accepts(value):
            return
        self.value = value
        self._text = None
        self._invalid = False
        self._view_year, self._view_month = value.year, value.month
        self._emit()
        if close:
            self.close()

    # ------------------------------------------------------------------
    # 只读属性
    # ------------------------------------------------------------------
    @property
    def display_text(self) -> str:
        """当前日期的格式化文本，空值返回空串，便于表单提交 / 日志。"""
        return "" if self.value is None else self.value.strftime(self.display_format)

    @property
    def _min(self) -> datetime.date:
        """可选下界。"""
        if self.min_date is not None:
            return self.min_date
        lo, hi = sorted(self.year_range)
        return datetime.date(lo, 1, 1)

    @property
    def _max(self) -> datetime.date:
        """可选上界。"""
        if self.max_date is not None:
            return self.max_date
        lo, hi = sorted(self.year_range)
        return datetime.date(hi, 12, 31)

    @property
    def _fg(self) -> ft.ColorValue:
        """框内文字色：禁用时压灰。"""
        return ft.Colors.OUTLINE if self.disabled else ft.Colors.ON_SURFACE

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------
    def _accepts(self, day: datetime.date) -> bool:
        """``day`` 是否落在可选范围内。"""
        return self._min <= day <= self._max

    def _emit(self) -> None:
        """广播变化。

        ``on_change`` **按值变化去重**：同一个日期只回调一次，重复提交 / 点到
        已选中的那天 / 键入与当前值相同的文本都不会重复触发外部回调。
        """
        if self.value != self._emitted:
            self._emitted = self.value
            if self.on_change:
                self.on_change(self.value)
        self.notify()  # type: ignore[attr-defined]

    def _hover_key(self, key: str, hovering: bool) -> None:
        """更新悬停元素（同一 key 重复进入 / 离开时提前返回，避免抖动）。"""
        if (self._hover == key) == hovering:
            return
        self._hover = key if hovering else None
        self.notify()  # type: ignore[attr-defined]

    def _shift_month(self, delta: int) -> None:
        """面板月份 ±N（自动跨年）。"""
        y, m = self._view_year, self._view_month + delta
        y += (m - 1) // 12
        self._view_year, self._view_month = y, (m - 1) % 12 + 1
        self._hover = None
        self.notify()  # type: ignore[attr-defined]

    def _shift_year(self, delta: int) -> None:
        """面板年份 ±N（年月网格视图用）。"""
        self._view_year += delta
        self._hover = None
        self.notify()  # type: ignore[attr-defined]

    def _toggle_mode(self) -> None:
        """月历 ⇄ 年月网格。"""
        self._mode = "month" if self._mode == "day" else "day"
        self._hover = None
        self.notify()  # type: ignore[attr-defined]

    def _select_month(self, month: int) -> None:
        """在年月网格里选中某月，回到月历。"""
        self._view_month = month
        self._mode = "day"
        self._hover = None
        self.notify()  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    @ft.component
    def ui(self) -> ft.Control:
        """构建日期选择器 UI。"""
        page = ft.context.page
        field = self._build_field()
        panel = self._build_panel()
        floating = self._should_float(page)

        if floating:
            # 面板在浮层里，布局只占折叠态的高度。
            body: ft.Control = field
        elif self.is_open and not self.disabled:
            # 降级：面板流内展开，下方内容随之下移。
            body = ft.Column(controls=[field, panel], spacing=PANEL_GAP)
        else:
            body = field

        left, top, bottom = self._panel_origin(page)
        # 无条件调用（hook 顺序必须稳定）；visible=False 时浮层自动移除。
        # hole 把输入框从遮罩里挖出来：展开后还要能点框内文字落光标。
        use_float_layer(
            page=page,
            visible=floating and self.is_open and not self.disabled,
            left=left,
            top=top,
            bottom=bottom,
            content=panel,
            on_dismiss=self.close,
            hole=None
            if self._anchor is None
            else (self._anchor[0], self._anchor[1], self._field_w, self._field_h),
        )

        return self._with_label(body)

    # ---- 浮层定位 ----

    def _should_float(self, page: ft.Page) -> bool:
        """面板是否走页面浮层。"""
        if self.float_panel is not None:
            return self.float_panel
        return overlay_usable(page)

    def _panel_origin(
        self, page: ft.Page
    ) -> tuple[float, float | None, float | None]:
        """面板定位：返回 ``(left, top, bottom)``，``top`` / ``bottom`` 二选一。

        默认从输入框下沿往下弹；下方放不下就向上翻转，改用 ``bottom`` 锚定
        —— 这样面板多高都能自动贴住输入框上沿（``top`` 方式需要预先知道面板
        高度，估算误差会变成一条可见的缝）。左右方向同样做边界收拢。
        """
        ax, ay = self._anchor or (0.0, 0.0)
        page_w = float(getattr(page, "width", 0) or 0)
        page_h = float(getattr(page, "height", 0) or 0)

        left = ax
        if page_w and left + PANEL_W > page_w - SCREEN_MARGIN:
            left = max(SCREEN_MARGIN, page_w - PANEL_W - SCREEN_MARGIN)

        top = ay + self._field_h + PANEL_GAP
        if page_h and top + PANEL_H > page_h - SCREEN_MARGIN:
            if ay - PANEL_H - PANEL_GAP >= SCREEN_MARGIN:
                return left, None, page_h - ay + PANEL_GAP
        return left, top, None

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

    # ---- 输入框 ----

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

    def _on_field_resize(self, e: ft.LayoutSizeChangeEvent) -> None:
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

    def _on_text_change(self, e: ft.ControlEvent) -> None:
        """键入过程中即时解析：合法就同步 ``value`` 并广播，全程不打断输入。

        "合法就落地"是和 Element Plus 一致的模型 —— 敲到哪算到哪，失焦不会丢；
        敲到非法内容时保持上一个合法值，框体不标红（还在输入中，不算错）。
        """
        text = e.data or ""
        self._text = text
        self._invalid = False
        parsed = _parse_date(text)
        if parsed is not None and self._accepts(parsed) and parsed != self.value:
            self.value = parsed
            self._emit()
            return
        self.notify()  # type: ignore[attr-defined]

    def _on_text_submit(self, e: ft.ControlEvent) -> None:
        """回车提交：合法则选中并收起，非法则原样还原并标红。"""
        parsed = _parse_date(self._text if self._text is not None else self.display_text)
        self._text = None
        if parsed is not None and self._accepts(parsed):
            self._invalid = False
            self.select(parsed)
            return
        if self.value is None:
            # 本来就是空的，敲了半截又回车 —— 没东西可还原，也不算错。
            self._invalid = False
            self.notify()  # type: ignore[attr-defined]
            return
        self._invalid = True
        self.notify()  # type: ignore[attr-defined]

    def _on_text_blur(self, e: ft.ControlEvent) -> None:
        """失焦即放弃未提交的键入（回到格式化值）。"""
        if self._text is None:
            return
        self._text = None
        self.notify()  # type: ignore[attr-defined]

    def _build_field(self) -> ft.Control:
        """折叠态输入框：日期文本 + 可选 × + 日历图标。"""
        if self.disabled:
            border_color: ft.ColorValue = ft.Colors.OUTLINE_VARIANT
        elif self._invalid:
            border_color = ft.Colors.ERROR
        elif self.is_open:
            border_color = ft.Colors.PRIMARY
        else:
            border_color = ft.Colors.OUTLINE_VARIANT

        controls: list[ft.Control] = [ft.Container(expand=True, content=self._text_field())]
        if self._show_clear():
            controls.append(self._clear_button())
        controls.append(
            ft.Icon(
                ft.Icons.CALENDAR_MONTH,
                size=18,
                color=ft.Colors.OUTLINE if self.disabled else ft.Colors.ON_SURFACE_VARIANT,
            )
        )

        box = ft.Container(
            width=self.width,
            height=self.height,
            bgcolor=ft.Colors.SURFACE_CONTAINER
            if self.disabled
            else ft.Colors.SURFACE,
            border=ft.Border.all(1, border_color),
            border_radius=ft.BorderRadius.all(FIELD_RADIUS),
            padding=ft.Padding.symmetric(horizontal=FIELD_PAD_H),
            on_size_change=self._on_field_resize,
            size_change_interval=0,
            content=ft.Row(
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=controls,
            ),
        )
        if self.disabled:
            return box
        # 收起时整框都是"可点开日历"，展开后交回输入框自己的 I 形光标。
        return ft.GestureDetector(
            on_tap=self._on_field_tap,
            mouse_cursor=None if self.is_open else ft.MouseCursor.CLICK,
            content=box,
        )

    def _text_field(self) -> ft.Control:
        """框内文本。收起态 ``ignore_pointers`` —— 让点击穿透到外层手势。"""
        return ft.TextField(
            value=self._text if self._text is not None else self.display_text,
            border=ft.NoInputBorder(),
            filled=False,
            dense=True,
            text_size=TEXT_SIZE,
            color=self._fg,
            content_padding=ft.Padding.symmetric(vertical=6),
            hint_text=self.placeholder,
            hint_style=ft.TextStyle(size=TEXT_SIZE, color=ft.Colors.OUTLINE),
            keyboard_type=ft.KeyboardType.DATETIME,
            read_only=self.disabled,
            # 关键：收起（或禁用）时不吃指针事件，否则外层 GestureDetector 拿不到点击。
            ignore_pointers=self.disabled or not self.is_open,
            on_change=None if self.disabled else self._on_text_change,
            on_submit=None if self.disabled else self._on_text_submit,
            on_blur=None if self.disabled else self._on_text_blur,
        )

    def _show_clear(self) -> bool:
        """是否显示框内 ×：可清空、未禁用、且当前有值。"""
        return self.clearable and not self.disabled and self.value is not None

    def _clear_button(self) -> ft.Control:
        """框内清空按钮。

        用 ``GestureDetector`` 而不是 ``Container.on_click``：后者在内层时会被
        外层 ``GestureDetector`` 抢走（真机实测，点 × 变成开合面板），同类型的
        tap 识别器才会按"内层优先"决出胜者。
        """
        hovered = self._hover == "clear"
        return ft.GestureDetector(
            on_tap=lambda _e: self.clear(),
            content=ft.Container(
                padding=ft.Padding.all(3),
                border_radius=ft.BorderRadius.all(4),
                bgcolor=HOVER_BG if hovered else None,
                on_hover=lambda e: self._hover_key("clear", _truthy(e.data)),
                tooltip=ft.Tooltip(message="清除"),
                content=ft.Icon(ft.Icons.CLOSE, size=14, color=ft.Colors.OUTLINE),
            ),
        )

    # ---- 面板 ----

    def _build_panel(self) -> ft.Control:
        """月历面板：头部 + 星期行 + 日期网格 + 页脚。"""
        if self._mode == "month":
            body: ft.Control = self._month_grid()
        else:
            body = ft.Column(
                spacing=0,
                controls=[self._weekday_row(), self._day_grid()],
            )
        return ft.Container(
            width=PANEL_W,
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
            content=ft.Column(
                spacing=0,
                controls=[
                    self._header(),
                    body,
                    ft.Container(height=1, bgcolor=ft.Colors.OUTLINE_VARIANT),
                    self._footer(),
                ],
            ),
        )

    def _header(self) -> ft.Control:
        """面板头部：翻页箭头 + 可点击的年月标题（点它切年月网格）。"""
        if self._mode == "month":
            title = f"{self._view_year} 年"
            unit = "年"
        else:
            title = f"{self._view_year} 年 {self._view_month} 月"
            unit = "月"
        prev = (lambda: self._shift_year(-1)) if self._mode == "month" else (
            lambda: self._shift_month(-1)
        )
        nxt = (lambda: self._shift_year(1)) if self._mode == "month" else (
            lambda: self._shift_month(1)
        )

        hovered = self._hover == "title"
        title_btn = ft.Container(
            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
            border_radius=ft.BorderRadius.all(NAV_RADIUS),
            bgcolor=HOVER_BG if hovered else None,
            on_click=lambda _e: self._toggle_mode(),
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
        """面板里的方形图标按钮。"""
        hovered = self._hover == key
        return ft.Container(
            width=NAV_SIZE,
            height=NAV_SIZE,
            alignment=ft.Alignment.CENTER,
            border_radius=ft.BorderRadius.all(NAV_RADIUS),
            bgcolor=HOVER_BG if hovered else None,
            on_click=lambda _e: on_click(),
            on_hover=lambda e, k=key: self._hover_key(k, _truthy(e.data)),
            tooltip=ft.Tooltip(message=tooltip),
            content=ft.Icon(icon, size=18, color=ft.Colors.ON_SURFACE_VARIANT),
        )

    # -- 月历 --

    def _weekday_sequence(self) -> list[str]:
        """按 ``first_day_weekday`` 旋转后的星期标签（长度恒为 7）。

        ``WEEKDAYS[i]`` 对应 ``weekday() == i``；首列要放 ``first_day_weekday``，
        所以序列从该下标开始绕一圈。
        """
        labels = [str(x) for x in self.weekday_labels][:7] or list(WEEKDAYS)
        offset = int(self.first_day_weekday) % 7
        return labels[offset:] + labels[:offset]

    def _weekday_row(self) -> ft.Control:
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
                    for label in self._weekday_sequence()
                ],
            ),
        )

    def _grid_start(self) -> datetime.date:
        """网格第一格对应的日期（可能落在上月）。"""
        first = datetime.date(self._view_year, self._view_month, 1)
        offset = (first.weekday() - int(self.first_day_weekday)) % 7
        return first - datetime.timedelta(days=offset)

    def _day_grid(self) -> ft.Control:
        """6 × 7 日期网格，固定 6 行 —— 面板高度不随月份跳动。"""
        start = self._grid_start()
        rows: list[ft.Control] = []
        for r in range(GRID_ROWS):
            rows.append(
                ft.Row(
                    spacing=0,
                    controls=[
                        self._day_cell(start + datetime.timedelta(days=r * 7 + c))
                        for c in range(7)
                    ],
                )
            )
        return ft.Container(
            height=CELL_H * GRID_ROWS,
            content=ft.Column(spacing=0, controls=rows),
        )

    def _day_cell(self, day: datetime.date) -> ft.Control:
        """单个日期格：选中填主色、"今天"淡色底、越界灰字禁用。"""
        key = day.isoformat()
        in_month = (day.year, day.month) == (self._view_year, self._view_month)
        enabled = self._accepts(day)
        selected = self.value == day and enabled
        is_today = day == datetime.date.today()
        hovered = enabled and self._hover == key

        if selected:
            bgcolor: ft.ColorValue | None = SELECTED_BG
            color: ft.ColorValue = ft.Colors.ON_PRIMARY
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
            on_click=None if not enabled else (lambda _e, d=day: self.select(d)),
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

    # -- 年月网格 --

    def _month_grid(self) -> ft.Control:
        """4 × 3 年月网格，高度与月历区一致（面板不跳动）。"""
        span = WEEKDAY_H + CELL_H * GRID_ROWS
        pad = max(0, (span - MONTH_H * 4) // 2)
        rows: list[ft.Control] = []
        for r in range(4):
            rows.append(
                ft.Row(
                    spacing=0,
                    expand=True,
                    controls=[self._month_cell(r * 3 + c + 1) for c in range(3)],
                )
            )
        return ft.Container(
            height=span,
            padding=ft.Padding.symmetric(vertical=pad),
            content=ft.Column(spacing=0, expand=True, controls=rows),
        )

    def _month_cell(self, month: int) -> ft.Control:
        """年份网格里的单个月份。"""
        key = f"m{month}"
        value = self.value
        selected = (
            value is not None
            and value.year == self._view_year
            and value.month == month
        )
        enabled = self._month_enabled(month)
        hovered = enabled and self._hover == key

        if selected:
            bgcolor: ft.ColorValue | None = SELECTED_BG
            color: ft.ColorValue = ft.Colors.ON_PRIMARY
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
            on_click=None if not enabled else (lambda _e, m=month: self._select_month(m)),
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

    def _month_enabled(self, month: int) -> bool:
        """该月的任意一天在可选范围内即可选。"""
        first = datetime.date(self._view_year, month, 1)
        last = datetime.date(
            self._view_year, month, _get_days_in_month(self._view_year, month)
        )
        return last >= self._min and first <= self._max

    # -- 页脚 --

    def _footer(self) -> ft.Control:
        """页脚：左侧「今天」，右侧「清除」（有值且可清空时）。"""
        controls: list[ft.Control] = [
            self._link_button(
                "today",
                "今天",
                lambda: self.select(datetime.date.today()),
                enabled=self._accepts(datetime.date.today()),
            ),
            ft.Container(expand=True),
        ]
        if self.show_clear_link:
            controls.append(self._link_button("clear", "清除", self.clear))
        return ft.Container(
            height=FOOTER_H,
            padding=ft.Padding.only(left=2, right=2),
            content=ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=controls
            ),
        )

    @property
    def show_clear_link(self) -> bool:
        """页脚是否显示「清除」。"""
        return self.clearable and self.value is not None

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
        hovered = self._hover == key
        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=6, vertical=4),
            border_radius=ft.BorderRadius.all(CELL_RADIUS),
            bgcolor=HOVER_BG if hovered else None,
            on_click=lambda _e: on_click(),
            on_hover=lambda e, k=key: self._hover_key(k, _truthy(e.data)),
            content=ft.Text(label, size=SMALL_SIZE, color=ft.Colors.PRIMARY),
        )


@ft.component
def App():
    """DateInput 组件运行示例。"""
    basic = DateInput(
        label="开始日期",
        is_required=True,
        value=datetime.date(2026, 9, 26),
        on_change=lambda d: print(f"[DateInput] 选中 {d}"),
    )
    empty = DateInput(label="结束日期", is_vertical=True, placeholder="未选择")
    bounded = DateInput(
        label="活动周期",
        value=datetime.date(2026, 9, 10),
        min_date=datetime.date(2026, 9, 5),
        max_date=datetime.date(2026, 9, 20),
    )
    sunday_first = DateInput(
        label="周日起头",
        value=datetime.date(2026, 2, 28),
        first_day_weekday=6,
        display_format="%Y/%m/%d",
    )
    frozen = DateInput(
        label="只读",
        value=datetime.date(2026, 1, 1),
        disabled=True,
        clearable=False,
    )

    return ft.Column(
        controls=[
            ft.Text("DateInput 日期选择器", size=20, weight=ft.FontWeight.BOLD),
            ft.Text(
                "点框体挂出月历（悬浮、不推下方内容），点标题切年月网格，"
                "框内可直接键入 2026-09-26 / 20260926 / 2026年9月26日",
                size=13,
                color="#6b7280",
            ),
            ft.Divider(),
            basic.ui(),
            ft.Divider(),
            empty.ui(),
            ft.Divider(),
            bounded.ui(),
            ft.Divider(),
            sunday_first.ui(),
            ft.Divider(),
            frozen.ui(),
            ft.Divider(),
            ft.Button(
                content="打印当前值",
                on_click=lambda _: print(
                    f"{basic.value} / {empty.value} / {bounded.value} / "
                    f"{sunday_first.value} / {frozen.value}"
                ),
            ),
        ],
        spacing=14,
    )


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
