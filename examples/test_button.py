"""CS UI Button 组件测试示例 - 展示所有按钮风格、形状和状态"""

import os
import sys
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import flet as ft
from ui.input.button import Button
from ui.core.constants import StyleType, ButtonShape


def main(page: ft.Page):
    page.title = "CS UI Button 按钮组件"
    page.bgcolor = "#f8fafc"
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 20

    page.add(
        ft.Text("Button 按钮组件", size=28, weight=ft.FontWeight.BOLD, color="#1f2937"),
        ft.Text(
            "支持多种风格 (style_type) 和形状 (shape) 的组合", size=14, color="#6b7280"
        ),
        ft.Divider(),
        # 1. 实心按钮 - 所有风格
        ft.Text("1. 实心按钮 (plain=False)", size=18, weight=ft.FontWeight.BOLD),
        ft.Row(
            spacing=8,
            controls=[
                Button(content=ft.Text("默认"), style_type=StyleType.DEFAULT),
                Button(content=ft.Text("主要"), style_type=StyleType.PRIMARY),
                Button(content=ft.Text("信息"), style_type=StyleType.INFO),
                Button(content=ft.Text("成功"), style_type=StyleType.SUCCESS),
                Button(content=ft.Text("警告"), style_type=StyleType.WARNING),
                Button(content=ft.Text("错误"), style_type=StyleType.ERROR),
            ],
        ),
        ft.Divider(),
        # 2. 描边按钮 (plain=True)
        ft.Text("2. 描边按钮 (plain=True)", size=18, weight=ft.FontWeight.BOLD),
        ft.Row(
            spacing=8,
            controls=[
                Button(
                    content=ft.Text("默认"), style_type=StyleType.DEFAULT, plain=True
                ),
                Button(
                    content=ft.Text("主要"), style_type=StyleType.PRIMARY, plain=True
                ),
                Button(content=ft.Text("信息"), style_type=StyleType.INFO, plain=True),
                Button(
                    content=ft.Text("成功"), style_type=StyleType.SUCCESS, plain=True
                ),
                Button(
                    content=ft.Text("警告"), style_type=StyleType.WARNING, plain=True
                ),
                Button(content=ft.Text("错误"), style_type=StyleType.ERROR, plain=True),
            ],
        ),
        ft.Divider(),
        # 3. 按钮形状
        ft.Text("3. 按钮形状", size=18, weight=ft.FontWeight.BOLD),
        ft.Row(
            spacing=8,
            controls=[
                Button(
                    content=ft.Text("矩形"),
                    style_type=StyleType.PRIMARY,
                    shape=ButtonShape.RECTANGLE,
                ),
                Button(
                    content=ft.Text("圆角"),
                    style_type=StyleType.PRIMARY,
                    shape=ButtonShape.ROUND,
                ),
                Button(
                    content=ft.Text("胶囊"),
                    style_type=StyleType.PRIMARY,
                    shape=ButtonShape.CIRCLE,
                ),
            ],
        ),
        ft.Divider(),
        # 4. 禁用状态
        ft.Text("4. 禁用状态 (disabled=True)", size=18, weight=ft.FontWeight.BOLD),
        ft.Row(
            spacing=8,
            controls=[
                Button(
                    content=ft.Text("默认"), style_type=StyleType.DEFAULT, disabled=True
                ),
                Button(
                    content=ft.Text("主要"),
                    style_type=StyleType.PRIMARY,
                    plain=True,
                    disabled=True,
                ),
                Button(
                    content=ft.Text("成功"),
                    style_type=StyleType.SUCCESS,
                    plain=True,
                    disabled=True,
                ),
                Button(
                    content=ft.Text("危险"), style_type=StyleType.ERROR, disabled=True
                ),
            ],
        ),
        ft.Divider(),
        # 5. 带图标的按钮
        ft.Text("5. 图标按钮", size=18, weight=ft.FontWeight.BOLD),
        ft.Row(
            spacing=8,
            controls=[
                Button(
                    content=ft.Text("添加"),
                    icon=ft.Icons.ADD,
                    style_type=StyleType.PRIMARY,
                ),
                Button(
                    content=ft.Text("编辑"),
                    icon=ft.Icons.EDIT,
                    style_type=StyleType.INFO,
                ),
                Button(
                    content=ft.Text("删除"),
                    icon=ft.Icons.DELETE,
                    style_type=StyleType.ERROR,
                ),
                Button(
                    content=ft.Text("保存"),
                    icon=ft.Icons.SAVE,
                    style_type=StyleType.SUCCESS,
                ),
            ],
        ),
        ft.Divider(),
        # 6. 不同尺寸
        ft.Text("6. 不同尺寸", size=18, weight=ft.FontWeight.BOLD),
        ft.Row(
            spacing=8,
            controls=[
                Button(
                    content=ft.Text("小号", size=12),
                    style_type=StyleType.PRIMARY,
                    height=28,
                ),
                Button(
                    content=ft.Text("默认", size=14),
                    style_type=StyleType.PRIMARY,
                    height=36,
                ),
                Button(
                    content=ft.Text("大号", size=16),
                    style_type=StyleType.PRIMARY,
                    height=44,
                ),
            ],
        ),
    )


if __name__ == "__main__":
    ft.run(main)
