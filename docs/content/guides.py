"""四篇指南：架构、主题、多语言、响应式。"""

from __future__ import annotations

import flet as ft

from docs.blocks import (
    Doc,
    code,
    danger,
    h2,
    h3,
    note,
    p,
    split,
    tip,
    ul,
    warn,
)
from docs.content.live import (
    locale_playground,
    semantic_palette,
    theme_playground,
    token_scales,
)
from ui import Grid
from ui.core.tokens import FONT_SIZE, FONT_WEIGHT, RADIUS, SPACE, overlay

_MUTED = ft.Colors.ON_SURFACE_VARIANT

_TWO_KINDS = """# ① 静态控件：继承 Flet 原生控件，只改默认值
from ui import Card

Card(content=Text("Hello"), border_radius=12)


# ② 有状态组件：数据对象持有状态，ui() 负责渲染
from ui import Input


@ft.component
def Profile() -> ft.Control:
    name = ft.use_ref(lambda: Input(label="Name", width=240)).current
    return Column(spacing=12, controls=[name.ui()])"""

_PROVIDERS = '''@ft.component
def App() -> ft.Control:
    """语言最外层，主题其次，路由最内层。"""
    return I18nProvider(
        locale="zh-CN",
        build=lambda: ThemeProvider(build=router),
    )'''

_ROUTING = """ROUTES = [
    ft.Route(
        component=shell,              # 顶栏 + 侧边栏，切页不重建
        children=[
            ft.Route(index=True, component=HomePage),
            ft.Route(path="docs", component=DocsPage),
        ],
    ),
]


def main(page: ft.Page) -> None:
    page.render(
        lambda: ft.Router(ROUTES, not_found=NotFound, manage_views=False)
    )"""

_STATE = """@ft.component
def Orders() -> ft.Control:
    query, set_query = ft.use_state("")          # 局部状态
    rows = ft.use_memo(lambda: load(query), [query])   # 缓存昂贵计算
    table = ft.use_ref(lambda: Table(rows_per_page=10)).current  # 固定实例

    return Column(
        spacing=12,
        controls=[
            Input(label="Search", on_change=lambda e: set_query(e.control.value)).ui(),
            table,
        ],
    )"""

_THEME = """from ui import ThemeProvider, use_theme


@ft.component
def App() -> ft.Control:
    return ThemeProvider(build=shell)


@ft.component
def Palette() -> ft.Control:
    theme = use_theme()          # 订阅：切模式 / 换主色时重绘
    return Button(
        "Primary" if theme.is_dark else "Light",
        is_primary=True,
        on_click=lambda _: theme.toggle_mode(),
    )"""

_SURFACES = """from ui import theme_state

# 默认：灰里掺一丝品牌色相（浅色近白 / 深色深石板）
theme_state().set_surfaces("neutral")

# 更明显的着色表面：同一组色阶带上更多品牌色相
theme_state().set_surfaces("tonal")"""

_PALETTE = """from ui.core.palette import build_scheme, tonal

# 46 个角色一次算清（含明暗两套），直接下发给主题
ft.ColorScheme(**build_scheme("#1F6FEB", "light"))

# 十一档色阶：淡端淡而有色，深端沉而不浊，色相一度不漂
tonal("#1F6FEB")[600]      # '#3271D7'
tonal("#1F6FEB")[50]       # '#F4F8FF'"""

_TOKENS = """from ui import ELEVATION, RADIUS, SPACE

Container(
    padding=SPACE["4"],          # 16
    border_radius=RADIUS["md"],  # 12
    shadow=ELEVATION["2"],
)"""

_I18N_REGISTER = """from ui import register_messages

register_messages("zh-CN", {
    "app": {"title": "我的应用"},
    "hello": "你好，{name}",
    "cities": ["北京", "上海", "广州"],     # 成组文案：tr.list("cities")
})

register_messages("en-US", {
    "app.title": "My App",                  # 平铺写法等价
    "hello": "Hello, {name}",
    "cities": ["Beijing", "Shanghai", "Guangzhou"],
})"""

