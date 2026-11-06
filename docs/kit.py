"""站点视觉基础件：把「漂亮」收敛成少数几个可复用控件。

页面只调用这一层（`Surface` / `CodeBlock` / `DemoFrame` / `Callout` …），
所以配色、圆角、间距只在这里定义一次 —— 想整体调风格，改这个文件即可。

配色一律走 Material 3 角色色（`SURFACE` / `ON_SURFACE_VARIANT` / `PRIMARY` …），
明暗主题自动跟随；只有代码面板刻意固定为深色，见 :func:`CodeBlock`。
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Sequence
from typing import Any, cast

import flet as ft
import flet_code_editor as fce

from docs.blocks import CalloutKind, Demo, Tone
from ui import Code, semantic, semantic_text, use_i18n, use_t
from ui.core.theme import use_theme

# ---------------------------------------------------------------------------
# 令牌
# ---------------------------------------------------------------------------

MUTED: ft.ColorValue = ft.Colors.ON_SURFACE_VARIANT
BORDER: ft.ColorValue = ft.Colors.OUTLINE_VARIANT
SURFACE: ft.ColorValue = ft.Colors.SURFACE
PAGE_BG: ft.ColorValue = ft.Colors.SURFACE_CONTAINER_LOWEST
RAISED: ft.ColorValue = ft.Colors.SURFACE_CONTAINER_LOW

RADIUS_CARD = 16
RADIUS_BLOCK = 12

#: 代码面板固定深色（浅色界面里形成"纸与墨"的对比，深色界面里高于背景一档）。
_CODE_BG = "#0E1117"
_CODE_HEAD_BG = "#151A22"
_CODE_BORDER = "#232A35"

_TONE_FALLBACK: dict[str, str] = {
    "primary": "info",
    "success": "success",
    "warning": "warning",
    "danger": "danger",
    "info": "info",
    "neutral": "neutral",
}


def tone_color(tone: Tone) -> ft.ColorValue:
    """把语气映射成颜色：``primary`` 用主题主色，其余落语义色。"""
    if tone == "primary":
        return ft.Colors.PRIMARY
    return semantic(_TONE_FALLBACK.get(tone, "info"))


def tone_text(tone: Tone) -> ft.ColorValue:
    if tone == "primary":
        return ft.Colors.PRIMARY
    return semantic_text(_TONE_FALLBACK.get(tone, "info"))


def tint(tone: Tone, opacity: float = 0.10) -> ft.ColorValue:
    """同色的低透明度底 —— 徽标、图标底片都用它。"""
    return ft.Colors.with_opacity(opacity, tone_color(tone))


def hairline(*, color: ft.ColorValue = BORDER) -> ft.Control:
    return ft.Container(height=1, bgcolor=color)


# ---------------------------------------------------------------------------
# 文本
# ---------------------------------------------------------------------------


def eyebrow(text: str) -> ft.Control:
    return ft.Text(
        text.upper(),
        size=11,
        weight=ft.FontWeight.W_700,
        color=ft.Colors.PRIMARY,
        style=ft.TextStyle(letter_spacing=1.3),
    )


def lead(text: str, *, size: float = 15.5) -> ft.Control:
    """导语：比正文大一号、行高更松。"""
    return ft.Text(
        text,
        size=size,
        color=MUTED,
        style=ft.TextStyle(height=1.75),
    )


def body(text: str, *, size: float = 14) -> ft.Control:
    return ft.Text(text, size=size, style=ft.TextStyle(height=1.75))


def bullets(items: Sequence[str], *, tone: Tone = "primary") -> ft.Control:
    dot = tone_color(tone)
    return ft.Column(
        spacing=9,
        controls=[
            ft.Row(
                spacing=11,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.Container(
                        width=6,
                        height=6,
                        border_radius=3,
                        bgcolor=dot,
                        margin=ft.Margin.only(top=8),
                    ),
                    ft.Text(
                        item,
                        size=13.5,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                        style=ft.TextStyle(height=1.7),
                        expand=True,
                    ),
                ],
            )
            for item in items
        ],
    )


# ---------------------------------------------------------------------------
# 容器
# ---------------------------------------------------------------------------


def surface(
    content: ft.Control,
    *,
    padding: ft.PaddingValue | None = None,
    radius: int = RADIUS_CARD,
    bgcolor: ft.ColorValue = SURFACE,
    border: bool = True,
) -> ft.Container:
    """标准卡片面：一档底色 + 一条极窄描边（不用阴影，桌面端更干净）。"""
    return ft.Container(
        padding=padding or ft.Padding.all(20),
        border_radius=radius,
        bgcolor=bgcolor,
        border=ft.Border.all(1, BORDER) if border else None,
        content=content,
    )


@ft.component
def hover_card(
    content: ft.Control,
    *,
    on_click: Callable[[ft.Event[ft.Container]], None] | None = None,
    padding: int = 18,
    radius: int = RADIUS_CARD,
) -> ft.Control:
    """可点卡片：悬停时描边转为主色、底色抬一档。

    桌面端的"可点"靠悬停暗示最自然 —— 光标还没落下就已经知道能点。
    """
    hovered, set_hovered = ft.use_state(False)

    def on_hover(event: ft.Event[ft.Container]) -> None:
        set_hovered(str(event.data).lower() == "true")

    return ft.Container(
        padding=ft.Padding.all(padding),
        border_radius=radius,
        bgcolor=RAISED if hovered else SURFACE,
        border=ft.Border.all(
            1, ft.Colors.with_opacity(0.55, ft.Colors.PRIMARY) if hovered else BORDER
        ),
        animate=ft.Animation(140, ft.AnimationCurve.EASE_OUT),
        on_hover=on_hover,
        on_click=on_click,
        ink=on_click is not None,
        content=content,
    )


def icon_tile(
    icon: ft.IconData,
    *,
    tone: Tone = "primary",
    size: int = 36,
    icon_size: int = 18,
) -> ft.Control:
    return ft.Container(
        width=size,
        height=size,
        border_radius=10,
        bgcolor=tint(tone, 0.12),
        alignment=ft.Alignment.CENTER,
        content=ft.Icon(icon, size=icon_size, color=tone_text(tone)),
    )


def badge(
    text: str,
    *,
    tone: Tone = "primary",
    icon: ft.IconData | None = None,
) -> ft.Control:
    controls: list[ft.Control] = []
    if icon is not None:
        controls.append(ft.Icon(icon, size=12, color=tone_text(tone)))
    controls.append(
        ft.Text(
            text,
            size=11,
            weight=ft.FontWeight.W_600,
            color=tone_text(tone),
        )
    )
    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=9, vertical=3),
        border_radius=999,
        bgcolor=tint(tone, 0.12),
        content=ft.Row(
            spacing=5,
            tight=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=controls,
        ),
    )


def kbd(text: str) -> ft.Control:
    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=5, vertical=1),
        border_radius=5,
        bgcolor=RAISED,
        border=ft.Border.all(1, BORDER),
        content=ft.Text(text, size=10, color=MUTED, weight=ft.FontWeight.W_600),
    )


# ---------------------------------------------------------------------------
# 代码
# ---------------------------------------------------------------------------

_LANGUAGES: dict[str, fce.CodeLanguage] = {
    "python": fce.CodeLanguage.PYTHON,
    "bash": fce.CodeLanguage.BASH,
    "shell": fce.CodeLanguage.SHELL,
    "json": fce.CodeLanguage.JSON,
    "yaml": fce.CodeLanguage.YAML,
    "toml": fce.CodeLanguage.PLAINTEXT,
    "text": fce.CodeLanguage.PLAINTEXT,
}

_LINE_HEIGHT = 24
_CODE_PAD = 10
_CODE_SIZE = 12.5
_CODE_SIZE_MIN = 10.4


def _code_size(source: str) -> float:
    """按最长行挑字号：宽格子用大字号，窄格子自动缩，别让代码被右边切掉。

    ``CodeEditor`` 不会横向滚动也不会换行，所以只能靠字号买宽度。阈值按
    "分栏里那半边"（约 520px）与整页正文（约 700px）两种常见宽度取。
    """
    longest = max((len(line) for line in source.splitlines()), default=0)
    if longest <= 64:
        return _CODE_SIZE
    if longest <= 78:
        return 11.6
    if longest <= 96:
        return 11.0
    return _CODE_SIZE_MIN


def _fitted_height(source: str, size: float = _CODE_SIZE) -> int:
    """按整行取整，避免最后一行被截成半行。"""
    lines = source.count("\n") + 1
    line_height = round(size * 1.85)
    return min(520, lines * line_height + _CODE_PAD)


@ft.component
def code_block(
    source: str,
    *,
    filename: str | None = None,
    language: str = "python",
    height: int | None = None,
    font_size: float | None = None,
) -> ft.Control:
    """只读代码块：深色面板 + 文件名 + 一键复制。

    代码面板刻意**不跟随明暗主题**：浅色界面里它是一块"墨"，深色界面里它比
    背景高一档 —— 两种模式下都能一眼看出"这段是代码，不是正文"。
    """
    tr = use_t()
    copied, set_copied = ft.use_state(False)
    size = font_size or _code_size(source)
    resolved = height or _fitted_height(source, size)
    code_language = _LANGUAGES.get(language, fce.CodeLanguage.PYTHON)

    async def copy(event: ft.Event[ft.IconButton]) -> None:
        """复制是客户端动作（action），这里只负责把图标换成对勾再换回来。"""
        set_copied(True)
        await asyncio.sleep(1.4)
        set_copied(False)

    return ft.Container(
        border_radius=RADIUS_BLOCK,
        bgcolor=_CODE_BG,
        border=ft.Border.all(1, _CODE_BORDER),
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        content=ft.Column(
            spacing=0,
            controls=[
                ft.Container(
                    padding=ft.Padding.only(left=14, right=6, top=4, bottom=4),
                    bgcolor=_CODE_HEAD_BG,
                    border=ft.Border(bottom=ft.BorderSide(1, _CODE_BORDER)),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Row(
                                spacing=7,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Container(
                                        width=6,
                                        height=6,
                                        border_radius=3,
                                        bgcolor=ft.Colors.with_opacity(
                                            0.45, ft.Colors.WHITE
                                        ),
                                    ),
                                    ft.Text(
                                        filename or language.upper(),
                                        size=11,
                                        color=ft.Colors.with_opacity(
                                            0.62, ft.Colors.WHITE
                                        ),
                                        weight=ft.FontWeight.W_500,
                                    ),
                                ],
                            ),
                            ft.IconButton(
                                icon=ft.Icons.CHECK_ROUNDED
                                if copied
                                else ft.Icons.CONTENT_COPY,
                                icon_size=14,
                                icon_color=(
                                    ft.Colors.GREEN_ACCENT_200
                                    if copied
                                    else ft.Colors.with_opacity(
                                        0.55, ft.Colors.WHITE
                                    )
                                ),
                                tooltip=tr("site.copied")
                                if copied
                                else tr("site.copy"),
                                padding=6,
                                action=ft.CopyToClipboard(source),
                                on_click=copy,
                            ),
                        ],
                    ),
                ),
                Code(
                    value=source,
                    language=code_language,
                    code_theme=fce.CodeTheme.ATOM_ONE_DARK,
                    height=resolved,
                    text_style=ft.TextStyle(size=size, height=1.55),
                    read_only=True,
                ),
            ],
        ),
    )


@ft.component
def code_tabs(
    items: Sequence[tuple[str, str]],
    *,
    language: str = "python",
) -> ft.Control:
    """多方案代码：``[("pip", "..."), ("uv", "...")]``，标签名即文件名。"""
    active, set_active = ft.use_state(0)
    index = min(active, len(items) - 1)
    name, source = items[index]

    def pick(position: int) -> Callable[[ft.Event[ft.Container]], None]:
        return lambda _e: set_active(position)

    return ft.Column(
        spacing=8,
        controls=[
            ft.Row(
                spacing=4,
                controls=[
                    ft.Container(
                        padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                        border_radius=7,
                        bgcolor=RAISED if position == index else None,
                        border=ft.Border.all(
                            1,
                            BORDER if position == index else ft.Colors.TRANSPARENT,
                        ),
                        on_click=pick(position),
                        ink=True,
                        content=ft.Text(
                            label,
                            size=11.5,
                            color=(
                                ft.Colors.ON_SURFACE
                                if position == index
                                else MUTED
                            ),
                            weight=(
                                ft.FontWeight.W_600
                                if position == index
                                else ft.FontWeight.W_400
                            ),
                        ),
                    )
                    for position, (label, _source) in enumerate(items)
                ],
            ),
            code_block(source, filename=name, language=language),
        ],
    )


# ---------------------------------------------------------------------------
# 提示
# ---------------------------------------------------------------------------

_CALLOUT_ICONS: dict[CalloutKind, tuple[ft.IconData, Tone]] = {
    "success": (ft.Icons.CHECK_CIRCLE_OUTLINE, "success"),
    "warning": (ft.Icons.WARNING_AMBER_ROUNDED, "warning"),
    "danger": (ft.Icons.ERROR_OUTLINE_ROUNDED, "danger"),
    "tip": (ft.Icons.LIGHTBULB_OUTLINE_ROUNDED, "primary"),
    "info": (ft.Icons.INFO_OUTLINE_ROUNDED, "info"),
}


@ft.component
def callout(kind: CalloutKind, body_text: str, title: str | None = None) -> ft.Control:
    icon, tone = _CALLOUT_ICONS.get(kind, _CALLOUT_ICONS["info"])
    color = tone_text(tone)
    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=16, vertical=13),
        border_radius=RADIUS_BLOCK,
        bgcolor=tint(tone, 0.07),
        border=ft.Border(
            left=ft.BorderSide(3, tone_color(tone)),
            top=ft.BorderSide(1, tint(tone, 0.14)),
            right=ft.BorderSide(1, tint(tone, 0.14)),
            bottom=ft.BorderSide(1, tint(tone, 0.14)),
        ),
        content=ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                ft.Icon(icon, size=17, color=color),
                ft.Column(
                    expand=True,
                    spacing=3,
                    controls=[
                        *(
                            [
                                ft.Text(
                                    title,
                                    size=13,
                                    weight=ft.FontWeight.W_700,
                                    color=color,
                                )
                            ]
                            if title
                            else []
                        ),
                        ft.Text(
                            body_text,
                            size=13,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                            style=ft.TextStyle(height=1.65),
                        ),
                    ],
                ),
            ],
        ),
    )


# ---------------------------------------------------------------------------
# 实时演示
# ---------------------------------------------------------------------------


def _toggle_icon(icon: ft.IconData, label: str, *, active: bool, on_click: Any) -> ft.Control:
    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=9, vertical=4),
        border_radius=7,
        bgcolor=RAISED if active else None,
        border=ft.Border.all(1, BORDER if active else ft.Colors.TRANSPARENT),
        on_click=on_click,
        ink=True,
        tooltip=label,
        content=ft.Row(
            spacing=5,
            tight=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(
                    icon,
                    size=14,
                    color=ft.Colors.ON_SURFACE if active else MUTED,
                ),
                ft.Text(
                    label,
                    size=11.5,
                    color=ft.Colors.ON_SURFACE if active else MUTED,
                    weight=ft.FontWeight.W_600 if active else ft.FontWeight.W_400,
                ),
            ],
        ),
    )


@ft.component
def demo_frame(item: Demo) -> ft.Control:
    """演示卡：标题 + 实时预览 +（可选）源码。

    预览与源码都挂在同一张卡里，切换只是多渲染一块 —— 预览不会因为切走而
    重建，表单里填过的内容还在。
    """
    tr = use_t()
    show_code, set_show_code = ft.use_state(False)

    header: list[ft.Control] = []
    if item.title_key is not None or item.hint_key is not None:
        header.append(
            ft.Column(
                expand=True,
                spacing=3,
                controls=[
                    *(
                        [
                            ft.Text(
                                tr(item.title_key),
                                size=14,
                                weight=ft.FontWeight.W_700,
                            )
                        ]
                        if item.title_key
                        else []
                    ),
                    *(
                        [
                            ft.Text(
                                tr(item.hint_key),
                                size=12.5,
                                color=MUTED,
                                style=ft.TextStyle(height=1.6),
                            )
                        ]
                        if item.hint_key
                        else []
                    ),
                ],
            )
        )

    if item.code is not None:
        header.append(
            ft.Row(
                spacing=2,
                controls=[
                    _toggle_icon(
                        ft.Icons.VISIBILITY_OUTLINED,
                        tr("site.demo.preview"),
                        active=not show_code,
                        on_click=lambda _e: set_show_code(False),
                    ),
                    _toggle_icon(
                        ft.Icons.CODE,
                        tr("site.demo.code"),
                        active=show_code,
                        on_click=lambda _e: set_show_code(True),
                    ),
                ],
            )
        )

    stage = ft.Container(
        padding=ft.Padding.all(20) if item.padded else None,
        content=item.factory(),
    )

    return ft.Container(
        border_radius=RADIUS_CARD,
        bgcolor=SURFACE,
        border=ft.Border.all(1, BORDER),
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        content=ft.Column(
            spacing=0,
            controls=[
                *(
                    [
                        ft.Container(
                            padding=ft.Padding.only(
                                left=18, right=10, top=10, bottom=10
                            ),
                            content=ft.Row(
                                spacing=10,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=header,
                            ),
                        ),
                        hairline(),
                    ]
                    if header
                    else []
                ),
                stage,
                *(
                    [
                        hairline(),
                        ft.Container(
                            padding=ft.Padding.all(12),
                            content=code_block(item.code),
                        ),
                    ]
                    if show_code and item.code is not None
                    else []
                ),
            ],
        ),
    )


# ---------------------------------------------------------------------------
# 语言切换时保持实例
# ---------------------------------------------------------------------------

#: 语言切换后需要从旧实例搬移的用户输入字段。
_CARRIED_FIELDS = ("value", "start_value", "end_value", "selected", "target_keys")


def use_stable[T](factory: Callable[[], T]) -> T:
    """返回跨渲染稳定的实例，并在语言变化时用新文案重建。

    ``ui`` 的交互式组件把标签、候选列表作为构造参数，实例被固定后切语言会停在
    旧文案。这里在语言变化时重建，再以**绕过 observable 通知**的方式搬移用户
    已填写的值，避免渲染期回环。
    """
    locale = use_i18n().locale
    box = cast(ft.Ref[T | None], ft.use_ref(None))
    stamp = cast(ft.Ref[str | None], ft.use_ref(None))

    if box.current is None or stamp.current != locale:
        previous = box.current
        instance = factory()
        box.current = instance
        stamp.current = locale
        if previous is not None:
            for field in _CARRIED_FIELDS:
                if hasattr(previous, field) and hasattr(instance, field):
                    object.__setattr__(instance, field, getattr(previous, field))
    return cast(T, box.current)


def locale_label(locale: str) -> str:
    """``zh_CN`` → ``ZH``，给代码示例里的注释用。"""
    return locale.split("_")[0].upper()


@ft.component
def theme_sample() -> ft.Control:
    """一小块"当前主题长什么样"的色板，给主题章节当活道具。"""
    theme = use_theme()
    roles: tuple[tuple[str, ft.ColorValue, ft.ColorValue], ...] = (
        ("primary", ft.Colors.PRIMARY, ft.Colors.ON_PRIMARY),
        ("secondary", ft.Colors.SECONDARY_CONTAINER, ft.Colors.ON_SECONDARY_CONTAINER),
        ("tertiary", ft.Colors.TERTIARY_CONTAINER, ft.Colors.ON_TERTIARY_CONTAINER),
        ("surface", ft.Colors.SURFACE_CONTAINER_HIGH, ft.Colors.ON_SURFACE),
    )
    return ft.Column(
        spacing=8,
        controls=[
            ft.Row(
                spacing=8,
                controls=[
                    ft.Container(
                        width=64,
                        height=52,
                        border_radius=10,
                        bgcolor=bg,
                        alignment=ft.Alignment.CENTER,
                        content=ft.Text(
                            name,
                            size=9.5,
                            color=fg,
                            weight=ft.FontWeight.W_600,
                        ),
                    )
                    for name, bg, fg in roles
                ],
            ),
            ft.Text(
                f"{theme.mode_name} · {theme.primary}",
                size=11,
                color=MUTED,
            ),
        ],
    )


__all__ = [
    "BORDER",
    "MUTED",
    "PAGE_BG",
    "RADIUS_BLOCK",
    "RADIUS_CARD",
    "RAISED",
    "SURFACE",
    "badge",
    "body",
    "bullets",
    "callout",
    "code_block",
    "code_tabs",
    "demo_frame",
    "eyebrow",
    "hairline",
    "hover_card",
    "icon_tile",
    "kbd",
    "lead",
    "locale_label",
    "surface",
    "theme_sample",
    "tint",
    "tone_color",
    "tone_text",
    "use_stable",
]
