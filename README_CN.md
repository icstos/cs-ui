# CS-UI

[![Flet](https://img.shields.io/badge/Flet-1.0.0-blue)](https://flet.dev)
[![Python](https://img.shields.io/badge/Python-3.12%2B-green)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

基于 [Flet](https://flet.dev/) 构建的 Python UI 组件库，提供丰富的预样式、开箱即用组件，具备更优的默认值和清晰的模块化包结构。

## 特点

- **开箱即用** — `from ui import *` 直接导出 Flet 全部内容 + 所有 CS UI 组件
- **继承原生控件** — 所有组件直接继承 Flet 原生控件（如 `Button(ft.Button)`、`Text(ft.Text)`）
- **智能默认值** — 组件自带合理的样式默认值（颜色、尺寸、圆角等），加速原型开发
- **模块分类** — 组件按功能分类：chart / display / feedback / input / layout / navigation
- **声明式路由** — `ft.Router(routes, manage_views=False)` + `page.render` 的根视图路由
- **页面浮层可用** — 根视图路径下 `page.overlay` / `page.show_dialog` 正常渲染，
  `MultiSelect` 的下拉面板、`DateInput` 的月历、`DateTimeInput` 的「月历 + 时间轮盘」
  可以真正"悬挂"在内容之上
  （折叠态占用高度即整个组件高度，展开不推动下方内容）
- **双范式组件** — 无状态控件继承原生控件；有状态组件用 `@ft.observable` + `ui()` 函数
- **图表支持** — 通过 `flet-charts` 封装 Bar / Line / Area / Scatter 图表，x 轴数值 / 分类通吃

## 环境要求

- Python >= 3.12
- flet[all] >= 1.0.0
- flet-code-editor
- flet-charts
- flet-video / flet-audio / flet-webview

## 安装

```bash
uv pip install cs-ui
```

或从源码安装（可编辑模式）：

```bash
git clone https://github.com/icstos/cs-ui.git
cd cs-ui
pip install -e .
```

## 快速开始

```python
import flet as ft
from ui import (
    Button,
    Card,
    Checkbox,
    Column,
    Container,
    Divider,
    Input,
    Router,
    Route,
    Row,
    Text,
)


@ft.component
def HomePage() -> ft.Control:
    name = ft.use_ref(lambda: Input(label="姓名", value="Shawn", width=260)).current
    agree = ft.use_ref(lambda: Checkbox(label="我已阅读")).current

    # 页面返回普通控件，顶栏自绘 —— 根视图模式下 ft.View / ft.AppBar 不可用（见下）
    return Container(
        expand=True,
        content=Column(
            spacing=0,
            controls=[
                Container(
                    height=56,
                    bgcolor=ft.Colors.WHITE,
                    padding=ft.Padding.symmetric(horizontal=14),
                    content=Row(
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[Text("CS UI Demo", size=17, weight=ft.FontWeight.W_600)],
                    ),
                ),
                Card(
                    elevation=4,
                    content=Container(
                        padding=24,
                        border_radius=16,
                        content=Column(
                            controls=[
                                Text("CS UI 声明式示例", size=24, weight=ft.FontWeight.BOLD),
                                Text("基于 flet 1.0.0 构建的组件体系。", size=14, color="#6b7280"),
                                Divider(),
                                name.ui(),
                                Row(
                                    spacing=20,
                                    controls=[agree.ui(), ft.Switch(label="开关示例")],
                                ),
                                Button(
                                    "点我",
                                    on_click=lambda _: print("clicked!"),
                                ),
                            ],
                            spacing=16,
                        ),
                    ),
                ),
            ],
        ),
    )


@ft.component
def App() -> ft.Control:
    return Router([Route(index=True, component=HomePage)], manage_views=False)


def main(page: ft.Page) -> None:
    page.title = "CS UI Demo"
    page.render(App)


if __name__ == "__main__":
    ft.run(main)
```

> **渲染路径：请用 `page.render` + `Router(manage_views=False)`，不要用 `page.render_views`。**
>
> 两个实测过的坑：
>
> 1. `page.render_views`（`Router(manage_views=True)` 的视图栈）会把**整个页面浮层盖住** ——
>    `page.overlay` 里挂任何东西都是零像素、`page.show_dialog` 同样失效，
>    而且**不报错**（Python 侧 `len(page.overlay)` 正确、回调照常触发）。
>    `MultiSelect` 的悬浮面板、Toast、Dialog 都会因此失灵。
> 2. **`ft.View` 不能当普通控件用**。根视图模式下把一个 `View` 塞进控件树，
>    Flutter 侧会反复抛 `Bad state: No element`，整页渲染成灰块。
>    同理 `ft.AppBar` 是 `AdaptiveControl`，只能挂在 `View.appbar` 上，
>    进不了 `Column.controls` —— 顶栏请用 `Container` + `Row` 自绘。
>
> 迁移提示：`ft.app(main)` → `ft.run(main)`；`page.add(...)` → `page.render(Component)`；
> `page.go(route)` → `page.navigate(route)`；`page.views` 手工维护 →
> `ft.Router(routes, manage_views=False)`。项目内置的 `ui.Button` 用 `content` 传文字（不是 `label`）。
>
> 组件分两类：**无状态控件**（`Button` / `Table` / `Rating` … 直接继承 Flet 控件）直接构造即可；
> **有状态组件**（`Input` / `Checkbox` / `Switch` / `SelectBox` / `MultiSelect` … 由 `@ft.observable` 数据对象 +
> `@ft.component ui()` 组成）必须构造后再调用 `.ui()` 放进控件树，否则只会得到一块空白或灰块。
>
> 若宿主必须用视图栈（`manage_views=True`），`MultiSelect` 会自动降级为**流内展开**
> （面板占布局高度、会把下方内容推下去）；也可用 `float_panel=False` 显式关闭浮层。

## 包结构

```
src/ui/
├── __init__.py              # 导出 flet 全部内容 + 所有 CS UI 组件（617 个名字）
├── app.py                   # 传统式 App 入口
├── ft_init.py               # Flet 初始化
├── theme.py                 # 主题 / 配色
├── cli.py                   # 命令行入口
├── chart/                   # 图表（基于 flet-charts）
│   ├── _data.py             #   共享数据解析 + 配色（数值轴 / 分类轴）
│   ├── bar_chart.py         #   BarChart
│   ├── line_chart.py        #   LineChart
│   ├── rea_chart.py         #   AreaChart
│   └── scatter_chart.py     #   ScatterChart
├── components/              # 通用可复用控件
│   └── icon_button.py       #   IconButton
├── core/                    # 核心工具
│   ├── config.py            #   配置
│   ├── constants.py         #   StyleType / FeedbackStyle / ButtonShape …
│   ├── float_layer.py       #   页面浮层：overlay_usable / use_float_layer
│   ├── language.py          #   多语言
│   ├── logger.py            #   日志
│   ├── snackbar.py          #   SnackBar 类组件的 content 守卫
│   └── styles.py            #   统一样式助手
├── data/                    # 静态资源（字体、图片）
├── display/                 # 展示组件
│   ├── echarts.py           #   ECharts（WebView 内嵌）
│   ├── image.py             #   Image
│   ├── image_gridview.py    #   ImageGridView
│   ├── list_tile.py         #   ListTile
│   ├── log_container.py     #   LogContainer
│   ├── text.py              #   Text / Header_1..5 / Quote / Link / Code / Markdown / Json
│   └── media/               #   媒体
│       ├── audio.py         #     Audio / AudioPlayer
│       ├── pdf.py           #     Pdf
│       └── video.py         #     Video
├── feedback/                # 反馈 & 浮层
│   ├── alert_dialog.py      #   AlertDialog
│   ├── loading.py           #   Loading
│   ├── message.py           #   Message
│   ├── progress_bar.py      #   ProgressBar
│   └── toast.py             #   Toast / toast_success / toast_error …
├── input/                   # 表单输入
│   ├── button.py            #   Button
│   ├── checkbox.py          #   Checkbox / CheckboxGroup
│   ├── chip.py              #   Chip
│   ├── color_picker.py      #   ColorPicker
│   ├── date_input.py        #   DateInput
│   ├── datetime_input.py    #   DateTimeInput
│   ├── file_picker.py       #   FilePicker / DirPicker
│   ├── image_picker.py      #   ImagePicker
│   ├── input.py             #   Input（data_type: str/int/float/file/dir）
│   ├── multi_select.py      #   MultiSelect
│   ├── radio.py             #   RadioGroup
│   ├── rating.py            #   Rating
│   ├── search_bar.py        #   SearchBar
│   ├── segmented_button.py  #   SegmentedButton
│   ├── select_box.py        #   SelectBox
│   ├── slider.py            #   Slider
│   └── switch.py            #   Switch
├── layout/                  # 布局 & 容器
│   ├── card.py              #   Card
│   ├── column.py            #   Column
│   ├── container.py         #   Container
│   ├── divider.py           #   Divider
│   ├── expander.py          #   Expander
│   ├── grid_view.py         #   GridView
│   ├── list_view.py         #   ListView
│   ├── page.py              #   PageLayout
│   ├── row.py               #   Row
│   ├── stack.py             #   Stack
│   ├── table.py             #   Table（含分页）
│   ├── tabs.py              #   Tabs / Tab / TabBar / TabBarView
│   ├── time_line.py         #   Timeline / TimelineItem
│   └── view.py              #   View
├── navigation/              # 导航
│   ├── app_bar.py           #   AppBar
│   ├── bread_crumb.py       #   BreadCrumb / Crumb
│   └── paging.py            #   Paging / PagingState
└── utils/                   # 工具
    ├── code_editor.py       #   Code
    ├── code_view.py         #   CodeView
    └── componts.py          #   辅助组件
```

## 组件概况

| 分类 | 组件 |
|------|------|
| **Chart 图表** | BarChart、LineChart、AreaChart、ScatterChart |
| **Display 展示** | ECharts、Image、ImageGridView、ListTile、LogContainer、Text / Header_1..5 / Quote / Link / Code / Markdown / Json |
| **Display 媒体** | Audio、AudioPlayer、Video、Pdf |
| **Feedback 反馈** | AlertDialog、Loading、Message、ProgressBar、Toast |
| **Input 输入** | Button、Checkbox / CheckboxGroup、Chip、ColorPicker、DateInput、DateTimeInput、FilePicker / DirPicker、ImagePicker、Input、MultiSelect、RadioGroup、Rating、SearchBar、SegmentedButton、SelectBox、Slider、Switch |
| **Layout 布局** | Card、Column、Container、Divider、Expander、GridView、ListView、PageLayout、Row、Stack、Table、Tabs、Timeline、View |
| **Navigation 导航** | AppBar、BreadCrumb、Paging |

**双范式**：
- **无状态控件**（`Button` / `Table` / `ECharts` / `Rating` / `Timeline` / 图表 …）直接继承 Flet 控件，构造即用。
- **有状态组件**（`Input` / `Checkbox` / `Switch` / `SelectBox` / `MultiSelect` …）是 `@ft.observable` 数据对象，需构造后调用 `.ui()` 放进控件树。

## 导入方式

所有组件均可从 `ui` 直接导入：

```python
from ui import Button, Card, Column, Container, Divider, Row, Text, TextField
```

由于 `ui` 重新导出了 Flet，你也可以直接使用 Flet 类型：

```python
from ui import ft  # flet 模块

# 或
from ui import Page, Colors, Icons, MainAxisAlignment, CrossAxisAlignment
```

## 设计原则

- 基于 Flet 原生控件继承，`from ui import *` 即可使用
- 以包的形式组织代码，一个 `.py` 一般只实现一个控件
- 包内代码对外尽量无依赖
- 事件处理函数命名：`on_xx`
- 所有组件采用绝对路径导入
- 基于 Python 3.12+ 语法实现
- 参考 Flet 最新版本特性进行优化

## 示例

运行演示程序查看所有组件效果（11 个分类页 + 404 页）：

```bash
python examples/demo.py
```

| 路由 | 内容 |
|------|------|
| `/` | 首页导航（按分类进入各页） |
| `/general` | 文本 / 按钮 / 图标 / 标签 |
| `/layout` | 容器 / 列表 / 表格 / 时间线 |
| `/navigation` | 面包屑 / 标签页 / 分页 |
| `/form` | 输入框 / 选择器 / 滑块 / 评分 |
| `/upload` | 文件 / 目录 / 保存 / 图片 |
| `/feedback` | Toast / 消息 / 对话框 / 进度 |
| `/display` | 日志 / 代码 / ECharts / 图片 |
| `/charts` | 折线 / 面积 / 柱状 / 散点图 |
| `/media` | 音频 / 视频 / PDF |
| `/about` | 迁移速查与设计说明 |

其他测试文件：

- `examples/test_home.py` — 最小首页
- `examples/test_form.py` — 表单组件
- `examples/test_feedback.py` — 反馈组件（对话框、消息提示、加载、进度条）
- `examples/test_chart.py` — 图表组件
- `examples/test_line_chart.py` — 折线图
- `examples/test_button.py` — 按钮变体
- `examples/test_minimal.py` / `test_simple.py` — 最小示例
- `examples/my_control.py` — 自定义控件示例

## 参考资料

- <https://github.com/flet-dev/examples.git>
- <https://flet.dev/>
