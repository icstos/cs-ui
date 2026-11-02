"""本地化格式化：日期、时间、数字、月份 / 星期名、列表连接词。

**为什么单独一个模块**：多语言适配失败最常见的样子不是"没翻译"，而是
"翻译了但格式还是中文的" —— 英文界面里出现 ``2026 年 9 月``、``1,286 项``
里的量词、日历表头写死"一二三四五六日"。这些值和文案一样必须跟着语言走，
所以统一从这里取，组件里不再出现任何字面量。

所有函数都读**当前语言**（``ui.core.i18n`` 的全局状态），因此：

- 在 ``@ft.component`` 里调用前先 ``tr = use_t()`` 订阅，切语言才会重绘；
- 组件外（日志、导出）直接调用即可，拿到的也是当前语言的结果。

线程安全性与 ``t()`` 一致：语言状态是进程级单例，切语言是显式动作，
不存在"渲染到一半语言变了"的中间态。
"""

from __future__ import annotations

import datetime as _dt
from collections.abc import Iterable
from typing import Any

from ui.core.i18n import t

__all__ = [
    "calendar_title",
    "first_weekday",
    "format_date",
    "format_datetime",
    "format_list",
    "format_number",
    "format_time",
    "month_cell",
    "month_name",
    "weekday_names",
]

_COMMA = ","
_DOT = "."


# ---------------------------------------------------------------------------
# 数字
# ---------------------------------------------------------------------------
def format_number(value: float | int, decimals: int | None = None) -> str:
    """按当前语言分组数字：``1286`` → ``1,286``。

    Args:
        value: 待格式化的数字。
        decimals: 固定小数位；``None`` 表示"整数就显示整数，小数原样保留"。

    >>> set_locale("en-US"); format_number(1286)          # doctest: +SKIP
    '1,286'
    """
    if decimals is None:
        text = f"{int(value):,}" if float(value).is_integer() else f"{value:,}"
    else:
        text = f"{value:,.{decimals}f}"

    thousand = t("ui.format.thousand")
    decimal = t("ui.format.decimal")
    if thousand == _COMMA and decimal == _DOT:
        return text  # 绝大多数语言走这条，零额外开销
    # 用 NUL 做中转，避免"先把 . 换成 , 再把 , 换成空格"这类顺序错误
    return text.replace(_COMMA, "\x00").replace(_DOT, decimal).replace("\x00", thousand)


# ---------------------------------------------------------------------------
# 日期 / 时间
# ---------------------------------------------------------------------------
def format_date(value: _dt.date, *, long: bool = False) -> str:
    """按当前语言的写法格式化日期。

    ``long=False`` → ``2026-09-26`` / ``09/26/2026``；
    ``long=True``  → ``2026 年 09 月 26 日`` / ``September 26, 2026``。
    """
    if long:
        return t("ui.format.date_long", y=value.year, m=value.month, d=value.day,
                 name=month_name(value.month))
    return t("ui.format.date", y=value.year, m=value.month, d=value.day)


def format_time(value: _dt.time | _dt.datetime, *, seconds: bool = False) -> str:
    """按当前语言格式化时间（24 小时制，``09:30`` / ``09:30:15``）。"""
    key = "ui.format.time_seconds" if seconds else "ui.format.time"
    return t(key, h=value.hour, mi=value.minute, s=getattr(value, "second", 0))


def format_datetime(value: _dt.datetime, *, seconds: bool = False) -> str:
    """日期 + 时间，中间用空格连接（各语言的日期、时间顺序各自决定）。"""
    return f"{format_date(value)} {format_time(value, seconds=seconds)}"


# ---------------------------------------------------------------------------
# 月份 / 星期
# ---------------------------------------------------------------------------
def month_name(month: int, *, short: bool = False) -> str:
    """1~12 的月份名；``short=True`` 取缩写（``Jan``），中文两者都是 ``9 月``。"""
    if short:
        # 中文没有"缩写"概念，语言包里不重复写一遍，直接回落到全称。
        found = t(f"ui.calendar.months_short.{month}")
        if found != f"ui.calendar.months_short.{month}":
            return found
    return t(f"ui.calendar.months.{month}")


def weekday_names() -> tuple[str, ...]:
    """7 个星期名，索引与 ``date.weekday()`` 一致：0 = 周一 … 6 = 周日。"""
    return tuple(t(f"ui.calendar.weekdays.{i}") for i in range(1, 8))


def first_weekday() -> int:
    """每周首日（0 = 周一，6 = 周日）。由语言包决定：中文周一、英文周日。"""
    raw = t("ui.calendar.first_weekday")
    try:
        return int(raw) % 7
    except ValueError:
        return 0  # 语言包写错不该让日历崩掉，按 ISO 的周一兜底


def calendar_title(year: int, month: int, *, mode: str = "day") -> str:
    """月历面板头部的标题：``2026 年 9 月`` / ``September 2026`` / ``2026 年``。"""
    if mode == "year":
        return t("ui.calendar.title_year", year=year)
    return t(
        "ui.calendar.title_day",
        year=year,
        num=month,
        name=month_name(month),
        short=month_name(month, short=True),
    )


def month_cell(month: int) -> str:
    """年月网格里单格的文字：``9 月`` / ``Sep``。"""
    return t(
        "ui.calendar.cell_month",
        num=month,
        name=month_name(month),
        short=month_name(month, short=True),
    )


# ---------------------------------------------------------------------------
# 列表
# ---------------------------------------------------------------------------
def format_list(items: Iterable[Any], *, limit: int | None = None) -> str:
    """把若干项连成一句：``A、B、C`` / ``A, B, C``。

    Args:
        items: 待连接的项（非字符串自动 ``str()``）。
        limit: 最多显示几项，超出部分折成 ``… +N``，用于 Chip 汇总这类窄容器。
    """
    values = [item if isinstance(item, str) else str(item) for item in items]
    if limit is not None and len(values) > limit:
        rest = len(values) - limit
        values = [*values[:limit], f"+{rest}"]
    return t("ui.format.list_sep").join(values)
