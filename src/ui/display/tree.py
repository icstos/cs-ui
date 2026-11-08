"""树形控件 (Tree)。

交互与视觉参考 Element Plus 的 ``el-tree``：层级展示、展开折叠、复选联动、
当前选中、关键字过滤。四条实现取舍（改前先读）：

1. **扁平化渲染**。Flet 的每个控件都要序列化后过桥，递归建控件树意味着
   "展开一个叶子"也得重建整棵树，节点一多首帧就卡。这里先把树拍平成
   "当前可见的行"，再交给 :class:`flet.ListView` —— 它在
   ``build_controls_on_demand`` 下滚动才真正生成行控件。
2. **状态只有四个集合**：``expanded`` / ``checked`` / ``current`` / ``query``。
   **半选态不存**，由子节点状态反推（:meth:`Tree._refresh_states`），所以
   ``set_checked_keys`` 之后不会出现"父选中但子未选"的自相矛盾。
3. **一次点击只做一件事**：整行 = 选中（可附带展开）、箭头 = 只展开、
   复选框 = 只勾选。三者是各自独立的 ``GestureDetector`` —— 同类型手势的
   嵌套识别器按"内层优先"决出胜负，不会一次点击触发两件事。
4. **不做键盘导航**。Flet 1.0 的 ``KeyboardListener`` 在组件重绘后会把焦点
   交给兄弟节点（真机实测：按一次 ↓ 之后按键就跑到下一棵树上了），没有稳定的
   控件级按键钩子。与其给一个"按两下就失灵"的能力，不如不给。

用法::

    tree = Tree(
        data=[
            TreeNode("src", children=[
                TreeNode("main.py"),
                TreeNode("ui", children=[TreeNode("tree.py")]),
            ]),
            {"label": "README.md"},
        ],
        show_checkbox=True,
        on_node_click=lambda node: print(node.label),
    )
    ...
    Column([tree.ui()])

``data`` 里既可以放 :class:`TreeNode`，也可以直接放 ``dict``（认 ``label`` /
``title`` / ``name``、``children``、``id`` / ``key`` 这几组常用字段），
标量会被当成纯文本叶子。
"""

from __future__ import annotations

import enum
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from functools import partial
from typing import Any

import flet as ft

from ui.core.doc import Api, Example, Spec, info, run, tip
from ui.core.i18n import t, use_t
from ui.core.tokens import FONT_SIZE, RADIUS, overlay

__all__ = ["Tree", "TreeNode"]

#: 节点 key 的类型：字符串或整数（与 Element 的 ``node-key`` 对齐）
Key = str | int

# ---- 尺寸 -----------------------------------------------------------------
ROW_HEIGHT = 32  # 行高：桌面端列表的常规密度
INDENT = 18  # 每一级的缩进增量
ARROW_BOX = 18  # 展开箭头的点击区
CHECK_BOX = 16  # 复选框方框边长
CHECK_HIT = 22  # 复选框的可点区域（比方框大一圈，桌面鼠标才好点）
TEXT_SIZE = FONT_SIZE["body"]
TRAILING_SIZE = FONT_SIZE["caption"]
EMPTY_HEIGHT = 72

# ---- 配色（全部走主题角色，明暗自动跟随）-----------------------------------
SELECTED_BG = ft.Colors.with_opacity(0.12, ft.Colors.PRIMARY)
HOVER_BG = overlay(0.06)
GUIDE_COLOR = ft.Colors.OUTLINE_VARIANT

# 复选框未选中态的边框只有"常态 / 禁用"两种。逐行新建 ``ft.Border`` + ``with_opacity``
# 实测约 10µs，可勾选的树几百行就要白扔几毫秒 —— 缓存成两个值。
# 值是令牌串（``"outline"`` / ``"outline,0.4"``），由 Flutter 按当前主题解析，
# 所以提前建好不会把配色固定在浅色主题上。
_CHECK_BORDER = ft.Border.all(1.5, ft.Colors.OUTLINE)
_CHECK_BORDER_OFF = ft.Border.all(1.5, ft.Colors.with_opacity(0.4, ft.Colors.OUTLINE))
_CHECK_RADIUS = ft.BorderRadius.all(3)  # 同上：三种状态共用一个圆角值
_HALF_BAR_RADIUS = ft.BorderRadius.all(1)  # 半选短横的圆角，同上
_CHECK_MARGIN = ft.Margin.only(right=2)  # 复选框与标签之间的固定间距


class _Check(enum.Enum):
    """复选框三态。只用于渲染，不作为持久状态（半选由子节点反推）。"""

    UNCHECKED = 0
    HALF = 1
    CHECKED = 2


@dataclass
class TreeNode:
    """一个树节点。

    Args:
        label: 显示文本（过滤按它做子串匹配）。
        key: 唯一标识，供 ``checked`` / ``expanded`` / ``current`` 引用。
            不传时按路径自动生成（``"0/2/1"``），路径在数据不变时是稳定的。
        children: 子节点，元素可以是 :class:`TreeNode` 或 ``dict``。
        icon: 行首图标（``ft.Icons.*``）。不传就不占位，靠缩进表达层级。
        trailing: 行尾右对齐的次要文本（数量、大小、时间）。
        disabled: 该节点不可点选 / 不可勾选（其子树也不参与勾选级联），
            但仍可用箭头展开查看 —— "看得到、选不了"。
        data: 原始业务对象；回调里拿 ``node.data`` 就能回到自己的数据。
    """

    label: str
    key: Key | None = None
    children: list[TreeNode] = field(default_factory=list)
    icon: ft.IconData | None = None
    trailing: str | None = None
    disabled: bool = False
    data: Any = None

    @property
    def is_leaf(self) -> bool:
        """是否叶子节点。"""
        return not self.children


