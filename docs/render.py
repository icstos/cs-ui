"""把内容 DSL 渲染成控件；顺带从标题生成右侧目录。"""

from __future__ import annotations

from collections.abc import Sequence

import flet as ft

from docs import kit
from docs.blocks import (
    Block,
    Bullets,
    Callout,
    Code,
    CodeTabs,
    Custom,
    Demo,
    Heading,
    Prose,
    Split,
)
from ui import Translator, use_t

_MUTED = kit.MUTED


def _heading(block: Heading, text: str) -> ft.Control:
    if block.level == 2:
        return ft.Container(
            key=block.anchor,
            margin=ft.Margin.only(top=10),
            content=ft.Text(text, size=24, weight=ft.FontWeight.W_700),
        )
    return ft.Text(text, size=16, weight=ft.FontWeight.W_700)


def _code_tabs(block: CodeTabs) -> ft.Control:
    language = block.items[0].language if block.items else "python"
    return kit.code_tabs(
        tuple(
            (item.filename or item.language.upper(), item.source)
            for item in block.items
        ),
        language=language,
    )


def _split(block: Split, tr: Translator) -> ft.Control:
    """左说明、右演示。宽屏并排，窄屏（< 992）上下堆叠。

    不能写成固定 ``Row`` + ``expand`` 比例：``expand`` 只分配"剩余空间"，
    640 的窗口里左栏会缩到 250 左右，说明文字一段一行、演示面板里的表单全挤成
    两行。用 ``ResponsiveRow`` 让换行发生在 Flutter 侧，正文不用重排。
    """
    left, right = block.ratio
    total = max(1, left + right)
    left_span = max(1, round(12 * left / total))
    right_span = max(1, 12 - left_span)
    return ft.ResponsiveRow(
        columns=12,
        spacing=32,
        run_spacing=22,
        vertical_alignment=ft.CrossAxisAlignment.START,
        controls=[
            ft.Container(
                col={"xs": 12, "lg": left_span},
                content=ft.Column(
                    spacing=14,
                    controls=render_blocks(block.left, tr),
                ),
            ),
            ft.Container(
                col={"xs": 12, "lg": right_span}, content=block.right()
            ),
        ],
    )


def _render(block: Block, tr: Translator) -> ft.Control:
    match block:
        case Heading():
            return _heading(block, tr(block.key))
        case Prose():
            return ft.Text(
                tr(block.key),
                size=14,
                style=ft.TextStyle(height=1.8),
            )
        case Bullets():
            return kit.bullets([tr(key) for key in block.keys], tone=block.tone)
        case Code():
            return kit.code_block(
                block.source, filename=block.filename, language=block.language
            )
        case CodeTabs():
            return _code_tabs(block)
        case Callout():
            return kit.callout(
                block.kind,
                tr(block.body_key, **block.params),
                tr(block.title_key) if block.title_key else None,
            )
        case Demo():
            return kit.demo_frame(block)
        case Split():
            return _split(block, tr)
        case Custom():
            return block.factory()
    raise TypeError(f"未知内容块：{type(block).__name__}")


def render_blocks(blocks: Sequence[Block], tr: Translator) -> list[ft.Control]:
    """渲染一组内容块。``tr`` 由调用方的组件传下来，整段共用一次翻译。"""
    return [_render(block, tr) for block in blocks]


@ft.component
def BlocksView(blocks: Sequence[Block], *, spacing: int = 18) -> ft.Control:
    """内容块视图：语言变化时整段重绘（文本全部来自语言包）。"""
    tr = use_t()
    return ft.Column(
        spacing=spacing,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        controls=render_blocks(blocks, tr),
    )


def outline(blocks: Sequence[Block]) -> tuple[Heading, ...]:
    """抽出二级标题作为"本页目录"。三级标题不占位，避免侧栏比正文还长。

    分栏块里的标题也算 —— 它同样是页面上真实存在的锚点。
    """
    found: list[Heading] = []
    for block in blocks:
        if isinstance(block, Heading) and block.level == 2:
            found.append(block)
        elif isinstance(block, Split):
            found.extend(outline(block.left))
    return tuple(found)


__all__ = ["BlocksView", "outline", "render_blocks"]
