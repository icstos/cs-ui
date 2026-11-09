"""响应式：窗口宽度 → 三档布局策略。

为什么是"三档"而不是六档
------------------------

:data:`~ui.core.tokens.BREAKPOINT` 里有六个断点（xs…xxl），那是**栅格换列**需要的
粒度；布局**策略**只要三档就够了，而且再多就是把同一件事切成碎片：

=========  ==================  ================================================
窗口类      宽度                布局上真正变了什么
=========  ==================  ================================================
compact    < 768               单列；侧栏收起；页头操作折到第二行；内边距 16
medium     768 – 1199          两列；侧栏可常驻；内边距 24
expanded   ≥ 1200              侧栏 + 内容 + 大纲三栏；内边距 32；内容居中限宽
=========  ==================  ================================================

六个断点里的 md(768) 与 xl(1200) 正好是这三档的分界，所以「组件认为自己是窄屏」
与「ResponsiveRow 已经换列」永远同步 —— 这一条比多一档粒度重要得多。

性能：只在**跨档**时通知
------------------------

``page.on_resize`` 每拖一个像素就触发一次。若把宽度写进 observable，每次都会通知
订阅者重绘整棵子树 —— 拖动窗口时画面会变成幻灯片。所以：

* :class:`ResponsiveState` 只有 ``size_class`` 一个字段，**赋值前先比较**，
  跨档才写（写 observable 字段即通知）；
* 精确宽度放在 :func:`viewport` 返回的不可变快照里，更新它**不触发任何重绘**；
* 需要"跟着像素连续变化"的东西（图片宽度、图表画布）**不要**走这里 ——
  交给 Flutter 的 ``expand`` / ``ResponsiveRow`` / ``on_size_change``，
  那是在渲染层解决的，不经过 Python。

一句话：**结构性变化走 Python（跨档，罕见），连续性变化走 Flutter（每帧，免费）。**

用法::

    from ui import use_responsive, Grid, PageLayout

    @ft.component
    def Page() -> ft.Control:
        r = use_responsive()            # 跨档时本组件重绘
        return PageLayout(
            title="用户管理",
            controls=[
                Grid(min_col_width=260, controls=cards),   # 换列在 Flutter 侧
                ViewPanel if r.size_class != "compact" else None,
            ],
        )
"""

from __future__ import annotations

import weakref
from dataclasses import dataclass
from typing import Any, TypeVar

import flet as ft

from ui.core.tokens import BREAKPOINT

__all__ = [
    "COLUMNS",
    "SIZE_CLASSES",
    "ResponsiveState",
    "Viewport",
    "apply_responsive",
    "at_least",
    "pick",
    "reset",
    "resolve",
    "responsive_context",
    "responsive_state",
    "size_class",
    "update",
    "use_responsive",
    "viewport",
]

T = TypeVar("T")

#: 三档窗口类，窄 → 宽。顺序即"能力递增"，取值时可以直接比下标。
SIZE_CLASSES: tuple[str, ...] = ("compact", "medium", "expanded")

#: 每档的栅格列数 —— 正好是 Material 3 的 4 / 8 / 12 列。
#: 卡片墙、表单、统计块都按这个数算 `col`，于是"一屏几列"在框架里只有一个答案。
COLUMNS: dict[str, int] = {"compact": 4, "medium": 8, "expanded": 12}

#: 窗口类分界：与 :data:`BREAKPOINT` 的 md / xl 同源，不另写数字。
_BOUNDS: tuple[tuple[str, int], ...] = (
    ("expanded", BREAKPOINT["xl"]),
    ("medium", BREAKPOINT["md"]),
)

#: 宽度未知时的假设值。宁可假设成"宽敞"也不假设成"紧凑"：
#: 猜宽了最多是多留一点白，猜窄了会把侧栏永久收起来、让用户以为功能没了。
_DEFAULT_WIDTH: float = 1280.0
_DEFAULT_HEIGHT: float = 800.0


