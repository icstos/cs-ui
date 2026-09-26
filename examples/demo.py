"""CS UI 组件库示例 —— flet 1.0.0 声明式版本。

运行::

    python examples/demo.py

无头遍历所有路由做冒烟测试::

    python scripts/smoke_test.py examples.demo main --routes /,/general,/layout,/navigation,/form,/upload,/feedback,/display,/charts,/media,/about

与旧版 (flet 0.x) 的差异
------------------------
============================  ================================  ============================
旧版 (0.x)                    新版 (1.0.0)                       说明
============================  ================================  ============================
``ft.app(main)``              ``ft.run(main)``                   入口重命名
``page.add(...)``             ``page.render(component)``         根视图渲染
``page.go(route)``            ``page.navigate(route)``           导航 API
``page.views`` 手动维护        ``ft.Router(ROUTES)``              声明式路由
``page.overlay.append(...)``  ``page.overlay.append(...)``       不变（浮层的唯一可用通道）
``ft.View(appbar=AppBar())``  ``Container + Row`` 自绘顶栏        见下「两个坑」
命令式 class 组件              ``@ft.component`` + hooks          函数式组件 + 状态
``Tooltip(content=...)``      ``control.tooltip=Tooltip(...)``   Tooltip 变成装饰值
``Badge(badge_value=...)``    ``Badge(label=...)``               字段重命名
============================  ================================  ============================

两个必须知道的坑
----------------
1. **``page.render`` 与 ``page.render_views`` 不等价。** 后者走视图栈，
   会把**整个页面浮层盖住** —— ``page.overlay`` 里挂什么都是零像素，
   连 ``page.show_dialog`` 也一样，而且**不报错**。需要"悬挂面板"的组件
   （如 ``MultiSelect``）因此失效。本 demo 统一用 ``page.render`` +
   ``Router(manage_views=False)``。
2. **``ft.View`` 不能当普通控件用。** 在 ``manage_views=False``（router 不进
   视图栈）时把一个 ``View`` 塞进控件树，Flutter 侧会连续抛
   ``Bad state: No element``，整页渲染成灰块。所以本 demo 的页面统一返回
   ``Container``，顶栏由 :func:`top_bar` 自绘（``ft.AppBar`` 是
   ``AdaptiveControl``，只能挂在 ``View.appbar``，进不了 ``Column.controls``）。

组件库中的两类组件
------------------
1. **无状态控件**（``@ft.control`` 继承原生控件）：直接构造即可，如 ``Button``、
   ``Table``、``Expander``、``ImageGridView``。
2. **有状态组件**（``@ft.observable`` 数据对象 + ``@ft.component ui()``）：
   必须在 ``@ft.component`` 内部构造，并用 :func:`state` 固定实例，
   否则父组件每次重渲染都会重建对象、表单状态随之丢失。
"""

from __future__ import annotations

import asyncio
import datetime as dt
import math
import sys
from pathlib import Path

import flet as ft

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ui import (  # noqa: E402
    # ---- chart ----
    AreaChart,
    BarChart,
    LineChart,
    ScatterChart,
    # ---- core ----
    ButtonShape,
    LayoutType,
    StyleType,
    # ---- display ----
    Audio,
    AudioPlayer,
    Code,
    CodeEditor,
    CodeView,
    Header_1,
    Header_2,
    Header_3,
    Header_4,
    Header_5,
    Image,
    ImageGridView,
    Json,
    Link,
    ListTile,
    LogContainer,
    Markdown,
    Pdf,
    Quote,
    Text,
    Video,
    build_playlist,
    # ---- feedback ----
    AlertDialog,
    Loading,
    Message,
    ProgressBar,
    Toast,
    toast_error,
    toast_info,
    toast_success,
    toast_warning,
    # ---- input ----
    Button,
    Checkbox,
    CheckboxGroup,
    Chip,
    DateInput,
    DateTimeInput,
    DirPicker,
    FilePicker,
    FileSaver,
    ImagePicker,
    Input,
    MultiSelect,
    Radio,
    RangeSlider,
    Rating,
    SearchBar,
    SegmentedButton,
    SelectBox,
    Slider,
    Switch,
    # ---- layout ----
    Card,
    Column,
    Container,
    Divider,
    Expander,
    GridView,
    ListView,
    PageLayout,
    Row,
    Stack,
    Tab,
    TabBar,
    TabBarView,
    Table,
    Tabs,
    Timeline,
    TimelineItem,
    VerticalDivider,
    # ---- navigation ----
    BreadCrumb,
    Crumb,
    Paging,
    PagingState,
)

# ----------------------------------------------------------------------
# 常量与主题
# ----------------------------------------------------------------------

FONT_FILE = ROOT / "src" / "ui" / "data" / "fonts" / "AlibabaPuHuiTi-3-55-Regular.otf"
LOGO_FILE = ROOT / "src" / "ui" / "data" / "images" / "logo.png"

PAGE_BG = "#f6f8fb"
BORDER = "#e5e7eb"
MUTED = "#6b7280"
ACCENT = "#1f6feb"

SAMPLE_AUDIO = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
SAMPLE_VIDEO = "https://flutter.github.io/assets-for-api-docs/assets/videos/bee.mp4"
SAMPLE_VIDEO_2 = "https://flutter.github.io/assets-for-api-docs/assets/videos/butterfly.mp4"
SAMPLE_PDF = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"

# 图表演示数据（列字典格式）
MONTHS = ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月"]
SALES: dict[str, list] = {
    "月份": MONTHS,
    "线上": [120, 152, 141, 179, 210, 245, 268, 302],
    "线下": [86, 92, 105, 118, 124, 121, 138, 149],
}

# 首页导航目录: (路由, 标题, 描述, 图标)
NAV_ITEMS: list[tuple[str, str, str, ft.IconData]] = [
    ("general", "通用", "文本 / 按钮 / 图标 / 标签", ft.Icons.WIDGETS),
    ("layout", "布局", "容器 / 列表 / 表格 / 时间线", ft.Icons.DASHBOARD_CUSTOMIZE),
    ("navigation", "导航", "面包屑 / 标签页 / 分页", ft.Icons.EXPLORE),
    ("form", "表单", "输入框 / 选择器 / 滑块 / 评分", ft.Icons.EDIT_NOTE),
    ("upload", "文件", "文件 / 目录 / 保存 / 图片", ft.Icons.UPLOAD_FILE),
    ("feedback", "反馈", "Toast / 消息 / 对话框 / 进度", ft.Icons.FEEDBACK_OUTLINED),
    ("display", "展示", "日志 / 代码 / 列表项 / 图片网格", ft.Icons.TABLE_CHART),
    ("charts", "图表", "折线 / 面积 / 柱状 / 散点", ft.Icons.INSERT_CHART_OUTLINED),
    ("media", "媒体", "音频 / 视频 / PDF", ft.Icons.PLAY_CIRCLE_OUTLINE),
    ("about", "关于", "设计理念与 1.0.0 迁移说明", ft.Icons.INFO_OUTLINE),
]


# ----------------------------------------------------------------------
# 辅助函数（普通函数，不含 hooks）
# ----------------------------------------------------------------------


