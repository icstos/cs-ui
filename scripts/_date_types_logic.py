"""DateInput 多类型逻辑层单测（无 GUI）。

覆盖 ``type`` 引入的九种语义：单值四种、多选三种、范围两种 —— 值的规整与还原、
显示文本、点选流程、粒度下钻、越界拒绝、区间连条标记。

用法::

    python scripts/_date_types_logic.py
"""

from __future__ import annotations

import datetime
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ui.core.i18n import set_locale  # noqa: E402
from ui.input.calendar_panel import DayMark  # noqa: E402
from ui.input.date_input import (  # noqa: E402
    DateInput,
    _parse_month,
    _parse_year,
    week_bounds,
)

set_locale("zh-CN")
D = datetime.date
ok = True


def check(name: str, got, want) -> None:
    global ok
    good = got == want
    ok = ok and good
    print(f"{'PASS' if good else 'FAIL'}  {name}: got={got!r} want={want!r}")


def _raises(fn) -> bool:
    try:
        fn()
    except ValueError:
        return True
    return False



# ---------------------------------------------------------------------------
print("== 值的规整（入参 -> 规范形状）==")
check("month 夹到 1 号", DateInput(type="month", value=D(2026, 9, 26)).value, D(2026, 9, 1))
check("year 夹到 1-1", DateInput(type="year", value=D(2026, 9, 26)).value, D(2026, 1, 1))
check("datetime 取日期", DateInput(value=datetime.datetime(2026, 9, 26, 9)).value, D(2026, 9, 26))
check("多值去重升序", DateInput(type="dates", value=[D(2026, 9, 8), D(2026, 9, 1), D(2026, 9, 8)]).value,
      [D(2026, 9, 1), D(2026, 9, 8)])
check("多月份对齐", DateInput(type="months", value=[D(2026, 9, 20)]).value, [D(2026, 9, 1)])
check("多年份对齐", DateInput(type="years", value=[D(2026, 7, 3)]).value, [D(2026, 1, 1)])
check("范围两端换序", DateInput(type="daterange", value=(D(2026, 9, 20), D(2026, 9, 1))).value,
      (D(2026, 9, 1), D(2026, 9, 20)))
check("范围半填保留", DateInput(type="daterange", value=(D(2026, 9, 1), None)).value,
      (D(2026, 9, 1), None))
check("范围空 -> None", DateInput(type="daterange").value, None)
check("非法类型报错", _raises(lambda: DateInput(type="century")), True)


# ---------------------------------------------------------------------------
print("== 显示文本 ==")
check("周", DateInput(type="week", value=D(2026, 9, 26)).display_text, "2026 年第 39 周")
check("月", DateInput(type="month", value=D(2026, 9, 1)).display_text, "2026年9月")
check("年", DateInput(type="year", value=D(2026, 1, 1)).display_text, "2026年")
check("多日期截断", DateInput(type="dates", value=[D(2026, 9, 1), D(2026, 9, 8), D(2026, 9, 15)]).display_text,
      "2026-09-01、+2")
check("多月不截断", DateInput(type="months", value=[D(2026, 1, 1), D(2026, 3, 1)]).display_text,
      "2026年1月、2026年3月")
check("日期范围", DateInput(type="daterange", value=(D(2026, 9, 1), D(2026, 9, 20))).display_text,
      "2026-09-01 ~ 2026-09-20")
check("月份范围", DateInput(type="monthrange", value=(D(2026, 3, 1), D(2026, 9, 1))).display_text,
      "2026年3月 ~ 2026年9月")
check("半填带连接符", DateInput(type="daterange", value=(D(2026, 9, 1), None)).display_text,
      "2026-09-01 ~ ")
check("空值空串", DateInput(type="years").display_text, "")

# ---------------------------------------------------------------------------
print("== 周的计算（ISO 周号在两种首日下都成立）==")
check("周一起：9-26 所在周", week_bounds(D(2026, 9, 26), 0),
      (D(2026, 9, 21), 2026, 39))
check("周日起：9-26 所在周", week_bounds(D(2026, 9, 26), 6),
      (D(2026, 9, 20), 2026, 39))
check("跨年周（2027-01-01 属 2026 第 53 周）", week_bounds(D(2027, 1, 1), 0)[1:], (2026, 53))

