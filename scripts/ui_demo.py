"""CS-UI 组件效果展示 Demo

基于 src/ui 下各组件，使用 flet 0.86.0 声明式编程实现完整的组件效果展示。
运行方式: python scripts/ui_demo.py
"""

import asyncio
import datetime
import math
import os
import random
import sys
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import flet as ft
from ui import (
    # feedback
    AlertDialog,
    App,
    # navigation
    AppBar,
    # input
    Button,
    ButtonShape,
    # layout
    Card,
    Checkbox,
    CheckboxGroup,
    Chip,
    Code,
    DateInput,
    Divider,
    Expander,
    # display
    Header_1,
    Header_2,
    Header_3,
    Header_4,
    Header_5,
    Image,
    Input,
    Json,
    LayoutType,
    # chart
    LineChart,
    Link,
    ListTile,
    Loading,
    LogContainer,
    Markdown,
    Message,
    Paging,
    ProgressBar,
    Quote,
    Radio,
    RangeSlider,
    Rating,
    Route,
    SearchBar,
    SegmentedButton,
    SelectBox,
    Slider,
    # core
    StyleType,
    Switch,
    Tab,
    TabBar,
    TabBarView,
    Table,
    Tabs,
    VerticalDivider,
)

# 直接导入：navigation/__init__.py 未导出 PagingState，
# 加上 ui/__init__.py 末尾设置 __name__ = "cs-ui" 会破坏子模块回退导入
from ui.navigation.paging import PagingState

# 颜色常量
C_PRIMARY = "#1f6feb"
C_MUTED = "#6b7280"
C_DARK = "#1f2937"
C_BG_LIGHT = ft.Colors.with_opacity(0.4, ft.Colors.GREY_100)


# ─── 辅助函数 ──────────────────────────────────────────────────────


def section(title: str, desc: str, content: ft.Control) -> ft.Control:
    """构建展示区块：小标题 + 描述 + 内容容器"""
    return ft.Column(
        controls=[
            Header_4(title),
            ft.Text(desc, size=12, color=C_MUTED) if desc else ft.Container(height=0),
            ft.Container(
                content=content,
                padding=ft.Padding.all(14),
                bgcolor=C_BG_LIGHT,
                border_radius=8,
            ),
        ],
        spacing=6,
    )


def page_shell(title: str, subtitle: str, *content: ft.Control) -> ft.Control:
    """页面外壳：返回按钮 + 标题 + 内容区"""
    return ft.Column(
        controls=[
            ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        tooltip="返回首页",
                        on_click=lambda _: ft.context.page.navigate("/"),
                    ),
                    ft.Column(
                        controls=[
                            Header_3(title),
                            ft.Text(subtitle, size=13, color=C_MUTED),
                        ],
                        spacing=2,
                    ),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            Divider(),
            ft.Column(controls=list(content), spacing=18, expand=True),
        ],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        spacing=8,
    )


# ─── 首页 ─────────────────────────────────────────────────────────


@ft.component
def HomePage():
    nav_items = [
        (
            "buttons",
            "Button 按钮",
            "按钮样式、类型、形状与禁用状态",
            ft.Icons.SMART_BUTTON,
        ),
        (
            "form",
            "Form 表单",
            "输入框、选择器、滑块、开关等表单组件",
            ft.Icons.EDIT_NOTE,
        ),
        (
            "feedback",
            "Feedback 反馈",
            "对话框、消息提示、进度条、日志",
            ft.Icons.FEEDBACK,
        ),
        (
            "layout",
            "Layout 布局",
            "卡片、容器、列表、表格、标签页",
            ft.Icons.VIEW_QUILT,
        ),
        (
            "display",
            "Display 展示",
            "标题文本、代码、Markdown、图片",
            ft.Icons.TABLE_CHART,
        ),
        ("navigation", "Navigation 导航", "应用栏、分页器", ft.Icons.NAVIGATE_NEXT),
        ("chart", "Chart 图表", "折线图数据可视化", ft.Icons.SHOW_CHART),
    ]
    cards = [
        Card(
            elevation=2,
            content=ft.Container(
                padding=16,
                on_click=lambda e, r=route: ft.context.page.navigate(f"/{r}"),
                ink=True,
                border_radius=12,
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.START,
                    spacing=12,
                    controls=[
                        ft.Icon(icon, size=32, color=C_PRIMARY),
                        ft.Column(
                            spacing=2,
                            controls=[
                                ft.Text(title, size=16, weight=ft.FontWeight.BOLD),
                                ft.Text(desc, size=13, color=C_MUTED),
                            ],
                        ),
                    ],
                ),
            ),
        )
        for route, title, desc, icon in nav_items
    ]
    return ft.Column(
        controls=[
            Header_1("CS-UI 组件库"),
            ft.Text(
                "基于 Flet 0.86.0 声明式编程的 Python UI 组件库，点击卡片查看各分类组件效果",
                size=14,
                color=C_MUTED,
            ),
            Divider(),
            ft.Row(controls=cards, wrap=True, spacing=12, run_spacing=12),
        ],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        spacing=8,
    )


