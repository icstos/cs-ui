# CS UI

基于 [Flet](https://flet.dev/) 构建的 Python UI 组件库，提供丰富的预样式、开箱即用组件，具备更优的默认值和清晰的模块化包结构。

## 特点

- **开箱即用** — `from ui import *` 直接导出 Flet 全部内容 + 所有 CS UI 组件
- **继承原生控件** — 所有组件直接继承 Flet 原生控件（如 `Button(ft.Button)`、`Text(ft.Text)`）
- **智能默认值** — 组件自带合理的样式默认值（颜色、尺寸、圆角等），加速原型开发
- **模块分类** — 组件按功能分类：chart / display / feedback / input / layout / navigation
- **路由系统** — 内置 `App` 类，支持自动路由
- **图表支持** — 通过 `flet-charts` 封装 Bar / Line / Area / Scatter 图表

## 环境要求

- Python >= 3.13
- flet[all] >= 0.85.2
- flet-code-editor
- flet-charts

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
from ui import App, Button, Card, Checkbox, Column, Container, Divider, Row, Switch, Text, TextField

def main(page: ft.Page):
    page.title = "CS UI Demo"
    page.bgcolor = "#f8fafc"

    card = Card(
        elevation=4,
        content=Container(
            padding=24,
            border_radius=16,
            content=Column(
                controls=[
                    Text("CS UI 框架示例", size=24, weight="bold"),
                    Text("基于 Flet 风格构建的组件体系。", size=14, color="#6b7280"),
                    Divider(),
                    TextField(
                        label="输入内容",
                        hint_text="按回车提交",
                        width=320,
                    ),
                    Row(
                        controls=[
                            Checkbox(label="我已阅读"),
                            Switch(label="开关示例"),
                        ],
                        spacing=20,
                    ),
                    Button(label="点我", on_click=lambda e: print("clicked!")),
                ],
                spacing=16,
            ),
        ),
    )
    page.add(card)

if __name__ == "__main__":
    ft.app(target=main)
```

## 包结构

```
src/ui/
├── __init__.py          # 导出 flet + 所有子包
├── app.py               # App 类（含路由）
├── ft_init.py           # Flet 初始化
├── chart/               # 图表
│   ├── bar_chart.py     #   BarChart
│   ├── line_chart.py    #   LineChart
│   ├── rea_chart.py     #   AreaChart
│   └── scatter_chart.py #   ScatterChart
├── core/                # 核心工具
│   ├── config.py
│   ├── constants.py
│   ├── form.py
│   └── language.py
├── data/                # 静态资源（字体、图片）
├── display/             # 展示组件
│   ├── image.py         #   Image
│   ├── image_gridview.py#   ImageGridView
│   ├── list_tile.py     #   ListTile
│   ├── log_container.py #   LogContainer
│   └── text.py          #   Text
├── feedback/            # 反馈 & 浮层
│   ├── alert_dialog.py  #   AlertDialog
│   ├── loading.py       #   Loading
│   ├── message.py       #   Message
│   ├── progress_bar.py  #   ProgressBar
│   └── toast.py         #   SnackBar
├── input/               # 表单输入
│   ├── button.py            #   Button
│   ├── checkbox.py          #   Checkbox
│   ├── chip.py              #   Chip
│   ├── color_picker.py      #   ColorPicker
│   ├── date_input.py        #   DateInput
│   ├── datetime_input.py    #   DateTimeInput
│   ├── file_picker.py       #   FilePicker
│   ├── image_picker.py      #   ImagePicker
│   ├── input.py             #   TextField
│   ├── multi_select.py      #   MultiSelect
│   ├── radio.py             #   RadioGroup
│   ├── rating.py            #   Rating
│   ├── search_bar.py        #   SearchBar
│   ├── segmented_button.py  #   SegmentedButton
│   ├── select_box.py        #   Dropdown
│   ├── slider.py            #   Slider
│   └── switch.py            #   Switch
├── layout/              # 布局 & 容器
│   ├── card.py          #   Card
│   ├── column.py        #   Column
│   ├── container.py     #   Container
│   ├── divider.py       #   Divider
│   ├── expander.py      #   Expander
│   ├── grid_view.py     #   GridView
│   ├── list_view.py     #   ListView
│   ├── page.py          #   Page
│   ├── row.py           #   Row
│   ├── stack.py         #   Stack
│   ├── table.py         #   Table
│   ├── tabs.py          #   Tabs
│   ├── time_line.py     #   Timeline
│   └── view.py          #   View
├── navigation/          # 导航
│   ├── app_bar.py       #   AppBar
│   ├── bread_crumb.py   #   BreadCrumb
│   └── paging.py        #   NavigationBar
└── utils/               # 工具
    ├── code_editor.py   #   CodeEditor
    ├── code_view.py     #   CodeView
    └── componts.py      #   辅助组件
```

## 组件概况

| 分类 | 组件 |
|------|------|
| **Chart 图表** | BarChart、LineChart、AreaChart、ScatterChart |
| **Display 展示** | Image、ImageGridView、ListTile、LogContainer、Text |
| **Feedback 反馈** | AlertDialog、Loading、Message、ProgressBar、SnackBar |
| **Input 输入** | Button、Checkbox、Chip、ColorPicker、DateInput、DateTimeInput、FilePicker、ImagePicker、TextField、MultiSelect、RadioGroup、Rating、SearchBar、SegmentedButton、Dropdown、Slider、Switch |
| **Layout 布局** | Card、Column、Container、Divider、Expander、GridView、ListView、Page、Row、Stack、Table、Tabs、Timeline、View |
| **Navigation 导航** | AppBar、BreadCrumb、NavigationBar |

## 导入方式

所有组件均可从 `ui` 直接导入：

```python
from ui import App, Button, Card, Column, Container, Divider, Row, Text, TextField
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
- 基于 Python 3.13+ 语法实现
- 参考 Flet 最新版本特性进行优化

## 示例

运行演示程序查看所有组件效果：

```bash
python examples/demo.py
```

其他测试文件：

- `examples/test_home.py` — 最小首页
- `examples/test_form.py` — 表单组件
- `examples/test_feedback.py` — 反馈组件（对话框、消息提示、加载、进度条）
- `examples/test_chart.py` — 图表组件
- `examples/test_line_chart.py` — 折线图
- `examples/test_button.py` — 按钮变体
- `examples/test_minimal.py` / `test_simple.py` — 最小示例

## 参考资料

- <https://github.com/flet-dev/examples.git>
- <https://flet.dev/>
