"""数字输入框 (NumberInput)。

桌面端的数字输入框有三层需求，本组件按「打字优先、按钮辅助」的顺序处理：

1. **打字**：只放行数字 / 一个负号 / 一个小数点；结构不合法（第二个小数点、
   负号跑到中间）时**保留上一次可接受的文本**，不闪红、不吞字。失焦或回车时统一
   规整 —— 按 ``precision`` 舍入、按 ``min`` / ``max`` 收口。
2. **步进**：``step`` 是加减的粒度，``step_strictly`` 让取值只落在步长网格上；
   到界的那一侧按钮自动变灰不可点，而不是"点了没反应"。
3. **读数**：``precision`` 固定小数位（``1`` + ``precision=2`` 显示 ``1.00``），
   ``prefix`` / ``suffix`` 挂货币符号与单位，单位只做展示、不参与编辑。

按钮布局对齐 layui-vue 的 ``input-number``：

* ``controls_position="both"``（默认）—— 减号在左、加号在右，与文本平铺一行，
  横排表单里左右对称、视觉重量最稳；
* ``controls_position="right"`` —— 两个箭头在右侧**上下堆叠**，只占一个按钮宽度，
  适合表格单元格和窄容器；
* ``controls_position="none"`` —— 不显示按钮，只保留数字校验与格式化。

数值运算全程走 :class:`decimal.Decimal`，``0.1 + 0.2`` 不会变成
``0.30000000000000004`` —— 金额、税率、百分比这类字段不需要调用方再兜一层舍入。

用法::

    qty = NumberInput(label="数量", value=1, min=1, max=99)
    rate = NumberInput(
        label="税率", value=0.13, step=0.01, precision=2, suffix="%",
        controls_position="right",
    )
    ...
    container = qty.ui()
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

import flet as ft

from ui.core.doc import Api, Example, Spec, info, run, tip, warn
from ui.core.tokens import FONT_SIZE, RADIUS, overlay
from ui.input.input import Label

__all__ = ["NumberInput"]

# ---------------------------------------------------------------------------
# 尺寸
# ---------------------------------------------------------------------------
FIELD_WIDTH = 160  # 默认宽度
FIELD_RADIUS = RADIUS["lg"]  # 与 DateInput / DateTimeInput 的输入框同圆角

#: 每档尺寸的像素栅格：外框高度 / 字号 / 按钮宽度 / 图标大小
SIZE_SPECS: dict[str, dict[str, int]] = {
    "sm": {"height": 28, "text": FONT_SIZE["small"], "button": 26, "icon": 14},
    "md": {"height": 36, "text": FONT_SIZE["body"], "button": 32, "icon": 16},
    "lg": {"height": 44, "text": FONT_SIZE["subtitle"], "button": 38, "icon": 18},
}

#: ``controls_position`` 的合法取值
CONTROLS_POSITIONS: tuple[str, ...] = ("both", "right", "none")

# ---------------------------------------------------------------------------
# 配色：全部走主题角色，明暗主题自动跟随
# ---------------------------------------------------------------------------
HOVER_BG = overlay(0.08)  # 按钮悬停底色（M3 的悬停档）
DISABLED_FG = ft.Colors.with_opacity(0.38, ft.Colors.ON_SURFACE)  # 禁用字色 / 到界图标

# ---------------------------------------------------------------------------
# 文本判定
# ---------------------------------------------------------------------------
#: 键入过程中**允许**出现的形状：``-`` / ``1.`` / ``.5`` 都是合法中间态，
#: 因为用户必然要经过它们；真正的合法性在提交时判定。
_EDITING = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d*)?$")

#: 提交时抹掉的噪声：千分位逗号、货币符号、百分号、空格
_NOISE = re.compile(r"[^0-9.+-]")


def _dec(value: float | Decimal | str | None) -> Decimal | None:
    """把任意输入收敛成 ``Decimal``；无法解析时返回 ``None``。

    浮点走 ``Decimal(str(x))`` 而不是 ``Decimal(float)`` —— 后者会把二进制误差
    原样搬进来（``Decimal(0.1)`` 是 ``0.1000000000000000055511151231257827``）。
    字符串则先抹掉 ``1,234.50`` / ``¥99`` / ``12 %`` 这类噪声，粘贴即用。
    """
    if value is None or isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return Decimal(str(value))
    text = _NOISE.sub("", str(value).strip())
    if text in ("", "-", "+", ".", "-.", "+."):
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def _step_decimals(step: Decimal) -> int:
    """步长自带的小数位数（``0.01`` → 2、``1`` → 0），用作 ``precision`` 的默认值。"""
    exponent = step.normalize().as_tuple().exponent
    return max(0, -int(exponent)) if isinstance(exponent, int) else 0


def _truthy(value: object) -> bool:
    """把 hover 事件载荷归一成布尔（可能是 ``True``，也可能是 ``"true"``）。"""
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


@ft.observable
@dataclass
class NumberInput(Label):
    """数字输入框：带步进按钮、精度、单位与范围约束。

    Args:
        value: 当前值。``None`` 表示空（显示 ``hint_text``）。
        min: 下界（含）。``None`` 表示不限。
        max: 上界（含）。``None`` 表示不限。
        step: 加减步长，默认 ``1``；``precision`` 未指定时由它推断小数位。
        precision: 保留小数位。``None``（默认）跟随 ``step``：``step=0.01`` → 2 位，
            ``step=1`` → 0 位；显式给值可锁定显示位数（不影响 ``step``）。
        step_strictly: 只允许取步长的整数倍（以 ``min`` 为起点，未设 ``min`` 则从 0
            起算），键入的其它值会在提交时被吸附到最近的网格点。
        prefix: 框内左侧的固定文案，如货币符号 ``¥``。
        suffix: 框内右侧的固定文案，如 ``%`` / ``时`` / ``kg``。
        controls_position: 按钮布局，``"both"``（左右各一）/ ``"right"``（右侧上下
            堆叠）/ ``"none"``（不显示）。
        size: 尺寸档位，``"sm"`` / ``"md"`` / ``"lg"``，默认 ``"md"``。
        width: 整个控件宽度，默认 160。
        hint_text: 值为 ``None`` 时的占位文本。
        read_only: 只能点按钮、不能键入（layui 的 ``disabled-input``）。
        disabled: 整体禁用（按钮与输入都不可用）。
        on_change: 值变化回调，入参是最新的 ``int`` / ``float`` / ``None``。
            按值去重：同一个值不会重复回调。
    """

    value: int | float | Decimal | str | None = 0
    min: int | float | Decimal | None = None
    max: int | float | Decimal | None = None
    step: int | float | Decimal = 1
    precision: int | None = None
    step_strictly: bool = False
    prefix: str | None = None
    suffix: str | None = None
    controls_position: str = "both"
    size: str = "md"
    width: int | float = FIELD_WIDTH
    hint_text: str | None = None
    read_only: bool = False
    disabled: bool = False
    on_change: Callable[[int | float | None], None] | None = None

    def __post_init__(self) -> None:
        self._step = _dec(self.step) or Decimal(1)
        if self._step <= 0:
            self._step = Decimal(1)
        self._precision = (
            _step_decimals(self._step)
            if self.precision is None
            else max(0, int(self.precision))
        )
        low, high = _dec(self.min), _dec(self.max)
        if low is not None and high is not None and low > high:
            low, high = high, low
        self._low, self._high = low, high

        # 运行期状态（下划线开头 => 不参与序列化，变更后靠 notify() 重绘）
        self._text: str | None = None  # 正在输入的原文；None = 显示格式化值
        self._hover: str | None = None  # 当前悬停元素的 key
        self._focused: bool = False
        self.value = self._out(self._normalize(_dec(self.value)))
        self._emitted = self.value

    # ------------------------------------------------------------------
    # 公开操作
    # ------------------------------------------------------------------
    @property
    def display_text(self) -> str:
        """按 ``precision`` 格式化后的文本，供表单提交 / 日志使用。"""
        current = _dec(self.value)
        return "" if current is None else f"{current:.{self._precision}f}"

    def commit(self) -> None:
        """提交正在输入的文本（失焦 / 回车时自动调用，也可代码触发）。"""
        if self._text is None:
            return
        text, self._text = self._text, None
        if text.strip() == "":
            self._apply(None)
        else:
            parsed = _dec(text)
            # 解析不出来（只敲了个负号之类）就退回上一个值，不把展示位清空
            self._apply(
                self._normalize(parsed) if parsed is not None else _dec(self.value)
            )

    def set_value(self, value: float | Decimal | str | None) -> None:
        """从外部设值：规整（范围 / 精度）后落值。

        与直接写 ``value`` 的区别是这个入口接受字符串、会做规整，而且**值没变时
        不触发重绘** —— 宿主每次渲染都调它也不会掉帧。
        """
        target = self._normalize(_dec(value))
        if self._out(target) == self.value:
            return  # 值没变：连正在输入的原文都不动（宿主每次渲染都会调到这里）
        self._text = None
        self._apply(target)

    def increase(self) -> None:
        """加一个 ``step``。"""
        self._bump(1)

    def decrease(self) -> None:
        """减一个 ``step``。"""
        self._bump(-1)

    # ------------------------------------------------------------------
    # 取值与规整
    # ------------------------------------------------------------------
    def _out(self, value: Decimal | None) -> int | float | None:
        """``Decimal`` → 对外的 ``int`` / ``float``：精度 0 就老老实实给整数。"""
        if value is None:
            return None
        return int(value) if self._precision == 0 else float(value)

    def _normalize(self, value: Decimal | None) -> Decimal | None:
        """吸附网格 → 收口到 ``[min, max]`` → 舍入到 ``precision``。

        顺序不能反：先吸附再收口，边界值才一定落在网格上；最后才舍入，避免
        两次舍入把 ``0.05`` 抬成 ``0.1``。
        """
        if value is None:
            return None
        if self.step_strictly:
            base = self._low if self._low is not None else Decimal(0)
            ticks = ((value - base) / self._step).to_integral_value(ROUND_HALF_UP)
            value = base + ticks * self._step
        if self._low is not None and value < self._low:
            value = self._low
        if self._high is not None and value > self._high:
            value = self._high
        quantum = Decimal(1).scaleb(-self._precision)
        return value.quantize(quantum, rounding=ROUND_HALF_UP)

    def _within(self, value: Decimal) -> bool:
        """``value`` 是否已经落在闭区间内（键入过程中用来判断能不能实时回读）。"""
        return (self._low is None or value >= self._low) and (
            self._high is None or value <= self._high
        )

    def _apply(self, value: Decimal | None) -> None:
        """落值并广播；``value`` 已规整过。"""
        self.value = self._out(value)
        if self.value != self._emitted:
            self._emitted = self.value
            if self.on_change:
                self.on_change(self.value)
        self.notify()  # type: ignore[attr-defined]

    def _bump(self, sign: int) -> None:
        """按 ``step`` 步进；到界后不动（按钮此刻本就该是灰的）。"""
        if self.disabled:
            return
        self.commit()  # 先把半截输入落定，再基于它加减
        current = _dec(self.value)
        nxt = self._normalize(
            (current if current is not None else Decimal(0)) + sign * self._step
        )
        if nxt != current:
            self._apply(nxt)
        else:
            self.notify()  # type: ignore[attr-defined]

    def _at_bound(self, sign: int) -> bool:
        """该方向是否已经到头（到头则按钮禁用）。"""
        current = _dec(self.value)
        if current is None:
            return False
        if sign > 0:
            return self._high is not None and current >= self._high
        return self._low is not None and current <= self._low

    def _can_step(self, sign: int) -> bool:
        return (
            not self.disabled
            and self.controls_position != "none"
            and not self._at_bound(sign)
        )

    # ------------------------------------------------------------------
    # 事件
    # ------------------------------------------------------------------
    def _hover_key(self, key: str, hovering: bool) -> None:
        """更新悬停元素（进入 / 离开重复触发时提前返回，避免抖动重绘）。"""
        if (self._hover == key) == hovering:
            return
        self._hover = key if hovering else None
        self.notify()  # type: ignore[attr-defined]

    def _on_text_change(self, e: ft.ControlEvent) -> None:
        """键入：结构合法就记住原文并把合法数值实时回读给外部。

        这里**不规整**用户正在敲的字（不补零、不夹到范围内、不改小数点），
        否则光标会跳。真正的收口留给 :meth:`commit`。
        """
        text = e.data or ""
        if not _EDITING.match(text):
            # 第二个小数点 / 负号跑到中间 —— 重建一次，输入框取回上一个可接受文本
            self.notify()  # type: ignore[attr-defined]
            return
        self._text = text
        parsed = _dec(text)
        if parsed is not None and self._within(parsed):
            self.value = self._out(parsed)
            if self.value != self._emitted:
                self._emitted = self.value
                if self.on_change:
                    self.on_change(self.value)
        self.notify()  # type: ignore[attr-defined]

    def _on_text_submit(self, e: ft.ControlEvent) -> None:
        """回车：提交并规整。"""
        self.commit()

    def _on_text_blur(self, e: ft.ControlEvent) -> None:
        """失焦：提交并规整（这也是"点了按钮再回来"的收口点）。"""
        self._focused = False
        editing = self._text is not None
        self.commit()
        if not editing:
            # commit 在"没有正在输入的原文"时直接返回，不会 notify；
            # 少了这一次重绘，聚焦态的主色描边会一直留在已经失焦的框上。
            self.notify()  # type: ignore[attr-defined]

    def _on_text_focus(self, e: ft.ControlEvent) -> None:
        self._focused = True
        self.notify()  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    @ft.component
    def ui(self) -> ft.Control:
        """构建数字输入框（含标签排版）。"""
        return self._with_label(self._box())

    def _with_label(self, body: ft.Control) -> ft.Control:
        """按 ``is_vertical`` 把标签摆到框体左侧 / 上方。"""
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
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _box(self) -> ft.Control:
        """外框：描边 + 圆角 + 内嵌「按钮 / 文本 / 按钮」。"""
        spec = SIZE_SPECS.get(self.size, SIZE_SPECS["md"])
        position = (
            self.controls_position
            if self.controls_position in CONTROLS_POSITIONS
            else "both"
        )

        controls: list[ft.Control] = []
        if position == "both":
            controls.append(self._button("dec", ft.Icons.REMOVE, -1, spec, "left"))
            controls.append(self._field(spec))
            controls.append(self._button("inc", ft.Icons.ADD, 1, spec, "right"))
        elif position == "right":
            controls.append(self._field(spec))
            controls.append(self._stepper(spec))
        else:
            controls.append(self._field(spec))

        return ft.Container(
            width=self.width,
            height=spec["height"],
            # 用 container 档而非 surface：明暗主题下都比页面底色差一档，
            # 框体才立得起来（深色下 surface 与页面同色，字段会"陷"进背景）。
            bgcolor=ft.Colors.SURFACE_CONTAINER,
            border=ft.Border.all(1, self._border_color),
            border_radius=ft.BorderRadius.all(FIELD_RADIUS),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=ft.Row(
                spacing=0,
                vertical_alignment=ft.CrossAxisAlignment.STRETCH,
                controls=controls,
            ),
        )

    @property
    def _border_color(self) -> ft.ColorValue:
        """描边色：禁用 > 聚焦 > 悬停 > 常态。"""
        if self.disabled:
            return ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE_VARIANT)
        if self._focused:
            return ft.Colors.PRIMARY
        if self._hover == "field":
            return ft.Colors.OUTLINE
        return ft.Colors.OUTLINE_VARIANT

    def _field(self, spec: dict[str, int]) -> ft.Control:
        """中间的可编辑区：prefix + 输入框 + suffix。"""
        row: list[ft.Control] = []
        if self.prefix:
            row.append(self._affix(self.prefix, spec))
        row.append(
            ft.TextField(
                value=self._text if self._text is not None else self.display_text,
                expand=True,
                border=ft.NoInputBorder(),
                filled=False,
                dense=True,
                height=spec["height"] - 8,
                text_size=spec["text"],
                text_align=ft.TextAlign.CENTER,
                text_vertical_align=ft.VerticalAlignment.CENTER,
                color=ft.Colors.ON_SURFACE if not self.disabled else DISABLED_FG,
                cursor_color=ft.Colors.PRIMARY,
                cursor_width=1,
                selection_color=ft.Colors.with_opacity(0.24, ft.Colors.PRIMARY),
                bgcolor=ft.Colors.TRANSPARENT,
                hover_color=ft.Colors.TRANSPARENT,
                focused_bgcolor=ft.Colors.TRANSPARENT,
                content_padding=ft.Padding.symmetric(horizontal=2, vertical=0),
                hint_text=self.hint_text,
                hint_style=ft.TextStyle(size=spec["text"], color=ft.Colors.OUTLINE),
                keyboard_type=ft.KeyboardType.NUMBER,
                read_only=self.read_only or self.disabled,
                on_change=None if self.disabled else self._on_text_change,
                on_submit=None if self.disabled else self._on_text_submit,
                on_blur=None if self.disabled else self._on_text_blur,
                on_focus=None if self.disabled else self._on_text_focus,
            )
        )
        if self.suffix:
            row.append(self._affix(self.suffix, spec))

        return ft.Container(
            expand=True,
            alignment=ft.Alignment.CENTER,
            padding=ft.Padding.symmetric(horizontal=6),
            on_hover=None
            if self.disabled
            else lambda e: self._hover_key("field", _truthy(e.data)),
            content=ft.Row(
                spacing=2,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=row,
            ),
        )

    def _affix(self, text: str, spec: dict[str, int]) -> ft.Control:
        """单位 / 货币符号：只读文案，不参与编辑、也不会被复制进值里。"""
        return ft.Text(
            text,
            size=max(FONT_SIZE["caption"], spec["text"] - 1),
            color=ft.Colors.ON_SURFACE_VARIANT if not self.disabled else DISABLED_FG,
        )

    def _button(
        self,
        key: str,
        icon: ft.IconData,
        sign: int,
        spec: dict[str, int],
        side: str,
    ) -> ft.Control:
        """左右平铺的方形步进按钮。``side`` 决定分隔线画在哪条内边。"""
        enabled = self._can_step(sign)
        border = (
            ft.Border.only(right=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT))
            if side == "left"
            else ft.Border.only(left=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT))
        )
        return ft.Container(
            width=spec["button"],
            alignment=ft.Alignment.CENTER,
            border=border,
            bgcolor=HOVER_BG if enabled and self._hover == key else None,
            on_click=None if not enabled else lambda _e: self._bump(sign),
            on_hover=None
            if not enabled
            else lambda e, k=key: self._hover_key(k, _truthy(e.data)),
            content=ft.Icon(
                icon,
                size=spec["icon"],
                color=ft.Colors.ON_SURFACE_VARIANT if enabled else DISABLED_FG,
            ),
        )

    def _stepper(self, spec: dict[str, int]) -> ft.Control:
        """右侧上下堆叠的步进器：上箭头负责加、下箭头负责减。"""
        return ft.Container(
            width=spec["button"],
            border=ft.Border.only(left=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
            content=ft.Column(
                spacing=0,
                controls=[
                    self._mini_button("inc", ft.Icons.KEYBOARD_ARROW_UP, 1, spec),
                    ft.Container(height=1, bgcolor=ft.Colors.OUTLINE_VARIANT),
                    self._mini_button("dec", ft.Icons.KEYBOARD_ARROW_DOWN, -1, spec),
                ],
            ),
        )

    def _mini_button(
        self, key: str, icon: ft.IconData, sign: int, spec: dict[str, int]
    ) -> ft.Control:
        """堆叠步进器里的半高按钮。"""
        enabled = self._can_step(sign)
        return ft.Container(
            expand=True,
            alignment=ft.Alignment.CENTER,
            bgcolor=HOVER_BG if enabled and self._hover == key else None,
            on_click=None if not enabled else lambda _e: self._bump(sign),
            on_hover=None
            if not enabled
            else lambda e, k=key: self._hover_key(k, _truthy(e.data)),
            content=ft.Icon(
                icon,
                size=max(FONT_SIZE["caption"], spec["icon"] - 3),
                color=ft.Colors.ON_SURFACE_VARIANT if enabled else DISABLED_FG,
            ),
        )


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
def _caption(text: str) -> ft.Control:
    return ft.Text(text, size=FONT_SIZE["small"], color=ft.Colors.ON_SURFACE_VARIANT)


@ft.component
def _stepper() -> ft.Control:
    """步进与单位：按钮到界自动变灰，单位只做展示。"""
    qty = ft.use_memo(
        lambda: NumberInput(
            label="数量", value=12, min=1, max=99, suffix="件", width=180
        ),
        [],
    )
    duration = ft.use_memo(
        lambda: NumberInput(
            label="时长",
            value=1.5,
            step=0.5,
            step_strictly=True,
            suffix="时",
            controls_position="right",
            width=160,
        ),
        [],
    )
    return ft.Column(
        spacing=14,
        controls=[
            qty.ui(),
            duration.ui(),
            _caption(
                f"数量 {qty.value} 件 · 时长 {duration.display_text} 时"
                "（只落在 0.5 的网格上）"
            ),
        ],
    )


@ft.component
def _precision() -> ft.Control:
    """精度与范围夹紧：键入时不打断，失焦 / 回车才收口。"""
    price = ft.use_memo(
        lambda: NumberInput(
            label="单价",
            value=199.9,
            step=0.1,
            precision=2,
            prefix="¥",
            min=0,
            width=200,
        ),
        [],
    )
    percent = ft.use_memo(
        lambda: NumberInput(
            label="完成度",
            value=42,
            min=0,
            max=100,
            step=1,
            suffix="%",
            width=180,
        ),
        [],
    )
    return ft.Column(
        spacing=14,
        controls=[
            price.ui(),
            percent.ui(),
            _caption(
                f"{price.display_text} 元 · {percent.value}% —— 在「完成度」里输入 1000，"
                "失焦或回车后会被夹到 100"
            ),
        ],
    )


@ft.component
def _readonly() -> ft.Control:
    """只读与禁用：一个只是不许键入，另一个连按钮都不响应。"""
    frozen = ft.use_memo(
        lambda: NumberInput(label="只读", value=8, read_only=True, width=160), []
    )
    off = ft.use_memo(
        lambda: NumberInput(label="禁用", value=25, disabled=True, width=160), []
    )
    return ft.Column(
        spacing=14,
        controls=[
            frozen.ui(),
            off.ui(),
            _caption(
                f"只读 {frozen.value}（可点加减、不能键入） · 禁用 {off.value}（全不可用）"
            ),
        ],
    )


_STEPPER_CODE = """qty = NumberInput(label="数量", value=12, min=1, max=99, suffix="件")
duration = NumberInput(
    label="时长", value=1.5, step=0.5, step_strictly=True,
    suffix="时", controls_position="right",
)
Column([qty.ui(), duration.ui()])"""

_PRECISION_CODE = """price = NumberInput(
    label="单价", value=199.9, step=0.1, precision=2, prefix="¥", min=0,
)
percent = NumberInput(label="完成度", value=42, min=0, max=100, suffix="%")

