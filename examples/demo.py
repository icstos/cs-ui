import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import flet as ft
from cs_ui import (
    App,
    Badge,
    Button,
    Card,
    Checkbox,
    Chip,
    Column,
    Container,
    Divider,
    Dropdown,
    IconButton,
    Loading,
    ProgressBar,
    Row,
    Slider,
    Switch,
    Tabs,
    Text,
    TextField,
    Tooltip,
)


def main(page):
    # --- 通用组件 ---
    page.add(Text("通用组件", size=24, weight="bold"))
    page.add(
        Row(
            Button(label="主要按钮", on_click=lambda e: page.add(Text("按钮已点击!", color="green"))),
            Button(label="禁用按钮", disabled=True),
            IconButton(icon=ft.Icons.FAVORITE, tooltip="喜欢",
                       on_click=lambda e: page.add(Text("IconButton 点击", color="blue"))),
            spacing=12,
        )
    )
    page.add(
        Row(
            ft.FilledIconButton(
                icon=ft.Icons.MAIL,
                badge=Badge(badge_value=5),
            ),
            ft.FilledIconButton(
                icon=ft.Icons.SHOPPING_CART,
                badge=Badge(badge_value=100, max_value=99),
            ),
            Chip(label_text="标签一"),
            Chip(label_text="标签二"),
            Divider(),
            spacing=16,
        )
    )
    page.add(
        Tooltip(message="这是一个提示", content=Text("鼠标悬停查看提示", color="#1f6feb"))
    )

    # --- 布局组件 ---
    page.add(Text("布局组件", size=24, weight="bold"))
    page.add(
        Card(
            bgcolor="#ffffff",
            elevation=4,
            content=Container(
                padding=24,
                border_radius=16,
                bgcolor="#ffffff",
                content=Column(
                    Text("卡片标题", size=18, weight="bold"),
                    Text("这是卡片内容，使用 Card + Container + Column 组合。", size=14, color="#333333"),
                    spacing=8,
                ),
            ),
        )
    )

    # --- 表单组件 ---
    page.add(Text("表单组件", size=24, weight="bold"))
    page.add(
        Column(
            TextField(label="输入内容", hint_text="按回车提交", width=320,
                      on_submit=lambda e: page.add(Text(f"提交内容：{e.control.value}", color="green"))),
            Dropdown(label="选择一项", options_list=["选项一", "选项二", "选项三"], value="选项一", width=320,
                     on_change=lambda e: page.add(Text(f"下拉选择：{e.control.value}"))),
            Slider(value=20, min=0, max=100, divisions=10, label="滑块值", width=320,
                   on_change=lambda e: page.add(Text(f"滑块值：{e.control.value}"))),
            Row(
                Checkbox(label="我已阅读", on_change=lambda e: page.add(Text(f"勾选状态：{e.control.value}"))),
                Switch(label="开关示例", on_change=lambda e: page.add(Text(f"开关状态：{e.control.value}"))),
                spacing=20,
            ),
            spacing=16,
        )
    )

    # --- 反馈组件 ---
    page.add(Text("反馈组件", size=24, weight="bold"))
    page.add(
        Row(
            ProgressBar(progress=60, width=200, color="#4caf50"),
            Loading(),
            Loading(size_name="small"),
            Loading(size_name="large"),
            spacing=20,
        )
    )


if __name__ == "__main__":
    App(title="CS UI Demo", on_start=main).run()
