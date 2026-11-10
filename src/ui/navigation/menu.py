"""菜单 (Menu) —— 侧边多级导航，支持折叠、手风琴、分组与徽标。

``Menu`` （``type`` / ``size`` / ``collapse`` /
``accordion`` / ``dot`` / ``selectedKey`` / ``expandedKeys``），

``MenuItem`` 是 ``@dataclass`` 而不是 ``ft.Control``。菜单是一棵树，不是一叠控件：
展开状态、选中链路、手风琴、缩进全都要按树算。把树交给控件图去表达，就得在渲染期
反读 ``controls`` 的私有字段，还得处理"控件只能有一个父节点"—— 一旦某行要同时出现在
折叠态和展开态，就炸。所以这里让 ``MenuItem`` 老老实实当节点，渲染时再生成控件。

用法::

    menu = Menu(
        items=[
            MenuItem("home", "概览", icon=ft.Icons.DASHBOARD_OUTLINED),
            MenuGroup("运维", [
                MenuItem(
                    "host",
                    "主机",
                    icon=ft.Icons.DNS_OUTLINED,
                    children=[
                        MenuItem("host-list", "主机列表"),
                        MenuItem("host-group", "主机分组"),
                    ],
                ),
            ]),
        ],
        selected_key="host-list",
        on_select=lambda item: print("选中", item.key),
    )
    Column([menu], expand=True)

``Menu`` 是 ``@ft.observable`` 的，改属性即重绘 —— 不必重新构造实例::

    menu.collapsed = True        # 折成图标条
    menu.selected_key = "home"   # 外部改选中

.. note::
    别在组件函数里**每次渲染都新建** ``Menu(...)``：新实例意味着展开状态、选中状态
    每次都被重置回初始值。用 ``use_stable`` 把实例钉住，或把它放到状态容器里。

设计取舍（改样式前先读）::

    1. **选中是"淡主色底 + 主色字"，不是主色实底**。侧边栏一屏有几十行，
       铺一块满饱和的色，视觉重量会压过页面正文本身。
    2. **水平菜单只画一层**。下拉浮层需要锚点的**绝对坐标**，而 Flet 只给
       ``on_size_change``（尺寸），不给位置（见 ``core/float_layer.py``）。
       与其做一个位置会飘的假浮层，不如老实只画一层。
    3. **图标比文字淡半档**。一列里八枚图标与八行文字同深度，整块会发糊。
"""

from __future__ import annotations

import math
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass, field
from typing import Any

import flet as ft

from ui.core.doc import Example, Spec, run
from ui.core.i18n import t, use_t
from ui.core.tokens import (
    DURATION,
    FONT_SIZE,
    FONT_WEIGHT,
    RADIUS,
    SPACE,
    disabled_layer,
    hairline,
    overlay,
    selected_layer,
    state_layer,
)

__all__ = [
    "ORIENTATIONS",
    "SCROLL_KEY_PREFIX",
    "SIZES",
    "Menu",
    "MenuGroup",
    "MenuItem",
    "find_path",
    "norm_selected",
    "prune_expanded",
    "row_height",
    "scroll_key",
    "toggle_expanded",
    "visible_rows",
    "walk",
]

# ---------------------------------------------------------------------------
# 尺寸：三档，数值对齐 KingDesign 的 large / default / small
# ---------------------------------------------------------------------------
SIZES: tuple[str, ...] = ("large", "default", "small")
ORIENTATIONS: tuple[str, ...] = ("vertical", "horizontal")

ROW_H: dict[str, int] = {"large": 48, "default": 40, "small": 32}
ROW_TEXT: dict[str, int] = {
    "large": FONT_SIZE["title"],  # 16  大号导航（48 行高）
    "default": FONT_SIZE["body"],  # 14  默认菜单项（40 行高）
    "small": FONT_SIZE["small"],  # 12  紧凑菜单（32 行高）
}
ROW_ICON: dict[str, int] = {"large": 20, "default": 18, "small": 16}

LEAD = SPACE["3"]  # 12  行内左右留白
ICON_GAP = SPACE["2"]  # 8   图标与文字
ROW_GAP = 2  # 行与行之间（2px 比 4px 更"整"）
CHEVRON = 16  # 展开箭头 / 右侧徽标的尺寸
CHEVRON_BOX = 24  # 箭头的旋转包围盒（16 转 180° 需要 22.6 的空间）
DOT_SIZE = 6  # 圆点直径
GROUP_TOP = SPACE["3"]  # 12  分组标题上方的空档

# ---------------------------------------------------------------------------
# 颜色：全走角色，明暗与主色自动跟随
#
# 照 Arco Menu 的分工（``item_default`` / ``bg_item_hover`` / ``bg_item_selected``
# / ``item_selected`` / ``icon_default``）落到 M3 角色上：
#
#   行文字   on_surface_variant       行图标  outline（比文字淡一档）
#   悬停     on_surface 字 + 8% 底    选中    主色字 + 12% 主色底
#
# 三个决定：
#   * **选中不铺主色实底**。侧边栏一屏几十行，满饱和的蓝会压过页面正文；
#     12% 主色只是"这块被点亮了"，重量还在正文这一侧。
#   * **祖先（选中项的父级）也用主色字，但不给底**。一层淡底 + 主色字标记
#     "你在哪"，再往上只留主色字标"你从哪来" —— 纯灰的祖先链看不出这层关系。
#   * **底一律用 overlay 叠，不用 container 阶梯**。M3 的 container 在浅色下逐级
#     变灰、暗色下逐级变亮，方向相反；overlay 两种模式都成立（Transfer 同款）。
# ---------------------------------------------------------------------------
#: 普通行文字：次要正文色（侧边栏里几十行，一律用正文色会整屏发亮）
FG = ft.Colors.ON_SURFACE_VARIANT
#: 悬停行文字：抬到正文色
FG_ACTIVE = ft.Colors.ON_SURFACE
#: 普通行图标：比文字再淡一档（Arco 的 ``icon_default = text-3``，文字是 text-2）
FG_ICON = ft.Colors.OUTLINE
#: 悬停行图标：跟进到次要正文色，但不必到正文色（图标比文字"轻"是常态）
FG_ICON_HOVER = ft.Colors.ON_SURFACE_VARIANT
#: 选中项 / 选中项祖先：主色。文字与图标同色 —— 这条链是"当前所在位置"，
#: 应当整条一起亮，而不是只亮一行。
FG_SELECTED = ft.Colors.PRIMARY
BG_SELECTED = selected_layer()
BG_HOVER = state_layer("hover")
FG_DISABLED = disabled_layer()
FG_MUTED = ft.Colors.OUTLINE  # 展开箭头 / 分组标题
#: 行状态的过渡：悬停底色硬切会"啪"地跳一下，120ms 让它是"漫过来"的
ROW_ANIM = ft.Animation(DURATION["fast"], ft.AnimationCurve.EASE_OUT)