# 键入 1000 不会被中途改写；失焦或回车时夹到 100
Column([price.ui(), percent.ui()])"""


SPEC = Spec(
    name="NumberInput",
    summary="数字输入：步进按钮、固定精度、单位，以及失焦时的范围夹紧。",
    definition=(
        "数字输入和文本框的差别不在键盘，而在「值」要守规矩：不能为空得莫名其妙、"
        "不能停在 1000 而界面上限是 99、金额不能带出一串浮点尾巴。所以它把键入、"
        "步进、读数拆成三条路径：键入只拦结构错，失焦与回车才按精度和范围收口；"
        "步进以 ``step`` 为粒度，到界的一侧按钮直接变灰；显示始终走格式化值。"
    ),
    anatomy=[
        (
            "外框",
            "36px 高、8px 圆角、1px 描边；聚焦转主色、悬停加深、禁用整体降透明度。",
        ),
        (
            "步进按钮",
            "both 是左右各一个加减，right 是右侧上下堆叠（窄容器与表格用），none 只留输入。",
        ),
        (
            "数值区",
            "只放行数字 / 一个负号 / 一个小数点；结构不合法时退回上一个可接受文本。",
        ),
        (
            "前后缀",
            "货币符号与单位常驻框内，只做展示、不进入值，也不会被用户误删。",
        ),
        (
            "边界",
            "值到 min / max 后该方向按钮变灰；不靠「点了没反应」暗示已经到头。",
        ),
    ],
    when=[
        "数量、金额、税率、时长这类必须可计算、可比较的字段",
        "需要「点一下加一」的连续微调，而不只是键入",
        "业务有明确上下限（库存 1-99、折扣 0-100），越界要被收口",
    ],
    avoid=[
        "手机号、邮编、订单号：它们长得像数字但语义是文本，用 Input（别丢前导 0）",
        "需要输入自由表达式（1+2、10%）的字段：数字框只认一个数",
        "从固定档位里挑（S/M/L）：用 SegmentedButton 或 Radio，步进按钮会让人一直点",
    ],
    examples=[
        Example(
            "步进与单位",
            _stepper,
            hint="数量到 99 后加号变灰；时长按 0.5 步进，单位「时」不参与编辑。",
            code=_STEPPER_CODE,
        ),
        Example(
            "精度与范围",
            _precision,
            hint="单价固定两位小数；在完成度里输入 1000，失焦后被夹到 100。",
            code=_PRECISION_CODE,
        ),
        Example(
            "只读与禁用",
            _readonly,
            hint="只读仍可点按钮改值；禁用连按钮一起失效，用来表示「当前不可编辑」。",
        ),
    ],
    api=[
        Api(
            "value",
            "int | float | Decimal | str | None",
            "0",
            "当前值；None 表示空，显示 hint_text",
        ),
        Api("min", "int | float | Decimal | None", "None", "下界（含），失焦时夹紧"),
        Api(
            "max", "int | float | Decimal | None", "None", "上界（含），到界后加号变灰"
        ),
        Api(
            "step", "int | float | Decimal", "1", "加减粒度，也决定 precision 的默认值"
        ),
        Api(
            "precision",
            "int | None",
            "None",
            "固定小数位；None 时跟随 step（0.01 → 2 位）",
        ),
        Api(
            "suffix",
            "str | None",
            "None",
            "框内单位或百分号；prefix 是左侧的同款（货币符号）",
        ),
        Api(
            "controls_position",
            "str",
            "'both'",
            "both 左右平铺 / right 右侧堆叠 / none 不显示按钮",
        ),
        Api("read_only", "bool", "False", "只能点按钮、不能键入"),
        Api("disabled", "bool", "False", "整体禁用：按钮与输入都不响应"),
        Api(
            "on_change",
            "Callable[[int | float | None], None] | None",
            "None",
            "值变化回调；按值去重，同一个值不会重复回调",
        ),
    ],
    notes=[
        tip(
            "键入过程中组件不夹紧、不补零、不改小数点 —— 否则光标会跳。范围与精度"
            "统一在失焦 / 回车时收口；同时补了失焦后的重绘，聚焦描边不会留在"
            "已经离开的框上。"
        ),
        info(
            "运算全程走 Decimal，0.1 + 0.2 不会变成 0.30000000000000004。"
            "step_strictly=True 时取值吸附到以 min（未设则 0）为起点的步长网格，"
            "适合「半小时一格」这类时间档位。"
        ),
        warn(
            "外部改值请用 set_value：它会做同样的规整，且值没变时不触发重绘。"
            "直接写 value 会绕过范围与精度，下一次步进才被纠正。"
        ),
    ],
    tags=("数字", "数字输入", "number", "步进", "stepper", "表单"),
)


if __name__ == "__main__":
    run(SPEC)
