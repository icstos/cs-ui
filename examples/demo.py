import os
import sys
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import flet as ft
from cs_ui import (
    AlertDialog,
    AppBar,
    Badge,
    Button,
    Card,
    Checkbox,
    Chip,
    Column,
    Container,
    Divider,
    Dropdown,
    GridView,
    IconButton,
    Image,
    ListTile,
    Loading,
    ListView,
    ProgressBar,
    RadioGroup,
    Row,
    Slider,
    SnackBar,
    Switch,
    Tabs,
    Text,
    TextField,
    Tooltip,
)


# ─── 路由页面构建函数 ───────────────────────────────────────────────

def home_view(page):
    """首页 - 导航入口"""
    nav_items = [
        ("core", "Core", "核心工具", ft.Icons.BUILD),
        ("general", "General", "通用组件", ft.Icons.WIDGETS),
        ("layout", "Layout", "布局组件", ft.Icons.VIEW_QUILT),
        ("navigation", "Navigation", "导航组件", ft.Icons.NAVIGATE_NEXT),
        ("form", "Form", "表单组件", ft.Icons.EDIT_NOTE),
        ("feedback", "Feedback", "反馈组件", ft.Icons.FEEDBACK),
        ("data_display", "Data Display", "数据展示", ft.Icons.TABLE_CHART),
        ("about", "About", "关于", ft.Icons.INFO),
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
                        alignment="start",
                        spacing=12,
                        controls=[
                            ft.Icon(icon, size=32, color="#1f6feb"),
                            Column(
                                spacing=2,
                                controls=[
                                    Text(title, size=16, weight="bold"),
                                    Text(desc, size=13, color="#6b7280"),
                                ],
                            ),
                        ],
                    ),
                ),
            )
        )
    return ft.View(
        route="/",
        appbar=ft.AppBar(title=ft.Text("CS UI Demo"), bgcolor="#1f6feb", color="white"),
        controls=[
            Text("CS UI 组件库", size=28, weight="bold", color="#1f2937"),
            Text("基于 Flet 的 Python UI 组件库，点击卡片查看各分类组件效果", size=14, color="#6b7280"),
            Divider(),
            Column(
                expand=True,
                scroll=ft.ScrollMode.AUTO,
                spacing=8,
                controls=cards,
            ),
        ],
        padding=20,
        bgcolor="#f8fafc",
    )


def core_view(page):
    """Core - 核心工具"""
    return ft.View(
        route="/core",
        appbar=ft.AppBar(title=ft.Text("Core 核心工具"), bgcolor="#1f6feb", color="white"),
        controls=[
            Text("resolve_icon() 图标解析", size=20, weight="bold"),
            Text("将字符串图标名自动解析为 Flet 图标对象，支持 ft.Icons 枚举和字符串", size=13, color="#6b7280"),
            Divider(),
            Text("使用 ft.Icons 枚举：", size=14, weight="bold"),
            Row(
                spacing=16,
                controls=[
                    ft.Icon(ft.Icons.HOME, size=32, color="#1f6feb"),
                    ft.Icon(ft.Icons.SETTINGS, size=32, color="#f59e0b"),
                    ft.Icon(ft.Icons.FAVORITE, size=32, color="#ef4444"),
                    ft.Icon(ft.Icons.SEARCH, size=32, color="#10b981"),
                ],
            ),
            Divider(),
            Text("组件继承体系：", size=14, weight="bold"),
            Text("所有组件直接继承自 ft.Xxx 原生控件，通过 __init__ 自定义默认值和便捷参数", size=13, color="#6b7280"),
            Card(
                elevation=2,
                content=Container(
                    padding=16,
                    bgcolor="#1e293b",
                    border_radius=8,
                    content=ft.Text(
                        "class Button(ft.Button):\n"
                        "    def __init__(self, label='', bgcolor='#1f6feb', **kwargs):\n"
                        "        super().__init__(bgcolor=bgcolor, **kwargs)\n"
                        "        if label:\n"
                        "            self.content = ft.Text(label, color='white')",
                        color="#e2e8f0", size=13, font_family="Consolas",
                    ),
                ),
            ),
        ],
        padding=20,
        bgcolor="#f8fafc",
        scroll=ft.ScrollMode.AUTO,
    )