def state(factory):
    """取到「跨渲染稳定」的有状态组件实例。

    ``ui`` 中的表单类组件（``Input`` / ``Checkbox`` / ``SelectBox`` …）是
    ``@ft.observable`` 数据对象与 ``@ft.component ui()`` 的组合。它们必须在
    ``@ft.component`` 中构造，而父组件每次重渲染都会重新执行函数体，普通局部
    变量会被重建、状态随之丢失，因此用 ``ft.use_ref`` 把实例固定下来。
    """
    return ft.use_ref(factory).current


def section(
    title: str, hint: str | None = None, *controls: ft.Control
) -> ft.Control:
    """带标题与说明的演示分组。

    Args:
        title: 分组标题。
        hint: 标题下一行的灰色说明文字，可为 ``None``。
        *controls: 分组正文控件。

    注意：这里刻意做了类型校验。控件列表里混入裸字符串时，Flutter 侧不会抛
    Python 异常，只会把整块内容渲染成一个灰块 —— 极难排查，所以在构造期就拦住。
    """
    if hint is not None and not isinstance(hint, str):
        raise TypeError(
            f"section() 的 hint 必须是 str，收到 {type(hint).__name__}；"
            "如需省略说明文字请显式传 None。"
        )
    for item in controls:
        # 正文既可以是控件，也可以是 @ft.component / ui() 产出的 Component 节点
        if not isinstance(item, (ft.Control, ft.Component)):
            raise TypeError(
                f"section() 的正文只能是控件或 Component，收到 {type(item).__name__}；"
                "说明文字请放在 hint 参数。"
            )
    body: list[ft.Control] = [ft.Text(title, size=17, weight=ft.FontWeight.W_600)]
    if hint:
        body.append(ft.Text(hint, size=12, color=MUTED))
    body.extend(controls)
    return Column(controls=[Divider(color=BORDER, height=26), *body], spacing=10)


def panel(*controls: ft.Control, padding: int = 12, height: int | None = None) -> ft.Control:
    """白底描边面板，用于承载表格 / 列表等控件。"""
    return Container(
        bgcolor=ft.Colors.WHITE,
        border=ft.Border.all(1, BORDER),
        border_radius=8,
        padding=padding,
        height=height,
        content=Column(controls=list(controls), spacing=10),
    )


def swatch(color: str, width: int = 56, height: int = 36, radius: int = 6) -> ft.Control:
    """纯色块，用于布局演示。"""
    return Container(
        bgcolor=color,
        width=width,
        height=height,
        border_radius=radius,
        alignment=ft.Alignment.CENTER,
    )


def labeled(label: str, control: ft.Control) -> ft.Control:
    """给单个演示控件加一行灰色说明。"""
    return Column(
        spacing=3,
        controls=[ft.Text(label, size=12, color=MUTED), control],
    )


@ft.component
def ThemeToggle() -> ft.Control:
    """顶栏右侧的明暗主题切换。"""
    page = ft.context.page
    is_dark, set_dark = ft.use_state(page.theme_mode == ft.ThemeMode.DARK)

    def toggle(_):
        next_dark = not is_dark
        set_dark(next_dark)
        page.theme_mode = ft.ThemeMode.DARK if next_dark else ft.ThemeMode.LIGHT
        page.update()

    return ft.IconButton(
        icon=ft.Icons.DARK_MODE if not is_dark else ft.Icons.LIGHT_MODE,
        tooltip="切换明暗主题",
        on_click=toggle,
    )


def top_bar(
    title: str,
    *,
    leading: ft.Control | None = None,
    actions: list[ft.Control] | None = None,
) -> ft.Control:
    """自绘顶栏。

    为什么不用 ``ft.AppBar``：它是 ``AdaptiveControl``，只能挂在 ``ft.View``
    的 ``appbar`` 字段上，不能塞进 ``Column.controls``。而本项目用
    ``page.render`` 渲染根视图（原因见 :func:`main`），页面不再返回
    ``ft.View``，因此这里用 ``Container + Row`` 画一条等价的顶栏。
    """
    return Container(
        height=56,
        bgcolor=ft.Colors.WHITE,
        padding=ft.Padding.symmetric(horizontal=14),
        border=ft.Border(bottom=ft.BorderSide(1, BORDER)),
        content=Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                Row(
                    spacing=6,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        *([leading] if leading is not None else []),
                        ft.Text(title, size=17, weight=ft.FontWeight.W_600),
                    ],
                ),
                Row(
                    spacing=6,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[ThemeToggle(), *(actions or [])],
                ),
            ],
        ),
    )


def page_shell(
    title: str,
    hint: str,
    *controls: ft.Control,
    actions: list[ft.Control] | None = None,
) -> ft.Control:
    """统一页面骨架：顶栏 + 可滚动内容区。

    返回**普通控件**而不是 ``ft.View`` —— 根视图模式下 ``View`` 无法作为
    控件渲染。

    注意：``ft.context.page`` 在回调执行期未必可用，因此这里在渲染期就把它
    取出来闭包捕获，供「返回首页」按钮使用。
    """
    current_page = ft.context.page
    return Container(
        expand=True,
        bgcolor=PAGE_BG,
        content=Column(
            expand=True,
            spacing=0,
            controls=[
                top_bar(
                    title,
                    leading=ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        tooltip="返回首页",
                        on_click=lambda _: current_page.navigate("/"),
                    ),
                    actions=actions,
                ),
                Container(
                    expand=True,
                    padding=ft.Padding.symmetric(vertical=18, horizontal=22),
                    content=Column(
                        expand=True,
                        scroll=ft.ScrollMode.AUTO,
                        spacing=16,
                        controls=[
                            ft.Text(hint, size=12, color=MUTED),
                            *controls,
                        ],
                    ),
                ),
            ],
        ),
    )


# ----------------------------------------------------------------------
# 首页
# ----------------------------------------------------------------------