_I18N_USE = """from ui import use_t


@ft.component
def Greeting() -> ft.Control:
    tr = use_t()                    # 唯一的订阅点
    return Text(tr("hello", name="Shawn"))"""

_I18N_FORMAT = """from ui import calendar_title, format_date, format_number, weekday_names

format_number(1_287_640)          # 1,287,640   /   1,287,640
format_date(date(2026, 9, 26))    # 2026-09-26  /   09/26/2026
format_date(date(2026, 9, 26), long=True)
                                  # 2026年9月26日 / September 26, 2026
calendar_title(2026, 9)           # 2026年9月  /   September 2026
weekday_names()                   # ('一', …)   /   ('Mon', …)"""

ARCHITECTURE: Doc = (
    p("arch.intro"),
    h2("arch.layers.title"),
    p("arch.layers.desc"),
    ul(
        "arch.layers.point1",
        "arch.layers.point2",
        "arch.layers.point3",
        "arch.layers.point4",
    ),
    h2("arch.kinds.title"),
    p("arch.kinds.desc"),
    code(_TWO_KINDS, "components.py"),
    note("arch.kinds.note", "arch.kinds.note_title"),
    h2("arch.providers.title"),
    p("arch.providers.desc"),
    code(_PROVIDERS, "app.py"),
    tip("arch.providers.tip", "arch.providers.tip_title"),
    h2("arch.routing.title"),
    p("arch.routing.desc"),
    code(_ROUTING, "main.py"),
    danger("arch.routing.danger", "arch.routing.danger_title"),
    h2("arch.state.title"),
    p("arch.state.desc"),
    code(_STATE, "orders.py"),
    h3("arch.state.hooks"),
    ul("arch.state.point1", "arch.state.point2", "arch.state.point3"),
    h2("arch.perf.title"),
    p("arch.perf.desc"),
    ul("arch.perf.point1", "arch.perf.point2", "arch.perf.point3"),
)

THEMING: Doc = (
    p("theme.intro"),
    split(
        (
            h2("theme.live.title"),
            p("theme.live.desc"),
            ul("theme.live.point1", "theme.live.point2"),
        ),
        theme_playground,
    ),
    h2("theme.tokens.title"),
    p("theme.tokens.desc"),
    code(_TOKENS, "tokens.py"),
    split(
        (
            h3("theme.tokens.scale"),
            p("theme.tokens.scale_desc"),
        ),
        token_scales,
    ),
    h2("theme.semantic.title"),
    p("theme.semantic.desc"),
    split((p("theme.semantic.desc2"),), semantic_palette),
    h2("theme.palette.title"),
    p("theme.palette.desc"),
    code(_PALETTE, "core/palette.py"),
    p("theme.palette.desc2"),
    ul("theme.palette.point1", "theme.palette.point2", "theme.palette.point3"),
    h2("theme.modes.title"),
    p("theme.modes.desc"),
    code(_THEME, "theme.py"),
    h2("theme.surfaces.title"),
    p("theme.surfaces.desc"),
    code(_SURFACES, "surfaces.py"),
    p("theme.surfaces.tonal"),
    warn("theme.trap", "theme.trap_title"),
)

I18N: Doc = (
    p("i18n.intro"),
    split(
        (
            h2("i18n.live.title"),
            p("i18n.live.desc"),
            ul("i18n.live.point1", "i18n.live.point2"),
        ),
        locale_playground,
    ),
    h2("i18n.register.title"),
    p("i18n.register.desc"),
    code(_I18N_REGISTER, "i18n/catalog.py"),
    tip("i18n.register.tip", "i18n.register.tip_title"),
    h2("i18n.use.title"),
    p("i18n.use.desc"),
    code(_I18N_USE, "greeting.py"),
    h2("i18n.format.title"),
    p("i18n.format.desc"),
    code(_I18N_FORMAT, "format.py"),
    note("i18n.format.note", "i18n.format.note_title"),
    h2("i18n.fallback.title"),
    p("i18n.fallback.desc"),
    ul("i18n.fallback.point1", "i18n.fallback.point2", "i18n.fallback.point3"),
)


