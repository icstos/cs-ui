"""CS UI 表单组件测试示例 - 展示全部输入控件"""

import os
import sys
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import flet as ft
from ui import (
    Input,
    NumberInput,
    Button,
    SelectBox,
    Checkbox,
    CheckboxGroup,
    Radio,
    Switch,
    Slider,
    Rating,
    SegmentedButton,
    Chip,
    SearchBar,
    Text,
    Divider,
    Column,
    Row,
    Container,
)
from ui.core.constants import LayoutType, StyleType


def main(page: ft.Page):
    page.title = "CS UI 表单组件"
    page.bgcolor = "#f8fafc"
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 20

    # 输出框
    output = ft.Text(size=14, color="#6b7280")

    page.add(
        ft.Text("Form 表单组件", size=28, weight=ft.FontWeight.BOLD, color="#1f2937"),
        ft.Text("全部输入控件的综合展示", size=14, color="#6b7280"),
        Divider(),
        # 1. 文本输入
        ft.Text("1. Input 文本输入", size=18, weight=ft.FontWeight.BOLD),
        ft.Text('label="用户名", hint_text="请输入用户名"', size=12, color="#6b7280"),
        Input(label="用户名", hint_text="请输入用户名", width=320),
        ft.Text(
            'label="密码", password=True, can_reveal_password=True',
            size=12,
            color="#6b7280",
        ),
        Input(
            label="密码",
            hint_text="请输入密码",
            password=True,
            can_reveal_password=True,
            width=320,
        ),
        Divider(),
        # 2. 数字输入
        ft.Text("2. NumberInput 数字输入", size=18, weight=ft.FontWeight.BOLD),
        ft.Text("带增减按钮的数值输入框", size=12, color="#6b7280"),
        NumberInput(label="数量", value=0, width=200),
        NumberInput(label="价格", value=9.99, width=200),
        Divider(),
        # 3. 下拉选择
        ft.Text("3. SelectBox 下拉选择", size=18, weight=ft.FontWeight.BOLD),
        SelectBox(
            label="选择城市", options=["北京", "上海", "广州", "深圳"], width=320
        ),
        Divider(),
        # 4. 复选框
        ft.Text("4. Checkbox 复选框", size=18, weight=ft.FontWeight.BOLD),
        Checkbox(label="我已阅读并同意用户协议"),
        Checkbox(label="订阅邮件通知", value=True),
        Divider(),
        # 5. 多选框组
        ft.Text("5. CheckboxGroup 多选框组", size=18, weight=ft.FontWeight.BOLD),
        CheckboxGroup(
            options=["Python", "JavaScript", "Go", "Rust", "TypeScript"],
            layout_type=LayoutType.VERTICAL,
        ),
        Divider(),
        # 6. 开关
        ft.Text("6. Switch 开关", size=18, weight=ft.FontWeight.BOLD),
        Row(
            spacing=16,
            controls=[
                Column(
                    spacing=4,
                    controls=[ft.Text("深色模式", size=13), Switch(value=False)],
                ),
                Column(
                    spacing=4,
                    controls=[ft.Text("自动保存", size=13), Switch(value=True)],
                ),
                Column(
                    spacing=4, controls=[ft.Text("通知", size=13), Switch(value=True)]
                ),
            ],
        ),
        Divider(),
        # 7. 滑块
        ft.Text("7. Slider 滑块", size=18, weight=ft.FontWeight.BOLD),
        ft.Text("min=0, max=100, divisions=10, label='{value}%'", size=12),
        Slider(min=0, max=100, divisions=10, label="{value}%", width=320),
        Divider(),
        # 8. 评分
        ft.Text("8. Rating 评分控件", size=18, weight=ft.FontWeight.BOLD),
        ft.Text("点击星星进行评分", size=12, color="#6b7280"),
        Rating(on_change=lambda v: print(f"评分: {v}")),
        Divider(),
        # 9. 单选组
        ft.Text("9. Radio 单选组", size=18, weight=ft.FontWeight.BOLD),
        Radio(
            options=["男", "女", "其他"],
            value="男",
            on_change=lambda e: print(f"选择: {e.data}"),
        ),
        Divider(),
        # 10. 分段按钮
        ft.Text("10. SegmentedButton 分段按钮", size=18, weight=ft.FontWeight.BOLD),
        SegmentedButton(
            options=["日", "周", "月", "年"],
            on_change=lambda e: print(f"分段选择: {e.data}"),
        ),
        Divider(),
        # 11. Chip
        ft.Text("11. Chip 标签", size=18, weight=ft.FontWeight.BOLD),
        Row(
            spacing=8,
            controls=[
                Chip(label="Python"),
                Chip(label="Flet"),
                Chip(label="UI 框架"),
                Chip(label="开源"),
            ],
        ),
        Divider(),
        # 12. 搜索栏
        ft.Text("12. SearchBar 搜索栏", size=18, weight=ft.FontWeight.BOLD),
        ft.Text("输入关键词搜索选项", size=12, color="#6b7280"),
        SearchBar(
            options=["Python", "JavaScript", "TypeScript", "Go", "Rust", "Java"],
            width=320,
        ),
        Divider(),
        # 13. 提交按钮
        ft.Text("13. 表单提交按钮", size=18, weight=ft.FontWeight.BOLD),
        Row(
            spacing=12,
            controls=[
                Button(
                    content=ft.Text("提交"),
                    style_type=StyleType.PRIMARY,
                    on_click=lambda e: print("提交"),
                ),
                Button(
                    content=ft.Text("重置"),
                    plain=True,
                    on_click=lambda e: print("重置"),
                ),
            ],
        ),
    )


if __name__ == "__main__":
    ft.run(main)