# ---------------------------------------------------------------------------
print("== 单值点选 ==")
d = DateInput(type="date", value=D(2026, 9, 1))
d._cal_pick(D(2026, 9, 26))
check("选中并收起", (d.value, d.is_open), (D(2026, 9, 26), False))

w = DateInput(type="week", value=D(2026, 9, 1))
w._cal_pick(D(2026, 9, 24))  # 周四 -> 所在周一 9-21
check("点周内任意一天 -> 整周锚点", w.value, D(2026, 9, 21))

m = DateInput(type="month", value=D(2026, 1, 1))
m._cal_pick_month(2026, 9)
check("月份点选", m.value, D(2026, 9, 1))

y = DateInput(type="year", value=D(2020, 1, 1))
y._cal_pick_year(2026)
check("年份点选", y.value, D(2026, 1, 1))

# ---------------------------------------------------------------------------
print("== 多选点选 ==")
s = DateInput(type="dates")
s._cal_pick(D(2026, 9, 8))
s._cal_pick(D(2026, 9, 1))
check("多选按序收集", s.value, [D(2026, 9, 1), D(2026, 9, 8)])
s._cal_pick(D(2026, 9, 8))
check("再点一次取消", s.value, [D(2026, 9, 1)])
check("多选不自动收起", s.is_open, False)  # 从未 open 过，保持关闭

sm = DateInput(type="months")
sm._cal_pick_month(2026, 9)
sm._cal_pick_month(2026, 3)
check("多月份收集", sm.value, [D(2026, 3, 1), D(2026, 9, 1)])

sy = DateInput(type="years")
sy._cal_pick_year(2026)
sy._cal_pick_year(2024)
sy._cal_pick_year(2026)
check("多年份切换", sy.value, [D(2024, 1, 1)])

# ---------------------------------------------------------------------------
print("== 范围点选 ==")
r = DateInput(type="daterange")
r._cal_pick(D(2026, 9, 20))
check("第一下记起点", r.value, (D(2026, 9, 20), None))
r._cal_pick(D(2026, 9, 10))
check("第二下补终点并换序", r.value, (D(2026, 9, 10), D(2026, 9, 20)))
check("范围选完收起", r.is_open, False)
r._cal_pick(D(2026, 10, 5))
check("第三下重新开始", r.value, (D(2026, 10, 5), None))

mr = DateInput(type="monthrange")
mr._cal_pick_month(2026, 9)
mr._cal_pick_month(2027, 3)
check("月份范围跨年", mr.value, (D(2026, 9, 1), D(2027, 3, 1)))

# ---------------------------------------------------------------------------
print("== 区间连条标记 ==")
r = DateInput(type="daterange", value=(D(2026, 9, 10), D(2026, 9, 20)))
check("起点：实心 + 左圆角", r._cal_marks(D(2026, 9, 10)),
      DayMark(selected=True, band=True, round_left=True, round_right=False))
check("中间：只有带子", r._cal_marks(D(2026, 9, 15)),
      DayMark(selected=False, band=True, round_left=False, round_right=False))
check("终点：实心 + 右圆角", r._cal_marks(D(2026, 9, 20)),
      DayMark(selected=True, band=True, round_left=False, round_right=True))
check("区间外无标记", r._cal_marks(D(2026, 9, 21)), DayMark())

rh = DateInput(type="daterange", value=(D(2026, 9, 1), None))
rh._hover_day = D(2026, 9, 5)
check("半填时悬停预览", rh._cal_marks(D(2026, 9, 3)),
      DayMark(selected=False, band=True, round_left=False, round_right=False))
check("预览终点画实心", rh._cal_marks(D(2026, 9, 5)).selected, True)

wk = DateInput(type="week", value=D(2026, 9, 23))
check("整周连条（周三）", wk._cal_marks(D(2026, 9, 22)).band, True)
check("邻周不连", wk._cal_marks(D(2026, 9, 28)).band, False)
check("锚点当天实心", wk._cal_marks(D(2026, 9, 23)).selected, True)

# ---------------------------------------------------------------------------
print("== 粒度下钻 ==")
z = DateInput(type="date", value=D(2026, 9, 26))
check("起始粒度", z._mode, "day")
z._cal_zoom_out()
check("日 -> 月", (z._mode, z._view_year), ("month", 2026))
z._cal_zoom_out()
check("月 -> 年", z._mode, "year")
z._cal_zoom_out()
check("年到顶不再放大", z._mode, "year")
check("年网格标题区间起点", z._cal_views()[0][0] - z._cal_views()[0][0] % 12, 2016)
z._cal_select_year(2024)
check("选年落到月网格", (z._mode, z._view_year), ("month", 2024))
z._cal_select_month(3)
check("选月落到日视图", (z._mode, z._view_month), ("day", 3))

