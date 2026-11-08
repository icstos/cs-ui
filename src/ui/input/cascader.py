"""级联选择器 (Cascader)。

交互模型对齐 Element ``el-cascader`` 与桌面端软件的直觉：**一个输入框，点开
挂出多列面板，每一级占一列、逐级向右展开**。

- 单选：点叶子（或 ``check_strictly`` 下的任意级）即选中并收起；框内按
  ``separator`` 显示完整路径（``show_all_levels=False`` 只显最后一级）；
- 多选（``multiple``）：复选框父子级联、父节点三态（√ / – / 空）；框内以
  Chip 展示，``collapse_tags`` 折叠为「第一个 + 数量」；
- ``check_strictly``：父子不关联，可选任意一级（单击行展开，点选框/单选点选定）；
- ``expand_trigger="hover"``：悬停即展开下一级（点选框仍走点击）；
- ``filterable``：展开后框内可直接键入，面板切成扁平命中列表（显示路径、
  高亮命中子串），点命中项与列内点选项同一套语义；
- ``clearable``：框内 × 一键清空；``emit_path=False`` 时对外只回叶子值。

.. note::
    面板挂在页面浮层（``page.overlay``），不占布局高度；浮层不可用时自动
    降级为流内展开（机制与 :class:`~ui.input.date_input.DateInput` 相同，
    见 :func:`ui.core.float_layer.overlay_usable`）。

.. note::
    不做键盘导航，原因与 :class:`~ui.display.tree.Tree` 相同：flet 1.0 的
    ``KeyboardListener`` 在重绘后会把焦点交给兄弟节点，没有稳定的控件级
    按键钩子。

用法::

    c = Cascader(label="所属地区", options=[
        {"label": "浙江", "children": [
            {"label": "杭州", "children": [{"label": "西湖区"}]},
        ]},
    ])
    ...
    container = c.ui()
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field, replace
from typing import Any

import flet as ft

from ui.core.doc import Api, Example, Spec, info, run, tip, warn
from ui.core.empty import empty_line
from ui.core.float_layer import use_float_layer
from ui.core.i18n import t, use_t
from ui.core.icons import PANEL_CLOSE, PANEL_OPEN
from ui.core.tokens import FONT_SIZE, ICON_SIZE
from ui.input.input import Label
from ui.input.panel_field import (
    DISABLED_FG,
    FIELD_HEIGHT,
    FIELD_WIDTH,
    HOVER_BG,
    PANEL_GAP,
    PANEL_PAD,
    PanelField,
    place_panel,
)

__all__ = ["Cascader", "CascaderNode"]

# ---------------------------------------------------------------------------
# 尺寸（面板独有）
# ---------------------------------------------------------------------------
COL_W = 180  # 每一级菜单的列宽
ITEM_H = 32  # 单行高度
ITEM_PAD_H = 12  # 行内左右内边距
MIN_ROWS = 5  # 面板最少显示的行数（再少也保持这个高度，避免面板跳动）
MAX_ROWS = 8  # 面板最多显示的行数（更多的行内滚动）
CHIP_MAX_W = 120  # 单个 Chip 文本的最大宽度（超出省略）

#: 行文字：与正文同档（列表行就是正文）
ITEM_SIZE = FONT_SIZE["body"]


def _clip(text: str, limit: float = CHIP_MAX_W, size: float = 12.0) -> str:
    """按估算像素宽截断文本（全角按 1em、半角按 0.55em），超出补省略号。"""
    width = 0.0
    for i, ch in enumerate(text):
        width += size if ord(ch) > 0x2E7F else size * 0.55
        if width > limit:
            return text[:i] + "…"
    return text


# ---------------------------------------------------------------------------
# 数据
# ---------------------------------------------------------------------------
@dataclass
class CascaderNode:
    """归一化后的选项节点。

    Args:
        label: 显示文本。
        value: 提交值（``None`` 时用 ``label`` 兜底 —— 纯展示型数据不必两个都写）。
        children: 子节点列表。
        disabled: 禁用（自身与子树都不可选，但仍可展开查看）。
        leaf: 显式叶子标记（用于"还有动态子级但目前没有 children"的场景；
            ``None`` 表示按 ``children`` 推断）。
    """

    label: str = ""
    value: Any = None
    children: list[CascaderNode] = field(default_factory=list)
    disabled: bool = False
    leaf: bool | None = None

    @property
    def is_leaf(self) -> bool:
        """是否叶子：显式 ``leaf`` 优先，否则看有没有 children。"""
        return self.leaf if self.leaf is not None else not self.children


#: 路径：从根到某节点的 value 序列。内部状态的唯一钥匙。
Path = tuple[Any, ...]


def _normalize(
    raw: Any,
    *,
    label_key: str,
    value_key: str,
    children_key: str,
    disabled_key: str,
    leaf_key: str,
) -> CascaderNode:
    """把 dict / CascaderNode / 标量归一成 :class:`CascaderNode`。

    ``CascaderNode`` 的子级也要递归 —— 允许 ``CascaderNode(children=[{...}])``
    这种"半结构半数据"的写法。只做一层拷贝的话，循环里会把 dict 当节点用，
    读 ``.children`` 就抛 ``AttributeError``。
    """
    kw = {
        "label_key": label_key,
        "value_key": value_key,
        "children_key": children_key,
        "disabled_key": disabled_key,
        "leaf_key": leaf_key,
    }
    if isinstance(raw, CascaderNode):
        return replace(
            raw,
            label=str(raw.label),
            value=raw.value if raw.value is not None else str(raw.label),
            children=[_normalize(child, **kw) for child in raw.children],
        )
    if isinstance(raw, dict):
        children = [_normalize(child, **kw) for child in (raw.get(children_key) or [])]
        label = raw.get(label_key)
        value = raw.get(value_key)
        return CascaderNode(
            label=str(label if label is not None else value),
            value=value if value is not None else str(label),
            children=children,
            disabled=bool(raw.get(disabled_key, False)),
            leaf=raw.get(leaf_key),
        )
    # 标量：展示与取值同一个东西
    return CascaderNode(label=str(raw), value=raw)


# ---------------------------------------------------------------------------
# 三态
# ---------------------------------------------------------------------------
@dataclass
class _Check:
    """复选三态（多选模式用）。用单例实例而不是 enum，比较直接 ``is``。"""

    name: str


_UNCHECKED = _Check("unchecked")
_CHECKED = _Check("checked")
_HALF = _Check("half")


# ---------------------------------------------------------------------------
# 组件
# ---------------------------------------------------------------------------
@ft.observable
@dataclass
class Cascader(PanelField, Label):
    """级联选择器：输入框 + 多列浮层面板。

    Args:
        options: 选项数据源。接受 dict（``label`` / ``value`` / ``children`` /
            ``disabled`` / ``leaf``，键名可用下面的 ``*_key`` 参数改）、
            :class:`CascaderNode` 或标量（展示与取值同一个东西）。
        value: 当前值。单选：路径列表（``emit_path=True``，默认）或叶子值
            （``emit_path=False``）；多选：前两者的列表。``None`` 表示未选择。
        multiple: 是否多选（复选 + 父子级联 + Chip 展示）。
        check_strictly: 父子不关联，可选任意一级。
        emit_path: 对外值是否为完整路径（``False`` 时只回该节点自身的 value）。
        show_all_levels: 框内是否显示完整路径（单选 / 非折叠 Chip 生效）。
        separator: 路径分隔符，默认 ``" / "``。
        placeholder: 未选择时的占位文本。``None`` 取语言包「请选择」。
        clearable: 是否显示框内 ×，默认 True。
        filterable: 展开后可键入搜索（面板切成扁平命中列表）。
        filter_method: 自定义命中判定 ``(node, keyword) -> bool``；
            ``None`` 用「label 忽略大小写包含」。
        expand_trigger: 展开下一级的方式，``"click"``（默认）或 ``"hover"``。
        collapse_tags: 多选时是否折叠 Chip（显示第一个 + 数量）。
        width: 输入框宽度，默认 240。
        height: 输入框高度，默认 40。
        disabled: 是否禁用。
        is_open: 面板是否展开（运行期状态，可代码控制）。
        float_panel: 面板是否走页面浮层。``None`` 自动判定。
        label_key / value_key / children_key / disabled_key / leaf_key:
            dict 数据源的键名映射。
        on_change: 选中变化回调，接收对外形式的最新值。
        on_expand_change: 展开节点变化回调，接收路径 value 列表。
        on_visible_change: 面板出现 / 隐藏回调。
    """

    options: list[Any] = field(default_factory=list)
    value: Any = None
    multiple: bool = False
    check_strictly: bool = False
    emit_path: bool = True
    show_all_levels: bool = True
    separator: str = " / "
    placeholder: str | None = None
    clearable: bool = True
    filterable: bool = False
    filter_method: Callable[[CascaderNode, str], bool] | None = None
    expand_trigger: str = "click"
    collapse_tags: bool = False
    width: int | float = FIELD_WIDTH
    height: int | float = FIELD_HEIGHT
    disabled: bool = False
    is_open: bool = False
    float_panel: bool | None = None
    label_key: str = "label"
    value_key: str = "value"
    children_key: str = "children"
    disabled_key: str = "disabled"
    leaf_key: str = "leaf"
    on_change: Callable[[Any], None] | None = None
    on_expand_change: Callable[[list[Any]], None] | None = None
    on_visible_change: Callable[[bool], None] | None = None

    # ------------------------------------------------------------------
    # 初始化：建索引 + 把对外 value 换成内部路径
    # ------------------------------------------------------------------
    def __post_init__(self) -> None:
        # PanelField / 运行期状态
        self._hover: str | None = None
        self._anchor: tuple[float, float] | None = None
        self._field_w: float = float(self.width)
        self._field_h: float = float(self.height)
        self._invalid: bool = False
        self._query: str = ""  # 过滤关键词；空串 = 列模式
        # 面板展开链：chain[i] 是第 i 级被展开节点的路径
        self._chain: list[Path] = []
        # 内部选中态
        self._active: Path | None = None  # 单选
        self._checked: set[Path] = set()  # 多选
        self._states: dict[Path, _Check] = {}  # 多选三态缓存
        self._emitted: Any = None
        self._rebuild()
        self._load_value(self.value)

    # ------------------------------------------------------------------
    # 索引
    # ------------------------------------------------------------------
    def _rebuild(self) -> None:
        """options → 归一化树 + 三个索引（一次 O(n)）。"""
        kw = {
            "label_key": self.label_key,
            "value_key": self.value_key,
            "children_key": self.children_key,
            "disabled_key": self.disabled_key,
            "leaf_key": self.leaf_key,
        }
        self._roots: list[CascaderNode] = [
            _normalize(raw, **kw) for raw in self.options
        ]
        self._by_path: dict[Path, CascaderNode] = {}
        self._parent_of: dict[Path, Path | None] = {}
        self._by_value: dict[Any, Path] = {}

        stack: list[tuple[CascaderNode, Path | None]] = [
            (node, None) for node in self._roots
        ]
        while stack:
            node, parent = stack.pop()
            path: Path = (parent or ()) + (node.value,)
            if path not in self._by_path:  # 同 path 后到者不覆盖先到者
                self._by_path[path] = node
            self._parent_of.setdefault(path, parent)
            self._by_value.setdefault(node.value, path)
            for child in node.children:
                stack.append((child, path))

    def refresh(self) -> None:
        """options 被就地修改后调用：重建索引并按当前对外 value 重载选中态。"""
        self._rebuild()
        self._chain = []
        self._load_value(self.value)
        self.notify()  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # 对外值 ↔ 内部路径
    # ------------------------------------------------------------------
    def _to_path(self, item: Any) -> Path | None:
        """对外单项值 → 内部路径。非法/找不到返回 ``None``。"""
        if isinstance(item, (list, tuple)):
            path = tuple(item)
            return path if path in self._by_path else None
        return self._by_value.get(item)

    def _emit_form(self, path: Path) -> Any:
        """内部路径 → 对外单项值（emit_path 决定给路径还是叶子值）。"""
        return list(path) if self.emit_path else path[-1]

    def _load_value(self, value: Any) -> None:
        """把对外 ``value`` 装进内部选中态（构造 / refresh 时）。"""
        self._query = ""
        if self.multiple:
            items = (
                value
                if isinstance(value, (list, tuple))
                else ([] if value is None else [value])
            )
            paths = {p for p in (self._to_path(i) for i in items) if p is not None}
            self._active = None
            self._checked = paths
            if not self.check_strictly:
                # 与 set_checked 同一套语义：级联到子树
                for path in list(paths):
                    self._subtree(path, True)
            # 三态缓存要立刻算一次：否则面板第一次打开时，已勾选的节点画出来
            # 全是空框（_states 只有 _toggle_check 之后才有值）。
            self._refresh_states()
        else:
            path = self._to_path(value) if value is not None else None
            self._checked = set()
            self._active = path
            if path is not None:
                # 跟随选中路径展开面板列
                self._chain = [path[: i + 1] for i in range(len(path) - 1)]

    def _write_back(self) -> None:
        """内部选中态 → 对外 ``value`` 并按值去重广播。"""
        if self.multiple:
            snapshot = [self._emit_form(p) for p in self._checked_paths()]
        else:
            snapshot = None if self._active is None else self._emit_form(self._active)
        self.value = snapshot
        if snapshot != self._emitted:
            self._emitted = snapshot
            if self.on_change:
                self.on_change(snapshot)
        self.notify()  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # 公开操作
    # ------------------------------------------------------------------
    def open(self) -> None:
        """展开面板（列跟随当前选中路径）。"""
        if self.disabled or self.is_open:
            return
        self._query = ""
        if not self._chain:
            base = self._active
            if base is not None:
                self._chain = [base[: i + 1] for i in range(len(base) - 1)]
        self.is_open = True
        self.notify()  # type: ignore[attr-defined]
        if self.on_visible_change:
            self.on_visible_change(True)

    def close(self) -> None:
        """收起面板（丢弃未提交的过滤词与悬停态）。"""
        if not self.is_open:
            return
        self.is_open = False
        self._hover = None
        self._query = ""
        self.notify()  # type: ignore[attr-defined]
        if self.on_visible_change:
            self.on_visible_change(False)

    def toggle_open(self) -> None:
        """展开 / 收起。"""
        self.close() if self.is_open else self.open()

    def clear(self) -> None:
        """清空选中。"""
        if self.multiple:
            if not self._checked:
                return
            self._checked = set()
        else:
            if self._active is None:
                return
            self._active = None
        self._write_back()

    def clear_checked_nodes(self) -> None:
        """清空多选勾选（Element 同名方法的别名）。"""
        self.clear()

    def _show_clear(self) -> bool:
        """框内 × 只在真有选中时出现。

        ``PanelField`` 的默认判断是 ``value is not None``，而多选清空后的值是
        ``[]`` —— 它不是 ``None``，于是 × 会一直挂在框里，点了又没有可清的东西。
        """
        has_value = bool(self._checked) if self.multiple else self._active is not None
        return self.clearable and not self.disabled and has_value

    def get_checked_nodes(self, leaf_only: bool = False) -> list[CascaderNode]:
        """当前选中的节点列表（多选取勾选集，单选取 0/1 个）。

        Args:
            leaf_only: 只要叶子节点。
        """
        if self.multiple:
            paths = self._checked_paths()
        else:
            paths = [self._active] if self._active is not None else []
        return [
            self._by_path[p] for p in paths if not leaf_only or self._by_path[p].is_leaf
        ]

    def select(self, path: Sequence[Any], close: bool = True) -> None:
        """按路径选中（单选）；``close=False`` 保持面板展开。多选请用 ``set_checked_paths``。"""
        p = self._to_path(list(path))
        if p is None:
            return
        node = self._by_path[p]
        if node.disabled:
            return
        self._active = p
        self._write_back()
        if close:
            self.close()

    def set_checked_paths(self, paths: Iterable[Sequence[Any]]) -> None:
        """按路径集合设置多选勾选（自动级联 / 收敛，非法路径忽略）。"""
        if not self.multiple:
            return
        picked = {
            p
            for p in (self._to_path(list(path)) for path in paths)
            if p is not None and not self._by_path[p].disabled
        }
        self._checked = picked
        if not self.check_strictly:
            for path in list(picked):
                self._subtree(path, True)
        self._refresh_states()
        self._write_back()

    # ------------------------------------------------------------------
    # 展示
    # ------------------------------------------------------------------
    @property
    def _display_text(self) -> str:
        """单选框内文本：完整路径或最后一级。"""
        if self._active is None:
            return ""
        nodes = self._nodes_on(self._active)
        if not nodes:
            return ""
        return (
            self.separator.join(n.label for n in nodes)
            if self.show_all_levels
            else nodes[-1].label
        )

    def _nodes_on(self, path: Path) -> list[CascaderNode]:
        """路径上从根到该节点的所有节点。

        注意 ``_by_path`` 的键是**路径前缀元组**，不是单个 value ——
        逐前缀查，别拿 value 当 key（否则显示恒为空，自检抓过）。
        """
        nodes: list[CascaderNode] = []
        for i in range(len(path)):
            node = self._by_path.get(path[: i + 1])
            if node is not None:
                nodes.append(node)
        return nodes

    def _path_label(self, path: Path) -> str:
        """过滤列表里一行显示的完整路径文本。"""
        return self.separator.join(n.label for n in self._nodes_on(path))

    # ------------------------------------------------------------------
    # 多选：级联
    # ------------------------------------------------------------------
    def _children_of(self, path: Path) -> list[Path]:
        node = self._by_path.get(path)
        if node is None:
            return []
        return [
            c
            for c in ((path + (ch.value,)) for ch in node.children)
            if c in self._by_path
        ]

    def _subtree(self, path: Path, value: bool) -> None:
        """把勾选铺到整棵子树（禁用节点连同子树跳过）—— 迭代。"""
        stack = [path]
        while stack:
            current = stack.pop()
            node = self._by_path.get(current)
            if node is None or node.disabled:
                continue
            if value:
                self._checked.add(current)
            else:
                self._checked.discard(current)
            stack.extend(self._children_of(current))

    def _refresh_states(self) -> None:
        """由勾选集合反推每个可见节点的三态（后序，子先于父）。"""
        self._states.clear()

        def visit(path: Path) -> _Check:
            state = self._states.get(path)
            if state is not None:
                return state
            node = self._by_path[path]
            kids = self._children_of(path)
            if self.check_strictly or node.disabled or not kids:
                state = _CHECKED if path in self._checked else _UNCHECKED
            else:
                child_states = [visit(k) for k in kids if not self._by_path[k].disabled]
                usable = child_states or [_UNCHECKED]
                if all(s is _CHECKED for s in usable):
                    state = _CHECKED
                    self._checked.add(path)
                elif any(s is not _UNCHECKED for s in usable):
                    state = _HALF
                    self._checked.discard(path)
                else:
                    state = _UNCHECKED
                    self._checked.discard(path)
            self._states[path] = state
            return state

        for root in self._roots:
            visit((root.value,))
        # 收敛后只留"勾选即存在"的路径，防止僵尸 key
        self._checked = {p for p in self._checked if p in self._by_path}

    def _checked_paths(self) -> list[Path]:
        """勾选路径按树先序列出。"""
        if self.check_strictly:
            return [p for p in self._by_path if p in self._checked]
        self._refresh_states()
        return [p for p in self._by_path if self._states.get(p) is _CHECKED]

    def _toggle_check(self, path: Path) -> None:
        """勾选 / 取消勾选某节点（含级联），并回写广播。"""
        if self.check_strictly:
            if path in self._checked:
                self._checked.discard(path)
            else:
                self._checked.add(path)
        else:
            self._refresh_states()
            target = self._states.get(path) is _CHECKED
            self._subtree(path, not target)
        self._refresh_states()
        self._write_back()

    # ------------------------------------------------------------------
    # 面板行为
    # ------------------------------------------------------------------
    def _expand(self, path: Path) -> None:
        """把展开链推进到 ``path``（其子级成为新的一列）。"""
        node = self._by_path.get(path)
        if node is None or node.is_leaf:
            return
        depth = len(path) - 1
        self._chain = self._chain[:depth] + [path]
        self._hover = None
        self.notify()  # type: ignore[attr-defined]
        if self.on_expand_change:
            self.on_expand_change(list(path))

    def _pick(self, path: Path) -> None:
        """行点击语义：有子级就展开；叶子（或严格模式任意级）就选中。"""
        node = self._by_path.get(path)
        if node is None or node.disabled:
            return
        if not node.is_leaf:
            self._expand(path)
            return
        if self.multiple:
            self._toggle_check(path)
            return
        self._active = path
        self._write_back()
        self.close()

    def _on_row_enter(self, path: Path) -> None:
        """悬停展开（仅 ``expand_trigger="hover"`` 且有子级）。"""
        if self.expand_trigger != "hover" or self.disabled:
            return
        node = self._by_path.get(path)
        if node is None or node.disabled or node.is_leaf:
            return
        if self._chain and self._chain[-1] == path:
            return
        self._expand(path)

    def _on_query_change(self, e: ft.ControlEvent) -> None:
        """过滤词键入：只更新面板，不动选中态。"""
        # 用 control.value 而不是 e.data：前者是控件的真值，后者在部分事件里
        # 是字符串化的载荷，拿它当文本会出现"输入一个字符、过滤词变成 true"。
        self._query = str(e.control.value or "")
        self.notify()  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # 匹配
    # ------------------------------------------------------------------
    def _matched(self, node: CascaderNode, keyword: str) -> bool:
        if self.filter_method is not None:
            return bool(self.filter_method(node, keyword))
        return keyword in node.label.casefold()

    def _matched_paths(self) -> list[Path]:
        """命中的节点路径（先序）。禁用节点连同子树跳过（与列内一致）。"""
        keyword = self._query.casefold().strip()
        if not keyword:
            return []
        hits: list[Path] = []
        stack = [((node.value,), node) for node in reversed(self._roots)]
        while stack:
            path, node = stack.pop()
            if node.disabled:
                continue
            if self._matched(node, keyword):
                hits.append(path)
            for child in reversed(node.children):
                stack.append((path + (child.value,), child))
        return hits

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    @ft.component
    def ui(self) -> ft.Control:
        """构建级联选择器 UI。"""
        use_t()
        page = ft.context.page
        field = self._build_field(self._inner_field(), self._trailing_icon())
        panel = self._build_panel()
        floating = self._should_float(page)

        if floating:
            body: ft.Control = field
        elif self.is_open and not self.disabled:
            body = ft.Column(controls=[field, panel], spacing=PANEL_GAP)
        else:
            body = field

        panel_w, panel_h = self._panel_size()
        left, top, bottom = place_panel(
            page, self._anchor, self._field_h, panel_w, panel_h
        )
        use_float_layer(
            page=page,
            visible=floating and self.is_open and not self.disabled,
            left=left,
            top=top,
            bottom=bottom,
            content=panel,
            on_dismiss=self.close,
            hole=self._hole(),
        )
        return self._with_label(body)

    # ---- 折叠态 ----
    def _trailing_icon(self) -> ft.Control:
        """右侧图标：面板展开 / 收起。用语义图标，与 SelectBox / ColorPicker 同一形状。"""
        return ft.Icon(
            PANEL_CLOSE if self.is_open else PANEL_OPEN,
            size=ICON_SIZE["lg"],
            color=DISABLED_FG if self.disabled else ft.Colors.ON_SURFACE_VARIANT,
        )

    def _inner_field(self) -> ft.Control:
        """框内内容：多选是 Chip 行，单选是文本；过滤框只在面板展开后出现
        （el 的模型：收起时显示已选路径，展开后清空供键入搜索）。"""
        if self.multiple:
            chips = self._chips()
            if not self.filterable or not self.is_open:
                return ft.Row(
                    spacing=4,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    scroll=ft.ScrollMode.AUTO,
                    controls=chips or [self._hint()],
                )
            return ft.Row(
                spacing=4,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
                controls=chips + [self._search_box(fixed_w=90)],
            )
        if not self.filterable or not self.is_open:
            text = self._display_text
            if text:
                return ft.Text(
                    text,
                    size=ITEM_SIZE,
                    color=self._fg,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                )
            return self._hint()
        # filterable 且已展开：框内清空供键入
        return self._search_box()

    def _hint(self) -> ft.Control:
        """占位文本。"""
        return ft.Text(
            self.placeholder or t("ui.cascader.placeholder"),
            size=ITEM_SIZE,
            color=ft.Colors.ON_SURFACE_VARIANT,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )

    def _search_box(self, fixed_w: float | None = None) -> ft.Control:
        """过滤输入框。只在面板展开后出现（见 :meth:`_inner_field`），所以
        这里不需要 ``ignore_pointers`` 的收起态穿透逻辑。"""
        return ft.TextField(
            value=self._query,
            width=fixed_w,
            expand=None if fixed_w else True,
            border=ft.NoInputBorder(),
            filled=False,
            dense=True,
            text_size=ITEM_SIZE,
            color=self._fg,
            content_padding=ft.Padding.symmetric(vertical=6),
            hint_text=self.placeholder or t("ui.cascader.placeholder"),
            hint_style=ft.TextStyle(size=ITEM_SIZE, color=ft.Colors.ON_SURFACE_VARIANT),
            read_only=self.disabled,
            on_change=None if self.disabled else self._on_query_change,
        )

    def _chips(self) -> list[ft.Control]:
        """多选的 Chip 行：默认全部，``collapse_tags`` 只留第一个 + "+n"。"""
        paths = self._checked_paths()
        if not paths:
            return []
        shown = paths[:1] if (self.collapse_tags and len(paths) > 1) else paths
        chips = [self._chip(p) for p in shown]
        hidden = len(paths) - len(shown)
        if hidden > 0:
            chips.append(
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                    content=ft.Text(
                        f"+{hidden}", size=12, color=ft.Colors.ON_SURFACE_VARIANT
                    ),
                )
            )
        return chips

    def _chip(self, path: Path) -> ft.Control:
        """单个已选项 Chip：文本（可截断）+ ×；点 × 移除该项并广播。"""
        node = self._by_path.get(path)
        label = (
            node.label
            if (node is not None and not self.show_all_levels)
            else self._path_label(path)
        )
        label = _clip(label)
        removable = not (self.disabled or (node is not None and node.disabled))
        return ft.Container(
            height=22,
            padding=ft.Padding.only(left=8, right=2),
            bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.ON_SURFACE),
            border_radius=ft.BorderRadius.all(4),
            content=ft.Row(
                spacing=2,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text(
                        label,
                        size=12,
                        color=ft.Colors.ON_SURFACE,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.GestureDetector(
                        on_tap=None
                        if not removable
                        else (lambda _e, p=path: self._remove(p)),
                        content=ft.Container(
                            padding=ft.Padding.all(2),
                            border_radius=ft.BorderRadius.all(3),
                            content=ft.Icon(
                                ft.Icons.CLOSE,
                                size=ICON_SIZE["sm"],
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                        ),
                    ),
                ],
            ),
        )

    def _remove(self, path: Path) -> None:
        """移除一个已选项（Chip ×）。"""
        if self.check_strictly:
            self._checked.discard(path)
            self._refresh_states()
            self._write_back()
        else:
            self._toggle_check(path)

    # ---- 面板 ----
    def _panel_size(self) -> tuple[float, float]:
        """估算面板宽高（浮层定位用）。列模式下宽度随级数增长。"""
        if self._query.strip():
            rows = min(max(len(self._matched_paths()), 1), MAX_ROWS)
            width = PANEL_PAD * 2 + COL_W + 2
            return width, PANEL_PAD * 2 + 2 + rows * ITEM_H
        columns = 1
        rows = MIN_ROWS
        if self._roots:
            # 高度按当前各列里最多行数定（夹在 MIN/MAX_ROWS），宽度随级数走
            counts = [len(self._roots)]
            counts.extend(len(self._children_of(p)) for p in self._chain)
            columns = len(counts)
            rows = min(max(max(counts), MIN_ROWS), MAX_ROWS)
        width = PANEL_PAD * 2 + COL_W * columns + 2
        return width, PANEL_PAD * 2 + 2 + rows * ITEM_H

    def _build_panel(self) -> ft.Control:
        """面板：过滤态是扁平命中列表；否则是多列。"""
        width, height = self._panel_size()
        if not self._roots:
            body: ft.Control = self._empty()
        elif self._query.strip():
            body = self._filter_list(height)
        else:
            body = self._columns(height)
        return self._panel_shell(width, body)

    def _empty(self) -> ft.Control:
        # 与选项行同一列宽、两行高 —— 空态不该让面板收缩成一条。
        return empty_line(t("ui.cascader.empty"), width=COL_W, height=ITEM_H * 2)

    def _columns(self, height: float) -> ft.Control:
        """多列面板：每级一列。"""
        chain = self._chain
        cols: list[ft.Control] = []
        level_items: list[list[Path]] = [
            [p for p in ((node.value,) for node in self._roots) if p in self._by_path]
        ]
        for i in range(len(chain)):
            level_items.append(self._children_of(chain[i]))
        for items in level_items:
            cols.append(self._column(items, height))
        return ft.Row(spacing=0, controls=cols)

    def _column(self, items: list[Path], height: float) -> ft.Control:
        """一列：可滚动的行列表，右侧 1px 分隔线。"""
        rows = [self._row(p) for p in items]
        return ft.Container(
            width=COL_W,
            height=height,
            border=ft.Border.only(right=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
            content=ft.ListView(spacing=0, padding=0, controls=rows),
        )

    def _state_of(self, path: Path) -> _Check:
        """某节点当前的复选三态（严格模式直接查集合，级联模式查缓存）。"""
        if self.check_strictly:
            return _CHECKED if path in self._checked else _UNCHECKED
        return self._states.get(path, _UNCHECKED)

    def _row(self, path: Path) -> ft.Control:
        """面板里的一行：多选带复选框，严格单选带单选点，有子级带右箭头。"""
        node = self._by_path[path]
        disabled = node.disabled or self.disabled
        state = self._state_of(path)

        controls: list[ft.Control] = []
        if self.multiple:
            controls.append(self._check_hit(path, state, disabled))
        elif self.check_strictly:
            controls.append(self._radio_hit(path, disabled))

        active = path in self._chain or path == self._active
        label_color = (
            DISABLED_FG
            if disabled
            else ft.Colors.PRIMARY
            if active
            else ft.Colors.ON_SURFACE
        )
        controls.append(
            ft.Text(
                node.label,
                size=ITEM_SIZE,
                weight=ft.FontWeight.W_500 if active else None,
                color=label_color,
                expand=True,
                max_lines=1,
                overflow=ft.TextOverflow.ELLIPSIS,
            )
        )
        if not node.is_leaf:
            controls.append(
                ft.Icon(
                    ft.Icons.KEYBOARD_ARROW_RIGHT,
                    size=16,
                    color=DISABLED_FG if disabled else ft.Colors.ON_SURFACE_VARIANT,
                )
            )
        elif not self.multiple and path == self._active:
            controls.append(ft.Icon(ft.Icons.CHECK, size=16, color=ft.Colors.PRIMARY))

        hover_key = f"row:{path}"
        row = ft.Container(
            height=ITEM_H,
            padding=ft.Padding.only(left=ITEM_PAD_H, right=8),
            bgcolor=HOVER_BG if self._hover == hover_key and not disabled else None,
            content=ft.Row(
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=controls,
            ),
        )
        if disabled:
            return row
        # 悬停一律走 enter / exit：GestureDetector 的 on_hover 载荷不可靠（Tree 踩过）；
        # hover 展开与悬停底色共用 enter 一个入口。
        expand_on_hover = self.expand_trigger == "hover" and not node.is_leaf
        return ft.GestureDetector(
            on_tap=lambda _e, p=path: self._pick(p),
            on_enter=lambda _e, p=path, ex=expand_on_hover: (
                self._hover_key(f"row:{p}", True),
                self._on_row_enter(p) if ex else None,
            ),
            on_exit=lambda _e, p=path: self._hover_key(f"row:{p}", False),
            content=row,
        )

    def _check_hit(self, path: Path, state: _Check, disabled: bool) -> ft.Control:
        """多选复选框（命中区比图形大一点，好点）。"""
        box = ft.Container(
            width=16,
            height=16,
            border_radius=ft.BorderRadius.all(4),
            border=ft.Border.all(1.5, DISABLED_FG if disabled else ft.Colors.OUTLINE),
            bgcolor=(
                ft.Colors.with_opacity(0.5, ft.Colors.PRIMARY)
                if (state is _HALF and not disabled)
                else ft.Colors.PRIMARY
                if (state is _CHECKED and not disabled)
                else None
            ),
            content=(
                ft.Icon(
                    ft.Icons.CHECK if state is _CHECKED else ft.Icons.REMOVE,
                    size=12,
                    color=ft.Colors.ON_PRIMARY,
                )
                if state is not _UNCHECKED
                else None
            ),
        )
        if disabled:
            return box
        return ft.GestureDetector(
            on_tap=lambda _e, p=path: self._toggle_check(p),
            content=ft.Container(
                width=24, height=ITEM_H, alignment=ft.Alignment.CENTER_LEFT, content=box
            ),
        )

    def _radio_hit(self, path: Path, disabled: bool) -> ft.Control:
        """严格单选的单选点（任意级可选）。"""
        selected = self._active == path
        color = (
            DISABLED_FG
            if disabled
            else (ft.Colors.PRIMARY if selected else ft.Colors.OUTLINE)
        )
        dot = ft.Container(
            width=16,
            height=16,
            border_radius=ft.BorderRadius.all(8),
            border=ft.Border.all(1.5, color),
            alignment=ft.Alignment.CENTER,
            content=(
                ft.Container(
                    width=8,
                    height=8,
                    bgcolor=ft.Colors.PRIMARY,
                    border_radius=ft.BorderRadius.all(4),
                )
                if selected
                else None
            ),
        )
        if disabled:
            return dot
        return ft.GestureDetector(
            on_tap=lambda _e, p=path: self._pick_strict(p),
            content=ft.Container(
                width=24, height=ITEM_H, alignment=ft.Alignment.CENTER_LEFT, content=dot
            ),
        )

    def _pick_strict(self, path: Path) -> None:
        """严格单选：点单选点直接选中（叶子也收面板）。"""
        node = self._by_path.get(path)
        if node is None or node.disabled:
            return
        self._active = path
        self._write_back()
        self.close()

    def _filter_list(self, height: float) -> ft.Control:
        """过滤态：扁平命中列表，显示完整路径并高亮命中子串。"""
        paths = self._matched_paths()
        if not paths:
            return self._empty()
        keyword = self._query.casefold().strip()
        rows: list[ft.Control] = []
        for path in paths:
            label = self._path_label(path)
            lower = label.casefold()
            idx = lower.find(keyword)
            spans: list[ft.TextSpan] = []
            if idx < 0:
                spans.append(ft.TextSpan(label))
            else:
                if idx:
                    spans.append(ft.TextSpan(label[:idx]))
                spans.append(
                    ft.TextSpan(
                        label[idx : idx + len(self._query.strip())],
                        style=ft.TextStyle(
                            color=ft.Colors.PRIMARY, weight=ft.FontWeight.W_600
                        ),
                    )
                )
                rest = idx + len(self._query.strip())
                if rest < len(label):
                    spans.append(ft.TextSpan(label[rest:]))
            rows.append(self._filter_row(path, ft.Text(spans=spans, size=ITEM_SIZE)))
        return ft.Container(
            width=COL_W,
            height=height,
            content=ft.ListView(spacing=0, padding=0, controls=rows),
        )

    def _filter_row(self, path: Path, label: ft.Control) -> ft.Control:
        hover_key = f"frow:{path}"
        node = self._by_path[path]
        disabled = node.disabled or self.disabled
        row = ft.Container(
            height=ITEM_H,
            padding=ft.Padding.only(left=ITEM_PAD_H, right=8),
            bgcolor=HOVER_BG if self._hover == hover_key and not disabled else None,
            content=ft.Row(
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[label, ft.Container(expand=True)],
            ),
        )
        if disabled:
            return row
        return ft.GestureDetector(
            on_tap=lambda _e, p=path: self._pick_from_filter(p),
            on_enter=lambda _e, p=path: self._hover_key(f"frow:{p}", True),
            on_exit=lambda _e, p=path: self._hover_key(f"frow:{p}", False),
            content=row,
        )

    def _pick_from_filter(self, path: Path) -> None:
        """过滤列表点击：可选中就选中收起；有子级则退出过滤并展开到该级。"""
        node = self._by_path.get(path)
        if node is None or node.disabled:
            return
        if node.is_leaf or self.check_strictly:
            if self.multiple:
                self._toggle_check(path)
                return
            self._active = path
            self._write_back()
            self.close()
            return
        self._query = ""
        self._expand(path)


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
_REGIONS = [
    {
        "label": "浙江省",
        "children": [
            {
                "label": "杭州市",
                "children": [
                    {"label": "西湖区"},
                    {"label": "滨江区"},
                    {"label": "余杭区"},
                ],
            },
            {"label": "宁波市", "children": [{"label": "海曙区"}, {"label": "鄞州区"}]},
        ],
    },
    {
        "label": "广东省",
        "children": [
            {"label": "广州市", "children": [{"label": "天河区"}, {"label": "越秀区"}]},
            {"label": "深圳市", "children": [{"label": "南山区"}, {"label": "福田区"}]},
        ],
    },
    {
        "label": "江苏省",
        "children": [
            {"label": "南京市", "children": [{"label": "鼓楼区"}, {"label": "玄武区"}]},
            {
                "label": "苏州市",
                "children": [{"label": "姑苏区"}, {"label": "工业园区"}],
            },
        ],
    },
]


def _caption(text: str) -> ft.Control:
    return ft.Text(text, size=FONT_SIZE["small"], color=ft.Colors.ON_SURFACE_VARIANT)


def _as_text(value: Any) -> str:
    """把对外 value 折成一行可读文本（单选是路径，多选是路径的列表）。"""
    if value is None or value == [] or value == "":
        return "未选择"
    if isinstance(value, (list, tuple)):
        if value and isinstance(value[0], (list, tuple)):
            return " · ".join(" / ".join(str(part) for part in item) for item in value)
        return " / ".join(str(part) for part in value)
    return str(value)


@ft.component
def _echo(select: Cascader) -> ft.Control:
    """回显对外值：这一行才是提交给后端的形状，框里的路径只是展示。"""
    return _caption(f"提交值：{_as_text(select.value)}")


@ft.component
def _basic() -> ft.Control:
    """省 → 市 → 区三级；点父级只展开，点到最后一级才落定。"""
    select = ft.use_memo(
        lambda: Cascader(
            label="收货地区",
            options=_REGIONS,
            value=["浙江省", "杭州市", "西湖区"],
            is_required=True,
        ),
        [],
    )
    return ft.Column(spacing=10, controls=[select.ui(), _echo(select)])


@ft.component
def _strict() -> ft.Control:
    """同一份数据，check_strictly 打开后任意一级都能选，框里只显示末级。"""
    select = ft.use_memo(
        lambda: Cascader(
            label="归属大区",
            options=_REGIONS,
            check_strictly=True,
            show_all_levels=False,
            value=["广东省"],
        ),
        [],
    )
    leaf_only = ft.use_memo(
        lambda: Cascader(label="对比：默认只选叶子", options=_REGIONS), []
    )
    return ft.Column(
        spacing=10,
        controls=[
            select.ui(),
            leaf_only.ui(),
            _echo(select),
        ],
    )


@ft.component
def _filter() -> ft.Control:
    """展开后直接在框内键入，面板换成扁平命中列表并高亮命中片段。"""
    select = ft.use_memo(
        lambda: Cascader(label="搜索地区", options=_REGIONS, filterable=True),
        [],
    )
    return ft.Column(spacing=10, controls=[select.ui(), _echo(select)])


_BASIC_CODE = """options = [
    {"label": "浙江省", "children": [
        {"label": "杭州市", "children": [{"label": "西湖区"}, {"label": "滨江区"}]},
        {"label": "宁波市", "children": [{"label": "海曙区"}]},
    ]},
]

