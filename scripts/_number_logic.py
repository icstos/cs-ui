"""NumberAnimation 纯逻辑断言（不启窗口）。

覆盖：格式化（千分位 / 小数位 / 符号位 / 前后缀 / 空分隔符）、缓动曲线的端点与
单调性、显示值的取整、起跑判定、中途换目标、``on_finish`` 只触发一次、
"字符串没变就不发"的推送优化。

真正的观感（滚起来顺不顺）交给真机探针。

用法::

    python scripts/_number_logic.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ui.display.number_animation import (
    EASINGS,
    NumberAnimation,
    ease_in_out,
    ease_out_cubic,
    format_value,
)

_fails = 0
_passes = 0


def check(name: str, got: object, want: object) -> None:
    global _fails, _passes
    if got == want:
        _passes += 1
        print(f"PASS  {name}")
    else:
        _fails += 1
        print(f"FAIL  {name}\n        期望 {want!r}\n        实际 {got!r}")


# ---------------------------------------------------------------------------
print("=== 格式化 ===")
check("整数加千分位", format_value(1286), "1,286")
check("零", format_value(0), "0")
check("负数", format_value(-42), "-42")
check("小数默认取整", format_value(1234.5678), "1,235")
check("两位小数", format_value(1234.5678, precision=2), "1,234.57")
check(
    "千分位只加在整数段",
    format_value(1234.5678, precision=2, separator=" "),
    "1 234.57",
)
check("关闭分组", format_value(1234567, separator=""), "1234567")
check("自定义分隔符", format_value(1234567, separator="_"), "1_234_567")
check("前缀", format_value(1200, prefix="¥"), "¥1,200")
check("后缀", format_value(0.5, precision=1, suffix="%"), "0.5%")
check("负号在前缀之前", format_value(-1200, prefix="¥"), "-¥1,200")
check("-0.004 不留负号", format_value(-0.004), "0")
check("-0.004 保留两位仍是 0", format_value(-0.004, precision=2), "0.00")
check("负的零保留位仍是 0", format_value(-0.0), "0")
check("precision 负数当 0", format_value(9.6, precision=-2), "10")
check("极小值不会被写成科学计数", format_value(0.000123, precision=6), "0.000123")
check("大数", format_value(1234567890), "1,234,567,890")

print()
print("=== 缓动 ===")
check("ease-out 起点", round(ease_out_cubic(0.0), 6), 0.0)
check("ease-out 终点", round(ease_out_cubic(1.0), 6), 1.0)
check("ease-in-out 起点", round(ease_in_out(0.0), 6), 0.0)
check("ease-in-out 中点", round(ease_in_out(0.5), 6), 0.5)
check("ease-in-out 终点", round(ease_in_out(1.0), 6), 1.0)
check("ease-out 前段快于线性", ease_out_cubic(0.25) > 0.25, True)
check(
    "ease-out 全程单调",
    all(ease_out_cubic(i / 50) < ease_out_cubic((i + 1) / 50) for i in range(50)),
    True,
)
check("表里有 linear", round(EASINGS["linear"](0.37), 6), 0.37)

print()
print("=== 起跑与取整 ===")
a = NumberAnimation(end=1286, duration=0)
check("构造时显示 start", a.value, 0)
check("标签跟着显示值", a._label(), "0")
a._snap(1286)
check("落位后等于 end", a.value, 1286)
check("落位后的标签", a._label(), "1,286")

b = NumberAnimation(end=1234.567, precision=0)
check("没有小数位时取整到 0 位", b.value, 0)
b._snap(1234.567)
check("_snap 也按 precision 取整", b.value, 1235)
check("已经到达就不该再起一轮", b._shown == round(b.end, b._places), True)

c = NumberAnimation(end=0.2846, precision=3, suffix="%", separator="")
c._snap(0.2846)
check("小数三位 + 后缀", c._label(), "0.285%")

print()
print("=== 重绘节流：屏幕上那串字没变就不重绘 ===")


class Counter(NumberAnimation):
    """数一下自己被要求重绘了几次。"""

    paints: int = 0

    def _repaint(self) -> None:
        self.paints += 1


d = Counter(end=1000)
object.__setattr__(d, "_label_shown", "0")
for value in (1.2, 1.4, 1.6, 2.1):
    d._show(value)
check("四个中间值只重绘两次（1 / 2）", d.paints, 2)
check("最后停在 2", d._label(), "2")

d._show(2.0)
check("值变但字没变，不重绘", d.paints, 2)

print()
print("=== 跑一轮：终点、回调、中途换目标 ===")


def run(coro):
    return asyncio.run(coro)


e = NumberAnimation(end=100, duration=1)
done: list[int] = []
e.on_finish = lambda: done.append(1)
run(e._run(0))
check("落定于 end", e.value, 100)
check("on_finish 只触发一次", len(done), 1)

f = NumberAnimation(end=10, duration=0)
run(f._run(0))
check("duration 为 0 直接落位", f.value, 10)


async def retarget() -> NumberAnimation:
    g = NumberAnimation(end=1000, duration=240)
    object.__setattr__(g, "_token", 1)
    task = asyncio.ensure_future(g._run(1))
    await asyncio.sleep(0.08)
    mid = g.value
    g.end = 40  # 跑到一半改目标
    await task
    assert 0 < mid < 1000, mid
    return g


g = run(retarget())
check("中途换目标后落在新终点", g.value, 40)


async def early_stop() -> tuple[float, int]:
    """token 失效（play / 卸载）后旧的一轮必须停手。"""
    h = NumberAnimation(end=1000, duration=240)
    object.__setattr__(h, "_token", 2)
    task = asyncio.ensure_future(h._run(2))
    await asyncio.sleep(0.06)
    frozen = h.value
    object.__setattr__(h, "_token", 3)  # 作废
    await task
    return frozen, h.value


frozen, after = run(early_stop())
check("作废后不再往前走", after, frozen)
check("确实停在了中途", frozen < 1000, True)

print()
print("=== play 从 start 重来 ===")
k = NumberAnimation(end=500, start=100, duration=0)
k._snap(500)
k._launch = lambda: None  # 不排真定时器，只看状态
k.play()
check("play 把显示值拉回 start", k.value, 100)

print()
print("==============================================")
print(f"{_passes} passed, {_fails} failed")
raise SystemExit(1 if _fails else 0)
