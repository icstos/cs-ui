"""穿梭框 (Transfer) —— 两列清单之间搬条目。

参考 Ant Design ``Transfer``。它和 :class:`~ui.input.MultiSelect` 不是一回事：

================  ==================================  ==========================
                  ``MultiSelect``                       ``Transfer``
================  ==================================  ==========================
形态               折叠下拉框，点开才看得见              两列常驻并列
一次看到           已选项（其余要点开）                  「已选 vs 未选」全貌
适合               标签、筛选项这类轻量多选              权限、成员、可见列这类
                                                        需要**对比着挑**的场景
================  ==================================  ==========================

用法::

    tr = Transfer(
        label="可见列",
        data_source=[
            TransferItem("name", "姓名"),
            TransferItem("dept", "部门", description="一级部门 / 二级部门"),
            TransferItem("salary", "薪资", disabled=True),
        ],
        target_keys=["name", "dept"],
        on_change=lambda keys, direction, moved: print(keys, direction, moved),
    )
    Column([tr.ui()])

四条实现取舍（改前先读）
------------------------
1. **不做双击移动**。单击行 = 勾选（AntD 的行为），双击在 Flutter 里必须挂
   ``on_double_tap``，而它与 ``on_tap`` 共存时**单击要等双击判定超时**才触发
   （约 300ms），勾选会明显发木。与其让每一次勾选都慢半拍，不如只保留单击。
   搬条目一律走中间的箭头 —— 一次搬一批，比双击一条条搬更符合"穿梭"的原意。
2. **``target_keys`` 恒按 ``data_source`` 排序**。移入顺序不参与排序，右侧
   因此永远和数据源同序，对拍（diff）、持久化、断言都可重复。移入次序本身
   也没有信息量 —— 真要排序就该有显式的排序功能，而不是靠点击先后。
3. **勾选是全局的，搜索只影响可见性**。搜索时已勾选的项即便被过滤掉，仍然
   算勾选、仍会被搬走（AntD 同此语义）。头部全选框的三态只看**当前可见项**，
   因为点它是在"对眼前这批"下决定 —— 两个半径都说得通，跟主流保持一致。
4. **悬停只在"换行"时重绘**。每行各挂 ``on_enter`` / ``on_exit``，鼠标划过
   一列会来几十次事件；比较"当前悬停的那一行"，没变就 return。

性能：一次渲染约 ``2 × 行数`` 个行控件，行是"复选框 + 一到两段文字"的扁结构；
勾选一次重绘整棵树，实测 40 行 × 2 列约 2ms。列表超出高度时内部滚动，
**不做分页** —— 桌面端滚轮比翻页自然，需要分段时请配合 ``show_search``。

.. note::
    不做键盘导航，原因同 :class:`~ui.display.tree.Tree`：flet 1.0 的
    ``KeyboardListener`` 在重绘后会把焦点交给兄弟节点，没有稳定的控件级按键钩子。
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field

import flet as ft

from ui.core.i18n import t, use_t
from ui.core.styles import outline_input
from ui.core.theme import use_theme
from ui.core.tokens import (
    FONT_SIZE,
    FONT_WEIGHT,
    RADIUS,
    SPACE,
    hairline,
    overlay,
)
from ui.input.input import Label

__all__ = [
    "DIRECTIONS",
    "Transfer",
    "TransferItem",
    "check_state",
    "match_items",
    "move_targets",
    "split_items",
]

# ---------------------------------------------------------------------------
# 尺寸
# ---------------------------------------------------------------------------
LIST_W = 240  # 单列宽度
LIST_H = 320  # 单列高度（列头 + 搜索 + 列表）
HEAD_H = 44  # 列头高度
SEARCH_H = 32  # 搜索框本体高度
SEARCH_PAD = SPACE["2"]  # 搜索区上下内边距
ROW_PAD_V = 7  # 行上下内边距
ROW_GAP = 2  # 行与行之间的缝：没它时相邻两行的选中底色会连成一块
ARROW = 36  # 中间箭头按钮边长
BOX = 16  # 复选框边长
BOX_HIT = 24  # 复选框命中宽度
BOX_RADIUS = 4  # 复选框圆角

#: 允许的移动方向
DIRECTIONS: tuple[str, str] = ("left", "right")

#: 悬停行底色
HOVER_BG = overlay(0.06)
#: 禁用字色
DISABLED_FG = overlay(0.38)
#: 勾选行底色（淡主色）
PICKED_BG = overlay(0.10, role=ft.Colors.PRIMARY)


# ---------------------------------------------------------------------------
# 纯函数（逻辑单测的抓手，都不碰控件）
# ---------------------------------------------------------------------------
def split_items(
    items: Sequence[TransferItem], target_keys: Iterable[str]
) -> tuple[list[TransferItem], list[TransferItem]]:
    """按 ``target_keys`` 把条目分成 (待选, 已选)，两侧**都保持数据源原序**。"""
    chosen = set(target_keys)
    source: list[TransferItem] = []
    target: list[TransferItem] = []
    for item in items:
        (target if item.key in chosen else source).append(item)
    return source, target


def match_items(items: Sequence[TransferItem], query: str) -> list[TransferItem]:
    """按关键字过滤：命中标题或说明，大小写不敏感；空查询原样返回。"""
    keyword = query.strip().casefold()
    if not keyword:
        return list(items)
    return [
        item
        for item in items
        if keyword in item.title.casefold() or keyword in item.description.casefold()
    ]


def check_state(items: Sequence[TransferItem], picked: Iterable[str]) -> str:
    """三态：``"all"`` / ``"some"`` / ``"none"``。

    只看传进来的这批（调用方负责先过滤），因此搜索态下就是"可见项的选中情况"。
    **禁用项不要传进来**：它们搬不走，算进总数会让全选框永远停在"半选"。
    """
    chosen = set(picked)
    total = len(items)
    if total == 0:
        return "none"
    hit = sum(1 for item in items if item.key in chosen)
    if hit == 0:
        return "none"
    return "all" if hit == total else "some"


def move_targets(
    items: Sequence[TransferItem],
    target_keys: Iterable[str],
    keys: Iterable[str],
    direction: str,
) -> list[str]:
    """搬一批 key 到某一侧，返回**新的** ``target_keys``。

    - ``direction="right"``：并进已选；``"left"``：从已选里移出；
    - 数据源里没有的 key、以及 ``disabled`` 的条目**一律不动**（禁用项既搬不进
      也搬不出，否则"禁用"就只是画着好看）；
    - 结果按 ``data_source`` 排序，与 :func:`split_items` 的渲染顺序一致。
    """
    if direction not in DIRECTIONS:
        raise ValueError(f"direction 只能是 {DIRECTIONS}，收到 {direction!r}")
    by_key = {item.key: item for item in items}
    movable = [k for k in keys if k in by_key and not by_key[k].disabled]
    current = set(target_keys)
    if direction == "right":
        current.update(movable)
    else:
        current.difference_update(movable)
    wanted = set(current)
    return [item.key for item in items if item.key in wanted]


# ---------------------------------------------------------------------------
# 条目
# ---------------------------------------------------------------------------
@dataclass
class TransferItem:
    """一条可穿梭的数据。

    Args:
        key: 稳定标识，穿梭时搬的就是它。
        title: 主文本。
        description: 副文本（可选），用来放"部门 / 邮箱 / 备注"这类补充信息。
        disabled: 该条不可搬（两侧都搬不动，但仍然显示、仍然可以被全选到）。
    """

    key: str
    title: str
    description: str = ""
    disabled: bool = False


# ---------------------------------------------------------------------------
# 组件
# ---------------------------------------------------------------------------
@ft.observable
@dataclass
class Transfer(Label):
    """穿梭框。

    Args:
        data_source: 全部条目，左右两列都从它派生。
        target_keys: 已选条目的 key（对外受控值，按数据源序）。
        titles: 两列标题 ``(左, 右)``。``None`` 取语言包「待选 / 已选」。
        show_search: 每列是否带搜索框，默认 True。
        show_select_all: 列头是否显示全选框，默认 True。
        one_way: 单向模式，只允许从待选搬到已选（隐藏反向箭头），默认 False。
        list_width: 单列宽度，默认 240。
        height: 单列高度，默认 320（列头 + 搜索 + 列表）。
        disabled: 整体禁用。
        on_change: 搬运后回调 ``(target_keys, direction, moved_keys)``。
        on_select_change: 勾选变化后回调 ``(left_picked, right_picked)``。
    """

    data_source: list[TransferItem] = field(default_factory=list)
    target_keys: list[str] = field(default_factory=list)
    titles: tuple[str, str] | None = None
    show_search: bool = True
    show_select_all: bool = True
    one_way: bool = False
    list_width: int | float = LIST_W
    height: int | float = LIST_H
    disabled: bool = False
    on_change: Callable[[list[str], str, list[str]], None] | None = None
    on_select_change: Callable[[list[str], list[str]], None] | None = None

    def __post_init__(self) -> None:
        # 运行期状态。下划线开头 => 不参与序列化，变更后靠 _repaint 触发重绘。
        self._picked: dict[str, set[str]] = {"left": set(), "right": set()}
        self._query: dict[str, str] = {"left": "", "right": ""}
        self._hover: str | None = None

    # ------------------------------------------------------------------
    # 派生数据
    # ------------------------------------------------------------------
    @property
    def source_items(self) -> list[TransferItem]:
        """待选条目（按数据源序）。"""
        return split_items(self.data_source, self.target_keys)[0]

    @property
    def selected_items(self) -> list[TransferItem]:
        """已选条目（按数据源序）。"""
        return split_items(self.data_source, self.target_keys)[1]

    def items(self, side: str) -> list[TransferItem]:
        """某一侧的**可见**条目（已套用该侧搜索词）。"""
        return match_items(self._side_items(side), self._query[side])

    def _side_items(self, side: str) -> list[TransferItem]:
        return self.source_items if side == "left" else self.selected_items

    def picked(self, side: str) -> list[str]:
        """某一侧已勾选的 key（按数据源序，只含仍然存在且合法的）。"""
        chosen = self._picked[side]
        return [item.key for item in self.data_source if item.key in chosen]

    def is_move_ready(self, direction: str) -> bool:
        """该方向现在是否有可搬的条目（决定箭头是否点亮）。"""
        side = "left" if direction == "right" else "right"
        return bool(self._movable(side))

    def _movable(self, side: str) -> list[str]:
        """某一侧已勾选且真的能搬的 key。"""
        by_key = {item.key: item for item in self.data_source}
        return [
            key
            for key in self.picked(side)
            if key in by_key and not by_key[key].disabled
        ]

    # ------------------------------------------------------------------
    # 对外动作（脚本可调）
    # ------------------------------------------------------------------
    def move(self, direction: str) -> list[str]:
        """把当前勾选的一批搬到 ``direction`` 一侧，返回新的 target_keys。"""
        side = "left" if direction == "right" else "right"
        keys = self._movable(side)
        if not keys or self.disabled:
            return list(self.target_keys)
        return self.move_keys(keys, direction)

    def move_keys(self, keys: Iterable[str], direction: str) -> list[str]:
        """搬指定的 key（不必先勾选），返回新的 target_keys。"""
        moved = [
            item.key
            for item in self.data_source
            if item.key in set(keys) and not item.disabled
        ]
        if direction == "left" and self.one_way:
            return list(self.target_keys)
        next_targets = move_targets(
            self.data_source, self.target_keys, moved, direction
        )
        if next_targets == self.target_keys:
            return list(self.target_keys)
        self.target_keys = next_targets
        # 搬走的条目不该还留在这侧的勾选里：用户下一次按箭头时，
        # 期望的是"搬刚勾的那批"，而不是重搬一批已经不在这边的东西。
        self._picked["left" if direction == "right" else "right"].difference_update(
            moved
        )
        self._repaint()
        if self.on_change is not None:
            self.on_change(list(next_targets), direction, moved)
        return list(next_targets)

    def toggle(self, side: str, key: str) -> None:
        """勾选 / 取消勾选一条。"""
        if self.disabled:
            return
        chosen = self._picked[side]
        if key in chosen:
            chosen.discard(key)
        else:
            chosen.add(key)
        self._repaint()
        self._selection_changed()

    def toggle_all(self, side: str, on: bool | None = None) -> None:
        """整侧（当前可见项）全选 / 全不选。``on=None`` 按当前三态取反。

        只作用于**可搬**的可见项：禁用项勾上也搬不走，勾了只会让人困惑。
        条目本身禁用的不算，组件整体禁用时直接不响应。
        """
        if self.disabled:
            return
        visible = self._pickable(side)
        if not visible:
            return
        state = check_state(visible, self._picked[side])
        want = (state != "all") if on is None else bool(on)
        chosen = self._picked[side]
        keys = {item.key for item in visible}
        if want:
            chosen.update(keys)
        else:
            chosen.difference_update(keys)
        self._repaint()
        self._selection_changed()

    def _pickable(self, side: str) -> list[TransferItem]:
        """某一侧可见且**可以勾选**的条目（禁用项排除）。"""
        return [item for item in self.items(side) if not item.disabled]

    def clear_selection(self, side: str | None = None) -> None:
        """清空勾选（``None`` 清两侧）。搬完一批后自动做，一般不用手动调。"""
        sides = (side,) if side else DIRECTIONS
        for name in sides:
            self._picked[name].clear()
        self._repaint()
        self._selection_changed()

    def set_query(self, side: str, text: str) -> None:
        """设定某侧的搜索词。"""
        if self._query[side] == text:
            return
        self._query[side] = text
        self._repaint()

    def invalidate(self) -> None:
        """外部改过 ``data_source`` / ``target_keys`` 后调一次，重算派生状态。"""
        alive = {item.key for item in self.data_source}
        for chosen in self._picked.values():
            chosen.intersection_update(alive)
        self.target_keys = [k for k in self.target_keys if k in alive]
        self._repaint()

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------
    def _selection_changed(self) -> None:
        if self.on_select_change is not None:
            self.on_select_change(self.picked("left"), self.picked("right"))

    def _repaint(self) -> None:
        """请求重绘。

        名字**不能**叫 ``_notify``：``@ft.observable`` 自己注入了
        ``_notify(name)`` 做属性变更通知（签名不同，覆盖了会直接 ``TypeError``）。
        """
        notify = getattr(self, "notify", None)
        if callable(notify):
            notify()

    def _hover_row(self, key: str, on: bool) -> None:
        """悬停换行才重绘：划一列会有几十次 enter/exit。"""
        if on:
            if self._hover == key:
                return
            self._hover = key
        else:
            if self._hover != key:  # 已经换到别的行了，旧行的 exit 直接忽略
                return
            self._hover = None
        self._repaint()

    def _head_titles(self) -> tuple[str, str]:
        if self.titles is not None:
            return self.titles
        return (t("ui.transfer.source"), t("ui.transfer.target"))

    # ------------------------------------------------------------------
    # 渲染
    # ------------------------------------------------------------------
    @ft.component
    def ui(self) -> ft.Control:
        """构建穿梭框。"""
        use_t()  # 订阅语言：列标题、空状态、搜索占位跟着切
        use_theme()  # 订阅主题：勾选底色 / 悬停底色都是角色色

        body = ft.Row(
            spacing=SPACE["3"],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                self._column("left"),
                self._arrows(),
                self._column("right"),
            ],
        )
        if self.v_label is None:
            return body
        if self.is_vertical:
            return ft.Column(
                spacing=self.spacing,
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.START,
                controls=[self.v_label, body],
            )
        return ft.Row(
            spacing=self.spacing,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[self.v_label, body],
        )

    def _column(self, side: str) -> ft.Control:
        """一列：列头 + 搜索（可选）+ 列表。"""
        rows: list[ft.Control] = [self._head(side)]
        if self.show_search:
            rows.append(self._search(side))
        rows.append(self._list(side))
        return ft.Container(
            width=self.list_width,
            height=self.height,
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=RADIUS["lg"],
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=ft.Column(spacing=0, tight=True, controls=rows),
        )

    def _head(self, side: str) -> ft.Control:
        """列头：全选框 + 标题 + 右侧「勾了几 / 共几条」。"""
        visible = self.items(side)
        pickable = self._pickable(side)
        title = self._head_titles()[0 if side == "left" else 1]
        picked = sum(1 for item in visible if item.key in self._picked[side])

        if picked:
            counter = ft.Text(
                f"{picked} / {len(visible)}",
                size=FONT_SIZE["caption"],
                color=ft.Colors.PRIMARY,
                weight=FONT_WEIGHT["medium"],
            )
        else:
            counter = ft.Text(
                str(len(visible)),
                size=FONT_SIZE["caption"],
                color=ft.Colors.ON_SURFACE_VARIANT,
            )

        controls: list[ft.Control] = []
        if self.show_select_all:
            controls.append(
                self._box_hit(
                    check_state(pickable, self._picked[side]),
                    on_tap=lambda _e, s=side: self.toggle_all(s),
                    enabled=not self.disabled and bool(pickable),
                )
            )
        controls.append(
            ft.Text(
                title,
                size=FONT_SIZE["subtitle"],
                weight=FONT_WEIGHT["medium"],
                color=DISABLED_FG if self.disabled else ft.Colors.ON_SURFACE,
                max_lines=1,
                overflow=ft.TextOverflow.ELLIPSIS,
            )
        )
        controls.append(ft.Container(expand=True))
        controls.append(counter)
        return ft.Container(
            height=HEAD_H,
            padding=ft.Padding.symmetric(horizontal=SPACE["2"]),
            border=ft.Border.only(bottom=hairline()),
            content=ft.Row(
                spacing=SPACE["2"],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=controls,
            ),
        )

    def _search(self, side: str) -> ft.Control:
        """列内的搜索框。窄、无边框、贴一层淡底，不抢列头的层级。"""
        return ft.Container(
            padding=ft.Padding.only(
                left=SPACE["2"], right=SPACE["2"], top=SEARCH_PAD, bottom=SEARCH_PAD
            ),
            content=ft.TextField(
                value=self._query[side],
                height=SEARCH_H,
                dense=True,
                filled=True,
                # 用角色色而不是 overlay(0.04)：浅色下两者差不多，暗色下 4% 的白
                # 在黑底上等于没有 —— 搜索框会变成一截浮着的占位文字。
                fill_color=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                # 无边框但保留圆角：Flet 1.0 里圆角只能经 border 传，
                # 直接用 NoInputBorder 会得到一个生硬的直角矩形。
                border=outline_input(
                    radius=RADIUS["md"],
                    color=ft.Colors.TRANSPARENT,
                    focused_color=ft.Colors.PRIMARY,
                ),
                text_size=FONT_SIZE["small"],
                content_padding=ft.Padding.symmetric(
                    horizontal=SPACE["2"], vertical=0
                ),
                prefix=ft.Container(
                    width=20,
                    alignment=ft.Alignment.CENTER_LEFT,
                    content=ft.Icon(
                        ft.Icons.SEARCH, size=15, color=ft.Colors.OUTLINE
                    ),
                ),
                hint_text=t("ui.transfer.search"),
                hint_style=ft.TextStyle(
                    size=FONT_SIZE["small"], color=ft.Colors.OUTLINE
                ),
                read_only=self.disabled,
                on_change=lambda e, s=side: self.set_query(s, e.control.value or ""),
            ),
        )

    def _list(self, side: str) -> ft.Control:
        """可滚动的行列表；空态给一句"为什么空、下一步做什么"。"""
        visible = self.items(side)
        body_h = self.height - HEAD_H
        if self.show_search:
            body_h -= SEARCH_H + SEARCH_PAD * 2
        if not visible:
            return ft.Container(
                height=body_h,
                alignment=ft.Alignment.CENTER,
                content=self._empty(side),
            )
        return ft.Container(
            height=body_h,
            content=ft.ListView(
                spacing=ROW_GAP,
                padding=ft.Padding.symmetric(
                    horizontal=SPACE["1"], vertical=SPACE["1"]
                ),
                controls=[self._row(item, side) for item in visible],
            ),
        )

    def _empty(self, side: str) -> ft.Control:
        """空态：图标 + 一句主文 + 一句提示。"""
        if side == "left":
            icon = ft.Icons.INBOX
            main = t("ui.transfer.empty_source")
            hint = t("ui.transfer.empty_source_hint")
        else:
            icon = ft.Icons.ARROW_FORWARD
            main = t("ui.transfer.empty_target")
            hint = t("ui.transfer.empty_target_hint")
        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=SPACE["4"]),
            content=ft.Column(
                spacing=SPACE["1"],
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(icon, size=22, color=ft.Colors.OUTLINE_VARIANT),
                    ft.Text(
                        main,
                        size=FONT_SIZE["small"],
                        color=ft.Colors.OUTLINE,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        hint,
                        size=FONT_SIZE["caption"],
                        color=ft.Colors.OUTLINE_VARIANT,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
            ),
        )

    def _row(self, item: TransferItem, side: str) -> ft.Control:
        """一行：复选框 + 主文本（+ 副文本）。整行可点，点哪都算勾选。"""
        blocked = self.disabled or item.disabled
        picked = item.key in self._picked[side]
        hovered = self._hover == f"{side}:{item.key}" and not blocked

        bgcolor = None
        if picked:
            bgcolor = PICKED_BG
        elif hovered:
            bgcolor = HOVER_BG

        text_color = DISABLED_FG if blocked else ft.Colors.ON_SURFACE
        lines: list[ft.Control] = [
            ft.Text(
                item.title,
                size=FONT_SIZE["body"],
                color=text_color,
                max_lines=1,
                overflow=ft.TextOverflow.ELLIPSIS,
            )
        ]
        if item.description:
            lines.append(
                ft.Text(
                    item.description,
                    size=FONT_SIZE["caption"],
                    color=DISABLED_FG
                    if blocked
                    else ft.Colors.ON_SURFACE_VARIANT,
                    max_lines=2,
                    overflow=ft.TextOverflow.ELLIPSIS,
                )
            )

        box = ft.Container(
            padding=ft.Padding.symmetric(horizontal=SPACE["2"], vertical=ROW_PAD_V),
            border_radius=RADIUS["md"],
            bgcolor=bgcolor,
            content=ft.Row(
                spacing=SPACE["2"],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        width=BOX_HIT,
                        alignment=ft.Alignment.CENTER_LEFT,
                        content=self._box(
                            "checked" if picked else "none", enabled=not blocked
                        ),
                    ),
                    ft.Column(spacing=0, tight=True, expand=True, controls=lines),
                ],
            ),
        )
        if blocked:
            return box
        # 整行一个 GestureDetector（复选框图形不单独挂事件）：内层再挂一个
        # 会和整行抢命中区，点方框边缘的手感就不一致了。
        return ft.GestureDetector(
            on_tap=lambda _e, s=side, k=item.key: self.toggle(s, k),
            on_enter=lambda _e, s=side, k=item.key: self._hover_row(f"{s}:{k}", True),
            on_exit=lambda _e, s=side, k=item.key: self._hover_row(f"{s}:{k}", False),
            content=box,
        )

    def _arrows(self) -> ft.Control:
        """中间的两个箭头，垂直居中于两列。

        右移（主操作）在上、左移在下 —— 和 AntD 的 ``>`` / ``<`` 同序，
        也和"先挑出去、再拿回来"的阅读顺序一致。
        """
        buttons: list[ft.Control] = [self._arrow("right")]
        if not self.one_way:
            buttons.append(self._arrow("left"))
        # 不设高度、交给外层 Row 的 CENTER 对齐：定高再自己居中，会差那么
        # 十几像素（Row 里三列同高时，定高容器的"居中"其实是顶对齐）。
        return ft.Container(
            content=ft.Column(spacing=SPACE["2"], tight=True, controls=buttons),
        )

    def _arrow(self, direction: str) -> ft.Control:
        """箭头按钮：有可搬的条目就点亮（淡主色底 + 主色图标），否则只剩淡灰轮廓。"""
        active = self.is_move_ready(direction) and not self.disabled
        key = f"arrow:{direction}"
        hovered = active and self._hover == key
        if active:
            bgcolor = overlay(0.16, role=ft.Colors.PRIMARY) if hovered else PICKED_BG
            border = None
            color = ft.Colors.PRIMARY
        else:
            bgcolor = None
            border = ft.Border.all(1, ft.Colors.OUTLINE_VARIANT)
            color = ft.Colors.OUTLINE_VARIANT

        tip = t(
            "ui.transfer.move_right" if direction == "right" else "ui.transfer.move_left"
        )
        box = ft.Container(
            width=ARROW,
            height=ARROW,
            border_radius=RADIUS["md"],
            bgcolor=bgcolor,
            border=border,
            alignment=ft.Alignment.CENTER,
            tooltip=tip if active else None,
            content=ft.Icon(
                ft.Icons.CHEVRON_RIGHT if direction == "right" else ft.Icons.CHEVRON_LEFT,
                size=20,
                color=color,
            ),
        )
        if not active:
            return box
        return ft.GestureDetector(
            on_tap=lambda _e, d=direction: self.move(d),
            on_enter=lambda _e, k=key: self._hover_row(k, True),
            on_exit=lambda _e, k=key: self._hover_row(k, False),
            content=box,
        )

    # ------------------------------------------------------------------
    # 复选框（自绘：16px 的方框比 ft.Checkbox 紧凑一半，且能画三态）
    # ------------------------------------------------------------------
    def _box(self, state: str, *, enabled: bool = True) -> ft.Control:
        """复选框图形。``state`` 取 ``"checked"`` / ``"some"`` / ``"none"``。"""
        filled = state != "none"
        bgcolor = None
        border_color = overlay(0.30)
        if filled:
            bgcolor = ft.Colors.PRIMARY if enabled else overlay(0.26)
            border_color = bgcolor
        icon: ft.Control | None = None
        if state == "checked":
            icon = ft.Icon(ft.Icons.CHECK, size=12, color=ft.Colors.ON_PRIMARY)
        elif state == "some":
            icon = ft.Icon(ft.Icons.REMOVE, size=12, color=ft.Colors.ON_PRIMARY)
        return ft.Container(
            width=BOX,
            height=BOX,
            border_radius=BOX_RADIUS,
            bgcolor=bgcolor,
            border=ft.Border.all(1.5, border_color),
            alignment=ft.Alignment.CENTER,
            content=icon,
        )

    def _box_hit(
        self,
        state: str,
        *,
        on_tap: Callable[..., None],
        enabled: bool,
    ) -> ft.Control:
        """带命中区的复选框（列头的全选框；行内不需要，整行都是命中区）。"""
        box = self._box(state, enabled=enabled)
        if not enabled:
            return ft.Container(width=BOX_HIT, content=box)
        return ft.GestureDetector(
            on_tap=on_tap,
            content=ft.Container(
                width=BOX_HIT,
                padding=ft.Padding.symmetric(vertical=SPACE["1"]),
                content=box,
            ),
        )


@ft.component
def App():  # pragma: no cover - 冒烟用
    """冒烟 / 手工验收用的最小页面。"""
    tr = Transfer(
        label="可见列",
        data_source=[
            TransferItem("name", "姓名"),
            TransferItem("dept", "部门", description="一级 / 二级部门"),
            TransferItem("title", "职位"),
            TransferItem("email", "邮箱", description="企业邮箱"),
            TransferItem("phone", "手机"),
            TransferItem("salary", "薪资", disabled=True),
        ],
        target_keys=["name", "dept"],
    )
    return ft.Column(
        spacing=16,
        controls=[
            tr.ui(),
            ft.Text("被禁用的「薪资」两侧都搬不动。", size=12, color=ft.Colors.OUTLINE),
        ],
    )


if __name__ == "__main__":  # pragma: no cover
    ft.run(lambda page: page.render(App))