# ─── Button 按钮 ──────────────────────────────────────────────────


@ft.component
def ButtonsPage():
    return page_shell(
        "Button 按钮组件",
        "展示不同样式类型、描边、形状与禁用状态的按钮",
        section(
            "按钮类型 (style_type)",
            "DEFAULT / PRIMARY / SUCCESS / INFO / WARNING / ERROR",
            ft.Row(
                spacing=8,
                wrap=True,
                controls=[
                    Button(content="Default", style_type=StyleType.DEFAULT),
                    Button(content="Primary", style_type=StyleType.PRIMARY),
                    Button(content="Success", style_type=StyleType.SUCCESS),
                    Button(content="Info", style_type=StyleType.INFO),
                    Button(content="Warning", style_type=StyleType.WARNING),
                    Button(content="Error", style_type=StyleType.ERROR),
                ],
            ),
        ),
        section(
            "描边按钮 (plain)",
            "plain=True 时背景镂空，仅显示边框",
            ft.Row(
                spacing=8,
                wrap=True,
                controls=[
                    Button(content="Default", style_type=StyleType.DEFAULT, plain=True),
                    Button(content="Primary", style_type=StyleType.PRIMARY, plain=True),
                    Button(content="Success", style_type=StyleType.SUCCESS, plain=True),
                    Button(content="Info", style_type=StyleType.INFO, plain=True),
                    Button(content="Warning", style_type=StyleType.WARNING, plain=True),
                    Button(content="Error", style_type=StyleType.ERROR, plain=True),
                ],
            ),
        ),
        section(
            "按钮形状 (shape)",
            "RECTANGLE / ROUND / CIRCLE",
            ft.Row(
                spacing=8,
                controls=[
                    Button(
                        content="Rectangle",
                        style_type=StyleType.PRIMARY,
                        plain=True,
                        shape=ButtonShape.RECTANGLE,
                    ),
                    Button(
                        content="Round",
                        style_type=StyleType.PRIMARY,
                        plain=True,
                        shape=ButtonShape.ROUND,
                    ),
                    Button(
                        content="Circle",
                        style_type=StyleType.PRIMARY,
                        plain=True,
                        shape=ButtonShape.CIRCLE,
                    ),
                ],
            ),
        ),
        section(
            "禁用状态 (disabled)",
            "disabled=True 时按钮不可点击，颜色变灰",
            ft.Row(
                spacing=8,
                wrap=True,
                controls=[
                    Button(
                        content="Default", style_type=StyleType.DEFAULT, disabled=True
                    ),
                    Button(
                        content="Primary", style_type=StyleType.PRIMARY, disabled=True
                    ),
                    Button(
                        content="Success", style_type=StyleType.SUCCESS, disabled=True
                    ),
                    Button(
                        content="Warning", style_type=StyleType.WARNING, disabled=True
                    ),
                ],
            ),
        ),
        section(
            "图标按钮",
            "Button 携带 icon 属性，以及原生 ft.IconButton",
            ft.Column(
                spacing=12,
                controls=[
                    ft.Row(
                        spacing=8,
                        controls=[
                            Button(
                                content="添加",
                                icon=ft.Icons.ADD,
                                style_type=StyleType.PRIMARY,
                            ),
                            Button(
                                content="删除",
                                icon=ft.Icons.DELETE,
                                style_type=StyleType.ERROR,
                            ),
                            Button(
                                content="保存",
                                icon=ft.Icons.SAVE,
                                style_type=StyleType.SUCCESS,
                            ),
                        ],
                    ),
                    ft.Row(
                        spacing=8,
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.FAVORITE,
                                icon_color=ft.Colors.RED,
                                tooltip="喜欢",
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE, icon_color=C_MUTED, tooltip="删除"
                            ),
                            ft.IconButton(
                                icon=ft.Icons.ADD_CIRCLE,
                                icon_color=ft.Colors.GREEN,
                                tooltip="添加",
                            ),
                            ft.IconButton(
                                icon=ft.Icons.SETTINGS,
                                icon_color=C_PRIMARY,
                                tooltip="设置",
                            ),
                        ],
                    ),
                ],
            ),
        ),
        section(
            "主要按钮 (is_primary)",
            "is_primary=True 等价于 style_type=PRIMARY",
            ft.Row(
                spacing=8,
                controls=[
                    Button(content="Primary Button", is_primary=True),
                    Button(content="With Icon", is_primary=True, icon=ft.Icons.SEND),
                ],
            ),
        ),
    )