@ft.component
def HomePage() -> ft.Control:
    page = ft.context.page

    def nav_card(route: str, title: str, desc: str, icon: ft.IconData) -> ft.Control:
        return Card(
            elevation=1,
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            content=Container(
                padding=14,
                ink=True,
                on_click=lambda _, _r=route: page.navigate(f"/{_r}"),
                content=Row(
                    spacing=12,
                    controls=[
                        Container(
                            width=38,
                            height=38,
                            border_radius=8,
                            bgcolor="#e8f0fe",
                            alignment=ft.Alignment.CENTER,
                            content=ft.Icon(icon, size=20, color=ACCENT),
                        ),
                        Column(
                            expand=True,
                            spacing=2,
                            controls=[
                                ft.Text(title, size=15, weight=ft.FontWeight.W_600),
                                ft.Text(desc, size=12, color=MUTED),
                            ],
                        ),
                        ft.Icon(ft.Icons.CHEVRON_RIGHT, color="#c1c7d0", size=18),
                    ],
                ),
            ),
        )

    return Container(
        expand=True,
        bgcolor=PAGE_BG,
        content=Column(
            expand=True,
            spacing=0,
            controls=[
                top_bar("CS UI 组件库 Demo"),
                Container(
                    expand=True,
                    padding=ft.Padding.symmetric(vertical=18, horizontal=22),
                    content=Column(
                        expand=True,
                        scroll=ft.ScrollMode.AUTO,
                        spacing=14,
                        controls=[
                            ft.Text(
                                "基于 flet 1.0.0 的声明式组件库",
                                size=26,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Text(
                                "全部组件已适配 flet 1.0.0：@ft.component + hooks 函数式组件、"
                                "ft.Router 声明式路由、根视图渲染与页面浮层。",
                                size=13,
                                color=MUTED,
                            ),
                            Row(
                                spacing=10,
                                wrap=True,
                                controls=[
                                    _pill("flet >= 1.0.0", ACCENT, "#e8f0fe"),
                                    _pill("10 个分类 · 60+ 组件", "#10b981", "#e7f7ee"),
                                    _pill("点击卡片进入分类", "#f59e0b", "#fef4e3"),
                                ],
                            ),
                            Divider(color=BORDER, height=26),
                            ft.Text("组件分类", size=17, weight=ft.FontWeight.W_600),
                            GridView(
                                height=500,
                                runs_count=3,
                                spacing=12,
                                run_spacing=12,
                                child_aspect_ratio=3.1,
                                controls=[
                                    nav_card(route, title, desc, icon)
                                    for route, title, desc, icon in NAV_ITEMS
                                ],
                            ),
                        ],
                    ),
                ),
            ],
        ),
    )


def _pill(text: str, color: str, bgcolor: str) -> ft.Control:
    return Container(
        padding=ft.Padding.symmetric(vertical=6, horizontal=12),
        border_radius=20,
        bgcolor=bgcolor,
        content=ft.Text(text, size=12, color=color),
    )


# ----------------------------------------------------------------------
# 通用组件
# ----------------------------------------------------------------------


@ft.component
def GeneralPage() -> ft.Control:
    text_section = section(
        "文本 Text",
        "Header_1 ~ Header_5 对应 Material 的 5 级标题；Quote / Link 为常用变体。",
        Column(
            spacing=6,
            controls=[
                Header_1("Header_1"),
                Header_2("Header_2"),
                Header_3("Header_3"),
                Header_4("Header_4"),
                Header_5("Header_5"),
                Text("普通正文 Text", size=14),
                Quote("引用文本 Quote，默认带浅蓝底色", size=14),
                Link("Link 外链（点击用系统浏览器打开）", link="https://flet.dev"),
            ],
        ),
    )

    button_section = section(
        "按钮 Button",
        "StyleType 提供 6 种语义色；plain=True 为描边按钮；ButtonShape 控制形态。",
        Row(
            wrap=True,
            spacing=10,
            run_spacing=10,
            controls=[Button(i.name, style_type=i) for i in StyleType],
        ),
        Row(
            wrap=True,
            spacing=10,
            run_spacing=10,
            controls=[
                Button(f"plain {i.name}", style_type=i, plain=True) for i in StyleType
            ],
        ),
        Row(
            wrap=True,
            spacing=10,
            run_spacing=10,
            controls=[
                Button("圆角", shape=ButtonShape.ROUND, plain=True),
                Button("直角", shape=ButtonShape.RECTANGLE, plain=True),
                Button("胶囊", shape=ButtonShape.CIRCLE, plain=True),
                Button("主按钮", is_primary=True),
                Button("带图标", icon=ft.Icons.ADD),
                Button("禁用", disabled=True),
            ],
        ),
    )

    icon_section = section(
        "图标与徽标 Icon / Badge",
        "Badge 挂在按钮上显示角标；Tooltip 在 1.0.0 中作为控件的 tooltip 值使用。",
        Row(
            spacing=16,
            wrap=True,
            controls=[
                ft.IconButton(icon=ft.Icons.FAVORITE, icon_color="#ef4444", tooltip="喜欢"),
                ft.IconButton(icon=ft.Icons.DELETE, icon_color=MUTED, tooltip="删除"),
                ft.IconButton(icon=ft.Icons.ADD_CIRCLE, icon_color="#10b981", tooltip="新增"),
                ft.FilledIconButton(icon=ft.Icons.MAIL, badge=ft.Badge(label="5")),
                ft.FilledIconButton(
                    icon=ft.Icons.NOTIFICATIONS, badge=ft.Badge(label="99+")
                ),
                Container(
                    padding=ft.Padding.symmetric(vertical=8, horizontal=14),
                    border_radius=6,
                    bgcolor=ft.Colors.WHITE,
                    border=ft.Border.all(1, BORDER),
                    content=ft.Text("悬停查看富文本提示", size=13, color=ACCENT),
                    tooltip=ft.Tooltip(
                        message="这是 flet 1.0.0 的 Tooltip 写法",
                        bgcolor="#1f2937",
                        padding=8,
                        text_style=ft.TextStyle(color=ft.Colors.WHITE, size=12),
                    ),
                ),
            ],
        ),
    )

    chip_single = state(
        lambda: Chip(label="单选 Chip", options=["Python", "Flet", "Rust"])
    )
    chip_multi = state(
        lambda: Chip(
            label="多选 Chip",
            options=["前端", "后端", "算法", "设计"],
            multi_select=True,
            selected_values=["后端"],
        )
    )

    chip_section = section(
        "标签 Chip",
        "继承自 Label，支持单选 / 多选，自动带标签与布局方向。",
        chip_single.ui(),
        chip_multi.ui(),
    )

    image_section = section(
        "图片 Image 与分割线 Divider",
        "Image 可指定 fit / border_radius；Divider 支持 leading_indent 缩进。",
        Row(
            spacing=12,
            controls=[
                Image(
                    src=str(LOGO_FILE),
                    width=120,
                    height=90,
                    border_radius=8,
                    fit=ft.BoxFit.CONTAIN,
                ),
                Column(
                    expand=True,
                    spacing=4,
                    controls=[
                        ft.Text("上方内容", size=13),
                        Divider(color=BORDER),
                        ft.Text("下方内容", size=13),
                        Divider(color=BORDER, leading_indent=40),
                        ft.Text("带 leading_indent 的分割线", size=12, color=MUTED),
                    ],
                ),
            ],
        ),
    )

    markdown_section = section(
        "Markdown 与 Json",
        "Markdown 走 GitHub 扩展集；Json 基于 flet-code-editor，默认只读。",
        Markdown(
            "### Markdown 渲染\n"
            "\n"
            "- 支持 **粗体**、*斜体*、`行内代码`\n"
            "- 支持有序 / 无序列表\n"
            "- 支持 [链接](https://flet.dev) 与代码块\n"
            "\n"
            "```python\n"
            'print("hello, cs-ui")\n'
            "```\n"
        ),
        Json(value='{"name": "cs-ui", "version": "0.0.5", "flet": ">=1.0.0"}'),
    )

    return page_shell(
        "通用 General",
        "文本、按钮、图标、标签、图片等基础展示与交互元素。",
        text_section,
        button_section,
        icon_section,
        chip_section,
        image_section,
        markdown_section,
    )


# ----------------------------------------------------------------------
# 布局组件
# ----------------------------------------------------------------------


@ft.component
def LayoutPage() -> ft.Control:
    flex_section = section(
        "Row / Column / Container / Stack",
        "布局基元；Stack 用相对定位把红色角标压在头像右下角。",
        Row(
            spacing=8,
            controls=[
                swatch("#ef4444"),
                swatch("#f59e0b"),
                swatch("#10b981"),
                swatch("#3b82f6"),
                VerticalDivider(width=16, thickness=1, color=BORDER),
                Column(
                    spacing=8,
                    controls=[
                        swatch("#ef4444", 140, 28),
                        swatch("#f59e0b", 140, 28),
                        swatch("#10b981", 140, 28),
                    ],
                ),
                Container(
                    bgcolor="#e8f0fe",
                    padding=14,
                    border_radius=8,
                    content=ft.Text("Container：内边距 + 圆角 + 背景", size=13),
                ),
                Stack(
                    controls=[
                        Container(
                            width=72,
                            height=72,
                            border_radius=36,
                            bgcolor="#dbeafe",
                            alignment=ft.Alignment.CENTER,
                            content=ft.Icon(ft.Icons.PERSON, size=36, color=ACCENT),
                        ),
                        Container(
                            bgcolor="#ef4444",
                            border_radius=10,
                            padding=ft.Padding.symmetric(vertical=1, horizontal=6),
                            right=0,
                            bottom=4,
                            content=ft.Text("3", size=10, color=ft.Colors.WHITE),
                        ),
                    ],
                ),
            ],
        ),
    )

    list_section = section(
        "ListView / GridView",
        "两者都支持按需构建（build_controls_on_demand），适合长列表。",
        Row(
            spacing=12,
            controls=[
                Container(
                    height=190,
                    width=260,
                    border_radius=8,
                    bgcolor=ft.Colors.WHITE,
                    border=ft.Border.all(1, BORDER),
                    content=ListView(
                        expand=True,
                        divider_thickness=0.5,
                        controls=[
                            Container(
                                padding=ft.Padding.symmetric(vertical=9, horizontal=12),
                                content=ft.Text(f"列表项 {i + 1}", size=13),
                            )
                            for i in range(20)
                        ],
                    ),
                ),
                Container(
                    height=190,
                    expand=True,
                    border_radius=8,
                    bgcolor=ft.Colors.WHITE,
                    border=ft.Border.all(1, BORDER),
                    padding=8,
                    content=GridView(
                        expand=True,
                        runs_count=5,
                        spacing=8,
                        run_spacing=8,
                        child_aspect_ratio=1.6,
                        controls=[
                            Container(
                                bgcolor="#e8f0fe",
                                border_radius=6,
                                alignment=ft.Alignment.CENTER,
                                content=ft.Text(f"{i + 1}", size=13, color=ACCENT),
                            )
                            for i in range(15)
                        ],
                    ),
                ),
            ],
        ),
    )

    expander_section = section(
        "Expander 折叠面板",
        "继承 ExpansionTile，统一了圆角、标题背景与展开动画。",
        Expander(
            title="基础用法",
            subtitle="点击标题展开 / 折叠",
            controls=[
                ft.Text("这里是折叠面板的内容区。", size=13),
                Divider(color=BORDER),
                ft.Text("里面可以放任意控件。", size=12, color=MUTED),
            ],
        ),
        Expander(
            title="带前置图标",
            leading=ft.Icon(ft.Icons.FOLDER, color=ACCENT, size=18),
            controls=[ft.Text("支持 leading / trailing 自定义。", size=13)],
        ),
    )

    timeline_section = section(
        "Timeline 时间线",
        "垂直时间线：左侧轨道 + 右侧内容，done=True 自动使用对勾图标。",
        Timeline(
            items=[
                TimelineItem("提交申请", "09:12", "材料已上传完成", done=True),
                TimelineItem("部门审批", "10:30", "审核人：张工", done=True),
                TimelineItem("财务复核", "14:05", "等待财务确认", color="#f59e0b"),
                TimelineItem("归档", "", "完成后自动归档"),
            ],
        ),
    )

    table_control = state(lambda: Table(data_table=_build_data_table(), rows_per_page=8))

    table_section = section(
        "Table 数据表格",
        "封装 DataTable + 分页器，自动补「编号」列并给行加悬停色。",
        table_control,
    )

    skeleton_section = section(
        "PageLayout 页面骨架",
        "把「标题 + 副标题 + 操作区 + 内边距 + 滚动」收敛到一个容器里。",
        Container(
            height=260,
            border=ft.Border.all(1, BORDER),
            border_radius=10,
            content=PageLayout(
                title="用户管理",
                subtitle="管理系统用户、角色与权限",
                padding=16,
                actions=[Button("导出"), Button("新建用户", icon=ft.Icons.ADD)],
                controls=[
                    Row(
                        spacing=10,
                        controls=[
                            _stat("总用户", "1,286", ACCENT),
                            _stat("活跃", "942", "#10b981"),
                            _stat("待审", "37", "#f59e0b"),
                        ],
                    ),
                    ft.Text("页面内容区自动带滚动", size=12, color=MUTED),
                ],
            ),
        ),
    )

    return page_shell(
        "布局 Layout",
        "布局基元、列表网格、折叠面板、时间线、数据表格与页面骨架。",
        flex_section,
        list_section,
        expander_section,
        timeline_section,
        table_section,
        skeleton_section,
    )


def _stat(label: str, value: str, color: str) -> ft.Control:
    return Container(
        width=96,
        padding=10,
        border_radius=8,
        bgcolor=ft.Colors.WHITE,
        border=ft.Border.all(1, BORDER),
        content=Column(
            spacing=2,
            controls=[
                ft.Text(value, size=18, weight=ft.FontWeight.BOLD, color=color),
                ft.Text(label, size=11, color=MUTED),
            ],
        ),
    )


def _build_data_table() -> ft.DataTable:
    """构造一张演示用的 DataTable。"""
    import random

    rows = [
        ft.DataRow(
            cells=[
                ft.DataCell(ft.Text(f"用户 {i + 1:02d}")),
                ft.DataCell(ft.Text(f"user{i + 1:02d}@cstos.com")),
                ft.DataCell(ft.Text(str(random.randint(20, 60)))),
                ft.DataCell(
                    ft.Text(
                        "启用" if i % 3 else "停用",
                        color="#10b981" if i % 3 else "#ef4444",
                    )
                ),
            ]
        )
        for i in range(46)
    ]
    return ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("姓名")),
            ft.DataColumn(ft.Text("邮箱")),
            ft.DataColumn(ft.Text("年龄"), numeric=True),
            ft.DataColumn(ft.Text("状态")),
        ],
        rows=rows,
    )