@dataclass(slots=True)
class _Row:
    """扁平化后的一行：把"渲染需要的东西"一次算好，渲染期不再回溯父链。"""

    node: TreeNode
    key: Key
    depth: int
    parent: _Row | None = None
    children: list[_Row] = field(default_factory=list)
    #: 过滤态：本节点是否命中
    matched: bool = False
    #: 过滤态：自己或后代是否命中（决定这一行要不要出现）
    subtree_matched: bool = False


def _normalize(raw: Any, path: str) -> TreeNode:
    """把 ``TreeNode`` / ``dict`` / 标量统一成 :class:`TreeNode`（就地补全 key）。"""
    if isinstance(raw, TreeNode):
        node = raw
    elif isinstance(raw, Mapping):
        label = raw.get("label", raw.get("title", raw.get("name", "")))
        node = TreeNode(
            label=str(label),
            key=raw.get("key", raw.get("id")),
            icon=raw.get("icon"),
            trailing=raw.get("trailing"),
            disabled=bool(raw.get("disabled", False)),
            data=raw,
        )
        node.children = list(raw.get("children") or ())
    else:
        node = TreeNode(label=str(raw))

    if node.key is None:
        node.key = path
    node.children = [
        _normalize(child, f"{path}/{index}" if path else str(index))
        for index, child in enumerate(node.children)
    ]
    return node