# ─── Form 表单 ────────────────────────────────────────────────────


@ft.component
def FormPage():
    username = Input(label="用户名", value="shawn", hint_text="请输入用户名")
    age = Input(label="年龄", value="25", data_type="int")
    price = Input(label="价格", value="99.9", data_type="float")
    filepath = Input(label="文件路径", value="", data_type="file")
    dirpath = Input(label="目录路径", value="", data_type="dir")
    city = SelectBox(
        label="所在城市", options=["北京", "上海", "广州", "深圳"], value="北京"
    )
    agree = Checkbox(label="同意用户协议", value=True)
    hobbies = CheckboxGroup(
        label="兴趣爱好",
        options=["阅读", "音乐", "运动", "旅行", "编程"],
        value=["阅读", "编程"],
    )
    dark_mode = Switch(label="深色模式", value=False)
    auto_save = Switch(label="自动保存", value=True, is_vertical=True)
    gender = Radio(label="性别", options=["男", "女", "其他"], value="男")
    volume = Slider(
        label="音量", value=0.3, min=0, max=1, divisions=10, slider_label="{value:.0%}"
    )
    price_range = RangeSlider(
        label="价格范围",
        min=0,
        max=1000,
        start_value=200,
        end_value=800,
        divisions=10,
        slider_label="{value}",
    )
    birth_date = DateInput(label="出生日期", value=datetime.date(2000, 1, 1))
    single_chip = Chip(label="单选 Chip", options=["Python", "Flet", "Rust"])
    multi_chip = Chip(
        label="多选 Chip",
        options=["前端", "后端", "全栈", "运维"],
        multi_select=True,
        is_vertical=True,
    )
    segmented = SegmentedButton(
        options=["日", "周", "月", "年"],
        selected=["月"],
        allow_multiple_selection=False,
    )

    def print_values(e):
        print(f"用户名: {username.value}")
        print(f"年龄: {age.value}")
        print(f"价格: {price.value}")
        print(f"文件: {filepath.value}")
        print(f"目录: {dirpath.value}")
        print(f"城市: {city.value}")
        print(f"同意: {agree.value}")
        print(f"爱好: {hobbies.value}")
        print(f"深色: {dark_mode.value}, 自动保存: {auto_save.value}")
        print(f"性别: {gender.value}")
        print(f"音量: {volume.value}")
        print(f"价格范围: {price_range.start_value} - {price_range.end_value}")
        print(f"生日: {birth_date.value}")
        print(f"单选Chip: {single_chip.value}")
        print(f"多选Chip: {multi_chip.selected_values}")

    return page_shell(
        "Form 表单组件",
        "输入框、选择器、复选框、开关、滑块、标签、评分、日期等表单组件",
        section(
            "文本输入 (Input)",
            "支持 str / int / float 数据类型，int/float 自带增减按钮",
            ft.Column(
                spacing=10,
                controls=[
                    username.ui(),
                    age.ui(),
                    price.ui(),
                ],
            ),
        ),
        section(
            "文件 / 目录选择 (Input data_type=file/dir)",
            "点击前缀图标打开系统文件/目录选择器",
            ft.Column(spacing=10, controls=[filepath.ui(), dirpath.ui()]),
        ),
        section(
            "下拉选择 (SelectBox)",
            "基于 DropdownM2 封装的单选下拉框",
            city.ui(),
        ),
        section(
            "复选框 (Checkbox / CheckboxGroup)",
            "单个复选框与支持全选的多选组",
            ft.Column(spacing=8, controls=[agree.ui(), hobbies.ui()]),
        ),
        section(
            "开关 (Switch)",
            "水平与垂直布局的开关组件",
            ft.Column(spacing=8, controls=[dark_mode.ui(), auto_save.ui()]),
        ),
        section(
            "单选组 (Radio)",
            "水平布局的单选按钮组",
            gender.ui(),
        ),
        section(
            "滑块 (Slider / RangeSlider)",
            "单值滑块与双值范围滑块",
            ft.Column(spacing=10, controls=[volume.ui(), price_range.ui()]),
        ),
        section(
            "标签选择 (Chip)",
            "单选与多选 Chip 标签",
            ft.Column(spacing=10, controls=[single_chip.ui(), multi_chip.ui()]),
        ),
        section(
            "评分 (Rating)",
            "点击星星选择评分，再次点击同一颗星可重置",
            ft.Column(
                spacing=8,
                controls=[
                    ft.Text("请评分:", size=13),
                    Rating(value=4, on_change=lambda v: print(f"评分: {v}")),
                    ft.Text("只读模式:", size=13),
                    Rating(value=3, readonly=True),
                ],
            ),
        ),
        section(
            "分段按钮 (SegmentedButton)",
            "allow_multiple_selection=False 时为单选模式",
            segmented,
        ),
        section(
            "日期选择 (DateInput)",
            "年/月/日三下拉框，自动处理闰年",
            birth_date.ui(),
        ),
        section(
            "搜索栏 (SearchBar)",
            "点击展开选项列表",
            SearchBar(options=["Python", "Flet", "CS-UI", "JavaScript", "Rust"]),
        ),
        section(
            "表单值",
            "点击按钮在控制台打印所有表单组件的当前值",
            Button(
                content="打印表单值",
                icon=ft.Icons.PRINT,
                on_click=print_values,
                is_primary=True,
            ),
        ),
    )


