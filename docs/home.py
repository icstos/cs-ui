"""首页：先让人看懂"这是什么"，再让人想动手。"""

from __future__ import annotations

import flet as ft

from docs import kit
from docs.shell import site_footer
from docs.site import (
    CATEGORIES,
    COMPONENT_TOTAL,
    GITHUB_URL,
    PACKAGE_VERSION,
    PYTHON_VERSION,
)
from ui import (
    Button,
    Checkbox,
    Chip,
    Input,
    LineChart,
    ProgressBar,
    Rating,
    Switch,
    toast_success,
    use_t,
)
from ui.core.theme import use_theme

_MAX = 960


# ---------------------------------------------------------------------------
# 小道具
# ---------------------------------------------------------------------------


def _centered(content: ft.Control, *, padding: int = 40) -> ft.Control:
    """内容居中到一个最大宽度，窗口再宽也不会拉成一条长线。

    960 是「最小窗口 1040 减去左右各 40」的余量，窄窗口下也不会顶出边界。
    """
    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=padding),
        alignment=ft.Alignment.TOP_CENTER,
        content=ft.Container(width=_MAX, content=content),
    )


def _chip_row() -> list[ft.Control]:
    tr = use_t()
    return [
        kit.badge(
            tr("home.meta.python", version=PYTHON_VERSION),
            tone="info",
            icon=ft.Icons.TERMINAL,
        ),
        kit.badge("Flet 1.0.5", tone="success", icon=ft.Icons.BOLT),
        kit.badge(tr("home.meta.license"), tone="neutral", icon=ft.Icons.GAVEL),
    ]


# ---------------------------------------------------------------------------
# 首屏
# ---------------------------------------------------------------------------


@ft.component
def _window() -> ft.Control:
    """一个"正在运行的 cs-ui 应用"缩略：全是真控件，不是截图。"""
    tr = use_t()
    theme = use_theme()

    rail_icons = (
        ft.Icons.DASHBOARD_OUTLINED,
        ft.Icons.INSIGHTS_OUTLINED,
        ft.Icons.FOLDER_OUTLINED,
        ft.Icons.SETTINGS_OUTLINED,
    )
    rail = ft.Container(
        width=46,
        padding=ft.Padding.symmetric(vertical=12),
        border=ft.Border(right=ft.BorderSide(1, kit.BORDER)),
        content=ft.Column(
            spacing=6,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=30,
                    height=30,
                    border_radius=9,
                    bgcolor=ft.Colors.PRIMARY_CONTAINER,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Icon(
                        ft.Icons.AUTO_AWESOME, size=16, color=ft.Colors.PRIMARY
                    ),
                ),
                *[
                    ft.Container(
                        width=30,
                        height=30,
                        border_radius=9,
                        alignment=ft.Alignment.CENTER,
                        content=ft.Icon(icon, size=16, color=kit.MUTED),
                    )
                    for icon in rail_icons
                ],
            ],
        ),
    )

    def tile(value: str, label: str, delta: str, tone: str) -> ft.Control:
        return ft.Container(
            expand=True,
            padding=12,
            border_radius=11,
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border=ft.Border.all(1, kit.BORDER),
            content=ft.Column(
                spacing=4,
                controls=[
                    ft.Text(label, size=10.5, color=kit.MUTED),
                    ft.Row(
                        spacing=6,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text(value, size=19, weight=ft.FontWeight.W_700),
                            kit.badge(delta, tone=tone),
                        ],
                    ),
                ],
            ),
        )

    chart = LineChart(
        data={
            "m": ["1", "2", "3", "4", "5", "6", "7", "8"],
            "v": [42, 58, 51, 76, 68, 92, 86, 110],
        },
        x="m",
        y=["v"],
        height=132,
        show_grid=False,
        show_legend=False,
        show_x_labels=False,
        tooltip=False,
        curved=True,
        stroke_width=2.5,
        color=theme.primary,
    )

    body = ft.Column(
        expand=True,
        spacing=12,
        controls=[
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Column(
                        spacing=1,
                        controls=[
                            ft.Text(
                                tr("home.window.title"),
                                size=13.5,
                                weight=ft.FontWeight.W_700,
                            ),
                            ft.Text(
                                tr("home.window.subtitle"),
                                size=10.5,
                                color=kit.MUTED,
                            ),
                        ],
                    ),
                    ft.CircleAvatar(
                        content=ft.Text("SC", size=10, weight=ft.FontWeight.W_700),
                        bgcolor=ft.Colors.PRIMARY_CONTAINER,
                        color=ft.Colors.PRIMARY,
                        radius=13,
                    ),
                ],
            ),
            ft.Row(
                spacing=10,
                controls=[
                    tile(
                        tr("home.window.stat1"),
                        tr("home.window.stat1_label"),
                        "+12%",
                        "success",
                    ),
                    tile(
                        tr("home.window.stat2"),
                        tr("home.window.stat2_label"),
                        "+4%",
                        "info",
                    ),
                ],
            ),
            ft.Container(
                padding=ft.Padding.only(left=4, right=4, top=8),
                border_radius=11,
                bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
                border=ft.Border.all(1, kit.BORDER),
                content=ft.Column(
                    spacing=6,
                    controls=[
                        ft.Container(
                            padding=ft.Padding.only(left=10, top=9),
                            content=ft.Text(
                                tr("home.window.chart"),
                                size=10.5,
                                color=kit.MUTED,
                            ),
                        ),
                        chart,
                    ],
                ),
            ),
        ],
    )

    return ft.Container(
        # 伪窗口是插图，给它固定高度：里面的 Row/Column 都靠 expand 分配空间，
        # 而滚动列表里的高度是无界的，不给定高度就会整块画不出来。
        height=360,
        border_radius=16,
        bgcolor=ft.Colors.SURFACE,
        border=ft.Border.all(1, kit.BORDER),
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        shadow=ft.BoxShadow(
            blur_radius=44,
            spread_radius=-12,
            color=ft.Colors.with_opacity(
                0.22 if theme.is_dark else 0.14, ft.Colors.BLACK
            ),
            offset=ft.Offset(0, 20),
        ),
        content=ft.Column(
            spacing=0,
            controls=[
                ft.Container(
                    height=34,
                    padding=ft.Padding.symmetric(horizontal=12),
                    bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
                    border=ft.Border(bottom=ft.BorderSide(1, kit.BORDER)),
                    content=ft.Row(
                        spacing=6,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            *[
                                ft.Container(
                                    width=9,
                                    height=9,
                                    border_radius=5,
                                    bgcolor=kit.BORDER,
                                )
                                for _ in range(3)
                            ],
                            ft.Container(width=6),
                            ft.Text("cs-ui · dashboard", size=10.5, color=kit.MUTED),
                        ],
                    ),
                ),
                ft.Row(
                    expand=True,
                    spacing=0,
                    vertical_alignment=ft.CrossAxisAlignment.STRETCH,
                    controls=[
                        rail,
                        ft.Container(
                            expand=True,
                            padding=ft.Padding.only(
                                left=14, right=14, top=12, bottom=14
                            ),
                            content=body,
                        ),
                    ],
                ),
            ],
        ),
    )