@ft.observable
@dataclass
class Tree:
    """树形控件。

    Args:
        data: 根节点列表，元素为 :class:`TreeNode` / ``dict`` / 标量。
        show_checkbox: 是否在每行前显示复选框（父子联动），默认 False。
        check_strictly: 勾选是否严格独立（父子不联动），默认 False。
        expand_on_click_node: 点击整行时是否顺带展开 / 收起，默认 True。
        check_on_click_node: 点击整行时是否顺带勾选，默认 False。
        highlight_current: 是否高亮当前行，默认 True。
        accordion: 手风琴模式：同一层级同时只展开一个，默认 False。
        show_lines: 是否画层级引导线（深树更容易看清归属），默认 False。
        indent: 每一级的缩进像素，默认 18。
        node_height: 行高，默认 32。密度要求高的场景可降到 28。
        height: 视口高度。给值时内部滚动（长树必须给值，否则随内容撑高）；
            ``None`` 表示由内容撑开，交给外层滚动。
        width: 组件宽度，``None`` 表示跟随父容器。
        expanded: 初始展开的 key 集合（等价于 Element 的 default-expanded-keys）。
        checked: 初始勾选的 key 集合（等价于 default-checked-keys）。
        current: 初始当前行的 key。
        default_expand_all: 初始展开全部，默认 False。
        disabled: 整体禁用。
        hoverable: 行悬停高亮，默认 True。悬停只就地改那一行的底色、不重建整棵树，
            所以只有"不想要这个反馈"时才关它，性能上没什么可省的。
        empty_text: 空数据文案，``None`` 取语言包。
        on_node_click: 点击节点回调，参数为该节点。
        on_node_context: 右键节点回调，``(node, event)``。
        on_current_change: 当前行变化回调，参数为新的 :class:`TreeNode`。
        on_check_change: 勾选变化回调，参数为最新的已勾选 key 列表。
        on_expand: 节点展开回调。
        on_collapse: 节点收起回调。
    """

    data: list[Any] = field(default_factory=list)
    show_checkbox: bool = False
    check_strictly: bool = False
    expand_on_click_node: bool = True
    check_on_click_node: bool = False
    highlight_current: bool = True
    accordion: bool = False
    show_lines: bool = False
    indent: int = INDENT
    node_height: int = ROW_HEIGHT
    height: int | float | None = None
    width: int | float | None = None
    expanded: set[Key] = field(default_factory=set)
    checked: set[Key] = field(default_factory=set)
    current: Key | None = None
    default_expand_all: bool = False
    disabled: bool = False
    hoverable: bool = True
    empty_text: str | None = None
    on_node_click: Callable[[TreeNode], None] | None = None
    on_node_context: Callable[[TreeNode, ft.TapEvent], None] | None = None
    on_current_change: Callable[[TreeNode], None] | None = None
    on_check_change: Callable[[list[Key]], None] | None = None
    on_expand: Callable[[TreeNode], None] | None = None
    on_collapse: Callable[[TreeNode], None] | None = None

    def __post_init__(self) -> None:
        # 复制调用方传进来的集合：组件会就地增删，不该连带改到外面那份
        self.expanded = set(self.expanded)
        self.checked = set(self.checked)
        # 运行期状态一律下划线开头：不参与序列化，改了靠 notify() 重绘。
        # 注意**没有** ``_hover``：悬停属于单行，由 :func:`_tree_row` 各管各的；
        # 放进这棵树就会被当成"树的状态变了"，划过一行重画整棵。
        self._query = ""
        self._index: dict[Key, _Row] = {}
        self._rows: list[_Row] = []
        self._roots: list[_Row] = []
        self._visible: list[_Row] = []
        self._states: dict[Key, _Check] = {}
        self._rebuild()
        if self.default_expand_all:
            self.expanded = {row.key for row in self._rows if row.children}
        # 初始勾选与 set_checked_keys 同一套语义：级联到子树、忽略无效 key。
        # 不做这步，_refresh_states 会因"父勾但子未勾"把初始 key 全部踢掉。
        if self.checked and not self.check_strictly:
            for key in list(self.checked):
                row = self._index.get(key)
                if row is not None and not row.node.disabled:
                    self._set_subtree(row, True)
            self.checked = {
                key
                for key in self.checked
                if key in self._index and not self._index[key].node.disabled
            }

    # ------------------------------------------------------------------
    # 公开操作
    # ------------------------------------------------------------------

    def set_data(self, data: Iterable[Any]) -> None:
        """整体换数据（会保留仍然存在的 key 的展开 / 勾选 / 当前行）。"""
        self.data = list(data)
        self.refresh()

    def refresh(self) -> None:
        """数据被就地修改后调用：重建索引并重绘。"""
        self._rebuild()
        keys = self._index.keys()
        self.expanded = self.expanded & keys
        self.checked = self.checked & keys
        if self.current not in self._index:
            self.current = None
        self.notify()  # type: ignore[attr-defined]

    def expand(self, key: Key, expand: bool = True) -> None:
        """展开 / 收起指定节点。"""
        row = self._index.get(key)
        if row is None or not row.children:
            return
        self._set_expanded(row, expand)
        self.notify()  # type: ignore[attr-defined]

    def collapse(self, key: Key) -> None:
        """收起指定节点。"""
        self.expand(key, False)

    def toggle(self, key: Key) -> None:
        """反转指定节点的展开态。"""
        row = self._index.get(key)
        if row is None or not row.children:
            return
        self.expand(key, key not in self.expanded)

    def expand_all(self) -> None:
        """展开全部有子节点的节点。"""
        self.expanded = {row.key for row in self._rows if row.children}
        self.notify()  # type: ignore[attr-defined]

    def collapse_all(self) -> None:
        """全部收起。"""
        self.expanded = set()
        self.notify()  # type: ignore[attr-defined]

    def filter(self, text: str | None) -> None:
        """按 ``label`` 子串过滤（忽略大小写）；``None`` / 空串表示清除。

        过滤态下自动展示命中节点及其祖先链，不改变用户原来的展开状态；
        清空过滤后回到原来的展开态。
        """
        query = (text or "").strip()
        if query == self._query:
            return
        self._query = query
        self.notify()  # type: ignore[attr-defined]

    @property
    def filter_text(self) -> str:
        """当前过滤词（空串表示未过滤）。"""
        return self._query

    def is_expanded(self, key: Key) -> bool:
        """指定节点是否展开。"""
        return key in self.expanded

    def is_checked(self, key: Key) -> bool:
        """指定节点是否处于"完全勾选"（半选不算）。"""
        self._refresh_states()
        return self._states.get(key) is _Check.CHECKED

    def get_current_key(self) -> Key | None:
        """当前行的 key。"""
        return self.current

    def get_current_node(self) -> TreeNode | None:
        """当前行的节点。"""
        row = self._index.get(self.current) if self.current is not None else None
        return row.node if row else None

    def set_current_key(self, key: Key | None) -> None:
        """设置当前行；``None`` 表示取消高亮。"""
        if key is not None and key not in self._index:
            return
        if key == self.current:
            return
        self.current = key
        row = self._index.get(key) if key is not None else None
        self.notify()  # type: ignore[attr-defined]
        if row is not None and self.on_current_change:
            self.on_current_change(row.node)

    def node(self, key: Key) -> TreeNode | None:
        """按 key 取节点。"""
        row = self._index.get(key)
        return row.node if row else None

    def get_checked_keys(self, leaf_only: bool = False) -> list[Key]:
        """已勾选的 key 列表（按树中的先后顺序）。

        Args:
            leaf_only: 只返回叶子节点（提交表单时通常要这一份）。
        """
        self._refresh_states()
        return [
            row.key
            for row in self._rows
            if self._states.get(row.key) is _Check.CHECKED
            and not (leaf_only and row.children)
        ]

    def get_checked_nodes(self, leaf_only: bool = False) -> list[TreeNode]:
        """已勾选的节点列表。"""
        return [
            self._index[key].node for key in self.get_checked_keys(leaf_only=leaf_only)
        ]

    def get_half_checked_keys(self) -> list[Key]:
        """半选（部分子节点被选中）的 key 列表。"""
        self._refresh_states()
        return [
            row.key for row in self._rows if self._states.get(row.key) is _Check.HALF
        ]

    def set_checked_keys(self, keys: Iterable[Key]) -> None:
        """按 key 设置勾选；非严格模式下自动级联到子节点并收敛父节点。"""
        self.checked = {
            key
            for key in keys
            if key in self._index and not self._index[key].node.disabled
        }
        if not self.check_strictly:
            for key in list(self.checked):
                self._set_subtree(self._index[key], True)
        self._refresh_states()
        self.notify()  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # 内部：索引 / 状态
    # ------------------------------------------------------------------

    def _rebuild(self) -> None:
        """把 ``data`` 归一化成 ``_Row`` 树 + key 索引（一次 O(n)）。"""
        roots = [_normalize(raw, str(index)) for index, raw in enumerate(self.data)]
        self._index.clear()
        self._rows.clear()

        def walk(nodes: list[TreeNode], depth: int, parent: _Row | None) -> list[_Row]:
            rows: list[_Row] = []
            for node in nodes:
                row = _Row(node=node, key=node.key, depth=depth, parent=parent)
                self._index[row.key] = row
                self._rows.append(row)
                row.children = walk(node.children, depth + 1, row)
                rows.append(row)
            return rows

        self._roots = walk(roots, 0, None)

    def _set_subtree(self, row: _Row, value: bool) -> None:
        """把勾选态铺到整棵子树（禁用节点连同子树跳过）—— 迭代而非递归。"""
        stack = [row]
        while stack:
            current = stack.pop()
            if current.node.disabled:
                continue
            if value:
                self.checked.add(current.key)
            else:
                self.checked.discard(current.key)
            stack.extend(current.children)

    def _refresh_states(self) -> None:
        """由已勾选集合反推每个节点的三态（后序，子先于父计算）。

        非严格模式下顺便修正 ``checked``：满子节点才留父 key，否则踢掉 ——
        这样外部直接塞进来的一组 key 也会被收敛成自洽状态。
        """
        states = self._states
        states.clear()
        for row in reversed(self._rows):
            if self.check_strictly or row.node.disabled or not row.children:
                states[row.key] = (
                    _Check.CHECKED if row.key in self.checked else _Check.UNCHECKED
                )
                continue

            children = [child for child in row.children if not child.node.disabled]
            if not children:
                states[row.key] = (
                    _Check.CHECKED if row.key in self.checked else _Check.UNCHECKED
                )
                continue

            child_states = [states[child.key] for child in children]
            if all(state is _Check.CHECKED for state in child_states):
                states[row.key] = _Check.CHECKED
                self.checked.add(row.key)
            elif any(state is not _Check.UNCHECKED for state in child_states):
                states[row.key] = _Check.HALF
                self.checked.discard(row.key)
            else:
                states[row.key] = _Check.UNCHECKED
                self.checked.discard(row.key)

    def _set_expanded(self, row: _Row, expand: bool) -> bool:
        """更新展开态（含手风琴处理）。返回是否真的变了。"""
        if not row.children:
            return False
        if expand:
            if self.accordion and row.parent is not None:
                for sibling in row.parent.children:
                    if sibling is not row:
                        self.expanded.discard(sibling.key)
            if row.key in self.expanded:
                return False
            self.expanded.add(row.key)
            if self.on_expand:
                self.on_expand(row.node)
            return True
        if row.key not in self.expanded:
            return False
        self.expanded.discard(row.key)
        if self.on_collapse:
            self.on_collapse(row.node)
        return True

    def _prepare(self) -> None:
        """渲染前一次算好：三态 + 过滤 + 可见行。"""
        self._refresh_states()
        if self._query:
            needle = self._query.casefold()
            # 后序：子节点的命中要先算好，父节点才知道要不要露出来
            for row in reversed(self._rows):
                row.matched = needle in row.node.label.casefold()
                row.subtree_matched = row.matched or any(
                    child.subtree_matched for child in row.children
                )
        self._visible = self._collect()

    def _collect(self) -> list[_Row]:
        """DFS 收集可见行：过滤态下忽略展开状态，只留命中路径。"""
        visible: list[_Row] = []

        if self._query:

            def walk_filtered(rows: list[_Row]) -> None:
                for row in rows:
                    if not row.subtree_matched:
                        continue
                    visible.append(row)
                    walk_filtered(row.children)

            walk_filtered(self._roots)
            return visible

        def walk(rows: list[_Row]) -> None:
            for row in rows:
                visible.append(row)
                if row.key in self.expanded:
                    walk(row.children)

        walk(self._roots)
        return visible

    # ------------------------------------------------------------------
    # 内部：事件
    # ------------------------------------------------------------------

    def _on_row_tap(self, key: Key, _event: ft.TapEvent) -> None:
        """整行点击：选中当前行，并按设置决定是否顺带展开 / 勾选。"""
        self._activate(key)

    def _on_row_context(self, key: Key, event: ft.TapEvent) -> None:
        row = self._index.get(key)
        if row is None or row.node.disabled:
            return
        if self.highlight_current:
            self.current = row.key
            self.notify()  # type: ignore[attr-defined]
        if self.on_node_context:
            self.on_node_context(row.node, event)

    def _on_arrow_tap(self, key: Key, _event: ft.TapEvent) -> None:
        row = self._index.get(key)
        if row is None:
            return
        if self._set_expanded(row, row.key not in self.expanded):
            self.notify()  # type: ignore[attr-defined]

    def _on_check_tap(self, key: Key, _event: ft.TapEvent | None = None) -> None:
        row = self._index.get(key)
        if row is None or row.node.disabled or self.disabled:
            return
        self._toggle_check(row)
        self.notify()  # type: ignore[attr-defined]
        if self.on_check_change:
            self.on_check_change(self.get_checked_keys())

    def _toggle_check(self, row: _Row) -> None:
        if self.check_strictly:
            if row.key in self.checked:
                self.checked.discard(row.key)
            else:
                self.checked.add(row.key)
        else:
            state = self._states.get(row.key, _Check.UNCHECKED)
            self._set_subtree(row, state is not _Check.CHECKED)
        self._refresh_states()

    def _activate(self, key: Key) -> None:
        row = self._index.get(key)
        if row is None or row.node.disabled or self.disabled:
            return

        changed = False
        if self.expand_on_click_node:
            changed |= self._set_expanded(row, row.key not in self.expanded)
        if self.check_on_click_node and self.show_checkbox:
            self._toggle_check(row)
            if self.on_check_change:
                self.on_check_change(self.get_checked_keys())
            changed = True
        if self.current != row.key:
            self.current = row.key
            changed = True
            if self.on_current_change:
                self.on_current_change(row.node)
        if changed:
            self.notify()  # type: ignore[attr-defined]
        if self.on_node_click:
            self.on_node_click(row.node)

    # ------------------------------------------------------------------
    # 内部：渲染
    # ------------------------------------------------------------------

    def _row_control(
        self,
        row: _Row,
        *,
        hovered: bool = False,
        on_enter: Callable | None = None,
        on_exit: Callable | None = None,
    ) -> ft.Control:
        """一行：引导线 + 箭头 + 复选框 + 图标 + 文本 + 尾部。

        ``hovered`` / ``on_enter`` / ``on_exit`` 由 :func:`_tree_row` 提供：悬停状态
        属于**行**，不属于树 —— 放在树上就会"划过一行重画全部"。
        """
        disabled = self.disabled or row.node.disabled
        state = self._states.get(row.key, _Check.UNCHECKED)
        selected = self.highlight_current and self.current == row.key

        if selected:
            bgcolor: ft.ColorValue | None = SELECTED_BG
        elif hovered and not disabled:
            bgcolor = HOVER_BG
        else:
            bgcolor = None

        controls: list[ft.Control] = [
            *self._guides(row.depth),
            self._arrow(row, disabled),
        ]
        if self.show_checkbox:
            controls.append(self._checkbox(row, state, disabled))
        if row.node.icon:
            controls.append(self._icon(row, disabled))
        controls.append(self._label(row, selected, disabled))
        if row.node.trailing:
            controls.append(
                ft.Container(
                    padding=ft.Padding.only(left=8),
                    content=ft.Text(
                        row.node.trailing,
                        size=TRAILING_SIZE,
                        color=ft.Colors.OUTLINE,
                        no_wrap=True,
                    ),
                )
            )

        body = ft.Container(
            height=self.node_height,
            margin=ft.Margin.symmetric(horizontal=4),
            padding=ft.Padding.only(right=8),
            border_radius=ft.BorderRadius.all(RADIUS["md"]),
            bgcolor=bgcolor,
            content=ft.Row(
                spacing=0,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=controls,
            ),
        )

        # 禁用行不挂手势：GestureDetector 一个事件都没有时会抛错（真机踩过）
        handlers: dict[str, object] = {}
        if not disabled:
            handlers["on_tap"] = partial(self._on_row_tap, row.key)
            if self.on_node_context is not None:
                handlers["on_secondary_tap"] = partial(self._on_row_context, row.key)
            # 悬停用 enter / exit：GestureDetector 的 hover 载荷是 None，
            # 拿不到"进/出"（只有 Container 给 "true"/"false"）。
            if on_enter is not None:
                handlers["on_enter"] = on_enter
            if on_exit is not None:
                handlers["on_exit"] = on_exit
        if not handlers:
            return body
        return ft.GestureDetector(content=body, **handlers)  # type: ignore[arg-type]

    def _guides(self, depth: int) -> list[ft.Control]:
        """层级缩进；``show_lines`` 时每级再画一根 1px 竖线。

        缩进**必须**无条件给：引导线只是装饰，不能让它决定布局 —— 否则关掉
        引导线整棵树会拍平（真机截图里踩过）。竖线放在缩进格的正中，正好对齐
        上一级箭头的中心；高度取整行高，行与行之间自然接成一条连续的线。
        """
        cells: list[ft.Control] = []
        for _ in range(depth):
            if self.show_lines:
                content: ft.Control | None = ft.Container(
                    width=1, height=self.node_height, bgcolor=GUIDE_COLOR
                )
            else:
                content = None
            cells.append(
                ft.Container(
                    width=self.indent,
                    height=self.node_height,
                    alignment=ft.Alignment.CENTER,
                    content=content,
                )
            )
        return cells

    def _arrow(self, row: _Row, disabled: bool) -> ft.Control:
        """展开箭头：叶子留等宽占位，保证同级的文字左边缘对齐。"""
        if not row.children:
            return ft.Container(width=ARROW_BOX, height=ARROW_BOX)

        expanded = row.key in self.expanded
        icon = ft.Container(
            width=ARROW_BOX,
            height=ARROW_BOX,
            alignment=ft.Alignment.CENTER,
            border_radius=ft.BorderRadius.all(RADIUS["sm"]),
            content=ft.Icon(
                ft.Icons.KEYBOARD_ARROW_DOWN
                if expanded
                else ft.Icons.KEYBOARD_ARROW_RIGHT,
                size=18,
                color=ft.Colors.OUTLINE if disabled else ft.Colors.ON_SURFACE_VARIANT,
            ),
        )
        if self.disabled:
            return icon
        return ft.GestureDetector(
            on_tap=partial(self._on_arrow_tap, row.key), content=icon
        )

    def _checkbox(self, row: _Row, state: _Check, disabled: bool) -> ft.Control:
        """三态复选框：选中是实心方块 + 对勾，半选是一条短横。"""
        if state is _Check.CHECKED:
            box = ft.Container(
                width=CHECK_BOX,
                height=CHECK_BOX,
                border_radius=_CHECK_RADIUS,
                bgcolor=ft.Colors.OUTLINE if disabled else ft.Colors.PRIMARY,
                alignment=ft.Alignment.CENTER,
                content=ft.Icon(ft.Icons.CHECK, size=12, color=ft.Colors.ON_PRIMARY),
            )
        elif state is _Check.HALF:
            box = ft.Container(
                width=CHECK_BOX,
                height=CHECK_BOX,
                border_radius=_CHECK_RADIUS,
                bgcolor=ft.Colors.OUTLINE if disabled else ft.Colors.PRIMARY,
                alignment=ft.Alignment.CENTER,
                content=ft.Container(
                    width=8,
                    height=2,
                    border_radius=_HALF_BAR_RADIUS,
                    bgcolor=ft.Colors.ON_PRIMARY,
                ),
            )
        else:
            # 空框必须真的空心：写 Colors.TRANSPARENT 时 Flutter 侧会画出一块
            # 灰底，深色主题下看着像"半灰的实心块"，和勾选态撞在一起。
            box = ft.Container(
                width=CHECK_BOX,
                height=CHECK_BOX,
                border_radius=_CHECK_RADIUS,
                bgcolor=None,
                border=_CHECK_BORDER_OFF if disabled else _CHECK_BORDER,
            )

        hit = ft.Container(
            width=CHECK_HIT,
            height=CHECK_HIT,
            margin=_CHECK_MARGIN,
            alignment=ft.Alignment.CENTER,
            content=box,
        )
        if disabled:
            return hit
        return ft.GestureDetector(
            on_tap=partial(self._on_check_tap, row.key), content=hit
        )

    def _icon(self, row: _Row, disabled: bool) -> ft.Control:
        return ft.Container(
            width=18,
            height=18,
            margin=ft.Margin.only(right=4),
            alignment=ft.Alignment.CENTER,
            content=ft.Icon(
                row.node.icon,
                size=16,
                color=ft.Colors.OUTLINE if disabled else ft.Colors.ON_SURFACE_VARIANT,
            ),
        )

    def _label(self, row: _Row, selected: bool, disabled: bool) -> ft.Control:
        """节点文本；有过滤词时把命中的那一段染色加粗。"""
        if disabled:
            color: ft.ColorValue = ft.Colors.OUTLINE
        elif selected:
            color = ft.Colors.PRIMARY
        else:
            color = ft.Colors.ON_SURFACE

        common = {
            "size": TEXT_SIZE,
            "color": color,
            "weight": ft.FontWeight.W_500 if selected else None,
            "no_wrap": True,
            "overflow": ft.TextOverflow.ELLIPSIS,
            "expand": True,
        }

        needle = self._query.casefold()
        at = row.node.label.casefold().find(needle) if needle else -1
        if at < 0:
            return ft.Text(row.node.label, **common)

        end = at + len(needle)
        return ft.Text(
            spans=[
                ft.TextSpan(row.node.label[:at]),
                ft.TextSpan(
                    row.node.label[at:end],
                    style=ft.TextStyle(
                        color=ft.Colors.PRIMARY, weight=ft.FontWeight.W_600
                    ),
                ),
                ft.TextSpan(row.node.label[end:]),
            ],
            **common,
        )

    def _body(self, rows: list[_Row]) -> ft.Control:
        # 每行一个组件：悬停状态挂在行自己身上，划过一行只重绘那一行，
        # 而不是整棵树（见 :func:`_tree_row`）。
        controls = [_tree_row(self, row, key=row.key) for row in rows]
        if self.height is not None:
            # 长树给固定视口：ListView 按需构建，滚动时才生成行
            return ft.ListView(
                controls=controls,
                height=self.height,
                spacing=0,
                padding=0,
                build_controls_on_demand=True,
            )
        return ft.Column(
            controls=controls,
            spacing=0,
            # 行要铺满宽度：否则"点空白处也能选中"和整行悬停高亮都会失效
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )

    def _empty(self) -> ft.Control:
        return ft.Container(
            height=EMPTY_HEIGHT,
            alignment=ft.Alignment.CENTER,
            content=ft.Text(
                self.empty_text or t("ui.tree.empty"),
                size=FONT_SIZE["small"],
                color=ft.Colors.OUTLINE,
            ),
        )

    @ft.component
    def ui(self) -> ft.Control:
        """构建树控件。"""
        use_t()  # 订阅语言：空态文案要跟着切
        self._prepare()
        body: ft.Control = self._body(self._visible) if self._visible else self._empty()
        return ft.Container(width=self.width, content=body)


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
def _project() -> list[TreeNode]:
    """四层文件树：cs-ui / src / ui / *.py —— 用来演示缩进、展开与禁用行。"""
    return [
        TreeNode(
            "cs-ui",
            key="root",
            icon=ft.Icons.FOLDER_SPECIAL,
            trailing="4 项",
            children=[
                TreeNode(
                    "src",
                    key="src",
                    icon=ft.Icons.FOLDER_OPEN,
                    children=[
                        TreeNode(
                            "ui",
                            key="ui",
                            icon=ft.Icons.FOLDER,
                            children=[
                                TreeNode(
                                    "tree.py",
                                    key="tree",
                                    icon=ft.Icons.DESCRIPTION,
                                ),
                                TreeNode(
                                    "image_gridview.py",
                                    key="grid",
                                    icon=ft.Icons.DESCRIPTION,
                                ),
                                TreeNode(
                                    "number_animation.py",
                                    key="anim",
                                    icon=ft.Icons.DESCRIPTION,
                                ),
                            ],
                        ),
                        TreeNode("app.py", key="app", icon=ft.Icons.DESCRIPTION),
                    ],
                ),
                TreeNode(
                    "docs",
                    key="docs",
                    icon=ft.Icons.FOLDER,
                    children=[
                        TreeNode("index.md", key="index", icon=ft.Icons.ARTICLE),
                    ],
                ),
                TreeNode("README.md", key="readme", icon=ft.Icons.ARTICLE),
                TreeNode("vendor", key="vendor", icon=ft.Icons.LOCK, disabled=True),
            ],
        ),
    ]