def general_view(page):
    """General - 通用组件"""
    return ft.View(
        route="/general",
        appbar=ft.AppBar(title=ft.Text("General 通用组件"), bgcolor="#1f6feb", color="white"),
        controls=[
            Text("Text 文本", size=20, weight="bold"),
            Row(
                spacing=16,
                controls=[
                    Text("默认文本", size=16),
                    Text("大号文本", size=24, weight="bold"),
                    Text("彩色文本", size=16, color="#ef4444"),
                    Text("斜体文本", size=16, italic=True),
                ],
            ),
            Divider(),

            Text("Button 按钮", size=20, weight="bold"),
            Row(
                spacing=12,
                controls=[
                    Button(label="主要按钮", on_click=lambda e: print("clicked")),
                    Button(label="禁用按钮", disabled=True),
                    Button(label="绿色按钮", bgcolor="#10b981"),
                    Button(label="红色按钮", bgcolor="#ef4444"),
                ],
            ),
            Divider(),

            Text("IconButton 图标按钮", size=20, weight="bold"),
            Row(
                spacing=12,
                controls=[
                    IconButton(icon=ft.Icons.FAVORITE, icon_color="#ef4444", tooltip="喜欢"),
                    IconButton(icon=ft.Icons.DELETE, icon_color="#6b7280", tooltip="删除"),
                    IconButton(icon=ft.Icons.ADD_CIRCLE, icon_color="#10b981", tooltip="添加"),
                ],
            ),
            Divider(),

            Text("Badge 徽标", size=20, weight="bold"),
            Row(
                spacing=16,
                controls=[
                    ft.FilledIconButton(icon=ft.Icons.MAIL, badge=Badge(badge_value=5)),
                    ft.FilledIconButton(icon=ft.Icons.NOTIFICATIONS, badge=Badge(badge_value=99, max_value=99)),
                    ft.FilledIconButton(icon=ft.Icons.SHOPPING_CART, badge=Badge(badge_value=0, badge_color="#10b981")),
                ],
            ),
            Divider(),

            Text("Chip 标签", size=20, weight="bold"),
            Row(
                spacing=8,
                controls=[
                    Chip(label_text="Python"),
                    Chip(label_text="Flet"),
                    Chip(label_text="UI 框架"),
                ],
            ),
            Divider(),

            Text("Divider 分割线", size=20, weight="bold"),
            Text("上方文本"),
            Divider(),
            Text("下方文本"),
            Divider(),

            Text("Tooltip 提示", size=20, weight="bold"),
            Tooltip(
                message="这是一个提示信息",
                content=Text("鼠标悬停查看提示", color="#1f6feb", size=14),
            ),
            Divider(),

            Text("Image 图片", size=20, weight="bold"),
            Image(
                src="https://picsum.photos/seed/csui/300/150",
                width=300,
                height=150,
                border_radius=8,
                fit=ft.ImageFit.COVER,
            ),
        ],
        padding=20,
        bgcolor="#f8fafc",
        scroll=ft.ScrollMode.AUTO,
    )


