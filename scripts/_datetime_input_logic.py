"""DateTimeInput 逻辑层单测（不需要真机，纯 Python 断言）。

跑法::

    python scripts/_datetime_input_logic.py

覆盖：文本解析（`_split_datetime_text` / `_parse_time_parts` / `_parse_datetime`）、
值规整与钳制、时间轮盘取值与环形步进、月历钩子、`on_change` 去重、面板尺寸。
"""

from __future__ import annotations

import datetime
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ui.input.datetime_input import (  # noqa: E402
    TIME_ROWS,
    DateTimeInput,
    _parse_datetime,
    _parse_time_parts,
    _split_datetime_text,
)

FAILED: list[str] = []


def check(label: str, got: object, want: object) -> None:
    ok = got == want
    if not ok:
        FAILED.append(label)
    print(f"{'PASS' if ok else 'FAIL'}  {label}: got={got!r} want={want!r}")


print("== _split_datetime_text ==")
for text, want in [
    ("2026-09-26 09:30", ("2026-09-26", "09:30")),
    ("2026-09-26 09:30:15", ("2026-09-26", "09:30:15")),
    ("2026/9/26 9:30", ("2026/9/26", "9:30")),
    ("20260926 0930", ("20260926", "0930")),
    ("2026年9月26日 9时30分", ("2026年9月26日", "9时30分")),
    ("2026-09-26T09:30:15", ("2026-09-26", "09:30:15")),
    ("2026-09-26 09：30", ("2026-09-26", "09:30")),
    ("2026-09-26", ("2026-09-26", "")),
    ("09:30", ("", "09:30")),
    ("", ("", "")),
]:
    check(f"split {text!r}", _split_datetime_text(text), want)

print("\n== _parse_time_parts ==")
for text, want in [
    ("09:30", {"hour": 9, "minute": 30}),
    ("9:30:15", {"hour": 9, "minute": 30, "second": 15}),
    ("0930", {"hour": 9, "minute": 30}),
    ("093000", {"hour": 9, "minute": 30, "second": 0}),
    ("9时30分", {"hour": 9, "minute": 30}),
    ("9时", {"hour": 9}),
    ("9", {"hour": 9}),
    ("23:59:59", {"hour": 23, "minute": 59, "second": 59}),
    ("24:00", None),
    ("09:60", None),
    ("abc", None),
    ("", None),
    (None, None),
]:
    check(f"time {text!r}", _parse_time_parts(text), want)

print("\n== _parse_datetime（没提到的部分沿用 base）==")
base = datetime.datetime(2026, 1, 1, 8, 15, 20)
for text, want in [
    ("2026-09-26 09:30", datetime.datetime(2026, 9, 26, 9, 30, 20)),
    ("2026-09-26", datetime.datetime(2026, 9, 26, 8, 15, 20)),
    ("09:30", datetime.datetime(2026, 1, 1, 9, 30, 20)),
    ("20260926 0930", datetime.datetime(2026, 9, 26, 9, 30, 20)),
    ("2026年9月26日 9时30分15秒", datetime.datetime(2026, 9, 26, 9, 30, 15)),
    ("abc", None),
    ("", None),
]:
    check(f"datetime {text!r}", _parse_datetime(text, base), want)

print("\n== 值规整 / 钳制 ==")
d = DateTimeInput(value=datetime.datetime(2026, 9, 26, 9, 30, 47, 123456))
check("微秒清零", d.value.microsecond, 0)
check("不显示秒 => 秒归零", d.value, datetime.datetime(2026, 9, 26, 9, 30))
check("display_text", d.display_text, "2026-09-26 09:30")
check("with_seconds display", DateTimeInput(
    value=datetime.datetime(2026, 9, 26, 9, 30, 47), with_seconds=True
).display_text, "2026-09-26 09:30:47")
check("自定义 display_format", DateTimeInput(
    value=datetime.datetime(2026, 9, 26, 9, 30), display_format="%Y/%m/%d %H:%M"
).display_text, "2026/09/26 09:30")
check("空值 display_text", DateTimeInput(value=datetime.datetime(2026, 1, 1)).display_text,
      "2026-01-01 00:00")