mo = DateInput(type="month", value=D(2026, 9, 1))
check("月份选择器起始粒度", mo._mode, "month")
mo._cal_zoom_out()
check("月份选择器可到年", mo._mode, "year")

yr = DateInput(type="year", value=D(2026, 1, 1))
check("年份选择器起始粒度", yr._mode, "year")
yr._cal_zoom_out()
check("年份选择器不再放大", yr._mode, "year")

# ---------------------------------------------------------------------------
print("== 面板列数与宽度 ==")
check("单值一列", DateInput()._cal_view_count(), 1)
check("日期范围两列", DateInput(type="daterange")._cal_view_count(), 2)
check("月份范围两列", DateInput(type="monthrange")._cal_view_count(), 2)
check("范围双列相差一月", DateInput(type="daterange", value=(D(2026, 9, 1), None))._views,
      [(2026, 9), (2026, 10)])
check("月份范围双列相差一年", DateInput(type="monthrange", value=(D(2026, 3, 1), None))._views,
      [(2026, 3), (2027, 3)])
check("范围面板更宽", DateInput(type="daterange")._panel_width() > DateInput()._panel_width(), True)

# ---------------------------------------------------------------------------
print("== 翻页（两列整体平移，保持相邻）==")
f = DateInput(type="daterange", value=(D(2026, 12, 1), None))
f._cal_shift_month(1)
check("跨年翻月", f._views, [(2027, 1), (2027, 2)])

# ---------------------------------------------------------------------------
print("== 越界拒绝 ==")
b = DateInput(
    type="daterange", min_date=D(2026, 9, 1), max_date=D(2026, 9, 30)
)
b.select((D(2026, 9, 5), D(2026, 10, 5)))
check("越界范围整体拒绝", b.value, None)
b.select((D(2026, 9, 5), D(2026, 9, 25)))
check("合法范围接受", b.value, (D(2026, 9, 5), D(2026, 9, 25)))

# ---------------------------------------------------------------------------
print("== 键入解析 ==")
for text, want in [
    ("2026-09", D(2026, 9, 1)),
    ("2026/9", D(2026, 9, 1)),
    ("202609", D(2026, 9, 1)),
    ("2026", D(2026, 1, 1)),
    ("2026年9月", D(2026, 9, 1)),
    ("2026-13", None),
    ("", None),
]:
    check(f"_parse_month({text!r})", _parse_month(text), want)
for text, want in [
    ("2026", D(2026, 1, 1)),
    ("2026年", D(2026, 1, 1)),
    ("26", None),
    ("20261", None),
]:
    check(f"_parse_year({text!r})", _parse_year(text), want)
check("范围类型不可键入", DateInput(type="daterange")._editable, False)
check("月份类型可键入", DateInput(type="month")._editable, True)

# ---------------------------------------------------------------------------
print("== on_change 形状 ==")
seen: list[object] = []
m = DateInput(type="months", on_change=seen.append)
m._cal_pick_month(2026, 9)
m._cal_pick_month(2026, 3)
check("多选回调传 list", seen, [[D(2026, 9, 1)], [D(2026, 3, 1), D(2026, 9, 1)]])
seen.clear()
r = DateInput(type="daterange", on_change=seen.append)
r._cal_pick(D(2026, 9, 1))
r._cal_pick(D(2026, 9, 9))
check("范围回调传 tuple", seen,
      [(D(2026, 9, 1), None), (D(2026, 9, 1), D(2026, 9, 9))])

# ---------------------------------------------------------------------------
print("== 清空 / 外部灌值 ==")
c = DateInput(type="dates", value=[D(2026, 9, 1)])
c.clear()
check("多选清空", c.value, [])
c.set_value([D(2026, 9, 5), D(2026, 9, 2)])
check("set_value 规整", c.value, [D(2026, 9, 2), D(2026, 9, 5)])

print()
print("RESULT:", "ALL PASS" if ok else "HAS FAILURES")
sys.exit(0 if ok else 1)
