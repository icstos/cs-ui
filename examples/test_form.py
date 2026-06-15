"""CS UI 表单组件测试示例 - 展示全部输入控件"""

import os
import sys
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_root, "src"))
sys.path.insert(0, _root)

import flet as ft
from ui import (
    Input,
    Button,
    SelectBox,
    Checkbox,
    CheckboxGroup,
    Radio,
    Rating,
    SegmentedButton,
    Chip,
    SearchBar,
    Divider,
    Column,
    Row,
    Switch,
    Slider,
)
from ui.core.constants import LayoutType, StyleType


@ft.component
def App():
    username = Input(label="用户名", hint_text="请输入用户名")
    quantity = Input(label="数量", value=0, data_type="int")
    price = Input(label="价格", value=9.99, data_type="float")
    city_select = SelectBox(label="选择城市", options=["北京", "上海", "广州", "深圳"])
    agree = Checkbox(label="我已阅读并同意用户协议")
    subscribe = Checkbox(label="订阅邮件通知", value=True)
    skills = CheckboxGroup(
        options=["Python", "JavaScript", "Go", "Rust", "TypeScript"],
        checkbox_layout_type=LayoutType.VERTICAL,
    )
    dark_mode = Switch(label="深色模式", value=False)
    auto_save = Switch(label="自动保存", value=True)
    notify = Switch(label="通知", value=True)
    volume_slider = Slider(min=0, max=100, divisions=10, slider_label="{value}%")
    gender = Radio(options=["男", "女", "其他"], value="男")
    tags = Chip(options=["Python", "Flet", "UI 框架", "开源"])

    return Column(
        spacing=8,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Text(
                "Form 表单组件", size=28, weight=ft.FontWeight.BOLD, color="#1f2937"
            ),
            ft.Text("全部输入控件的综合展示", size=14, color="#6b7280"),
            Divider(),
            ft.Text("1. Input 文本输入", size=18, weight=ft.FontWeight.BOLD),
            ft.Text(
                'label="用户名", hint_text="请输入用户名"', size=12, color="#6b7280"
            ),
            username.ui(),
            ft.Text(
                "password=True, can_reveal_password=True", size=12, color="#6b7280"
            ),
            ft.TextField(
                label="密码",
                hint_text="请输入密码",
                password=True,
                can_reveal_password=True,
                width=320,
            ),
            Divider(),
            ft.Text("2. NumberInput 数字输入", size=18, weight=ft.FontWeight.BOLD),
            ft.Text("带增减按钮的数值输入框", size=12, color="#6b7280"),
            quantity.ui(),
            price.ui(),
            Divider(),
            ft.Text("3. SelectBox 下拉选择", size=18, weight=ft.FontWeight.BOLD),
            city_select.ui(),
            Divider(),
            ft.Text("4. Checkbox 复选框", size=18, weight=ft.FontWeight.BOLD),
            agree.ui(),
            subscribe.ui(),
            Divider(),
            ft.Text("5. CheckboxGroup 多选框组", size=18, weight=ft.FontWeight.BOLD),
            skills.ui(),
            Divider(),
            ft.Text("6. Switch 开关", size=18, weight=ft.FontWeight.BOLD),
            Row(
                spacing=16,
                controls=[dark_mode.ui(), auto_save.ui(), notify.ui()],
            ),
            Divider(),
            ft.Text("7. Slider 滑块", size=18, weight=ft.FontWeight.BOLD),
            ft.Text(
                "min=0, max=100, divisions=10, slider_label='{value}%'", size=12
            ),
            ft.Container(content=volume_slider.ui(), width=320),
            Divider(),
            ft.Text("8. Rating 评分控件", size=18, weight=ft.FontWeight.BOLD),
            ft.Text("点击星星进行评分", size=12, color="#6b7280"),
            Rating(on_change=lambda v: print(f"评分: {v}")),
            Divider(),
            ft.Text("9. Radio 单选组", size=18, weight=ft.FontWeight.BOLD),
            gender.ui(),
            Divider(),
            ft.Text("10. SegmentedButton 分段按钮", size=18, weight=ft.FontWeight.BOLD),
            SegmentedButton(options=["日", "周", "月", "年"]),
            Divider(),
            ft.Text("11. Chip 标签", size=18, weight=ft.FontWeight.BOLD),
            tags.ui(),
            Divider(),
            ft.Text("12. SearchBar 搜索栏", size=18, weight=ft.FontWeight.BOLD),
            ft.Text("输入关键词搜索选项", size=12, color="#6b7280"),
            ft.Container(
                content=SearchBar(
                    options=[
                        "Python",
                        "JavaScript",
                        "TypeScript",
                        "Go",
                        "Rust",
                        "Java",
                    ],
                ),
                width=320,
            ),
            Divider(),
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
        ],
    )


def main(page: ft.Page):
    page.title = "CS UI 表单组件"
    page.bgcolor = "#f8fafc"
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 20
    page.render(App)


if __name__ == "__main__":
    ft.run(main)