# ---------------------------------------------------------------------------
# 每行一个组件：把"悬停"关在一行之内
# ---------------------------------------------------------------------------
@ft.component
def _tree_row(tree: Tree, row: _Row) -> ft.Control:
    """树行 = 一个独立组件，悬停状态挂在它自己身上。

    悬停若记在 ``Tree`` 上，``notify()`` 会让整棵树重绘 —— 一屏 60 行就是
    60 次行构建 + 一份全新的控件树下发。拆到行上之后，划过一行只重绘那一行。
    （为什么不"就地改颜色 + update()"：已挂载的控件在 flet 1.1 里是冻结的，
    改属性与 ``update()`` 都会抛 ``Frozen controls cannot be updated``。）
    """
    hovered, set_hovered = ft.use_state(False)

    def on_enter(_e: ft.Event) -> None:
        if not hovered:
            set_hovered(True)

    def on_exit(_e: ft.Event) -> None:
        if hovered:
            set_hovered(False)

    live = tree.hoverable
    return tree._row_control(
        row,
        hovered=hovered and live,
        on_enter=on_enter if live else None,
        on_exit=on_exit if live else None,
    )


@ft.component
def _basic() -> ft.Control:
    """默认展开 cs-ui 与 src：ui 那一层的文件藏在里面，等用户点开。"""
    tree = ft.use_memo(
        lambda: Tree(
            data=_project(),
            expanded={"root", "src"},
            show_lines=True,
            height=268,
        ),
        [],
    )
    return tree.ui()