# ─── Feedback 反馈 ────────────────────────────────────────────────


@ft.component
def FeedbackPage():
    # AlertDialog 实例
    default_dialog = AlertDialog(
        title="确认操作", msg="你确定要执行此操作吗？此操作不可撤销。"
    )
    primary_dialog = AlertDialog(
        title="提示", msg="这是一条主要信息提示。", style_type=StyleType.PRIMARY
    )
    success_dialog = AlertDialog(
        title="操作成功", msg="数据已成功保存到服务器。", style_type=StyleType.SUCCESS
    )
    warning_dialog = AlertDialog(
        title="警告",
        msg="此操作可能存在风险，请谨慎操作。",
        style_type=StyleType.WARNING,
    )
    error_dialog = AlertDialog(
        title="错误", msg="操作失败，请检查网络连接后重试。", style_type=StyleType.ERROR
    )
    info_dialog = AlertDialog(
        title="信息", msg="系统将于今晚 22:00 进行维护。", style_type=StyleType.INFO
    )

    # LogContainer 实例
    log_container = LogContainer(
        logs=["[INFO] 系统初始化完成", "[SUCCESS] 所有服务已就绪"], height=180
    )

    async def add_logs(e):
        await log_container.add("[INFO] 正在处理请求...")
        await asyncio.sleep(0.4)
        await log_container.add("[WARNING] 检测到潜在风险")
        await asyncio.sleep(0.4)
        await log_container.add("[ERROR] 请求处理失败，错误码: 500")
        await asyncio.sleep(0.4)
        await log_container.add("[SUCCESS] 重试成功，任务完成")

    def clear_logs(e):
        log_container.clear()

    return page_shell(
        "Feedback 反馈组件",
        "对话框、消息提示、进度条、加载动画与日志容器",
        section(
            "对话框 (AlertDialog)",
            "6 种样式类型的模态对话框",
            ft.Row(
                spacing=8,
                wrap=True,
                controls=[
                    Button(
                        content="Default",
                        on_click=lambda e: default_dialog.show(e.page),
                    ),
                    Button(
                        content="Primary",
                        style_type=StyleType.PRIMARY,
                        on_click=lambda e: primary_dialog.show(e.page),
                    ),
                    Button(
                        content="Success",
                        style_type=StyleType.SUCCESS,
                        on_click=lambda e: success_dialog.show(e.page),
                    ),
                    Button(
                        content="Warning",
                        style_type=StyleType.WARNING,
                        on_click=lambda e: warning_dialog.show(e.page),
                    ),
                    Button(
                        content="Error",
                        style_type=StyleType.ERROR,
                        on_click=lambda e: error_dialog.show(e.page),
                    ),
                    Button(
                        content="Info",
                        style_type=StyleType.INFO,
                        on_click=lambda e: info_dialog.show(e.page),
                    ),
                ],
            ),
        ),
        section(
            "消息提示 (Message)",
            "SnackBar 样式的底部消息提示，6 种类型",
            ft.Row(
                spacing=8,
                wrap=True,
                controls=[
                    Button(
                        content="Default",
                        on_click=lambda e: Message(content="这是一条默认消息").show(),
                    ),
                    Button(
                        content="Primary",
                        style_type=StyleType.PRIMARY,
                        on_click=lambda e: Message(
                            content="主要消息", style_type=StyleType.PRIMARY
                        ).show(),
                    ),
                    Button(
                        content="Success",
                        style_type=StyleType.SUCCESS,
                        on_click=lambda e: Message(
                            content="操作成功！", style_type=StyleType.SUCCESS
                        ).show(),
                    ),
                    Button(
                        content="Warning",
                        style_type=StyleType.WARNING,
                        on_click=lambda e: Message(
                            content="请注意风险", style_type=StyleType.WARNING
                        ).show(),
                    ),
                    Button(
                        content="Error",
                        style_type=StyleType.ERROR,
                        on_click=lambda e: Message(
                            content="操作失败", style_type=StyleType.ERROR
                        ).show(),
                    ),
                    Button(
                        content="Info",
                        style_type=StyleType.INFO,
                        on_click=lambda e: Message(
                            content="系统提示", style_type=StyleType.INFO
                        ).show(),
                    ),
                ],
            ),
        ),
        section(
            "进度条 (ProgressBar)",
            "支持百分比 (0-100) 和小数 (0.0-1.0) 两种模式",
            ft.Column(
                spacing=10,
                controls=[
                    ft.Text("progress=30 (百分比模式)", size=12, color=C_MUTED),
                    ProgressBar(progress=30, color=C_PRIMARY),
                    ft.Text("progress=0.7 (小数模式)", size=12, color=C_MUTED),
                    ProgressBar(progress=0.7, color="#10b981"),
                    ft.Text("progress=100 (满进度)", size=12, color=C_MUTED),
                    ProgressBar(progress=100, color="#f59e0b"),
                ],
            ),
        ),
        section(
            "加载动画 (Loading)",
            "small / normal / large 三种尺寸",
            ft.Row(
                spacing=30,
                vertical_alignment=ft.CrossAxisAlignment.END,
                controls=[
                    ft.Column(
                        spacing=4,
                        controls=[
                            ft.Text("small", size=11, color=C_MUTED),
                            Loading(size_name="small"),
                        ],
                    ),
                    ft.Column(
                        spacing=4,
                        controls=[
                            ft.Text("normal", size=11, color=C_MUTED),
                            Loading(size_name="normal"),
                        ],
                    ),
                    ft.Column(
                        spacing=4,
                        controls=[
                            ft.Text("large", size=11, color=C_MUTED),
                            Loading(size_name="large"),
                        ],
                    ),
                ],
            ),
        ),
        section(
            "日志容器 (LogContainer)",
            "带颜色高亮的滚动日志视图，支持 add / clear",
            ft.Column(
                spacing=10,
                controls=[
                    log_container.ui(),
                    ft.Row(
                        spacing=8,
                        controls=[
                            Button(
                                content="添加日志",
                                icon=ft.Icons.ADD,
                                on_click=add_logs,
                                is_primary=True,
                            ),
                            Button(
                                content="清空日志",
                                icon=ft.Icons.CLEAR,
                                on_click=clear_logs,
                            ),
                        ],
                    ),
                ],
            ),
        ),
    )


