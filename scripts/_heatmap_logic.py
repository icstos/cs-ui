"""Heatmap 纯逻辑断言（不启窗口）。

覆盖：入参折形、周对齐、列数、色阶层级、显式区间、空白格语义、统计、
坐标反算、tooltip 定宽。渲染期的东西（控件结构、悬停重绘）交给真机探针。

用法::

    python scripts/_heatmap_logic.py
"""

from __future__ import annotations

import datetime as dt
import sys
from itertools import pairwise
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ui.display.heatmap import (
    COLOR_THEMES,
    TIP_MAX_W,
    TIP_MIN_W,
    Heatmap,
    HeatmapItem,
    _as_date,
    _as_item,
    _text_width,
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
# 入参折形
# ---------------------------------------------------------------------------
check("_as_date: date 原样", _as_date(D(2026, 9, 26)), D(2026, 9, 26))
check(
    "_as_date: datetime 取日期",
    _as_date(dt.datetime(2026, 9, 26, 13, 5)),  # noqa: DTZ001 - 故意测无时区的本地时间
    D(2026, 9, 26),
)
check("_as_date: ISO 字符串", _as_date("2026-09-26"), D(2026, 9, 26))
check("_as_date: 带时间的字符串", _as_date("2026-09-26T08:00:00"), D(2026, 9, 26))
check("_as_date: 秒级时间戳", _as_date(1_790_000_000), _as_date(1_790_000_000.0))
check("_as_date: 毫秒时间戳与秒级等价", _as_date(1_790_000_000_000), _as_date(1_790_000_000))
raises("_as_date: 非法类型报错", lambda: _as_date(object()))

check("_as_item: HeatmapItem 原样", _as_item(HeatmapItem(D(2026, 1, 2), 3)).value, 3)
check(
    "_as_item: dict 的 date 键",
    _as_item({"date": D(2026, 1, 2), "value": 5}),
    HeatmapItem(D(2026, 1, 2), 5, None),
)
check(
    "_as_item: dict 的 day 键",
    _as_item({"day": "2026-01-02", "value": 1}),
    HeatmapItem(D(2026, 1, 2), 1, None),
)
check(
    "_as_item: dict 带 data",
    _as_item({"date": D(2026, 1, 2), "value": 1, "data": "x"}).data,
    "x",
)
check("_as_item: 二元组", _as_item((D(2026, 1, 2), 9)), HeatmapItem(D(2026, 1, 2), 9, None))
raises("_as_item: dict 缺日期报错", lambda: _as_item({"value": 1}))
raises("_as_item: 三元组报错", lambda: _as_item((D(2026, 1, 2), 1, 2)))

# ---------------------------------------------------------------------------
# 周对齐与列数
# ---------------------------------------------------------------------------
data = [HeatmapItem(D(2026, 9, 1) + dt.timedelta(days=i), i % 7) for i in range(30)]
for first in (0, 6):
    hm = Heatmap(data=list(data), first_day_of_week=first)
    hm._prepare()
    check(f"首日={first}: 起点对齐到周首", hm._origin.weekday(), first)
    last_cell = hm._origin + dt.timedelta(days=hm._cols * 7 - 1)
    check(f"首日={first}: 终点覆盖数据末日", last_cell >= D(2026, 9, 30), True)
    check(f"首日={first}: 起点不晚于数据首日", hm._origin <= D(2026, 9, 1), True)
    check(
        f"首日={first}: 列数够用且不浪费",
        hm._cols,
        ((last_cell - hm._origin).days // 7) + 1,
    )

hm = Heatmap(data=list(data), first_day_of_week=0)
hm._prepare()
check("列数: 30 天跨 5 周", hm._cols, 5)
check("网格宽 = 列数*格 + 间隙", hm._grid_w, 5 * 12 + 4 * 4)
check("网格高 = 7 格 + 6 间隙", hm._grid_h, 7 * 12 + 6 * 4)

single = Heatmap(data=[HeatmapItem(D(2026, 9, 26), 1)], first_day_of_week=0)
single._prepare()
check("单天数据只要 1 列", single._cols, 1)
check("单天数据网格宽 = 一格", single._grid_w, 12)

empty = Heatmap(data=[])
empty._prepare()
check("空数据不炸", empty._cols, 1)
check("空数据 stats 全 0", empty.stats()["filled"], 0.0)

# ---------------------------------------------------------------------------
# 色阶层级
# ---------------------------------------------------------------------------
hm = Heatmap(
    data=[
        HeatmapItem(D(2026, 9, 1), 0),
        HeatmapItem(D(2026, 9, 2), 10),
        HeatmapItem(D(2026, 9, 3), 20),
        HeatmapItem(D(2026, 9, 4), 40),
    ],
    value_range=(10, 40),
)
hm._prepare()
check("值为 0 → 第 0 级", hm._level(hm.item_at(D(2026, 9, 1))), 0)
check("缺数据 → 第 0 级", hm._level(None), 0)
check("等于下限 → 第 1 级", hm._level(hm.item_at(D(2026, 9, 2))), 1)
check("等于上限 → 最高级", hm._level(hm.item_at(D(2026, 9, 4))), len(hm._ramp))
check(
    "中间值单调不降",
    hm._level(hm.item_at(D(2026, 9, 2))) <= hm._level(hm.item_at(D(2026, 9, 3)))
    <= hm._level(hm.item_at(D(2026, 9, 4))),
    True,
)
check(
    "第 0 级用底板色",
    hm._color_of(hm.item_at(D(2026, 9, 1))),
    hm._min_color,
)
check("超出区间上界仍封顶", hm._level(HeatmapItem(D(2026, 9, 5), 999)), len(hm._ramp))

auto = Heatmap(data=[HeatmapItem(D(2026, 9, 2), 3), HeatmapItem(D(2026, 9, 4), 30)])
auto._prepare()
check("自动区间下限取最小正值", auto._range[0], 3.0)
check("自动区间上限取最大值", auto._range[1], 30.0)

# ---------------------------------------------------------------------------
# 色阶与主题
# ---------------------------------------------------------------------------
check("内置主题齐全", sorted(COLOR_THEMES), ["blue", "green", "orange", "purple", "red"])
for name, pair in COLOR_THEMES.items():
    check(f"{name}: 浅深两套都是 4 级", (len(pair["light"]), len(pair["dark"])), (4, 4))

unknown = Heatmap(data=[HeatmapItem(D(2026, 9, 1), 1)], color_theme="不存在")
unknown._prepare()
check(
    "未知主题回落到默认绿",
    unknown._ramp,
    COLOR_THEMES["green"]["light"],
)
custom = Heatmap(data=[HeatmapItem(D(2026, 9, 1), 1)], active_colors=("#a", "#b", "#c"))
custom._prepare()
check("自定义色阶盖过主题", custom._ramp, ("#a", "#b", "#c"))

# ---------------------------------------------------------------------------
# 空白格语义
# ---------------------------------------------------------------------------
hm = Heatmap(data=[HeatmapItem(D(2026, 9, 10), 1)], first_day_of_week=0)
hm._prepare()
check("区间内的空白天要画", hm._painted(D(2026, 9, 10)), True)
check("区间外的格子不画", hm._painted(D(2026, 8, 31)), False)
check("区间外格子颜色为空", hm._color_of(None), None)

filled = Heatmap(data=[HeatmapItem(D(2026, 9, 10), 1)], fill_calendar_leading=True)
filled._prepare()
check("fill 打开后首尾也画", filled._painted(D(2026, 8, 31)), True)

# ---------------------------------------------------------------------------
# 统计
# ---------------------------------------------------------------------------
hm = Heatmap(
    data=[
        HeatmapItem(D(2026, 9, 1), 4),
        HeatmapItem(D(2026, 9, 2), 0),
        HeatmapItem(D(2026, 9, 3), 8),
    ]
)
st = hm.stats()
check("统计: 天数为区间天数", st["days"], 3.0)
check("统计: 有值天数", st["filled"], 2.0)
check("统计: 空白天数", st["blank"], 1.0)
check("统计: 峰值", st["peak"], 8.0)
check("统计: 均值只算有值的天", st["mean"], 6.0)
check("统计: 总和", st["total"], 12.0)

# ---------------------------------------------------------------------------
# 坐标反算（悬停命中）
# ---------------------------------------------------------------------------
hm = Heatmap(
    data=[HeatmapItem(D(2026, 9, 1) + dt.timedelta(days=i), 1) for i in range(60)],
    first_day_of_week=0,
)
hm._prepare()
pitch_x = hm._cell + hm._gap_x
pitch_y = hm._cell + hm._gap_y
check("左上角命中 (0,0)", hm._hit(0.5, 0.5), (0, 0))
check(
    "第 3 列第 5 行中心命中自己",
    hm._hit(3 * pitch_x + hm._cell / 2, 5 * pitch_y + hm._cell / 2),
    (3, 5),
)
check("越界 x 返回 None", hm._hit(hm._grid_w + 1, 5), None)
check("越界 y 返回 None", hm._hit(5, hm._grid_h + 1), None)
check("负坐标返回 None", hm._hit(-1, 5), None)

# ---------------------------------------------------------------------------
# 月份标签：不重叠、不吞掉整月
# ---------------------------------------------------------------------------
year2026 = [
    HeatmapItem(D(2026, 1, 1) + dt.timedelta(days=i), i % 15) for i in range(365)
]
hm = Heatmap(data=list(year2026), first_day_of_week=0)
hm._prepare()
labels = hm._month_labels()
check("整年 12 个月全在", len(labels), 12)
check("整年从 1 月开始（残月 12 月让位）", labels[0][1], "1月")

pitch = hm._cell + hm._gap_x
overlaps = [
    (a[1], b[1])
    for a, b in pairwise(labels)
    if b[0] * pitch < a[0] * pitch + _text_width(a[1], hm._label_size)
]
check("相邻标签不重叠", overlaps, [])

from_1104 = [
    HeatmapItem(D(2025, 11, 4) + dt.timedelta(days=i), i % 13) for i in range(365)
]
hm2 = Heatmap(data=from_1104, first_day_of_week=0)
hm2._prepare()
labels2 = [label for _, label in hm2._month_labels()]
check("首列残月离得开就保留", labels2[0], "11月")
check("跨年标签连续", labels2[:3], ["11月", "12月", "1月"])

# ---------------------------------------------------------------------------
# tooltip 定宽
# ---------------------------------------------------------------------------
check("CJK 比拉丁宽", _text_width("月月", 11) > _text_width("ab", 11), True)
check("空串宽度为 0", _text_width("", 11), 0.0)
w_short = min(TIP_MAX_W, max(TIP_MIN_W, int(_text_width("2026-09-26 · 3", 11)) + 18))
w_long = min(TIP_MAX_W, max(TIP_MIN_W, int(_text_width("长" * 80, 11)) + 18))
check("短文案不小于最小宽度", w_short >= TIP_MIN_W, True)
check("超长文案被夹在上限", w_long, TIP_MAX_W)

# ---------------------------------------------------------------------------
# 缓存：同参数不重建、换数据要重建
# ---------------------------------------------------------------------------
hm = Heatmap(data=[HeatmapItem(D(2026, 9, 1), 1)])
hm._prepare()
first_stamp = hm._stamp
hm._grid = "grid-sentinel"  # type: ignore[assignment]
hm._prepare()
check("同参数不重建（网格对象保留）", hm._grid, "grid-sentinel")
check("同参数指纹不变", hm._stamp, first_stamp)

hm.data = [HeatmapItem(D(2026, 9, 1), 99)]
hm._prepare()
check("改数值后指纹变化", hm._stamp != first_stamp, True)
check("改数值后网格重建", hm._grid is None, True)

hm.data = [HeatmapItem(D(2026, 9, 1), 99)]
hm._prepare()
kept = hm._stamp
hm.invalidate()
check("invalidate 清掉指纹", hm._stamp, None)
hm._prepare()
check("重建后指纹回到同一个值", hm._stamp, kept)

# ---------------------------------------------------------------------------
print("-- 色阶：由配色引擎派生，不再是一张手写色表 --")
# ---------------------------------------------------------------------------
from ui.core.color import luminance  # noqa: E402
from ui.core.tokens import PRIMARY_SEEDS  # noqa: E402
from ui.display.heatmap import SCALE_ANCHORS, SCALE_STEPS  # noqa: E402

check("色阶级数是 4", SCALE_STEPS, 4)
check("主题数与锚色数一致", sorted(COLOR_THEMES), sorted(SCALE_ANCHORS))
check("锚色全部来自品牌色板",
      all(v in PRIMARY_SEEDS.values() for v in SCALE_ANCHORS.values()), True)
for name, scale in SCALE_ANCHORS.items():
    modes = COLOR_THEMES[name]
    check(f"{name} 明暗两套齐全", sorted(modes), ["dark", "light"])
    for mode in ("light", "dark"):
        values = modes[mode]
        check(f"{name}/{mode} 四级", len(values), 4)
        check(f"{name}/{mode} 末级即锚色", values[-1], scale)
        lums = [luminance(c) for c in values]
        strictly = all(a < b for a, b in pairwise(lums)) if mode == "dark" \
            else all(a > b for a, b in pairwise(lums))
        check(f"{name}/{mode} 明度单调（量级不会被读反）", strictly, True)

print()
print(f"{_passes} passed, {_fails} failed")
print("RESULT:", "ALL PASS" if _fails == 0 else "FAILED")
sys.exit(0 if _fails == 0 else 1)