@ft.component
def _selection(tree: Tree) -> ft.Control:
    """把勾选结果读出来。

    ``tree`` 是**参数**，组件会因此订阅这棵树 —— 勾选一变这一行自己重绘，
    不需要再拉一个 use_state 去镜像状态。
    """
    keys = tree.get_checked_keys()
    if not keys:
        return ft.Text(
            "未勾选任何节点 · 勾一个父节点看看级联",
            size=FONT_SIZE["small"],
            color=ft.Colors.ON_SURFACE_VARIANT,
        )
    leaves = [node.label for node in tree.get_checked_nodes(leaf_only=True)]
    detail = "、".join(leaves[:3]) + ("…" if len(leaves) > 3 else "")
    text = f"已选 {len(keys)} 个节点" + (f" · {detail}" if detail else "")
    return ft.Text(
        text,
        size=FONT_SIZE["small"],
        color=ft.Colors.ON_SURFACE_VARIANT,
        no_wrap=True,
        overflow=ft.TextOverflow.ELLIPSIS,
    )


@ft.component
def _checked() -> ft.Control:
    """勾父节点会级联到整棵子树；只勾一部分时父节点显示成一条短横。"""
    tree = ft.use_memo(
        lambda: Tree(
            data=_project(),
            show_checkbox=True,
            show_lines=True,
            height=240,
        ),
        [],
    )
    return ft.Column(spacing=6, controls=[tree.ui(), _selection(tree)])


