"""Rating 的行为不变量（纯逻辑，不需要窗口）。

这一份主要守住一个**曾经反掉的判断**：星标回调的挂载条件写成了
``None if self._interactive else handler`` —— 可交互的星一个处理器都没有，
只读/禁用的反而全挂上。于是文档站里悬停「只读展示」示例时会进 ``_handle_hover``，
而那时整棵 component 树是冻结的，``icon.icon = ...`` 直接抛
``Frozen controls cannot be updated``。

要测的不是色值，而是三件事：

1. **谁能挂处理器** —— 只有可交互的实例挂，只读/禁用一个都不挂；
2. **冻结时不写自己** —— 冻结树里写属性会抛异常，且 patch 会跳过整棵子树，
   此时只能把结果交给 ``on_change`` / ``on_preview``；
3. **分数归一** —— 夹紧、按精度吸附、0 归一成未评分。

用法::

    python scripts/_rating_logic.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import flet as ft

from ui.input.rating import (
    STAR_EMPTY,
    STAR_FULL,
    STAR_HALF,
    Rating,
)

_fails: list[str] = []
_passed = 0


def check(name: str, got: object, want: object) -> None:
    global _passed
    if got == want:
        _passed += 1
        print(f"PASS  {name}: got={got!r}")
    else:
        _fails.append(f"{name}: got={got!r} want={want!r}")
        print(f"FAIL  {name}: got={got!r} want={want!r}")


def check_true(name: str, ok: bool, detail: str = "") -> None:
    global _passed
    if ok:
        _passed += 1
        print(f"PASS  {name}{('  ' + detail) if detail else ''}")
    else:
        _fails.append(f"{name}{('  ' + detail) if detail else ''}")
        print(f"FAIL  {name}{('  ' + detail) if detail else ''}")


def section(title: str) -> None:
    print(f"\n== {title} ==")


def _freeze(*controls: ft.Control) -> None:
    """模拟 flet 在 @ft.component 渲染后给整棵子树打的冻结标记。"""
    for control in controls:
        object.__setattr__(control, "_frozen", True)


def _hover_event(index: int, entering: bool) -> SimpleNamespace:
    return SimpleNamespace(data="true" if entering else "false", control=SimpleNamespace(data=index))


def _stub_update(control: Rating) -> list[int]:
    """把 ``update()`` 打桩：未挂到 page 的控件调它必抛，这里只关心调用次数。"""
    calls: list[int] = []
    control.update = lambda: calls.append(1)  # type: ignore[method-assign]
    return calls


# ---------------------------------------------------------------------------
section("处理器挂载：可交互才挂（曾经反了）")

live = Rating(value=3)
check_true(
    "可交互示例每颗星都挂了悬停",
    all(star.on_hover is not None for star in live.controls),
)
check_true(
    "可交互示例每颗星都挂了点击",
    all(star.on_tap_down is not None for star in live.controls),
)

for label, kwargs in (
    ("只读", {"readonly": True}),
    ("禁用", {"disabled": True}),
):
    quiet = Rating(value=4, **kwargs)
    check_true(
        f"{label}不挂悬停（否则会在冻结树里撞上写属性）",
        all(star.on_hover is None for star in quiet.controls),
    )
    check_true(
        f"{label}不挂点击",
        all(star.on_tap_down is None for star in quiet.controls),
    )

# ---------------------------------------------------------------------------
section("分数归一：夹紧 / 吸附 / 0 归一")

check("超上界夹到 elements", Rating(value=9).value, 5.0)
check("负数归一成未评分", Rating(value=-2).value, None)
check("0 归一成未评分", Rating(value=0).value, None)
check("整星精度下 3.6 吸附到 4", Rating(value=3.6).value, 4.0)
check("半星精度下 3.6 吸附到 3.5", Rating(value=3.6, precision=0.5).value, 3.5)
check("precision 落在 (0,1) 一律按半星", Rating(value=3.4, precision=0.7).precision, 0.5)

# ---------------------------------------------------------------------------
section("图标：按剩余量分档")

icons = [icon.icon for icon in Rating(value=3.5, precision=0.5)._icons]
check(
    "3.5 分 = 3 整 + 1 半 + 1 空",
    icons,
    [STAR_FULL, STAR_FULL, STAR_FULL, STAR_HALF, STAR_EMPTY],
)
check("5 分全是整星", [icon.icon for icon in Rating(value=5)._icons], [STAR_FULL] * 5)
check("未评分全是空星", [icon.icon for icon in Rating(value=None)._icons], [STAR_EMPTY] * 5)
check("元素个数可调", len(Rating(value=2, elements=3)._icons), 3)

# ---------------------------------------------------------------------------
section("冻结树里不写自己，把结果交给回调")

got: list[object] = []
frozen = Rating(value=2, on_change=got.append)
_freeze(frozen)
check_true("确实处于冻结态", frozen._frozen_tree)
frozen._set(4.0)
check("冻结时 value 不被改写（写了会抛异常）", frozen.value, 2.0)
check("冻结时回调照常收到分数", got, [4.0])

# ---------------------------------------------------------------------------
section("冻结 + 无受控通道：悬停静默降级，不抛异常")

froze = Rating(value=1)
_freeze(froze)
froze._handle_hover(_hover_event(2, True))
check("没有炸，也没有留下本地预览", froze._local_preview, None)
check_true("画的仍是真实值", froze._shown() == 1.0)

# ---------------------------------------------------------------------------
section("受控预览：外部给什么就画什么")

seen: list[object] = []
controlled = Rating(value=1, on_preview=seen.append)
controlled._handle_hover(_hover_event(2, True))
check("悬停把意图交给 on_preview", seen, [3.0])
check("受控模式下组件自己不记预览", controlled._local_preview, None)
check_true("preview 参数生效", Rating(value=1, preview=4)._shown() == 4.0)
check("preview 也会被归一", Rating(value=1, preview=9).preview, 5.0)

# ---------------------------------------------------------------------------
section("非冻结路径：预览与落分都会重画自己")

plain = Rating(value=2)
updates = _stub_update(plain)
plain._handle_hover(_hover_event(3, True))
check("本地预览记下了第 4 颗", plain._local_preview, 4.0)
check_true("画的是预览而不是真实值", plain._shown() == 4.0)
check("悬停触发一次重绘", len(updates), 1)
plain._handle_hover(_hover_event(3, False))
check("移开恢复到真实值", plain._local_preview, None)
check_true("恢复后画真实值", plain._shown() == 2.0)
check("移开也重绘一次", len(updates), 2)

# 从第 3 颗滑到第 4 颗时，第 3 颗的「移出」不该抹掉第 4 颗刚点亮的预览
slide = Rating(value=0)
_stub_update(slide)
slide._handle_hover(_hover_event(2, True))
slide._handle_hover(_hover_event(3, True))
slide._handle_hover(_hover_event(2, False))
check("相邻切星时预览不被前一颗的移出抹掉", slide._local_preview, 4.0)

# ---------------------------------------------------------------------------
print(f"\n{_passed} passed, {len(_fails)} failed")
if _fails:
    for f in _fails:
        print("  -", f)
    raise SystemExit(1)