def layout_view(page):
    """Layout - 布局组件"""
    return ft.View(
        route="/layout",
        appbar=ft.AppBar(title=ft.Text("Layout 布局组件"), bgcolor="#1f6feb", color="white"),
        controls=[
            Text("Row 行布局", size=20, weight="bold"),
            Row(
                alignment="center",
                spacing=8,
                controls=[
                    Container(bgcolor="#ef4444", width=60, height=40, border_radius=4),
                    Container(bgcolor="#f59e0b", width=60, height=40, border_radius=4),
                    Container(bgcolor="#10b981", width=60, height=40, border_radius=4),
                    Container(bgcolor="#3b82f6", width=60, height=40, border_radius=4),
                ],
            ),
            Divider(),

            Text("Column 列布局", size=20, weight="bold"),
            Column(
                spacing=8,
                controls=[
                    Container(bgcolor="#ef4444", width=200, height=30, border_radius=4),
                    Container(bgcolor="#f59e0b", width=200, height=30, border_radius=4),
                    Container(bgcolor="#10b981", width=200, height=30, border_radius=4),
                ],
            ),
            Divider(),

            Text("Container 容器", size=20, weight="bold"),
            Row(
                spacing=12,
                controls=[
                    Container(
                        bgcolor="#dbeafe", padding=16, border_radius=8,
                        content=Text("蓝色容器", color="#1e40af"),
                    ),
                    Container(
                        bgcolor="#dcfce7", padding=16, border_radius=8,
                        content=Text("绿色容器", color="#166534"),
                    ),
                    Container(
                        bgcolor="#fef3c7", padding=16, border_radius=8,
                        content=Text("黄色容器", color="#92400e"),
                    ),
                ],
            ),
            Divider(),

            Text("Card 卡片", size=20, weight="bold"),
            Row(
                spacing=12,
                controls=[
                    Card(
                        elevation=2,
                        content=Container(
                            padding=16, border_radius=12,
                            content=Column(
                                spacing=4,
                                controls=[
                                    Text("卡片一", size=16, weight="bold"),
                                    Text("低阴影效果", size=13, color="#6b7280"),
                                ],
                            ),
                        ),
                    ),
                    Card(
                        elevation=8,
                        content=Container(
                            padding=16, border_radius=12,
                            content=Column(
                                spacing=4,
                                controls=[
                                    Text("卡片二", size=16, weight="bold"),
                                    Text("高阴影效果", size=13, color="#6b7280"),
                                ],
                            ),
                        ),
                    ),
                ],
            ),
            Divider(),

            Text("ListView 列表视图", size=20, weight="bold"),
            Container(
                height=200,
                border_radius=8,
                bgcolor="#ffffff",
                border=ft.border.all(1, "#e5e7eb"),
                content=ListView(
                    expand=True,
                    spacing=0,
                    controls=[
                        Container(
                            padding=12,
                            content=Text(f"列表项 {i + 1}", size=14),
                            bgcolor="#ffffff" if i % 2 == 0 else "#f9fafb",
                        )
                        for i in range(10)
                    ],
                ),
            ),
            Divider(),

            Text("GridView 网格视图", size=20, weight="bold"),
            Container(
                height=200,
                border_radius=8,
                bgcolor="#ffffff",
                border=ft.border.all(1, "#e5e7eb"),
                content=GridView(
                    expand=True,
                    runs_count=4,
                    spacing=8,
                    run_spacing=8,
                    controls=[
                        Container(
                            bgcolor="#dbeafe", border_radius=8, padding=12,
                            content=Text(f"网格 {i + 1}", size=13, color="#1e40af", text_align="center"),
                        )
                        for i in range(8)
                    ],
                ),
            ),
        ],
        padding=20,
        bgcolor="#f8fafc",
        scroll=ft.ScrollMode.AUTO,
    )


def navigation_view(page):
    """Navigation - 导航组件"""
    return ft.View(
        route="/navigation",
        appbar=ft.AppBar(title=ft.Text("Navigation 导航组件"), bgcolor="#1f6feb", color="white"),
        controls=[
            Text("AppBar 应用栏", size=20, weight="bold"),
            Text("当前页面顶部的 AppBar 即为示例", size=13, color="#6b7280"),
            Divider(),

            Text("Tabs 标签页", size=20, weight="bold"),
            Tabs(
                expand=True,
                animation_duration=300,
                selected_index=0,
                tabs=[
                    ft.Tab(
                        label="标签一",
                        content=Container(
                            padding=16,
                            content=Text("标签一的内容", size=14),
                        ),
                    ),
                    ft.Tab(
                        label="标签二",
                        content=Container(
                            padding=16,
                            content=Text("标签二的内容", size=14),
                        ),
                    ),
                    ft.Tab(
                        label="标签三",
                        content=Container(
                            padding=16,
                            content=Text("标签三的内容", size=14),
                        ),
                    ),
                ],
            ),
            Divider(),

            Text("NavigationBar 底部导航", size=20, weight="bold"),
            Text("NavigationBar 适合放在页面底部，此处展示静态效果", size=13, color="#6b7280"),
            Container(
                bgcolor="#ffffff",
                border_radius=12,
                border=ft.border.all(1, "#e5e7eb"),
                padding=8,
                content=NavigationBar(
                    selected_index=0,
                    destinations_config=[
                        (ft.Icons.HOME, "首页"),
                        (ft.Icons.SEARCH, "搜索"),
                        (ft.Icons.PERSON, "我的"),
                    ],
                ),
            ),
        ],
        padding=20,
        bgcolor="#f8fafc",
        scroll=ft.ScrollMode.AUTO,
    )


