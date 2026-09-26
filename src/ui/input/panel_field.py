"""带浮层面板的表单字段混入 (PanelField)。

``DateInput`` / ``DateTimeInput`` / ``ColorPicker`` 是同一类东西：**一个折叠态的
输入框 + 一块挂在页面浮层上的面板**。三者的差异只在"面板里画什么"，而下面这些
东西是逐像素一致的：

- 折叠态输入框：圆角 / 描边（常态 / 悬停 / 展开 / 非法）/ 内边距 / 内部清空按钮；
- 面板外壳：白底 + 1px 描边 + 圆角 + 阴影 + 统一内边距；
- 浮层定位：``place_panel`` 往下弹、放不下就向上翻转，左右收拢进窗口；
- 交互接缝：整框可点、点击外部收起、记录锚点坐标与实测尺寸、悬停 key 去抖、
  页脚文字按钮、面板内 1px 分隔线、``Label`` 的横 / 竖排版。

抽这一层的收益不是"少写几行"，而是**所有选择器的面板看起来是同一个东西**：
任何一个组件的圆角、阴影、展开描边改了，另外两个自动跟上。

宿主须提供以下字段（本混入只读不写）：

- ``value`` / ``disabled`` / ``clearable`` / ``is_open`` / ``float_panel``：
  决定折叠态外观与浮层行为；
- ``_invalid``：键入内容非法时框体转红边；
- ``_hover``：当前悬停元素的 key；
- ``_anchor`` / ``_field_w`` / ``_field_h``：输入框左上角页面坐标与实测尺寸；
- ``notify()``：由 ``@ft.observable`` 提供；``_hover_key()`` 由本混入提供。

与月历真正的耦合只剩 ``CalendarPanel`` 覆写的 ``_cal_*`` 钩子，见
:mod:`ui.input.calendar_panel`。
"""

from __future__ import annotations

from collections.abc import Callable

import flet as ft

from ui.core.float_layer import overlay_usable

__all__ = ["PanelField", "place_panel", "panel_shell"]

# ---------------------------------------------------------------------------
# 折叠态输入框
# ---------------------------------------------------------------------------
FIELD_WIDTH = 240  # 输入框默认宽度
FIELD_HEIGHT = 40  # 输入框高度
FIELD_RADIUS = 8  # 输入框 / 面板圆角
FIELD_PAD_H = 10  # 输入框左右内边距

# ---------------------------------------------------------------------------
# 面板
# ---------------------------------------------------------------------------
PANEL_PAD = 8  # 面板默认内边距
PANEL_GAP = 4  # 面板与输入框之间的间距（降级为流内展开时的行距）

# ---------------------------------------------------------------------------
# 面板里的小按钮
# ---------------------------------------------------------------------------
NAV_SIZE = 26  # 方形图标按钮
NAV_RADIUS = 6  # 小按钮圆角
LINK_RADIUS = 6  # 页脚文字按钮圆角（与月历的 CELL_RADIUS 同值）

# ---------------------------------------------------------------------------
# 字号
# ---------------------------------------------------------------------------
TEXT_SIZE = 13
SMALL_SIZE = 12
LABEL_SIZE = 11

SCREEN_MARGIN = 8  # 面板与窗口边缘的最小间距

# ---------------------------------------------------------------------------
# 配色（全部走主题色，明暗主题下都可用）
# ---------------------------------------------------------------------------
HOVER_BG = ft.Colors.with_opacity(0.06, ft.Colors.ON_SURFACE)  # 悬停底色
DISABLED_FG = ft.Colors.with_opacity(0.38, ft.Colors.ON_SURFACE)  # 禁用字色


