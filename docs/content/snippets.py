"""文档中展示的 Python / Shell 代码片段。

代码保持与框架当前 API 一致；这里集中维护，避免页面文件被长字符串淹没。
"""

from __future__ import annotations

INSTALL_PIP = "pip install cs-ui"
INSTALL_UV = "uv pip install cs-ui"
INSTALL_SOURCE = """git clone https://github.com/icstos/cs-ui.git
cd cs-ui
pip install -e ."""

QUICK_START = '''from __future__ import annotations

import flet as ft
from ui import Button, Card, Column, Container, Text, ThemeProvider


@ft.component
def App() -> ft.Control:
    return ThemeProvider(
        build=lambda: Container(
            expand=True,
            alignment=ft.Alignment.CENTER,
            content=Card(
                content=Container(
                    padding=28,
                    content=Column(
                        spacing=14,
                        controls=[
                            Text("Hello, cs-ui", size=26, weight=ft.FontWeight.BOLD),
                            Text("用 Python 构建桌面界面。", color=ft.Colors.ON_SURFACE_VARIANT),
                            Button("开始使用", is_primary=True),
                        ],
                    ),
                ),
            ),
        )
    )


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))'''

RUN_APP = "python main.py"
RUN_WATCH = "flet run main.py --watch"

PROJECT_TREE = """my_app/
├── main.py           # 入口：page.render(App)
├── views/            # 页面组件（ft.Route 声明）
├── components/       # 业务组件
├── i18n/             # 文案包（可选）
└── assets/           # 字体、图片等静态资源"""

PROVIDERS = '''from __future__ import annotations

import flet as ft
from ui import I18nProvider, Route, Router, ThemeProvider


@ft.component
def App() -> ft.Control:
    return I18nProvider(
        locale="zh-CN",
        build=lambda: ThemeProvider(
            build=lambda: Router(ROUTES, not_found=NotFoundPage, manage_views=False)
        ),
    )


def main(page: ft.Page) -> None:
    page.render(App)'''

ROUTER = '''ROUTES: list[ft.Route] = [
    ft.Route(
        component=Shell,
        children=[
            ft.Route(index=True, component=HomePage),
            ft.Route(path="settings", component=SettingsPage),
        ],
    ),
]


@ft.component
def Shell() -> ft.Control:
    outlet = ft.use_route_outlet()
    return ft.Column(controls=[TopBar(), outlet], expand=True)


ft.run(lambda page: page.render(App))'''

THEME_STATE = '''from ui import PRIMARY_SEEDS, use_theme

@ft.component
def ThemeControls() -> ft.Control:
    theme = use_theme()

    return ft.Row(
        controls=[
            ft.Button("明暗", on_click=lambda _: theme.toggle_mode()),
            ft.Button("主色", on_click=lambda _: theme.set_primary(PRIMARY_SEEDS["violet"])),
            ft.Button("跟随系统", on_click=lambda _: theme.set_mode("system")),
        ]
    )'''

TOKENS = '''from ui import RADIUS, SPACE, semantic, semantic_text, overlay

ft.Container(
    padding=SPACE["4"],              # 16
    border_radius=RADIUS["lg"],      # 8
    bgcolor=ft.Colors.SURFACE_CONTAINER,
    border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
    content=ft.Text("已保存", color=semantic_text("success")),
)'''

I18N_REGISTER = '''from ui import register_messages

register_messages("zh-CN", {
    "app": {"title": "我的应用"},
    "hello": "你好，{name}",
    "files": {"one": "{n} 个文件", "other": "{n} 个文件"},
    "cities": ["北京", "上海", "深圳"],
})

register_messages("en-US", {
    "app.title": "My App",
    "hello": "Hello, {name}",
    "files": {"one": "{n} file", "other": "{n} files"},
    "cities": ["Beijing", "Shanghai", "Shenzhen"],
})'''

I18N_USE = '''from ui import use_t

@ft.component
def Toolbar() -> ft.Control:
    tr = use_t()  # 订阅语言：切换时本组件自动重绘
    return ft.Text(tr("hello", name="Shawn"))'''

I18N_FORMAT = '''from datetime import date
from ui import format_date, format_number, calendar_title

format_number(1286)          # 1,286
format_date(date(2026, 9, 26))          # 2026-09-26 / 09/26/2026
format_date(date(2026, 9, 26), long=True)  # 2026年9月26日 / September 26, 2026
calendar_title(2026, 9)      # 2026年9月 / September 2026'''

DUAL_PARADIGM = '''# 静态控件：继承 Flet 原生控件，构造即用
button = Button("保存", is_primary=True)

# 交互式组件：observable 数据对象 + ui()
name = ft.use_ref(lambda: Input(label="姓名", value="Shawn")).current
name_control = name.ui()'''

COMPONENT_STATE = '''@ft.component
def ProfileForm() -> ft.Control:
    # 有状态组件必须用 ref 固定实例，否则父组件重渲染会丢输入
    name = ft.use_ref(lambda: Input(label="姓名", width=260)).current
    agree = ft.use_ref(lambda: Checkbox(label="我已阅读并同意")).current

    return ft.Column(
        spacing=16,
        controls=[name.ui(), agree.ui(), Button("提交", is_primary=True)],
    )'''

RUN_DOCS = "python docs/main.py"
SMOKE_DOCS = (
    "python scripts/smoke_test.py docs.main App "
    "--routes /,/docs/getting-started,/docs/architecture,/docs/theming,/docs/i18n,"
    "/components,/components/general,/components/layout,/components/navigation,"
    "/components/form,/components/feedback,/components/display,/components/charts,"
    "/components/media,/components/upload,/search,/about"
)