lo = datetime.datetime(2026, 9, 5, 8, 0)
hi = datetime.datetime(2026, 9, 20, 18, 0)
b = DateTimeInput(value=datetime.datetime(2026, 9, 10, 14, 0),
                  min_datetime=lo, max_datetime=hi)
check("_min", b._min, lo)
check("_max", b._max, hi)
check("范围内可选", b._accepts(datetime.datetime(2026, 9, 20, 18, 0)), True)
check("超上界不可选", b._accepts(datetime.datetime(2026, 9, 20, 18, 1)), False)
check("超下界不可选", b._accepts(datetime.datetime(2026, 9, 5, 7, 59)), False)
check("日期级钩子（当天含部分可选）", b._cal_bounds(),
      (datetime.date(2026, 9, 5), datetime.date(2026, 9, 20)))
r = DateTimeInput(value=datetime.datetime(2026, 9, 26, 9, 30), year_range=(2100, 1900))
check("乱序 year_range 兜底下界", r._min, datetime.datetime(1900, 1, 1))
check("乱序 year_range 兜底上界", r._max, datetime.datetime(2100, 12, 31, 23, 59, 59))

print("\n== 时间列：取值 / 窗口 / 步进 ==")
d = DateTimeInput(value=datetime.datetime(2026, 9, 26, 9, 30))
check("hour 全量", d._time_values("hour"), list(range(24)))
check("minute 全量（step=1）", d._time_values("minute"), list(range(60)))
check("second 列默认不出现", d._kinds, ("hour", "minute"))
check("含秒时三列", DateTimeInput(with_seconds=True)._kinds, ("hour", "minute", "second"))
check("窗口行数", len(d._time_window("hour")), TIME_ROWS)
check("窗口选中项居中", d._time_window("hour")[TIME_ROWS // 2], (0, 9))
check("窗口环形回绕（0 点向上）",
      DateTimeInput(value=datetime.datetime(2026, 9, 26, 0, 0))._time_window("hour"),
      [(-3, 21), (-2, 22), (-1, 23), (0, 0), (1, 1), (2, 2), (3, 3)])

m5 = DateTimeInput(value=datetime.datetime(2026, 9, 26, 9, 37), minute_step=5)
check("步长对齐 + 补入当前值", m5._time_values("minute"),
      [0, 5, 10, 15, 20, 25, 30, 35, 37, 40, 45, 50, 55])
check("补入值也能居中", m5._time_window("minute")[TIME_ROWS // 2], (0, 37))

s = DateTimeInput(value=datetime.datetime(2026, 9, 26, 9, 30), minute_step=30)
check("值少时环形铺满窗口（不出现空行）",
      s._time_window("minute"), [(-3, 0), (-2, 30), (-1, 0), (0, 30), (1, 0), (2, 30), (3, 0)])

w = DateTimeInput(value=datetime.datetime(2026, 9, 26, 23, 30))
w._step_time("hour", 1)
check("小时环形 +1（23 -> 00）", w.value, datetime.datetime(2026, 9, 26, 0, 30))
w._step_time("hour", -1)
check("小时环形 -1（00 -> 23）", w.value, datetime.datetime(2026, 9, 26, 23, 30))
w.set_time(minute=59)
w._step_time("minute", 1)
check("分钟环形 +1（59 -> 00）", w.value, datetime.datetime(2026, 9, 26, 23, 0))
m5._step_time("minute", 1)
check("按步长步进（37 -> 40）", m5.value, datetime.datetime(2026, 9, 26, 9, 40))
m5._step_time("minute", -2)
check("按步长步进（40 -> 30）", m5.value, datetime.datetime(2026, 9, 26, 9, 30))

print("\n== set_time 只改提到的字段 ==")
p = DateTimeInput(value=datetime.datetime(2026, 9, 26, 9, 30, 15), with_seconds=True)
p.set_time(hour=21)
check("只改小时", p.value, datetime.datetime(2026, 9, 26, 21, 30, 15))
p.set_time(second=5)
check("只改秒", p.value, datetime.datetime(2026, 9, 26, 21, 30, 5))
p.set_time()
check("空调用不变", p.value, datetime.datetime(2026, 9, 26, 21, 30, 5))

print("\n== 月历钩子 ==")
c = DateTimeInput(value=datetime.datetime(2026, 9, 26, 9, 30))
check("日期格高亮看日期部分", c._cal_is_selected(datetime.date(2026, 9, 26)), True)
check("其它日期不高亮", c._cal_is_selected(datetime.date(2026, 9, 25)), False)
c._cal_pick(datetime.date(2026, 10, 5))
check("点日期只改日期、保留时间", c.value, datetime.datetime(2026, 10, 5, 9, 30))
check("点日期后面板仍展开（未收起）", c.is_open, False)
c.open()
check("open 后展开", c.is_open, True)
c._cal_pick(datetime.date(2026, 11, 5))
check("open 态下点日期不收起", c.is_open, True)
check("点日期同步视图月份", (c._view_year, c._view_month), (2026, 11))
c._cal_toggle_mode()
check("切年月网格", c._mode, "month")
c._cal_shift_year(2)
check("网格翻年", c._view_year, 2028)
c._cal_select_month(3)
check("选月回月历", (c._mode, c._view_month), ("day", 3))
c._cal_shift_month(11)
check("跨年翻月", (c._view_year, c._view_month), (2029, 2))
check("年月网格：范围外的月禁用",
      DateTimeInput(value=datetime.datetime(2026, 9, 10),
                    min_datetime=lo, max_datetime=hi)._cal_month_enabled(8), False)
c.close()
check("close 后收起", c.is_open, False)

print("\n== on_change 去重 ==")
seen: list[object] = []
e = DateTimeInput(value=datetime.datetime(2026, 9, 26, 9, 30), on_change=seen.append)
e.set_time(hour=9)
check("同值不回调", seen, [])
e.set_time(hour=10)
e.set_time(hour=10)
check("改一次只回调一次", seen, [datetime.datetime(2026, 9, 26, 10, 30)])
e._cal_pick(datetime.date(2026, 9, 26))
check("点回同一天不重复回调", len(seen), 1)
e.clear()
e.clear()
check("清空回调一次", seen, [datetime.datetime(2026, 9, 26, 10, 30), None])
check("清空后 value 为 None", e.value, None)
check("清空后 display_text 为空", e.display_text, "")

print("\n== 键入解析（含边界钳制）==")
b2 = DateTimeInput(value=datetime.datetime(2026, 9, 10, 14, 0),
                   min_datetime=lo, max_datetime=hi)
check("合法键入", b2._parse("2026-09-11 09:05"), datetime.datetime(2026, 9, 11, 9, 5))
check("越界键入被拒", b2._parse("2026-09-25 09:05"), None)
check("只给时间保留日期", b2._parse("09:05"), datetime.datetime(2026, 9, 10, 9, 5))
check("非法键入被拒", b2._parse("hello"), None)
check("键入秒被规整掉", b2._parse("2026-09-11 09:05:30"),
      datetime.datetime(2026, 9, 11, 9, 5))

print("\n== 面板尺寸 ==")
check("无秒面板宽", DateTimeInput()._panel_w(), 367)
check("有秒面板宽", DateTimeInput(with_seconds=True)._panel_w(), 417)
check("面板高与 DateInput 一致（309）", DateTimeInput()._panel_h(), 309)

print()
if FAILED:
    print(f"RESULT: {len(FAILED)} FAILED -> {FAILED}")
    sys.exit(1)
print("RESULT: ALL PASS")