# ----------------------------------------------------------------------
# 导航组件
# ----------------------------------------------------------------------


@ft.component
def NavigationPage() -> ft.Control:
    page = ft.context.page

    breadcrumb_section = section(
        "BreadCrumb 面包屑",
        "items 支持 str / (文本, 路由) / Crumb 三种写法；点击可跳转或走自定义回调。",
        BreadCrumb(
            items=[
                Crumb("首页", route="/"),
                Crumb("导航", route="/navigation"),
                Crumb("当前页面"),
            ],
        ),
        BreadCrumb(items=["带字符串", ("带路由", "/general"), "当前"], active_color=ACCENT),
    )

    tabs_section = section(
        "Tabs 标签页",
        "由 TabBar + TabBarView 组合，Tabs 负责联动切换。",
        Container(
            height=200,
            border_radius=8,
            bgcolor=ft.Colors.WHITE,
            border=ft.Border.all(1, BORDER),
            content=Tabs(
                length=3,
                content=Column(
                    controls=[
                        TabBar(
                            tabs=[
                                Tab(text="概览", icon=ft.Icons.DASHBOARD),
                                Tab(text="明细", icon=ft.Icons.LIST_ALT),
                                Tab(text="设置", icon=ft.Icons.SETTINGS),
                            ]
                        ),
                        TabBarView(
                            expand=True,
                            height=140,
                            controls=[
                                Container(
                                    padding=16, content=ft.Text("概览页内容", size=14)
                                ),
                                Container(
                                    padding=16, content=ft.Text("明细页内容", size=14)
                                ),
                                Container(
                                    padding=16, content=ft.Text("设置页内容", size=14)
                                ),
                            ],
                        ),
                    ]
                ),
            ),
        ),
    )

    navbar_section = section(
        "NavigationBar / NavigationRail",
        "移动端底部导航与桌面端侧边导航，这里做静态展示。",
        Row(
            spacing=16,
            controls=[
                Container(
                    width=360,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=10,
                    border=ft.Border.all(1, BORDER),
                    content=ft.NavigationBar(
                        selected_index=1,
                        destinations=[
                            ft.NavigationBarDestination(
                                icon=ft.Icons.HOME_OUTLINED, label="首页"
                            ),
                            ft.NavigationBarDestination(icon=ft.Icons.SEARCH, label="搜索"),
                            ft.NavigationBarDestination(
                                icon=ft.Icons.PERSON_OUTLINE, label="我的"
                            ),
                        ],
                    ),
                ),
                Container(
                    height=200,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=10,
                    border=ft.Border.all(1, BORDER),
                    content=ft.NavigationRail(
                        selected_index=0,
                        label_type=ft.NavigationRailLabelType.ALL,
                        destinations=[
                            ft.NavigationRailDestination(
                                icon=ft.Icons.DASHBOARD_OUTLINED, label="看板"
                            ),
                            ft.NavigationRailDestination(
                                icon=ft.Icons.ARTICLE_OUTLINED, label="文章"
                            ),
                            ft.NavigationRailDestination(
                                icon=ft.Icons.SETTINGS_OUTLINED, label="设置"
                            ),
                        ],
                    ),
                ),
            ],
        ),
    )

    paging_state = state(
        lambda: PagingState(
            sum_data_nums=137,
            data_per_page_nums=10,
            on_change_page=lambda p: print(f"[Paging] 当前页 = {p}"),
        )
    )

    paging_section = section(
        "Paging 分页器",
        "由 PagingState 状态对象驱动，页数多时自动折叠为省略号。",
        panel(Paging(paging_state)),
    )

    return page_shell(
        "导航 Navigation",
        "面包屑、标签页、底部 / 侧边导航与分页器。",
        breadcrumb_section,
        tabs_section,
        navbar_section,
        paging_section,
        section(
            "页面跳转",
            "page.navigate(path) 是 1.0.0 的导航入口，等价于 push_route。",
            Button(
                "跳转到「关于」页",
                is_primary=True,
                on_click=lambda _: page.navigate("/about"),
            ),
        ),
    )


