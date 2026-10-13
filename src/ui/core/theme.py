"""主题运行时：明暗模式 + 主色种子 + 声明式订阅。

框架层只做三件事，其余交给 Flutter：

1. **主色种子** → ``ft.Theme(color_scheme_seed=...)``。Flutter 由这一个色值
   **推导整套 Material 3 色板**（``primary`` / ``secondary`` / ``surface`` /
   ``surface_container`` / ``outline`` … 共 52 个角色），所以"换主色"是改一个字符串
   的事，不需要维护任何调色板表。
2. **明暗模式** → ``page.theme_mode``（``SYSTEM`` / ``LIGHT`` / ``DARK``）。
   ``SYSTEM`` 时跟随系统，监听 :attr:`flet.Page.platform_brightness` 的变化。
3. **把主题推给组件** → :func:`ThemeProvider` 组件 + :func:`use_theme` 订阅钩子。
   组件读一次 :attr:`ThemeState.mode` 就登记了依赖，模式一变自动重绘。

用法（应用入口）::

    import flet as ft
    from ui import ft
    from ui.core.theme import ThemeProvider

    @ft.component
    def App():
        return ThemeProvider(build=lambda: MainShell())

    ft.run(lambda page: page.render(App()))

用法（组件内）::

    @ft.component
    def MyWidget():
        th = use_theme()          # 订阅：主题一变就重绘
        return ft.Text("就绪", color=semantic("success", th.mode_name))
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import flet as ft

from ui.core.tokens import (
    PRIMARY_SEEDS,
    SEMANTIC_ROLES,
    semantic,
    semantic_text,
)

__all__ = [
    "MODES",
    "ThemeState",
    "theme_state",
    "current_mode",
    "use_theme",
    "build_theme",
    "apply_theme",
    "ThemeProvider",
    "ThemeSwitcher",
    "set_system_brightness",
]

#: ``ThemeState.mode`` 的合法取值
MODES: tuple[str, ...] = ("system", "light", "dark")


def _norm_mode(mode: str | None) -> str:
    """把模式归一到 ``system`` / ``light`` / ``dark``（非法值退回 ``system``）。

    ``mode`` 可能是任何东西 —— 调用方既会传字符串常量，也可能直接把
    ``theme_state().mode = 3`` 打进来。这里用 ``str()`` 兜住，
    **模式解析永远不该让整页崩掉**。
    """
    m = str(mode if mode is not None else "").strip().lower()
    return m if m in MODES else "system"


@ft.observable
@dataclass
class ThemeState:
    """全局主题状态。

    这是一个**模块级单例**（:func:`theme_state`），由 :func:`ThemeProvider` 负责
    写进 ``page``。选单例而不是 context，是因为主题在 flet 里本来就是全局的
    （``page.theme`` / ``page.theme_mode``），再造一层 context 只会让"这个颜色
    到底跟谁走"变得难查。
    """

    mode: str = "system"  # system / light / dark
    primary: str = PRIMARY_SEEDS["blue"]  # 品牌色种子（喂给 color_scheme_seed）
    font_family: str | None = None  # None = 用 Flutter 默认
    platform_brightness: str = "light"  # 系统亮度，仅 mode=="system" 时生效
    _bound: bool = False  # 是否已挂过 platform_brightness 监听

    # ---- 查询 ----

    @property
    def mode_name(self) -> str:
        """当前**实际生效**的模式（``system`` 已解析成 ``light`` / ``dark``）。"""
        if self.mode in ("light", "dark"):
            return self.mode
        return "dark" if self.platform_brightness == "dark" else "light"

    @property
    def is_dark(self) -> bool:
        return self.mode_name == "dark"

    # ---- 变更（自动通知，触发订阅者重绘） ----

    def set_mode(self, mode: str) -> None:
        self.mode = _norm_mode(mode)

    def set_primary(self, primary: str) -> None:
        """换品牌色种子。非法输入退回默认种子 —— 颜色由 Flutter 解析，
        给错值最多是"看不出主色"，不该抛。"""
        text = str(primary).strip() if primary is not None else ""
        self.primary = text or PRIMARY_SEEDS["blue"]

    def toggle_mode(self) -> None:
        """明暗互切 —— 永远切到与**当前看到的**相反的那一档。

        给顶栏的☀ / 🌙 按钮用：无论当前是 ``system`` 还是已固定，点一下
        一定要看到画面变了。``system`` + 系统浅色 → 切到 ``dark``；
        若改成"冻成 light"，按钮就变成"点了没反应"，是最伤直觉的一种 bug。
        """
        self.mode = "light" if self.mode_name == "dark" else "dark"

    def cycle_mode(self) -> None:
        """``system`` → ``light`` → ``dark`` → ``system``（三态循环，给下拉用）。"""
        idx = MODES.index(_norm_mode(self.mode))
        self.mode = MODES[(idx + 1) % len(MODES)]


#: 进程级单例
_state = ThemeState()

#: 主题 context。默认值就是上面的单例，所以**没挂 Provider 也能用**；
#: 真正的价值在于 :func:`ft.use_context` 碰到 ``Observable`` 值会**自动订阅** ——
#: 而"在组件体里读 observable 字段"是**不会**订阅的（flet 1.0.4 只在
#: 「组件参数是 Observable」「use_state」「use_context」这三处订阅）。
#: 换句话说：走 context 才有声明式的自动重绘，直接读全局单例是静默失效的。
theme_context = ft.create_context(default_value=_state)


def theme_state() -> ThemeState:
    """拿到全局主题状态单例。

    组件里请用 :func:`use_theme` —— 它会自动订阅、主题一变就重绘；
    这个函数只是给**非组件环境**（启动代码、单测）用的。
    """
    return _state


def current_mode() -> str:
    """当前实际生效的模式（``"light"`` / ``"dark"``）。

    给 :mod:`ui.core.tokens` 的 :func:`~ui.core.tokens.semantic` 做隐式默认值用 ——
    所以它是模块级函数而不是需要传参的显式依赖。
    """
    return _state.mode_name


def use_theme() -> ThemeState:
    """订阅全局主题。**必须在组件体内调用**。

    flet 的 ``use_context`` 会在拿到 ``Observable`` 值时自动挂订阅，所以这里
    读到的状态一变，本组件就重绘 —— 调用方不需要手动 ``page.update()``，
    也不需要用 ``use_state`` 镜像一份（镜像一份就会漏更新）。
    """
    return ft.use_context(theme_context)


def build_theme(state: ThemeState) -> ft.Theme:
    """由状态构造 :class:`flet.Theme`。

    滚动条与路由动画按**桌面端**调过：Windows 上 4px 细滚动条、隐藏轨道
    （只在滚动时出现），路由切换不做横向滑动（桌面端该做的是淡入）。
    """
    return ft.Theme(
        color_scheme_seed=state.primary,
        use_material3=True,
        font_family=state.font_family,
        scrollbar_theme=ft.ScrollbarTheme(
            thickness=4,
            radius=10,
            main_axis_margin=5,
            cross_axis_margin=-10,
            track_visibility=False,
            thumb_visibility=False,
            track_color={ft.ControlState.DEFAULT: ft.Colors.TRANSPARENT},
            thumb_color={
                ft.ControlState.HOVERED: ft.Colors.TRANSPARENT,
                ft.ControlState.DEFAULT: ft.Colors.TRANSPARENT,
            },
        ),
        page_transitions=ft.PageTransitionsTheme(
            android=ft.PageTransitionTheme.NONE,
            ios=ft.PageTransitionTheme.NONE,
            macos=ft.PageTransitionTheme.NONE,
            windows=ft.PageTransitionTheme.NONE,
            linux=ft.PageTransitionTheme.NONE,
        ),
    )


def apply_theme(
    page: ft.Page,
    state: ThemeState | None = None,
    *,
    on_brightness: Callable[[str], None] | None = None,
) -> None:
    """把状态写进 ``page``，并挂一次系统亮度监听。

    幂等：重复调用不会重复挂监听（``system`` 模式下系统亮度变了才有意义）。
    """
    st = state or _state
    page.theme = build_theme(st)
    page.theme_mode = (
        ft.ThemeMode.SYSTEM
        if st.mode == "system"
        else (ft.ThemeMode.DARK if st.mode == "dark" else ft.ThemeMode.LIGHT)
    )
    if st._bound:
        return
    st._bound = True

    def _on_change(e: ft.PlatformBrightnessChangeEvent) -> None:
        value = getattr(e, "brightness", None)
        name = getattr(value, "value", value)
        st.platform_brightness = "dark" if str(name).lower().endswith("dark") else "light"
        if on_brightness:
            on_brightness(st.platform_brightness)

    page.on_platform_brightness_change = _on_change
    current = getattr(page, "platform_brightness", None)
    if current is not None:
        name = getattr(current, "value", current)
        st.platform_brightness = "dark" if str(name).lower().endswith("dark") else "light"


@ft.component
def ThemeProvider(*, build: Callable[[], ft.Control]) -> ft.Control:
    """把全局主题挂到页面，并在主题变化时重新下发。

    必须放在**根视图**里（``page.render(lambda: ThemeProvider(build=...))``）——
    它要写 ``page.theme``，写在页面组件里会晚一帧，表现为"切模式闪一下旧配色"。

    Args:
        build: **工厂函数**，返回应用主体。必须是函数而不是现成的控件：
            本组件靠它把 ``build()`` 的结果缓存起来（``use_memo`` + 空依赖），
            使得"主题变了"只重新下发配色，**不重建整棵控件树** ——
            否则用户在表单里填了一半的内容会被主题切换清空。

    ``build`` 用关键字传：做成位置参数很容易和"传一个控件"的直觉撞车。
    """
    return _ThemeBridge(state=_state, build=build)


@ft.component
def _ThemeBridge(*, state: ThemeState, build: Callable[[], ft.Control]) -> ft.Control:
    """订阅主题并把它写进 ``page``。

    ``state`` 是 **Observable 类型的组件参数** —— flet 会因此自动给本组件挂订阅
    （见 ``Component._subscribe_observable_args``），主题一变本组件就重跑一遍
    ``use_effect``。这是不依赖私有 API 的唯一可靠做法。
    """
    page = ft.context.page
    deps = (state.mode, state.primary, state.platform_brightness, state.font_family)
    # 空依赖 -> 只在首次渲染调用一次，主题变化时复用同一棵子树
    node = ft.use_memo(build, [])
    ft.use_effect(lambda: apply_theme(page, state), list(deps))
    return node


def set_system_brightness(name: str) -> None:
    """测试与无平台环境下直接设定系统亮度（``"light"`` / ``"dark"``）。"""
    _state.platform_brightness = "dark" if str(name).lower() == "dark" else "light"


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
@ft.component
def ThemeSwitcher(*, compact: bool = False) -> ft.Control:
    """主色色板 + 明暗开关。框架应用可以直接把它放进顶栏。"""
    th = use_theme()
    return ft.Row(
        spacing=8,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            *(
                []
                if compact
                else [
                    ft.Container(
                        width=18,
                        height=18,
                        tooltip=f"主色 · {name}",
                        border_radius=ft.BorderRadius.all(4),
                        bgcolor=seed,
                        border=ft.Border.all(
                            2,
                            (
                                ft.Colors.ON_SURFACE
                                if th.primary.lower() == seed.lower()
                                else ft.Colors.TRANSPARENT
                            ),
                        ),
                        on_click=lambda _e, v=seed: th.set_primary(v),
                    )
                    for name, seed in PRIMARY_SEEDS.items()
                ]
            ),
            ft.IconButton(
                icon=(
                    ft.Icons.LIGHT_MODE
                    if th.mode_name == "dark"
                    else ft.Icons.DARK_MODE
                ),
                tooltip=f"明暗：当前 {'深色' if th.mode_name == 'dark' else '浅色'}"
                        f"（{'跟随系统' if th.mode == 'system' else th.mode}）",
                on_click=lambda _e: th.toggle_mode(),
            ),
        ],
    )


@ft.component
def App() -> ft.Control:
    """主题模块运行示例。"""
    return ThemeProvider(
        build=lambda: ft.Container(
            expand=True,
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
            padding=24,
            content=ft.Column(
                spacing=16,
                controls=[
                    ft.Text("设计令牌 + 主题运行时", size=20,
                            weight=ft.FontWeight.W_600),
                    ft.Text("下面的卡片、状态胶囊、按钮全部走 Material 3 角色色，"
                            "切明暗 / 换主色时不需要改任何一行组件代码。",
                            size=13, color=ft.Colors.ON_SURFACE_VARIANT),
                    ft.Row(
                        spacing=12,
                        controls=[
                            ft.Button("主要按钮"),
                            ft.FilledTonalButton("次要按钮"),
                            ThemeSwitcher(),
                        ],
                    ),
                    ft.Container(
                        padding=14,
                        border_radius=ft.BorderRadius.all(8),
                        bgcolor=ft.Colors.SURFACE,
                        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                        content=ft.Column(
                            spacing=8,
                            controls=[
                                *(
                                    ft.Row(
                                        spacing=10,
                                        controls=[
                                            ft.Container(
                                                width=14,
                                                height=14,
                                                border_radius=ft.BorderRadius.all(3),
                                                bgcolor=semantic(role),
                                            ),
                                            ft.Text(
                                                f"{role:<8} {semantic(role)}",
                                                size=13,
                                                color=semantic_text(role),
                                            ),
                                        ],
                                    )
                                    for role in SEMANTIC_ROLES
                                ),
                            ],
                        ),
                    ),
                ],
            ),
        )
    )