"""CS UI 反馈组件测试示例 - 展示进度条、加载、对话框、消息提示"""

import os
import sys
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import flet as ft
from ui import (
    ProgressBar,
    Loading,
    AlertDialog,
    Message,
    Button,
    Text,
    Divider,
    Column,
    Row,
)
from ui.core.constants import StyleType


def main(page: ft.Page):
    page.title = "CS UI 反馈组件"
    page.bgcolor = "#f8fafc"
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 20

    # 创建对话框实例
    default_dialog = AlertDialog(
        title="确认操作",
        msg="你确定要执行此操作吗？",
        on_yes_click=lambda e: print("已确认"),
        on_no_click=lambda e: print("已取消"),
    )
    primary_dialog = AlertDialog(
        title="主色调对话框",
        msg="这是一个主色调对话框",
        style_type=StyleType.PRIMARY,
        on_yes_click=lambda e: print("primary yes"),
        on_no_click=lambda e: print("primary no"),
    )
    success_dialog = AlertDialog(
        title="操作成功",
        msg="文件已成功保存",
        style_type=StyleType.SUCCESS,
        on_yes_click=lambda e: print("success ok"),
    )
    warning_dialog = AlertDialog(
        title="警告",
        msg="磁盘空间不足，请及时清理",
        style_type=StyleType.WARNING,
        on_yes_click=lambda e: print("warning ok"),
        on_no_click=lambda e: print("warning no"),
    )
    error_dialog = AlertDialog(
        title="错误",
        msg="连接服务器失败，请检查网络",
        style_type=StyleType.ERROR,
        on_yes_click=lambda e: print("error ok"),
        on_no_click=lambda e: print("error no"),
    )
    info_dialog = AlertDialog(
        title="信息",
        msg="系统将在 10 分钟后自动更新",
        style_type=StyleType.INFO,
        on_yes_click=lambda e: print("info ok"),
    )

    def show_default_dialog(e):
        default_dialog.show(e.page)

    def show_primary_dialog(e):
        primary_dialog.show(e.page)

    def show_success_dialog(e):
        success_dialog.show(e.page)

    def show_warning_dialog(e):
        warning_dialog.show(e.page)

    def show_error_dialog(e):
        error_dialog.show(e.page)

    def show_info_dialog(e):
        info_dialog.show(e.page)

    page.add(
        ft.Text(
            "Feedback 反馈组件", size=28, weight=ft.FontWeight.BOLD, color="#1f2937"
        ),
        ft.Text("进度条、加载状态、对话框和消息提示", size=14, color="#6b7280"),
        Divider(),
        # 1. ProgressBar
        ft.Text("1. ProgressBar 进度条", size=18, weight=ft.FontWeight.BOLD),
        ft.Text("进度 30%（百分比模式）", size=12, color="#6b7280"),
        ProgressBar(progress=30, width=400, color="#1f6feb"),
        ft.Text("进度 0.7（小数模式）", size=12, color="#6b7280"),
        ProgressBar(progress=0.7, width=400, color="#10b981"),
        ft.Text("进度 100%（满进度）", size=12, color="#6b7280"),
        ProgressBar(progress=100, width=400, color="#f59e0b"),
        Divider(),
        # 2. Loading
        ft.Text("2. Loading 加载指示器", size=18, weight=ft.FontWeight.BOLD),
        Row(
            alignment="end",
            spacing=24,
            controls=[
                Column(
                    spacing=4,
                    controls=[
                        ft.Text("small", size=11, color="#6b7280"),
                        Loading(size_name="small"),
                    ],
                ),
                Column(
                    spacing=4,
                    controls=[
                        ft.Text("normal", size=11, color="#6b7280"),
                        Loading(size_name="normal"),
                    ],
                ),
                Column(
                    spacing=4,
                    controls=[
                        ft.Text("large", size=11, color="#6b7280"),
                        Loading(size_name="large"),
                    ],
                ),
            ],
        ),
        Divider(),
        # 3. Message (SnackBar)
        ft.Text("3. Message 消息提示", size=18, weight=ft.FontWeight.BOLD),
        ft.Text("类似 SnackBar，支持多种语义风格", size=12, color="#6b7280"),
        Row(
            spacing=8,
            controls=[
                Button(
                    content=ft.Text("默认消息"),
                    on_click=lambda e: Message(content="这是一条默认消息").show(),
                ),
                Button(
                    content=ft.Text("成功消息"),
                    style_type=StyleType.SUCCESS,
                    on_click=lambda e: Message(
                        content="操作成功！", style_type=StyleType.SUCCESS
                    ).show(),
                ),
                Button(
                    content=ft.Text("错误消息"),
                    style_type=StyleType.ERROR,
                    on_click=lambda e: Message(
                        content="操作失败，请重试", style_type=StyleType.ERROR
                    ).show(),
                ),
                Button(
                    content=ft.Text("警告消息"),
                    style_type=StyleType.WARNING,
                    on_click=lambda e: Message(
                        content="请注意保存数据", style_type=StyleType.WARNING
                    ).show(),
                ),
            ],
        ),
        Divider(),
        # 4. AlertDialog
        ft.Text("4. AlertDialog 对话框", size=18, weight=ft.FontWeight.BOLD),
        ft.Text("支持多种风格，带标题和操作按钮", size=12, color="#6b7280"),
        Row(
            spacing=8,
            controls=[
                Button(content=ft.Text("默认对话框"), on_click=show_default_dialog),
                Button(
                    content=ft.Text("主要"),
                    style_type=StyleType.PRIMARY,
                    on_click=show_primary_dialog,
                ),
                Button(
                    content=ft.Text("成功"),
                    style_type=StyleType.SUCCESS,
                    on_click=show_success_dialog,
                ),
                Button(
                    content=ft.Text("警告"),
                    style_type=StyleType.WARNING,
                    on_click=show_warning_dialog,
                ),
                Button(
                    content=ft.Text("错误"),
                    style_type=StyleType.ERROR,
                    on_click=show_error_dialog,
                ),
                Button(
                    content=ft.Text("信息"),
                    style_type=StyleType.INFO,
                    on_click=show_info_dialog,
                ),
            ],
        ),
    )


if __name__ == "__main__":
    ft.run(main)
