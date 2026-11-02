"""CS UI 组件库示例 —— flet 1.0.0 声明式 + 三语实时切换。

运行::

    python examples/demo.py

无头遍历所有路由做冒烟测试::

    python scripts/smoke_test.py examples.demo main --routes /,/general,/layout,/navigation,/form,/upload,/feedback,/display,/charts,/media,/about

多语言怎么做的
------------
1. **文案外置**：``examples/i18n/{zh_CN,zh_TW,en_US}.json`` 三份对照表，
   启动时 :func:`ui.load_catalogs` 一次装完；脚手架代码里不再出现任何界面文字。
2. **订阅点只有一处**：每个页面组件体开头 ``tr = use_t()``。切语言时
   只有订阅过的组件重绘，``Router`` 不重建、页面滚动位置不变。
3. **组件内置文案免费**：分页器、月历、选择器页脚这些由组件库自己画的文字
   早已走语言包（``ui.core.locales``），这里不用传任何参数。
4. **格式也跟着走**：``use_t()`` 之外，日期与数字用 :mod:`ui.core.format`
   —— 英文界面里日期是 ``09/26/2026``、日历首日是周日、千分位照常。
5. **表单状态不丢**：见 :func:`state` —— 语言变化时重建组件（否则标签会停在
   旧语言），只把用户已经填好的值搬过去。

两个必须知道的坑（照抄本文件时最容易踩）
--------------------------------------
1. **``page.render`` 与 ``page.render_views`` 不等价。** 后者走视图栈，
   会把**整个页面浮层盖住** —— ``page.overlay`` 里挂什么都是零像素，
   连 ``page.show_dialog`` 也一样，而且**不报错**。需要"悬挂面板"的组件
   （如 ``MultiSelect``）因此失效。本 demo 统一用 ``page.render`` +
   ``Router(manage_views=False)``。
2. **``ft.View`` 不能当普通控件用。** 在 ``manage_views=False`` 时把一个
   ``View`` 塞进控件树，Flutter 侧会连续抛 ``Bad state: No element``，
   整页渲染成灰块。所以页面统一返回 ``Container``，顶栏由 :func:`top_bar` 自绘。

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
EXAMPLES = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ui import (  # noqa: E402
    # ---- chart ----
    AreaChart,
    BarChart,
    LineChart,
    ScatterChart,
    # ---- core ----
    PRIMARY_SEEDS,
    ButtonShape,
    I18nProvider,
    LanguageSwitcher,
    LayoutType,
    StyleType,
    ThemeProvider,
    __version__ as UI_VERSION,
    format_number,
    load_catalogs,
    semantic,
    semantic_text,
    theme_state,
    use_i18n,
    use_t,
    use_theme,
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
    ColorPicker,
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
# 静态资源与语言包
# ----------------------------------------------------------------------

FONT_FILE = ROOT / "src" / "ui" / "data" / "fonts" / "AlibabaPuHuiTi-3-55-Regular.otf"
LOGO_FILE = ROOT / "src" / "ui" / "data" / "images" / "logo.png"
I18N_DIR = EXAMPLES / "i18n"

#: 装表在**导入期**完成：首帧渲染前语言就是对的，不会先闪一下默认语言。
#: 装到框架自己的注册表里，所以 apply 的文案与框架文案共用一套回退链。
load_catalogs(I18N_DIR)

# 页面骨架的配色一律走 Material 3 角色（由 Flutter 按当前主题解析），
# 不写死具体色值 —— 写死的话明暗主题下必然有一半读不清。
PAGE_BG = ft.Colors.SURFACE_CONTAINER_LOWEST
BORDER = ft.Colors.OUTLINE_VARIANT
MUTED = ft.Colors.ON_SURFACE_VARIANT
ACCENT = PRIMARY_SEEDS["blue"]

SAMPLE_AUDIO = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
SAMPLE_VIDEO = "https://flutter.github.io/assets-for-api-docs/assets/videos/bee.mp4"
SAMPLE_VIDEO_2 = "https://flutter.github.io/assets-for-api-docs/assets/videos/butterfly.mp4"
SAMPLE_PDF = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"

#: 首页导航目录：**只写路由与图标**，标题与描述全部来自语言包 ``nav.<route>.*``。
#: 加一个分类 = 加一行（再补三份文案），不用改任何布局代码。
NAV: list[tuple[str, ft.IconData]] = [
    ("general", ft.Icons.WIDGETS),
    ("layout", ft.Icons.DASHBOARD_CUSTOMIZE),
    ("navigation", ft.Icons.EXPLORE),
    ("form", ft.Icons.EDIT_NOTE),
    ("upload", ft.Icons.UPLOAD_FILE),
    ("feedback", ft.Icons.FEEDBACK_OUTLINED),
    ("display", ft.Icons.TABLE_CHART),
    ("charts", ft.Icons.INSERT_CHART_OUTLINED),
    ("media", ft.Icons.PLAY_CIRCLE_OUTLINE),
    ("about", ft.Icons.INFO_OUTLINE),
]

#: 组件统计（按分类），首页 / 关于页共用。
STATS: list[tuple[str, str, str]] = [
    ("general", "10", ACCENT),
    ("layout", "12", "#10b981"),
    ("navigation", "5", "#f59e0b"),
    ("form", "21", "#ef4444"),
    ("feedback", "5", "#8b5cf6"),
    ("display", "22", "#ec4899"),
]

#: 语言变化时需要从旧实例搬到新实例的字段（见 :func:`state`）。
_CARRIED_FIELDS = ("value", "start_value", "end_value", "selected")


# ----------------------------------------------------------------------
# 辅助函数（普通函数，不含 hooks）
# ----------------------------------------------------------------------


def state(factory):
    """取到「跨渲染稳定」的有状态组件实例，并在语言切换时安全重建。

    为什么不能只用 ``ft.use_ref(factory)``：``ui`` 里的表单组件是
    ``@ft.observable`` 数据对象，**文案是构造参数**（``label`` / ``placeholder``
    / ``options``）。实例一旦被 ref 钉住，切语言后标签、候选列表仍停在旧语言 ——
    "界面翻译了，输入框还写着中文"是这类 demo 最常见的破绽。

    所以这里做两件事：
    1. 语言变化时用新文案重建实例；
    2. 把用户已经填好的值搬过去，写入走 ``object.__setattr__`` **绕过 observable
       通知** —— 渲染期给 observable 赋值会立刻触发新一轮渲染，形成回环。

    Args:
        factory: 无参工厂，返回组件实例（``Input(...)`` / ``Rating(...)`` …）。
    """
    locale = use_i18n().locale
    box = ft.use_ref(None)
    stamp = ft.use_ref(None)

    if box.current is None or stamp.current != locale:
        previous = box.current
        box.current = factory()
        stamp.current = locale
        if previous is not None:
            for field in _CARRIED_FIELDS:
                if hasattr(previous, field) and hasattr(box.current, field):
                    object.__setattr__(box.current, field, getattr(previous, field))
    return box.current


def section(
    title: str,
    hint: str | None = None,
    *controls: ft.Control,
    stretch: bool = False,
) -> ft.Control:
    """带标题与说明的演示分组。

    Args:
        title: 分组标题。
        hint: 标题下一行的灰色说明文字，可为 ``None``。
        *controls: 分组正文控件。
        stretch: 让正文横向撑满。**只有需要横向约束的控件才开**
            （``Timeline`` 是 Column，交叉轴不拉伸时内容列会被压成 0 宽）。

    注意：这里刻意做了类型校验。控件列表里混入裸字符串时，Flutter 侧不会抛
    Python 异常，只会把整块内容渲染成一个灰块 —— 极难排查，所以在构造期就拦住。
    """
    if hint is not None and not isinstance(hint, str):
        raise TypeError(
            f"section() 的 hint 必须是 str，收到 {type(hint).__name__}；"
            "如需省略说明文字请显式传 None。"
        )
    for item in controls:
        if not isinstance(item, (ft.Control, ft.Component)):
            raise TypeError(
                f"section() 的正文只能是控件或 Component，收到 {type(item).__name__}；"
                "说明文字请放在 hint 参数。"
            )
    body: list[ft.Control] = [ft.Text(title, size=17, weight=ft.FontWeight.W_600)]
    if hint:
        body.append(ft.Text(hint, size=12, color=MUTED))
    body.extend(controls)
    return Column(
        controls=[Divider(color=BORDER, height=26), *body],
        spacing=10,
        horizontal_alignment=(
            ft.CrossAxisAlignment.STRETCH
            if stretch
            else ft.CrossAxisAlignment.START
        ),
    )


def panel(*controls: ft.Control, padding: int = 12, height: int | None = None) -> ft.Control:
    """描边面板，用于承载表格 / 列表等控件。"""
    return Container(
        bgcolor=ft.Colors.SURFACE,
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
def _pill(text: str, role: str = "primary") -> ft.Control:
    """状态胶囊。

    **刻意做成组件**而不是普通函数：它的颜色是 Python 侧算出来的
    （M3 没有 success / warning 这些角色），必须由 :func:`use_theme` 订阅、
    在主题变化时重绘。写成普通函数的话，颜色会在父组件渲染那一刻被定死。
    """
    use_theme()
    if role == "primary":
        bgcolor, fg = ft.Colors.PRIMARY_CONTAINER, ft.Colors.ON_PRIMARY_CONTAINER
    else:
        # 底色是该语义色的淡染，与文字同源 —— 否则"绿字压蓝底"这类错配很容易发生
        bgcolor = ft.Colors.with_opacity(0.16, semantic(role))
        fg = semantic_text(role)
    return Container(
        padding=ft.Padding.symmetric(vertical=6, horizontal=12),
        border_radius=20,
        bgcolor=bgcolor,
        content=ft.Text(text, size=12, color=fg),
    )


# ----------------------------------------------------------------------
# 顶栏
# ----------------------------------------------------------------------


@ft.component
def ThemeToggle() -> ft.Control:
    """顶栏右侧的明暗切换。

    用 :func:`use_theme` **订阅**全局主题：读一次 ``mode`` / ``primary``
    就登记了依赖，主题一变本组件自动重绘，不需要手动 ``page.update()``
    （声明式下那既多余又危险 —— 控件树是 frozen 的）。
    """
    th = use_theme()
    tr = use_t()
    next_mode = tr("common.theme.dark") if th.mode_name == "light" else tr("common.theme.light")
    current = (
        tr("common.theme.system")
        if th.mode == "system"
        else tr(f"common.theme.{th.mode}")
    )
    return ft.IconButton(
        icon=ft.Icons.DARK_MODE if th.mode_name == "light" else ft.Icons.LIGHT_MODE,
        tooltip=tr("common.theme.toggle", next=next_mode, mode=current),
        on_click=lambda _: th.toggle_mode(),
    )


@ft.component
def PrimaryPicker() -> ft.Control:
    """顶栏右侧的主色切换：一排色块，点一下就换整套 Material 3 色板。

    只改一个字符串（``color_scheme_seed``），Flutter 负责推导出全部角色色 ——
    这就是"全局换色"不需要维护调色板表的原因。
    """
    th = use_theme()
    tr = use_t()

    return ft.Container(
        height=32,
        padding=ft.Padding.symmetric(horizontal=6),
        border_radius=ft.BorderRadius.all(6),
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
        content=ft.Row(
            spacing=4,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=18,
                    height=18,
                    tooltip=tr("common.theme.primary", name=name),
                    border_radius=ft.BorderRadius.all(4),
                    bgcolor=hex_value,
                    border=ft.Border.all(
                        2,
                        (
                            ft.Colors.ON_SURFACE
                            if th.primary.lower() == hex_value.lower()
                            else ft.Colors.TRANSPARENT
                        ),
                    ),
                    on_click=lambda _e, v=hex_value: th.set_primary(v),
                )
                for name, hex_value in PRIMARY_SEEDS.items()
            ],
        ),
    )


def top_bar(
    title: str,
    *,
    leading: ft.Control | None = None,
    actions: list[ft.Control] | None = None,
) -> ft.Control:
    """自绘顶栏：``[←] 标题 … [页面操作] | [语言] [主色] [明暗]``。

    为什么不用 ``ft.AppBar``：它是 ``AdaptiveControl``，只能挂在 ``ft.View``
    的 ``appbar`` 字段上，不能塞进 ``Column.controls``。而本项目用
    ``page.render`` 渲染根视图，页面不再返回 ``ft.View``，因此这里用
    ``Container + Row`` 画一条等价的顶栏。

    控件分组遵循桌面软件的直觉：**页面自己的操作靠左，全局设置靠右**，
    中间用 1px 竖线分开 —— 用户不会把"读取所有值"和"换主题"混成一类。
    """
    trailing: list[ft.Control] = list(actions or [])
    if trailing:
        trailing.append(VerticalDivider(width=9, thickness=1, color=BORDER))
    trailing += [LanguageSwitcher(), PrimaryPicker(), ThemeToggle()]

    return Container(
        height=56,
        bgcolor=ft.Colors.SURFACE_CONTAINER,
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
                    controls=trailing,
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
    控件渲染。注意 ``ft.context.page`` 在回调执行期未必可用，所以在渲染期
    就把它取出来闭包捕获，供「返回首页」使用。
    """
    tr = use_t()
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
                        tooltip=tr("common.back"),
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
    tr = use_t()
    page = ft.context.page

    def nav_card(route: str, icon: ft.IconData) -> ft.Control:
        return Card(
            elevation=1,
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
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
                            bgcolor=ft.Colors.PRIMARY_CONTAINER,
                            alignment=ft.Alignment.CENTER,
                            content=ft.Icon(
                                icon, size=20, color=ft.Colors.ON_PRIMARY_CONTAINER
                            ),
                        ),
                        Column(
                            expand=True,
                            spacing=2,
                            controls=[
                                ft.Text(
                                    tr(f"nav.{route}.title"),
                                    size=15,
                                    weight=ft.FontWeight.W_600,
                                ),
                                ft.Text(
                                    tr(f"nav.{route}.desc"),
                                    size=12,
                                    color=MUTED,
                                    max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                            ],
                        ),
                        ft.Icon(ft.Icons.CHEVRON_RIGHT, color=ft.Colors.OUTLINE, size=18),
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
                top_bar(tr("home.title")),
                Container(
                    expand=True,
                    padding=ft.Padding.symmetric(vertical=18, horizontal=22),
                    content=Column(
                        expand=True,
                        scroll=ft.ScrollMode.AUTO,
                        spacing=14,
                        controls=[
                            ft.Text(
                                tr("home.headline"),
                                size=26,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Text(tr("home.intro"), size=13, color=MUTED),
                            Row(
                                spacing=10,
                                wrap=True,
                                controls=[
                                    _pill(tr("home.badge_flet")),
                                    _pill(tr("home.badge_scale"), "success"),
                                    _pill(tr("home.badge_hint"), "warning"),
                                ],
                            ),
                            Divider(color=BORDER, height=26),
                            ft.Text(
                                tr("home.catalog"),
                                size=17,
                                weight=ft.FontWeight.W_600,
                            ),
                            GridView(
                                height=500,
                                runs_count=3,
                                spacing=12,
                                run_spacing=12,
                                child_aspect_ratio=3.1,
                                controls=[nav_card(route, icon) for route, icon in NAV],
                            ),
                            ft.Text(
                                tr("home.version", version=UI_VERSION),
                                size=11,
                                color=MUTED,
                            ),
                        ],
                    ),
                ),
            ],
        ),
    )