# ---------------------------------------------------------------------------
# 数据节点
# ---------------------------------------------------------------------------
@dataclass
class MenuItem:
    """一个菜单项。既是叶子，也可以是子菜单的父节点（看 ``children``）。

    Args:
        key: 全局唯一标识。选中、展开都用它 —— 不要拿 ``text`` 当键，
            文案是会跟着语言变的。
        text: 显示文本。
        icon: 可选图标。一级项配图标最有用（折叠成图标条后，图标就是唯一信息）。
        children: 子项。非空即为"可展开"，本身**不可选中** —— 点它是展开/收起。
        disabled: 禁用。整行置灰且不响应点击（展开也一样）。
        dot: 在这一项前面加个圆点（常用来标"有新内容"）。有图标时不显示 ——
            一个位置塞两个前导符号，谁都不清楚哪个是哪个。
        badge: 右侧徽标，传 ``str`` / ``int``（如未读数）。``None`` 不显示。
        tooltip: 悬停提示，默认用 ``text``（折叠态只显示图标，提示很有用）。
        data: 挂给业务的载荷，原样不碰，回调里拿走。
    """

    key: str
    text: str
    icon: ft.IconData | None = None
    children: list[MenuItem] = field(default_factory=list)
    disabled: bool = False
    dot: bool = False
    badge: str | int | None = None
    tooltip: str = ""
    data: Any = None

    @property
    def is_leaf(self) -> bool:
        """没有子项 = 可选中。"""
        return not self.children


@dataclass
class MenuGroup:
    """一组菜单项 + 一条分组标题。

    分组**只影响视觉**：展开状态、选中逻辑照旧按整棵树算。所以把任意几项
    包进 ``MenuGroup`` 都不会改变行为，只是多一行小标题。

    Args:
        text: 标题文字。折叠态不渲染（图标条里放不下，也没有意义）。
        items: 组内菜单项。
    """

    text: str
    items: list[MenuItem] = field(default_factory=list)


# ---------------------------------------------------------------------------
# 纯函数：树的遍历与规则（单测直接断言这几个）
# ---------------------------------------------------------------------------
def walk(nodes: Sequence[MenuItem | MenuGroup]) -> Iterator[MenuItem]:
    """先序遍历所有菜单项（分组会被展开，不含标题本身）。"""
    for node in nodes:
        if isinstance(node, MenuGroup):
            yield from walk(node.items)
            continue
        yield node
        yield from walk(node.children)


def _tops(nodes: Sequence[MenuItem | MenuGroup]) -> list[MenuItem]:
    """顶层菜单项（分组拍平成它们里面的项）。"""
    out: list[MenuItem] = []
    for node in nodes:
        if isinstance(node, MenuGroup):
            out.extend(node.items)
        else:
            out.append(node)
    return out


def find_path(nodes: Sequence[MenuItem | MenuGroup], key: str) -> tuple[str, ...]:
    """从根到 ``key`` 的祖先链（**含自身**）；找不到返回空元组。

    用来判断"选中项在哪个父级下面"——要给它展开、给祖先加亮。
    """

    def dig(items: Sequence[MenuItem], trail: tuple[str, ...]) -> tuple[str, ...]:
        for item in items:
            here = (*trail, item.key)
            if item.key == key:
                return here
            got = dig(item.children, here)
            if got:
                return got
        return ()

    return dig(_tops(nodes), ())


def norm_selected(nodes: Sequence[MenuItem | MenuGroup], key: str) -> str:
    """把选中键归一到"真的是一个可选中的项"，否则返回 ``""``。

    三类要拦下来：键不存在（数据换过一轮）、指向父节点（它只负责展开）、
    以及禁用项（选中了也点不回去，高亮只会让人困惑）。
    """
    if not key:
        return ""
    for item in walk(nodes):
        if item.key == key:
            return "" if (item.disabled or not item.is_leaf) else key
    return ""


def prune_expanded(
    nodes: Sequence[MenuItem | MenuGroup], expanded: Sequence[str]
) -> tuple[str, ...]:
    """丢掉已经不存在、或已经没有子项的展开键。

    数据是外部给的，可能整棵换掉（切权限、换模块）。不清理的话展开集合会
    一直膨胀，而且下次恰好有同名键时，菜单会莫名其妙地"自己开着"。
    """
    parents = {item.key for item in walk(nodes) if item.children}
    keep = [key for key in dict.fromkeys(expanded) if key in parents]
    return tuple(keep)


def toggle_expanded(
    nodes: Sequence[MenuItem | MenuGroup],
    expanded: Sequence[str],
    key: str,
    *,
    accordion: bool = False,
) -> tuple[str, ...]:
    """点了一下 ``key``：开着的关上，关着的打开。

    ``accordion`` 打开时**同一层级只留一个** —— 注意不是"全菜单只留一个"：
    真按全局算，展开子级时父级必须留着，结果就是"子级永远只有一个开着的"，
    和用户对"手风琴"的预期（每一列同时只开一个）不符。
    """
    current = list(dict.fromkeys(expanded))
    if key in current:
        current.remove(key)
        return tuple(current)

    if accordion:
        path = find_path(nodes, key)
        siblings = _siblings(nodes, path)
        current = [k for k in current if k not in siblings]
    current.append(key)
    return tuple(current)


def _siblings(nodes: Sequence[MenuItem | MenuGroup], path: Sequence[str]) -> set[str]:
    """和 ``path`` 末项同级的、可展开的兄弟键（不含自己）。"""
    if not path:
        return set()
    parent = path[-2] if len(path) > 1 else ""
    pool = _tops(nodes)
    if parent:
        for item in walk(nodes):
            if item.key == parent:
                pool = item.children
                break
    return {item.key for item in pool if item.children and item.key != path[-1]}