# ----------------------------------------------------------------------
# 表单组件
# ----------------------------------------------------------------------


@ft.component
def FormPage() -> ft.Control:
    page = ft.context.page

    name = state(lambda: Input(label="姓名", value="Shawn", width=260))
    age = state(lambda: Input(label="年龄", value="30", data_type="int"))
    amount = state(lambda: Input(label="金额", value="199.9", data_type="float"))
    project_dir = state(
        lambda: Input(label="项目目录", value="", data_type="dir", width=300)
    )
    agree = state(lambda: Checkbox(label="我已阅读并同意用户协议", is_required=True))
    hobbies = state(
        lambda: CheckboxGroup(
            label="兴趣",
            options=["阅读", "跑步", "旅行", "音乐"],
            is_required=True,
        )
    )
    dark = state(lambda: Switch(label="深色模式"))
    notify = state(lambda: Switch(label="接收通知", value=True))
    gender = state(
        lambda: Radio(
            label="性别",
            options=["男", "女", "保密"],
            value="男",
            radio_layout_type=LayoutType.HORIZONTAL,
        )
    )
    city = state(
        lambda: SelectBox(
            label="城市",
            options=["北京", "上海", "广州", "深圳", "杭州"],
            value="杭州",
        )
    )
    tags = state(
        lambda: MultiSelect(
            label="标签",
            options=["前端", "后端", "数据", "设计", "运维", "测试", "算法", "产品"],
            value=["后端", "数据"],
        )
    )
    volume = state(
        lambda: Slider(
            label="音量",
            value=40,
            min=0,
            max=100,
            divisions=10,
            slider_label="{value}%",
        )
    )
    price_range = state(
        lambda: RangeSlider(
            label="价格区间",
            start_value=1500,
            end_value=6500,
            min=0,
            max=10000,
            divisions=20,
            slider_label="{value}",
        )
    )
    # Rating 是 @ft.control 控件（非 observable + ui() 那类），
    # 用 state() 固定实例即可直接放进控件树，避免父组件重渲染时丢选中态。
    pitch = state(lambda: Rating(value=4, elements=5))
    align_mode = state(
        lambda: SegmentedButton(
            options=["左对齐", "居中", "右对齐"],
            selected=["居中"],
            allow_multiple_selection=False,
            allow_empty_selection=False,
        )
    )
    birthday = state(lambda: DateInput(label="出生日期", value=dt.date(1996, 5, 20)))
    meeting = state(
        lambda: DateTimeInput(
            label="会议时间",
            value=dt.datetime(2026, 3, 18, 9, 30),
            with_seconds=False,
            minute_step=5,
        )
    )
    checkin = state(
        lambda: DateTimeInput(
            label="打卡时刻",
            value=dt.datetime(2026, 3, 18, 9, 30, 15),
            with_seconds=True,
            hour_step=1,
            second_step=5,
            clearable=False,
        )
    )
    search = state(
        lambda: SearchBar(
            options=["北京", "上海", "广州", "深圳", "杭州"],
            bar_hint_text="搜索城市…",
            view_hint_text="输入关键字",
            on_click=lambda e: print(f"[SearchBar] 选择 {e.control.data}"),
        )
    )

    def dump_values(_):
        # Rating 内部按 0 计数，对外展示统一 +1 还原为「几颗星」
        stars = pitch.value + 1 if isinstance(pitch.value, int) else 0
        message = (
            f"姓名={name.value} | 年龄={age.value} | 城市={city.value} | 标签={tags.value} "
            f"| 音量={volume.value} | 评分={stars} "
            f"| 生日={birthday.value} | 会议={meeting.value} | 打卡={checkin.value}"
        )
        toast_info(message, page=page)

    return page_shell(
        "表单 Form",
        "表单类组件遵循 observable 数据对象 + ui() 组件模式，实例用 ft.use_ref 固定，"
        "父组件重渲染不会丢状态。",
        section(
            "Input 输入框",
            "data_type 支持 str / int / float / file / dir，数值型自动带 +/- 步进按钮。",
            Column(spacing=10, controls=[name.ui(), age.ui(), amount.ui(), project_dir.ui()]),
        ),
        section(
            "Checkbox / CheckboxGroup",
            "CheckboxGroup 内置「全选」，支持水平 / 垂直布局。",
            Column(spacing=10, controls=[agree.ui(), hobbies.ui()]),
        ),
        section(
            "Switch 开关",
            "on_change 回调直接拿到布尔值，value 即当前开关状态。",
            Column(spacing=10, controls=[dark.ui(), notify.ui()]),
        ),
        section(
            "Radio 单选",
            "单选组，options 传字符串列表，选中值从 value 读取。",
            gender.ui(),
        ),
        section(
            "SelectBox / MultiSelect",
            "SelectBox 基于 DropdownM2；MultiSelect 是折叠式多选下拉框，"
            "面板挂在页面浮层上（不占布局高度、不推下方内容），点外部或「完成」收起。",
            Column(spacing=12, controls=[city.ui(), tags.ui()]),
        ),
        section(
            "Slider / RangeSlider",
            "min / max / divisions / slider_label 与原生一致，外层套了 Label 布局。",
            Column(spacing=12, controls=[volume.ui(), price_range.ui()]),
        ),
        section(
            "Rating 评分",
            "value 从 1 开始计数；readonly=True 时为只读展示。",
            Row(
                spacing=24,
                controls=[
                    labeled("可交互", pitch),
                    labeled("只读", Rating(value=3, readonly=True)),
                    labeled("禁用", Rating(value=2, disabled=True)),
                ],
            ),
        ),
        section(
            "SegmentedButton 分段按钮",
            "options 传字符串即可，内部自动包装成 Segment。",
            align_mode,
        ),
        section(
            "DateInput / DateTimeInput",
            "两者点框体都挂出悬浮面板（不占布局高度、不推下方内容），框内可直接键入 "
            "2026-09-26 / 20260926 / 2026年9月26日 / 09:30。DateInput 点标题可切年月"
            "网格快速跨年；DateTimeInput 面板是「月历 + 时/分/秒轮盘」并排，点日期不收起"
            "（可接着调时间），滚轮或 ▲▼ 步进，点「完成」收起。",
            Column(spacing=12, controls=[birthday.ui(), meeting.ui(), checkin.ui()]),
        ),
        section(
            "SearchBar 搜索栏",
            "options 直接生成候选列表，点击候选项触发 on_click。",
            panel(search),
        ),
        actions=[Button("读取所有值", is_primary=True, on_click=dump_values)],
    )