# ─── Layout 布局 ──────────────────────────────────────────────────


@ft.component
def LayoutPage():
    # 构建表格数据
    table_rows = [
        ft.DataRow(
            cells=[
                ft.DataCell(ft.Text(f"用户{i:03d}")),
                ft.DataCell(ft.Text(dept)),
                ft.DataCell(ft.Text(str(salary))),
            ]
        )
        for i, (dept, salary) in enumerate(
            [("技术部", 18000), ("市场部", 12000), ("财务部", 15000), ("人事部", 13000)]
            * 3,
            start=1,
        )
    ]
    data_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("姓名")),
            ft.DataColumn(ft.Text("部门")),
            ft.DataColumn(ft.Text("薪资"), numeric=True),
        ],
        rows=table_rows,
    )

    return page_shell(
        "Layout 布局组件",
        "卡片、容器、行列、堆叠、分割线、展开折叠、列表、网格、表格与标签页",
        section(
            "卡片 (Card)",
            "不同 elevation 阴影高度",
            ft.Row(
                spacing=12,
                controls=[
                    Card(
                        elevation=1,
                        content=ft.Container(
                            padding=16,
                            border_radius=8,
                            content=ft.Column(
                                spacing=4,
                                controls=[
                                    ft.Text(
                                        "低阴影", size=15, weight=ft.FontWeight.BOLD
                                    ),
                                    ft.Text("elevation=1", size=12, color=C_MUTED),
                                ],
                            ),
                        ),
                    ),
                    Card(
                        elevation=6,
                        content=ft.Container(
                            padding=16,
                            border_radius=8,
                            content=ft.Column(
                                spacing=4,
                                controls=[
                                    ft.Text(
                                        "高阴影", size=15, weight=ft.FontWeight.BOLD
                                    ),
                                    ft.Text("elevation=6", size=12, color=C_MUTED),
                                ],
                            ),
                        ),
                    ),
                ],
            ),
        ),
        section(
            "容器 (Container)",
            "带背景色与圆角的容器",
            ft.Row(
                spacing=12,
                wrap=True,
                controls=[
                    ft.Container(
                        bgcolor="#dbeafe",
                        padding=16,
                        border_radius=8,
                        content=ft.Text("蓝色容器", color="#1e40af"),
                    ),
                    ft.Container(
                        bgcolor="#dcfce7",
                        padding=16,
                        border_radius=8,
                        content=ft.Text("绿色容器", color="#166534"),
                    ),
                    ft.Container(
                        bgcolor="#fef3c7",
                        padding=16,
                        border_radius=8,
                        content=ft.Text("黄色容器", color="#92400e"),
                    ),
                ],
            ),
        ),
        section(
            "行 / 列布局 (Row / Column)",
            "水平排列与垂直排列",
            ft.Column(
                spacing=10,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                        spacing=8,
                        controls=[
                            ft.Container(
                                bgcolor="#ef4444", width=60, height=40, border_radius=4
                            ),
                            ft.Container(
                                bgcolor="#f59e0b", width=60, height=40, border_radius=4
                            ),
                            ft.Container(
                                bgcolor="#10b981", width=60, height=40, border_radius=4
                            ),
                            ft.Container(
                                bgcolor="#3b82f6", width=60, height=40, border_radius=4
                            ),
                        ],
                    ),
                    ft.Column(
                        spacing=6,
                        controls=[
                            ft.Container(
                                bgcolor="#ef4444", width=200, height=24, border_radius=4
                            ),
                            ft.Container(
                                bgcolor="#f59e0b", width=200, height=24, border_radius=4
                            ),
                            ft.Container(
                                bgcolor="#10b981", width=200, height=24, border_radius=4
                            ),
                        ],
                    ),
                ],
            ),
        ),
        section(
            "堆叠 (Stack)",
            "子控件层叠排列",
            ft.Container(
                width=200,
                height=120,
                border_radius=8,
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                content=ft.Stack(
                    controls=[
                        ft.Container(bgcolor="#3b82f6", width=200, height=120),
                        ft.Container(
                            bgcolor="#ef4444",
                            width=120,
                            height=80,
                            left=40,
                            top=20,
                            border_radius=8,
                        ),
                        ft.Text(
                            "Stack",
                            color=ft.Colors.WHITE,
                            size=20,
                            weight=ft.FontWeight.BOLD,
                            left=70,
                            top=40,
                        ),
                    ],
                ),
            ),
        ),
        section(
            "分割线 (Divider / VerticalDivider)",
            "水平与垂直分割线",
            ft.Row(
                spacing=20,
                controls=[
                    ft.Column(
                        expand=True,
                        controls=[
                            ft.Text("上方文本"),
                            Divider(),
                            ft.Text("下方文本"),
                            Divider(),
                            ft.Text("底部文本"),
                        ],
                    ),
                    ft.Row(
                        controls=[
                            ft.Text("左"),
                            VerticalDivider(width=1),
                            ft.Text("右"),
                        ],
                    ),
                ],
            ),
        ),
        section(
            "展开折叠 (Expander)",
            "点击标题展开/折叠内容，带动画过渡",
            ft.Column(
                spacing=10,
                controls=[
                    Expander(
                        title="Expander 示例一",
                        controls=[
                            ft.Text("这是展开后的第一行内容。", size=13),
                            ft.Text("这是展开后的第二行内容。", size=13),
                            ft.Text("可以放置任意控件。", size=13),
                        ],
                    ),
                    Expander(
                        title="Expander 示例二",
                        controls=[
                            ft.Text("另一个展开内容。", size=13),
                            Button(content="操作按钮", style_type=StyleType.PRIMARY),
                        ],
                    ),
                ],
            ),
        ),
        section(
            "列表视图 (ListView)",
            "可滚动的列表，适合大量条目",
            ft.Container(
                height=180,
                border_radius=8,
                border=ft.border.all(1, ft.Colors.GREY_300),
                content=ft.ListView(
                    expand=True,
                    spacing=0,
                    controls=[
                        ft.Container(
                            padding=10,
                            content=ft.Text(f"列表项 {i + 1}", size=14),
                            bgcolor=ft.Colors.WHITE
                            if i % 2 == 0
                            else ft.Colors.GREY_50,
                        )
                        for i in range(15)
                    ],
                ),
            ),
        ),
        section(
            "网格视图 (GridView)",
            "runs_count 控制每行项数",
            ft.Container(
                height=160,
                border_radius=8,
                border=ft.border.all(1, ft.Colors.GREY_300),
                content=ft.GridView(
                    expand=True,
                    runs_count=4,
                    spacing=8,
                    run_spacing=8,
                    controls=[
                        ft.Container(
                            bgcolor="#dbeafe",
                            border_radius=8,
                            padding=10,
                            content=ft.Text(
                                f"网格 {i + 1}",
                                size=12,
                                color="#1e40af",
                                text_align=ft.TextAlign.CENTER,
                            ),
                        )
                        for i in range(8)
                    ],
                ),
            ),
        ),
        section(
            "数据表格 (Table)",
            "带分页、行号与悬浮高亮的数据表格",
            Table(data_table=data_table, rows_per_page=5, with_paged=True),
        ),
        section(
            "标签页 (Tabs)",
            "TabBar + TabBarView 组合",
            Tabs(
                length=3,
                content=ft.Column(
                    controls=[
                        TabBar(
                            tabs=[
                                Tab(text="概览"),
                                Tab(text="详情"),
                                Tab(text="设置"),
                            ]
                        ),
                        TabBarView(
                            controls=[
                                ft.Container(
                                    ft.Text("概览内容：这里展示概览信息", size=14),
                                    padding=16,
                                ),
                                ft.Container(
                                    ft.Text("详情内容：这里展示详细信息", size=14),
                                    padding=16,
                                ),
                                ft.Container(
                                    ft.Text("设置内容：这里展示设置选项", size=14),
                                    padding=16,
                                ),
                            ],
                            height=120,
                        ),
                    ]
                ),
            ),
        ),
    )