# ---------------------------------------------------------------------------
# 纯函数工具
# ---------------------------------------------------------------------------
def _truthy(value: object) -> bool:
    """把 hover 事件载荷归一成布尔（可能是 bool，也可能是 ``"true"`` 字符串）。"""
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def place_panel(
    page: ft.Page,
    anchor: tuple[float, float] | None,
    field_h: float,
    panel_w: float,
    panel_h: float,
) -> tuple[float, float | None, float | None]:
    """面板定位：返回 ``(left, top, bottom)``，``top`` / ``bottom`` 二选一。

    默认从锚点（输入框）下沿往下弹；下方放不下就向上翻转、改用 ``bottom`` 锚定
    —— 这样面板多高都能自动贴住输入框上沿（``top`` 方式要求预先知道面板高度，
    高度估算的误差会变成一条可见的缝）。左右方向做边界收拢。

    两个都放不下时保持"向下弹"，让面板溢出到窗口外，也好过盖住输入框。
    """
    ax, ay = anchor or (0.0, 0.0)
    page_w = float(getattr(page, "width", 0) or 0)
    page_h = float(getattr(page, "height", 0) or 0)

    left = ax
    if page_w and left + panel_w > page_w - SCREEN_MARGIN:
        left = max(SCREEN_MARGIN, page_w - panel_w - SCREEN_MARGIN)

    top = ay + field_h + PANEL_GAP
    if page_h and top + panel_h > page_h - SCREEN_MARGIN:
        if ay - panel_h - PANEL_GAP >= SCREEN_MARGIN:
            return left, None, page_h - ay + PANEL_GAP
    return left, top, None


def panel_shell(
    *,
    width: float,
    body: ft.Control,
    pad: float = PANEL_PAD,
) -> ft.Control:
    """面板外壳：白底 + 1px 描边 + 圆角 + 阴影 + 统一内边距。

    所有选择器的面板都套这一层 —— 圆角、描边、阴影只在这里定义一次。
    """
    return ft.Container(
        width=width,
        bgcolor=ft.Colors.SURFACE,
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        border_radius=ft.BorderRadius.all(FIELD_RADIUS),
        padding=ft.Padding.symmetric(vertical=pad, horizontal=pad),
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        shadow=ft.BoxShadow(
            blur_radius=12,
            color=ft.Colors.with_opacity(0.10, ft.Colors.BLACK),
            offset=ft.Offset(0, 3),
        ),
        content=body,
    )