# ---------------------------------------------------------------------------
# 纯函数：给定宽度，回答"算哪一档"
# ---------------------------------------------------------------------------
def size_class(width: float | int | None) -> str:
    """宽度 → ``compact`` / ``medium`` / ``expanded``。

    边界取**左闭右开**（``>= 768`` 即 medium）：断点值本身属于更宽的那一档。
    这样 768 整的窗口不会因为浮点误差在两档之间抖动。
    """
    w = _coerce(width)
    for name, lower in _BOUNDS:
        if w >= lower:
            return name
    return "compact"


def at_least(width: float | int | None, breakpoint: str) -> bool:
    """宽度是否达到某个断点（``"sm"`` / ``"md"`` / …）。

    给"只要一个阈值"的场合用：比如窄屏隐藏次要操作、宽屏才显示大纲栏。
    非法断点名返回 ``False``（而不是抛）—— 布局判断不该让整页起不来。
    """
    floor = BREAKPOINT.get(str(breakpoint).strip().lower())
    if floor is None:
        return False
    return _coerce(width) >= floor


def pick(
    width: float | int | None,
    *,
    compact: T,
    medium: T | None = None,
    expanded: T | None = None,
) -> T:
    """按当前档取值，未给出的宽档**沿窄档继承**。

    ``pick(w, compact=1, expanded=3)`` 在中等窗口上得到 1 —— 这是"渐进增强"的
    默认语义：先保证窄屏能看，再给宽屏加成，不必把三档都写满。
    """
    cls = size_class(width)
    if cls == "expanded":
        return expanded if expanded is not None else (
            medium if medium is not None else compact
        )
    if cls == "medium":
        return medium if medium is not None else compact
    return compact


def resolve(value: Any, width: float | int | None = None) -> Any:
    """把 ``int | {"compact": 1, "medium": 2, "expanded": 3}`` 解析成当前档的值。

    组件属性想支持"按断点给不同值"时，只要在构建时过一遍这个函数；字典里缺的
    档位同样沿窄档继承（``{"compact": 1, "expanded": 3}`` 在中等屏上是 1）。
    """
    if not isinstance(value, dict):
        return value
    table = {str(k).strip().lower(): v for k, v in value.items()}
    base = table.get("compact", next(iter(table.values()), None))
    return pick(
        width if width is not None else viewport().width,
        compact=base,
        medium=table.get("medium"),
        expanded=table.get("expanded"),
    )


# ---------------------------------------------------------------------------
# 状态
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Viewport:
    """窗口尺寸快照。**不可变**：换尺寸就换一个新的，避免"读一半被改掉"。"""

    width: float = _DEFAULT_WIDTH
    height: float = _DEFAULT_HEIGHT

    @property
    def size_class(self) -> str:
        return size_class(self.width)

    @property
    def columns(self) -> int:
        return COLUMNS[self.size_class]

    @property
    def is_compact(self) -> bool:
        return self.size_class == "compact"


@ft.observable
@dataclass
class ResponsiveState:
    """全局响应式状态（模块级单例，见 :func:`responsive_state`）。

    **只有一个 observable 字段**是有意的：``size_class`` 赋值即通知，所以只要保证
    "值没变就不赋值"，就不会出现拖动窗口时每像素重绘一次。精确宽度不在这里 ——
    它在 :func:`viewport` 里，更新它不触发重绘。
    """

    size_class: str = "expanded"

    # ---- 查询 ----

    @property
    def columns(self) -> int:
        """当前档的栅格列数（4 / 8 / 12）。"""
        return COLUMNS[self.size_class]

    @property
    def is_compact(self) -> bool:
        return self.size_class == "compact"

    @property
    def is_expanded(self) -> bool:
        return self.size_class == "expanded"

    def is_at_least(self, other: str) -> bool:
        """当前档是否**不窄于** ``other``（``"medium"`` / ``"expanded"``）。"""
        if other not in SIZE_CLASSES:
            return False
        return SIZE_CLASSES.index(self.size_class) >= SIZE_CLASSES.index(other)