def form_view(page):
    """Form - 表单组件"""
    return ft.View(
        route="/form",
        appbar=ft.AppBar(title=ft.Text("Form 表单组件"), bgcolor="#1f6feb", color="white"),
        controls=[
            Text("TextField 文本输入", size=20, weight="bold"),
            TextField(label="用户名", hint_text="请输入用户名", width=320),
            TextField(label="密码", hint_text="请输入密码", password=True, can_reveal_password=True, width=320),
            Divider(),

            Text("Dropdown 下拉选择", size=20, weight="bold"),
            Dropdown(
                label="选择城市",
                options_list=["北京", "上海", "广州", "深圳"],
                width=320,
            ),
            Divider(),

            Text("Checkbox 复选框", size=20, weight="bold"),
            Column(
                spacing=4,
                controls=[
                    Checkbox(label="我已阅读并同意用户协议"),
                    Checkbox(label="订阅邮件通知", value=True),
                ],
            ),
            Divider(),

            Text("Switch 开关", size=20, weight="bold"),
            Column(
                spacing=4,
                controls=[
                    Switch(label="深色模式"),
                    Switch(label="自动保存", value=True),
                ],
            ),
            Divider(),

            Text("Slider 滑块", size=20, weight="bold"),
            Slider(min=0, max=100, divisions=10, label="{value}%", width=320),
            Divider(),

            Text("RadioGroup 单选组", size=20, weight="bold"),
            RadioGroup(
                label="选择性别",
                options=["男", "女", "其他"],
                value="男",
            ),
        ],
        padding=20,
        bgcolor="#f8fafc",
        scroll=ft.ScrollMode.AUTO,
    )


def feedback_view(page):
    """Feedback - 反馈组件"""
    dialog = AlertDialog(title_text="确认操作", content_text="你确定要执行此操作吗？")

    def show_snackbar(e):
        sb = SnackBar(message="操作成功！")
        page.overlay.append(sb)
        sb.open = True
        page.update()

    def show_dialog(e):
        dialog.actions = [
            ft.TextButton("取消", on_click=lambda e: close_dialog()),
            ft.TextButton("确认", on_click=lambda e: close_dialog()),
        ]
        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    def close_dialog():
        dialog.open = False
        page.update()

    return ft.View(
        route="/feedback",
        appbar=ft.AppBar(title=ft.Text("Feedback 反馈组件"), bgcolor="#1f6feb", color="white"),
        controls=[
            Text("ProgressBar 进度条", size=20, weight="bold"),
            Text("progress=30（百分比模式）", size=13, color="#6b7280"),
            ProgressBar(progress=30, width=400, color="#1f6feb"),
            Text("progress=0.7（小数模式）", size=13, color="#6b7280"),
            ProgressBar(progress=0.7, width=400, color="#10b981"),
            Text("progress=100（满进度）", size=13, color="#6b7280"),
            ProgressBar(progress=100, width=400, color="#f59e0b"),
            Divider(),

            Text("Loading 加载中", size=20, weight="bold"),
            Row(
                alignment="end",
                spacing=24,
                controls=[
                    Column(
                        spacing=4,
                        controls=[
                            Text("small", size=11, color="#6b7280"),
                            Loading(size_name="small"),
                        ],
                    ),
                    Column(
                        spacing=4,
                        controls=[
                            Text("normal", size=11, color="#6b7280"),
                            Loading(size_name="normal"),
                        ],
                    ),
                    Column(
                        spacing=4,
                        controls=[
                            Text("large", size=11, color="#6b7280"),
                            Loading(size_name="large"),
                        ],
                    ),
                ],
            ),
            Divider(),

            Text("SnackBar 消息提示", size=20, weight="bold"),
            Button(label="显示 SnackBar", on_click=show_snackbar),
            Divider(),

            Text("AlertDialog 对话框", size=20, weight="bold"),
            Button(label="显示 AlertDialog", on_click=show_dialog, bgcolor="#6366f1"),
        ],
        padding=20,
        bgcolor="#f8fafc",
        scroll=ft.ScrollMode.AUTO,
    )


def data_display_view(page):
    """Data Display - 数据展示"""
    return ft.View(
        route="/data_display",
        appbar=ft.AppBar(title=ft.Text("Data Display 数据展示"), bgcolor="#1f6feb", color="white"),
        controls=[
            Text("ListTile 列表项", size=20, weight="bold"),
            Card(
                elevation=1,
                content=Column(
                    spacing=0,
                    controls=[
                        ListTile(title_text="用户管理", subtitle_text="管理系统用户和权限"),
                        Divider(height=1),
                        ListTile(title_text="系统设置", subtitle_text="配置系统参数和选项"),
                        Divider(height=1),
                        ListTile(title_text="数据备份", subtitle_text="备份和恢复系统数据"),
                        Divider(height=1),
                        ListTile(title_text="操作日志", subtitle_text="查看系统操作记录"),
                    ],
                ),
            ),
        ],
        padding=20,
        bgcolor="#f8fafc",
        scroll=ft.ScrollMode.AUTO,
    )


