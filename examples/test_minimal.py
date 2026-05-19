import flet as ft
import warnings
warnings.filterwarnings("ignore")

def home_view(page):
    return ft.View(
        route="/",
        appbar=ft.AppBar(title=ft.Text("CS UI Demo"), bgcolor="#1f6feb", color="white"),
        controls=[
            ft.Text("CS UI 组件库", size=28, weight="bold", color="#1f2937"),
            ft.Text("基于 Flet 的 Python UI 组件库，点击卡片查看各分类组件效果", size=14, color="#6b7280"),
            ft.Divider(),
            ft.Row(
                spacing=12,
                controls=[
                    ft.Container(
                        padding=16,
                        on_click=lambda e: page.go("/general"),
                        ink=True,
                        border_radius=12,
                        bgcolor="#e0e7ff",
                        content=ft.Column(
                            spacing=2,
                            controls=[
                                ft.Text("General", size=16, weight="bold"),
                                ft.Text("通用组件", size=13, color="#6b7280"),
                            ],
                        ),
                    ),
                    ft.Container(
                        padding=16,
                        on_click=lambda e: page.go("/layout"),
                        ink=True,
                        border_radius=12,
                        bgcolor="#dcfce7",
                        content=ft.Column(
                            spacing=2,
                            controls=[
                                ft.Text("Layout", size=16, weight="bold"),
                                ft.Text("布局组件", size=13, color="#6b7280"),
                            ],
                        ),
                    ),
                ],
            ),
        ],
        padding=20,
        bgcolor="#f8fafc",
    )

def general_view(page):
    return ft.View(
        route="/general",
        appbar=ft.AppBar(title=ft.Text("General 通用组件"), bgcolor="#1f6feb", color="white"),
        controls=[
            ft.Text("Button 按钮", size=20, weight="bold"),
            ft.Row(
                spacing=12,
                controls=[
                    ft.ElevatedButton("主要按钮"),
                    ft.ElevatedButton("次要按钮"),
                ],
            ),
        ],
        padding=20,
        bgcolor="#f8fafc",
    )

def layout_view(page):
    return ft.View(
        route="/layout",
        appbar=ft.AppBar(title=ft.Text("Layout 布局组件"), bgcolor="#1f6feb", color="white"),
        controls=[
            ft.Text("Row 行布局", size=20, weight="bold"),
            ft.Row(
                spacing=8,
                controls=[
                    ft.Container(bgcolor="#ef4444", width=60, height=40, border_radius=4),
                    ft.Container(bgcolor="#10b981", width=60, height=40, border_radius=4),
                    ft.Container(bgcolor="#3b82f6", width=60, height=40, border_radius=4),
                ],
            ),
        ],
        padding=20,
        bgcolor="#f8fafc",
    )

ROUTES = {
    "/": home_view,
    "/general": general_view,
    "/layout": layout_view,
}

def main(page: ft.Page):
    page.title = "CS UI Demo"
    page.bgcolor = "#f8fafc"

    def route_change(e):
        page.views.clear()
        route = page.route or "/"
        builder = ROUTES.get(route, home_view)
        page.views.append(builder(page))
        page.update()

    page.on_route_change = route_change
    page.go(page.route or "/")

ft.run(main)