@ft.component
def _hero() -> ft.Control:
    tr = use_t()
    page = ft.context.page
    theme = use_theme()

    left = ft.Column(
        spacing=18,
        controls=[
            ft.Container(
                padding=ft.Padding.symmetric(horizontal=10, vertical=3),
                border_radius=999,
                bgcolor=ft.Colors.PRIMARY_CONTAINER,
                content=ft.Row(
                    spacing=6,
                    tight=True,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(
                            width=6,
                            height=6,
                            border_radius=3,
                            bgcolor=ft.Colors.PRIMARY,
                        ),
                        ft.Text(
                            tr("home.eyebrow", version=PACKAGE_VERSION),
                            size=11,
                            weight=ft.FontWeight.W_600,
                            color=ft.Colors.ON_PRIMARY_CONTAINER,
                        ),
                    ],
                ),
            ),
            ft.Text(
                tr("home.title"),
                size=46,
                weight=ft.FontWeight.W_800,
                style=ft.TextStyle(letter_spacing=-1.4, height=1.12),
            ),
            ft.Container(
                padding=ft.Padding.only(right=18),
                content=ft.Text(
                    tr("home.lead"),
                    size=15.5,
                    color=kit.MUTED,
                    style=ft.TextStyle(height=1.8),
                ),
            ),
            ft.Row(
                spacing=10,
                wrap=True,
                run_spacing=10,
                controls=[
                    Button(
                        tr("home.cta.start"),
                        is_primary=True,
                        icon=ft.Icons.ROCKET_LAUNCH,
                        on_click=lambda _e: page.navigate("/docs/quickstart"),
                    ),
                    Button(
                        tr("home.cta.components"),
                        icon=ft.Icons.VIEW_QUILT,
                        on_click=lambda _e: page.navigate("/components"),
                    ),
                ],
            ),
            ft.Row(spacing=8, wrap=True, run_spacing=8, controls=_chip_row()),
        ],
    )

    return ft.Container(
        padding=ft.Padding.only(top=52, bottom=44),
        gradient=ft.RadialGradient(
            center=ft.Alignment(-0.75, -1.05),
            radius=1.4,
            colors=[
                ft.Colors.with_opacity(
                    0.16 if theme.is_dark else 0.12, ft.Colors.PRIMARY
                ),
                ft.Colors.with_opacity(0.0, ft.Colors.PRIMARY),
            ],
        ),
        content=_centered(
            ft.ResponsiveRow(
                columns=12,
                spacing=36,
                run_spacing=32,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(col={"xs": 12, "lg": 5}, content=left),
                    ft.Container(col={"xs": 12, "lg": 7}, content=_window()),
                ],
            )
        ),
    )


