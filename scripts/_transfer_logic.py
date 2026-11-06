"""Transfer 纯逻辑断言（不启窗口）。

覆盖：条目划分与保序、搜索匹配、三态判定、搬运的四种边界（禁用 / 不存在 /
重复搬 / 单向）、组件状态机（勾选、全选、搜索态下的全选半径、搬完清空勾选、
回调参数与顺序）、空数据与非法入参。

渲染期的东西（控件结构、颜色、真机点击）交给 smoke_test 与真机探针。

用法::

    python scripts/_transfer_logic.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ui.core.i18n import set_locale
from ui.input.transfer import (
    DIRECTIONS,
    Transfer,
    TransferItem,
    check_state,
    match_items,
    move_targets,
    split_items,
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


def keys(items: list[TransferItem]) -> list[str]:
    return [item.key for item in items]


# ---------------------------------------------------------------------------
# 夹具
# ---------------------------------------------------------------------------
def make_items() -> list[TransferItem]:
    return [
        TransferItem("name", "姓名"),
        TransferItem("dept", "部门", description="一级 / 二级"),
        TransferItem("title", "职位"),
        TransferItem("email", "邮箱", description="企业邮箱"),
        TransferItem("salary", "薪资", disabled=True),
    ]


def make_transfer(**kwargs: object) -> Transfer:
    params = {"data_source": make_items(), "target_keys": ["name"]}
    params.update(kwargs)
    return Transfer(**params)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# 纯函数
# ---------------------------------------------------------------------------
def test_split() -> None:
    items = make_items()
    source, target = split_items(items, ["name", "title"])
    check("划分：待选保序", keys(source), ["dept", "email", "salary"])
    check("划分：已选保序", keys(target), ["name", "title"])
    check("划分：空已选", keys(split_items(items, [])[1]), [])
    check("划分：全选", keys(split_items(items, [i.key for i in items])[0]), [])
    check("划分：未知 key 忽略", keys(split_items(items, ["nope"])[1]), [])


def test_match() -> None:
    items = make_items()
    check("搜索：空查询原样返回", keys(match_items(items, "")), keys(items))
    check("搜索：空白查询原样返回", keys(match_items(items, "   ")), keys(items))
    check("搜索：命中标题", keys(match_items(items, "邮")), ["email"])
    check("搜索：命中说明", keys(match_items(items, "企业")), ["email"])
    eng = [TransferItem("k1", "Department"), TransferItem("k2", "Role")]
    check("搜索：大小写不敏感", keys(match_items(eng, "DEPART")), ["k1"])
    check("搜索：大小写不敏感（反查）", keys(match_items(eng, "role")), ["k2"])
    check("搜索：无命中", keys(match_items(items, "zzz")), [])
    check("搜索：首尾空格忽略", keys(match_items(items, "  部门 ")), ["dept"])


def test_state() -> None:
    items = make_items()
    check("三态：都没勾", check_state(items, []), "none")
    check("三态：勾了一部分", check_state(items, ["name"]), "some")
    check("三态：全勾", check_state(items, [i.key for i in items]), "all")
    check("三态：空列表恒为 none", check_state([], ["name"]), "none")
    check("三态：集合外的 key 不影响", check_state(items[:2], ["name", "zzz"]), "some")
    check("三态：恰好全中", check_state(items[:2], ["name", "dept"]), "all")


def test_move_targets_func() -> None:
    items = make_items()
    check("搬运：移入", move_targets(items, [], ["name", "dept"], "right"), ["name", "dept"])
    check("搬运：移入按数据源排序", move_targets(items, [], ["dept", "name"], "right"), ["name", "dept"])
    check("搬运：移出", move_targets(items, ["name", "dept"], ["name"], "left"), ["dept"])
    check("搬运：禁用项移不进", move_targets(items, [], ["salary"], "right"), [])
    check("搬运：禁用项移不出", move_targets(items, ["salary"], ["salary"], "left"), ["salary"])
    check("搬运：未知 key 忽略", move_targets(items, [], ["ghost"], "right"), [])
    check("搬运：重复移入幂等", move_targets(items, ["name"], ["name"], "right"), ["name"])
    check("搬运：移出不存在的不动", move_targets(items, ["name"], ["dept"], "left"), ["name"])
    check(
        "搬运：一批里混着可搬与不可搬",
        move_targets(items, [], ["name", "salary", "ghost"], "right"),
        ["name"],
    )
    try:
        move_targets(items, [], ["name"], "up")
    except ValueError as exc:
        check("搬运：非法方向抛 ValueError", "up" in str(exc), True)
    else:
        check("搬运：非法方向抛 ValueError", "没抛", "抛了")


# ---------------------------------------------------------------------------
# 组件状态机
# ---------------------------------------------------------------------------
def test_basic_state() -> None:
    tr = make_transfer()
    check("初始：待选", keys(tr.source_items), ["dept", "title", "email", "salary"])
    check("初始：已选", keys(tr.selected_items), ["name"])
    check("初始：两侧都没勾", (tr.picked("left"), tr.picked("right")), ([], []))
    check("初始：箭头都不亮", (tr.is_move_ready("left"), tr.is_move_ready("right")), (False, False))


def test_toggle_and_move() -> None:
    tr = make_transfer()
    tr.toggle("left", "dept")
    tr.toggle("left", "title")
    check("勾选：顺序按数据源", tr.picked("left"), ["dept", "title"])
    check("勾选：右侧箭头亮起", tr.is_move_ready("right"), True)
    check("勾选：左侧箭头仍灭", tr.is_move_ready("left"), False)

    tr.toggle("left", "dept")
    check("勾选：再点取消", tr.picked("left"), ["title"])

    seen: list[tuple[list[str], str, list[str]]] = []
    tr.on_change = lambda ts, d, m: seen.append((ts, d, m))
    tr.move("right")
    check("搬运：已选更新", tr.target_keys, ["name", "title"])
    check("搬运：待选更新", keys(tr.source_items), ["dept", "email", "salary"])
    check("搬运：回调参数", seen, [(["name", "title"], "right", ["title"])])
    check("搬运：搬完清掉该侧勾选", tr.picked("left"), [])
    check("搬运：箭头复位", tr.is_move_ready("right"), False)

    tr.toggle("right", "title")
    tr.move("left")
    check("搬回：已选更新", tr.target_keys, ["name"])
    check("搬回：搬完清掉右侧勾选", tr.picked("right"), [])


def test_move_noop() -> None:
    tr = make_transfer()
    seen: list[object] = []
    tr.on_change = lambda *a: seen.append(a)
    check("空搬：没勾就返回原值", tr.move("right"), ["name"])
    check("空搬：不触发回调", seen, [])

    tr.disabled = True
    tr.toggle("left", "dept")
    check("禁用：勾不上", tr.picked("left"), [])
    check("禁用：搬不动", tr.move("right"), ["name"])
    tr.disabled = False


def test_disabled_item() -> None:
    tr = make_transfer()
    tr.toggle("left", "salary")  # 行被禁用时 UI 挡掉了，这里直接走状态层
    check("禁用条目：仍能被勾上（状态层不改写）", tr.picked("left"), ["salary"])
    check("禁用条目：箭头不亮", tr.is_move_ready("right"), False)
    check("禁用条目：搬不动", tr.move("right"), ["name"])


def test_select_all() -> None:
    tr = make_transfer()
    tr.toggle_all("left")
    check("全选：跳过禁用项", tr.picked("left"), ["dept", "title", "email"])
    check("全选：三态变 all", check_state(tr._pickable("left"), tr.picked("left")), "all")
    tr.toggle_all("left")
    check("全不选：清空", tr.picked("left"), [])
    tr.toggle_all("left", True)
    tr.toggle_all("left", False)
    check("全不选：显式 False", tr.picked("left"), [])


def test_search_scope() -> None:
    tr = make_transfer()
    tr.toggle("left", "dept")
    tr.set_query("left", "邮")
    check("搜索：可见项收窄", keys(tr.items("left")), ["email"])
    check("搜索：勾选是全局的（被过滤的仍在）", tr.picked("left"), ["dept"])
    tr.toggle_all("left")  # 只选可见的 email
    check("搜索态全选：只作用于可见项", tr.picked("left"), ["dept", "email"])
    tr.toggle_all("left")  # 只取消可见的 email
    check("搜索态全不选：只作用于可见项", tr.picked("left"), ["dept"])

    tr.move("right")  # 被过滤掉的 dept 照样搬走
    check("搜索态搬运：搬走全部已勾选（含隐藏）", tr.target_keys, ["name", "dept"])
    tr.set_query("left", "")
    check("清空搜索：恢复全部", keys(tr.items("left")), ["title", "email", "salary"])


def test_one_way() -> None:
    tr = make_transfer(one_way=True, target_keys=["name", "dept"])
    tr.toggle("right", "dept")
    check("单向：右侧箭头仍可亮（反向不渲染）", tr.is_move_ready("left"), True)
    check("单向：搬不动", tr.move("left"), ["name", "dept"])
    check("单向：move_keys 也挡住", tr.move_keys(["dept"], "left"), ["name", "dept"])


def test_move_keys() -> None:
    tr = make_transfer()
    check("指定搬：不必先勾", tr.move_keys(["email"], "right"), ["name", "email"])
    check("指定搬：跳过禁用", tr.move_keys(["salary"], "right"), ["name", "email"])
    check("指定搬：结果按数据源排序", tr.move_keys(["title", "dept"], "right"), ["name", "dept", "title", "email"])


def test_select_change_callback() -> None:
    tr = make_transfer()
    seen: list[tuple[list[str], list[str]]] = []
    tr.on_select_change = lambda left, right: seen.append((left, right))
    tr.toggle("left", "dept")
    tr.toggle("right", "name")
    check("勾选回调：逐次触发", len(seen), 2)
    check("勾选回调：参数是最新两侧", seen[-1], (["dept"], ["name"]))
    tr.clear_selection()
    check("清空勾选：两侧都清", (tr.picked("left"), tr.picked("right")), ([], []))
    check("清空勾选：也回调", seen[-1], ([], []))


def test_invalidate() -> None:
    tr = make_transfer()
    tr.toggle("left", "dept")
    tr.data_source = [TransferItem("name", "姓名"), TransferItem("dept", "部门")]
    tr.target_keys = [*tr.target_keys, "ghost"]
    tr.invalidate()
    check("失效：剔除已不存在的已选", tr.target_keys, ["name"])
    check("失效：剔除已不存在的勾选", tr.picked("left"), ["dept"])
    check("失效：两侧重算", (keys(tr.source_items), keys(tr.selected_items)), (["dept"], ["name"]))


def test_titles_and_edges() -> None:
    set_locale("zh-CN")
    check("标题：默认取语言包", make_transfer()._head_titles(), ("待选", "已选"))
    check("标题：可覆盖", make_transfer(titles=("候选", "已授权"))._head_titles(), ("候选", "已授权"))

    empty = Transfer()
    check("空数据：两侧都空", (empty.source_items, empty.selected_items), ([], []))
    check("空数据：箭头不亮", (empty.is_move_ready("left"), empty.is_move_ready("right")), (False, False))
    empty.toggle_all("left")  # 不该崩
    check("空数据：全选无副作用", empty.picked("left"), [])

    check("方向常量", DIRECTIONS, ("left", "right"))


def test_hover() -> None:
    tr = make_transfer()
    repaints: list[int] = []
    real = tr.notify

    def counting(*args: object, **kwargs: object) -> None:
        repaints.append(1)
        real(*args, **kwargs)  # type: ignore[misc]

    tr.notify = counting  # type: ignore[method-assign]
    tr._hover_row("left:dept", True)
    tr._hover_row("left:dept", True)  # 同一行不重绘
    check("悬停：换行才重绘", len(repaints), 1)
    tr._hover_row("left:title", True)
    check("悬停：换到新行重绘", len(repaints), 2)
    tr._hover_row("left:dept", False)  # 旧行的 exit 忽略
    check("悬停：旧行 exit 不重绘", len(repaints), 2)
    tr._hover_row("left:title", False)
    check("悬停：当前行 exit 重绘", len(repaints), 3)
    check("悬停：状态归零", tr._hover, None)


def main() -> int:
    for fn in (
        test_split,
        test_match,
        test_state,
        test_move_targets_func,
        test_basic_state,
        test_toggle_and_move,
        test_move_noop,
        test_disabled_item,
        test_select_all,
        test_search_scope,
        test_one_way,
        test_move_keys,
        test_select_change_callback,
        test_invalidate,
        test_titles_and_edges,
        test_hover,
    ):
        print(f"\n## {fn.__name__}")
        fn()
    print(f"\nRESULT: {_passes} passed, {_fails} failed")
    return 1 if _fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