# ---------------------------------------------------------------------------
# 响应式
# ---------------------------------------------------------------------------
_RESP_GRID = """from ui import Grid

Grid(
    min_col_width=260,        # 一格至少多宽 —— 不是固定宽度
    max_cols=4,               # 再宽的屏也就 4 格
    controls=cards,           # 每个子项自动占一格
)"""

_RESP_HOOK = """from ui import use_responsive

@ft.component
def Shell() -> ft.Control:
    r = use_responsive()                  # 只在**跨档**时重绘
    return Row(controls=[
        None if r.is_compact else sidebar(),   # 窄屏收起侧栏
        content(expand=True),
    ])"""

_RESP_OWN = """# 部件量**自己**的宽度，不看窗口
PageLayout(
    title="用户管理",
    max_content_width="content",       # 宽屏居中限宽，窄屏自动失效
    controls=[table, Grid(min_col_width=240, controls=cards)],
)"""

_RESP_BREAK = """# 断点与 flet.ResponsiveRow 逐项相同（0 / 576 / 768 / 992 / 1200 / 1400）
size_class(700)    # 'compact'   —— 单列
size_class(900)    # 'medium'    —— 两列
size_class(1400)   # 'expanded'  —— 三栏 + 侧栏"""


@ft.component
def responsive_playground() -> ft.Control:
    """实时演示：拖滑块改容器宽度，栅格自己换列（换列在渲染层，Python 不算）。"""
    width, set_width = ft.use_state(720)
    tiles = [
        ft.Container(
            height=64,
            padding=SPACE["3"],
            border_radius=RADIUS["md"],
            bgcolor=overlay(0.05),
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            content=ft.Text(
                f"格 {i}",
                size=FONT_SIZE["body"],
                weight=FONT_WEIGHT["medium"],
            ),
        )
        for i in range(1, 7)
    ]
    return ft.Column(
        spacing=SPACE["3"],
        controls=[
            ft.Row(
                spacing=SPACE["3"],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text(
                        f"{width} px",
                        size=FONT_SIZE["body"],
                        weight=FONT_WEIGHT["semibold"],
                    ),
                    ft.Text(
                        "拖我改宽度 →",
                        size=FONT_SIZE["small"],
                        color=_MUTED,
                    ),
                ],
            ),
            ft.Slider(
                min=280,
                max=1100,
                value=width,
                label="{value} px",
                on_change=lambda e: set_width(int(float(e.control.value))),
            ),
            ft.Container(
                width=width,
                content=Grid(min_col_width=200, max_cols=4, controls=tiles),
            ),
        ],
    )


RESPONSIVE: Doc = (
    p("resp.intro"),
    h2("resp.rules.title"),
    p("resp.rules.desc"),
    ul(
        "resp.rules.point1",
        "resp.rules.point2",
        "resp.rules.point3",
        "resp.rules.point4",
    ),
    code(_RESP_BREAK, "core/responsive.py"),
    h2("resp.live.title"),
    split(
        (p("resp.live.desc"),),
        responsive_playground,
    ),
    h2("resp.grid.title"),
    p("resp.grid.desc"),
    code(_RESP_GRID, "grid.py"),
    tip("resp.grid.tip", "resp.grid.tip_title"),
    h2("resp.hook.title"),
    p("resp.hook.desc"),
    code(_RESP_HOOK, "shell.py"),
    warn("resp.hook.warn", "resp.hook.warn_title"),
    h2("resp.own.title"),
    p("resp.own.desc"),
    code(_RESP_OWN, "page.py"),
    note("resp.own.note", "resp.own.note_title"),
    h2("resp.boot.title"),
    p("resp.boot.desc"),
)
