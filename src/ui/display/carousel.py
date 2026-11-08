"""轮播 (Carousel) —— 一组内容在同一块地方里轮换。

``Carousel``。它的职责很窄：**空间不够，但内容
必须都摆出来**。所以它不做"图片查看器"（那是 :class:`~ui.display.ImageGridView`），
也不做"分页列表"（那是 :class:`~ui.navigation.Pagination`）——它只负责在同一块
矩形里，把 N 个控件轮流搬到台前。

用法::

    carousel = Carousel(
        slides=[ft.Image(src=s, fit=ft.BoxFit.COVER) for s in urls],
        height=260,
        autoplay=True,
        loop=True,
        on_change=lambda old, new: print(old, "->", new),
    )
    Column([carousel.ui()])

五个取舍（改前先读）
--------------------
1. **滑动，不是淡入淡出**。淡入淡出实现更省（只动 opacity），但"右边还有一张"
   这个最重要的暗示就没了 —— 用户不知道能往哪儿翻。所以每张按
   ``offset = i - index`` 排在一条隐形横带上，切页只改 ``index``：所有卡片
   同时平移一格，Flutter 自己补间。

2. **线性排布，不绕圈**。真正无缝的循环需要"克隆一张首图放在队尾"，而 Flet 的
   控件**不能同时挂在两个父节点上**，克隆任意用户的控件不可靠。所以 ``loop``
   在 0 ↔ 末页那一下是**瞬切**（``animate_offset`` 时长给 0），其余每一页都
   正常补间。这是本组件唯一一处看得见的取舍，换来的是"slide 里放什么都行"。

3. **宽度靠 ``on_size_change`` 量，不要求调用方给**。Flet 没有 ``LayoutBuilder``，
   而 ``offset`` 的单位是"自身尺寸的倍数" —— 只有知道每张多宽，``i - index``
   才等于"平移 i 格"。首帧还没量到时只画当前这张（位置必然正确），量到之后
   换成整条横带，两帧画面完全一致，看不到跳变。

4. **自动播放挂在 ``use_effect`` 上，用 token 作废旧计时**。``page.run_task``
   拿到的是 ``Future``，没有 cancel；所以每次重排就把 ``_token`` 加一，旧协程
   醒来发现 token 变了就静默退出。**关掉自动播放 / 悬停暂停也照样作废**：
   否则「暂停」之后那一次已排好的计时还会再翻一张。

5. **圆点按 16×16 的命中区做，不是 4px 的小横条本身**。4px 高的目标点不中，
   这是最容易被忽略的可达性问题：可视尺寸 16×4，命中区上下各垫 6px。

配色：圆点在 ``inside`` 时用白色（压在图片上，只有白色可靠），并带一层极淡的
投影 —— 浅色图片上也能看见；``outside`` 时改用主题角色（``primary`` /
``outline``），因为它落在页面底色上。箭头是一层半透明黑 + 白图标，与内容解耦。
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any

import flet as ft

from ui.core.config import logger
from ui.core.doc import Api, Example, Spec, info, run, tip, warn
from ui.core.empty import empty_block
from ui.core.i18n import t, use_t
from ui.core.theme import use_theme
from ui.core.tokens import DURATION, FONT_SIZE, FONT_WEIGHT, RADIUS, SPACE, overlay

__all__ = [
    "ARROW_MODES",
    "DOT_MODES",
    "DOT_POSITIONS",
    "TRIGGERS",
    "Carousel",
    "normalize_index",
    "slide_offsets",
    "step_index",
]

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------
#: 箭头显隐策略：``hover`` 悬停才出现（默认）/ ``always`` 一直在 / ``never`` 不画
ARROW_MODES: tuple[str, ...] = ("hover", "always", "never")
#: 圆点位置：``inside`` 压在内容上 / ``outside`` 落在内容外 / ``none`` 不画
DOT_MODES: tuple[str, ...] = ("inside", "outside", "none")
#: 圆点吸附的边
DOT_POSITIONS: tuple[str, ...] = ("bottom", "top", "left", "right")
#: 圆点切换内容的触发方式：``click`` 点击 / ``hover`` 划过
TRIGGERS: tuple[str, ...] = ("click", "hover")

ARROW = 32  # 箭头按钮边长
ARROW_ICON = 18  # 箭头图标字号（比按钮小一圈才不顶边）
EDGE = SPACE["3"]  # 12  箭头 / 圆点离内容边缘的距离
DOT_W = 16  # 默认圆点：横条
DOT_H = 4
DOT_ROUND = 8  # radius_dot=True 时的圆点直径
DOT_PAD_H = 3  # 左右垫 3 + 左右垫 3 = 6 的间距
DOT_PAD_V = 6  # 上下各垫 6，命中区高 16


# ---------------------------------------------------------------------------
# 纯函数（单测直接断言这几个）
# ---------------------------------------------------------------------------
def normalize_index(index: int, count: int, *, loop: bool = False) -> int:
    """把任意整数折进 ``0 .. count-1``。

    ``count <= 0`` 时返回 0 —— 空轮播也得有个合法索引，否则调用方到处写判断。
    ``loop`` 打开时按取模绕回（``-1`` → 最后一张）；关掉时直接夹到两端。
    """
    if count <= 0:
        return 0
    value = int(index)
    if loop:
        return value % count
    return min(max(value, 0), count - 1)


def step_index(
    index: int, delta: int, count: int, *, loop: bool = False
) -> tuple[int, bool]:
    """往前走（``delta > 0``）或往回走一步。

    Returns:
        ``(新索引, 是否瞬移)``。**瞬移**指跨过了首尾边界 —— 线性排布下这一下
        会横穿整条，补间只会让人眼晕，所以调用方要把动画时长设成 0。
        走到头又走不动（没开 loop）时返回原索引，调用方据此判断"没变化"。
    """
    if count <= 1:
        return 0, False
    raw = int(index) + int(delta)
    if loop:
        return raw % count, raw >= count or raw < 0
    return min(max(raw, 0), count - 1), False


def slide_offsets(count: int, index: int) -> tuple[int, ...]:
    """第 ``i`` 张相对当前的位置（0 = 正在台前）。

    这个"线性"的映射是刻意的：它让每张的位置只跟自己的序号有关，切页时所有
    卡片平移同样的格数，动画天然同步。换成环形最近距离也能算，但那样每张卡片
    的位置会在跨过对侧时突变 —— 补间会把它从屏幕这头扫到那头。
    """
    return tuple(i - int(index) for i in range(max(count, 0)))


def _entering(value: object) -> bool:
    """把 hover 事件载荷归一成"进来了吗"（可能是 bool，也可能是 ``"true"``）。"""
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


# ---------------------------------------------------------------------------
# 组件
# ---------------------------------------------------------------------------
@ft.observable
@dataclass
class Carousel:
    """轮播：一叠控件轮流上台。

    Args:
        slides: 每一页的内容，按显示顺序给。任意控件都行 —— 一格图片、
            一张卡片、一段视频。**必须自己撑满**（图片加 ``fit=COVER``，
            卡片加 ``expand=True``），轮播只负责把它们搬来搬去。
        index: 初始显示第几张（从 0 数）。之后读 :attr:`current` 拿当前页。
        height: 轮播高度。**必须给**：每张卡片按这个高度横向排开。
        width: 组件宽度，``None`` 跟随父容器（推荐）。
        arrow: 左右箭头的显隐，``"hover"`` / ``"always"`` / ``"never"``。
            ``hover`` 时箭头在指针进入前不占点击 —— 看不见的东西不该能点。
        dots: 圆点，``"inside"`` 压在内容上 / ``"outside"`` 落在内容外 /
            ``"none"``。内容不是图片时用 ``outside``，主题色在任意底色上都读得清。
        dots_position: 圆点贴哪条边，``bottom`` / ``top`` / ``left`` /
            ``right``。左右两侧时自动竖排。
        radius_dot: 圆点用圆形（8px）而不是 16×4 的小横条。
        trigger: 圆点切页的触发方式，``"click"`` 点击 / ``"hover"`` 划过。
        autoplay: 自动播放。
        autoplay_speed: 自动播放间隔（毫秒）。
        pause_on_hover: 指针停在轮播上时暂停自动播放（默认开）。长文案最怕
            "刚想读就被翻走"。
        loop: 到最后一张后是否绕回第一张。
        duration: 切换动画时长（毫秒）。
        border_radius: 圆角；``0`` 即为直角。
        on_change: 切页回调，入参 ``(旧索引, 新索引)``。
        on_click: 点击内容区回调，入参当前索引。内容里自己的按钮不受影响。

    Notes:
        高度必须由调用方给定，宽度不用 —— 宽度在挂载后由 ``on_size_change``
        量出来，父容器变宽变窄它自己跟着变。
    """

    slides: Sequence[ft.Control] = field(default_factory=list)
    index: int = 0
    height: float = 220
    width: int | float | None = None
    arrow: str = "hover"
    dots: str = "inside"
    dots_position: str = "bottom"
    radius_dot: bool = False
    trigger: str = "click"
    autoplay: bool = False
    autoplay_speed: int = 4000
    pause_on_hover: bool = True
    loop: bool = False
    duration: int = 420
    border_radius: float = RADIUS["lg"]
    on_change: Callable[[int, int], None] | None = None
    on_click: Callable[[int], None] | None = None

    # ---- 运行期状态（下划线开头：不参与构造，靠 _repaint() 重绘）------------
    _index: int = field(default=0, init=False, repr=False)
    _width: float = field(default=0.0, init=False, repr=False)
    _hovered: bool = field(default=False, init=False, repr=False)
    _hover_key: str | None = field(default=None, init=False, repr=False)
    _snap: bool = field(default=False, init=False, repr=False)
    _token: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        for name, value, allowed in (
            ("arrow", self.arrow, ARROW_MODES),
            ("dots", self.dots, DOT_MODES),
            ("dots_position", self.dots_position, DOT_POSITIONS),
            ("trigger", self.trigger, TRIGGERS),
        ):
            if value not in allowed:
                raise ValueError(f"{name} 只能是 {allowed}，收到 {value!r}")
        if self.height <= 0:
            raise ValueError("height 必须大于 0：每张按这个高度横向排开")
        self._index = normalize_index(self.index, len(self.slides), loop=self.loop)
        self._width = float(self.width or 0)

    # ==================================================================
    # 对外查询
    # ==================================================================
    @property
    def count(self) -> int:
        """一共有几页。"""
        return len(self.slides)

    @property
    def current(self) -> int:
        """当前显示第几页（从 0 数）。"""
        return self._index

    # ==================================================================
    # 状态变更（也可以从代码里调，不只是点箭头）
    # ==================================================================
    def go(self, index: int, *, animate: bool = True) -> None:
        """跳到第 ``index`` 页。越界时按 ``loop`` 绕回或夹到端点。"""
        count = len(self.slides)
        target = normalize_index(index, count, loop=self.loop)
        if target == self._index:
            return
        jumped = self.loop and count > 1 and not 0 <= int(index) < count
        self._apply(target, jumped=jumped, animate=animate)

    def next(self, *, animate: bool = True) -> None:
        """下一页（到头了按 ``loop`` 决定绕回还是不动）。"""
        target, jumped = step_index(self._index, 1, len(self.slides), loop=self.loop)
        if target != self._index:
            self._apply(target, jumped=jumped, animate=animate)

    def prev(self, *, animate: bool = True) -> None:
        """上一页。"""
        target, jumped = step_index(self._index, -1, len(self.slides), loop=self.loop)
        if target != self._index:
            self._apply(target, jumped=jumped, animate=animate)

    def invalidate(self) -> None:
        """换掉了 ``slides`` 之后调一下：把索引夹回合法区间并重绘。"""
        self._index = normalize_index(self._index, len(self.slides), loop=self.loop)
        self._repaint()

    # ==================================================================
    # 内部
    # ==================================================================
    def _apply(self, target: int, *, jumped: bool, animate: bool) -> None:
        old = self._index
        # 瞬移这一帧把动画时长压到 0：Flutter 的隐式动画不补间，位置直接就位
        self._snap = (not animate) or jumped
        self._index = target
        self._repaint()
        if self.on_change is not None:
            self.on_change(old, target)

    def _repaint(self) -> None:
        """请求重绘。

        名字**不能**叫 ``_notify``：``@ft.observable`` 自己注入了
        ``_notify(name)``，覆盖了会在构造期直接 ``TypeError``。
        """
        notify = getattr(self, "notify", None)
        if callable(notify):
            notify()

    def _hover_matters(self) -> bool:
        """悬停状态会不会影响画面 —— 不影响就别挂监听，省一轮重绘。"""
        return self.arrow == "hover" or (self.autoplay and self.pause_on_hover)

    @property
    def _paused(self) -> bool:
        """自动播放此刻是否该停（悬停暂停）。"""
        return bool(self.autoplay and self.pause_on_hover and self._hovered)

    # ---- 自动播放 ----------------------------------------------------
    def _schedule(self):
        """排下一次自动切换。作为 ``use_effect`` 的 setup 调用。

        依赖变化（切页 / 开关 / 间隔 / 悬停 / 页数）就会重跑：旧的协程靠
        ``_token`` 作废，新的从这一刻重新计时 —— "刚翻完不该马上又翻"。

        ``_token`` 必须在最前面加一，哪怕这一轮不排计时：关掉自动播放或悬停
        暂停时也要把**已经在睡**的那次作废，不然暂停之后还会莫名翻一张。
        """
        token = object.__getattribute__(self, "_token") + 1
        # 直接 setattr 会让 @ft.observable 触发一次重绘，而 _token 不影响画面
        object.__setattr__(self, "_token", token)
        if not self.autoplay or self._paused or len(self.slides) < 2:
            return
        delay = max(int(self.autoplay_speed), 200) / 1000

        async def tick() -> None:
            await asyncio.sleep(delay)
            if token != object.__getattribute__(self, "_token"):
                return  # 期间切过页 / 悬停过 / 关掉了自动播放
            self.next()

        try:
            ft.context.page.run_task(tick)
        except Exception:  # noqa: BLE001 - 页面已关 / 纯逻辑测试里的假 Page
            logger.debug("轮播的自动播放定时器没能排上", exc_info=True)
        return

    # ---- 事件 --------------------------------------------------------
    def _on_resize(self, e: ft.LayoutSizeChangeEvent) -> None:
        """量到真实宽度：整条横带这才排得出来。"""
        width = getattr(e, "width", None)
        if width and abs(width - self._width) > 0.5:
            self._width = float(width)
            self._repaint()

    def _hover_stage(self, e: Any) -> None:
        entering = _entering(getattr(e, "data", e))
        if entering == self._hovered:
            return
        self._hovered = entering
        self._repaint()

    def _hover_item(self, key: str, e: Any) -> None:
        """箭头 / 圆点的悬停：只记一个键，范围没变就不重绘。"""
        entering = _entering(getattr(e, "data", e))
        if entering:
            if self._hover_key == key:
                return
            self._hover_key = key
        else:
            if self._hover_key != key:
                return  # 离开的是别的控件（事件顺序乱时会出现），忽略
            self._hover_key = None
        self._repaint()

    def _hover_dot(self, page: int, e: Any) -> None:
        """圆点悬停：``trigger="hover"`` 时顺手切过去。"""
        entering = _entering(getattr(e, "data", e))
        if entering and self.trigger == "hover" and page != self._index:
            self._hover_key = f"d{page}"
            self.go(page)  # go() 自己会重绘
            return
        self._hover_item(f"d{page}", e)

    # ==================================================================
    # 渲染
    # ==================================================================
    @ft.component
    def ui(self) -> ft.Control:
        """构建轮播。"""
        use_t()  # 订阅语言：箭头的 tooltip 跟着切
        use_theme()  # 订阅主题：outside 圆点走角色色
        ft.use_effect(
            self._schedule,
            [
                self._index,
                self.autoplay,
                self.autoplay_speed,
                self._paused,
                len(self.slides),
                self.loop,
            ],
        )
        return ft.Container(width=self.width, content=self._compose())

    def _compose(self) -> ft.Control:
        """内容区 + 可选的"外面"那圈圆点。"""
        bar = self._outside_dots()
        if bar is None:
            return self._stage()
        if self.dots_position in ("left", "right"):
            stage = self._stage(expand=True)
            items: list[ft.Control] = (
                [bar, stage] if self.dots_position == "left" else [stage, bar]
            )
            return ft.Row(
                spacing=SPACE["2"],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=items,
            )
        stage = self._stage()
        controls = [bar, stage] if self.dots_position == "top" else [stage, bar]
        return ft.Column(spacing=SPACE["2"], tight=True, controls=controls)

    def _stage(self, *, expand: bool = False) -> ft.Control:
        """内容舞台：一条被裁切的横带 + 压在它上面的箭头与圆点。"""
        count = len(self.slides)
        layers: list[ft.Control] = []
        if count == 0:
            layers.append(self._empty())
        elif self._width > 0:
            layers.extend(self._slide(i) for i in range(count))
        else:
            # 还没量到宽度：先只画当前这张。它的位置必然是对的（offset 为 0），
            # 量到之后换成整条横带，两帧像素一致，看不到跳变。
            layers.append(
                ft.Container(height=self.height, content=self.slides[self._index])
            )
        if count > 1:
            if self.arrow != "never":
                layers.extend([self._arrow(-1), self._arrow(1)])
            if self.dots == "inside":
                layers.append(self._inside_dots())
        return ft.Container(
            height=self.height,
            expand=expand,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            border_radius=self.border_radius,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            on_size_change=self._on_resize,
            size_change_interval=0,
            on_hover=self._hover_stage if self._hover_matters() else None,
            content=ft.Stack(
                height=self.height,
                alignment=ft.Alignment.CENTER,
                controls=layers,
            ),
        )

    def _empty(self) -> ft.Control:
        # 高度交给外层：轮播本身是定高的，空态只需在中间居中一行。
        return empty_block(t("ui.carousel.empty"), height=None)

    def _slide(self, page: int) -> ft.Control:
        """一页。``offset`` 的单位是"自身的倍数"，宽即一格，所以直接写格数。"""
        duration = 0 if self._snap else self.duration
        return ft.Container(
            width=self._width,
            height=self.height,
            offset=ft.Offset(float(page - self._index), 0),
            animate_offset=ft.Animation(duration, ft.AnimationCurve.EASE_IN_OUT),
            # 点击挂在**每一页**上，不挂在舞台：箭头与圆点是舞台的兄弟节点，
            # 挂在舞台会被 Flet 的点击冒泡带出来（点箭头同时也算点了内容）。
            on_click=self._tap if self.on_click is not None else None,
            content=self.slides[page],
        )

    def _tap(self, _e: Any) -> None:
        if self.on_click is not None:
            self.on_click(self._index)

    # ---- 箭头 --------------------------------------------------------
    def _arrow(self, direction: int) -> ft.Control:
        """左右箭头。``arrow="hover"`` 时指针进来前是透明的，且**完全不挡路**。

        为什么未浮现时要包一层 ``TransparentPointer``：Flet 的 ``Container``
        只要带圆角或底色，命中测试就返回"命中"—— 一块 ``opacity=0`` 的圆盘
        照样会把内容区边缘的点击吃掉（真机对拍：点箭头既没翻页、也没触发
        ``on_click``，事件凭空消失）。``TransparentPointer`` 让它穿过去，点到的
        就是底下那一页。

        透明度与动画留在**外层**容器上：外层控件身份不变，淡入依旧补间；只有
        "脸面"在浮现 / 未浮现之间换了个壳。
        """
        key = "prev" if direction < 0 else "next"
        # 不循环时走到头，这一侧的箭头点了也不会动。以前它照常亮着、照常悬停、
        # 点了什么都不发生 —— 看起来就是坏了。现在淡出并且不接点击。
        at_edge = not self.loop and (
            self._index <= 0 if direction < 0 else self._index >= len(self.slides) - 1
        )
        shown = self.arrow == "always" or self._hovered or self._hover_key == key
        lit = self._hover_key == key and not at_edge
        anchor: dict[str, float] = {"left": EDGE} if direction < 0 else {"right": EDGE}
        face = ft.Container(
            width=ARROW,
            height=ARROW,
            border_radius=RADIUS["full"],
            bgcolor=overlay(0.46 if lit else 0.30, role=ft.Colors.BLACK),
            alignment=ft.Alignment.CENTER,
            content=ft.Icon(
                ft.Icons.CHEVRON_LEFT_ROUNDED
                if direction < 0
                else ft.Icons.CHEVRON_RIGHT_ROUNDED,
                size=ARROW_ICON,
                color=ft.Colors.WHITE,
            ),
        )
        return ft.Container(
            width=ARROW,
            height=ARROW,
            # 钉在垂直中线上而不是 top=0/bottom=0 撑满整列：撑满就是一整条
            # 看不见的挡板，会把内容区右边缘的点击全吃掉
            top=(self.height - ARROW) / 2,
            opacity=0.0 if not shown else (0.38 if at_edge else 1.0),
            animate_opacity=ft.Animation(DURATION["fast"], ft.AnimationCurve.EASE_OUT),
            tooltip=t("ui.carousel.prev") if direction < 0 else t("ui.carousel.next"),
            on_hover=None
            if (not shown or at_edge)
            else (lambda e, k=key: self._hover_item(k, e)),
            on_click=None
            if (not shown or at_edge)
            else (lambda _e, d=direction: self.prev() if d < 0 else self.next()),
            content=face if shown else ft.TransparentPointer(content=face),
            **anchor,
        )

    # ---- 圆点 --------------------------------------------------------
    def _dots(self) -> ft.Control:
        """一排（或一列）圆点。左右贴边时竖排。"""
        vertical = self.dots_position in ("left", "right")
        maker = ft.Column if vertical else ft.Row
        return maker(
            spacing=0,
            tight=True,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[self._dot(i) for i in range(len(self.slides))],
        )

    def _dot(self, page: int) -> ft.Control:
        active = page == self._index
        hovered = self._hover_key == f"d{page}"
        inside = self.dots == "inside"
        if inside:
            # 压在图片上：只有白色可靠。非当前项降透明度，悬停提一档
            color: ft.ColorValue = ft.Colors.WHITE
            if not active:
                color = ft.Colors.with_opacity(
                    0.72 if hovered else 0.42, ft.Colors.WHITE
                )
        elif active:
            color = ft.Colors.PRIMARY
        else:
            color = ft.Colors.OUTLINE if hovered else ft.Colors.OUTLINE_VARIANT

        width, height = DOT_W, DOT_H
        if self.radius_dot:
            width = height = DOT_ROUND
        elif self.dots_position in ("left", "right"):
            # 竖排时横条要跟着转 90°，否则读起来像"一摞省略号"
            width, height = DOT_H, DOT_W
        box = ft.Container(
            width=width,
            height=height,
            bgcolor=color,
            border_radius=RADIUS["full"],
            # 极淡的投影：白点在浅色图片上只剩一条若隐若现的边
            shadow=None
            if not inside
            else [
                ft.BoxShadow(
                    blur_radius=3,
                    offset=ft.Offset(0, 1),
                    color=ft.Colors.with_opacity(0.32, ft.Colors.BLACK),
                )
            ],
        )
        # 可视 16×4，命中区 22×16：4px 高的目标点不中，垫高是可达性要求
        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=DOT_PAD_H, vertical=DOT_PAD_V),
            tooltip=t("ui.carousel.slide", n=page + 1),
            on_click=lambda _e, p=page: self.go(p),
            on_hover=lambda e, p=page: self._hover_dot(p, e),
            content=box,
        )

    def _inside_dots(self) -> ft.Control:
        """压在内容上的那层圆点。只占一条细边，不挡内容区的点击。"""
        bar = ft.Container(alignment=ft.Alignment.CENTER, content=self._dots())
        position = self.dots_position
        if position in ("bottom", "top"):
            return ft.Container(
                left=0,
                right=0,
                **{position: EDGE},
                alignment=ft.Alignment.BOTTOM_CENTER
                if position == "bottom"
                else ft.Alignment.TOP_CENTER,
                content=bar,
            )
        return ft.Container(
            top=0,
            bottom=0,
            **{position: EDGE},
            alignment=ft.Alignment.CENTER_LEFT
            if position == "left"
            else ft.Alignment.CENTER_RIGHT,
            content=bar,
        )

    def _outside_dots(self) -> ft.Control | None:
        if self.dots != "outside" or len(self.slides) < 2:
            return None
        if self.dots_position in ("left", "right"):
            return self._dots()
        return ft.Container(alignment=ft.Alignment.CENTER, content=self._dots())


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
_MUTED = ft.Colors.ON_SURFACE_VARIANT

#: 示例页的渐变底。**具名常量而不是内联字面量**：这是演示用的品牌色组合，
#: 不是界面令牌，但要能一眼看出"这四个是刻意的"。
_SLIDE_PALETTE: tuple[tuple[str, str], ...] = (
    ("#1F6FEB", "#4F46E5"),  # PRIMARY_SEEDS: blue -> indigo
    ("#0D9488", "#16A34A"),  # teal -> green
    ("#EA580C", "#DC2626"),  # orange -> red
    ("#7C3AED", "#DB2777"),  # violet -> pink
)

#: 每页的标题与副标题。示例内容全部本地绘制，不引用网络图片。
_CARDS: tuple[tuple[str, str], ...] = (
    ("设计令牌", "一套令牌，明暗与主色自动跟随"),
    ("组件库", "六十余个组件，交互与可访问性对齐"),
    ("文档站", "每个组件都能就地跑起来"),
    ("桌面端", "同一份代码，Windows / macOS 都能跑"),
)


def _sample(index: int, title: str, subtitle: str) -> ft.Control:
    """一页"图"：渐变底 + 文字。离线可渲染，不依赖任何网络资源。"""
    start, end = _SLIDE_PALETTE[index % len(_SLIDE_PALETTE)]
    return ft.Container(
        expand=True,
        padding=SPACE["6"],
        alignment=ft.Alignment.CENTER,
        gradient=ft.LinearGradient(
            begin=ft.Alignment.TOP_LEFT,
            end=ft.Alignment.BOTTOM_RIGHT,
            colors=[start, end],
        ),
        content=ft.Column(
            spacing=SPACE["2"],
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(
                    title,
                    size=FONT_SIZE["headline_lg"],
                    weight=FONT_WEIGHT["semibold"],
                    color=ft.Colors.WHITE,
                ),
                ft.Text(
                    subtitle,
                    size=FONT_SIZE["body"],
                    color=ft.Colors.with_opacity(0.85, ft.Colors.WHITE),
                ),
            ],
        ),
    )


def _deck(count: int) -> list[ft.Control]:
    """取前 ``count`` 页。"""
    return [_sample(i, title, sub) for i, (title, sub) in enumerate(_CARDS[:count])]


def _caption(text: str) -> ft.Text:
    return ft.Text(text, size=FONT_SIZE["caption"], color=_MUTED)


@ft.component
def _basic() -> ft.Control:
    """四页、循环、圆点压在内容上；切页结果回写到下面那行说明。"""
    index, set_index = ft.use_state(0)
    carousel = ft.use_memo(
        lambda: Carousel(
            slides=_deck(4),
            height=220,
            loop=True,
            on_change=lambda _old, new: set_index(new),
        ),
        [],
    )
    return ft.Container(
        width=680,
        content=ft.Column(
            spacing=SPACE["2"],
            controls=[
                carousel.ui(),
                _caption(f"第 {index + 1} / {carousel.count} 张 · 箭头与圆点都能翻"),
            ],
        ),
    )


@ft.component
def _outside() -> ft.Control:
    """圆点落到内容外、箭头常显：内容不是图片时主题色才读得清。"""
    carousel = ft.use_memo(
        lambda: Carousel(
            slides=_deck(3),
            height=200,
            arrow="always",
            dots="outside",
            radius_dot=True,
            loop=True,
        ),
        [],
    )
    return ft.Container(width=680, content=carousel.ui())


@ft.component
def _autoplay() -> ft.Control:
    """自动播放默认是停的，点「播放」才开始 —— 演示页不该自己动起来。"""
    carousel = ft.use_memo(
        lambda: Carousel(
            slides=_deck(3),
            height=200,
            autoplay_speed=2500,
            dots="outside",
            loop=True,
        ),
        [],
    )
    playing, set_playing = ft.use_state(False)

    def toggle(_event: ft.Event[ft.Button]) -> None:
        # 赋值即重绘：ui() 里的 use_effect 会按新的 autoplay 重排（或作废）计时
        carousel.autoplay = not carousel.autoplay
        set_playing(carousel.autoplay)

    return ft.Container(
        width=680,
        content=ft.Column(
            spacing=SPACE["2"],
            controls=[
                carousel.ui(),
                ft.Row(
                    spacing=SPACE["3"],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Button("暂停" if playing else "播放", on_click=toggle),
                        _caption("每 2.5 秒翻一张；指针停在上面会暂停计时"),
                    ],
                ),
            ],
        ),
    )


# ---------------------------------------------------------------------------
# 示例源码（“查看代码”面板）
# ---------------------------------------------------------------------------
_BASIC_CODE = """carousel = Carousel(
    slides=[card_a, card_b, card_c],   # 每页自己撑满：图片 fit=COVER，卡片 expand=True
    height=220,                        # 高度必填，每页按它横向排开
    loop=True,
    on_change=lambda old, new: print(old, "->", new),
)