# ---------------------------------------------------------------------------
# 数字与特性
# ---------------------------------------------------------------------------


@ft.component
def _stats() -> ft.Control:
    tr = use_t()
    items = (
        (str(COMPONENT_TOTAL), tr("home.stats.components")),
        (str(len(CATEGORIES)), tr("home.stats.categories")),
        ("3", tr("home.stats.languages")),
        ("100%", tr("home.stats.typed")),
    )
    return _centered(
        ft.Row(
            spacing=28,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row(
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text(value, size=24, weight=ft.FontWeight.W_800),
                        ft.Text(label, size=12, color=kit.MUTED),
                    ],
                )
                for value, label in items
            ],
        )
    )


@ft.component
def _counter_demo() -> ft.Control:
    tr = use_t()
    count, set_count = ft.use_state(0)
    return ft.Column(
        spacing=12,
        controls=[
            ft.Row(
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.END,
                controls=[
                    ft.Text(f"{count}", size=34, weight=ft.FontWeight.W_800),
                    ft.Text(tr("home.feature.reactive.unit"), size=12, color=kit.MUTED),
                ],
            ),
            ft.Row(
                spacing=8,
                controls=[
                    Button(
                        "+1",
                        is_primary=True,
                        on_click=lambda _e: set_count(count + 1),
                    ),
                    Button(
                        tr("home.feature.reactive.reset"),
                        plain=True,
                        on_click=lambda _e: set_count(0),
                    ),
                ],
            ),
        ],
    )


@ft.component
def _palette_demo() -> ft.Control:
    theme = use_theme()
    tr = use_t()
    seeds = ("#1F6FEB", "#4F46E5", "#7C3AED", "#0D9488", "#16A34A", "#EA580C")
    return ft.Column(
        spacing=12,
        controls=[
            ft.Row(
                spacing=7,
                wrap=True,
                controls=[
                    ft.Container(
                        width=26,
                        height=26,
                        border_radius=8,
                        bgcolor=seed,
                        border=ft.Border.all(
                            2,
                            ft.Colors.ON_SURFACE
                            if theme.primary.lower() == seed.lower()
                            else ft.Colors.TRANSPARENT,
                        ),
                        on_click=lambda _e, value=seed: theme.set_primary(value),
                    )
                    for seed in seeds
                ],
            ),
            ft.Row(
                spacing=8,
                controls=[
                    Button(tr("home.feature.themed.action"), is_primary=True),
                    Button(tr("home.feature.themed.secondary"), plain=True),
                ],
            ),
        ],
    )


@ft.component
def _feature_large(*, slug: str, body: ft.Control) -> ft.Control:
    tr = use_t()
    return ft.Container(
        col={"xs": 12, "md": 6},
        content=ft.Container(
            padding=22,
            border_radius=kit.RADIUS_CARD,
            bgcolor=kit.SURFACE,
            border=ft.Border.all(1, kit.BORDER),
            content=ft.Column(
                spacing=14,
                controls=[
                    ft.Text(
                        tr(f"home.feature.{slug}.title"),
                        size=16,
                        weight=ft.FontWeight.W_700,
                    ),
                    ft.Text(
                        tr(f"home.feature.{slug}.desc"),
                        size=13,
                        color=kit.MUTED,
                        style=ft.TextStyle(height=1.7),
                    ),
                    ft.Container(padding=ft.Padding.only(top=4), content=body),
                ],
            ),
        ),
    )