def visible_rows(
    nodes: Sequence[MenuItem | MenuGroup],
    expanded: Sequence[str],
    *,
    collapsed: bool = False,
) -> tuple[tuple[MenuItem, int], ...]:
    """当前该画出来的行 ``(项, 深度)``，按显示顺序。

    ``collapsed`` 时只返回顶层 —— 折叠成图标条后没有地方放子项，硬留在树里
    只会撑出一个空行。``expanded`` 里没有的父节点，其子树整支跳过。
    """
    if collapsed:
        return tuple((item, 0) for item in _tops(nodes))

    shown = set(expanded)
    rows: list[tuple[MenuItem, int]] = []

    def dig(items: Sequence[MenuItem], depth: int) -> None:
        for item in items:
            rows.append((item, depth))
            if item.children and item.key in shown:
                dig(item.children, depth + 1)

    dig(_tops(nodes), 0)
    return tuple(rows)


def row_height(size: str) -> int:
    """档位 → 行高。非法档位退回 ``default``（不给调用方抛异常的机会）。"""
    return ROW_H.get(size, ROW_H["default"])


#: 滚动锚点的名字前缀。带上它，菜单里的 key 就不会和页面上别的
#: ``ScrollKey`` 撞名。
SCROLL_KEY_PREFIX = "menu:"


def scroll_key(key: str) -> ft.ScrollKey:
    """菜单项 → 滚动锚点的 ``key``。

    菜单通常比侧栏高（组件多的时候尤其明显），"当前页在下面第 40 行"这件事
    光看高亮是看不见的 —— 用户得先自己滚下去。调用方拿到这个 key 之后：

    .. code-block:: python

        await column.scroll_to(scroll_key=menu.scroll_key(name), duration=0)

    注意类型：Flet 1.1 的 ``Key`` 是**带类型**的，``ScrollKey`` 与普通字符串
    （隐式 ``ValueKey``）在 Flutter 侧走的是两套查找。传字符串不报错、也不滚动，
    是最难查的一种失效。
    """
    return ft.ScrollKey(f"{SCROLL_KEY_PREFIX}{key}")


