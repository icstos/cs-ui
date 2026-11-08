"""多选下拉框 (MultiSelect)。

交互与视觉参考 Streamlit 的 ``st.multiselect``：

- 折叠态是一个带边框的输入框，已选项以 Chip 排列在框内，右端一个下拉箭头；
- 点击框体在下方展开选项面板：每行「复选框 + 文本」，选中行高亮为淡蓝底；
- 点选项即时切换（面板保持展开），点 Chip 上的 × 单独移除，点「全选」整组切换；
- 再次点击框体，或点面板右下角「完成」收起；
- ``searchable`` 时展开后框体右侧出现一个窄搜索框，按文本忽略大小写过滤选项；
- ``max_selected`` 给上限：到顶后未选项变灰不可点，「全选」也一并锁住。

与 :class:`~ui.input.checkbox.CheckboxGroup` 的区别：
``CheckboxGroup`` 是纯表单控件，无边框、无汇总展示、选项常驻可见；
``MultiSelect`` 是折叠式下拉框，适合选项较多、需要一眼看到已选项的场景。

.. note::
    面板挂在**页面浮层**（``page.overlay``）上，因此：

    - 折叠态的高度就是整个组件占用布局的高度，展开面板不会把下方内容推下去；
    - 展开时铺一层全屏透明遮罩，点面板外部即收起（也顺带挡住了页面滚动，
      面板不会与输入框错位）。

    浮层需要 ``page.render`` 这条根视图路径；若宿主用的是
    ``page.render_views``（Router 的 ``manage_views=True`` 视图栈），
    浮层层会被视图盖住，此时组件**自动降级为流内展开**（面板会占高度）。
    也可用 ``float_panel=False`` 强制走流内展开。
    判定逻辑见 :func:`ui.core.float_layer.overlay_usable`。

.. note::
    ``side`` / ``border`` 之类的样式沿用 :mod:`ui.core.styles` 的约定：
    展开态边框用主题主色，等价于原生输入框的聚焦态。

用法::

    ms = MultiSelect(label="标签", options=["A", "B", "C"], value=["A"])
    ...
    container = ms.ui()
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import flet as ft

from ui.core.doc import Api, Example, Spec, info, run, tip
from ui.core.empty import empty_line
from ui.core.float_layer import overlay_usable, use_float_layer
from ui.core.format import format_list
from ui.core.i18n import t, use_t
from ui.core.tokens import (
    FONT_SIZE,
    ICON_SIZE,
    disabled_layer,
    selected_layer,
    state_layer,
)
from ui.input.input import Label
from ui.input.panel_field import DISABLED_FG

__all__ = ["MultiSelect"]

BORDER_RADIUS = 8  # 输入框 / 面板圆角
CHIP_RADIUS = 6  # Chip 圆角
ROW_RADIUS = 6  # 选项行圆角
ROW_HEIGHT = 34  # 选项行高
PANEL_PAD = 6  # 面板上下内边距（选项行左右内缩量同值）
PANEL_GAP = 4  # 面板与输入框之间的间距
FIELD_PAD_H = 10
FIELD_PAD_V = 8
FOOTER_HEIGHT = 36
SEARCH_W = 104  # 框内搜索框宽度（展开且 searchable 时占位）
SEARCH_H = 26  # 框内搜索框高度（比 Chip 略高，撑高 2px 可以接受）
TEXT_SIZE = FONT_SIZE["body"]  # 选项行 = 正文
CHIP_TEXT_SIZE = FONT_SIZE["small"]  # 框内 Chip 比正文小一档
DEFAULT_FIELD_HEIGHT = 40  # 尺寸上报前的兜底值
SCREEN_MARGIN = 8  # 面板与窗口边缘的最小间距

#: 选中行背景：淡蓝（对齐 Streamlit 的选中高亮）
SELECTED_BG = selected_layer()
#: 悬停行背景：淡灰
HOVER_BG = state_layer("hover")
#: 到上限后被锁住的行：文字与图标一起压到禁用档的灰（与整组禁用同一档）
LOCKED_FG = disabled_layer()


def _truthy(value: object) -> bool:
    """把 hover 事件载荷归一成布尔（可能是 bool，也可能是 ``"true"`` 字符串）。"""
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


@ft.observable
@dataclass
class MultiSelect(Label):
    """多选下拉框。

    Args:
        value: 已选中的选项值列表。
        options: 全部可选项（文本即值）。
        placeholder: 未选择任何项时框内的占位文本。``None``（默认）取语言包。
        width: 输入框与面板宽度，默认 320。
        panel_height: 选项区最大高度，超出后内部滚动，默认 260。
        show_select_all: 是否在面板顶部显示「全选」行（支持半选态），默认 True。
        show_footer: 是否显示「已选 N / M + 完成」页脚，默认 True。
        is_open: 面板是否展开（运行期状态，可代码控制）。
        disabled: 是否禁用。
        float_panel: 面板是否走页面浮层。``None``（默认）表示自动：
            浮层可用时悬挂，否则退化为流内展开。``True`` / ``False`` 强制指定。
        on_change: 选择变化回调，接收最新的已选列表副本。
        searchable: 展开后框体右侧是否带搜索框，按选项文本忽略大小写过滤，默认 False。
        max_selected: 最多可选几项。``None``（默认）不限；到上限后未选项置灰不可点。
    """

    value: list[str] = field(default_factory=list)
    options: list[str] = field(default_factory=list)
    placeholder: str | None = None
    width: int | float = 320
    panel_height: int | float = 260
    show_select_all: bool = True
    show_footer: bool = True
    is_open: bool = False
    disabled: bool = False
    float_panel: bool | None = None
    on_change: Callable[[list[str]], None] | None = None
    searchable: bool = False
    max_selected: int | None = None

    def __post_init__(self) -> None:
        # 运行期状态：当前鼠标悬停的行 key。下划线开头 => 不参与序列化，
        # 变更后靠 notify() 触发重绘。
        self._hover: str | None = None
        # 框内搜索词（仅 searchable 且展开时有值）。
        self._query: str = ""
        # 输入框左上角的页面坐标（点击时从事件里换算得到），浮层据此定位。
        self._anchor: tuple[float, float] | None = None
        # 输入框的实际高度（由 on_size_change 上报），Chip 换行时会变高。
        self._field_h: float = DEFAULT_FIELD_HEIGHT

    # ------------------------------------------------------------------
    # 公开操作
    # ------------------------------------------------------------------

    def select(self, option: str, selected: bool = True) -> None:
        """选中 / 取消选中单个选项。已达上限时新选项不再进入。"""
        if selected:
            if option in self.value:
                return
            if self._at_limit:
                return
            self.value = [*self.value, option]
        else:
            if option not in self.value:
                return
            self.value = [v for v in self.value if v != option]
        self._emit()

    def toggle(self, option: str) -> None:
        """反转单个选项的选中态。"""
        self.select(option, option not in self.value)

    def select_all(self, selected: bool = True) -> None:
        """全选 / 全不选。设了上限且装不下全部选项时，「全选」不生效。"""
        if (
            selected
            and self.max_selected is not None
            and self.max_selected < len(self.options)
        ):
            return
        target = list(self.options) if selected else []
        if list(self.value) == target:
            return
        self.value = target
        self._emit()

    def clear(self) -> None:
        """清空已选。"""
        self.select_all(False)

    def open(self) -> None:
        """展开面板。"""
        if self.disabled or self.is_open:
            return
        # 每次打开都从干净状态开始：上次的搜索词留着，看到的就不是完整选项了。
        self._query = ""
        self.is_open = True
        self.notify()  # type: ignore[attr-defined]

    def close(self) -> None:
        """收起面板。"""
        if not self.is_open:
            return
        self.is_open = False
        self._hover = None
        self.notify()  # type: ignore[attr-defined]

    def toggle_open(self) -> None:
        """展开 / 收起。"""
        self.close() if self.is_open else self.open()

    # ------------------------------------------------------------------
    # 只读属性
    # ------------------------------------------------------------------

    @property
    def all_selected(self) -> bool:
        """是否已全选。"""
        return bool(self.options) and len(self.value) == len(self.options)

    @property
    def partially_selected(self) -> bool:
        """是否部分选中（用于「全选」行的半选态）。"""
        return bool(self.value) and not self.all_selected

    @property
    def display_text(self) -> str:
        """已选内容的纯文本表示，便于日志 / 表单提交。

        分隔符按语言走（中文顿号、英文逗号）—— 这不是"细节"，导出 CSV 或
        写日志时用错分隔符会直接变成脏数据。
        """
        return format_list(self.value)

    @property
    def _fg(self) -> ft.ColorValue:
        """主文字色：禁用时整体压灰。"""
        return ft.Colors.OUTLINE if self.disabled else ft.Colors.ON_SURFACE

    @property
    def _visible_options(self) -> list[str]:
        """面板里真正要画的选项：套上搜索词后的结果，无搜索词时就是全部。"""
        keyword = self._query.strip().casefold()
        if not keyword:
            return list(self.options)
        return [option for option in self.options if keyword in option.casefold()]

    @property
    def _at_limit(self) -> bool:
        """是否已经选到上限。没设上限时永远为 False。"""
        return self.max_selected is not None and len(self.value) >= self.max_selected

    def _row_locked(self, option: str) -> bool:
        """这一行现在是否点不动：到上限后，未选项一律锁住（已选的仍可取消）。"""
        return self._at_limit and option not in self.value

    def _all_locked(self, options: list[str]) -> bool:
        """「全选」这一行是否该锁住：剩下的名额装不下这批未选项。

        判据是「未选数 > 剩余名额」而不是「上限 < 选项数」—— 已经选了 2 个、
        上限 3 个时，眼前只剩 1 个未选项，全选仍然是能完成的动作。
        """
        if self.max_selected is None:
            return False
        extra = sum(1 for option in options if option not in self.value)
        return extra > self.max_selected - len(self.value)

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------

    def _emit(self) -> None:
        if self.on_change:
            self.on_change(list(self.value))
        self.notify()  # type: ignore[attr-defined]

    def _hover_row(self, key: str, hovering: bool) -> None:
        """更新悬停行（同一个 key 重复进入 / 离开时提前返回，避免抖动）。"""
        if (self._hover == key) == hovering:
            return
        self._hover = key if hovering else None
        self.notify()  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    @ft.component
    def ui(self) -> ft.Control:
        """构建多选下拉框 UI。"""
        use_t()  # 订阅语言：占位符 / 全选 / 页脚计数都要跟着切
        page = ft.context.page
        field = self._build_field()
        floating = self._should_float(page)
        left, top, bottom = self._panel_origin(page)

        # 无条件调用（hook 顺序必须稳定）；visible=False 时浮层自动移除。
        # hole 把输入框从遮罩里挖出来，否则 Chip 的 × 会被遮罩抢走点击。
        use_float_layer(
            page=page,
            visible=floating and self.is_open and not self.disabled,
            left=left,
            top=top,
            bottom=bottom,
            content=self._build_panel(),
            on_dismiss=self.close,
            hole=None
            if self._anchor is None
            else (self._anchor[0], self._anchor[1], float(self.width), self._field_h),
        )

        if floating:
            # 面板在浮层里，布局只占折叠态的高度。
            body: ft.Control = field
        elif self.is_open and not self.disabled:
            # 降级：面板流内展开，下方内容随之下移。
            body = ft.Column(controls=[field, self._build_panel()], spacing=PANEL_GAP)
        else:
            body = field

        return self._with_label(body)

    # ---- 浮层定位 ----

    def _should_float(self, page: ft.Page) -> bool:
        """面板是否走页面浮层。"""
        if self.float_panel is not None:
            return self.float_panel
        return overlay_usable(page)

    def _panel_height(self) -> float:
        """面板高度估算，用于判断往下弹还是往上弹。"""
        total = PANEL_PAD * 2 + 2  # 上下内边距 + 上下边框
        if self.show_select_all:
            total += ROW_HEIGHT + 1
        if self.options:
            total += max(
                ROW_HEIGHT,
                min(float(self.panel_height), len(self._visible_options) * ROW_HEIGHT),
            )
        else:
            total += ROW_HEIGHT
        if self.show_footer:
            total += 1 + FOOTER_HEIGHT
        return total

    def _panel_origin(self, page: ft.Page) -> tuple[float, float | None, float | None]:
        """面板定位：返回 ``(left, top, bottom)``，``top`` / ``bottom`` 二选一。

        默认从输入框下沿往下弹；下方放不下就向上翻转，改用 ``bottom`` 锚定
        —— 这样面板多高都能自动贴住输入框上沿（``top`` 方式需要预先知道面板
        高度，估算误差会变成一条可见的缝）。
        """
        ax, ay = self._anchor or (0.0, 0.0)
        height = self._panel_height()
        page_h = float(getattr(page, "height", 0) or 0)

        top = ay + self._field_h + PANEL_GAP
        # 下方放不下、上方又确实能容纳时向上翻；两边都放不下就保持向下 ——
        # 溢出到窗口外，好过把输入框本身盖住。
        if (
            page_h
            and top + height > page_h - SCREEN_MARGIN
            and ay - height - PANEL_GAP >= SCREEN_MARGIN
        ):
            return ax, None, page_h - ay + PANEL_GAP
        return ax, top, None

    def _with_label(self, body: ft.Control) -> ft.Control:
        """按 ``v_label`` / ``is_vertical`` 把标签摆到内容旁。"""
        if self.v_label is None:
            return body
        if self.is_vertical:
            return ft.Column(
                controls=[self.v_label, body],
                spacing=self.spacing,
                horizontal_alignment=ft.CrossAxisAlignment.START,
            )
        return ft.Row(
            controls=[self.v_label, body],
            spacing=self.spacing,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

    # ---- 输入框 ----

    def _on_field_click(self, e: ft.TapEvent) -> None:
        """记录输入框位置（浮层据此定位），再切换展开态。"""
        gp = getattr(e, "global_position", None)
        lp = getattr(e, "local_position", None)
        if gp is not None and lp is not None:
            # 控件左上角全局坐标 = 命中点全局坐标 - 命中点局部坐标
            self._anchor = (gp.x - lp.x, gp.y - lp.y)
        self.toggle_open()

    def _on_field_resize(self, e: ft.LayoutSizeChangeEvent) -> None:
        """记录输入框实际高度：Chip 换行会变高，浮层要跟着下移。"""
        h = getattr(e, "height", None)
        if h and abs(h - self._field_h) > 0.5:
            self._field_h = float(h)
            self.notify()  # type: ignore[attr-defined]

    def _build_field(self) -> ft.Control:
        """折叠态输入框：已选 Chip + 下拉箭头（可搜索时箭头前多一个输入框）。

        点击监听走 ``GestureDetector.on_tap`` —— ``Container.on_click`` 的事件
        不带坐标，而浮层需要知道输入框在页面上的位置；``GestureDetector`` 的
        ``local_position`` 正好相对输入框，``global - local`` 即输入框左上角。

        Chip 的 ``×`` 同样用 ``GestureDetector``：``Container.on_click`` 在内层
        时会被外层 ``GestureDetector`` 抢走（真机实测，点 ``×`` 变成开合面板）；
        同类型的 tap 识别器才会按"内层优先"决出胜者。

        搜索框必须画在这里、**不能**放进浮层面板：浮层每次更新都是"移除节点再
        追加一棵新树"（见 :func:`ui.core.float_layer.use_float_layer`），放进
        去的输入框每键入一个字就会被重建一次，焦点立刻丢失，一个字都打不完整。
        """
        searching = self.searchable and self.is_open and not self.disabled
        # 展开且可搜索时，搜索框就是这一行唯一的输入控件：占位文本让位给它
        # （搜索框自带「搜索」提示，再摆一个「请选择」是两行废话）。
        tokens = [] if (searching and not self.value) else self._build_tokens()

        controls: list[ft.Control] = []
        if tokens:
            controls.append(
                ft.Row(
                    expand=True,
                    # 搜索时 Chip 改成单行横滚：腾出位置给右边的输入框，
                    # 换行还会把框体撑高、把浮层面板顶下去。
                    wrap=not searching,
                    scroll=ft.ScrollMode.AUTO if searching else None,
                    spacing=6,
                    run_spacing=6,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=tokens,
                )
            )
        if searching:
            # 没有 Chip 时让搜索框吃掉整行 —— 320px 的框体里只放一个 104px 的
            # 输入框，用户点在旁边的空白上只会把面板关掉。
            controls.append(self._build_search_inline(expand=not tokens))
        controls.append(
            ft.Icon(
                ft.Icons.ARROW_DROP_UP if self.is_open else ft.Icons.ARROW_DROP_DOWN,
                size=20,
                color=ft.Colors.ON_SURFACE_VARIANT,
            )
        )

        return ft.GestureDetector(
            on_tap=self._on_field_click,
            content=ft.Container(
                width=self.width,
                padding=ft.Padding.symmetric(
                    horizontal=FIELD_PAD_H, vertical=FIELD_PAD_V
                ),
                bgcolor=ft.Colors.SURFACE_CONTAINER
                if self.disabled
                else ft.Colors.SURFACE,
                border=ft.Border.all(
                    1,
                    ft.Colors.PRIMARY if self.is_open else ft.Colors.OUTLINE_VARIANT,
                ),
                border_radius=ft.BorderRadius.all(BORDER_RADIUS),
                on_size_change=None if self.disabled else self._on_field_resize,
                size_change_interval=0,
                content=ft.Row(
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=controls,
                ),
            ),
        )

    def _build_tokens(self) -> list[ft.Control]:
        """框内内容：已选 Chip，或占位文本。"""
        if not self.value:
            return [
                ft.Text(
                    self.placeholder or t("ui.common.placeholder"),
                    size=TEXT_SIZE,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                    no_wrap=True,
                    overflow=ft.TextOverflow.ELLIPSIS,
                )
            ]
        return [self._build_chip(option) for option in self.value]

    def _build_chip(self, option: str) -> ft.Control:
        """单个已选 Chip，尾部带 × 直接移除。

        点 Chip 其它位置会冒泡到输入框的 ``GestureDetector``，等同于开合面板。
        """
        close: ft.Control = ft.Container(
            padding=ft.Padding.all(2),
            border_radius=ft.BorderRadius.all(4),
            content=ft.Icon(
                ft.Icons.CLOSE,
                size=ICON_SIZE["sm"],
                color=DISABLED_FG if self.disabled else ft.Colors.ON_SURFACE_VARIANT,
            ),
        )
        if not self.disabled:
            close = ft.GestureDetector(
                on_tap=lambda _e, opt=option: self.select(opt, False),
                content=close,
            )

        return ft.Container(
            padding=ft.Padding.only(left=8, right=4, top=2, bottom=2),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
            border_radius=ft.BorderRadius.all(CHIP_RADIUS),
            content=ft.Row(
                tight=True,
                spacing=4,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text(
                        option,
                        size=CHIP_TEXT_SIZE,
                        color=self._fg,
                        no_wrap=True,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    close,
                ],
            ),
        )

    # ---- 展开面板 ----

    def _build_search_inline(self, *, expand: bool = False) -> ft.Control:
        """输入框右侧的搜索框：只在展开且 ``searchable`` 时出现。

        位置刻意放在**折叠态的框体里**而不是浮层面板里 —— 面板每次更新都会整棵
        重建（见 :meth:`_build_field` 的说明），输入框放进去会一个字都打不完。
        过滤只作用在选项文本上，不碰已选：搜索是「帮我看清这一屏」，不是「改值」。
        """
        return ft.TextField(
            value=self._query,
            width=None if expand else SEARCH_W,
            expand=expand,
            height=SEARCH_H,
            dense=True,
            filled=False,
            text_size=CHIP_TEXT_SIZE,
            color=self._fg,
            content_padding=ft.Padding.symmetric(horizontal=4, vertical=0),
            border=ft.NoInputBorder(),
            hint_text=t("ui.common.search"),
            hint_style=ft.TextStyle(size=CHIP_TEXT_SIZE, color=ft.Colors.ON_SURFACE_VARIANT),
            on_change=self._on_query_change,
        )

    def _on_query_change(self, e: ft.ControlEvent) -> None:
        """搜索词变化：只重绘面板，已选与对外 value 都不动。"""
        self._query = e.control.value or ""
        self.notify()  # type: ignore[attr-defined]

    def _build_panel(self) -> ft.Control:
        """展开面板：全选行 + 可滚动选项列表 + 页脚。"""
        blocks: list[ft.Control] = []
        options = self._visible_options

        if self.show_select_all:
            blocks.append(self._build_select_all_row())
            blocks.append(ft.Divider(height=1))

        if options:
            blocks.append(
                ft.Column(
                    controls=[self._build_option_row(o) for o in options],
                    spacing=0,
                    height=max(
                        ROW_HEIGHT,
                        min(float(self.panel_height), len(options) * ROW_HEIGHT),
                    ),
                    scroll=ft.ScrollMode.AUTO,
                )
            )
        else:
            # 一个选项都没有，和"搜了但没有命中"是同一件事：这一屏给不出东西。
            # 左对齐 + 与选项行同内边距 —— 读起来像"列表的最后一行"。
            blocks.append(
                empty_line(
                    t("ui.multiselect.empty"),
                    height=ROW_HEIGHT,
                    align=ft.Alignment.CENTER_LEFT,
                    padding=ft.Padding.symmetric(horizontal=PANEL_PAD + 8),
                )
            )

        if self.show_footer:
            blocks.append(ft.Divider(height=1))
            blocks.append(self._build_footer())

        return ft.Container(
            width=self.width,
            bgcolor=ft.Colors.SURFACE,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=ft.BorderRadius.all(BORDER_RADIUS),
            padding=ft.Padding.symmetric(vertical=PANEL_PAD),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            shadow=ft.BoxShadow(
                blur_radius=12,
                color=ft.Colors.with_opacity(0.10, ft.Colors.BLACK),
                offset=ft.Offset(0, 3),
            ),
            content=ft.Column(controls=blocks, spacing=0),
        )

    def _build_select_all_row(self) -> ft.Control:
        """「全选」行，支持「全选 / 半选 / 未选」三态。

        三态只看**当前可见**的选项：搜索时点「全选」，用户的意思显然是"眼前
        这批"，偷偷把被过滤掉的也选上就说不清了。上限装不下全部可见项时整行
        锁住 —— 点下去只能选一半，比点不动更让人困惑。
        """
        options = self._visible_options
        picked = [option for option in options if option in self.value]
        checked = bool(options) and len(picked) == len(options)
        if checked:
            icon = ft.Icons.CHECK_BOX
        elif picked:
            icon = ft.Icons.INDETERMINATE_CHECK_BOX
        else:
            icon = ft.Icons.CHECK_BOX_OUTLINE_BLANK
        over_limit = self._all_locked(options)
        return self._build_row(
            key="__all__",
            label=t("ui.common.select_all"),
            icon=icon,
            highlighted=checked,
            on_click=lambda _e: self._toggle_visible(options),
            option_disabled=over_limit,
        )

    def _toggle_visible(self, options: list[str]) -> None:
        """整批切换可见选项（「全选」行用），一次广播而不是逐个 emit。"""
        if not options:
            return
        if all(option in self.value for option in options):
            target = [v for v in self.value if v not in options]
        else:
            if self._all_locked(options):
                return
            target = [*self.value, *[o for o in options if o not in self.value]]
        if target == list(self.value):
            return
        self.value = target
        self._emit()

    def _build_option_row(self, option: str) -> ft.Control:
        """单个选项行。到上限后未选项变灰：还能看见，但点不动。"""
        selected = option in self.value
        return self._build_row(
            key=option,
            label=option,
            icon=ft.Icons.CHECK_BOX if selected else ft.Icons.CHECK_BOX_OUTLINE_BLANK,
            highlighted=selected,
            on_click=lambda _e, opt=option: self.toggle(opt),
            option_disabled=self._row_locked(option),
        )

    def _build_row(
        self,
        *,
        key: str,
        label: str,
        icon: ft.IconData,
        highlighted: bool,
        on_click: Callable[[ft.ControlEvent], None],
        option_disabled: bool = False,
    ) -> ft.Control:
        """选项行的公共骨架：整行可点，图标即复选框。"""
        blocked = self.disabled or option_disabled
        if highlighted:
            bgcolor: ft.ColorValue | None = SELECTED_BG
        elif not blocked and self._hover == key:
            bgcolor = HOVER_BG
        else:
            bgcolor = None

        return ft.Container(
            height=ROW_HEIGHT,
            margin=ft.Margin.symmetric(horizontal=PANEL_PAD),
            padding=ft.Padding.symmetric(horizontal=8),
            border_radius=ft.BorderRadius.all(ROW_RADIUS),
            bgcolor=bgcolor,
            on_click=None if blocked else on_click,
            on_hover=None
            if blocked
            else (lambda e, k=key: self._hover_row(k, _truthy(e.data))),
            content=ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(
                        icon,
                        size=18,
                        color=LOCKED_FG
                        if option_disabled
                        else ft.Colors.PRIMARY
                        if highlighted
                        else ft.Colors.OUTLINE,
                    ),
                    ft.Text(
                        label,
                        size=TEXT_SIZE,
                        color=LOCKED_FG if option_disabled else self._fg,
                        expand=True,
                        no_wrap=True,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                ],
            ),
        )

    def _build_footer(self) -> ft.Control:
        """页脚：已选计数 + 完成（收起面板）。"""
        return ft.Container(
            height=FOOTER_HEIGHT,
            padding=ft.Padding.only(left=PANEL_PAD + 6, right=PANEL_PAD),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text(
                        t(
                            "ui.multiselect.selected",
                            n=len(self.value),
                            total=len(self.options),
                        ),
                        size=CHIP_TEXT_SIZE,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                    ft.TextButton(
                        content=ft.Text(t("ui.common.done"), size=CHIP_TEXT_SIZE),
                        on_click=lambda _e: self.close(),
                    ),
                ],
            ),
        )


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
def _caption(text: str) -> ft.Control:
    return ft.Text(text, size=FONT_SIZE["small"], color=ft.Colors.ON_SURFACE_VARIANT)


@ft.component
def _echo(select: MultiSelect, limit: int | None = None) -> ft.Control:
    """把 value 读出来：Chip 只说明「选了哪些」，这行说明「程序拿到什么」。"""
    picked = "、".join(select.value) if select.value else "未选择"
    if limit is None:
        tail = ""
    elif len(select.value) >= limit:
        tail = " · 已达上限，其余选项不可点"
    else:
        tail = f" · 还可选 {limit - len(select.value)} 项"
    return _caption(f"已选 {len(select.value)} 项：{picked}{tail}")


_TECH = [
    "Python",
    "Flet",
    "FastAPI",
    "SQLite",
    "Docker",
    "Redis",
    "Nginx",
    "PostgreSQL",
]

_CITIES = [
    "北京",
    "上海",
    "广州",
    "深圳",
    "杭州",
    "南京",
    "成都",
    "武汉",
    "西安",
    "苏州",
    "厦门",
    "青岛",
]

_ROLES = ["查看", "编辑", "发布", "审核", "导出", "删除", "授权", "归档"]


@ft.component
def _basic() -> ft.Control:
    """两个已选项：框里是 Chip，× 直接删；点框体开面板继续挑。"""
    select = ft.use_memo(
        lambda: MultiSelect(
            label="技术栈",
            options=_TECH,
            value=["Python", "Flet"],
            is_required=True,
        ),
        [],
    )
    return ft.Column(spacing=10, controls=[select.ui(), _echo(select)])


@ft.component
def _search() -> ft.Control:
    """12 个城市，展开后框内直接键入：选项列表跟着收窄，已选不受影响。"""
    select = ft.use_memo(
        lambda: MultiSelect(
            label="常驻城市",
            options=_CITIES,
            searchable=True,
            panel_height=190,
        ),
        [],
    )
    return ft.Column(spacing=10, controls=[select.ui(), _echo(select)])


@ft.component
def _limit() -> ft.Control:
    """上限 3 个：选满后未选项转灰、点不动；「全选」也跟着锁住。"""
    select = ft.use_memo(
        lambda: MultiSelect(
            label="权限",
            options=_ROLES,
            value=["查看", "编辑"],
            max_selected=3,
        ),
        [],
    )
    return ft.Column(spacing=10, controls=[select.ui(), _echo(select, limit=3)])


_BASIC_CODE = """select = MultiSelect(
    label="技术栈",
    options=["Python", "Flet", "FastAPI", "SQLite"],
    value=["Python"],                       # 已选项以 Chip 显示在框内
)
Column([select.ui(), Text(f"已选 {select.value}")])

