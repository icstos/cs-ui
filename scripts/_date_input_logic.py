"""DateInput 逻辑层单测（无 GUI）：解析、范围约束、键入提交流程。"""

from __future__ import annotations

import datetime
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ui.input.date_input import DateInput, _parse_date, _get_days_in_month  # noqa: E402

ok = True


def check(name: str, got, want) -> None:
    global ok
    good = got == want
    ok = ok and good
    print(f"{'PASS' if good else 'FAIL'}  {name}: got={got!r} want={want!r}")


print("== _parse_date ==")
for text, want in [
    ("2026-09-26", datetime.date(2026, 9, 26)),
    ("2026/9/26", datetime.date(2026, 9, 26)),
    ("2026.9.26", datetime.date(2026, 9, 26)),
    ("20260926", datetime.date(2026, 9, 26)),
    ("2026年9月26日", datetime.date(2026, 9, 26)),
    ("2026 年 9 月 26 日", datetime.date(2026, 9, 26)),
    ("  2026-9-26  ", datetime.date(2026, 9, 26)),
    ("2026-02-30", None),
    ("2026-13-01", None),
    ("2026-09", None),
    ("", None),
    (None, None),
    ("abc", None),
]:
    check(f"parse {text!r}", _parse_date(text), want)

print("\n== _get_days_in_month ==")
check("2024-02 闰年", _get_days_in_month(2024, 2), 29)
check("2026-02 平年", _get_days_in_month(2026, 2), 28)
check("1900-02 整百非闰", _get_days_in_month(1900, 2), 28)
check("2000-02 整400闰", _get_days_in_month(2000, 2), 29)
check("2026-04", _get_days_in_month(2026, 4), 30)

print("\n== 键入流程 ==")
d = DateInput(value=datetime.date(2026, 9, 26))
d._on_text_change(SimpleNamespace(data="2026-10-01"))
check("键入合法 → value 同步", d.value, datetime.date(2026, 10, 1))
check("键入过程中不丢弃原文", d._text, "2026-10-01")

d._on_text_change(SimpleNamespace(data="2026-10-0"))
check("键入半截 → value 保持", d.value, datetime.date(2026, 10, 1))

d._on_text_change(SimpleNamespace(data="2026-9-16"))
d._on_text_submit(SimpleNamespace(data=None))
check("回车提交 → _text 清空", d._text, None)
check("回车提交 → value", d.value, datetime.date(2026, 9, 16))
check("回车提交 → 无错标记", d._invalid, False)

d._on_text_change(SimpleNamespace(data="不是日期"))
d._on_text_submit(SimpleNamespace(data=None))
check("非法回车 → 标红", d._invalid, True)
check("非法回车 → value 不被改坏", d.value, datetime.date(2026, 9, 16))
check("非法回车 → 原文清空（还原格式化值）", d.display_text, "2026-09-16")

d._on_text_change(SimpleNamespace(data="2026/11/2"))
check("再次编辑清掉标红", d._invalid, False)
d._on_text_blur(SimpleNamespace(data=None))
check("失焦 → 放弃未提交内容", (d._text, d.value), (None, datetime.date(2026, 11, 2)))

print("\n== 范围约束 ==")
b = DateInput(
    value=datetime.date(2026, 9, 10),
    min_date=datetime.date(2026, 9, 5),
    max_date=datetime.date(2026, 9, 20),
)
check("范围内可选", b._accepts(datetime.date(2026, 9, 5)), True)
check("下界内可选", b._accepts(datetime.date(2026, 9, 4)), False)
check("上界内可选", b._accepts(datetime.date(2026, 9, 21)), False)
b.select(datetime.date(2027, 1, 1))
check("越界 select 被拒", b.value, datetime.date(2026, 9, 10))

print("\n== year_range 兜底 ==")
r = DateInput()
check("默认下界", r._min, datetime.date(1900, 1, 1))
check("默认上界", r._max, datetime.date(2100, 12, 31))
check("默认空值", r.value, None)
check("空值时 display_text", r.display_text, "")
check("乱序 year_range 也能兜住", DateInput(year_range=(2100, 1900))._min,
      datetime.date(1900, 1, 1))

print("\n== 显示格式 ==")
f = DateInput(value=datetime.date(2026, 2, 28), display_format="%Y/%m/%d")
check("自定义格式", f.display_text, "2026/02/28")

print("\n== 面板状态机 ==")
s = DateInput(value=datetime.date(2026, 9, 10))
s.open()
check("open 后 is_open", s.is_open, True)
check("open 同步视图月份", (s._view_year, s._view_month), (2026, 9))
s._toggle_mode()
check("切到年月网格", s._mode, "month")
s._shift_year(2)
check("网格里翻年", s._view_year, 2028)
s._select_month(3)
check("选月回到月历", (s._mode, s._view_month), ("day", 3))
s._shift_month(11)
check("跨年翻月", (s._view_year, s._view_month), (2029, 2))
s._shift_month(-14)
check("反向跨年翻月", (s._view_year, s._view_month), (2027, 12))
s._shift_month(-12)
check("回到 2026-12", (s._view_year, s._view_month), (2026, 12))
s.close()
check("close 后 is_open", s.is_open, False)

s2 = DateInput()
s2.open()
check("空值时 open 落在今天", (s2._view_year, s2._view_month),
      (datetime.date.today().year, datetime.date.today().month))

print("\n== 网格起点（周一为首日）==")
g = DateInput()
g._view_year, g._view_month = 2026, 9
check("2026-09 网格起点 = 2026-08-31", g._grid_start(), datetime.date(2026, 8, 31))
g.first_day_weekday = 6
check("周日起头 → 2026-08-30", g._grid_start(), datetime.date(2026, 8, 30))
check("周日起头的表头", g._weekday_sequence(), ["日", "一", "二", "三", "四", "五", "六"])
g.first_day_weekday = 0
check("周一为表头首列", g._weekday_sequence(), ["一", "二", "三", "四", "五", "六", "日"])

print("\n== on_change 去重 ==")
seen: list = []
e1 = DateInput(value=datetime.date(2026, 9, 16), on_change=seen.append)
e1.select(datetime.date(2026, 9, 16))
check("重复选中同一值不回调", seen, [])
e1.select(datetime.date(2026, 9, 17))
check("换值回调一次", seen, [datetime.date(2026, 9, 17)])
e1.clear()
check("清空回调一次", seen, [datetime.date(2026, 9, 17), None])
e1.clear()
check("重复清空不回调", len(seen), 2)
e1._on_text_change(SimpleNamespace(data="2026-10-02"))
check("键入合法即广播", seen[-1], datetime.date(2026, 10, 2))
e1._on_text_change(SimpleNamespace(data="2026-10-02"))
check("键入同值不重复广播", len(seen), 3)
e1._on_text_change(SimpleNamespace(data="乱七八糟"))
check("键入非法不广播", len(seen), 3)
check("键入非法保留上一个合法值", e1.value, datetime.date(2026, 10, 2))

print("\n== 自定义星期标签 ==")
w = DateInput(weekday_labels=("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"))
check("英文标签不改语义", w._weekday_sequence(),
      ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"])

print("\nRESULT:", "ALL PASS" if ok else "HAS FAILURES")
sys.exit(0 if ok else 1)