# ---------------------------------------------------------------------------
# 组件
# ---------------------------------------------------------------------------
@ft.observable
@dataclass
class Menu:
    """侧边菜单。

    Args:
        items: 菜单项，元素是 :class:`MenuItem` 或 :class:`MenuGroup`。
        selected_key: 当前选中项。点击会自动更新它（半受控）—— 外部要接管就
            在 ``on_select`` 里回写自己的值。
        expanded_keys: 展开的父项键。构造后由菜单自己维护；外部想"默认展开某组"
            就传进来，后续的展开收起不会回调外部（要同步用 ``on_expand``）。
            选中项的祖先会自动算进展开集合（不写回这个字段），但用户手动收起
            过的父项除外 —— 收起的意图优先。
        collapsed: 折叠成图标条（仅 ``vertical``）。文字、子项、分组标题都不渲染。
        accordion: 手风琴 —— 同一层级同时只展开一个。
        dot: 给所有叶子项前面加圆点（单项可用 ``MenuItem.dot`` 覆盖）。
        size: ``"large"`` / ``"default"`` / ``"small"``，行高 48 / 40 / 32。
        orientation: ``"vertical"`` 侧边 / ``"horizontal"`` 顶栏（只渲一层）。
        width: 垂直菜单宽度。``None`` 跟随父容器。折叠态由调用方自己收窄容器，
            这里不擅自改 —— 宽度是布局的事，不是菜单的事。
        header: 菜单头部的任意控件（logo、标题、搜索框）。
        footer: 菜单底部（版本号、账户切换…）。
        show_collapse_arrow: 底部显示一枚折叠按钮。
        on_select: 选中叶子项时触发，入参 :class:`MenuItem`。
        on_expand: 展开集合变化时触发，入参 ``tuple[str, ...]``。
        on_collapse_change: 折叠状态变化时触发，入参 ``bool``。

    Notes:
        ``type="horizontal"`` 只画一层（原因见模块文档第 2 条）。``header`` /
        ``footer`` / ``dot`` / ``show_collapse_arrow`` 都只对垂直菜单有意义。
    """

    items: list = field(default_factory=list)
    selected_key: str = ""
    expanded_keys: tuple[str, ...] = ()
    collapsed: bool = False
    accordion: bool = False
    dot: bool = False
    size: str = "default"
    orientation: str = "vertical"
    width: int | None = 240
    header: ft.Control | None = None
    footer: ft.Control | None = None
    show_collapse_arrow: bool = False
    on_select: Callable[[MenuItem], None] | None = None
    on_expand: Callable[[tuple[str, ...]], None] | None = None
    on_collapse_change: Callable[[bool], None] | None = None

    # 悬停状态**故意不放在这里**。曾经有一个 ``_hover: str`` 字段，配
    # ``notify()`` 重绘 —— 鼠标划过一行就要重建整棵菜单（上百行控件 + 一次下发）。
    # 现在悬停挂在**每一行自己的组件**里（见 :func:`_row_view`）：状态一变只重画
    # 那一行，其余行 flet 的 diff 看到同一个控件对象直接跳过。

    # ------------------------------------------------------------------
    # 对外的小动作
    # ------------------------------------------------------------------
    def __post_init__(self) -> None:
        # 运行期状态：用户**明确收起**过的父项（哪怕里面装着当前选中项）。
        #
        # 为什么非要有这一笔账：选中项的祖先链是自动展开的（见
        # ``_effective_expanded``），只看展开集合的话，用户点父项收起后，
        # 下一条规则立刻又把它顶开 —— 表现就是**装着当前页的那一组收不起来**。
        # 这里让"用户的手"压过"自动展开"；换选中项、或再次点开时销账。
        # 下划线开头 => 不参与序列化（像 ``_picked`` / ``_hover`` 一样），
        # 变更后靠 ``_repaint`` 触发重绘。
        self._suppressed: set[str] = set()

    def select(self, key: str) -> None:
        """选中某一项（不触发 ``on_select``，供外部同步用）。"""
        self._set_selected(norm_selected(self.items, key))

    def expand(self, *keys: str) -> None:
        """强制展开这些父项（``on_expand`` 照常触发）。"""
        merged = prune_expanded(self.items, (*self.expanded_keys, *keys))
        # 明确展开 = 销账：用户改主意了，别再替他记着"这组他收起过"。
        keep = {k for k in self._suppressed if k not in merged}
        dropped = keep != self._suppressed
        self._suppressed = keep
        if merged == self.expanded_keys:
            if dropped:
                self._repaint()
            return
        self.expanded_keys = merged
        if self.on_expand:
            self.on_expand(merged)

    def toggle(self, key: str) -> None:
        """展开 / 收起某个父项。

        收起是**用户的明确意图**，要压过"选中项的祖先自动露出来"这条便利规则
        —— 否则装着当前页的那一组永远收不起来。这一笔账记在 ``_suppressed``：只有
        当收起的正是选中项的祖先时才记（别处的收起本来就没人跟它抢）。
        之后再点开、``expand()``、或者跳到别的项，账自动销掉。
        """
        item = self._item_of(key)
        if item is None or item.disabled or not item.children:
            return  # 禁用的父项、叶子、或键根本不存在
        trail = find_path(self.items, self.selected_key)
        if key in self._effective_expanded(trail):
            # 收起：确认它真的从展开集合里去掉，并（若它是选中项的祖先）记账
            merged = tuple(k for k in dict.fromkeys(self.expanded_keys) if k != key)
            keep = set(self._suppressed)
            if key in trail[:-1]:
                keep.add(key)
        else:
            merged = toggle_expanded(
                self.items, self.expanded_keys, key, accordion=self.accordion
            )
            keep = {k for k in self._suppressed if k != key}
        if merged == self.expanded_keys and keep == self._suppressed:
            return
        self._suppressed = keep
        if merged == self.expanded_keys:
            # expanded_keys 一个字没变，只是记了一笔账 —— 得自己敲一下重绘
            self._repaint()
        else:
            self.expanded_keys = merged
        if self.on_expand:
            self.on_expand(merged)

    def set_collapsed(self, value: bool) -> None:
        """折叠 / 展开整条菜单。"""
        if value == self.collapsed:
            return
        self.collapsed = value
        if self.on_collapse_change:
            self.on_collapse_change(value)

    # ------------------------------------------------------------------
    # 内部：归一与查找
    # ------------------------------------------------------------------
    def _repaint(self) -> None:
        """请求重绘。

        名字**不能**叫 ``_notify``：``@ft.observable`` 自己注入了 ``_notify(name)``，
        覆盖了会在构造期直接 ``TypeError``。
        """
        notify = getattr(self, "notify", None)
        if callable(notify):
            notify()

    def _effective_expanded(self, path: Sequence[str] | None = None) -> tuple[str, ...]:
        """真正生效的展开集合：``expanded_keys`` + 选中项的祖先链。

        祖先链必须露出来，否则"我在哪"无从看起；但**只在用户没有明确收起它
        的时候** —— 用户点一下父项，意图比"自动露出"更强，那笔账记在
        ``_suppressed`` 里（见 ``__post_init__``）。这层"自动展开"仍然只算、
        不写回 ``expanded_keys``：写回去就把用户的收起意图抹平了。

        Args:
            path: 已知的选中链路（``find_path`` 的结果）。一次渲染里这个链路要被
                用两回（算展开集合、标祖先高亮），传进来就不用重复遍历整棵树。
        """
        expanded = prune_expanded(self.items, self.expanded_keys)
        trail = path if path is not None else find_path(self.items, self.selected_key)
        if not trail:
            return expanded
        auto = [key for key in trail[:-1] if key not in self._suppressed]
        return tuple(dict.fromkeys((*expanded, *auto)))

    def _set_selected(self, key: str) -> None:
        """换选中项，并让新链路上的"用户收起过"作废。

        不作废的后果很具体：用户收起过「主机」，之后从别处跳到「主机 › 主机列表」，
        那一组还收着 —— 菜单上完全看不出自己身在何处，只有个亮着的父项。
        """
        if self._suppressed:
            trail = set(find_path(self.items, key)[:-1])
            keep = {k for k in self._suppressed if k not in trail}
            if keep != self._suppressed:
                # 不在这里 _repaint：紧接着的 selected_key 赋值本来就要重绘一次
                self._suppressed = keep
        self.selected_key = key

    def _group_starts(self) -> dict[str, MenuGroup]:
        """ "分组标题挂在哪一行之前"：组内第一项的键 → 分组。一次 O(项数)。

        曾经是每画一行就回扫一遍顶层 ``items``（``_group_before``），
        行数 × 顶层项数 —— 120 行的菜单要跑一万多次比较，光这一项就占渲染时间
        的 16%。分组标题只可能出现在**组内第一项**之前，所以一张
        ``第一项键 → 分组`` 的表就够，查一次是 dict.get。
        """
        starts: dict[str, MenuGroup] = {}
        for node in self.items:
            if isinstance(node, MenuGroup) and node.items:
                starts.setdefault(node.items[0].key, node)
        return starts

    def _item_of(self, key: str) -> MenuItem | None:
        for item in walk(self.items):
            if item.key == key:
                return item
        return None

    # ------------------------------------------------------------------
    # 事件
    # ------------------------------------------------------------------
    def _click(self, e: ft.ControlEvent) -> None:
        """整行的点击：叶子选中、父项展开。

        ``data`` 里放的是键而不是项本身 —— 控件图里塞自定义对象在 Flet 的
        序列化边界上迟早出事，键是安全的。
        """
        item = self._item_of(str(e.control.data))
        if item is None or item.disabled:
            return
        if item.children:
            # 折叠态点父项：先摊开菜单再展开这一组。用户点进去就是要看内容，
            # 此时弹一个需要浮层的二级面板，代价远大于收益（见模块文档第 2 条）。
            if self.collapsed:
                self.set_collapsed(False)
            self.toggle(item.key)
            return
        if item.key == self.selected_key:
            return  # 再点一次同一个不算"换了"
        self._set_selected(item.key)
        if self.on_select:
            self.on_select(item)

    # ------------------------------------------------------------------
    # 渲染
    # ------------------------------------------------------------------
    @ft.component
    def ui(self) -> ft.Control:
        """构建菜单。"""
        use_t()  # 折叠按钮的 tooltip 跟着语言切
        if self.orientation == "horizontal":
            return self._horizontal()
        return self._vertical()

    # -- 垂直 ----------------------------------------------------------
    def _vertical(self) -> ft.Control:
        # 选中链路一次算清：既要拿它补展开集合，又要标祖先高亮。
        path = find_path(self.items, self.selected_key)
        expanded = self._effective_expanded(path)
        rows = visible_rows(self.items, expanded, collapsed=self.collapsed)
        ancestors = set(path[:-1])
        # 分组标题的挂载点一次算清（原先每行回扫一遍顶层，行数 × 项数）
        group_starts = {} if self.collapsed else self._group_starts()
        body: list[ft.Control] = []

        if self.header is not None and not self.collapsed:
            body.append(
                ft.Container(
                    content=self.header, padding=ft.Padding.only(bottom=SPACE["2"])
                )
            )

        for item, depth in rows:
            group = group_starts.get(item.key)
            if group is not None:
                body.append(self._group_title(group))
            body.append(
                _row_view(
                    self,
                    item,
                    depth,
                    selected=item.key == self.selected_key,
                    in_path=item.key in ancestors,
                    expanded=item.key in expanded,
                    key=item.key,
                )
            )

        if self.footer is not None and not self.collapsed:
            body.append(
                ft.Container(
                    content=self.footer, padding=ft.Padding.only(top=SPACE["2"])
                )
            )
        if self.show_collapse_arrow:
            body.append(self._collapse_arrow())

        return ft.Container(
            width=None if self.collapsed else self.width,
            content=ft.Column(
                spacing=ROW_GAP,
                tight=True,
                # 折叠态的行是方块，得居中；展开态的行要撑满，靠 ``Text(expand=True)``
                # 把 ``Row`` 顶到列宽，所以这里给 START 就够。
                horizontal_alignment=(
                    ft.CrossAxisAlignment.CENTER
                    if self.collapsed
                    else ft.CrossAxisAlignment.START
                ),
                controls=body,
            ),
        )

    def _group_title(self, group: MenuGroup) -> ft.Control:
        """分组标题：小一号、更淡，只做视觉切分。"""
        return ft.Container(
            padding=ft.Padding.only(
                left=LEAD, top=GROUP_TOP, bottom=SPACE["1"], right=LEAD
            ),
            content=ft.Text(
                group.text,
                size=FONT_SIZE["small"],
                color=FG_MUTED,
                weight=FONT_WEIGHT["medium"],
                no_wrap=True,
                overflow=ft.TextOverflow.ELLIPSIS,
            ),
        )

    # -- 水平 ----------------------------------------------------------
    def _horizontal(self) -> ft.Control:
        """顶栏：只画一层。子项在这里不展开（原因见模块文档第 2 条）。"""
        # 顶栏只画一层，可当前选中项很可能是某个一级项的子项 —— 那就把它的
        # **一级祖先**点亮。否则用户在"主机列表"页上，顶栏一片灰，等于没导航。
        ancestors = set(find_path(self.items, self.selected_key)[:-1])
        tabs = [
            _tab_view(
                self, item, item.key == self.selected_key or item.key in ancestors
            )
            for item in _tops(self.items)
        ]
        return ft.Row(spacing=0, tight=True, controls=tabs)

    def _tab(self, item: MenuItem, selected: bool, hovered: bool) -> ft.Control:
        """顶栏的一项。悬停只换字色 —— 顶栏不铺底色（见下）。"""
        size = self._size_key
        icon = (
            ft.Icon(
                item.icon,
                size=ROW_ICON[size],
                color=self._icon_fg(item, selected, False, hovered),
            )
            if item.icon
            else None
        )
        return ft.Container(
            height=row_height(size),
            padding=ft.Padding.symmetric(horizontal=SPACE["4"]),
            alignment=ft.Alignment.CENTER,
            # 选中靠底部 3px 与主色字，不铺底色 —— 顶栏是页面的一部分，
            # 铺一块色会把它切成"卡片里的导航"，反而更碎（Arco 的水平
            # 菜单同理：只有一条 label，没有块）。未选中也留同宽的透明边，
            # 换选中时文字不上下跳。
            border=ft.Border.only(
                bottom=ft.BorderSide(
                    3,
                    ft.Colors.PRIMARY if selected else ft.Colors.TRANSPARENT,
                )
            ),
            content=ft.Row(
                spacing=ICON_GAP,
                tight=True,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    *([icon] if icon else []),
                    ft.Text(
                        item.text,
                        size=ROW_TEXT[size],
                        color=self._fg(item, selected, False, hovered),
                        weight=FONT_WEIGHT["medium"] if selected else None,
                        no_wrap=True,
                    ),
                    *(
                        [self._badge(item, lit=selected)]
                        if item.badge is not None
                        else []
                    ),
                ],
            ),
            data=item.key,
            on_click=None if item.disabled else self._click,
        )

    # -- 单行 ----------------------------------------------------------
    def _row(
        self,
        item: MenuItem,
        depth: int,
        *,
        selected: bool,
        in_path: bool,
        expanded: bool,
        hovered: bool = False,
        on_hover: Callable | None = None,
    ) -> ft.Container:
        """一行菜单项。折叠态只剩图标。

        ``hovered`` / ``on_hover`` 由 :func:`_row_view` 提供 —— 悬停状态挂在**每一行
        自己的组件**里，划过一行只有那一行重绘（见该函数的说明）。
        """
        size = self._size_key
        hint = item.tooltip or item.text
        hover_handler = None if (item.disabled or on_hover is None) else on_hover

        if self.collapsed:
            # 折叠后只剩图标，选中项的**父级**也必须亮起来：选中项本身藏在
            # 子菜单里看不见，整条图标栏里不给任何标记，用户就找不到自己在哪。
            lit = selected or in_path
            return ft.Container(
                width=row_height(size),
                height=row_height(size),
                alignment=ft.Alignment.CENTER,
                border_radius=RADIUS["lg"],
                bgcolor=BG_SELECTED if lit else (BG_HOVER if hovered else None),
                animate=ROW_ANIM,
                content=ft.Icon(
                    item.icon or ft.Icons.CIRCLE_OUTLINED,
                    size=ROW_ICON[size],
                    color=FG_SELECTED
                    if lit
                    else self._icon_fg(item, False, False, hovered),
                ),
                tooltip=hint,
                data=item.key,
                on_click=None if item.disabled else self._click,
                on_hover=hover_handler,
            )

        leading: list[ft.Control] = []
        # 圆点**悬挂**在左侧留白里：它的宽度从内边距里扣掉，文字 x 不变。
        # 不扣的话，同一层里"带圆点"与"不带圆点"的两项文字会差 14px（文档页里
        # 一眼就能看出歪），而扣掉之后圆点正好落在缩进的空当里，像条目标记。
        pad_left = LEAD + depth * self._indent
        if self._show_dot(item):
            leading.append(self._dot())
            pad_left = max(0, pad_left - DOT_SIZE - ICON_GAP)
        if item.icon is not None:
            leading.append(
                ft.Icon(
                    item.icon,
                    size=ROW_ICON[size],
                    color=self._icon_fg(item, selected, in_path, hovered),
                )
            )

        trailing: list[ft.Control] = []
        if item.badge is not None:
            trailing.append(self._badge(item, lit=selected))
        if item.children:
            trailing.append(
                ft.Container(
                    width=CHEVRON_BOX,
                    height=CHEVRON_BOX,
                    alignment=ft.Alignment.CENTER,
                    # 盒子要比图标大一圈，而且不裁剪：16px 的方盒转 180°，
                    # 对角线 22.6 会顶出边界 —— Flet 的 Container 默认 HARD_EDGE，
                    # 转出来就只剩一个"L"（真机第一版就是这样，看着像箭头坏了）。
                    #
                    # ``rotate`` 的单位是**弧度**不是圈（``LayoutControl`` 的文档：
                    # 一整圈 ``math.pi * 2``），写 ``0.5`` 得到的是 28.6° 的歪箭头。
                    # 旋转是**属性变化**，吃得到隐式动画；子项高度没法补间
                    # （Flutter 不知道"内容高度"是多少），所以展开本身是瞬时的，
                    # 靠这枚箭头把"发生了什么"交代清楚。
                    clip_behavior=ft.ClipBehavior.NONE,
                    rotate=math.pi if expanded else 0,
                    animate_rotation=ft.Animation(
                        DURATION["fast"], ft.AnimationCurve.EASE_OUT
                    ),
                    content=ft.Icon(ft.Icons.EXPAND_MORE, size=CHEVRON, color=FG_MUTED),
                )
            )

        label = ft.Text(
            item.text,
            size=ROW_TEXT[size],
            color=self._fg(item, selected, in_path, hovered),
            weight=FONT_WEIGHT["medium"]
            if (selected or in_path or item.children)
            else None,
            no_wrap=True,
            overflow=ft.TextOverflow.ELLIPSIS,
            expand=True,
        )

        return ft.Container(
            height=row_height(size),
            padding=ft.Padding.only(left=pad_left, right=LEAD),
            border_radius=RADIUS["lg"],
            bgcolor=BG_SELECTED if selected else (BG_HOVER if hovered else None),
            animate=ROW_ANIM,
            tooltip=hint,
            data=item.key,
            # 只给**选中那一行**挂滚动锚点：菜单比可视区高时，外层可以用
            # ``Column.scroll_to(scroll_key=menu.scroll_key(...))`` 把"我在哪"
            # 滚进视野。只标一行，同页出现多个菜单也不会互相抢。
            # 必须是 ``ft.ScrollKey`` 而不是普通字符串 —— Key 在 Flet 1.1 里带类型，
            # 字符串会被当成普通 ValueKey，``scroll_to`` 收到后不报错、也不滚动。
            key=scroll_key(item.key) if selected else None,
            on_click=None if item.disabled else self._click,
            on_hover=hover_handler,
            content=ft.Row(
                spacing=ICON_GAP,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[*leading, label, *trailing],
            ),
        )

    @property
    def _size_key(self) -> str:
        """归一的尺寸键（非法值退回 ``default``）。"""
        return self.size if self.size in ROW_H else "default"

    @property
    def _indent(self) -> int:
        """每一级的缩进 = 图标宽 + 图标与文字的间距。

        这样 ``depth=1`` 的文字起点正好压在父项文字的起点上：子项没有图标，
        那截空白本身就是层级的线索。再额外加一档缩进，父子两行反而会"错位"
        —— 真机第一版就是这么歪的（子项比父项还靠左 10px）。
        """
        return ROW_ICON[self._size_key] + ICON_GAP

    def _fg(self, item: MenuItem, selected: bool, in_path: bool, hovered: bool) -> str:
        """一行**文字**的颜色。优先级：禁用 > 选中 / 祖先 > 悬停 > 普通。

        选中项与它的祖先链同为**主色** —— 底只有一块（给选中项），颜色标记整条
        "当前位置 → 来源"的关系。祖先用正文黑的话，这条关系就只能靠"比别的行深
        一点"去猜，隔着几个分组根本看不出来。
        """
        if item.disabled:
            return FG_DISABLED
        if selected or in_path:
            return FG_SELECTED
        return FG_ACTIVE if hovered else FG

    def _icon_fg(
        self, item: MenuItem, selected: bool, in_path: bool, hovered: bool
    ) -> str:
        """一行**图标**的颜色：比文字淡半档，选中时跟文字一起转主色。"""
        if item.disabled:
            return FG_DISABLED
        if selected or in_path:
            return FG_SELECTED
        return FG_ICON_HOVER if hovered else FG_ICON

    def _show_dot(self, item: MenuItem) -> bool:
        """圆点只在"叶子 + 没有图标"时出现，避免一个位置两个前导符号。"""
        return bool((item.dot or self.dot) and item.is_leaf and item.icon is None)

    def _dot(self) -> ft.Control:
        """小圆点：始终主色 —— 它在选中行上落在 12% 主色底里，主色依然读得出来，
        换成反相色反而会变成一块"比周围更暗"的杂点。"""
        return ft.Container(
            width=DOT_SIZE,
            height=DOT_SIZE,
            border_radius=RADIUS["full"],
            bgcolor=FG_SELECTED,
        )

    def _badge(self, item: MenuItem, *, lit: bool = False) -> ft.Control:
        """右侧计数：中性淡底胶囊。

        原先用主色实底，结果一列菜单里全屏最重的一块是这个"12"—— 比选中行还重，
        视线会被它拽走。改成中性淡底后它只提供信息、不参与层级竞争；行被选中时
        转成淡主色底，免得压在淡蓝底上糊掉。
        """
        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=SPACE["1"] + 2, vertical=1),
            border_radius=RADIUS["full"],
            bgcolor=overlay(0.16, role=ft.Colors.PRIMARY) if lit else overlay(0.08),
            content=ft.Text(
                str(item.badge),
                size=FONT_SIZE["caption"],
                color=FG_SELECTED if lit else FG,
                weight=FONT_WEIGHT["medium"],
                no_wrap=True,
            ),
        )

    def _collapse_arrow(self) -> ft.Control:
        """底部折叠按钮：一条与菜单行同高、同圆角、**左对齐**的操作行。

        三处讲究：

        * 自绘而不是 ``IconButton`` —— Material 会塞进 48 的最小尺寸和一圈内边距，
          菜单底部就多出一块对不齐的空白。
        * 左对齐而不是居中：居中会变成一个孤零零的"页脚"，和上面一列左对齐的行
          没有共同的基准线；左对齐后箭头正好压在图标那一列上，读起来是"菜单的
          最后一行"，而不是"另一个东西"。
        * 上方一条细线：线以下是**控件**不是导航 —— 点它不切页面，只收起菜单。
          没有这条线，它和禁用行的视觉差别几乎为零。
        """
        closed = self.collapsed
        button = ft.Container(
            # 与菜单行同高 —— 它是"菜单的最后一行"，不该自带另一套尺寸。
            height=row_height(self._size_key),
            # ``alignment`` 不只是对齐：设了它，Container 才会撑满可用宽度（Flutter
            # 的 ``Align`` 无 widthFactor 时吃满约束）。没有它，这一行会缩成内容的
            # 宽度，左对齐就退化成"整块居中"。
            alignment=ft.Alignment.CENTER if closed else ft.Alignment.CENTER_LEFT,
            padding=(
                ft.Padding.symmetric(horizontal=SPACE["1"])
                if closed
                else ft.Padding.symmetric(horizontal=LEAD)
            ),
            border_radius=RADIUS["lg"],
            ink=True,
            tooltip=t("ui.menu.expand") if closed else t("ui.menu.collapse"),
            on_click=lambda _e: self.set_collapsed(not closed),
            content=ft.Row(
                spacing=ICON_GAP,
                tight=True,
                alignment=(
                    ft.MainAxisAlignment.CENTER
                    if closed
                    else ft.MainAxisAlignment.START
                ),
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(
                        ft.Icons.CHEVRON_RIGHT if closed else ft.Icons.CHEVRON_LEFT,
                        size=CHEVRON,
                        color=FG_MUTED,
                    ),
                    *(
                        []
                        if closed
                        else [
                            ft.Text(
                                t("ui.menu.collapse"),
                                size=FONT_SIZE["small"],
                                color=FG_MUTED,
                            )
                        ]
                    ),
                ],
            ),
        )
        return ft.Container(
            margin=ft.Margin.only(top=SPACE["2"]),
            padding=ft.Padding.only(top=SPACE["2"]),
            border=ft.Border.only(top=hairline()),
            content=button,
        )


