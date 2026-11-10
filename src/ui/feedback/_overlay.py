"""浮动卡片栈：``Message`` / ``Notification`` 共用的浮层底座。

为什么不继续用 ``SnackBar``
--------------------------
``SnackBar`` 走 ``page.show_dialog``，也就是**弹层栈**：后一条会把前一条顶下去；
位置钉在窗口底部；没有标题，也没法按类型配色。而这两类提示真正需要的恰好是
相反的——「多条同时可见、按位置叠放、类型各有颜色」。所以它们自己挂
``page.overlay``，本模块就是那层底座。

栈的形态
--------
**同一个页面、同一个位置只有一个浮层节点**：一个定位用的 ``Container`` 套一个
``Column``。新卡片进来只改 ``Column.controls``，不新增浮层节点——浮层一多，
命中测试与重绘都会变贵。

四条实现约定
------------
1. **进出场只动 ``opacity`` / ``offset``**。两者都在 Flutter 端插值，不需要
   逐帧回调；首帧用「透明 + 偏移」挂上去，隔一帧改成终值，Flutter 自己补间。
2. **计时器带 token**。``page.run_task`` 返回的是 ``Future``，拿不到取消句柄，
   只能让旧回调自己作废：每次重排都 ``token += 1``，回调发现 token 不是最新
   就静默退出。
3. **悬停暂停**。鼠标停上去就冻结剩余时间，移开再续上——长文案最怕"刚想读
   就被收走"。
4. **合并同款**。``merge_key`` 相同的卡片不再新增，只把计数加一、把计时器
   重置到满——连点三次保存，应该是一条「已保存 ×3」，不是三条。
"""

from __future__ import annotations

import asyncio
import time
import weakref
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import flet as ft

from ui.core.config import logger
from ui.core.float_layer import overlay_usable
from ui.core.tokens import DURATION

__all__ = ["OverlayCard", "OverlayHost", "host_for", "peek_host"]

#: 进场时长。200ms 是"看得见但不拖沓"的档位（与 tokens.DURATION["normal"] 同源）
ENTER_MS = DURATION["normal"]
#: 退场比进场快一档：用户已经决定不要它了，别让他等
EXIT_MS = DURATION["fast"] + 20
#: 挂上去到开始补间之间要让出一帧，否则 flet 会把两次赋值合并成一次
FIRST_FRAME_MS = 16


@dataclass(frozen=True)
class Slot:
    """一种弹出位置。

    ``vertical`` / ``horizontal`` 决定贴哪条边；``enter`` / ``exit`` 是补间用的
    相对偏移（相对卡片自身尺寸的倍数 —— Flutter 的 ``Offset`` 就是这么算的）。
    """

    vertical: str  # "top" | "bottom"
    horizontal: str  # "left" | "center" | "right"
    enter: tuple[float, float]
    exit: tuple[float, float]

    @property
    def reversed_order(self) -> bool:
        """贴底时最新的一条在最下面 —— 视觉上贴着屏幕边缘长出来。"""
        return self.vertical == "bottom"

    def anchor(self, inset: int) -> dict[str, int]:
        """算出浮层节点的定位参数（容器自身的 left/right/top/bottom）。"""
        if self.horizontal == "center":
            return {self.vertical: inset, "left": 0, "right": 0}
        horizontal = {
            "left": {"left": inset},
            "right": {"right": inset},
        }[self.horizontal]
        return {self.vertical: inset, **horizontal}

    def cross(self) -> ft.CrossAxisAlignment:
        return {
            "left": ft.CrossAxisAlignment.START,
            "center": ft.CrossAxisAlignment.CENTER,
            "right": ft.CrossAxisAlignment.END,
        }[self.horizontal]


#: 位置名 → 槽位。名字沿用 Element 的写法，调用方不用记方向。
SLOTS: dict[str, Slot] = {
    "top-center": Slot("top", "center", (0, -0.35), (0, -0.2)),
    "top-left": Slot("top", "left", (-0.08, 0), (-0.08, 0)),
    "top-right": Slot("top", "right", (0.08, 0), (0.08, 0)),
    "bottom-left": Slot("bottom", "left", (-0.08, 0), (-0.08, 0)),
    "bottom-right": Slot("bottom", "right", (0.08, 0), (0.08, 0)),
}


@dataclass
class OverlayCard:
    """一条已经挂上栈的卡片。调用方拿它去 ``close()``，或读 ``count``。"""

    control: ft.Control
    duration: int
    merge_key: Any = None
    on_merge: Callable[[int], None] | None = None
    on_close: Callable[[], None] | None = None
    wrapper: ft.Container | None = None
    count: int = 1
    remaining: int = 0
    token: int = 0
    hovered: bool = False
    deadline: float = 0.0
    closed: bool = False
    dismissed: bool = False
    extra: dict[str, Any] = field(default_factory=dict)