# ─── Display 展示 ────────────────────────────────────────────────


@ft.component
def DisplayPage():
    return page_shell(
        "Display 展示组件",
        "标题文本、引用、链接、代码、Markdown、JSON、图片与列表项",
        section(
            "标题文本 (Header_1 ~ Header_5)",
            "5 级标题层次",
            ft.Column(
                spacing=4,
                controls=[
                    Header_1("Header 1 标题"),
                    Header_2("Header 2 标题"),
                    Header_3("Header 3 标题"),
                    Header_4("Header 4 标题"),
                    Header_5("Header 5 标题"),
                ],
            ),
        ),
        section(
            "引用 (Quote)",
            "带背景色的引用文本",
            Quote("这是一段引用文本，用于强调或展示参考内容。"),
        ),
        section(
            "链接 (Link)",
            "点击在浏览器中打开链接",
            Link("访问 CS-UI GitHub 仓库", link="https://github.com/icstos/cs-ui"),
        ),
        section(
            "代码 (Code)",
            "只读代码编辑器，支持语法高亮",
            Code(
                value='def hello(name: str) -> str:\n    return f"Hello, {name}!"\n\nprint(hello("CS-UI"))',
                height=120,
            ),
        ),
        section(
            "Markdown",
            "GitHub 风格的 Markdown 渲染",
            Markdown(
                value=(
                    "# Markdown 标题\n\n"
                    "## 二级标题\n\n"
                    "支持 **加粗**、*斜体*、`行内代码`。\n\n"
                    "- 列表项一\n"
                    "- 列表项二\n"
                    "- 列表项三\n\n"
                    "[链接](https://github.com/icstos/cs-ui)\n"
                ),
            ),
        ),
        section(
            "JSON 展示 (Json)",
            "只读 JSON 代码视图",
            Json(
                value='{\n  "name": "cs-ui",\n  "version": "0.0.5",\n  "author": "Shawn Chen",\n  "dependencies": ["flet>=1.0.0", "flet-charts"]\n}',
                height=140,
            ),
        ),
        section(
            "图片 (Image)",
            "网络图片展示",
            Image(
                src="https://flet.dev/img/pages/home/flet-home.png",
                width=300,
                height=150,
                border_radius=8,
                fit=ft.BoxFit.COVER,
            ),
        ),
        section(
            "列表项 (ListTile)",
            "带头像、标题、副标题与尾部图标的列表项",
            Card(
                elevation=1,
                content=ft.Column(
                    spacing=0,
                    controls=[
                        ListTile(
                            leading=ft.Icon(ft.Icons.PERSON, color=C_PRIMARY),
                            title=ft.Text("用户管理"),
                            subtitle=ft.Text("管理系统用户和权限"),
                            trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT, color=C_MUTED),
                        ),
                        Divider(height=1),
                        ListTile(
                            leading=ft.Icon(ft.Icons.SETTINGS, color=C_PRIMARY),
                            title=ft.Text("系统设置"),
                            subtitle=ft.Text("配置系统参数和选项"),
                            trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT, color=C_MUTED),
                        ),
                        Divider(height=1),
                        ListTile(
                            leading=ft.Icon(ft.Icons.BACKUP, color=C_PRIMARY),
                            title=ft.Text("数据备份"),
                            subtitle=ft.Text("备份和恢复系统数据"),
                            trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT, color=C_MUTED),
                        ),
                    ],
                ),
            ),
        ),
    )