# ---------------------------------------------------------------------------
# 每行一个组件：把"悬停"关在一行之内
# ---------------------------------------------------------------------------
@ft.component
def _row_view(
    menu: Menu,
    item: MenuItem,
    depth: int,
    *,
    selected: bool,
    in_path: bool,
    expanded: bool,
) -> ft.Control:
    """菜单行 = 一个独立组件，悬停状态挂在它自己身上。

    这是"悬停不要重绘整棵菜单"的唯一干净做法。flet 1.1 里组件重绘的粒度是
    **组件**：状态放在 ``Menu`` 上，改一次就要重建上百行；拆到行上，hover 只让
    **这一行**重绘（实测 ``_row`` 的调用次数从 94 次降到 1 次）。

    为什么不用"就地改颜色 + update()"这条更省的路
    ------------------------------------------------
    已挂载的控件在 flet 1.1 里是**冻结**的（``_frozen``），改属性或调 ``update()``
    都会抛 ``Frozen controls cannot be updated``。冻结是框架刻意的设计：渲染后的
    控件树不可变，改 UI 的正确入口是重绘组件。硬解冻等于和框架对着干，跨版本
    必然出问题 —— 所以这里走"缩小重绘范围"，而不是"绕过冻结"。
    """
    hovered, set_hovered = ft.use_state(False)

    def on_hover(e: ft.ControlEvent) -> None:
        on = str(e.data).strip().lower() == "true"
        if on != hovered:
            set_hovered(on)

    return menu._row(
        item,
        depth,
        selected=selected,
        in_path=in_path,
        expanded=expanded,
        hovered=hovered,
        on_hover=on_hover,
    )