select = Cascader(
    label="收货地区",
    options=options,
    value=["浙江省", "杭州市", "西湖区"],   # 完整路径 → 框内显示「浙江省 / 杭州市 / 西湖区」
)
Column([select.ui(), Text(f"提交值：{select.value}")])"""

_STRICT_CODE = """select = Cascader(
    options=options,
    check_strictly=True,     # 父级也能直接选，不再级联到子树
    show_all_levels=False,   # 框内只显示最后一级
    value=["广东省"],
)"""

_FILTER_CODE = """select = Cascader(
    options=options,
    filterable=True,         # 展开后框内可键入，面板切成扁平命中列表
)"""


SPEC = Spec(
    name="Cascader",
    summary="按「省 → 市 → 区」逐级点选，框内回显完整路径。",
    definition=(
        "级联选择器把一棵层级树拆成并排的几列：点开一级，右边长出下一级，点到叶子"
        "才落定。它解决的是「这条数据有层级、但用户仍要看清全路径」—— 一条平铺的下拉"
        "装不下父子关系，三个联动的下拉又要求用户在控件之间来回挪焦点。默认只有叶子"
        "可选，因为父级本身通常不是一个可提交的答案。"
    ),
    anatomy=[
        ("框体", "40px 高的输入框，单行显示完整路径（超宽省略），展开时描边转主色。"),
        ("列", "每级一列 180px，列间一根发丝线；当前展开的那一级文字转主色并加粗。"),
        ("父级行", "右侧一个灰色右箭头，点它只展开下一列，不会落定。"),
        ("叶子行", "没有下级；单选时点下去即选中并收起，选中行尾部出现对勾。"),
        ("清除", "有选中时框内出现 ×，一次清空整条路径（多选清空全部勾选）。"),
        ("搜索", "filterable 时展开后可直接键入，面板换成扁平命中列表并显示完整路径。"),
    ],
    when=[
        "行政区划、组织架构、商品类目这类天然的层级字段",
        "用户需要确认完整路径，只给最后一级不足以说明问题",
        "层级固定在两三层，并排的列放得下",
    ],
    avoid=[
        "选项是平铺的一层：用 SelectBox，套上级联只多了两次点击",
        "层级超过四层或单层节点上百：用 Tree，并排的列会横向溢出屏幕",
        "要在一棵树里任意勾选多个分支：用 Tree 的多选，级联表达的仍是「一条路径」",
    ],
    examples=[
        Example(
            "省市区三级",
            _basic,
            hint="预置了一条完整路径；点开面板时列已经展开到「西湖区」所在的那一级。",
            code=_BASIC_CODE,
        ),
        Example(
            "任意级可选",
            _strict,
            hint="上面那个开了 check_strictly，父级也能直接选；下面那个是默认行为，点父级只会展开。",
            code=_STRICT_CODE,
        ),
        Example(
            "可搜索",
            _filter,
            hint="展开后键入「南」，面板切成扁平列表，命中片段用主色高亮。",
            code=_FILTER_CODE,
        ),
    ],
    api=[
        Api("options", "list[Any]", "[]", "选项树：dict / CascaderNode / 标量均可混用"),
        Api("value", "Any", "None", "当前值：单选为路径列表，多选为路径列表的列表"),
        Api("multiple", "bool", "False", "多选：复选框父子级联，框内以 Chip 展示"),
        Api("check_strictly", "bool", "False", "父子不关联，任意一级都可直接选"),
        Api(
            "emit_path", "bool", "True", "对外值给完整路径（False 只给该节点的 value）"
        ),
        Api("show_all_levels", "bool", "True", "框内显示完整路径（False 只显示末级）"),
        Api("separator", "str", '" / "', "路径分隔符，框内文本与 Chip 都用它"),
        Api("filterable", "bool", "False", "展开后可在框内键入，面板切成扁平命中列表"),
        Api("clearable", "bool", "True", "有选中时显示框内 ×，一次清空"),
        Api(
            "on_change",
            "Callable[[Any], None] | None",
            "None",
            "选中变化回调，收到的是对外形式的值",
        ),
    ],
    notes=[
        tip(
            "CascaderNode 的 children 现在会递归归一：之前只在 dict 分支里递归，"
            "往 CascaderNode 里塞 dict 子节点，展开到那一级就会抛 AttributeError。"
        ),
        info(
            "多选装入初始值后立刻重算一次三态，否则面板第一次打开时已勾选的节点全是"
            "空框；框内的 × 也改成「真有选中才出现」—— 多选清空后的 [] 不是 None，"
            "原来的判据会让 × 一直挂着。"
        ),
        warn(
            "不做键盘导航：flet 1.0 的 KeyboardListener 在重绘后会把焦点交给兄弟节点，"
            "没有稳定的控件级按键钩子。"
        ),
    ],
    tags=("级联", "省市区", "树形选择", "cascader", "地区"),
)


if __name__ == "__main__":
    run(SPEC)