# ─── Navigation 导航 ──────────────────────────────────────────────


@ft.component
def NavigationPage():
    paging_state = PagingState(
        sum_data_nums=128,
        data_per_page_nums=10,
        on_change_page=lambda page: print(f"当前页码: {page}"),
        on_change_per_page_nums=lambda n: print(f"每页条数: {n}"),
    )

    return page_shell(
        "Navigation 导航组件",
        "应用栏与分页器",
        section(
            "应用栏 (AppBar)",
            "页面顶部导航栏，包含标题与操作按钮",
            ft.Container(
                border_radius=8,
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                content=AppBar(
                    title=ft.Text("CS-UI Demo"),
                    bgcolor=C_PRIMARY,
                    color=ft.Colors.WHITE,
                    actions=[
                        ft.IconButton(
                            icon=ft.Icons.SEARCH,
                            icon_color=ft.Colors.WHITE,
                            tooltip="搜索",
                        ),
                        ft.IconButton(
                            icon=ft.Icons.NOTIFICATIONS,
                            icon_color=ft.Colors.WHITE,
                            tooltip="通知",
                        ),
                        ft.IconButton(
                            icon=ft.Icons.ACCOUNT_CIRCLE,
                            icon_color=ft.Colors.WHITE,
                            tooltip="账户",
                        ),
                    ],
                ),
            ),
        ),
        section(
            "分页器 (Paging)",
            "首页/上一页/页码/下一页/尾页 + 跳转 + 每页条数选择",
            ft.Container(
                padding=ft.Padding.all(16),
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=8,
                content=Paging(paging_state),
            ),
        ),
    )