@ft.component
def _tab_view(menu: Menu, item: MenuItem, selected: bool) -> ft.Control:
    """顶栏一项，同上：悬停只影响这一项。"""
    hovered, set_hovered = ft.use_state(False)

    def on_hover(e: ft.ControlEvent) -> None:
        on = str(e.data).strip().lower() == "true"
        if on != hovered:
            set_hovered(on)

    tab = menu._tab(item, selected, hovered and not selected)
    if not item.disabled:
        tab.on_hover = on_hover
    return tab


# ---------------------------------------------------------------------------
# 独立运行
# ---------------------------------------------------------------------------
@ft.component
def App():
    """Menu 组件运行示例。"""
    # 实例必须跨渲染稳定：每次重建都会把展开 / 选中状态打回初始值。
    # （``flet`` 没有 ``use_stable``，用 ``use_ref`` 兜住即可。）
    holder = ft.use_ref(None)
    if holder.current is None:
        holder.current = Menu(
            items=[
                MenuItem("home", "概览", icon=ft.Icons.DASHBOARD_OUTLINED),
                MenuItem("monitor", "监控", icon=ft.Icons.MONITOR_HEART_OUTLINED),
                MenuGroup(
                    "运维",
                    [
                        MenuItem(
                            "host",
                            "主机",
                            icon=ft.Icons.DNS_OUTLINED,
                            children=[
                                MenuItem("host-list", "主机列表", dot=True),
                                MenuItem("host-group", "主机分组"),
                                MenuItem("host-tag", "标签管理", badge="12"),
                            ],
                        ),
                        MenuItem(
                            "network",
                            "网络",
                            icon=ft.Icons.LAN_OUTLINED,
                            children=[
                                MenuItem("vpc", "私有网络"),
                                MenuItem("eip", "弹性 IP"),
                            ],
                        ),
                    ],
                ),
                MenuItem(
                    "archive",
                    "归档",
                    icon=ft.Icons.INVENTORY_2_OUTLINED,
                    children=[MenuItem("archive-cold", "冷归档")],
                ),
                MenuItem("setting", "设置", icon=ft.Icons.SETTINGS_OUTLINED),
                MenuItem(
                    "audit",
                    "审计日志",
                    icon=ft.Icons.RECEIPT_LONG_OUTLINED,
                    disabled=True,
                ),
            ],
            selected_key="host-list",
            expanded_keys=("host",),
            show_collapse_arrow=True,
            on_select=lambda item: print("select", item.key),
            on_expand=lambda keys: print("expand", keys),
            on_collapse_change=lambda v: print("collapsed", v),
        )
    return ft.Container(
        padding=24,
        bgcolor=ft.Colors.SURFACE,
        content=ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[holder.current.ui()],
        ),
    )


