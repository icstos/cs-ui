"""快速开始。"""

from __future__ import annotations

from docs.blocks import Doc, code, h2, note, p, tabs, tip, ul

_INSTALL = "pip install cs-ui"
_INSTALL_UV = "uv pip install cs-ui"
_INSTALL_SRC = """git clone https://github.com/icstos/cs-ui.git
cd cs-ui
pip install -e ."""

_FIRST_APP = """import flet as ft
from ui import Button, Card, Column, Container, Text, ThemeProvider


@ft.component
def Counter() -> ft.Control:
    count, set_count = ft.use_state(0)

    return Card(
        content=Container(
            padding=24,
            content=Column(
                spacing=14,
                controls=[
                    Text(f"Clicked {count} times", size=20, weight=ft.FontWeight.W_700),
                    Button(
                        "+1",
                        is_primary=True,
                        on_click=lambda _: set_count(count + 1),
                    ),
                ],
            ),
        )
    )


def main(page: ft.Page) -> None:
    page.padding = 0
    page.render(lambda: ThemeProvider(build=Counter))


ft.run(main)"""

_RUN = """# 桌面窗口
flet run main.py

# 浏览器预览（同一份代码）
flet run --web main.py"""

_TREE = """my_app/
├─ main.py          # 入口：page.render(App)
├─ app.py           # 根组件：Provider + Router
├─ pages/           # 一个路由一个页面组件
├─ widgets/         # 只属于本项目的组合控件
├─ i18n/            # zh_CN.json / zh_TW.json / en_US.json
└─ assets/          # 字体与图片"""

_STATE = """from ui.core.i18n import set_locale

# 切换语言不需要重启，也不需要重建路由
set_locale("zh-TW")

# 组件内部用 use_t() 取文案，它就自动订阅了语言变化
# tr = use_t()
# tr("nav.home.title")"""

QUICKSTART: Doc = (
    p("start.intro"),
    h2("start.install.title"),
    p("start.install.desc"),
    tabs(
        code(_INSTALL, "pip", "bash"),
        code(_INSTALL_UV, "uv", "bash"),
        code(_INSTALL_SRC, "source", "bash"),
    ),
    note("start.install.note", "start.install.note_title"),
    h2("start.first.title"),
    p("start.first.desc"),
    code(_FIRST_APP, "main.py"),
    tip("start.first.tip", "start.first.tip_title"),
    h2("start.run.title"),
    p("start.run.desc"),
    code(_RUN, "terminal", "bash"),
    h2("start.layout.title"),
    p("start.layout.desc"),
    code(_TREE, "project", "text"),
    h2("start.next.title"),
    p("start.next.desc"),
    ul("start.next.point1", "start.next.point2", "start.next.point3"),
    code(_STATE, "locale.py"),
)