def about_view(page):
    """About - 关于"""
    return ft.View(
        route="/about",
        appbar=ft.AppBar(title=ft.Text("About 关于"), bgcolor="#1f6feb", color="white"),
        controls=[
            Text("CS UI 组件库", size=28, weight="bold", color="#1f2937"),
            Text("基于 Flet 的 Python UI 组件库", size=16, color="#6b7280"),
            Divider(),
            Card(
                elevation=2,
                content=Container(
                    padding=20, border_radius=12,
                    content=Column(
                        spacing=8,
                        controls=[
                            Text("设计理念", size=18, weight="bold"),
                            Text("• 直接继承 Flet 原生控件，零学习成本", size=14),
                            Text("• 通过 __init__ 自定义默认值和便捷参数", size=14),
                            Text("• 组件按功能分类：general / layout / navigation / form / feedback / data_display", size=14),
                            Text("• 所有组件 100% 兼容 Flet 原生 API", size=14),
                        ],
                    ),
                ),
            ),
            Divider(),
            Text("组件统计", size=18, weight="bold"),
            Row(
                spacing=8,
                wrap=True,
                controls=[
                    Card(
                        elevation=1,
                        content=Container(
                            padding=16, border_radius=8,
                            content=Column(
                                spacing=2,
                                controls=[
                                    Text("8", size=24, weight="bold", color="#1f6feb"),
                                    Text("General", size=12, color="#6b7280"),
                                ],
                            ),
                        ),
                    ),
                    Card(
                        elevation=1,
                        content=Container(
                            padding=16, border_radius=8,
                            content=Column(
                                spacing=2,
                                controls=[
                                    Text("6", size=24, weight="bold", color="#10b981"),
                                    Text("Layout", size=12, color="#6b7280"),
                                ],
                            ),
                        ),
                    ),
                    Card(
                        elevation=1,
                        content=Container(
                            padding=16, border_radius=8,
                            content=Column(
                                spacing=2,
                                controls=[
                                    Text("3", size=24, weight="bold", color="#f59e0b"),
                                    Text("Navigation", size=12, color="#6b7280"),
                                ],
                            ),
                        ),
                    ),
                    Card(
                        elevation=1,
                        content=Container(
                            padding=16, border_radius=8,
                            content=Column(
                                spacing=2,
                                controls=[
                                    Text("6", size=24, weight="bold", color="#ef4444"),
                                    Text("Form", size=12, color="#6b7280"),
                                ],
                            ),
                        ),
                    ),
                    Card(
                        elevation=1,
                        content=Container(
                            padding=16, border_radius=8,
                            content=Column(
                                spacing=2,
                                controls=[
                                    Text("4", size=24, weight="bold", color="#8b5cf6"),
                                    Text("Feedback", size=12, color="#6b7280"),
                                ],
                            ),
                        ),
                    ),
                    Card(
                        elevation=1,
                        content=Container(
                            padding=16, border_radius=8,
                            content=Column(
                                spacing=2,
                                controls=[
                                    Text("1", size=24, weight="bold", color="#ec4899"),
                                    Text("Data Display", size=12, color="#6b7280"),
                                ],
                            ),
                        ),
                    ),
                ],
            ),
        ],
        padding=20,
        bgcolor="#f8fafc",
        scroll=ft.ScrollMode.AUTO,
    )


# ─── 路由表 ─────────────────────────────────────────────────────────

ROUTES = {
    "/": home_view,
    "/core": core_view,
    "/general": general_view,
    "/layout": layout_view,
    "/navigation": navigation_view,
    "/form": form_view,
    "/feedback": feedback_view,
    "/data_display": data_display_view,
    "/about": about_view,
}


# ─── 主程序 ─────────────────────────────────────────────────────────

def main(page: ft.Page):
    page.title = "CS UI Demo"
    page.bgcolor = "#f8fafc"

    def route_change(e):
        page.views.clear()
        route = page.route or "/"
        builder = ROUTES.get(route, home_view)
        page.views.append(builder(page))
        page.update()

    def view_pop(e):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    # 初始化路由
    page.route = "/"
    route_change(None)


if __name__ == "__main__":
    ft.run(main)