def _tree() -> list:
    """演示用的菜单树：三种形态（叶子 / 可展开 / 分组）各来一份。"""
    return [
        MenuItem("home", "概览", icon=ft.Icons.DASHBOARD_OUTLINED),
        MenuItem("monitor", "监控", icon=ft.Icons.MONITOR_HEART_OUTLINED),
        MenuGroup(
            "运维",
            [
                MenuItem(
                    "host",
                    "主机",
                    icon=ft.Icons.DNS_OUTLINED,
                    children=[
                        MenuItem("host-list", "主机列表", dot=True),
                        MenuItem("host-group", "主机分组"),
                        MenuItem("host-tag", "标签管理", badge="12"),
                    ],
                ),
                MenuItem(
                    "network",
                    "网络",
                    icon=ft.Icons.LAN_OUTLINED,
                    children=[MenuItem("vpc", "私有网络"), MenuItem("eip", "弹性 IP")],
                ),
            ],
        ),
        MenuItem("setting", "设置", icon=ft.Icons.SETTINGS_OUTLINED),
    ]


@ft.component
def _collapsed() -> ft.Control:
    """折叠成图标条：只剩图标，选中项的**父级**也会亮起来。"""
    menu = ft.use_memo(
        lambda: Menu(items=_tree(), collapsed=True, selected_key="host-list"), []
    )
    return ft.Container(
        width=56,
        padding=6,
        bgcolor=ft.Colors.SURFACE,
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        border_radius=RADIUS["lg"],
        content=menu.ui(),
    )