@ft.component
def _filter() -> ft.Control:
    """过滤按 label 子串匹配，命中路径自动露出，清空后回到原来的展开态。"""
    tree = ft.use_memo(
        lambda: Tree(data=_project(), show_lines=True, height=196),
        [],
    )

    def find(e: ft.ControlEvent) -> None:
        tree.filter(str(e.control.value or ""))

    return ft.Column(
        spacing=8,
        controls=[
            ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.TextField(
                        hint_text="按名称过滤，例如 py",
                        width=210,
                        height=40,
                        dense=True,
                        on_change=find,
                    ),
                    ft.Button("全部展开", on_click=lambda _e: tree.expand_all()),
                    ft.Button("全部收起", on_click=lambda _e: tree.collapse_all()),
                ],
            ),
            tree.ui(),
        ],
    )


# ---------------------------------------------------------------------------
# 示例源码（“查看代码”面板）
# ---------------------------------------------------------------------------
_BASIC_CODE = """Tree(
    data=[
        TreeNode("src", icon=Icons.FOLDER, children=[
            TreeNode("main.py"),
            TreeNode("ui", children=[TreeNode("tree.py")]),
        ]),
        {"label": "README.md"},        # 也认 dict：label / title / name
    ],
    expanded={"src"},                  # 初始展开；default_expand_all 全开
    show_lines=True,                   # 深树才需要引导线
    height=268,                        # 给视口才会内部滚动
).ui()"""

