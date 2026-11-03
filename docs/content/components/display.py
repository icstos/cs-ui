"""数据展示：列表项、代码编辑器、代码视图。"""

from __future__ import annotations

import flet as ft
import flet_code_editor as fce

from docs import kit
from docs.blocks import Doc, demo, h2, note, p, ul
from docs.content.components._shared import panel
from ui import CodeEditor, CodeView, Column, ListTile, Text, use_t

_EDITOR_CODE = '''def greet(name: str) -> str:
    """一个可以就地编辑的代码块。"""
    return f"Hello, {name}!"


print(greet("cs-ui"))'''

_VIEW_CODE = '''from ui import CodeView, Container, Text

CodeView(
    component=Container(Text("上面的实时组件")),
    code="Container(Text('上面的实时组件'))",
)'''

_SAMPLE = '''class LRUCache[K, V]:
    """带容量上限的最近最少使用缓存。"""

    def __init__(self, capacity: int) -> None:
        self._capacity = capacity
        self._data: dict[K, V] = {}

    def get(self, key: K) -> V | None:
        if key not in self._data:
            return None
        self._data[key] = self._data.pop(key)   # 命中后移到队尾
        return self._data[key]
'''


@ft.component
def _list_tiles() -> ft.Control:
    tr = use_t()
    people = (
        ("Shawn Chen", "shawn@cstos.com", ft.Colors.PRIMARY, "SC"),
        ("Avery Lin", "avery@example.com", ft.Colors.TERTIARY, "AL"),
        ("Riley Wu", "riley@example.com", ft.Colors.SECONDARY, "RW"),
    )
    return panel(
        *[
            ListTile(
                leading=ft.CircleAvatar(
                    content=ft.Text(initials, size=12, weight=ft.FontWeight.W_700),
                    bgcolor=ft.Colors.with_opacity(0.18, color),
                    color=color,
                    radius=18,
                ),
                title=Text(name, size=13.5, weight=ft.FontWeight.W_600),
                subtitle=Text(email, size=11.5, color=kit.MUTED),
                trailing=ft.IconButton(
                    icon=ft.Icons.MORE_HORIZ,
                    icon_size=17,
                    icon_color=kit.MUTED,
                    tooltip=tr("cat.display.tile.more"),
                ),
            )
            for name, email, color, initials in people
        ],
    )


@ft.component
def _editor() -> ft.Control:
    return ft.Container(
        border_radius=10,
        border=ft.Border.all(1, kit.BORDER),
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        content=CodeEditor(
            value=_EDITOR_CODE,
            language=fce.CodeLanguage.PYTHON,
            code_theme=fce.CodeTheme.ATOM_ONE_LIGHT,
            height=190,
            padding=10,
        ),
    )


@ft.component
def _code_view() -> ft.Control:
    tr = use_t()
    return CodeView(
        component=kit.surface(
            padding=16,
            content=Column(
                spacing=6,
                controls=[
                    Text(tr("cat.display.view.preview"), size=13),
                    Text(tr("cat.display.view.hint"), size=11.5, color=kit.MUTED),
                ],
            ),
        ),
        code=_VIEW_CODE,
    )


DISPLAY: Doc = (
    p("cat.display.intro"),
    h2("cat.display.tile.title"),
    demo(_list_tiles, hint_key="cat.display.tile.hint", padded=False),
    h2("cat.display.editor.title"),
    demo(_editor, hint_key="cat.display.editor.hint", padded=False),
    h2("cat.display.view.title"),
    demo(_code_view, hint_key="cat.display.view.hint", code=_SAMPLE),
    ul("cat.display.note1", "cat.display.note2", "cat.display.note3"),
    note("cat.display.tip", "cat.display.tip_title"),
)