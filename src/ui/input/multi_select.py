"""多选下拉框 (MultiSelect)。

交互与视觉参考 Streamlit 的 ``st.multiselect``：

- 折叠态是一个带边框的输入框，已选项以 Chip 排列在框内，右端一个下拉箭头；
- 点击框体在下方展开选项面板：每行「复选框 + 文本」，选中行高亮为淡蓝底；
- 点选项即时切换（面板保持展开），点 Chip 上的 × 单独移除，点「全选」整组切换；
- 再次点击框体，或点面板右下角「完成」收起。

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

from ui.core.float_layer import overlay_usable, use_float_layer
from ui.input.input import Label

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
TEXT_SIZE = 13
CHIP_TEXT_SIZE = 12
DEFAULT_FIELD_HEIGHT = 40  # 尺寸上报前的兜底值
SCREEN_MARGIN = 8  # 面板与窗口边缘的最小间距

#: 选中行背景：淡蓝（对齐 Streamlit 的选中高亮）
SELECTED_BG = ft.Colors.with_opacity(0.12, ft.Colors.PRIMARY)
#: 悬停行背景：淡灰
HOVER_BG = ft.Colors.with_opacity(0.06, ft.Colors.ON_SURFACE)


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
        placeholder: 未选择任何项时框内的占位文本。
        width: 输入框与面板宽度，默认 320。
        panel_height: 选项区最大高度，超出后内部滚动，默认 260。
        show_select_all: 是否在面板顶部显示「全选」行（支持半选态），默认 True。
        show_footer: 是否显示「已选 N / M + 完成」页脚，默认 True。
        is_open: 面板是否展开（运行期状态，可代码控制）。
        disabled: 是否禁用。
        float_panel: 面板是否走页面浮层。``None``（默认）表示自动：
            浮层可用时悬挂，否则退化为流内展开。``True`` / ``False`` 强制指定。
        on_change: 选择变化回调，接收最新的已选列表副本。
    """

    value: list[str] = field(default_factory=list)
    options: list[str] = field(default_factory=list)
    placeholder: str = "请选择"
    width: int | float = 320
    panel_height: int | float = 260
    show_select_all: bool = True
    show_footer: bool = True
    is_open: bool = False
    disabled: bool = False
    float_panel: bool | None = None
    on_change: Callable[[list[str]], None] | None = None

    def __post_init__(self) -> None:
        # 运行期状态：当前鼠标悬停的行 key。下划线开头 => 不参与序列化，
        # 变更后靠 notify() 触发重绘。
        self._hover: str | None = None
        # 输入框左上角的页面坐标（点击时从事件里换算得到），浮层据此定位。
        self._anchor: tuple[float, float] | None = None
        # 输入框的实际高度（由 on_size_change 上报），Chip 换行时会变高。
        self._field_h: float = DEFAULT_FIELD_HEIGHT

    # ------------------------------------------------------------------
    # 公开操作
    # ------------------------------------------------------------------

    def select(self, option: str, selected: bool = True) -> None:
        """选中 / 取消选中单个选项。"""
        if selected:
            if option not in self.value:
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
        """全选 / 全不选。"""
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
        """已选内容的纯文本表示，便于日志 / 表单提交。"""
        return "、".join(self.value)

    @property
    def _fg(self) -> ft.ColorValue:
        """主文字色：禁用时整体压灰。"""
        return ft.Colors.OUTLINE if self.disabled else ft.Colors.ON_SURFACE

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
                min(float(self.panel_height), len(self.options) * ROW_HEIGHT),
            )
        else:
            total += ROW_HEIGHT
        if self.show_footer:
            total += 1 + FOOTER_HEIGHT
        return total

    def _panel_origin(
        self, page: ft.Page
    ) -> tuple[float, float | None, float | None]:
        """面板定位：返回 ``(left, top, bottom)``，``top`` / ``bottom`` 二选一。

        默认从输入框下沿往下弹；下方放不下就向上翻转，改用 ``bottom`` 锚定
        —— 这样面板多高都能自动贴住输入框上沿（``top`` 方式需要预先知道面板
        高度，估算误差会变成一条可见的缝）。
        """
        ax, ay = self._anchor or (0.0, 0.0)
        height = self._panel_height()
        page_h = float(getattr(page, "height", 0) or 0)

        top = ay + self._field_h + PANEL_GAP
        if page_h and top + height > page_h - SCREEN_MARGIN:
            if ay - height - PANEL_GAP >= SCREEN_MARGIN:
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
        """折叠态输入框：已选 Chip + 下拉箭头。

        点击监听走 ``GestureDetector.on_tap`` —— ``Container.on_click`` 的事件
        不带坐标，而浮层需要知道输入框在页面上的位置；``GestureDetector`` 的
        ``local_position`` 正好相对输入框，``global - local`` 即输入框左上角。

        Chip 的 ``×`` 同样用 ``GestureDetector``：``Container.on_click`` 在内层
        时会被外层 ``GestureDetector`` 抢走（真机实测，点 ``×`` 变成开合面板）；
        同类型的 tap 识别器才会按"内层优先"决出胜者。
        """
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
                    controls=[
                        ft.Row(
                            expand=True,
                            wrap=True,
                            spacing=6,
                            run_spacing=6,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=self._build_tokens(),
                        ),
                        ft.Icon(
                            ft.Icons.ARROW_DROP_UP
                            if self.is_open
                            else ft.Icons.ARROW_DROP_DOWN,
                            size=20,
                            color=ft.Colors.OUTLINE,
                        ),
                    ],
                ),
            ),
        )

    def _build_tokens(self) -> list[ft.Control]:
        """框内内容：已选 Chip，或占位文本。"""
        if not self.value:
            return [
                ft.Text(
                    self.placeholder,
                    size=TEXT_SIZE,
                    color=ft.Colors.OUTLINE,
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
                size=13,
                color=ft.Colors.OUTLINE
                if self.disabled
                else ft.Colors.ON_SURFACE_VARIANT,
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

    def _build_panel(self) -> ft.Control:
        """展开面板：全选行 + 可滚动选项列表 + 页脚。"""
        blocks: list[ft.Control] = []

        if self.show_select_all:
            blocks.append(self._build_select_all_row())
            blocks.append(ft.Divider(height=1))

        if self.options:
            blocks.append(
                ft.Column(
                    controls=[self._build_option_row(o) for o in self.options],
                    spacing=0,
                    height=max(
                        ROW_HEIGHT,
                        min(float(self.panel_height), len(self.options) * ROW_HEIGHT),
                    ),
                    scroll=ft.ScrollMode.AUTO,
                )
            )
        else:
            blocks.append(
                ft.Container(
                    height=ROW_HEIGHT,
                    padding=ft.Padding.symmetric(horizontal=PANEL_PAD + 8),
                    alignment=ft.Alignment.CENTER_LEFT,
                    content=ft.Text("暂无可选项", size=CHIP_TEXT_SIZE, color=ft.Colors.OUTLINE),
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
        """「全选」行，支持「全选 / 半选 / 未选」三态。"""
        checked = self.all_selected
        if checked:
            icon = ft.Icons.CHECK_BOX
        elif self.partially_selected:
            icon = ft.Icons.INDETERMINATE_CHECK_BOX
        else:
            icon = ft.Icons.CHECK_BOX_OUTLINE_BLANK
        return self._build_row(
            key="__all__",
            label="全选",
            icon=icon,
            highlighted=checked,
            on_click=lambda _e: self.select_all(not self.all_selected),
        )

    def _build_option_row(self, option: str) -> ft.Control:
        """单个选项行。"""
        selected = option in self.value
        return self._build_row(
            key=option,
            label=option,
            icon=ft.Icons.CHECK_BOX if selected else ft.Icons.CHECK_BOX_OUTLINE_BLANK,
            highlighted=selected,
            on_click=lambda _e, opt=option: self.toggle(opt),
        )

    def _build_row(
        self,
        *,
        key: str,
        label: str,
        icon: ft.IconData,
        highlighted: bool,
        on_click: Callable[[ft.ControlEvent], None],
    ) -> ft.Control:
        """选项行的公共骨架：整行可点，图标即复选框。"""
        if highlighted:
            bgcolor: ft.ColorValue | None = SELECTED_BG
        elif self._hover == key:
            bgcolor = HOVER_BG
        else:
            bgcolor = None

        return ft.Container(
            height=ROW_HEIGHT,
            margin=ft.Margin.symmetric(horizontal=PANEL_PAD),
            padding=ft.Padding.symmetric(horizontal=8),
            border_radius=ft.BorderRadius.all(ROW_RADIUS),
            bgcolor=bgcolor,
            on_click=None if self.disabled else on_click,
            on_hover=None
            if self.disabled
            else (lambda e, k=key: self._hover_row(k, _truthy(e.data))),
            content=ft.Row(
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(
                        icon,
                        size=18,
                        color=ft.Colors.PRIMARY if highlighted else ft.Colors.OUTLINE,
                    ),
                    ft.Text(
                        label,
                        size=TEXT_SIZE,
                        color=self._fg,
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
                        f"已选 {len(self.value)} / {len(self.options)}",
                        size=CHIP_TEXT_SIZE,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                    ft.TextButton(
                        content=ft.Text("完成", size=CHIP_TEXT_SIZE),
                        on_click=lambda _e: self.close(),
                    ),
                ],
            ),
        )


@ft.component
def App():
    """MultiSelect 组件运行示例。"""
    page = ft.context.page
    tags = MultiSelect(
        label="技术栈",
        options=[
            "Python", "Flet", "FastAPI", "SQLite",
            "Docker", "Redis", "Nginx", "PostgreSQL",
        ],
        value=["Python", "Flet"],
        is_required=True,
    )
    channels = MultiSelect(
        label="通知渠道",
        options=["站内信", "邮件", "短信", "企业微信", "钉钉"],
        value=["站内信", "邮件"],
        is_vertical=True,
        show_select_all=False,
        panel_height=160,
    )
    frozen = MultiSelect(
        label="只读",
        options=["A", "B", "C"],
        value=["A"],
        disabled=True,
    )

    return ft.Column(
        controls=[
            ft.Text("MultiSelect 多选下拉框", size=20, weight=ft.FontWeight.BOLD),
            ft.Text("点击输入框展开选项面板，已选项以 Chip 汇总", size=13, color="#6b7280"),
            ft.Divider(),
            tags.ui(),
            ft.Divider(),
            channels.ui(),
            ft.Divider(),
            frozen.ui(),
            ft.Divider(),
            ft.Button(
                content="打印当前值",
                on_click=lambda _: print(
                    f"技术栈: {tags.value} / 通知: {channels.value}"
                ),
            ),
        ],
        spacing=16,
    )


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
