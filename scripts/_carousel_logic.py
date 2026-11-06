"""Carousel 纯逻辑断言（不启窗口）。

覆盖：索引归一（绕回 / 夹边 / 空集）、单步推进的"瞬移"标记、线性排布的位置
映射、构造期参数校验、切页的各种边界与回调语义、悬停载荷解析、自动播放的
暂停判定。

配色、动画、命中区属于渲染期，交给 smoke_test 与真机探针。

用法::

    python scripts/_carousel_logic.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import flet as ft

from ui.display.carousel import (
    Carousel,
    _entering,
    normalize_index,
    slide_offsets,
    step_index,
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
        print(f"FAIL  {name}: got={got!r} want={want!r}")


def raises(name: str, fn, kind: type[BaseException]) -> None:
    """断言一定会抛某类异常 —— 参数校验比"能跑"更需要钉住。"""
    global _fails, _passes
    try:
        fn()
    except kind:
        _passes += 1
        print(f"PASS  {name}")
    except BaseException as exc:  # noqa: BLE001 - 报出实际类型才好定位
        _fails += 1
        print(f"FAIL  {name}: 抛了 {type(exc).__name__}，期望 {kind.__name__}")
    else:
        _fails += 1
        print(f"FAIL  {name}: 没抛异常，期望 {kind.__name__}")


def pages(n: int) -> list[ft.Control]:
    return [ft.Text(f"p{i}") for i in range(n)]


def carousel(n: int = 4, **kwargs) -> Carousel:
    kwargs.setdefault("height", 200)
    return Carousel(slides=pages(n), **kwargs)


def log_changes(**kwargs) -> tuple[Carousel, list[tuple[int, int]]]:
    seen: list[tuple[int, int]] = []
    return carousel(on_change=lambda a, b: seen.append((a, b)), **kwargs), seen


# ---------------------------------------------------------------------------
def test_normalize_index() -> None:
    check("空集归一为 0", normalize_index(7, 0), 0)
    check("负页数归一为 0", normalize_index(2, -3), 0)
    check("默认夹边：负数", normalize_index(-5, 4), 0)
    check("默认夹边：越界", normalize_index(9, 4), 3)
    check("默认夹边：界内不动", normalize_index(2, 4), 2)
    check("loop 绕回：-1", normalize_index(-1, 4, loop=True), 3)
    check("loop 绕回：-9", normalize_index(-9, 4, loop=True), 3)
    check("loop 绕回：+9", normalize_index(9, 4, loop=True), 1)
    check("单页时永远 0", normalize_index(3, 1), 0)


def test_step_index() -> None:
    check("0 页不推进", step_index(0, 1, 0), (0, False))
    check("1 页不推进", step_index(0, 1, 1), (0, False))
    check("界内前进不瞬移", step_index(1, 1, 4), (2, False))
    check("界内后退不瞬移", step_index(2, -1, 4), (1, False))
    check("到头不绕回就停住", step_index(3, 1, 4), (3, False))
    check("开头不绕回就停住", step_index(0, -1, 4), (0, False))
    check("绕回：末页下一张", step_index(3, 1, 4, loop=True), (0, True))
    check("绕回：首页上一张", step_index(0, -1, 4, loop=True), (3, True))
    check("绕回：界内前进不算瞬移", step_index(1, 1, 4, loop=True), (2, False))
    check("绕回：跨两圈", step_index(1, 9, 4, loop=True), (2, True))
    check("绕回：倒退跨圈", step_index(1, -9, 4, loop=True), (0, True))


def test_slide_offsets() -> None:
    check("线性位置：当前页在 0", slide_offsets(4, 2), (-2, -1, 0, 1))
    check("首页", slide_offsets(3, 0), (0, 1, 2))
    check("空集", slide_offsets(0, 0), ())
    check("负页数当空集", slide_offsets(-2, 0), ())
    # 关键性质：任意切页，每张的位移恰好是全体的平移量 —— 动画才会同步
    a, b = slide_offsets(5, 1), slide_offsets(5, 3)
    check(
        "切页 = 全体同幅平移", tuple(x - y for x, y in zip(a, b, strict=True)), (2,) * 5
    )


def test_ctor_validation() -> None:
    raises("arrow 非法", lambda: carousel(arrow="sometimes"), ValueError)
    raises("dots 非法", lambda: carousel(dots="middle"), ValueError)
    raises("dots_position 非法", lambda: carousel(dots_position="centre"), ValueError)
    raises("trigger 非法", lambda: carousel(trigger="drag"), ValueError)
    raises("height 必须为正", lambda: Carousel(slides=pages(2), height=0), ValueError)


def test_initial_state() -> None:
    check("默认第 0 页", carousel(4).current, 0)
    check("初始索引夹边", carousel(4, index=99).current, 3)
    check("初始负索引夹到 0", carousel(4, index=-2).current, 0)
    check("loop 时初始负索引绕回", carousel(4, index=-1, loop=True).current, 3)
    check("页数 = 内容数", carousel(3).count, 3)
    check("空轮播的索引仍是 0", carousel(0, index=5).current, 0)


def test_go() -> None:
    c, seen = log_changes()
    c.go(2)
    check("go 生效", (c.current, seen), (2, [(0, 2)]))
    c.go(2)
    check("go 到当前页不回调", (c.current, len(seen)), (2, 1))
    c.go(99)
    check("go 越界夹到末页", (c.current, seen[-1]), (3, (2, 3)))
    c.go(-5)
    check("go 越界夹到首页", (c.current, seen[-1]), (0, (3, 0)))
    check("普通跳转不瞬移", c._snap, False)


def test_go_loop_jump() -> None:
    c, seen = log_changes(loop=True)
    c.go(3)
    check("loop：界内跳转", (c.current, seen[-1]), (3, (0, 3)))
    check("loop：界内跳转不瞬移", c._snap, False)
    c.go(5)
    check("loop：越界跳转绕回", (c.current, seen[-1]), (1, (3, 1)))
    check("loop：越界跳转要瞬移", c._snap, True)


def test_next_prev() -> None:
    c, seen = log_changes()
    c.next()
    c.next()
    check("连续下一页", (c.current, seen), (2, [(0, 1), (1, 2)]))
    c.prev()
    check("上一页", (c.current, seen[-1]), (1, (2, 1)))
    c.go(3)
    seen.clear()
    c.next()
    check("末页再下一页：不动不回调", (c.current, seen), (3, []))
    c.go(0)
    seen.clear()
    c.prev()
    check("首页再上一页：不动不回调", (c.current, seen), (0, []))


def test_next_loop() -> None:
    c = carousel(3, loop=True)
    c.go(2)
    c.next()
    check("loop：末页下一页回到首页", c.current, 0)
    check("loop：跨边界的那一下要瞬移", c._snap, True)
    c.next()
    check("loop：界内下一页不瞬移", (c.current, c._snap), (1, False))
    c.prev()
    c.prev()
    check("loop：首页上一页到末页", c.current, 2)


def test_no_animation() -> None:
    c = carousel(4)
    c.next(animate=False)
    check("animate=False 也切页", c.current, 1)
    check("animate=False 走瞬移", c._snap, True)


def test_invalidate() -> None:
    c = carousel(5, index=4)
    c.slides = pages(2)
    c.invalidate()
    check("删页后索引夹回", c.current, 1)
    c.slides = []
    c.invalidate()
    check("清空后索引归零", c.current, 0)


def test_entering() -> None:
    check("bool True", _entering(True), True)
    check("bool False", _entering(False), False)
    check("字符串 true", _entering("true"), True)
    check("字符串 false", _entering("false"), False)
    check("大写 TRUE", _entering("TRUE"), True)
    check("带空格", _entering(" true "), True)
    check("数字 1", _entering("1"), True)
    check("空串当离开", _entering(""), False)
    check("None 当离开", _entering(None), False)


def test_hover_matters() -> None:
    check("hover 箭头要跟悬停", carousel(arrow="hover")._hover_matters(), True)
    check(
        "常显 + 不自动播就不跟",
        carousel(arrow="always")._hover_matters(),
        False,
    )
    check(
        "自动播 + 悬停暂停要跟",
        carousel(arrow="never", autoplay=True)._hover_matters(),
        True,
    )
    check(
        "自动播但不暂停就不跟",
        carousel(arrow="never", autoplay=True, pause_on_hover=False)._hover_matters(),
        False,
    )


def test_paused() -> None:
    c = carousel(autoplay=True)
    check("没悬停不暂停", c._paused, False)
    c._hovered = True
    check("悬停就暂停", c._paused, True)
    c.pause_on_hover = False
    check("关掉悬停暂停后不停", c._paused, False)
    c.autoplay = False
    check("没开自动播谈不上暂停", c._paused, False)


def main() -> int:
    for fn in (
        test_normalize_index,
        test_step_index,
        test_slide_offsets,
        test_ctor_validation,
        test_initial_state,
        test_go,
        test_go_loop_jump,
        test_next_prev,
        test_next_loop,
        test_no_animation,
        test_invalidate,
        test_entering,
        test_hover_matters,
        test_paused,
    ):
        print(f"\n=== {fn.__name__} ===")
        fn()
    print(f"\n{'=' * 46}\n{_passes} passed, {_fails} failed")
    return 1 if _fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
