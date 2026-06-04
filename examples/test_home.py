import flet as ft
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ui import Text, Card, Container, Column, Row, Divider


def home_view(page):
    """首页 - 导航入口"""
    nav_items = [
        ("core", "Core", "核心工具", ft.Icons.BUILD),
        ("general", "General", "通用组件", ft.Icons.WIDGETS),
        ("layout", "Layout", "布局组件", ft.Icons.VIEW_QUILT),
    ]
    cards = []
    for route, title, desc, icon in nav_items:
        cards.append(
            Card(
                elevation=2,
                content=Container(
                    padding=16,
                    on_click=lambda e, r=route: page.go(f"/{r}"),
                    ink=True,
                    border_radius=12,
                    content=Row(
                        ft.Icon(icon, size=32, color="#1f6feb"),
                        Column(
                            Text(title, size=16, weight="bold"),
                            Text(desc, size=13, color="#6b7280"),
                            spacing=2,
                        ),
                        alignment="start",
                        spacing=12,
                    ),
                ),
            )
        )
    return ft.View(
        route="/",
        appbar=ft.AppBar(title=ft.Text("CS UI Demo"), bgcolor="#1f6feb", color="white"),
        controls=[
            Text("CS UI 组件库", size=28, weight="bold", color="#1f2937"),
            Divider(),
            Column(*cards, spacing=8),
        ],
        padding=20,
        bgcolor="#f8fafc",
    )


def main(page: ft.Page):
    page.title = "Test Demo"
    page.bgcolor = "#f8fafc"

    page.views.append(home_view(page))
    page.update()


ft.run(main)