# ----------------------------------------------------------------------
# 文件选择
# ----------------------------------------------------------------------


@ft.component
def UploadPage() -> ft.Control:
    page = ft.context.page

    file_picker = state(lambda: FilePicker(allowed_extensions=["png", "jpg", "pdf"]))
    dir_picker = state(lambda: DirPicker())
    file_saver = state(lambda: FileSaver())
    image_picker = state(lambda: ImagePicker(label="头像", width=320))

    def read_values(_):
        toast_info(
            f"文件={file_picker.value} | 目录={dir_picker.value} "
            f"| 保存路径={file_saver.value} | 头像={image_picker.value}",
            page=page,
        )

    return page_shell(
        "文件 Upload",
        "文件类组件同样是 observable 数据对象，value 即最终选中的结果。",
        section(
            "FilePicker 文件选择",
            "allowed_extensions 限定后缀，allow_multiple 控制单选 / 多选。",
            file_picker.ui(),
        ),
        section(
            "DirPicker 目录选择",
            "选择目录后 value 为绝对路径，可直接喂给 Input(data_type='dir')。",
            dir_picker.ui(),
        ),
        section(
            "FileSaver 文件保存",
            "save_file(data) 弹出保存对话框并把内容写入所选路径。",
            file_saver.ui(),
        ),
        section(
            "ImagePicker 图片选择",
            "底层复用 Input 的 file 模式，选中后 value 为图片绝对路径。",
            image_picker.ui(),
        ),
        actions=[Button("读取所有值", is_primary=True, on_click=read_values)],
    )


# ----------------------------------------------------------------------
# 反馈组件
# ----------------------------------------------------------------------


@ft.component
def FeedbackPage() -> ft.Control:
    page = ft.context.page

    def make_toast(style_type: StyleType, text: str):
        def _show(_):
            # page 必须用关键字传：第一个位置参数是 content，
            # 写成 .show(page) 会让 content 指向页面本身并构成环形引用。
            Toast(content=text, style_type=style_type).show(page=page)

        return _show

    def show_message(_):
        Message(
            content="这是一条 Message（SnackBar），带关闭按钮，位于页面底部。",
            style_type=StyleType.INFO,
        ).show()

    def show_dialog(_):
        AlertDialog(
            title="删除确认",
            msg="删除后无法恢复，确定继续吗？",
            style_type=StyleType.WARNING,
            on_yes_click=lambda _: toast_success("已删除", page=page),
            on_no_click=lambda _: toast_info("已取消", page=page),
        ).show(page)

    # 用 hooks 管理进度值，演示「状态驱动 UI」的写法
    progress, set_progress = ft.use_state(0.35)

    def animate_progress(_):
        async def _pump():
            step = 0.02
            value = progress
            while value < 1.0:
                value = min(1.0, value + step)
                set_progress(value)
                await asyncio.sleep(0.02)

        page.run_task(_pump)

    return page_shell(
        "反馈 Feedback",
        "弹层统一走 page.show_dialog / page.pop_dialog；"
        "SnackBar 与 Toast 已包装成一行调用。",
        section(
            "Toast 轻提示",
            "浮动显示、自动消失，适合操作结果回执；toast_* 是快捷函数。",
            Row(
                wrap=True,
                spacing=10,
                run_spacing=10,
                controls=[
                    Button("默认", on_click=make_toast(StyleType.DEFAULT, "默认提示")),
                    Button("主要", on_click=make_toast(StyleType.PRIMARY, "主要提示")),
                    Button("信息", on_click=make_toast(StyleType.INFO, "已加载 12 条记录")),
                    Button("成功", on_click=make_toast(StyleType.SUCCESS, "保存成功")),
                    Button("警告", on_click=make_toast(StyleType.WARNING, "磁盘空间不足")),
                    Button("错误", on_click=make_toast(StyleType.ERROR, "请求失败")),
                ],
            ),
            Row(
                wrap=True,
                spacing=10,
                controls=[
                    Button("快捷：成功", on_click=lambda _: toast_success("快捷成功", page)),
                    Button("快捷：错误", on_click=lambda _: toast_error("快捷错误", page)),
                    Button("快捷：警告", on_click=lambda _: toast_warning("快捷警告", page)),
                    Button("快捷：信息", on_click=lambda _: toast_info("快捷信息", page)),
                ],
            ),
        ),
        section(
            "Message 消息条",
            "标准 SnackBar：位于底部并带关闭按钮，适合需要用户注意的通知。",
            Button("显示 Message", on_click=show_message),
        ),
        section(
            "AlertDialog 对话框",
            "title / msg / style_type 即可；分组按钮由 style_type 着色。",
            Row(
                wrap=True,
                spacing=10,
                run_spacing=10,
                controls=[
                    Button(
                        style.name,
                        on_click=lambda _, _s=style: AlertDialog(
                            title=f"{_s.name} 弹窗",
                            msg="这里是弹窗正文内容。",
                            style_type=_s,
                            on_yes_click=lambda _: None,
                            on_no_click=lambda _: None,
                        ).show(page),
                    )
                    for style in StyleType
                ],
            ),
            Button("带确认回调的弹窗", is_primary=True, on_click=show_dialog),
        ),
        section(
            "ProgressBar 进度条",
            "value 传 0~1 的浮点数；None 表示不确定进度。",
            ProgressBar(value=0.35, color=ACCENT),
            ProgressBar(value=0.72, color="#10b981"),
            ProgressBar(value=None, color="#f59e0b"),
        ),
        section(
            "Loading 加载环",
            "size_name 支持 small / normal / large。",
            Row(
                spacing=32,
                controls=[
                    Column(
                        spacing=4,
                        controls=[ft.Text("small", size=11, color=MUTED),
                                  Loading(size_name="small")],
                    ),
                    Column(
                        spacing=4,
                        controls=[ft.Text("normal", size=11, color=MUTED),
                                  Loading(size_name="normal")],
                    ),
                    Column(
                        spacing=4,
                        controls=[ft.Text("large", size=11, color=MUTED),
                                  Loading(size_name="large")],
                    ),
                ],
            ),
        ),
        section(
            "状态驱动 UI（hooks）",
            "ft.use_state + page.run_task：进度值变化自动触发组件重渲染。",
            ProgressBar(value=progress, color=ACCENT),
            ft.Text(f"当前进度：{progress * 100:.0f}%", size=12, color=MUTED),
            Button("模拟进度推进", on_click=animate_progress),
        ),
    )