_state = ResponsiveState()
_viewport = Viewport()

#: 已挂过 ``on_resize`` 的页面。用弱集合而不是给 Page 加属性：flet 的控件是
#: dataclass，往上塞未声明的字段是不受支持的写法，页面销毁也收不回来。
_BOUND_PAGES: "weakref.WeakSet[ft.Page]" = weakref.WeakSet()

#: 供 :func:`use_responsive` 订阅；``default_value`` 让没挂 Provider 的孤立组件
#: 也能拿到单例（与 :data:`ui.core.theme.theme_context` 同一套做法）。
responsive_context = ft.create_context(default_value=_state)


def responsive_state() -> ResponsiveState:
    """拿到全局响应式状态单例。

    组件里请用 :func:`use_responsive` —— 它会自动订阅，跨档时重绘。这个函数
    只给**非组件环境**（启动代码、纯控件 ``init()``、单测）用。
    """
    return _state


def viewport() -> Viewport:
    """当前窗口尺寸快照（不订阅、不重绘）。"""
    return _viewport


def use_responsive() -> ResponsiveState:
    """订阅全局响应式状态。**必须在组件体内调用**。

    返回的对象一跨档就换值，本组件随之重绘 —— 所以调用方可以放心地用它做
    "窄屏换成另一种布局"这类结构性判断（``if r.is_compact: ...``）。
    但**不要**用它做逐像素的算术（``width * 0.5``）：那是 Flutter 的活。
    """
    return ft.use_context(responsive_context)


# ---------------------------------------------------------------------------
# 更新
# ---------------------------------------------------------------------------
def _coerce(value: Any) -> float:
    """把任意输入变成合理的宽度值：非数字 / None / 负数都退回默认假设。

    **0 是合法宽度**（``BREAKPOINT["xs"]`` 就是 0，断点表要用它算归类），
    所以只把负数与 NaN 当成"没量到"。
    """
    try:
        number = float(value)
    except (TypeError, ValueError):
        return _DEFAULT_WIDTH
    if number != number or number < 0:  # NaN / 负数
        return _DEFAULT_WIDTH
    return number


def update(width: float | int | None, height: float | int | None = None) -> str:
    """写入新窗口尺寸，返回新档位。**跨档才会触发重绘**。

    这是整个响应式体系唯一的写入口 —— 启动时写一次，``page.on_resize`` 每次
    触发时再写一次，除此之外没有别的路径，所以"什么时候重绘"是可以静态推理的。
    """
    global _viewport
    w = _coerce(width)
    h = _coerce(height)
    _viewport = Viewport(w, h)
    cls = size_class(w)
    # 先比较再赋值：observable 的"赋值即通知"没有去重，无条件写就是每像素一帧。
    if cls != _state.size_class:
        _state.size_class = cls
    return cls


def reset() -> None:
    """复位到初始假设（测试用；正常运行时不需要）。"""
    global _viewport
    _viewport = Viewport()
    if _state.size_class != "expanded":
        _state.size_class = "expanded"


def apply_responsive(page: ft.Page) -> None:
    """把响应式状态挂到页面上：读一次初始宽度，之后跟着 ``on_resize`` 走。

    幂等：重复调用不会叠加重绘（页面记在一个弱集合里，页面销毁即自动移除）。
    若页面上已有别人写的 ``on_resize``，会被**串起来**（先更新状态，再跑原来那个），
    不会被覆盖掉。
    """
    update(page.width, page.height)
    if page in _BOUND_PAGES:
        return

    previous = page.on_resize

    def _on_resize(e: ft.PageResizeEvent) -> None:
        update(getattr(e, "width", None), getattr(e, "height", None))
        if previous is not None:
            previous(e)

    page.on_resize = _on_resize
    _BOUND_PAGES.add(page)