@ft.component
def _feature_small(*, slug: str, icon: ft.IconData, tone: str) -> ft.Control:
    tr = use_t()
    return ft.Container(
        col={"xs": 12, "sm": 6, "lg": 3},
        content=ft.Container(
            padding=18,
            border_radius=kit.RADIUS_CARD,
            bgcolor=kit.SURFACE,
            border=ft.Border.all(1, kit.BORDER),
            content=ft.Column(
                spacing=9,
                controls=[
                    kit.icon_tile(icon, tone=tone, size=32, icon_size=16),
                    ft.Text(
                        tr(f"home.feature.{slug}.title"),
                        size=13.5,
                        weight=ft.FontWeight.W_700,
                    ),
                    ft.Text(
                        tr(f"home.feature.{slug}.desc"),
                        size=12,
                        color=kit.MUTED,
                        style=ft.TextStyle(height=1.65),
                    ),
                ],
            ),
        ),
    )


@ft.component
def _features() -> ft.Control:
    tr = use_t()
    return _centered(
        ft.Column(
            spacing=16,
            controls=[
                ft.Column(
                    spacing=6,
                    controls=[
                        ft.Text(
                            tr("home.feature.title"),
                            size=26,
                            weight=ft.FontWeight.W_800,
                            style=ft.TextStyle(letter_spacing=-0.6),
                        ),
                        ft.Text(
                            tr("home.feature.subtitle"), size=13.5, color=kit.MUTED
                        ),
                    ],
                ),
                ft.ResponsiveRow(
                    columns=12,
                    spacing=14,
                    run_spacing=14,
                    controls=[
                        _feature_large(slug="reactive", body=_counter_demo()),
                        _feature_large(slug="themed", body=_palette_demo()),
                        _feature_small(slug="i18n", icon=ft.Icons.TRANSLATE, tone="info"),
                        _feature_small(
                            slug="typed", icon=ft.Icons.DATA_OBJECT, tone="success"
                        ),
                        _feature_small(
                            slug="modular",
                            icon=ft.Icons.EXTENSION_OUTLINED,
                            tone="warning",
                        ),
                        _feature_small(
                            slug="desktop",
                            icon=ft.Icons.DESKTOP_WINDOWS_OUTLINED,
                            tone="primary",
                        ),
                    ],
                ),
            ],
        )
    )


# ---------------------------------------------------------------------------
# 组件预览墙
# ---------------------------------------------------------------------------


@ft.component
def _tile(*, slug: str, preview: ft.Control, route: str) -> ft.Control:
    tr = use_t()
    page = ft.context.page
    return ft.Container(
        col={"xs": 12, "sm": 6, "lg": 4},
        content=kit.hover_card(
            on_click=lambda _e: page.navigate(route),
            padding=0,
            content=ft.Column(
                spacing=0,
                controls=[
                    ft.Container(
                        height=104,
                        padding=ft.Padding.symmetric(horizontal=16),
                        alignment=ft.Alignment.CENTER,
                        content=preview,
                    ),
                    kit.hairline(),
                    ft.Container(
                        padding=ft.Padding.symmetric(horizontal=14, vertical=9),
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(
                                    tr(f"home.tile.{slug}"),
                                    size=12,
                                    weight=ft.FontWeight.W_600,
                                ),
                                ft.Icon(
                                    ft.Icons.ARROW_OUTWARD, size=13, color=kit.MUTED
                                ),
                            ],
                        ),
                    ),
                ],
            ),
        ),
    )


@ft.component
def _tile_buttons() -> ft.Control:
    return ft.Row(
        spacing=7,
        wrap=True,
        alignment=ft.MainAxisAlignment.CENTER,
        controls=[
            Button("Primary", is_primary=True),
            Button("Plain", plain=True),
            Button("Icon", icon=ft.Icons.ADD),
        ],
    )


@ft.component
def _tile_inputs() -> ft.Control:
    return ft.Row(
        spacing=10,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            # 卡片窄，label 交给卡名，输入框自己占 150 就够。
            ft.Container(width=150, content=Input(value="Shawn", width=150).ui()),
            kit.use_stable(lambda: Switch(value=True)).ui(),
        ],
    )


@ft.component
def _tile_choices() -> ft.Control:
    tr = use_t()
    return ft.Column(
        spacing=6,
        controls=[
            kit.use_stable(
                lambda: Checkbox(label=tr("demo.field.notify"), value=True)
            ).ui(),
            Rating(value=4),
        ],
    )


