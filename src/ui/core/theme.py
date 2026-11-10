"""主题运行时：明暗模式 + 品牌色板 + 声明式订阅。

框架层只做四件事：

1. **品牌色 → 整套色板**。不是把种子交给 Flutter 推导（那样品牌色会被
   tonalSpot 抽成灰扑扑的钢蓝），而是由 :mod:`ui.core.palette` 按可复算的规则
   产出 46 个角色，明暗各一套，一次性下发（见 :func:`build_theme`）。
2. **明暗模式** → ``page.theme`` / ``page.dark_theme`` + ``page.theme_mode``。
   两套主题都**预先建好**，所以切模式时 Flutter 只是换一棵现成的主题树，
   不需要在运行时重算色板 —— 这是"切主题不掉帧"的关键。
3. **表面策略** → 中性色要不要掺品牌色相（``neutral`` 几乎无色 / ``tonal``
   明显着色）。两种策略都只是换一组中性色，组件一行都不用改。
4. **把主题推给组件** → :func:`ThemeProvider` 组件 + :func:`use_theme` 订阅钩子。
   组件读一次 :attr:`ThemeState.mode` 就登记了依赖，模式一变自动重绘。

输入类控件的统一外观（描边、字号、内边距）也在这一层通过
``input_decoration_theme`` / ``text_field_theme`` 下发 —— 组件自己的设置优先，
没写的落到主题，见 :func:`build_theme`。

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

from ui.core import palette, typography
from ui.core.i18n import use_t
from ui.core.styles import outline_input
from ui.core.tokens import (
    PRIMARY_SEEDS,
    RADIUS,
    SEMANTIC_ROLES,
    SPACE,
    disabled_layer,
    semantic,
    semantic_text,
    state_layer,
)

__all__ = [
    "MODES",
    "SURFACES",
    "ThemeProvider",
    "ThemeState",
    "ThemeSwitcher",
    "apply_theme",
    "build_theme",
    "current_mode",
    "set_system_brightness",
    "theme_state",
    "use_theme",
]

#: ``ThemeState.mode`` 的合法取值
MODES: tuple[str, ...] = ("system", "light", "dark")

#: ``ThemeState.surfaces`` 的合法取值 —— 中性色**掺多少品牌色相**：
#:
#: * ``neutral`` —— 掺 0.006（OKLab 彩度）。看着仍是灰，但比三通道相等的纯灰
#:   "活"一点：屏幕上的纯灰偏闷，掺一丝主色相之后与按钮、图标同族。
#: * ``tonal`` —— 掺 0.014，能明显看出表面带一点主色的冷暖（旧版 M3 的着色
#:   表面）。想要"卡片有调性"就用它，代价是淡色块之间容易互相串色。
#:
#: 两个取值都远低于"能被叫作彩色"的门槛：中性色的职责是托住内容。
SURFACES: tuple[str, ...] = ("neutral", "tonal")


def _norm_mode(mode: str | None) -> str:
    """把模式归一到 ``system`` / ``light`` / ``dark``（非法值退回 ``system``）。

    ``mode`` 可能是任何东西 —— 调用方既会传字符串常量，也可能直接把
    ``theme_state().mode = 3`` 打进来。这里用 ``str()`` 兜住，
    **模式解析永远不该让整页崩掉**。
    """
    m = str(mode if mode is not None else "").strip().lower()
    return m if m in MODES else "system"


def _norm_surfaces(name: str | None) -> str:
    """把表面策略归一到 ``neutral`` / ``tonal``（非法值退回中性）。

    与 :func:`_norm_mode` 同理：写错一个枚举名不该让整页起不来，退回 1.1 的
    默认观感即可。
    """
    s = str(name if name is not None else "").strip().lower()
    return s if s in SURFACES else "neutral"


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
    primary: str = PRIMARY_SEEDS["blue"]  # 品牌色（palette 由它算出整套色板）
    #: 表面策略：``neutral``（Flet 1.1 默认）/ ``tonal``（旧的着色表面）。
    #: 放在状态里而不是写成常量，是因为"换一种表面"和"换主色"是同一类决定 ——
    #: 都由主题运行时统一下发，组件不需要知道。
    surfaces: str = "neutral"
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

    def set_surfaces(self, name: str) -> None:
        """切换表面策略（``neutral`` / ``tonal``）。

        中性表面是 Flet 1.1 的默认：容器是纯中性灰，主色只出现在强调色上。
        旧项目若依赖"淡主色底的容器"，把这里设成 ``tonal`` 即可整体回退，
        不用改任何组件。
        """
        self.surfaces = _norm_surfaces(name)

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
#: 而"在组件体里读 observable 字段"是**不会**订阅的（flet 1.x 只在
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


def text_theme() -> ft.TextTheme:
    """把排印系统铺到 Material 3 的十三个文字槽位上。

    **为什么必须显式写**：``ft.Text`` 不传 ``size`` 时用的是 Flutter 侧
    ``TextTheme.bodyMedium`` 的默认值 —— 那是框架外部的一份常量，flet 升级、
    Flutter 换版本、甚至 ``use_material3`` 开关一变，全局正文就可能从 14 漂到
    16 或 13。整个框架的正文字号必须由**自己**的令牌说了算，所以这里一次性把
    每个槽位都钉死，不留给默认值。

    **每个槽位给的是"四件套"而不只是字号**：字号、行高、字距、字重都来自
    :mod:`ui.core.typography`。只钉字号是过去做法留下的坑 —— 34px 的标题沿用
    正文的 1.618 行高，上下两块之间会空出一大截；11px 的标签又会被挤成一团。
    现在大小字各按各的律走，``ft.Text`` 不写 ``style`` 也能排对。

    映射关系（左 M3 槽位，右框架档位 — 与 :data:`~ui.core.typography.HEADING`
    的六级标题一致，顺序**必须**保持 H1 > H2 > … > H6）::

        display_small    36  display_lg     headline_medium  24  headline_lg
        headline_large   28  display        headline_small   20  headline
        title_large      20  headline       title_medium     16  title
        title_small      14  body           body_large       16  title
        body_medium      14  body (默认)    body_small       12  small
        label_large      14  body           label_medium     12  small
        label_small      11  caption

    ``body_medium`` 就是"正文 14"的落地点：``ft.Text``、``ft.ListTile``、
    ``ft.TextField``（另有 ``text_field_theme`` 兜底）都从这里取值。

    **每个槽位都必须带 ``color``**，这不是冗余：flet 把 ``TextStyle`` 下发给
    Flutter 时是**替换**而不是合并，只写 ``size`` 的样式会把颜色字段一并清掉 ——
    于是框架里所有"没显式指定 color"的文字全部画成透明。这个坑踩过一次：输入框
    标签、列表标题一片空白，而截图检测（灰块 / 溢出）一声不响，因为它们既没渲染
    失败也没撑破盒子。所以颜色一律给 M3 的 ``ON_SURFACE``，需要别的颜色时由控件
    自己覆盖。
    """
    def slot(name: str) -> ft.TextStyle:
        return typography.text_style(name, color=ft.Colors.ON_SURFACE)

    _fg = ft.Colors.ON_SURFACE
    return ft.TextTheme(
        display_small=slot("display_lg"),
        headline_large=slot("display"),
        headline_medium=slot("headline_lg"),
        headline_small=slot("headline"),
        title_large=slot("headline"),
        title_medium=slot("title"),
        title_small=slot("body"),
        body_large=slot("title"),
        body_medium=slot("body"),
        body_small=slot("small"),
        label_large=slot("body"),
        label_medium=slot("small"),
        label_small=slot("caption"),
    )


def build_theme(state: ThemeState, mode: str | None = None) -> ft.Theme:
    """由状态构造某一档模式的 :class:`flet.Theme`（**明暗各建一个**）。

    Args:
        state: 主题状态（品牌色、表面策略、字体）。
        mode: ``"light"`` / ``"dark"``；``None`` 取当前生效的那一档。

    **为什么要把 ColorScheme 全给，而不是只给种子**：种子的推导规则
    （tonalSpot）会把品牌色映射到固定的 tone 40 并大幅降彩度，``#1F6FEB``
    出来是 ``#465D91`` —— 品牌色被改成了另一种颜色。而界面里"一半跟着种子变、
    一半由我们写死"的状态更糟：主按钮和图表第一条曲线会是两个蓝。所以整套
    46 个角色都由 :func:`ui.core.palette.build_scheme` 一次算清，Flutter 只负责画。

    滚动条与路由动画按**桌面端**调过：Windows 上 4px 细滚动条、隐藏轨道
    （只在滚动时出现），路由切换不做横向滑动（桌面端该做的是淡入）。

    输入类控件的统一外观也在这里（Flet 1.1 的 ``input_decoration_theme`` /
    ``text_field_theme``）：**组件自己传的优先，没传的落在这里**。放在主题层
    而不是每个组件里复制一遍，是因为"输入框长什么样"是全局决定 —— 改一次
    全框架一致，也不会出现某个页面忘了写 ``border`` 就退回 Material 默认。
    """
    mode_name = mode if mode in ("light", "dark") else state.mode_name
    scheme = palette.build_scheme(
        state.primary, mode_name, surfaces=_norm_surfaces(state.surfaces)
    )
    return ft.Theme(
        # 只给 color_scheme，**不给** color_scheme_seed：两者并存时 Flutter 会
        # 忽略种子，但留着它等于写着"这里还在用种子推导"，读代码的人会以为
        # 改一个种子就能换肤 —— 实际换肤走的是上面这条 build_scheme。
        color_scheme=ft.ColorScheme(**scheme),
        use_material3=True,
        font_family=state.font_family,
        # 正文 14 的落地点：所有没写 size 的文字、以及 flet 内置控件（ListTile /
        # Dropdown / Tooltip / DatePicker …）的字号都从这套 text_theme 取。
        text_theme=text_theme(),
        # 表面策略在 palette 里已经兑现成具体的中性色值，这里显式写 neutral
        # 只是告诉 Flutter"别再自行推导表面"—— 否则它会在我们的色板之上再叠
        # 一层 tone 推导，把层次关系又搅乱。
        surfaces=ft.ThemeSurfaces.NEUTRAL,
        # 桌面端用鼠标点，不需要 Material 给每个可点元素强塞 48px 命中区 ——
        # 那会让 32 高的行、图标按钮、紧凑工具栏全部虚胖。
        material_tap_target_size=ft.MaterialTapTargetSize.SHRINK_WRAP,
        # ---- 下面这一组是 flet 1.1 里"散装"的颜色字段 -------------------
        # 它们不属于 ColorScheme，但 Flutter 里确实在用：canvas 是页面底色、
        # divider 是内置分隔线、hint 是占位符、disabled 是禁用文字。不给的话
        # 它们各自取 Flutter 的默认值 —— 于是框架的画布和内置控件的底色不是
        # 同一个白，正是"组件与框架不和谐"的典型来源。
        canvas_color=ft.Colors.SURFACE,
        scaffold_bgcolor=ft.Colors.SURFACE,
        card_bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
        divider_color=ft.Colors.OUTLINE_VARIANT,
        hint_color=ft.Colors.ON_SURFACE_VARIANT,
        disabled_color=disabled_layer("label"),
        unselected_control_color=ft.Colors.OUTLINE,
        # 交互三态统一走 M3 状态层（见 tokens.STATE），与自研组件同一套数字：
        # flet 内置的 ListTile / IconButton 划过时的亮度，才不会和框架的树、
        # 表格、菜单"差一档"。
        focus_color=state_layer("focus", role=ft.Colors.PRIMARY),
        hover_color=state_layer("hover"),
        highlight_color=state_layer("pressed"),
        splash_color=state_layer("pressed"),
        input_decoration_theme=ft.InputDecorationTheme(
            # 描边而不是填充块：填充是"一块灰"，和卡片底糊在一起；
            # 描边在任何底色上都能读出输入区的边界。
            border=outline_input(color=ft.Colors.OUTLINE_VARIANT),
            filled=False,
            dense=True,
            content_padding=ft.Padding.symmetric(
                horizontal=SPACE["3"], vertical=SPACE["2"]
            ),
            # 提示语与标签走排印档位：输入框里的字与页面正文用同一套行高，
            # 光标高度、垂直居中才会和 36px 的控件高度对上（Material 默认 16px
            # 的行盒会让光标顶到描边上）。
            hint_style=typography.text_style(
                "body", color=ft.Colors.ON_SURFACE_VARIANT
            ),
            label_style=typography.text_style(
                "body", color=ft.Colors.ON_SURFACE_VARIANT
            ),
            helper_style=typography.text_style(
                "caption", color=ft.Colors.ON_SURFACE_VARIANT
            ),
        ),
        # 编辑中的文字与框架正文同档（Material 默认 16，比正文大一号）
        text_field_theme=ft.TextFieldTheme(
            text_style=typography.text_style("body", color=ft.Colors.ON_SURFACE)
        ),
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
        # 菜单默认取 M3 的 surfaceContainerHigh（浅色下比卡片底更灰一档），
        # 浮在白底卡片上会显得脏。改用容器最低层（浅色比卡片更白、深色比底色
        # 更深），再补一点阴影，菜单才像「浮在页面上」而不是另一块面板。
        popup_menu_theme=ft.PopupMenuTheme(
            color=ft.Colors.SURFACE_CONTAINER_LOWEST,
            elevation=8,
            shape=ft.RoundedRectangleBorder(radius=10),
            # 1.1 新增：菜单项悬停高亮的圆角。不设的话是直角，跟容器圆角打架。
            border_radius=RADIUS["lg"],
            menu_padding=ft.Padding.symmetric(vertical=6),
            label_text_style=typography.text_style(
                "body", color=ft.Colors.ON_SURFACE
            ),
        ),
    )


def apply_theme(
    page: ft.Page,
    state: ThemeState | None = None,
    *,
    on_brightness: Callable[[str], None] | None = None,
) -> None:
    """把状态写进 ``page``，并挂一次系统亮度监听。

    **两套主题都写**（``theme`` + ``dark_theme``）：只写 ``theme`` 时，深色模式
    下 Flutter 拿不到为深色准备的那棵树，只能把我们给的浅色色板硬套上去 ——
    表现出来的就是"深色模式其实没生效"或者"切换时整页重算一遍色板"。两套都
    写出去之后，切模式只是换一棵现成的树，颜色一次都不用再算。

    幂等：重复调用不会重复挂监听（``system`` 模式下系统亮度变了才有意义）。
    """
    st = state or _state
    page.theme = build_theme(st, "light")
    page.dark_theme = build_theme(st, "dark")
    # 页面底色必须**显式**给：不写的话 flet 的根视图是透明的，露出 Flutter 的
    # 默认底色 —— 浅色下是纯白、深色下是 ``#121212``。而我们的表面色是
    # ``#F7F9FD`` / ``#141518``（带一点品牌色相），于是"页面上那块内容"和
    # "页面本身"是两个不同的白/黑，卡片与背景的层次全被抹平。
    page.bgcolor = ft.Colors.SURFACE
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
        st.platform_brightness = (
            "dark" if str(name).lower().endswith("dark") else "light"
        )
        if on_brightness:
            on_brightness(st.platform_brightness)

    page.on_platform_brightness_change = _on_change
    current = getattr(page, "platform_brightness", None)
    if current is not None:
        name = getattr(current, "value", current)
        st.platform_brightness = (
            "dark" if str(name).lower().endswith("dark") else "light"
        )


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
    deps = (
        state.mode,
        state.primary,
        state.platform_brightness,
        state.font_family,
        state.surfaces,
    )
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
    tr = use_t()

    def seed_label(key: str) -> str:
        """色板提示用本地色名；语言包没写就退回种子键名，不至于显示成键路径。"""
        path = f"ui.theme.seeds.{key}"
        return tr(path) if tr.has(path) else key

    current = tr("ui.theme.dark") if th.mode_name == "dark" else tr("ui.theme.light")
    # system 时告诉用户"跟随系统"，手动选过则直接说是哪种
    setting = current if th.mode == "system" else tr(f"ui.theme.{th.mode}")

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
                        tooltip=tr("ui.theme.primary", name=seed_label(name)),
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
                tooltip=tr("ui.theme.mode", mode=current, setting=setting),
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
                    ft.Text(
                        "设计令牌 + 主题运行时",
                        style=typography.text_style("headline"),
                    ),
                    ft.Text(
                        "下面的卡片、状态胶囊、按钮全部走 Material 3 角色色，"
                        "切明暗 / 换主色时不需要改任何一行组件代码。",
                        style=typography.text_style(
                            "body", color=ft.Colors.ON_SURFACE_VARIANT
                        ),
                    ),
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
                                                style=typography.text_style(
                                                    "body",
                                                    color=semantic_text(role),
                                                ),
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