# ----------------------------------------------------------------------
# 数据显示
# ----------------------------------------------------------------------


@ft.component
def DisplayPage() -> ft.Control:
    page = ft.context.page

    logs = state(
        lambda: LogContainer(
            logs=[
                "info: 应用启动完成",
                "success: 已连接数据库",
                "warning: 配置文件缺少 theme 字段",
                "error: 无法连接缓存服务，已降级",
            ],
            height=170,
        )
    )

    def push_logs(_):
        async def _run():
            await logs.add("info: 开始同步数据…")
            await asyncio.sleep(0.25)
            await logs.add("success: 同步完成，共 128 条")
            await asyncio.sleep(0.25)
            await logs.add("warning: 3 条记录被跳过")

        page.run_task(_run)

    gallery = state(
        lambda: ImageGridView(
            title="示例图库",
            img_file_paths=[str(LOGO_FILE) for _ in range(23)],
            num_item_per_page=6,
            img_size=120,
            grid_height=300,
        )
    )

    return page_shell(
        "展示 Display",
        "日志、代码、列表项与图片网格。",
        section(
            "ListTile 列表项",
            "可直接传字符串，也可传控件自定义 title / subtitle / leading / trailing。",
            panel(
                ListTile(
                    title="用户管理",
                    subtitle="管理系统用户与角色",
                    leading=ft.Icon(ft.Icons.PEOPLE_OUTLINE, color=ACCENT),
                    trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT),
                ),
                Divider(height=1, color="#eef0f4"),
                ListTile(
                    title="系统设置",
                    subtitle="配置系统参数",
                    leading=ft.Icon(ft.Icons.SETTINGS_OUTLINED, color="#10b981"),
                    trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT),
                ),
                Divider(height=1, color="#eef0f4"),
                ListTile(
                    title="操作日志",
                    subtitle="查看历史操作记录",
                    leading=ft.Icon(ft.Icons.HISTORY, color="#f59e0b"),
                    trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT),
                ),
            ),
        ),
        section(
            "LogContainer 日志容器",
            "按关键字自动着色：error 红 / warning 橙 / success 绿 / info 蓝。",
            logs.ui(),
            Row(
                spacing=10,
                controls=[
                    Button("追加日志", on_click=push_logs),
                    Button("清空", on_click=lambda _: logs.clear()),
                ],
            ),
        ),
        section(
            "CodeEditor / CodeView",
            "CodeEditor 可编辑（含 autocomplete / issues），CodeView 用于代码与效果并排。",
            CodeEditor(
                value="def add(a: int, b: int) -> int:\n    return a + b\n",
                language="python",
                height=130,
            ),
            CodeView(
                code='Button("点我", is_primary=True)',
                component=Button("点我", is_primary=True),
            ),
        ),
        section(
            "ImageGridView 图片网格",
            "内置分页与缩略图尺寸滑块；图片路径可以是本地文件或 URL。",
            gallery.ui(),
        ),
    )


# ----------------------------------------------------------------------
# 图表
# ----------------------------------------------------------------------


@ft.component
def ChartsPage() -> ft.Control:
    return page_shell(
        "图表 Charts",
        "四个图表统一基于 flet_charts 封装，参数参考 Streamlit 风格"
        "（data / x / y），自动配色与坐标轴。",
        section(
            "LineChart 折线图",
            "data 支持数值列表、字典列表、列字典、元组列表四种格式。",
            LineChart(data=SALES, x="月份", y=["线上", "线下"], height=280, show_points=True),
        ),
        section(
            "AreaChart 面积图",
            "opacity / gradient 控制填充，curved 控制平滑。",
            AreaChart(data=SALES, x="月份", y=["线上"], height=280, color="#10b981"),
        ),
        section(
            "BarChart 柱状图",
            "stacked=True 切换为堆叠模式，rod_width 控制柱宽。",
            BarChart(data=SALES, x="月份", y=["线上", "线下"], height=280),
            BarChart(data=SALES, x="月份", y=["线上", "线下"], stacked=True, height=280),
        ),
        section(
            "ScatterChart 散点图",
            "radius 控制点半径，适合展示相关性。",
            ScatterChart(
                data=[
                    (round(math.cos(i * 0.4) * 10 + 20, 2), round(math.sin(i * 0.7) * 8 + 15, 2))
                    for i in range(40)
                ],
                height=280,
                color="#8b5cf6",
            ),
        ),
    )


# ----------------------------------------------------------------------
# 媒体
# ----------------------------------------------------------------------


@ft.component
def MediaPage() -> ft.Control:
    # flet 1.0.0 起 Audio 是 ft.Service（不是 ft.Control）：放进控件树会被
    # Flutter 判为 "Unknown control: Audio"。Service 在构造时自动注册到
    # page 的服务注册表，所以这里用 state() 固定实例、只持有引用不挂进树。
    audio_service = state(lambda: Audio(src=SAMPLE_AUDIO))

    return page_shell(
        "媒体 Media",
        "基于 flet-audio / flet-video / flet-webview 的媒体组件（示例资源来自网络）。",
        section(
            "Audio / AudioPlayer",
            "Audio 是 page 级 Service（无视觉输出，构造时自动注册）；"
            "AudioPlayer 是卡片式播放器，内部持有一个 Audio 实例。",
            panel(
                Row(
                    spacing=8,
                    controls=[
                        ft.Icon(ft.Icons.GRAPHIC_EQ, size=16, color=ACCENT),
                        ft.Text(
                            "Audio 服务已注册到 page._services · src="
                            f"{audio_service.src}",
                            size=12,
                            color=MUTED,
                        ),
                    ],
                )
            ),
            AudioPlayer(src=SAMPLE_AUDIO, title="示例音轨", subtitle="SoundHelix Song 1"),
        ),
        section(
            "Video 视频播放器",
            "src 传单源，或 playlist=build_playlist([...]) 传播放列表；loop 控制循环。",
            Video(src=SAMPLE_VIDEO, title="bee.mp4", height=260),
            Video(
                playlist=build_playlist([SAMPLE_VIDEO, SAMPLE_VIDEO_2]),
                title="示例播放列表",
                height=260,
            ),
        ),
        section(
            "Pdf 阅读器",
            "内嵌 WebView 预览，支持本地路径与远程地址。",
            Pdf(src=SAMPLE_PDF, title="示例文档", height=420),
        ),
    )


