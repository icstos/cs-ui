"""Menu 纯逻辑断言（不启窗口）。

覆盖：树的遍历与分组拍平、祖先链查找、选中归一（不存在 / 父节点 / 禁用）、
展开集合的清理与手风琴、可见行计算（折叠 / 逐层展开）、行高档位。

颜色、悬停与点击后的重绘属于渲染期，交给 smoke_test 与真机探针。

用法::

    python scripts/_menu_logic.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ui.navigation.menu import (
    Menu,
    MenuGroup,
    MenuItem,
    find_path,
    norm_selected,
    prune_expanded,
    row_height,
    toggle_expanded,
    visible_rows,
    walk,
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


# ---------------------------------------------------------------------------
# 样例树
#
#   home                      叶子
#   ── 运维（分组）──
#   host      ─> hl / hg / ht
#   net       ─> vpc / eip ─> eip-a   （三层）
#   archive   ─> cold
#   audit                     禁用叶子
# ---------------------------------------------------------------------------
def tree() -> list:
    return [
        MenuItem("home", "概览"),
        MenuGroup(
            "运维",
            [
                MenuItem(
                    "host",
                    "主机",
                    children=[
                        MenuItem("hl", "主机列表"),
                        MenuItem("hg", "主机分组"),
                        MenuItem("ht", "标签管理"),
                    ],
                ),
                MenuItem(
                    "net",
                    "网络",
                    children=[
                        MenuItem("vpc", "私有网络"),
                        MenuItem(
                            "eip", "弹性 IP", children=[MenuItem("eip-a", "IP 段")]
                        ),
                    ],
                ),
            ],
        ),
        MenuItem("archive", "归档", children=[MenuItem("cold", "冷归档")]),
        MenuItem("audit", "审计日志", disabled=True),
    ]


class _Event:
    """最小事件桩：组件只读 ``e.control.data``。"""

    def __init__(self, key: str) -> None:
        self.control = type("C", (), {"data": key})()


def keys(items) -> list[str]:
    return [item.key for item in items]


# ===========================================================================
print("=== walk / 分组拍平 ===")
check("先序 12 项", len(list(walk(tree()))), 12)
check(
    "顺序：分组被拍平",
    keys(walk(tree())),
    ["home", "host", "hl", "hg", "ht", "net", "vpc", "eip", "eip-a",
     "archive", "cold", "audit"],
)
check("空树不炸", list(walk([])), [])

print()
print("=== find_path ===")
check("叶子：两层链", find_path(tree(), "hg"), ("host", "hg"))
check("三层叶子", find_path(tree(), "eip-a"), ("net", "eip", "eip-a"))
check("顶层项只含自身", find_path(tree(), "home"), ("home",))
check("父节点也在链上", find_path(tree(), "host"), ("host",))
check("找不到 → ()", find_path(tree(), "nope"), ())
check("空键 → ()", find_path(tree(), ""), ())

print()
print("=== norm_selected ===")
check("叶子通过", norm_selected(tree(), "hl"), "hl")
check("父节点被拦（只管展开）", norm_selected(tree(), "host"), "")
check("禁用项被拦", norm_selected(tree(), "audit"), "")
check("不存在的键被拦", norm_selected(tree(), "nope"), "")
check("空键", norm_selected(tree(), ""), "")

print()
print("=== prune_expanded ===")
check("去掉不存在的键", prune_expanded(tree(), ["host", "nope"]), ("host",))
check("去掉叶子键（没子项）", prune_expanded(tree(), ["hl"]), ())
check("去重保序", prune_expanded(tree(), ["net", "host", "net"]), ("net", "host"))
check("全空", prune_expanded(tree(), []), ())

print()
print("=== toggle_expanded ===")
check("关掉已开", toggle_expanded(tree(), ("host",), "host"), ())
check("打开关着的", toggle_expanded(tree(), (), "host"), ("host",))
check("追加不覆盖", toggle_expanded(tree(), ("host",), "net"), ("host", "net"))
check("不存在的键：变了（实现不校验，归一交给 prune）",
      toggle_expanded(tree(), (), "nope"), ("nope",))
check(
    "手风琴：关掉同层兄弟",
    toggle_expanded(tree(), ("host",), "net", accordion=True),
    ("net",),
)
check(
    "手风琴：同层的 archive / host 一起关掉",
    toggle_expanded(tree(), ("archive", "host"), "net", accordion=True),
    ("net",),
)
check(
    "手风琴：子级只看自己的兄弟",
    toggle_expanded(tree(), ("net",), "eip", accordion=True),
    ("net", "eip"),
)

print()
print("=== visible_rows ===")
rows = visible_rows(tree(), (), collapsed=False)
check("全收起：只有顶层（分组拍平后 4 项）", keys(r for (r, _d) in rows), ["home", "host", "net", "archive", "audit"])
check("顶层深度都是 0", {d for (_r, d) in rows}, {0})

rows = visible_rows(tree(), ("host",), collapsed=False)
check(
    "展开 host：子项紧跟其后",
    [(r.key, d) for (r, d) in rows][:5],
    [("home", 0), ("host", 0), ("hl", 1), ("hg", 1), ("ht", 1)],
)

rows = visible_rows(tree(), ("net", "eip"), collapsed=False)
check(
    "三层：eip-a 深度 2",
    [(r.key, d) for (r, d) in rows if r.key in ("net", "vpc", "eip", "eip-a")],
    [("net", 0), ("vpc", 1), ("eip", 1), ("eip-a", 2)],
)

rows = visible_rows(tree(), ("net",), collapsed=False)
check("只开 net：eip 的子项不出现", "eip-a" in keys(r for (r, _d) in rows), False)

rows = visible_rows(tree(), ("net", "eip"), collapsed=True)
check("折叠：一切子项都不画", keys(r for (r, _d) in rows), ["home", "host", "net", "archive", "audit"])

check("空树：0 行", visible_rows([], ("x",)), ())

print()
print("=== row_height ===")
check("large", row_height("large"), 48)
check("default", row_height("default"), 40)
check("small", row_height("small"), 32)
check("非法档位退回 default", row_height("huge"), 40)

print()
print("=== Menu 组件：对外动作 ===")
m = Menu(items=tree(), selected_key="hl", expanded_keys=("host",))
check("初始选中", m.selected_key, "hl")
check("初始展开", m.expanded_keys, ("host",))

m.select("hg")
check("select 换选中", m.selected_key, "hg")
m.select("host")
check("select 指向父节点 → 清空（明确表示没有合法选中项）", m.selected_key, "")
m.select("hg")
m.select("audit")
check("select 指向禁用 → 清空", m.selected_key, "")

m.expand("net")
check("expand 追加", m.expanded_keys, ("host", "net"))
m.expand("nope")
check("expand 不存在的键不落地", m.expanded_keys, ("host", "net"))

m.toggle("host")
check("toggle 收起", m.expanded_keys, ("net",))

seen: list = []
m2 = Menu(items=tree(), on_expand=seen.append, on_select=seen.append)
m2.toggle("host")
check("toggle 触发 on_expand", seen, [("host",)])

seen.clear()
m2.selected_key = "hl"
m2._click(_Event("home"))
check("点叶子触发 on_select", [item.key for item in seen], ["home"])
check("点叶子改选中", m2.selected_key, "home")

seen.clear()
m5 = Menu(items=tree(), selected_key="home", on_expand=seen.append)
m5._click(_Event("host"))
check("点父项只展开、不选中", (m5.selected_key, seen), ("home", [("host",)]))
check("点父项后箭头朝上", "host" in m5.expanded_keys, True)

seen.clear()
m5._click(_Event("host"))
check("再点一次收起", m5.expanded_keys, ())

seen.clear()
m5._click(_Event("audit"))
check("点禁用项毫无反应", (m5.selected_key, seen), ("home", []))

print()
print("=== 折叠态点父项：自动摊开 ===")
m3 = Menu(items=tree(), collapsed=True, selected_key="hl", expanded_keys=("host",))
check("初始折叠", m3.collapsed, True)
m3._click(_Event("net"))
check("摊开菜单", m3.collapsed, False)
check("顺手展开该组", "net" in m3.expanded_keys, True)

print()
print("=== 选中项的祖先自动露出来（但不写回 expanded）===")
m4 = Menu(items=tree(), selected_key="cold", expanded_keys=())
check("effective 含 archive", m4._effective_expanded(), ("archive",))
check("字段本身没被改", m4.expanded_keys, ())

print()
print("=== 子项有选中时，父项也能收起（回归）===")
# 曾经的 bug：effective 无条件并入选中项的祖先链，于是"装着当前页的那一组"
# 永远收不起来 —— 点父项没有任何反应。
m6 = Menu(items=tree(), selected_key="hl", expanded_keys=())
check("自动露出的祖先", m6._effective_expanded(), ("host",))
m6.toggle("host")
check("收起成功", m6._effective_expanded(), ())
check("选中项不受影响（收起不等于取消选中）", m6.selected_key, "hl")
check(
    "子项确实不画了",
    "hl" in keys(r for (r, _d) in visible_rows(tree(), m6._effective_expanded())),
    False,
)
m6.toggle("host")
check("再点一次又开", m6._effective_expanded(), ("host",))
m6.toggle("host")
check("可以反复收/开", m6._effective_expanded(), ())

m7 = Menu(items=tree(), selected_key="hl")
m7.toggle("host")
m7.select("hg")
check("换选中项 → 那条链路重新自动展开", m7._effective_expanded(), ("host",))

m8 = Menu(items=tree(), selected_key="eip-a")
check("三层：祖先自动露两级", m8._effective_expanded(), ("net", "eip"))
m8.toggle("net")
check("收起最外层：下一级不再算展开", m8._effective_expanded(), ("eip",))
check("可见行回到 5 个顶层项", len(visible_rows(tree(), m8._effective_expanded())), 5)

m9 = Menu(items=tree(), selected_key="hl")
m9.toggle("host")
m9.expand("host")
check("expand 会销掉收起记录", m9._effective_expanded(), ("host",))

print()
print("=== toggle 的无效输入 ===")
m10 = Menu(items=tree(), selected_key="hl")
m10.toggle("hl")
check("叶子不参与展开", m10.expanded_keys, ())
m10.toggle("audit")
check("禁用项不响应", m10.expanded_keys, ())
m10.toggle("nope")
check("不存在的键不落地", m10.expanded_keys, ())
check("以上都不影响 effective", m10._effective_expanded(), ("host",))

seen.clear()
m11 = Menu(items=tree(), selected_key="hl", on_expand=seen.append)
m11.toggle("host")
check("收起自动展开的祖辈也回调 on_expand", seen, [()])


print()
print("==============================================")
print(f"{_passes} passed, {_fails} failed")
raise SystemExit(1 if _fails else 0)
