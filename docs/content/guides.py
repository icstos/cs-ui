"""三篇指南：架构、主题、多语言。"""

from __future__ import annotations

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

_TWO_KINDS = '''# ① 静态控件：继承 Flet 原生控件，只改默认值
from ui import Card

Card(content=Text("Hello"), border_radius=12)


# ② 有状态组件：数据对象持有状态，ui() 负责渲染
from ui import Input


@ft.component
def Profile() -> ft.Control:
    name = ft.use_ref(lambda: Input(label="Name", width=240)).current
    return Column(spacing=12, controls=[name.ui()])'''

_PROVIDERS = '''@ft.component
def App() -> ft.Control:
    """语言最外层，主题其次，路由最内层。"""
    return I18nProvider(
        locale="zh-CN",
        build=lambda: ThemeProvider(build=router),
    )'''

_ROUTING = '''ROUTES = [
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
    )'''

_STATE = '''@ft.component
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
    )'''

_THEME = '''from ui import ThemeProvider, use_theme


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
    )'''

_TOKENS = '''from ui import ELEVATION, RADIUS, SPACE

Container(
    padding=SPACE["4"],          # 16
    border_radius=RADIUS["md"],  # 12
    shadow=ELEVATION["2"],
)'''

_I18N_REGISTER = '''from ui import register_messages

register_messages("zh-CN", {
    "app": {"title": "我的应用"},
    "hello": "你好，{name}",
    "cities": ["北京", "上海", "广州"],     # 成组文案：tr.list("cities")
})

register_messages("en-US", {
    "app.title": "My App",                  # 平铺写法等价
    "hello": "Hello, {name}",
    "cities": ["Beijing", "Shanghai", "Guangzhou"],
})'''

_I18N_USE = '''from ui import use_t


@ft.component
def Greeting() -> ft.Control:
    tr = use_t()                    # 唯一的订阅点
    return Text(tr("hello", name="Shawn"))'''

_I18N_FORMAT = '''from ui import calendar_title, format_date, format_number, weekday_names

format_number(1_287_640)          # 1,287,640   /   1,287,640
format_date(date(2026, 9, 26))    # 2026-09-26  /   09/26/2026
format_date(date(2026, 9, 26), long=True)
                                  # 2026年9月26日 / September 26, 2026
calendar_title(2026, 9)           # 2026年9月  /   September 2026
weekday_names()                   # ('一', …)   /   ('Mon', …)'''

ARCHITECTURE: Doc = (
    p("arch.intro"),
    h2("arch.layers.title"),
    p("arch.layers.desc"),
    ul("arch.layers.point1", "arch.layers.point2", "arch.layers.point3", "arch.layers.point4"),
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
        ratio=(5, 6),
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
        ratio=(5, 6),
    ),
    h2("theme.semantic.title"),
    p("theme.semantic.desc"),
    split((p("theme.semantic.desc2"),), semantic_palette, ratio=(5, 6)),
    h2("theme.modes.title"),
    p("theme.modes.desc"),
    code(_THEME, "theme.py"),
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
        ratio=(5, 6),
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