Column([Container(width=680, content=carousel.ui())])"""

_OUTSIDE_CODE = """Carousel(
    slides=cards,
    height=200,
    arrow="always",      # hover 时箭头只在指针进入后才浮现
    dots="outside",      # 内容不是图片时用它：圆点落在页面底色上，走主题色
    radius_dot=True,
    loop=True,
)"""

_AUTOPLAY_CODE = """carousel = Carousel(
    slides=cards,
    height=200,
    autoplay_speed=2500,   # 毫秒；小于 200 会被夹到 200
    pause_on_hover=True,   # 指针停上去就暂停
    loop=True,
)

carousel.autoplay = True    # 运行期开关：赋值即重绘，计时重新排"""


# ---------------------------------------------------------------------------
# 组件说明
# ---------------------------------------------------------------------------
SPEC = Spec(
    name="Carousel",
    summary="同一块地方轮流摆几页内容：左右箭头、指示点，可选自动播放。",
    definition=(
        "轮播解决的是「位置只有一个，内容有好几份」。它按固定高度把每页横向排开，"
        "切页时整条带子平移一格 —— 用位移而不是淡入淡出，因为「右边还有一张」这个"
        "暗示只有看得见的边沿给得出来。它不加载也不裁剪内容：每页放图片、卡片还是"
        "一段视频都由调用方决定，轮播只负责决定谁在台前。"
    ),
    anatomy=[
        (
            "舞台",
            "圆角 8 的裁切窗口，高度由 height 定死；每页按这个高度横向排开，切页只改偏移量。",
        ),
        (
            "箭头",
            "32px 圆形、半透明黑底 + 白图标。arrow=hover 时指针进舞台才浮现，浮现前透明且不挡点击，点内容边缘不会被它吃掉。",
        ),
        (
            "指示点",
            "16×4 横条（radius_dot 换成 8px 圆），可视很小但命中区 22×16。inside 用白色压在内容上，outside 用主色 / outline 落在页面底色上。",
        ),
        (
            "自动播放",
            "计时挂在 use_effect 上：切页、悬停、改间隔都会作废旧计时从头算；指针停上去默认暂停，长文案最怕「刚想读就被翻走」。",
        ),
        (
            "空态",
            "slides 为空时给一行「暂无内容」，高度照旧 —— 高度塌成 0 的轮播在页面上等于消失了。",
        ),
    ],
    when=[
        "首页横幅、公告条：一个固定位置要轮换几份内容",
        "产品截图、步骤引导：用户本来就该按顺序看完",
        "空间被卡片挤死，但几张内容都得摆出来",
    ],
    avoid=[
        "用户要在几份内容之间来回对照：用 Tabs —— 标签常驻可点，位置一眼可见，圆点只表示数量与顺序",
        "表单、长文这类要读要填的内容：自动播放与误触都会打断，直接铺开",
        "只有两三页且都放得下：并排 GridView 少一次点击，也不用等动画",
    ],
    examples=[
        Example(
            "基础用法",
            _basic,
            hint="四页循环，圆点压在内容下沿；切页后下面那行跟着变，on_change 拿到的是 (旧, 新)。",
            code=_BASIC_CODE,
        ),
        Example(
            "外置圆点",
            _outside,
            hint="dots=outside + arrow=always：圆点落到内容外走主题色，箭头一直可见。",
            code=_OUTSIDE_CODE,
        ),
        Example(
            "自动播放",
            _autoplay,
            hint="默认停着，点「播放」才开始；指针停在轮播上会暂停，移开继续。",
            code=_AUTOPLAY_CODE,
        ),
    ],
    api=[
        Api("slides", "Sequence[Control]", "[]", "每一页的内容，按显示顺序给"),
        Api(
            "height",
            "float",
            "220",
            "轮播高度；<=0 直接抛 ValueError，每页按它横向排开",
        ),
        Api("width", "int | float | None", "None", "留空跟随父容器，挂载后自动量宽"),
        Api("arrow", "str", "'hover'", "hover / always / never 三档"),
        Api("dots", "str", "'inside'", "inside 压内容、outside 落内容外、none 不画"),
        Api(
            "dots_position",
            "str",
            "'bottom'",
            "bottom / top / left / right，左右时自动竖排",
        ),
        Api("autoplay", "bool", "False", "自动播放；运行期赋值即生效"),
        Api("loop", "bool", "False", "到最后一页是否绕回第一页"),
        Api(
            "on_change",
            "Callable[[int, int], None] | None",
            "None",
            "切页回调，入参 (旧索引, 新索引)",
        ),
        Api(
            "go(index)", "(int) -> None", "—", "跳到指定页；越界按 loop 绕回或夹到端点"
        ),
    ],
    notes=[
        tip(
            "高度是硬约束：每页按它横向排开，没有高度就没有「一格」，所以 <=0 会直接抛"
            " ValueError。宽度不用给 —— 挂载后由 on_size_change 量出真实宽度，父容器"
            "变宽变窄它自己跟着变。"
        ),
        info(
            "自动播放挂在 use_effect 上，切页 / 悬停 / 改 autoplay_speed 都会作废旧计时"
            "从头算，刚翻完不会马上又翻；关掉自动播放也会立刻取消已经排好的那一次。"
        ),
        warn(
            "loop=False 时，到头那一侧的箭头淡到 38% 并停止响应点击。点了没反应比看不见"
            "更像故障，所以宁可让它显式地表示「到头了」。"
        ),
    ],
    tags=("轮播", "carousel", "banner", "幻灯片", "自动播放"),
)


if __name__ == "__main__":
    run(SPEC)