@ft.component
def _horizontal() -> ft.Control:
    """顶栏水平菜单：只画一层，选中项靠底部 3px 主色线与主色字。"""
    menu = ft.use_memo(
        lambda: Menu(items=_tree(), orientation="horizontal", selected_key="host-list"),
        [],
    )
    return ft.Container(
        bgcolor=ft.Colors.SURFACE,
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        border_radius=RADIUS["lg"],
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        content=menu.ui(),
    )


_MENU_CODE = """menu = Menu(
    items=[
        MenuItem("home", "概览", icon=ft.Icons.DASHBOARD_OUTLINED),
        MenuGroup("运维", [
            MenuItem("host", "主机", icon=ft.Icons.DNS_OUTLINED, children=[
                MenuItem("host-list", "主机列表", dot=True),
                MenuItem("host-tag", "标签管理", badge="12"),
            ]),
        ]),
    ],
    selected_key="host-list",      # 选中项（半受控：点击会自己改）
    expanded_keys=("host",),       # 默认展开哪几组
    on_select=lambda item: ...,     # 叶子项被点中
)"""

SPEC = Spec(
    name="Menu",
    summary="侧边多级导航：分组、展开、选中链路、折叠成图标条。",
    definition=(
        "菜单是一棵树，不是一叠控件 —— 展开状态、选中链路、手风琴、缩进都要按树"
        "算。所以 MenuItem 是数据节点（dataclass），渲染时才生成控件；这样同一行"
        "可以同时出现在展开态与折叠态，不必和「控件只能有一个父节点」较劲。"
    ),
    anatomy=[
        (
            "行",
            "32 / 40 / 48 三档（small / default / large），图标 + 文字 + 可选徽标。",
        ),
        (
            "选中链路",
            "选中项 12% 主色底 + 主色字；它的祖先只转主色、不铺底 —— "
            "一层标「你在哪」，另一层标「你从哪来」。",
        ),
        ("展开箭头", "16px 的箭头转 180°，120ms 缓出；旋转是属性动画，能吃补间。"),
        ("圆点 / 徽标", "圆点标「有新内容」，徽标是计数。两个前导符号不会同时出现。"),
        ("折叠行", "底部一枚左对齐的折叠按钮，与行同高，上方一条发丝线。"),
        ("分组标题", "更小更淡的一行字，只做视觉切分，不参与展开与选中逻辑。"),
    ],
    when=[
        "应用的常驻侧边导航（一屏几十行）",
        "层级固定、需要快速在模块间切换",
        "需要折叠成图标条让出内容宽度",
    ],
    avoid=[
        "只有 3~5 个入口且不会再长：一排 Tab 更直接",
        "操作型菜单（右键、下拉动作）：用 PopupMenu，不要用导航菜单",
    ],
    examples=[
        Example("完整示例", App, hint="分组、子菜单、圆点、徽标、禁用项、折叠按钮。"),
        Example(
            "折叠态", _collapsed, hint="只剩图标；选中项藏在子级里时，父级图标也会亮。"
        ),
        Example("水平菜单", _horizontal, hint="顶栏形态只画一层，选中靠底部主色线。"),
    ],
    target=Menu,
    notes=[
        (
            "warn",
            "别在组件函数里每次重绘都 new 一个 Menu：新实例意味着展开状态与选中"
            "状态被打回初始值。用 use_memo / use_ref 把它钉住。",
        ),
        (
            "tip",
            "选中用 12% 主色底而不是主色实底：一屏几十行，满饱和的色会压过页面正文。"
            "图标比文字淡一档（outline），否则一列图标与文字同深度会发糊。",
        ),
        (
            "info",
            "选中项的祖先会自动展开，但**用户点一下就收得起来** —— 收起的意图优先，"
            "直到再点开、expand() 或跳到别的项。子项被收起后不画，父项仍留着主色，"
            "「你在哪条链上」不会丢。",
        ),
        (
            "info",
            "水平菜单只画一层：下拉浮层需要锚点的绝对坐标，而 Flet 只给尺寸、"
            "不给位置。与其做一个位置会飘的假浮层，不如老实只画一层。",
        ),
    ],
    tags=("菜单", "侧边栏", "导航树", "menu", "sidenav"),
)


if __name__ == "__main__":
    run(SPEC)
