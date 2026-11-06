"""Message / Notification 的栈逻辑断言（不启窗口）。

渲染期的东西（位置、动画、鼠标穿透）交给真机探针；这里只钉住那些**看不见
却容易写错**的行为：

- 位置槽位算出来的锚点与顺序；
- 进出场期间 ``opacity`` / ``offset`` 的取值；
- 计时器的 token 作废与悬停暂停；
- 合并同款的计数与回调；
- ``close_all`` 不新建浮层。

``_later`` 被换成一个可手动触发的记录器——否则每条断言都要真的等几百毫秒。

用法::

    python scripts/_feedback_logic.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import flet as ft

from ui.core.constants import StyleType
from ui.feedback import Message, Notification
from ui.feedback._overlay import (
    SLOTS,
    OverlayHost,
    host_for,
    peek_host,
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


def check_true(name: str, got: object) -> None:
    check(name, bool(got), True)


class FakePage:
    """够栈用的最小 Page。"""

    def __init__(self) -> None:
        self.overlay: list[ft.Control] = []
        self.views: list[object] = []  # overlay_usable() 读它，空列表即"根视图"
        self.updates = 0

    def update(self) -> None:
        self.updates += 1

    def run_task(self, *_a, **_kw):  # 真栈用它排队；测试里直接丢弃
        return None


class TestHost(OverlayHost):
    """把计时器换成本地可手动触发的队列。"""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.timers: list[tuple[int, object]] = []

    def _later(self, ms: int, fn) -> None:
        self.timers.append((ms, fn))

    def fire_all(self) -> None:
        pending, self.timers = self.timers, []
        for _ms, fn in pending:
            fn()


def make_host(position: str = "top-center", gap: int = 10) -> tuple[FakePage, TestHost]:
    page = FakePage()
    return page, TestHost(page, position, gap=gap)


# ---------------------------------------------------------------------------
# 位置槽位
# ---------------------------------------------------------------------------
check(
    "top-center 锚点：左右撑满（靠 TransparentPointer 不吞点击）",
    SLOTS["top-center"].anchor(20),
    {"top": 20, "left": 0, "right": 0},
)
check("top-right 锚点", SLOTS["top-right"].anchor(24), {"top": 24, "right": 24})
check("bottom-left 锚点", SLOTS["bottom-left"].anchor(24), {"bottom": 24, "left": 24})
check_true("贴底位置倒序", SLOTS["bottom-right"].reversed_order)
check("贴顶位置不倒序", SLOTS["top-right"].reversed_order, False)
check("居中位置居中排列", SLOTS["top-center"].cross(), ft.CrossAxisAlignment.CENTER)
check("右侧位置靠右排列", SLOTS["top-right"].cross(), ft.CrossAxisAlignment.END)

# ---------------------------------------------------------------------------
# 入场：先透明偏移，下一帧再补间到终值
# ---------------------------------------------------------------------------
page, host = make_host()
card = host.push(ft.Container(), duration=1000)
check("push 后卡片在列里", len(host.column.controls), 1)
check("首帧透明", card.wrapper.opacity, 0)
check("首帧带偏移", (card.wrapper.offset.x, card.wrapper.offset.y), (0, -0.35))
check("浮层只挂了一个节点", len(page.overlay), 1)
check("首次排队的是入场帧", host.timers[0][0], 16)

host.fire_all()  # 入场帧
check("入场后不透明", card.wrapper.opacity, 1)
check("入场后归位", (card.wrapper.offset.x, card.wrapper.offset.y), (0, 0))
check("入场后开始倒计时", host.timers[-1][0], 1000)

# ---------------------------------------------------------------------------
# 计时：token 作废 + 悬停暂停
# ---------------------------------------------------------------------------
stale = host.timers[-1][1]
card.hovered = True
card.token += 1  # 模拟"鼠标停上去"
stale()
check("作废的计时回调不关卡片", card.closed, False)

card.hovered = False
host._arm(card)
check("移开后重新排队", host.timers[-1][0], card.remaining)
host.fire_all()
check("到期自动关闭", card.closed, True)
check("退场先播动画", card.wrapper.opacity, 0)
check("退场后仍在列表里（等动画）", len(host.cards), 1)
host.fire_all()
check("动画结束才真正移除", len(host.cards), 0)
check("移除后列也空了", len(host.column.controls), 0)

# ---------------------------------------------------------------------------
# 常驻（duration=0）不倒计时
# ---------------------------------------------------------------------------
page, host = make_host()
host.push(ft.Container(), duration=0)
host.fire_all()
check("duration=0 不排关闭计时", len(host.timers), 0)

# ---------------------------------------------------------------------------
# 合并同款
# ---------------------------------------------------------------------------
page, host = make_host()
first_seen: list[int] = []
second_seen: list[int] = []
host.push(ft.Container(), duration=500, merge_key="saved", on_merge=first_seen.append)
second = host.push(ft.Container(), duration=500, merge_key="saved", on_merge=second_seen.append)
check("合并后只有一条", len(host.cards), 1)
check("计数递增", second.count, 2)
check("回调落在第一条卡片上（徽标长在它身上）", first_seen, [2])
check("新实例的回调不被调用", second_seen, [])
check("合并会重置计时", host.timers[-1][0], 500)

# 不同 key 不合并
host.push(ft.Container(), duration=500, merge_key="other")
check("不同 key 各自一条", len(host.cards), 2)

# ---------------------------------------------------------------------------
# 顺序：贴顶新的在上，贴底新的在下
# ---------------------------------------------------------------------------
page, host = make_host("top-right", gap=12)
first = host.push(ft.Container(key="a"), duration=0)
newer = host.push(ft.Container(key="b"), duration=0)
check("贴顶：新的排第一", host.column.controls[0] is newer.wrapper, True)
check("贴顶：旧的排第二", host.column.controls[-1] is first.wrapper, True)

page, host = make_host("bottom-right", gap=12)
old = host.push(ft.Container(key="a"), duration=0)
recent = host.push(ft.Container(key="b"), duration=0)
check("贴底：新的排最后", host.column.controls[-1] is recent.wrapper, True)
check("贴底：旧的排最前", host.column.controls[0] is old.wrapper, True)

# ---------------------------------------------------------------------------
# 栈复用：同页同位置只建一个浮层
# ---------------------------------------------------------------------------
page, host = make_host()
host.push(ft.Container(), duration=0)
host.push(ft.Container(), duration=0)
check("两次 push 仍只有一个浮层节点", len(page.overlay), 1)

fresh = FakePage()
first_host = host_for(fresh, "top-center")
check("host_for 第二次返回同一个栈", host_for(fresh, "top-center") is first_host, True)
check_true("peek_host 能看到已存在的栈", peek_host(fresh, "top-center") is first_host)
check("peek_host 对未创建的位置返回 None", peek_host(fresh, "bottom-left"), None)

# ---------------------------------------------------------------------------
# Message：入参折形
# ---------------------------------------------------------------------------
page = FakePage()
msg = Message.success("已保存", page=page)
check("show 返回 Message", isinstance(msg, Message), True)
check("类型落位", msg.style_type, StyleType.SUCCESS)
check_true("已经挂到栈上", msg._card is not None)
check("默认定宽", msg.width, 360)
check("显式宽度优先", Message("短", width=260).width, 260)
check("居中位置用 TransparentPointer（不吃点击）", type(make_host()[1].box).__name__, "TransparentPointer")
check("角落位置用普通容器（保证 on_click 只触发一次）", type(make_host("top-right")[1].box).__name__, "Container")

check("文本内容参与合并键", Message("已保存", grouping=True)._merge_key(), ("已保存", StyleType.INFO))
check("控件内容不参与合并", Message(ft.Text("x"), grouping=True)._merge_key(), None)
check("不开启合并时为 None", Message("已保存")._merge_key(), None)

Message("短消息", duration=0).show(page)
Message.close_all(page)
check("close_all 后栈清空", len(peek_host(page, "top-center").cards), 0)

# ---------------------------------------------------------------------------
# Notification：位置校验与形态
# ---------------------------------------------------------------------------
page = FakePage()
note = Notification.success("同步完成", "3 个组件已更新", page=page)
check("默认右上角", note.position, "top-right")
check("标题落位", note.title, "同步完成")
check("浮层挂在右上角", len(page.overlay), 1)

try:
    Notification("x", position="middle")
except ValueError:
    check("非法位置报错", "ValueError", "ValueError")
else:
    check("非法位置报错", "没有抛异常", "ValueError")

Notification("x", position="bottom-left", duration=0).show(page)
check("两个角落各一个浮层", len(page.overlay), 2)
Notification.close_all(page)
check(
    "close_all 清空所有角落",
    sum(len(h.cards) for h in [peek_host(page, p) for p in SLOTS] if h is not None),
    0,
)


print()
if _fails:
    print(f"RESULT: {_passes} passed, {_fails} FAILED")
    sys.exit(1)
print(f"RESULT: all {_passes} checks passed")