@ft.component
def _tile_chips() -> ft.Control:
    tr = use_t()
    return kit.use_stable(lambda: Chip(options=tr.list("demo.tags")[:3])).ui()


@ft.component
def _tile_progress() -> ft.Control:
    return ft.Column(
        spacing=10,
        width=190,
        controls=[
            ProgressBar(progress=0.68, height=8, border_radius=4),
            ProgressBar(
                progress=0.42,
                color=ft.Colors.TERTIARY,
                height=8,
                border_radius=4,
            ),
        ],
    )


@ft.component
def _tile_paging() -> ft.Control:
    tr = use_t()
    return ft.Row(
        spacing=8,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                padding=ft.Padding.symmetric(horizontal=9, vertical=3),
                border_radius=7,
                bgcolor=ft.Colors.PRIMARY_CONTAINER,
                content=ft.Text(
                    tr("home.tile.page", n=1),
                    size=11,
                    color=ft.Colors.ON_PRIMARY_CONTAINER,
                    weight=ft.FontWeight.W_600,
                ),
            ),
            *[
                ft.Text(str(n), size=11.5, color=kit.MUTED)
                for n in (2, 3, 4, "…", 12)
            ],
        ],
    )


@ft.component
def _showcase() -> ft.Control:
    tr = use_t()
    return _centered(
        ft.Column(
            spacing=16,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.END,
                    wrap=True,
                    run_spacing=8,
                    controls=[
                        ft.Column(
                            spacing=6,
                            controls=[
                                ft.Text(
                                    tr("home.showcase.title"),
                                    size=26,
                                    weight=ft.FontWeight.W_800,
                                    style=ft.TextStyle(letter_spacing=-0.6),
                                ),
                                ft.Text(
                                    tr("home.showcase.subtitle"),
                                    size=13.5,
                                    color=kit.MUTED,
                                ),
                            ],
                        ),
                        Button(
                            tr("home.showcase.all"),
                            plain=True,
                            icon=ft.Icons.ARROW_FORWARD,
                            on_click=lambda _e: ft.context.page.navigate("/components"),
                        ),
                    ],
                ),
                ft.ResponsiveRow(
                    columns=12,
                    spacing=14,
                    run_spacing=14,
                    controls=[
                        _tile(
                            slug="buttons",
                            preview=_tile_buttons(),
                            route="/components/general",
                        ),
                        _tile(
                            slug="inputs",
                            preview=_tile_inputs(),
                            route="/components/form",
                        ),
                        _tile(
                            slug="choices",
                            preview=_tile_choices(),
                            route="/components/form",
                        ),
                        _tile(
                            slug="chips",
                            preview=_tile_chips(),
                            route="/components/general",
                        ),
                        _tile(
                            slug="progress",
                            preview=_tile_progress(),
                            route="/components/feedback",
                        ),
                        _tile(
                            slug="paging",
                            preview=_tile_paging(),
                            route="/components/navigation",
                        ),
                    ],
                ),
            ],
        )
    )


# ---------------------------------------------------------------------------
# 代码 + 试玩 + 收尾
# ---------------------------------------------------------------------------

_CODE = '''@ft.component
def Orders() -> ft.Control:
    query, set_query = ft.use_state("")
    rows = ft.use_memo(lambda: search(query), [query])

    def on_change(e):
        set_query(e.control.value)

    return Column(
        spacing=12,
        controls=[
            Input(label="Search", on_change=on_change).ui(),
            Table(data_table=to_table(rows), rows_per_page=10),
        ],
    )'''


@ft.component
def _code_section() -> ft.Control:
    tr = use_t()
    return _centered(
        ft.ResponsiveRow(
            columns=12,
            spacing=36,
            run_spacing=24,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    col={"xs": 12, "lg": 5},
                    content=ft.Column(
                        spacing=12,
                        controls=[
                            kit.eyebrow(tr("home.code.eyebrow")),
                            ft.Text(
                                tr("home.code.title"),
                                size=26,
                                weight=ft.FontWeight.W_800,
                                style=ft.TextStyle(letter_spacing=-0.6),
                            ),
                            ft.Text(
                                tr("home.code.desc"),
                                size=13.5,
                                color=kit.MUTED,
                                style=ft.TextStyle(height=1.8),
                            ),
                            kit.bullets(
                                [tr("home.code.point1"), tr("home.code.point2")]
                            ),
                        ],
                    ),
                ),
                ft.Container(
                    col={"xs": 12, "lg": 7},
                    content=kit.code_block(_CODE, filename="orders.py"),
                ),
            ],
        )
    )