# ----------------------------------------------------------------------
# 关于
# ----------------------------------------------------------------------


@ft.component
def AboutPage() -> ft.Control:
    stats = [
        ("通用", "10", ACCENT),
        ("布局", "12", "#10b981"),
        ("导航", "5", "#f59e0b"),
        ("表单", "21", "#ef4444"),
        ("反馈", "5", "#8b5cf6"),
        ("展示", "22", "#ec4899"),
    ]

    return page_shell(
        "关于 About",
        "cs-ui · 基于 flet 1.0.0 的 Python UI 组件库。",
        section(
            "设计理念",
            "四条取舍原则：双范式、零学习成本、语义统一、共享内核。",
            Column(
                spacing=6,
                controls=[
                    ft.Text("• 双范式：无状态组件继承原生控件，有状态组件用 observable + ui()", size=13),
                    ft.Text("• 零学习成本：所有组件都是 flet 控件的子类，原生参数照常可用", size=13),
                    ft.Text("• 语义统一：StyleType 一处定义，按钮 / 弹窗 / 提示共用同一套配色", size=13),
                    ft.Text("• 共享内核：图表配色抽到 chart/_data.py，输入框边框抽到 core/styles.py", size=13),
                ],
            ),
        ),
        section(
            "组件统计（按分类）",
            "按 src/ui 下的子包统计，未计入 demo 自身的辅助函数。",
            Row(
                spacing=10,
                wrap=True,
                run_spacing=10,
                controls=[_stat(label, value, color) for label, value, color in stats],
            ),
        ),
        section(
            "flet 1.0.0 迁移速查",
            "本次适配中改动最密集的一批 API 对照。两个坑：page.render_views 会"
            "屏蔽页面浮层（overlay / show_dialog 都零渲染且不报错）；ft.View "
            "在根视图模式下不能当普通控件用（整页灰块）。",
            Markdown(
                "| 旧 API (0.x) | 新 API (1.0.0) |\n"
                "| --- | --- |\n"
                "| `ft.app(main)` | `ft.run(main)` |\n"
                "| `page.add(...)` | `page.render(Component)` |\n"
                "| `page.views.append(...)` | `ft.Router(ROUTES, manage_views=False)` + `page.render` |\n"
                "| `page.go(route)` | `page.navigate(route)` |\n"
                "| `page.overlay.append(dlg); dlg.open = True` | `page.show_dialog(dlg)` |\n"
                "| `ft.View(appbar=ft.AppBar(…))` | `Container` + 自绘顶栏（`View` 不再是控件） |\n"
                "| `TextField(border_radius=…, border_color=…)` | `TextField(border=ft.OutlineInputBorder(...))` |\n"
                "| `Tooltip(content=…)` | `control.tooltip = ft.Tooltip(message=…)` |\n"
                "| `Badge(badge_value=…)` | `Badge(label=…)` |\n"
            ),
        ),
        section(
            "运行示例",
            "两条命令即可跑起来：直接运行，或遍历全部路由做无头冒烟测试。",
            Code(
                value=(
                    "# 直接运行 demo\n"
                    "python examples/demo.py\n"
                    "\n"
                    "# 无头渲染冒烟测试（遍历所有路由）\n"
                    "python scripts/smoke_test.py examples.demo main "
                    "--routes /,/general,/layout,/navigation,/form,/upload,"
                    "/feedback,/display,/charts,/media,/about\n"
                ),
                language="bash",
                height=170,
            ),
        ),
    )


# ----------------------------------------------------------------------
# 404
# ----------------------------------------------------------------------


@ft.component
def NotFoundPage() -> ft.Control:
    """404 页面内容。

    注意：``not_found`` 必须返回**控件**而不是 ``ft.View`` —— 根视图模式下
    ``View`` 不能作为控件渲染（整页灰块）。顶栏因此由 :func:`top_bar` 自绘。
    """
    page = ft.context.page
    return Container(
        expand=True,
        bgcolor=PAGE_BG,
        content=Column(
            expand=True,
            spacing=0,
            controls=[
                top_bar("页面不存在"),
                Container(
                    expand=True,
                    alignment=ft.Alignment.CENTER,
                    content=Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=12,
                        controls=[
                            ft.Text(
                                "404", size=72, weight=ft.FontWeight.BOLD, color="#cbd5e1"
                            ),
                            ft.Text("当前路由未定义", size=14, color=MUTED),
                            Button(
                                "回到首页",
                                is_primary=True,
                                on_click=lambda _: page.navigate("/"),
                            ),
                        ],
                    ),
                ),
            ],
        ),
    )


# ----------------------------------------------------------------------
# 应用根组件
# ----------------------------------------------------------------------

ROUTES: list[ft.Route] = [
    ft.Route(index=True, component=HomePage),
    ft.Route(path="general", component=GeneralPage),
    ft.Route(path="layout", component=LayoutPage),
    ft.Route(path="navigation", component=NavigationPage),
    ft.Route(path="form", component=FormPage),
    ft.Route(path="upload", component=UploadPage),
    ft.Route(path="feedback", component=FeedbackPage),
    ft.Route(path="display", component=DisplayPage),
    ft.Route(path="charts", component=ChartsPage),
    ft.Route(path="media", component=MediaPage),
    ft.Route(path="about", component=AboutPage),
]


@ft.component
def App() -> ft.Control:
    """应用根组件：配置主题 + 声明式路由。"""
    _configure_page(ft.context.page)
    return ft.Router(ROUTES, not_found=NotFoundPage, manage_views=False)


def _configure_page(page: ft.Page) -> None:
    """统一页面级主题（字体 / 配色 / 过渡动画）。"""
    has_font = FONT_FILE.exists()
    if has_font:
        page.fonts = {"AlibabaPuHuiTi": str(FONT_FILE)}
    page.theme_mode = page.theme_mode or ft.ThemeMode.LIGHT
    page.theme = ft.Theme(
        color_scheme_seed=ACCENT,
        font_family="AlibabaPuHuiTi" if has_font else None,
        use_material3=True,
        page_transitions=ft.PageTransitionsTheme(
            android=ft.PageTransitionTheme.NONE,
            ios=ft.PageTransitionTheme.NONE,
            macos=ft.PageTransitionTheme.NONE,
            windows=ft.PageTransitionTheme.NONE,
            linux=ft.PageTransitionTheme.NONE,
        ),
    )


def main(page: ft.Page) -> None:
    """flet 1.0.0 入口：把 Router 渲染进根视图。

    用 ``page.render`` 而非 ``page.render_views``。后者会生成视图栈，
    把**整个页面浮层盖住**（``page.overlay`` 与 ``page.show_dialog``
    都不渲染，且不报错），MultiSelect 这类需要悬挂面板的组件就失效了。
    这里用 ``Router(manage_views=False)`` + ``page.render``，路由能力不变。
    """
    page.title = "CS UI Demo"
    page.window.width = 1180
    page.window.height = 840
    page.window.min_width = 900
    page.window.min_height = 640
    page.render(App)


if __name__ == "__main__":
    ft.run(main)
