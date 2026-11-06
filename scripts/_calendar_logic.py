"""Calendar 纯逻辑断言（不启窗口）。

覆盖：月网格对齐与长度、跨年翻页、星期标签旋转、视图初始化、选中与回写视图、
禁用（区间 / 逐日 / 两者叠加）、月 / 年两种翻页、粒度切换与回调参数、
「今天」的边界行为、悬停状态机、非法入参。

渲染期的东西（控件结构、颜色、真机点击）交给 smoke_test 与真机探针。

用法::

    python scripts/_calendar_logic.py
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ui.core.i18n import set_locale
from ui.display.calendar import (
    MODES,
    Calendar,
    month_grid,
    shift_month,
    weekday_labels,
)

D = dt.date
_fails = 0
_passes = 0


def check(name: str, got: object, want: object) -> None:
    global _fails, _passes
    if got == want:
        _passes += 1
        print(f"PASS  {name}")
    else:
        _fails += 1
        print(f"FAIL  {name}: got={got!r} want={want!r}")


def raises(name: str, fn) -> None:
    global _fails, _passes
    try:
        fn()
    except (TypeError, ValueError):
        _passes += 1
        print(f"PASS  {name}")
    else:
        _fails += 1
        print(f"FAIL  {name}: 没有抛异常")


# ---------------------------------------------------------------------------
# 网格：对齐 / 长度 / 内容
# ---------------------------------------------------------------------------
def test_grid() -> None:
    grid = month_grid(2026, 11, 0)
    check("网格恒为 42 格", len(grid), 42)
    check("2026-11 周一起：首格是 10-26", grid[0], D(2026, 10, 26))
    check("首格是周一", grid[0].weekday(), 0)
    check("末格是 12-06", grid[-1], D(2026, 12, 6))
    check("本月每天都在这 42 格里", all(d in grid for d in _days(2026, 11)), True)
    check("42 格连续无洞", (grid[-1] - grid[0]).days, 41)

    sunday_first = month_grid(2026, 11, 6)
    check("周日起：首格是 11-01", sunday_first[0], D(2026, 11, 1))
    check("周日起：首格是周日", sunday_first[0].weekday(), 6)

    # 2 月：闰年与平年都必须是 42 格（面板高度不随月份跳）
    check("2024-02（闰）42 格", len(month_grid(2024, 2, 0)), 42)
    check("2026-02（平）42 格", len(month_grid(2026, 2, 0)), 42)
    check("2026-02 含 28 天", len([d for d in month_grid(2026, 2, 0) if d.month == 2]), 28)

    # 任意起点：首格所在行必须以 first_day 开头
    for first in range(7):
        head = month_grid(2026, 7, first)[0]
        ok = head.weekday() == first % 7
        check(f"first_day={first} 首格星期对齐", ok, True)


def test_weekday_labels() -> None:
    set_locale("zh-CN")
    labels = weekday_labels(0)
    check("标签恒为 7 个", len(labels), 7)
    check("周一在首位", labels[0], "一")
    check("周日收尾", labels[-1], "日")
    sunday = weekday_labels(6)
    check("首日=周日时表头右移一位", sunday[0], "日")
    check("首日=周日时次位是周一", sunday[1], "一")
    check("乱给的整数也能归一到 0~6", weekday_labels(13)[0], weekday_labels(6)[0])


def test_shift_month() -> None:
    check("11 月退一个月", shift_month(2026, 11, -1), (2026, 10))
    check("1 月退一个月 → 上一年 12 月", shift_month(2026, 1, -1), (2025, 12))
    check("12 月进一个月 → 下一年 1 月", shift_month(2026, 12, 1), (2027, 1))
    check("跨 13 个月", shift_month(2026, 5, 13), (2027, 6))
    check("跨 -14 个月", shift_month(2026, 5, -14), (2025, 3))
    check("原地不动", shift_month(2026, 5, 0), (2026, 5))


# ---------------------------------------------------------------------------
# 初始化与状态机
# ---------------------------------------------------------------------------
def test_init() -> None:
    cal = Calendar(value=D(2026, 3, 9))
    check("视图跟随 value", cal.view, (2026, 3))
    check("选中即 value", cal.selected, D(2026, 3, 9))
    check("默认粒度是 month", cal.mode, "month")

    today = D.today()
    bare = Calendar()
    check("不给 value 时视图落在本月", bare.view, (today.year, today.month))
    check("不给 value 时没有选中", bare.selected, None)

    raises("非法 mode 报错", lambda: Calendar(mode="week"))
    raises(
        "valid_range 反序报错",
        lambda: Calendar(valid_range=(D(2026, 5, 1), D(2026, 4, 1))),
    )


def test_select() -> None:
    seen: list[D] = []
    cal = Calendar(value=D(2026, 3, 9), on_select=seen.append)
    cal.select(D(2026, 7, 20))
    check("选中回写", cal.selected, D(2026, 7, 20))
    check("视图跟着跳到 7 月", cal.view, (2026, 7))
    check("on_select 收到日期", seen, [D(2026, 7, 20)])

    cal.select(D(2026, 7, 20))
    check("重复点同一天不重复回调", seen, [D(2026, 7, 20)])

    check("selected 属性对外可读", cal.selected, D(2026, 7, 20))


def test_disabled() -> None:
    lo, hi = D(2026, 11, 2), D(2026, 11, 22)
    cal = Calendar(
        value=D(2026, 11, 5),
        valid_range=(lo, hi),
        disabled_date=lambda day: day.weekday() >= 5,
    )
    check("区间内工作日可选", cal.is_enabled(D(2026, 11, 4)), True)
    check("区间外不可选", cal.is_enabled(D(2026, 11, 23)), False)
    check("区间外（之前）不可选", cal.is_enabled(D(2026, 10, 31)), False)
    check("区间内周末仍被 disabled_date 挡住", cal.is_enabled(D(2026, 11, 7)), False)
    # 边界那天本身是周一：区间**下界包含**，但周末规则优先（11-01 是周日 → 被挡）
    check("边界：区间起点（周一）可选", cal.is_enabled(D(2026, 11, 2)), True)
    check("边界：区间前一天不可选", cal.is_enabled(D(2026, 11, 1)), False)
    check("边界：最后一天（周日）被周末规则挡住", cal.is_enabled(D(2026, 11, 22)), False)

    cal.select(D(2026, 11, 7))
    check("禁用日点了也不改选中", cal.selected, D(2026, 11, 5))
    cal.select(D(2026, 11, 9))
    check("可选日点了才改选中", cal.selected, D(2026, 11, 9))


def test_shift_and_mode() -> None:
    events: list[tuple[D, str]] = []
    cal = Calendar(value=D(2026, 1, 15), on_panel_change=lambda d, m: events.append((d, m)))

    cal.shift(-1)
    check("月视图退一月跨年", cal.view, (2025, 12))
    check("翻页回调带月首日与粒度", events[-1], (D(2025, 12, 1), "month"))

    cal.set_mode("year")
    check("切到年视图", cal.mode, "year")
    check("切粒度也回调", events[-1], (D(2025, 12, 1), "year"))
    cal.shift(1)
    check("年视图翻页按年", cal.view, (2026, 12))

    cal.set_mode("month")
    check("切回月视图", cal.mode, "month")
    raises("set_mode 非法值报错", lambda: cal.set_mode("decade"))
    check("MODES 只有两档", MODES, ("month", "year"))

    # 年视图里选月：落到那个月并回到月视图
    cal.set_mode("year")
    cal._pick_month(2027, 5)
    check("年视图选月 → 视图落位", cal.view, (2027, 5))
    check("年视图选月 → 回到月视图", cal.mode, "month")
    check("选月回调参数", events[-1], (D(2027, 5, 1), "month"))


def test_today() -> None:
    today = D.today()
    far = D(2001, 2, 3)
    cal = Calendar(value=far, mode="year")
    cal.go_today()
    check("今天：视图回到本月", cal.view, (today.year, today.month))
    check("今天：粒度回到月视图", cal.mode, "month")
    check("今天：默认顺手选中", cal.selected, today)

    blocked = Calendar(value=far, valid_range=(D(1999, 1, 1), D(2000, 1, 1)))
    blocked.go_today()
    check("今天在区间外则不选中", blocked.selected, far)
    check("今天在区间外仍然跳视图", blocked.view, (today.year, today.month))


def test_hover() -> None:
    cal = Calendar(value=D(2026, 11, 5))
    cal._hover_cell(D(2026, 11, 12), True)
    check("进入某日 → 记下悬停", cal._hover, D(2026, 11, 12))
    cal._hover_cell(D(2026, 11, 12), True)
    check("同格再进入不改变", cal._hover, D(2026, 11, 12))
    cal._hover_cell(D(2026, 11, 13), False)
    check("离开别的格子不误清", cal._hover, D(2026, 11, 12))
    cal._hover_cell(D(2026, 11, 12), False)
    check("离开本格才清空", cal._hover, None)

    cal._hover_unit("title", "true")
    check("页头悬停接受字符串载荷", cal._hover_key, "title")
    cal._hover_unit("title", "false")
    check("页头悬停复位", cal._hover_key, None)


def test_cache_invalidate() -> None:
    cal = Calendar(value=D(2026, 11, 5))
    cal.invalidate()  # 只要求不抛异常：外部改了 disabled_date 之后会调它
    check("invalidate 后状态不变", cal.selected, D(2026, 11, 5))


# ---------------------------------------------------------------------------
def _days(year: int, month: int) -> list[D]:
    out: list[D] = []
    day = D(year, month, 1)
    while day.month == month:
        out.append(day)
        day += dt.timedelta(days=1)
    return out


def main() -> int:
    for fn in (
        test_grid,
        test_weekday_labels,
        test_shift_month,
        test_init,
        test_select,
        test_disabled,
        test_shift_and_mode,
        test_today,
        test_hover,
        test_cache_invalidate,
    ):
        print(f"\n## {fn.__name__}")
        fn()
    print(f"\nRESULT: {_passes} passed, {_fails} failed")
    return 1 if _fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