# 每次勾选都会回写 value，并把副本交给回调
select = MultiSelect(
    options=["Python", "Flet"],
    on_change=lambda picked: print(picked),  # (list[str]) -> None
)"""

_SEARCH_CODE = """select = MultiSelect(
    options=["北京", "上海", "杭州", "深圳"],
    searchable=True,        # 展开后框内出现搜索框，按选项文本忽略大小写过滤
    panel_height=190,       # 选项区最高 190，超出内部滚动
)"""

_LIMIT_CODE = """select = MultiSelect(
    options=["查看", "编辑", "发布", "审核"],
    value=["查看", "编辑"],
    max_selected=3,         # 到 3 项后，未选项变灰不可点
    on_change=save,         # (list[str]) -> None
)"""


SPEC = Spec(
    name="MultiSelect",
    summary="折叠式多选框：已选项以 Chip 汇总，面板里逐项勾选。",
    definition=(
        "多选框回答的是一组「要哪几个」。它把已选项收成框内的 Chip，让表单在"
        "收起状态下也只有几行高，点开才铺出完整的选项列表 —— 选项多到十几二十个时，"
        "常驻的复选框组会把整张表单撑开好几屏。框里的 Chip 同时充当汇总：不看面板也"
        "知道选了什么，单个 × 就能摘掉，不必为了取消一项再把面板翻出来。"
    ),
    anatomy=[
        (
            "框体",
            "40px 高的边框输入框，内放 Chip、右端一个下拉箭头；展开时描边转主色。",
        ),
        ("Chip", "已选项，灰底小标签 + ×；× 单独移除该项，点别处仍是开合面板。"),
        ("搜索框", "searchable 且展开时出现在框体右侧，只过滤选项列表，不动已选。"),
        ("全选行", "三态（全选 / 半选 / 未选），作用范围是当前可见的选项。"),
        ("选项行", "整行可点，左侧复选框即状态；选中行铺 12% 主色底。"),
        ("页脚", "「已选 N / M」+「完成」。计数是给「还差几个」一个明确答案。"),
    ],
    when=[
        "选项十来个以上，全铺在表单里会占掉半屏",
        "提交前需要复核已选项（标签、筛选项、通知渠道）",
        "允许「先随便选几个，再回头删」，而不是一次定死",
    ],
    avoid=[
        "选项三五个且都很重要：用 CheckboxGroup，全部摊开比多一次点击快",
        "需要左右对照着挑（成员、可见列）：用 Transfer，两栏常驻才能看清「已选 vs 未选」",
        "选项互斥只能选一个：用 SelectBox，多选会让人以为能同时成立",
    ],
    examples=[
        Example(
            "基础多选",
            _basic,
            hint="框内两个 Chip，点 × 立即移除；点框体展开面板继续勾选，下方实时回显 value。",
            code=_BASIC_CODE,
        ),
        Example(
            "可搜索",
            _search,
            hint="点开面板后直接在框内键入：选项列表跟着收窄，已选的 Chip 不受影响。",
            code=_SEARCH_CODE,
        ),
        Example(
            "数量上限",
            _limit,
            hint="选到 3 项后未选项转灰；先把一项取消，其余才重新可点。",
            code=_LIMIT_CODE,
        ),
    ],
    api=[
        Api("value", "list[str]", "[]", "已选项；改变后 Chip 与面板勾选同步"),
        Api("options", "list[str]", "[]", "全部可选项，文本即提交值"),
        Api(
            "searchable", "bool", "False", "展开后框内可键入，按文本忽略大小写过滤选项"
        ),
        Api("max_selected", "int | None", "None", "最多可选几项；到顶后未选项置灰"),
        Api("panel_height", "int | float", "260", "选项区最大高度，超出后内部滚动"),
        Api("width", "int | float", "320", "输入框与面板宽度"),
        Api("show_select_all", "bool", "True", "面板顶部是否给「全选」行"),
        Api("show_footer", "bool", "True", "是否显示「已选 N / M + 完成」页脚"),
        Api("disabled", "bool", "False", "禁用：框体压灰，不展开面板"),
        Api(
            "on_change",
            "Callable[[list[str]], None] | None",
            "None",
            "选择变化回调，拿到的是新列表副本",
        ),
    ],
    notes=[
        info(
            "面板挂 page.overlay 悬浮，不占布局高度；宿主走 page.render_views 时"
            "浮层会被视图盖住，组件自动降级为流内展开（此时下方内容会下移）。"
        ),
        info(
            "搜索与「全选」都只认可见项：全选不会偷偷带上被过滤掉的选项，"
            "否则清空搜索后会冒出一批没点过的选中项。"
        ),
        tip(
            "到上限后把未选项置灰，而不是「点了没反应」：多选最怕的是用户以为点上了，"
            "提交时才发现少一项。max_selected 就是为此提供的参数。"
        ),
    ],
    tags=("多选", "标签", "下拉", "multiselect", "搜索", "上限"),
)


if __name__ == "__main__":
    run(SPEC)