# ─── Chart 图表 ───────────────────────────────────────────────────


@ft.component
def ChartPage():
    return page_shell(
        "Chart 图表组件",
        "基于 flet_charts 封装的折线图，支持多种数据格式",
        section(
            "数值列表 → 自动生成 X 轴",
            "data=[1, 3, 2, 5, 4, 6, 8]",
            LineChart(data=[1, 3, 2, 5, 4, 6, 8], height=250, show_points=True),
        ),
        section(
            "多条折线 (列字典)",
            "data={'月份':[...], '销量A':[...], '销量B':[...]}",
            LineChart(
                data={
                    "月份": [1, 2, 3, 4, 5],
                    "销量A": [3, 5, 2, 7, 4],
                    "销量B": [4, 6, 3, 8, 5],
                },
                x="月份",
                y=["销量A", "销量B"],
                height=280,
                curved=True,
                show_points=True,
            ),
        ),
        section(
            "平滑曲线 + 大量数据",
            "50 个数据点，curved=True",
            LineChart(
                data=[
                    (i, 10 + 5 * math.sin(i * 0.3) + 3 * math.cos(i * 0.7))
                    for i in range(50)
                ],
                height=280,
                curved=True,
                color="#06b6d4",
            ),
        ),
        section(
            "无网格 + 粗线条",
            "show_grid=False, tooltip=False, stroke_width=3.0",
            LineChart(
                data=[(1, 2), (2, 5), (3, 3), (4, 8), (5, 6)],
                height=220,
                color="#ef4444",
                show_grid=False,
                tooltip=False,
                stroke_width=3.0,
            ),
        ),
    )


# ─── 入口 ─────────────────────────────────────────────────────────


if __name__ == "__main__":
    app = App(name="CS-UI 组件展示", with_auto_routing=False)
    app.add_route(
        [
            Route(index=True, component=HomePage),
            Route(path="buttons", component=ButtonsPage),
            Route(path="form", component=FormPage),
            Route(path="feedback", component=FeedbackPage),
            Route(path="layout", component=LayoutPage),
            Route(path="display", component=DisplayPage),
            Route(path="navigation", component=NavigationPage),
            Route(path="chart", component=ChartPage),
        ]
    )
    app.run()
