"""Pagination 纯逻辑断言（不启窗口）。

覆盖：页码折叠的四种形态、总页数派生（含除零与负数兜底）、页码宽度、
跳页/点页的边界与回调语义、切每页条数回首页。

颜色与布局属于渲染期，交给 smoke_test 与真机探针。

用法::

    python scripts/_pagination_logic.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ui.navigation.pagination import (
    BTN,
    PaginationState,
    _page_width,
    get_center_pages,
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


def ev(data: object = None, value: object = None) -> SimpleNamespace:
    """最小事件桩：组件只读 ``e.control.data`` / ``e.control.value``。"""
    return SimpleNamespace(control=SimpleNamespace(data=data, value=value))


# ---------------------------------------------------------------------------
# 页码折叠
# ---------------------------------------------------------------------------
def test_center_pages() -> None:
    check("0 页：空", get_center_pages(1, 0), [])
    check("1 页：单个数", get_center_pages(1, 1), [1])
    check("6 页：全显示", get_center_pages(3, 6), [1, 2, 3, 4, 5, 6])
    check("7 页：开始折叠", get_center_pages(1, 7), [1, 2, 3, 4, 5, -1, 7])
    check("靠前（第 4 页）仍在左簇", get_center_pages(4, 20), [1, 2, 3, 4, 5, -1, 20])
    check(
        "中间（第 10 页）双省略",
        get_center_pages(10, 20),
        [1, -1, 8, 9, 10, 11, 12, -1, 20],
    )
    check("靠后（第 17 页）右簇", get_center_pages(17, 20), [1, -1, 16, 17, 18, 19, 20])
    check("末页", get_center_pages(20, 20), [1, -1, 16, 17, 18, 19, 20])
    check("中间：当前页恒在正中", get_center_pages(10, 20)[4], 10)
    check("任何输入都只出现一次 -1 边界值", get_center_pages(5, 100).count(-1), 2)


def test_center_pages_never_breaks_monotonic() -> None:
    """去掉省略号后页码必须严格递增 —— 折叠算法最容易出的错是重叠或倒序。"""
    bad: list[tuple[int, int]] = []
    for total in range(1, 60):
        for cur in range(1, total + 1):
            pages = [p for p in get_center_pages(cur, total) if p != -1]
            if pages != sorted(set(pages)):
                bad.append((cur, total))
            if cur not in pages:
                bad.append((cur, total))
    check("1..59 页 × 每个当前页：递增且含当前页", bad, [])


# ---------------------------------------------------------------------------
# 总页数派生
# ---------------------------------------------------------------------------
def test_sum_page_nums() -> None:
    check("整除：100/10", PaginationState(sum_data_nums=100).sum_page_nums, 10)
    check("余数：101/10 进位", PaginationState(sum_data_nums=101).sum_page_nums, 11)
    check("1 条也占一页", PaginationState(sum_data_nums=1).sum_page_nums, 1)
    check("0 条：0 页", PaginationState(sum_data_nums=0).sum_page_nums, 0)
    check(
        "每页 0 条不除零",
        PaginationState(sum_data_nums=10, data_per_page_nums=0).sum_page_nums,
        10,
    )
    check(
        "每页负数不除零",
        PaginationState(sum_data_nums=10, data_per_page_nums=-3).sum_page_nums,
        10,
    )
    check("负数条数视作 0", PaginationState(sum_data_nums=-5).sum_page_nums, 0)
    check(
        "非 10 的每页条数（Table 用 8）",
        PaginationState(sum_data_nums=25, data_per_page_nums=8).sum_page_nums,
        4,
    )


# ---------------------------------------------------------------------------
# 页码宽度
# ---------------------------------------------------------------------------
def test_page_width() -> None:
    check("1 位数取正方形", _page_width("1"), BTN)
    check("2 位数取正方形", _page_width("10"), BTN)
    check("3 位数开始变宽", _page_width("100") > BTN, True)
    check("4 位数比 3 位数更宽", _page_width("1000") > _page_width("100"), True)
    check("宽度随位数线性", _page_width("1000") - _page_width("100"), 8)


# ---------------------------------------------------------------------------
# 交互语义
# ---------------------------------------------------------------------------
def test_click() -> None:
    seen: list[int] = []
    s = PaginationState(sum_data_nums=95, data_per_page_nums=20, on_change_page=seen.append)
    check("5 页（95/20）", s.sum_page_nums, 5)

    s.click_update_page(ev(data=3))
    check("点第 3 页：页码更新", s.current_page, 3)
    check("点第 3 页：回调一次", seen, [3])

    s.click_update_page(ev(data=3))
    check("重复点同一页：仍回调（外部可能靠它刷新）", seen, [3, 3])

    s.click_update_page(ev(data=0))
    check("点第 0 页：忽略", (s.current_page, len(seen)), (3, 2))

    s.click_update_page(ev(data=99))
    check("超出总页数：忽略", (s.current_page, len(seen)), (3, 2))

    s.click_update_page(ev(data=5))
    check("点末页：允许", s.current_page, 5)


def test_goto() -> None:
    seen: list[int] = []
    s = PaginationState(sum_data_nums=95, data_per_page_nums=20, on_change_page=seen.append)
    s.handle_goto_page_submit(ev(value="4"))
    check("跳页：有效值生效", (s.current_page, seen), (4, [4]))

    s.handle_goto_page_submit(ev(value=" 2 "))
    check("跳页：忽略首尾空格", (s.current_page, seen), (2, [4, 2]))

    s.handle_goto_page_submit(ev(value="abc"))
    check("跳页：非数字忽略", (s.current_page, len(seen)), (2, 2))

    s.handle_goto_page_submit(ev(value=""))
    check("跳页：空串忽略", (s.current_page, len(seen)), (2, 2))

    s.handle_goto_page_submit(ev(value=None))
    check("跳页：None 忽略", (s.current_page, len(seen)), (2, 2))

    s.handle_goto_page_submit(ev(value="99"))
    check("跳页：越界忽略", (s.current_page, len(seen)), (2, 2))


def test_per_page() -> None:
    pages: list[int] = []
    sizes: list[int] = []
    s = PaginationState(
        sum_data_nums=500,
        current_page=7,
        on_change_page=pages.append,
        on_change_per_page_nums=sizes.append,
    )
    s.handle_change_per_page_nums(ev(value="20"))
    check("切条数：生效", s.data_per_page_nums, 20)
    check("切条数：回第一页", s.current_page, 1)
    check("切条数：先报页码再报条数", (pages, sizes), ([1], [20]))
    check("切条数后总页数重算", s.sum_page_nums, 25)

    s.handle_change_per_page_nums(ev(value="50"))
    check("切条数可多次", (s.data_per_page_nums, pages), (50, [1, 1]))


def test_no_callback() -> None:
    """回调全为 None 时不能抛 —— 只读展示用的分页器很常见。"""
    s = PaginationState(sum_data_nums=30)
    s.click_update_page(ev(data=2))
    s.handle_goto_page_submit(ev(value="3"))
    s.handle_change_per_page_nums(ev(value="15"))
    check("无回调：状态照常推进", (s.current_page, s.data_per_page_nums), (1, 15))


# ---------------------------------------------------------------------------
def main() -> int:
    for fn in (
        test_center_pages,
        test_center_pages_never_breaks_monotonic,
        test_sum_page_nums,
        test_page_width,
        test_click,
        test_goto,
        test_per_page,
        test_no_callback,
    ):
        print(f"\n=== {fn.__name__} ===")
        fn()
    print(f"\n{'=' * 46}\n{_passes} passed, {_fails} failed")
    return 1 if _fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
