"""数值动画 (NumberAnimation) —— 让一个数字"数"过去。
``number-animation``：给起点、终点和时长，数字从前者平滑滚到后者。
仪表盘的成交额、在线人数、完成率用它 —— 静态数字只给结论，滚动过程顺带告诉
读者"这个量级在什么位置""它刚刚变了"。

用法::

    NumberAnimation(end=128_640, duration=1200, size=36, weight="semibold")
    NumberAnimation(end=0.284, precision=3, suffix="%", separator="")
    NumberAnimation(end=42, start=1000, easing="linear")   # 反向、匀速

四条取舍（改前先读）
--------------------
1. **每帧只重绘自己这一格，不惊动父级**。看着像"直接改那个 ``Text`` 更快"，但
   组件的渲染产物是**冻结**的（Flet 1.0 会拦住对它的赋值，改一行就
   ``Frozen controls cannot be updated``）。所以走 ``notify()`` 重绘：作用域只有
   这个数字本身，父级卡片、整个仪表盘都不会跟着重建。

2. **不信 hooks，起跑判定写在渲染里**。``ui()`` 是被调用方**显式调用**的
   （``anim.ui()``），外层每次重绘都会重建组件实例、hooks 里的状态清零；用
   ``use_effect`` 排定时，"父级某个无关状态变了"都会把动画从头播一遍。所以
   判定只有一句：**没在跑、且显示值不等于终值**才起一轮。父级怎么重绘都不影响。

3. **30 帧，不是 60 帧；字符串没变就不重绘**。数字滚动的高频变化都在曲线前段，
   肉眼分辨不出 30 与 60 帧的减速过程，而每帧都是一次重绘加一次往返。整数计数
   更是如此：前几帧可能都还是同一个 "3"，那就一次重绘都别发。

4. **中途换目标从"当前值"接着走**，不是从 ``start`` 重来。KPI 每几秒刷一次，
   从 0 重播会让人以为数据在乱跳；从当前值续上新目标，才像"它涨到这儿了"。
   换目标后重新计时一整段 ``duration`` —— 短于它会在连续刷新时显得仓促。
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass, field

import flet as ft

from ui.core.config import logger
from ui.core.format import format_number

__all__ = [
    "EASINGS",
    "NumberAnimation",
    "ease_in_out",
    "ease_out_cubic",
    "format_value",
]

#: 帧间隔（秒）。约 30 帧/秒，理由见模块文档第 3 条。
FRAME = 0.032


# ---------------------------------------------------------------------------
# 纯函数：缓动与格式化
# ---------------------------------------------------------------------------
def ease_out_cubic(t: float) -> float:
    """先快后慢 —— 数值滚动的默认手感：起步就走，收尾轻轻停住。"""
    return 1.0 - (1.0 - t) ** 3


def ease_in_out(t: float) -> float:
    """两头慢、中间快。适合"变化不大但要看得见过程"的场合。"""
    return 4 * t * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


#: ``easing`` 收字符串时查这张表。取不到就退回 :func:`ease_out_cubic`。
EASINGS: dict[str, Callable[[float], float]] = {
    "linear": lambda t: t,
    "ease-out": ease_out_cubic,
    "ease-in-out": ease_in_out,
}


def format_value(
    value: float,
    *,
    precision: int = 0,
    separator: str | None = None,
    prefix: str = "",
    suffix: str = "",
) -> str:
    """把数字写成要显示的那串字符。

    Args:
        value: 数字。
        precision: 保留几位小数（负数按 0 处理）。
        separator: 千分位符号。``None`` 跟随当前语言（``1,286`` / ``1 286``）；
            给字符串就完全照办，``""`` 表示不要分组。
        prefix: 前缀，如 ``"¥"``。负数时负号在前缀**之前**（``-¥1,200``）。
        suffix: 后缀，如 ``"%"``。

    >>> format_value(1286)
    '1,286'
    >>> format_value(-1234.5678, precision=2, prefix="¥")
    '-¥1,234.57'
    """
    places = max(0, int(precision))
    # 先取整再判符号：-0.004 保留 0 位是 0，不该写成 "-0"
    rounded = round(float(value), places)
    negative = rounded < 0
    body = (
        format_number(abs(rounded), decimals=places)
        if separator is None
        else f"{abs(rounded):,.{places}f}".replace(",", separator or "")
    )
    return f"{'-' if negative else ''}{prefix}{body}{suffix}"


# ---------------------------------------------------------------------------
# 组件
# ---------------------------------------------------------------------------
@ft.observable
@dataclass
class NumberAnimation:
    """会滚动的数字。

    Args:
        end: 目标值。运行中改它会**从当前显示值**续着滚过去，不会从头重播。
        start: 起始值，默认 0。
        duration: 时长（毫秒）。``0`` 表示不要动画，直接落位。
        precision: 保留几位小数，默认 0。
        separator: 千分位符号。``None`` 跟随语言，``""`` 关闭分组。
        prefix: 前缀（``"¥"`` / ``"约 "``）。
        suffix: 后缀（``"%"`` / ``" 人"``）。
        easing: ``"ease-out"``（默认）/ ``"linear"`` / ``"ease-in-out"``，或
            自定义 ``f(进度 0~1) -> 0~1`` 的函数。
        active: 是否起播。``False`` 直接显示终值（数据还没到、或关掉了动效）。
        size: 字号。``None`` 跟随正文。
        color: 颜色。``None`` 跟随主题正文色。
        weight: 字重。
        on_finish: 滚到终点时回调一次（每次改 ``end`` 到达后各触发一次）。

    Notes:
        读屏软件念的是**终值**（``semantics_label``），不是中途那些数。
        要在页面里重新播一遍（"再刷新一次"），调 :meth:`play`。
    """

    end: float = 0.0
    start: float = 0.0
    duration: int = 1000
    precision: int = 0
    separator: str | None = None
    prefix: str = ""
    suffix: str = ""
    easing: str | Callable[[float], float] = "ease-out"
    active: bool = True
    size: float | None = None
    color: str | None = None
    weight: ft.FontWeight | None = None
    on_finish: Callable[[], None] | None = None

    #: 当前**显示**的值（不是 ``end``）。内部字段：改它们不该各自触发一次重绘，
    #: 由 :meth:`_show` 统一判断"屏幕上的字变了没"。
    _shown: float = field(default=0.0, init=False, repr=False)
    _label_shown: str = field(default="", init=False, repr=False)
    _animating: bool = field(default=False, init=False, repr=False)
    _token: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        self._snap(self.start if self.active else self.end)

    # ------------------------------------------------------------------
    # 对外
    # ------------------------------------------------------------------
    def play(self) -> None:
        """从 ``start`` 重新播一遍。"""
        self._show(self.start)
        if self.active:
            self._launch()

    @property
    def value(self) -> float:
        """此刻**显示**的值（动画中是中间值，落定后等于 ``end``）。"""
        return self._shown

    # ------------------------------------------------------------------
    # 内部：状态
    # ------------------------------------------------------------------
    @property
    def _places(self) -> int:
        return max(0, int(self.precision))

    @property
    def _ease(self) -> Callable[[float], float]:
        if callable(self.easing):
            return self.easing
        return EASINGS.get(self.easing, ease_out_cubic)

    def _snap(self, value: float) -> None:
        """把显示值设成某个数（不重绘）。"""
        object.__setattr__(self, "_shown", round(float(value), self._places))

    def _label(self) -> str:
        return format_value(
            self._shown,
            precision=self.precision,
            separator=self.separator,
            prefix=self.prefix,
            suffix=self.suffix,
        )

    def _repaint(self) -> None:
        """请求重绘。

        名字**不能**叫 ``_notify``：``@ft.observable`` 自己注入了 ``_notify(name)``，
        覆盖了会在构造期直接 ``TypeError``。
        """
        notify = getattr(self, "notify", None)
        if callable(notify):
            notify()

    def _show(self, value: float) -> None:
        """推进到某个值；**屏幕上那串字符没变就不重绘**。"""
        self._snap(value)
        label = self._label()
        if label == object.__getattribute__(self, "_label_shown"):
            return
        object.__setattr__(self, "_label_shown", label)
        self._repaint()

    # ------------------------------------------------------------------
    # 内部：动画
    # ------------------------------------------------------------------
    def _launch(self) -> None:
        """起一轮（并作废正在跑的那轮）。"""
        object.__setattr__(self, "_token", self._token + 1)
        token = self._token
        object.__setattr__(self, "_animating", True)

        async def runner() -> None:
            await self._run(token)

        try:
            ft.context.page.run_task(runner)
        except Exception:  # noqa: BLE001 - 页面已关 / 纯逻辑测试里的假 Page
            logger.debug("数值动画没能排上定时器", exc_info=True)
            object.__setattr__(self, "_animating", False)

    async def _run(self, token: int) -> None:
        try:
            target = float(self.end)
            origin = self._shown
            duration = max(0, int(self.duration))
            if duration == 0 or origin == round(target, self._places):
                self._show(target)
                self._finish()
                return

            t0 = time.perf_counter()
            while self._token == token:
                if float(self.end) != target:  # 中途换了目标：从当前值续上
                    origin, target = self._shown, float(self.end)
                    t0 = time.perf_counter()
                progress = (time.perf_counter() - t0) * 1000.0 / duration
                if progress >= 1.0:
                    self._show(target)
                    self._finish()
                    return
                span = target - origin
                self._show(origin + span * self._ease(max(0.0, progress)))
                await asyncio.sleep(FRAME)
        finally:
            if self._token == token:
                object.__setattr__(self, "_animating", False)

    def _finish(self) -> None:
        if self.on_finish is not None:
            self.on_finish()

    # ------------------------------------------------------------------
    # 渲染
    # ------------------------------------------------------------------
    @ft.component
    def ui(self) -> ft.Control:
        """构建这串数字。"""
        target = float(self.end)
        if not self.active:
            self._snap(target)  # 关掉动效：直接给终值，别留一个中间态

        label = self._label()
        object.__setattr__(self, "_label_shown", label)  # 屏幕上现在是这串字
        ctrl = ft.Text(
            label,
            size=self.size,
            color=self.color,
            weight=self.weight,
            no_wrap=True,
            # 读屏念终值：默认会随着每帧的 value 一路念过去，没人受得了
            semantics_label=format_value(
                target,
                precision=self.precision,
                separator=self.separator,
                prefix=self.prefix,
                suffix=self.suffix,
            ),
        )

        if (
            self.active
            and not object.__getattribute__(self, "_animating")
            and self._shown != round(target, self._places)
        ):
            self._launch()
        return ctrl