class PanelField:
    """折叠态输入框 + 浮层面板的通用外壳。见模块 docstring 的宿主契约。"""

    # ---- 宿主契约（由宿主类提供；这里列出便于对照） ----
    #   value / disabled / clearable / is_open / float_panel / _invalid / _hover /
    #   _anchor / _field_w / _field_h / width / height / notify()
    #   clear() / toggle_open()：由宿主实现

    # ------------------------------------------------------------------
    # 悬停去抖
    # ------------------------------------------------------------------
    def _hover_key(self, key: str, hovering: bool) -> None:
        """更新悬停元素（同一 key 重复进入 / 离开时提前返回，避免抖动）。"""
        if (self._hover == key) == hovering:  # type: ignore[attr-defined]
            return
        self._hover = key if hovering else None  # type: ignore[attr-defined]
        self.notify()  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # 折叠态输入框
    # ------------------------------------------------------------------
    @property
    def _fg(self) -> ft.ColorValue:
        """框内文字色：禁用时压灰。"""
        return (
            ft.Colors.OUTLINE if self.disabled else ft.Colors.ON_SURFACE  # type: ignore[attr-defined]
        )

    @property
    def _border_color(self) -> ft.ColorValue:
        """框体边框色：非法 > 展开 > 常态。"""
        if self.disabled:  # type: ignore[attr-defined]
            return ft.Colors.OUTLINE_VARIANT
        if self._invalid:  # type: ignore[attr-defined]
            return ft.Colors.ERROR
        if self.is_open:  # type: ignore[attr-defined]
            return ft.Colors.PRIMARY
        return ft.Colors.OUTLINE_VARIANT

    def _show_clear(self) -> bool:
        """是否显示框内 ×：可清空、未禁用、且当前有值。"""
        return (  # type: ignore[attr-defined]
            self.clearable and not self.disabled and self.value is not None
        )

    def _clear_button(self) -> ft.Control:
        """框内清空按钮。

        用 ``GestureDetector`` 而不是 ``Container.on_click``：后者在内层时会被
        外层 ``GestureDetector`` 抢走（真机实测，点 × 变成开合面板），同类型的
        tap 识别器才会按"内层优先"决出胜者。
        """
        return ft.GestureDetector(
            on_tap=lambda _e: self.clear(),  # type: ignore[attr-defined]
            content=ft.Container(
                padding=ft.Padding.all(3),
                border_radius=ft.BorderRadius.all(4),
                bgcolor=HOVER_BG if self._hover == "clear" else None,  # type: ignore[attr-defined]
                on_hover=lambda e: self._hover_key("clear", _truthy(e.data)),
                tooltip=ft.Tooltip(message="清除"),
                content=ft.Icon(ft.Icons.CLOSE, size=14, color=ft.Colors.OUTLINE),
            ),
        )

    def _build_field(self, text_field: ft.Control, trailing: ft.Control) -> ft.Control:
        """折叠态输入框 = 内容 + 可选 × + 尾图标，整体可点。

        关键在 ``text_field`` 的 ``ignore_pointers``：收起时必须让输入框不吃
        指针事件，否则外层 ``GestureDetector`` 永远收不到点击（flet 1.0 实测）。
        """
        controls: list[ft.Control] = [ft.Container(expand=True, content=text_field)]
        if self._show_clear():
            controls.append(self._clear_button())
        controls.append(trailing)

        box = ft.Container(
            width=self.width,  # type: ignore[attr-defined]
            height=self.height,  # type: ignore[attr-defined]
            bgcolor=ft.Colors.SURFACE_CONTAINER
            if self.disabled  # type: ignore[attr-defined]
            else ft.Colors.SURFACE,
            border=ft.Border.all(1, self._border_color),
            border_radius=ft.BorderRadius.all(FIELD_RADIUS),
            padding=ft.Padding.symmetric(horizontal=FIELD_PAD_H),
            on_size_change=None
            if self.disabled  # type: ignore[attr-defined]
            else self._on_field_size,
            size_change_interval=0,
            content=ft.Row(
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=controls,
            ),
        )
        if self.disabled:  # type: ignore[attr-defined]
            return box
        # 收起时整框都是"可点开面板"，展开后交回输入框自己的 I 形光标。
        return ft.GestureDetector(
            on_tap=self._on_field_tap,
            mouse_cursor=None if self.is_open else ft.MouseCursor.CLICK,  # type: ignore[attr-defined]
            content=box,
        )

    def _on_field_tap(self, e: ft.TapEvent) -> None:
        """记录输入框位置（浮层据此定位），再切换展开态。

        坐标只能从 ``GestureDetector`` 拿：``Container.on_click`` 的事件不带位置，
        而 ``TextField`` 的 ``on_click`` 同样如此。``global - local`` 就是控件
        左上角在页面客户区里的坐标。
        """
        gp = getattr(e, "global_position", None)
        lp = getattr(e, "local_position", None)
        if gp is not None and lp is not None:
            self._anchor = (gp.x - lp.x, gp.y - lp.y)  # type: ignore[attr-defined]
        self.toggle_open()  # type: ignore[attr-defined]

    def _on_field_size(self, e: ft.LayoutSizeChangeEvent) -> None:
        """记录输入框实测尺寸，浮层定位与遮罩挖洞都要用。"""
        w = getattr(e, "width", None)
        h = getattr(e, "height", None)
        changed = False
        if w and abs(w - self._field_w) > 0.5:  # type: ignore[attr-defined]
            self._field_w = float(w)  # type: ignore[attr-defined]
            changed = True
        if h and abs(h - self._field_h) > 0.5:  # type: ignore[attr-defined]
            self._field_h = float(h)  # type: ignore[attr-defined]
            changed = True
        if changed:
            self.notify()  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # 浮层
    # ------------------------------------------------------------------
    def _should_float(self, page: ft.Page) -> bool:
        """面板是否走页面浮层（``float_panel`` 显式指定优先）。"""
        if self.float_panel is not None:  # type: ignore[attr-defined]
            return self.float_panel  # type: ignore[attr-defined]
        return overlay_usable(page)

    def _hole(self) -> tuple[float, float, float, float] | None:
        """遮罩上给输入框挖的洞。"""
        if self._anchor is None:  # type: ignore[attr-defined]
            return None
        return (
            self._anchor[0],  # type: ignore[attr-defined]
            self._anchor[1],  # type: ignore[attr-defined]
            self._field_w,  # type: ignore[attr-defined]
            self._field_h,  # type: ignore[attr-defined]
        )

    # ------------------------------------------------------------------
    # 面板里的小控件
    # ------------------------------------------------------------------
    @staticmethod
    def _divider() -> ft.Control:
        """面板内的 1px 分隔线。"""
        return ft.Container(height=1, bgcolor=ft.Colors.OUTLINE_VARIANT)

    def _panel_shell(self, width: float, body: ft.Control) -> ft.Control:
        """面板外壳（见模块级 :func:`panel_shell`）。"""
        return panel_shell(width=width, body=body)

    def _nav_button(
        self,
        key: str,
        icon: ft.IconData,
        on_click: Callable[[], None],
        tooltip: str,
    ) -> ft.Control:
        """面板里的方形图标按钮（翻页 / 跳值 / 切换）。"""
        return ft.Container(
            width=NAV_SIZE,
            height=NAV_SIZE,
            alignment=ft.Alignment.CENTER,
            border_radius=ft.BorderRadius.all(NAV_RADIUS),
            bgcolor=HOVER_BG if self._hover == key else None,  # type: ignore[attr-defined]
            on_click=lambda _e: on_click(),
            on_hover=lambda e, k=key: self._hover_key(k, _truthy(e.data)),
            tooltip=ft.Tooltip(message=tooltip),
            content=ft.Icon(icon, size=18, color=ft.Colors.ON_SURFACE_VARIANT),
        )

    def _link_button(
        self,
        key: str,
        label: str,
        on_click: Callable[[], None],
        enabled: bool = True,
    ) -> ft.Control:
        """页脚的文字按钮。"""
        if not enabled:
            return ft.Container(
                padding=ft.Padding.symmetric(horizontal=6, vertical=4),
                content=ft.Text(label, size=SMALL_SIZE, color=DISABLED_FG),
            )
        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=6, vertical=4),
            border_radius=ft.BorderRadius.all(LINK_RADIUS),
            bgcolor=HOVER_BG if self._hover == key else None,  # type: ignore[attr-defined]
            on_click=lambda _e: on_click(),
            on_hover=lambda e, k=key: self._hover_key(k, _truthy(e.data)),
            content=ft.Text(label, size=SMALL_SIZE, color=ft.Colors.PRIMARY),
        )

    # ------------------------------------------------------------------
    # Label 排版
    # ------------------------------------------------------------------
    def _with_label(self, body: ft.Control) -> ft.Control:
        """按 ``v_label`` / ``is_vertical`` 把标签摆到内容旁。"""
        if self.v_label is None:  # type: ignore[attr-defined]
            return body
        if self.is_vertical:  # type: ignore[attr-defined]
            return ft.Column(
                controls=[self.v_label, body],  # type: ignore[attr-defined]
                spacing=self.spacing,  # type: ignore[attr-defined]
                horizontal_alignment=ft.CrossAxisAlignment.START,
            )
        return ft.Row(
            controls=[self.v_label, body],  # type: ignore[attr-defined]
            spacing=self.spacing,  # type: ignore[attr-defined]
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