@ft.component
def _playground() -> ft.Control:
    tr = use_t()
    page = ft.context.page

    name = kit.use_stable(lambda: Input(value="Shawn", width=190))
    notify = kit.use_stable(
        lambda: Checkbox(label=tr("home.play.checkbox"), value=True)
    )
    compact = kit.use_stable(lambda: Switch(label=tr("home.play.switch"), value=True))

    return _centered(
        ft.Container(
            padding=ft.Padding.symmetric(horizontal=26, vertical=24),
            border_radius=20,
            bgcolor=kit.SURFACE,
            border=ft.Border.all(1, kit.BORDER),
            content=ft.Column(
                spacing=16,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                        controls=[
                            ft.Column(
                                spacing=5,
                                expand=True,
                                controls=[
                                    ft.Text(
                                        tr("home.play.title"),
                                        size=18,
                                        weight=ft.FontWeight.W_700,
                                    ),
                                    ft.Text(
                                        tr("home.play.desc"),
                                        size=12.5,
                                        color=kit.MUTED,
                                    ),
                                ],
                            ),
                            kit.badge(
                                tr("home.play.badge"), tone="success", icon=ft.Icons.BOLT
                            ),
                        ],
                    ),
                    kit.hairline(),
                    ft.Row(
                        spacing=22,
                        vertical_alignment=ft.CrossAxisAlignment.END,
                        controls=[
                            # Input.ui() 自带 expand，用固定宽容器收住，
                            # 否则它会把同一行的其它控件一路推到右边。
                            ft.Column(
                                spacing=6,
                                controls=[
                                    ft.Text(
                                        tr("demo.field.name"),
                                        size=11.5,
                                        color=kit.MUTED,
                                    ),
                                    name.ui(),
                                ],
                            ),
                            ft.Column(spacing=10, controls=[notify.ui(), compact.ui()]),
                            Button(
                                tr("home.play.toast"),
                                is_primary=True,
                                icon=ft.Icons.NOTIFICATIONS_ACTIVE_OUTLINED,
                                on_click=lambda _e: toast_success(
                                    tr("home.play.toast_text"), page=page
                                ),
                            ),
                        ],
                    ),
                ],
            ),
        )
    )


@ft.component
def _cta() -> ft.Control:
    tr = use_t()
    page = ft.context.page
    return _centered(
        ft.Container(
            padding=ft.Padding.symmetric(horizontal=28, vertical=26),
            border_radius=20,
            bgcolor=ft.Colors.PRIMARY_CONTAINER,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=24,
                controls=[
                    ft.Column(
                        spacing=5,
                        expand=True,
                        controls=[
                            ft.Text(
                                tr("home.cta.title"),
                                size=21,
                                weight=ft.FontWeight.W_800,
                                color=ft.Colors.ON_PRIMARY_CONTAINER,
                            ),
                            ft.Text(
                                tr("home.cta.desc"),
                                size=13,
                                color=ft.Colors.ON_PRIMARY_CONTAINER,
                            ),
                        ],
                    ),
                    ft.Row(
                        spacing=8,
                        controls=[
                            ft.FilledButton(
                                tr("home.cta.start"),
                                icon=ft.Icons.ROCKET_LAUNCH,
                                on_click=lambda _e: page.navigate("/docs/quickstart"),
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.ON_PRIMARY_CONTAINER,
                                    color=ft.Colors.PRIMARY_CONTAINER,
                                ),
                            ),
                            ft.OutlinedButton(
                                tr("home.cta.source"),
                                icon=ft.Icons.CODE,
                                on_click=lambda _e: page.launch_url(GITHUB_URL),
                                style=ft.ButtonStyle(
                                    color=ft.Colors.ON_PRIMARY_CONTAINER
                                ),
                            ),
                        ],
                    ),
                ],
            ),
        )
    )


@ft.component
def _footer_slot() -> ft.Control:
    return _centered(site_footer(), padding=40)


@ft.component
def home_page() -> ft.Control:
    return ft.Container(
        expand=True,
        bgcolor=kit.PAGE_BG,
        content=ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[
                _hero(),
                _stats(),
                ft.Container(height=56),
                _features(),
                ft.Container(height=64),
                _showcase(),
                ft.Container(height=64),
                _code_section(),
                ft.Container(height=64),
                _playground(),
                ft.Container(height=56),
                _cta(),
                ft.Container(height=40),
                _footer_slot(),
            ],
        ),
    )


__all__ = ["home_page"]