# ----------------------------------------------------------------------
# 通用组件
# ----------------------------------------------------------------------


@ft.component
def GeneralPage() -> ft.Control:
    tr = use_t()

    text_section = section(
        tr("general.text.title"),
        tr("general.text.hint"),
        Column(
            spacing=6,
            controls=[
                Header_1("Header_1"),
                Header_2("Header_2"),
                Header_3("Header_3"),
                Header_4("Header_4"),
                Header_5("Header_5"),
                Text(tr("general.text.body"), size=14),
                Quote(tr("general.text.quote"), size=14),
                Link(tr("general.text.link"), link="https://flet.dev"),
            ],
        ),
    )

    button_section = section(
        tr("general.button.title"),
        tr("general.button.hint"),
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
                Button(
                    tr("general.button.plain", name=i.name), style_type=i, plain=True
                )
                for i in StyleType
            ],
        ),
        Row(
            wrap=True,
            spacing=10,
            run_spacing=10,
            controls=[
                Button(tr("general.button.round"), shape=ButtonShape.ROUND, plain=True),
                Button(
                    tr("general.button.rect"), shape=ButtonShape.RECTANGLE, plain=True
                ),
                Button(tr("general.button.pill"), shape=ButtonShape.CIRCLE, plain=True),
                Button(tr("general.button.primary"), is_primary=True),
                Button(tr("general.button.icon"), icon=ft.Icons.ADD),
                Button(tr("general.button.disabled"), disabled=True),
            ],
        ),
    )

    icon_section = section(
        tr("general.icon.title"),
        tr("general.icon.hint"),
        Row(
            spacing=16,
            wrap=True,
            controls=[
                ft.IconButton(
                    icon=ft.Icons.FAVORITE,
                    icon_color="#ef4444",
                    tooltip=tr("general.icon.love"),
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE,
                    icon_color=MUTED,
                    tooltip=tr("general.icon.delete"),
                ),
                ft.IconButton(
                    icon=ft.Icons.ADD_CIRCLE,
                    icon_color="#10b981",
                    tooltip=tr("general.icon.add"),
                ),
                ft.FilledIconButton(icon=ft.Icons.MAIL, badge=ft.Badge(label="5")),
                ft.FilledIconButton(
                    icon=ft.Icons.NOTIFICATIONS, badge=ft.Badge(label="99+")
                ),
                Container(
                    padding=ft.Padding.symmetric(vertical=8, horizontal=14),
                    border_radius=6,
                    bgcolor=ft.Colors.SURFACE,
                    border=ft.Border.all(1, BORDER),
                    content=ft.Text(tr("general.icon.rich"), size=13, color=ACCENT),
                    tooltip=ft.Tooltip(
                        message=tr("general.icon.rich_msg"),
                        bgcolor="#1f2937",
                        padding=8,
                        text_style=ft.TextStyle(color=ft.Colors.WHITE, size=12),
                    ),
                ),
            ],
        ),
    )

    chip_single = state(
        lambda: Chip(
            label=tr("general.chip.single"),
            options=tr.list("general.chip.options"),
        )
    )
    chip_multi = state(
        lambda: Chip(
            label=tr("general.chip.multi"),
            options=tr.list("general.chip.multi_options"),
            multi_select=True,
            selected_values=tr.list("general.chip.multi_options")[1:2],
        )
    )

    chip_section = section(
        tr("general.chip.title"),
        tr("general.chip.hint"),
        chip_single.ui(),
        chip_multi.ui(),
    )

    image_section = section(
        tr("general.image.title"),
        tr("general.image.hint"),
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
                        ft.Text(tr("general.image.top"), size=13),
                        Divider(color=BORDER),
                        ft.Text(tr("general.image.bottom"), size=13),
                        Divider(color=BORDER, leading_indent=40),
                        ft.Text(tr("general.image.indent"), size=12, color=MUTED),
                    ],
                ),
            ],
        ),
    )

    markdown_section = section(
        tr("general.markdown.title"),
        tr("general.markdown.hint"),
        Markdown(
            "### Markdown\n"
            "\n"
            "- **Bold**, *italic*, `inline code`\n"
            "- Ordered / unordered lists\n"
            "- [Links](https://flet.dev) and fenced code\n"
            "\n"
            "```python\n"
            'print("hello, cs-ui")\n'
            "```\n"
        ),
        Json(value='{"name": "cs-ui", "version": "0.1.1", "flet": ">=1.0.0"}'),
    )

    return page_shell(
        tr("nav.general.title"),
        tr("general.hint"),
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
    tr = use_t()

    flex_section = section(
        tr("layout.flex.title"),
        tr("layout.flex.hint"),
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
                    bgcolor=ft.Colors.PRIMARY_CONTAINER,
                    padding=14,
                    border_radius=8,
                    content=ft.Text(tr("layout.flex.container"), size=13),
                ),
                Stack(
                    controls=[
                        Container(
                            width=72,
                            height=72,
                            border_radius=36,
                            bgcolor=ft.Colors.SECONDARY_CONTAINER,
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
        tr("layout.list.title"),
        tr("layout.list.hint"),
        Row(
            spacing=12,
            controls=[
                Container(
                    height=190,
                    width=260,
                    border_radius=8,
                    bgcolor=ft.Colors.SURFACE,
                    border=ft.Border.all(1, BORDER),
                    content=ListView(
                        expand=True,
                        divider_thickness=0.5,
                        controls=[
                            Container(
                                padding=ft.Padding.symmetric(vertical=9, horizontal=12),
                                content=ft.Text(
                                    tr("layout.list.item", n=i + 1), size=13
                                ),
                            )
                            for i in range(20)
                        ],
                    ),
                ),
                Container(
                    height=190,
                    expand=True,
                    border_radius=8,
                    bgcolor=ft.Colors.SURFACE,
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
                                bgcolor=ft.Colors.PRIMARY_CONTAINER,
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
        tr("layout.expander.title"),
        tr("layout.expander.hint"),
        Expander(
            title=tr("layout.expander.basic"),
            subtitle=tr("layout.expander.basic_sub"),
            controls=[
                ft.Text(tr("layout.expander.basic_body1"), size=13),
                Divider(color=BORDER),
                ft.Text(tr("layout.expander.basic_body2"), size=12, color=MUTED),
            ],
        ),
        Expander(
            variant="filled",
            title=tr("layout.expander.filled"),
            subtitle=tr("layout.expander.filled_sub"),
            leading=ft.Icons.FOLDER_OPEN,
            accent="warning",
            controls=[ft.Text(tr("layout.expander.filled_body"), size=13)],
        ),
        Expander(
            variant="plain",
            density="compact",
            title=tr("layout.expander.plain"),
            trailing=ft.Text("3", size=12, color=MUTED),
            controls=[
                ft.Text(tr("layout.expander.plain_body"), size=12, color=MUTED)
            ],
        ),
    )

    timeline_section = section(
        tr("layout.timeline.title"),
        tr("layout.timeline.hint"),
        Timeline(
            items=[
                TimelineItem(
                    tr("layout.timeline.t1"),
                    "09:12",
                    tr("layout.timeline.d1"),
                    done=True,
                ),
                TimelineItem(
                    tr("layout.timeline.t2"),
                    "10:30",
                    tr("layout.timeline.d2"),
                    type="warning",
                ),
                TimelineItem(
                    tr("layout.timeline.t3"),
                    "14:05",
                    tr("layout.timeline.d3"),
                    type="info",
                ),
                TimelineItem("—", "—", tr("layout.timeline.d4")),
            ],
            pending=tr("layout.timeline.pending"),
        ),
        Timeline(
            mode="alternate",
            line_fade=True,
            density="compact",
            time_position="hidden",
            items=[
                TimelineItem("", "", tr("layout.timeline.alt1"), type="info"),
                TimelineItem("", "", tr("layout.timeline.alt2"), done=True),
                TimelineItem("", "", tr("layout.timeline.alt3"), done=True),
            ],
        ),
        stretch=True,
    )

    table_section = section(
        tr("layout.table.title"),
        tr("layout.table.hint"),
        Table(data_table=_build_data_table(tr), rows_per_page=8),
    )

    skeleton_section = section(
        tr("layout.page.title"),
        tr("layout.page.hint"),
        Container(
            height=260,
            border=ft.Border.all(1, BORDER),
            border_radius=10,
            content=PageLayout(
                title=tr("layout.page.user_title"),
                subtitle=tr("layout.page.user_subtitle"),
                padding=16,
                actions=[
                    Button(tr("layout.page.export")),
                    Button(tr("layout.page.create"), icon=ft.Icons.ADD),
                ],
                controls=[
                    Row(
                        spacing=10,
                        controls=[
                            _stat(tr("layout.page.stat_total"), "1,286", ACCENT),
                            _stat(tr("layout.page.stat_active"), "942", "#10b981"),
                            _stat(tr("layout.page.stat_pending"), "37", "#f59e0b"),
                        ],
                    ),
                    ft.Text(tr("layout.page.content"), size=12, color=MUTED),
                ],
            ),
        ),
    )

    return page_shell(
        tr("nav.layout.title"),
        tr("layout.hint"),
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
        bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
        border=ft.Border.all(1, BORDER),
        content=Column(
            spacing=2,
            controls=[
                ft.Text(value, size=18, weight=ft.FontWeight.BOLD, color=color),
                ft.Text(label, size=11, color=MUTED),
            ],
        ),
    )


def _build_data_table(tr) -> ft.DataTable:
    """构造一张演示用的 DataTable（列名与状态文字都取当前语言）。"""
    import random

    rows = [
        ft.DataRow(
            cells=[
                ft.DataCell(ft.Text(tr("layout.table.user", n=f"{i + 1:02d}"))),
                ft.DataCell(ft.Text(f"user{i + 1:02d}@cstos.com")),
                ft.DataCell(ft.Text(str(random.randint(20, 60)))),
                ft.DataCell(
                    ft.Text(
                        tr("layout.table.enabled")
                        if i % 3
                        else tr("layout.table.disabled"),
                        color="#10b981" if i % 3 else "#ef4444",
                    )
                ),
            ]
        )
        for i in range(46)
    ]
    return ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text(tr("layout.table.name"))),
            ft.DataColumn(ft.Text(tr("layout.table.email"))),
            ft.DataColumn(ft.Text(tr("layout.table.age")), numeric=True),
            ft.DataColumn(ft.Text(tr("layout.table.status"))),
        ],
        rows=rows,
    )


# ----------------------------------------------------------------------
# 导航组件
# ----------------------------------------------------------------------


@ft.component
def NavigationPage() -> ft.Control:
    tr = use_t()
    page = ft.context.page

    breadcrumb_section = section(
        tr("navigation.breadcrumb.title"),
        tr("navigation.breadcrumb.hint"),
        BreadCrumb(
            items=[
                Crumb(tr("navigation.breadcrumb.home"), route="/"),
                Crumb(tr("navigation.breadcrumb.nav"), route="/navigation"),
                Crumb(tr("navigation.breadcrumb.current")),
            ],
        ),
        BreadCrumb(
            items=[
                tr("navigation.breadcrumb.str"),
                (tr("navigation.breadcrumb.route"), "/general"),
                tr("navigation.breadcrumb.cur"),
            ],
            active_color=ACCENT,
        ),
    )

    tabs_section = section(
        tr("navigation.tabs.title"),
        tr("navigation.tabs.hint"),
        Container(
            height=200,
            border_radius=8,
            bgcolor=ft.Colors.SURFACE,
            border=ft.Border.all(1, BORDER),
            content=Tabs(
                length=3,
                content=Column(
                    controls=[
                        TabBar(
                            tabs=[
                                Tab(
                                    text=tr("navigation.tabs.overview"),
                                    icon=ft.Icons.DASHBOARD,
                                ),
                                Tab(
                                    text=tr("navigation.tabs.detail"),
                                    icon=ft.Icons.LIST_ALT,
                                ),
                                Tab(
                                    text=tr("navigation.tabs.settings"),
                                    icon=ft.Icons.SETTINGS,
                                ),
                            ]
                        ),
                        TabBarView(
                            expand=True,
                            height=140,
                            controls=[
                                Container(
                                    padding=16,
                                    content=ft.Text(
                                        tr("navigation.tabs.overview_body"), size=14
                                    ),
                                ),
                                Container(
                                    padding=16,
                                    content=ft.Text(
                                        tr("navigation.tabs.detail_body"), size=14
                                    ),
                                ),
                                Container(
                                    padding=16,
                                    content=ft.Text(
                                        tr("navigation.tabs.settings_body"), size=14
                                    ),
                                ),
                            ],
                        ),
                    ]
                ),
            ),
        ),
    )

    navbar_section = section(
        tr("navigation.navbar.title"),
        tr("navigation.navbar.hint"),
        Row(
            spacing=16,
            controls=[
                Container(
                    width=360,
                    bgcolor=ft.Colors.SURFACE,
                    border_radius=10,
                    border=ft.Border.all(1, BORDER),
                    content=ft.NavigationBar(
                        selected_index=1,
                        destinations=[
                            ft.NavigationBarDestination(
                                icon=ft.Icons.HOME_OUTLINED,
                                label=tr("navigation.navbar.home"),
                            ),
                            ft.NavigationBarDestination(
                                icon=ft.Icons.SEARCH,
                                label=tr("navigation.navbar.search"),
                            ),
                            ft.NavigationBarDestination(
                                icon=ft.Icons.PERSON_OUTLINE,
                                label=tr("navigation.navbar.mine"),
                            ),
                        ],
                    ),
                ),
                Container(
                    height=200,
                    bgcolor=ft.Colors.SURFACE,
                    border_radius=10,
                    border=ft.Border.all(1, BORDER),
                    content=ft.NavigationRail(
                        selected_index=0,
                        label_type=ft.NavigationRailLabelType.ALL,
                        destinations=[
                            ft.NavigationRailDestination(
                                icon=ft.Icons.DASHBOARD_OUTLINED,
                                label=tr("navigation.navbar.board"),
                            ),
                            ft.NavigationRailDestination(
                                icon=ft.Icons.ARTICLE_OUTLINED,
                                label=tr("navigation.navbar.article"),
                            ),
                            ft.NavigationRailDestination(
                                icon=ft.Icons.SETTINGS_OUTLINED,
                                label=tr("navigation.navbar.settings"),
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
            on_change_page=lambda p: print(f"[Paging] page={p}"),
        )
    )

    paging_section = section(
        tr("navigation.paging.title"),
        tr("navigation.paging.hint"),
        panel(Paging(paging_state)),
    )

    return page_shell(
        tr("nav.navigation.title"),
        tr("navigation.hint"),
        breadcrumb_section,
        tabs_section,
        navbar_section,
        paging_section,
        section(
            tr("navigation.jump.title"),
            tr("navigation.jump.hint"),
            Button(
                tr("navigation.jump.to_about"),
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
    tr = use_t()
    page = ft.context.page

    name = state(lambda: Input(label=tr("form.input.name"), value="Shawn", width=260))
    age = state(lambda: Input(label=tr("form.input.age"), value="30", data_type="int"))
    amount = state(
        lambda: Input(label=tr("form.input.amount"), value="199.9", data_type="float")
    )
    project_dir = state(
        lambda: Input(label=tr("form.input.dir"), value="", data_type="dir", width=300)
    )
    agree = state(lambda: Checkbox(label=tr("form.checkbox.agree"), is_required=True))
    hobbies = state(
        lambda: CheckboxGroup(
            label=tr("form.checkbox.hobbies"),
            options=tr.list("form.checkbox.options"),
            is_required=True,
        )
    )
    dark = state(lambda: Switch(label=tr("form.switch.dark")))
    notify = state(lambda: Switch(label=tr("form.switch.notify"), value=True))
    gender = state(
        lambda: Radio(
            label=tr("form.radio.gender"),
            options=tr.list("form.radio.options"),
            value=tr.list("form.radio.options")[0],
            radio_layout_type=LayoutType.HORIZONTAL,
        )
    )
    city = state(
        lambda: SelectBox(
            label=tr("form.select.city"),
            options=tr.list("form.select.cities"),
            value=tr.list("form.select.cities")[0],
        )
    )
    tags = state(
        lambda: MultiSelect(
            label=tr("form.select.tags"),
            options=tr.list("form.select.tag_options"),
            value=tr.list("form.select.tag_options")[1:3],
        )
    )
    volume = state(
        lambda: Slider(
            label=tr("form.slider.volume"),
            value=40,
            min=0,
            max=100,
            divisions=10,
            slider_label="{value}%",
        )
    )
    price_range = state(
        lambda: RangeSlider(
            label=tr("form.slider.price"),
            start_value=1500,
            end_value=6500,
            min=0,
            max=10000,
            divisions=20,
            slider_label="{value}",
        )
    )
    # Rating / SegmentedButton 是 @ft.control 控件（非 observable + ui() 那类），
    # 用 state() 固定实例即可直接放进控件树。
    pitch = state(lambda: Rating(value=4, elements=5))
    align_mode = state(
        lambda: SegmentedButton(
            options=tr.list("form.segmented.options"),
            selected=[tr.list("form.segmented.options")[1]],
            allow_multiple_selection=False,
            allow_empty_selection=False,
        )
    )
    birthday = state(
        lambda: DateInput(label=tr("form.date.birthday"), value=dt.date(1996, 5, 20))
    )
    meeting = state(
        lambda: DateTimeInput(
            label=tr("form.date.meeting"),
            value=dt.datetime(2026, 3, 18, 9, 30),
            with_seconds=False,
            minute_step=5,
        )
    )
    checkin = state(
        lambda: DateTimeInput(
            label=tr("form.date.checkin"),
            value=dt.datetime(2026, 3, 18, 9, 30, 15),
            with_seconds=True,
            hour_step=1,
            second_step=5,
            clearable=False,
        )
    )
    search = state(
        lambda: SearchBar(
            options=tr.list("form.select.cities"),
            bar_hint_text=tr("form.search.bar_hint"),
            view_hint_text=tr("form.search.view_hint"),
            on_click=lambda e: print(f"[SearchBar] {e.control.data}"),
        )
    )
    brand_color = state(lambda: ColorPicker(label=tr("form.color.brand"), value="#1F6FEB"))
    overlay_color = state(
        lambda: ColorPicker(
            label=tr("form.color.overlay"),
            value="#7C3AEDB3",  # 8 位十六进制按 CSS 顺序（末尾两位是透明度）
            default="#7C3AED",
            preset_cols=8,
        )
    )
    locked_color = state(
        lambda: ColorPicker(
            label=tr("form.color.locked"), value="#94A3B8", disabled=True, clearable=False
        )
    )

    def dump_values(_):
        # Rating 内部按 0 计数，对外展示统一 +1 还原为「几颗星」
        stars = pitch.value + 1 if isinstance(pitch.value, int) else 0
        toast_info(
            tr(
                "form.dump",
                name=name.value,
                age=age.value,
                city=city.value,
                tags=tags.display_text,
                volume=volume.value,
                stars=stars,
                birthday=birthday.display_text or "—",
                meeting=meeting.display_text or "—",
                brand=brand_color.value,
            ),
            page=page,
        )

    return page_shell(
        tr("nav.form.title"),
        tr("form.hint"),
        section(
            tr("form.input.title"),
            tr("form.input.hint"),
            Column(
                spacing=10,
                controls=[name.ui(), age.ui(), amount.ui(), project_dir.ui()],
            ),
        ),
        section(
            tr("form.checkbox.title"),
            tr("form.checkbox.hint"),
            Column(spacing=10, controls=[agree.ui(), hobbies.ui()]),
        ),
        section(
            tr("form.switch.title"),
            tr("form.switch.hint"),
            Column(spacing=10, controls=[dark.ui(), notify.ui()]),
        ),
        section(
            tr("form.radio.title"),
            tr("form.radio.hint"),
            gender.ui(),
        ),
        section(
            tr("form.select.title"),
            tr("form.select.hint"),
            Column(spacing=12, controls=[city.ui(), tags.ui()]),
        ),
        section(
            tr("form.slider.title"),
            tr("form.slider.hint"),
            Column(spacing=12, controls=[volume.ui(), price_range.ui()]),
        ),
        section(
            tr("form.rating.title"),
            tr("form.rating.hint"),
            Row(
                spacing=24,
                controls=[
                    labeled(tr("form.rating.interactive"), pitch),
                    labeled(tr("form.rating.readonly"), Rating(value=3, readonly=True)),
                    labeled(tr("form.rating.disabled"), Rating(value=2, disabled=True)),
                ],
            ),
        ),
        section(
            tr("form.segmented.title"),
            tr("form.segmented.hint"),
            align_mode,
        ),
        section(
            tr("form.date.title"),
            tr("form.date.hint"),
            Column(spacing=12, controls=[birthday.ui(), meeting.ui(), checkin.ui()]),
        ),
        section(
            tr("form.color.title"),
            tr("form.color.hint"),
            Column(
                spacing=12,
                controls=[brand_color.ui(), overlay_color.ui(), locked_color.ui()],
            ),
        ),
        section(
            tr("form.search.title"),
            tr("form.search.hint"),
            panel(search),
        ),
        actions=[
            Button(
                tr("common.read_values"),
                is_primary=True,
                on_click=dump_values,
            )
        ],
    )


# ----------------------------------------------------------------------
# 文件选择
# ----------------------------------------------------------------------


@ft.component
def UploadPage() -> ft.Control:
    tr = use_t()
    page = ft.context.page

    file_picker = state(lambda: FilePicker(allowed_extensions=["png", "jpg", "pdf"]))
    dir_picker = state(lambda: DirPicker())
    file_saver = state(lambda: FileSaver())
    image_picker = state(lambda: ImagePicker(label=tr("upload.image.label"), width=320))

    def read_values(_):
        toast_info(
            tr(
                "upload.dump",
                file=file_picker.value,
                dir=dir_picker.value,
                save=file_saver.value,
                image=image_picker.value,
            ),
            page=page,
        )

    return page_shell(
        tr("nav.upload.title"),
        tr("upload.hint"),
        section(
            tr("upload.file.title"),
            tr("upload.file.hint"),
            file_picker.ui(),
        ),
        section(
            tr("upload.dir.title"),
            tr("upload.dir.hint"),
            dir_picker.ui(),
        ),
        section(
            tr("upload.save.title"),
            tr("upload.save.hint"),
            file_saver.ui(),
        ),
        section(
            tr("upload.image.title"),
            tr("upload.image.hint"),
            image_picker.ui(),
        ),
        actions=[
            Button(
                tr("common.read_values"),
                is_primary=True,
                on_click=read_values,
            )
        ],
    )


# ----------------------------------------------------------------------
# 反馈组件
# ----------------------------------------------------------------------


@ft.component
def FeedbackPage() -> ft.Control:
    tr = use_t()
    page = ft.context.page

    def make_toast(style_type: StyleType, text: str):
        def _show(_):
            # page 必须用关键字传：第一个位置参数是 content，
            # 写成 .show(page) 会让 content 指向页面本身并构成环形引用。
            Toast(content=text, style_type=style_type).show(page=page)

        return _show

    def show_message(_):
        Message(content=tr("feedback.message.body"), style_type=StyleType.INFO).show()

    def show_dialog(_):
        AlertDialog(
            title=tr("feedback.dialog.delete_title"),
            msg=tr("feedback.dialog.delete_msg"),
            style_type=StyleType.WARNING,
            on_yes_click=lambda _: toast_success(
                tr("feedback.dialog.deleted"), page=page
            ),
            on_no_click=lambda _: toast_info(
                tr("feedback.dialog.canceled"), page=page
            ),
        ).show(page)

    # 用 hooks 管理进度值，演示「状态驱动 UI」的写法
    progress, set_progress = ft.use_state(0.35)

    def animate_progress(_):
        async def _pump():
            value = progress
            while value < 1.0:
                value = min(1.0, value + 0.02)
                set_progress(value)
                await asyncio.sleep(0.02)

        page.run_task(_pump)

    toast_rows = [
        (tr("feedback.toast.default"), StyleType.DEFAULT, tr("feedback.toast.msg_default")),
        (tr("feedback.toast.primary"), StyleType.PRIMARY, tr("feedback.toast.msg_primary")),
        (tr("feedback.toast.info"), StyleType.INFO, tr("feedback.toast.msg_info")),
        (tr("feedback.toast.success"), StyleType.SUCCESS, tr("feedback.toast.msg_success")),
        (tr("feedback.toast.warning"), StyleType.WARNING, tr("feedback.toast.msg_warning")),
        (tr("feedback.toast.error"), StyleType.ERROR, tr("feedback.toast.msg_error")),
    ]

    return page_shell(
        tr("nav.feedback.title"),
        tr("feedback.hint"),
        section(
            tr("feedback.toast.title"),
            tr("feedback.toast.hint"),
            Row(
                wrap=True,
                spacing=10,
                run_spacing=10,
                controls=[
                    Button(label, on_click=make_toast(style, text))
                    for label, style, text in toast_rows
                ],
            ),
            Row(
                wrap=True,
                spacing=10,
                controls=[
                    Button(
                        tr("feedback.toast.quick", name=tr("feedback.toast.success")),
                        on_click=lambda _: toast_success(
                            tr("feedback.toast.quick_success"), page
                        ),
                    ),
                    Button(
                        tr("feedback.toast.quick", name=tr("feedback.toast.error")),
                        on_click=lambda _: toast_error(
                            tr("feedback.toast.quick_error"), page
                        ),
                    ),
                    Button(
                        tr("feedback.toast.quick", name=tr("feedback.toast.warning")),
                        on_click=lambda _: toast_warning(
                            tr("feedback.toast.quick_warning"), page
                        ),
                    ),
                    Button(
                        tr("feedback.toast.quick", name=tr("feedback.toast.info")),
                        on_click=lambda _: toast_info(
                            tr("feedback.toast.quick_info"), page
                        ),
                    ),
                ],
            ),
        ),
        section(
            tr("feedback.message.title"),
            tr("feedback.message.hint"),
            Button(tr("feedback.message.show"), on_click=show_message),
        ),
        section(
            tr("feedback.dialog.title"),
            tr("feedback.dialog.hint"),
            Row(
                wrap=True,
                spacing=10,
                run_spacing=10,
                controls=[
                    Button(
                        style.name,
                        on_click=lambda _, _s=style: AlertDialog(
                            title=tr("feedback.dialog.title_n", name=_s.name),
                            msg=tr("feedback.dialog.body"),
                            style_type=_s,
                            on_yes_click=lambda _: None,
                            on_no_click=lambda _: None,
                        ).show(page),
                    )
                    for style in StyleType
                ],
            ),
            Button(
                tr("feedback.dialog.confirm"),
                is_primary=True,
                on_click=show_dialog,
            ),
        ),
        section(
            tr("feedback.progress.title"),
            tr("feedback.progress.hint"),
            ProgressBar(value=0.35, color=ACCENT),
            ProgressBar(value=0.72, color="#10b981"),
            ProgressBar(value=None, color="#f59e0b"),
        ),
        section(
            tr("feedback.loading.title"),
            tr("feedback.loading.hint"),
            Row(
                spacing=32,
                controls=[
                    Column(
                        spacing=4,
                        controls=[
                            ft.Text("small", size=11, color=MUTED),
                            Loading(size_name="small"),
                        ],
                    ),
                    Column(
                        spacing=4,
                        controls=[
                            ft.Text("normal", size=11, color=MUTED),
                            Loading(size_name="normal"),
                        ],
                    ),
                    Column(
                        spacing=4,
                        controls=[
                            ft.Text("large", size=11, color=MUTED),
                            Loading(size_name="large"),
                        ],
                    ),
                ],
            ),
        ),
        section(
            tr("feedback.hooks.title"),
            tr("feedback.hooks.hint"),
            ProgressBar(value=progress, color=ACCENT),
            ft.Text(
                tr("feedback.hooks.current", percent=f"{progress * 100:.0f}"),
                size=12,
                color=MUTED,
            ),
            Button(tr("feedback.hooks.run"), on_click=animate_progress),
        ),
    )


# ----------------------------------------------------------------------
# 数据显示
# ----------------------------------------------------------------------


@ft.component
def DisplayPage() -> ft.Control:
    tr = use_t()
    page = ft.context.page

    def log_lines() -> list[str]:
        return [
            tr("display.log.boot"),
            tr("display.log.db"),
            tr("display.log.theme"),
            tr("display.log.cache"),
        ]

    logs = state(lambda: LogContainer(logs=log_lines(), height=170))

    def push_logs(_):
        async def _run():
            await logs.add(tr("display.log.sync_start"))
            await asyncio.sleep(0.25)
            await logs.add(tr("display.log.sync_done"))
            await asyncio.sleep(0.25)
            await logs.add(tr("display.log.sync_skip"))

        page.run_task(_run)

    gallery = state(
        lambda: ImageGridView(
            title=tr("display.gallery.grid_title"),
            img_file_paths=[str(LOGO_FILE) for _ in range(23)],
            num_item_per_page=6,
            img_size=120,
            grid_height=300,
        )
    )

    return page_shell(
        tr("nav.display.title"),
        tr("display.hint"),
        section(
            tr("display.listtile.title"),
            tr("display.listtile.hint"),
            panel(
                ListTile(
                    title=tr("display.listtile.users"),
                    subtitle=tr("display.listtile.users_sub"),
                    leading=ft.Icon(ft.Icons.PEOPLE_OUTLINE, color=ACCENT),
                    trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT),
                ),
                Divider(height=1),
                ListTile(
                    title=tr("display.listtile.settings"),
                    subtitle=tr("display.listtile.settings_sub"),
                    leading=ft.Icon(ft.Icons.SETTINGS_OUTLINED, color="#10b981"),
                    trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT),
                ),
                Divider(height=1),
                ListTile(
                    title=tr("display.listtile.logs"),
                    subtitle=tr("display.listtile.logs_sub"),
                    leading=ft.Icon(ft.Icons.HISTORY, color="#f59e0b"),
                    trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT),
                ),
            ),
        ),
        section(
            tr("display.log.title"),
            tr("display.log.hint"),
            logs.ui(),
            Row(
                spacing=10,
                controls=[
                    Button(tr("display.log.append"), on_click=push_logs),
                    Button(tr("display.log.clear"), on_click=lambda _: logs.clear()),
                ],
            ),
        ),
        section(
            tr("display.code.title"),
            tr("display.code.hint"),
            CodeEditor(
                value="def add(a: int, b: int) -> int:\n    return a + b\n",
                language="python",
                height=130,
            ),
            CodeView(
                code=(
                    f'Button("{tr("display.code.run")}", '
                    "is_primary=True)"
                ),
                component=Button(tr("display.code.run"), is_primary=True),
            ),
        ),
        section(
            tr("display.gallery.title"),
            tr("display.gallery.hint"),
            gallery.ui(),
        ),
    )


# ----------------------------------------------------------------------
# 图表
# ----------------------------------------------------------------------


def _sales(tr) -> dict[str, list]:
    """图表演示数据（列字典格式）。键名即图例文字，所以也要跟着语言走。"""
    return {
        tr("charts.month"): tr.list("charts.months"),
        tr("charts.online"): [120, 152, 141, 179, 210, 245, 268, 302],
        tr("charts.offline"): [86, 92, 105, 118, 124, 121, 138, 149],
    }


@ft.component
def ChartsPage() -> ft.Control:
    tr = use_t()

    month = tr("charts.month")
    series = [tr("charts.online"), tr("charts.offline")]

    return page_shell(
        tr("nav.charts.title"),
        tr("charts.hint"),
        section(
            tr("charts.line.title"),
            tr("charts.line.hint"),
            LineChart(
                data=_sales(tr), x=month, y=series, height=280, show_points=True
            ),
        ),
        section(
            tr("charts.area.title"),
            tr("charts.area.hint"),
            AreaChart(
                data=_sales(tr),
                x=month,
                y=[tr("charts.online")],
                height=280,
                color="#10b981",
            ),
        ),
        section(
            tr("charts.bar.title"),
            tr("charts.bar.hint"),
            BarChart(data=_sales(tr), x=month, y=series, height=280),
            BarChart(data=_sales(tr), x=month, y=series, stacked=True, height=280),
        ),
        section(
            tr("charts.scatter.title"),
            tr("charts.scatter.hint"),
            ScatterChart(
                data=[
                    (
                        round(math.cos(i * 0.4) * 10 + 20, 2),
                        round(math.sin(i * 0.7) * 8 + 15, 2),
                    )
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
    tr = use_t()

    # flet 1.0.0 起 Audio 是 ft.Service（不是 ft.Control）：放进控件树会被
    # Flutter 判为 "Unknown control: Audio"。Service 在构造时自动注册到
    # page 的服务注册表，所以这里用 state() 固定实例、只持有引用不挂进树。
    audio_service = state(lambda: Audio(src=SAMPLE_AUDIO))

    return page_shell(
        tr("nav.media.title"),
        tr("media.hint"),
        section(
            tr("media.audio.title"),
            tr("media.audio.hint"),
            panel(
                Row(
                    spacing=8,
                    controls=[
                        ft.Icon(ft.Icons.GRAPHIC_EQ, size=16, color=ACCENT),
                        ft.Text(
                            tr("media.audio.registered", src=audio_service.src),
                            size=12,
                            color=MUTED,
                        ),
                    ],
                )
            ),
            AudioPlayer(
                src=SAMPLE_AUDIO,
                title=tr("media.audio.track_title"),
                subtitle=tr("media.audio.track_subtitle"),
            ),
        ),
        section(
            tr("media.video.title"),
            tr("media.video.hint"),
            Video(src=SAMPLE_VIDEO, title="bee.mp4", height=260),
            Video(
                playlist=build_playlist([SAMPLE_VIDEO, SAMPLE_VIDEO_2]),
                title=tr("media.video.playlist"),
                height=260,
            ),
        ),
        section(
            tr("media.pdf.title"),
            tr("media.pdf.hint"),
            Pdf(src=SAMPLE_PDF, title=tr("media.pdf.doc"), height=420),
        ),
    )


# ----------------------------------------------------------------------
# 关于
# ----------------------------------------------------------------------

MIGRATION_TABLE = (
    "| Legacy (0.x) | Current (1.0.0) |\n"
    "| --- | --- |\n"
    "| `ft.app(main)` | `ft.run(main)` |\n"
    "| `page.add(...)` | `page.render(Component)` |\n"
    "| `page.views.append(...)` | `ft.Router(ROUTES, manage_views=False)` + `page.render` |\n"
    "| `page.go(route)` | `page.navigate(route)` |\n"
    "| `page.overlay.append(dlg); dlg.open = True` | `page.show_dialog(dlg)` |\n"
    "| `ft.View(appbar=ft.AppBar(…))` | `Container` + custom top bar |\n"
    "| `TextField(border_radius=…, border_color=…)` | `TextField(border=ft.OutlineInputBorder(...))` |\n"
    "| `Tooltip(content=…)` | `control.tooltip = ft.Tooltip(message=…)` |\n"
    "| `Badge(badge_value=…)` | `Badge(label=…)` |\n"
)

RUN_SNIPPET = (
    "# run the demo\n"
    "python examples/demo.py\n"
    "\n"
    "# headless smoke test across every route\n"
    "python scripts/smoke_test.py examples.demo main "
    "--routes /,/general,/layout,/navigation,/form,/upload,"
    "/feedback,/display,/charts,/media,/about\n"
)


@ft.component
def AboutPage() -> ft.Control:
    tr = use_t()

    return page_shell(
        tr("nav.about.title"),
        tr("about.hint"),
        section(
            tr("about.design.title"),
            tr("about.design.hint"),
            Column(
                spacing=6,
                controls=[
                    ft.Text(tr(f"about.design.p{i}"), size=13) for i in range(1, 5)
                ],
            ),
        ),
        section(
            tr("about.i18n.title"),
            tr("about.i18n.hint"),
            Column(
                spacing=6,
                controls=[
                    ft.Text(tr(f"about.i18n.p{i}"), size=13) for i in range(1, 5)
                ],
            ),
        ),
        section(
            tr("about.stats.title"),
            tr("about.stats.hint"),
            Row(
                spacing=10,
                wrap=True,
                run_spacing=10,
                controls=[
                    _stat(tr(f"nav.{route}.title"), value, color)
                    for route, value, color in STATS
                ],
            ),
        ),
        section(
            tr("about.migration.title"),
            tr("about.migration.hint"),
            Markdown(MIGRATION_TABLE),
        ),
        section(
            tr("about.run.title"),
            tr("about.run.hint"),
            Code(value=RUN_SNIPPET, language="bash", height=170),
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
    tr = use_t()
    page = ft.context.page
    return Container(
        expand=True,
        bgcolor=PAGE_BG,
        content=Column(
            expand=True,
            spacing=0,
            controls=[
                top_bar(tr("notfound.title")),
                Container(
                    expand=True,
                    alignment=ft.Alignment.CENTER,
                    content=Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=12,
                        controls=[
                            ft.Text(
                                "404",
                                size=72,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.OUTLINE_VARIANT,
                            ),
                            ft.Text(tr("notfound.body"), size=14, color=MUTED),
                            Button(
                                tr("notfound.back"),
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


def _shell() -> ft.Control:
    """应用主体：主题下发 + 声明式路由。

    ``ThemeProvider`` 必须包在路由**外层**：它要写 ``page.theme``，
    放在页面组件里会晚一帧，表现为"切模式闪一下旧配色"。
    """
    return ThemeProvider(
        build=lambda: ft.Router(
            ROUTES, not_found=NotFoundPage, manage_views=False
        )
    )


@ft.component
def App() -> ft.Control:
    """根组件：语言在最外层，主题在其内。

    语言 Provider 放最外层有两个理由：一是它要在**首帧之前**把语言定下来
    （读持久化选择 / 系统语言），二是 404 之类的路由外页面也要能跟着切语言。
    ``build`` 传工厂函数 —— 切语言时只重绘订阅了 ``use_t()`` 的组件，
    整棵控件树和其中的表单状态都不重建。
    """
    return I18nProvider(locale="zh-CN", build=_shell)


def _configure_page(page: ft.Page) -> None:
    """页面级设置（字体）。**主题不在这里设** —— 交给 ``ThemeProvider``，
    否则会出现"两处都能改主题、谁最后生效说不清"的问题。"""
    if FONT_FILE.exists():
        page.fonts = {"AlibabaPuHuiTi": str(FONT_FILE)}
        theme_state().font_family = "AlibabaPuHuiTi"


def main(page: ft.Page) -> None:
    """flet 1.0.0 入口：把 Router 渲染进根视图。

    用 ``page.render`` 而非 ``page.render_views``。后者会生成视图栈，
    把**整个页面浮层盖住**（``page.overlay`` 与 ``page.show_dialog``
    都不渲染，且不报错），MultiSelect 这类需要悬挂面板的组件就失效了。
    """
    page.title = "CS UI"
    page.window.width = 1180
    page.window.height = 840
    page.window.min_width = 900
    page.window.min_height = 640
    _configure_page(page)
    page.render(App)


if __name__ == "__main__":
    ft.run(main)
