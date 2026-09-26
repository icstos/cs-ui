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

.. note::
    月历本体（头部翻页 / 星期表头 / 6 × 7 日期网格 / 年月网格 / 配色 / 悬停）
    全部来自 :class:`ui.input.calendar_panel.CalendarPanel`，与
    :class:`~ui.input.datetime_input.DateTimeInput` 共用同一套像素栅格。

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

from ui.core.float_layer import use_float_layer
from ui.input.calendar_panel import (
    CAL_W,
    FIELD_HEIGHT,
    FIELD_WIDTH,
    FOOTER_H,
    PANEL_GAP,
    PANEL_H,
    TEXT_SIZE,
    WEEKDAYS,
    CalendarPanel,
    place_panel,
)
from ui.input.calendar_panel import _get_days_in_month  # noqa: F401  (兼容导入)
from ui.input.calendar_panel import _is_leap_year  # noqa: F401  (兼容导入)
from ui.input.input import Label

__all__ = ["DateInput"]


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


@ft.observable
@dataclass
class DateInput(CalendarPanel, Label):
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
    def show_clear_link(self) -> bool:
        """页脚是否显示「清除」。"""
        return self.clearable and self.value is not None

    # ------------------------------------------------------------------
    # 月历钩子（其余月历能力来自 CalendarPanel）
    # ------------------------------------------------------------------
    def _cal_bounds(self) -> tuple[datetime.date, datetime.date]:
        return self._min, self._max

    def _cal_pick(self, day: datetime.date) -> None:
        """点某一天：选中并收起。"""
        self.select(day)

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

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    @ft.component
    def ui(self) -> ft.Control:
        """构建日期选择器 UI。"""
        page = ft.context.page
        field = self._build_field(
            self._text_field(),
            ft.Icon(
                ft.Icons.CALENDAR_MONTH,
                size=18,
                color=ft.Colors.OUTLINE if self.disabled else ft.Colors.ON_SURFACE_VARIANT,
            ),
        )
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

        left, top, bottom = place_panel(
            page, self._anchor, self._field_h, CAL_W, PANEL_H
        )
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
            hole=self._hole(),
        )

        return self._with_label(body)

    # ---- 输入框 ----

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

    # ---- 面板 ----

    def _build_panel(self) -> ft.Control:
        """月历面板：头部 + 星期行 + 日期网格 + 页脚。"""
        return self._panel_shell(
            CAL_W,
            ft.Column(
                spacing=0,
                controls=[
                    self._cal_header(),
                    self._cal_body(),
                    self._divider(),
                    self._footer(),
                ],
            ),
        )

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