_CHECK_CODE = """tree = Tree(
    data=[...],
    show_checkbox=True,
    expanded={"src"},
    on_check_change=lambda keys: print(keys),   # 全量 key，按树中顺序
)
Column([tree.ui(), Text(f"已选 {len(tree.get_checked_keys())} 项")])

# 提交表单时通常只要叶子
tree.get_checked_keys(leaf_only=True)"""

_FILTER_CODE = """tree = Tree(data=[...], show_lines=True, height=196)

tree.filter("py")        # 子串匹配（忽略大小写），命中路径自动露出
tree.filter(None)        # 清空过滤，回到过滤前的展开态
tree.expand_all()        # collapse_all() / expand(key) / toggle(key)
tree.set_current_key("ui")"""


# ---------------------------------------------------------------------------
# 组件说明
# ---------------------------------------------------------------------------
SPEC = Spec(
    name="Tree",
    summary="把层级数据铺成一列可展开的行：选中、勾选级联、关键字过滤。",
    definition=(
        "Tree 显示有父子关系的数据：文件目录、组织架构、分类表。它不递归建控件树，"
        "而是先把数据拍平成本轮可见的行，再交给按需构建的 ListView —— 展开一个节点只是"
        "重排可见行，节点上千首帧也不会卡。选中、勾选、展开、过滤是四件独立的事，各有"
        "自己的状态与回调，调用方按需接管其中一件即可。"
    ),
    anatomy=[
        (
            "行",
            "高 32px，整行可点即选中；层级、箭头、复选框、图标、文本、尾注排成一排。",
        ),
        (
            "展开箭头",
            "只有非叶子才画；叶子留一块同宽空位，同级文字的左边缘才对得齐。",
        ),
        (
            "复选框",
            "16px 方块配 22px 命中区：空框 / 实心对勾 / 一条短横（半选）三态。",
        ),
        (
            "层级缩进",
            "每级 18px；show_lines 时在缩进正中补一根 1px 竖线，行与行之间自然接成一条。",
        ),
        (
            "尾注",
            "trailing 右对齐的次要信息（数量、大小）。节点文字被省略号压缩时它保持完整。",
        ),
        ("空态", "没有可见行时居中一行「暂无节点」，高度 72px，容器不会塌成一条线。"),
    ],
    when=[
        "文件目录、组织架构、分类表这类天然分层的数据",
        "需要在层级上批量勾选，并且希望父节点自动收敛成全选 / 半选",
        "节点多到必须靠展开折叠控制一屏的信息量",
    ],
    avoid=[
        "只有一层的数据：ListView 或 ListTile 就够，树只是多留了一个空箭头位",
        (
            "两三个固定分区、每块都要完整阅读（设置项、说明区）：用 Expander 直接摊开，"
            "不该让用户点进树里找"
        ),
        "需要就地改节点内容（改名、改值）：树只管展示与选择，编辑行得自己拼",
    ],
    examples=[
        Example(
            "基础用法",
            _basic,
            hint="四层文件树，默认展开 cs-ui 与 src；点箭头只展开，点整行选中并顺带展开。",
            code=_BASIC_CODE,
        ),
        Example(
            "复选联动",
            _checked,
            hint="勾父节点级联到整棵子树；只勾一部分时父节点是短横，下方那行实时读出结果。",
            code=_CHECK_CODE,
        ),
        Example(
            "过滤与批量展开",
            _filter,
            hint="输入 py 只留下命中路径；过滤不改变展开状态，清空后原样回来。",
            code=_FILTER_CODE,
        ),
    ],
    api=[
        Api("data", "list[Any]", "[]", "根节点：TreeNode / dict / 标量都可"),
        Api("show_checkbox", "bool", "False", "行前复选框，默认父子级联"),
        Api("check_strictly", "bool", "False", "开则勾选各自独立，不再级联"),
        Api("expand_on_click_node", "bool", "True", "点整行时顺带展开 / 收起"),
        Api(
            "check_on_click_node",
            "bool",
            "False",
            "点整行时顺带勾选（需 show_checkbox）",
        ),
        Api("show_lines", "bool", "False", "画层级引导线；深树更容易看清归属"),
        Api(
            "height",
            "int | float | None",
            "None",
            "视口高度；给了才内部滚动，否则由内容撑开",
        ),
        Api(
            "expanded",
            "set[str | int]",
            "set()",
            "初始展开的 key；default_expand_all 全开",
        ),
        Api(
            "on_check_change",
            "Callable[[list[str | int]], None] | None",
            "None",
            "勾选变化回调，参数是全量 key（按树中顺序）",
        ),
        Api(
            "filter(text)",
            "(str | None) -> None",
            "—",
            "按 label 子串过滤；None 或空串清空",
        ),
    ],
    notes=[
        info(
            "半选态不单独存：状态里只有「已勾选」，父节点的半选由子节点反推。所以 "
            "set_checked_keys() 塞进一组不自洽的 key，渲染前也会被收敛成合法状态，"
            "不会出现父选中而子未选。"
        ),
        tip(
            "一次点击只做一件事：整行 = 选中（默认顺带展开）、箭头 = 只展开、复选框 = 只勾选，"
            "三者各自独立。想「点整行只选中」，把 expand_on_click_node 关掉。"
        ),
        info(
            "未勾选的方框用 bgcolor=None 而不是 Colors.TRANSPARENT：后者在 Flutter 侧会画出"
            "一块灰底，深色主题下空框看着像半灰的实心块，和半选态分不清。"
        ),
    ],
    tags=("树", "tree", "层级", "目录", "组织架构", "勾选"),
)


if __name__ == "__main__":
    run(SPEC)