class OverlayHost:
    """一个页面、一个位置上的卡片栈。"""

    def __init__(
        self,
        page: ft.Page,
        position: str,
        *,
        inset: int | None = None,
        gap: int = 12,
    ) -> None:
        self.page = page
        self.position = position
        self.slot = SLOTS[position]
        self.inset = DEFAULT_INSET[position] if inset is None else inset
        self.cards: list[OverlayCard] = []
        self.column = ft.Column(
            spacing=gap, tight=True, horizontal_alignment=self.slot.cross()
        )
        self.box = self._build_node()

    def _build_node(self) -> ft.Control:
        """造浮层节点。

        居中位置要撑满整行才能把卡片摆到中间，而**撑满的节点会把自己那条横带里
        的点击全部吃掉**（实测：10×10 的节点不会，撑满的会）。``TransparentPointer``
        正好解这个：它自己不吃事件，只让里面的东西照常响应。

        四个角落不需要撑满（宽度就是卡片宽度），用普通容器 —— 那里点击本来就
        该落在卡片上（``Notification`` 有 ``on_click``，穿透会导致"点一次、动作
        发生两次"）。

        代价：居中的消息条是"穿透"的，点它不会挡住下面的按钮 —— 包括它自己的
        关闭按钮。轻提示本来就不该拦人，这个取舍是划算的。
        """
        anchor = self.slot.anchor(self.inset)
        if self.slot.horizontal == "center":
            return ft.TransparentPointer(
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER, controls=[self.column]
                ),
                **anchor,
            )
        return ft.Container(content=self.column, **anchor)

    # ------------------------------------------------------------------
    # 对外
    # ------------------------------------------------------------------

    def push(
        self,
        control: ft.Control,
        *,
        duration: int,
        merge_key: Any = None,
        on_merge: Callable[[int], None] | None = None,
        on_close: Callable[[], None] | None = None,
    ) -> OverlayCard:
        """把一张卡片压入栈顶（贴底位置是栈底）。

        Args:
            control: 卡片本体（已画好的 ``Container``）。
            duration: 自动关闭的毫秒数，``0`` 表示常驻。
            merge_key: 合并键。``None`` 表示不合并；有同键卡片时只加计数。
            on_merge: 合并时回调，参数是新的计数 —— 用来把「×2」画到卡片上。
            on_close: 卡片真正消失（退场动画走完）后的回调。

        Returns:
            新建（或复用的）卡片，可用于 ``close()``。
        """
        if merge_key is not None:
            for card in self.cards:
                if not card.closed and card.merge_key == merge_key:
                    card.count += 1
                    card.remaining = duration
                    # 注意用 **card 上存的**回调，不是本次传进来的：计数徽标长在
                    # 第一条卡片上，新实例的控件根本没挂上去（踩过一次）。
                    if card.on_merge is not None:
                        card.on_merge(card.count)
                    self._arm(card)
                    self._update()
                    return card

        card = OverlayCard(
            control=control,
            duration=duration,
            merge_key=merge_key,
            on_merge=on_merge,
            on_close=on_close,
            remaining=duration,
        )
        card.wrapper = ft.Container(
            content=control,
            opacity=0,
            offset=ft.Offset(*self.slot.enter),
            animate_opacity=ft.Animation(ENTER_MS, ft.AnimationCurve.EASE_OUT),
            animate_offset=ft.Animation(ENTER_MS, ft.AnimationCurve.EASE_OUT),
            # 悬停冻结计时：容器本身不透明也无所谓，MouseRegion 覆盖整张卡片
            on_hover=lambda e: self._on_hover(card, e),
        )

        self.cards.insert(0, card)
        self._sync()
        self._mount()
        self._update()
        self._later(FIRST_FRAME_MS, lambda: self._reveal(card))
        return card

    def close(self, card: OverlayCard, *, animated: bool = True) -> None:
        """让一张卡片退场（幂等）。"""
        if card.closed:
            return
        card.closed = True
        card.token += 1
        if not animated or card.wrapper is None:
            self._drop(card)
            return
        wrapper = card.wrapper
        wrapper.animate_opacity = ft.Animation(EXIT_MS, ft.AnimationCurve.EASE_IN)
        wrapper.animate_offset = ft.Animation(EXIT_MS, ft.AnimationCurve.EASE_IN)
        wrapper.opacity = 0
        wrapper.offset = ft.Offset(*self.slot.exit)
        self._update()
        self._later(EXIT_MS + 10, lambda: self._drop(card))

    def clear(self, *, animated: bool = False) -> None:
        """清空整个栈（``close_all`` 用）。默认不播退场——一次关十条不该排队。"""
        for card in list(self.cards):
            self.close(card, animated=animated)

    # ------------------------------------------------------------------
    # 内部：挂载与重绘
    # ------------------------------------------------------------------

    def _mount(self) -> None:
        overlay = self.page.overlay
        if any(node is self.box for node in overlay):
            return
        if not overlay_usable(self.page):
            logger.warning(
                "当前渲染路径（page.render_views / manage_views）会盖住页面浮层，"
                "Message / Notification 可能不会显示。"
            )
        overlay.append(self.box)

    def _sync(self) -> None:
        cards = list(reversed(self.cards)) if self.slot.reversed_order else self.cards
        self.column.controls = [c.wrapper for c in cards if c.wrapper is not None]

    def _update(self) -> None:
        try:
            self.page.update()
        except Exception:  # noqa: BLE001
            # 页面已经关掉了 —— 消息条没义务在窗口消失后继续存在
            logger.debug("Message/Notification 重绘失败（页面可能已关闭）", exc_info=True)

    def _reveal(self, card: OverlayCard) -> None:
        if card.closed or card.wrapper is None:
            return
        card.wrapper.opacity = 1
        card.wrapper.offset = ft.Offset(0, 0)
        self._update()
        self._arm(card)

    def _drop(self, card: OverlayCard) -> None:
        if card.dismissed:
            return
        card.dismissed = True
        card.closed = True
        card.token += 1
        if card in self.cards:
            self.cards.remove(card)
        self._sync()
        self._update()
        if card.on_close is not None:
            try:
                card.on_close()
            except Exception:  # noqa: BLE001 - 回调由调用方提供，不该拖垮栈
                logger.exception("Message / Notification 的 on_close 回调抛异常")

    # ------------------------------------------------------------------
    # 内部：计时
    # ------------------------------------------------------------------

    def _later(self, ms: int, fn: Callable[[], None]) -> None:
        """``ms`` 毫秒后在页面事件循环上执行 ``fn``（不阻塞 UI）。"""

        async def _run() -> None:
            await asyncio.sleep(ms / 1000)
            try:
                fn()
            except Exception:  # noqa: BLE001
                logger.debug("Message/Notification 的延时回调抛异常", exc_info=True)

        try:
            self.page.run_task(_run)
        except Exception:  # noqa: BLE001
            # 事件循环已经停了（页面关闭 / 纯逻辑测试里的假 Page）
            logger.debug("无法排队延时回调", exc_info=True)

    def _arm(self, card: OverlayCard) -> None:
        """（重新）开始倒计时。"""
        if card.duration <= 0:
            return
        card.token += 1
        token = card.token
        delay = card.remaining if card.remaining > 0 else card.duration
        card.remaining = delay
        card.deadline = time.monotonic() + delay / 1000

        def _fire() -> None:
            if card.closed or card.hovered or card.token != token:
                return
            self.close(card)

        self._later(delay, _fire)

    def _on_hover(self, card: OverlayCard, e: Any) -> None:
        if card.closed or card.duration <= 0:
            return
        hovering = bool(getattr(e, "data", False))
        if hovering == card.hovered:
            return
        card.hovered = hovering
        if hovering:
            card.token += 1  # 作废挂起的关闭
            card.remaining = max(1, int((card.deadline - time.monotonic()) * 1000))
        else:
            self._arm(card)


#: 各位置默认离屏幕边缘的距离（逻辑像素）
DEFAULT_INSET: dict[str, int] = {
    "top-center": 20,
    "top-left": 24,
    "top-right": 24,
    "bottom-left": 24,
    "bottom-right": 24,
}

_HOSTS: weakref.WeakKeyDictionary[ft.Page, dict[str, OverlayHost]] = (
    weakref.WeakKeyDictionary()
)


def peek_host(page: ft.Page, position: str) -> OverlayHost | None:
    """只看不建：该位置还没有栈时返回 ``None``。

    ``close_all`` 用得上——不能为了"关掉全部"而先把四个角落的浮层都建出来。
    """
    pool = _HOSTS.get(page)
    return None if pool is None else pool.get(position)


def host_for(
    page: ft.Page, position: str, *, inset: int | None = None, gap: int = 12
) -> OverlayHost:
    """取（必要时创建）该页面该位置的卡片栈。"""
    pool = _HOSTS.get(page)
    if pool is None:
        pool = {}
        _HOSTS[page] = pool
    host = pool.get(position)
    if host is None:
        host = OverlayHost(page, position, inset=inset, gap=gap)
        pool[position] = host
    return host
