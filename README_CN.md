# CS-UI

[![Flet](https://img.shields.io/badge/Flet-1.0.5-blue)](https://flet.dev)
[![Python](https://img.shields.io/badge/Python-3.12%2B-green)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

基于 [Flet](https://flet.dev/) 构建的 Python UI 组件库，提供丰富的预样式、开箱即用组件，具备更优的默认值和清晰的模块化包结构。

## 特点

- **开箱即用** — `from ui import *` 直接导出 Flet 全部内容 + 所有 CS UI 组件
- **设计令牌 + Material 3 主题** — 组件里不出现裸色值/裸圆角/裸字号；
  一个品牌色种子（`color_scheme_seed`）推导出整套 M3 色板，
  明暗模式与主色切换是**框架级**的，不靠逐组件改颜色
- **继承原生控件** — 静态组件直接继承 Flet 原生控件（如 `Button(ft.Button)`、`Text(ft.Text)`）
- **智能默认值** — 组件自带合理的样式默认值（颜色、尺寸、圆角等），加速原型开发
- **模块分类** — 组件按功能分类：chart / display / feedback / input / layout / navigation
- **声明式路由** — `ft.Router(routes, manage_views=False)` + `page.render` 的根视图路由
- **页面浮层可用** — 根视图路径下 `page.overlay` / `page.show_dialog` 正常渲染，
  `MultiSelect` 的下拉面板、`DateInput` 的月历、`DateTimeInput` 的「月历 + 时间轮盘」
  可以真正"悬挂"在内容之上
  （折叠态占用高度即整个组件高度，展开不推动下方内容）
- **双范式组件** — 静态组件继承原生控件；交互式组件是 `@ft.component` 函数，
  内部用 `use_state` / `use_memo` / `use_effect` 等 hooks 声明状态与副作用
- **国际化 (i18n)** — 内置简体中文 / 繁體中文 / English，`use_t()` 一行订阅，
  切语言只重绘用到翻译的组件（不丢表单内容）；缺翻译自动沿
  `繁 → 简 → 英` 回退，选择写入本地配置、首帧即生效（不会先闪默认语言）
- **图表支持** — 通过 `flet-charts` 封装 Bar / Line / Area / Scatter 图表，x 轴数值 / 分类通吃
- **对得齐的字段网格** — `Descriptions` 默认就是带边框的表格：标签格淡底色、1px 细线分隔、
  外框圆角；`column` 决定一行几个字段，`span` 让长内容（地址、备注）跨两列，末行没排满时
  最后一个字段吃掉剩余列，不留空洞。`direction="vertical"` 换成标签在上，`bordered=False`
  去掉边框退成轻量对齐排布。列宽来自 `Row` 的权重（同一行权重之和恒等于 `column`），
  所以不测量像素，窗口缩放也自动跟手
- **看得见进度的步骤条** — `Step` 把流程建模成状态机：每步只可能是
  `wait` / `process` / `finish` / `error`，既可按 `active` 自动推导，也能在单步上钉死；
  连接线只给"已经走过"的段上色，进度靠颜色说话。横向平铺、垂直轴轨、一行式 `simple`
  三种排布，`simple` 点击即跳转；点击后组件就地重建，反馈即时，`on_change(index)`
  让状态源仍由调用方掌握

## 环境要求

- Python >= 3.12
- flet[all] ~= 1.0.5
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
│   ├── i18n.py              #   多语言：I18nProvider / LanguageSwitcher / use_t / t
│   ├── logger.py            #   日志
│   ├── snackbar.py          #   SnackBar 类组件的 content 守卫
│   ├── styles.py            #   统一样式助手
│   ├── theme.py             #   ThemeProvider / ThemeSwitcher / use_theme
│   └── tokens.py            #   设计令牌：SPACE / RADIUS / FONT_SIZE / 语义色
├── data/                    # 静态资源（字体、图片）
├── display/                 # 展示组件
│   ├── descriptions.py      #   Descriptions / DescriptionsItem
│   ├── image.py             #   Image
│   ├── image_gridview.py    #   ImageGridView
│   ├── list_tile.py         #   ListTile
│   ├── log_container.py     #   LogContainer
│   ├── text.py              #   Text / Header_1..5 / Quote / Link / Code / Markdown / Json
│   ├── tree.py             #   Tree / TreeNode（展开 / 复选 / 过滤）
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
│   ├── number_input.py      #   NumberInput（步进 / 精度 / 范围 / 单位）
│   ├── cascader.py          #   Cascader / CascaderNode（多列级联选择）
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
│   ├── step.py              #   Step / StepItem
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
| **Core 核心** | ThemeProvider、ThemeSwitcher、`use_theme`、theme_state；I18nProvider、LanguageSwitcher、`use_t`、`t` |
| **Chart 图表** | BarChart、LineChart、AreaChart、ScatterChart |
| **Display 展示** | Descriptions、Image、ImageGridView、ListTile、LogContainer、Tree、Text / Header_1..5 / Quote / Link / Code / Markdown / Json |
| **Display 媒体** | Audio、AudioPlayer、Video、Pdf |
| **Feedback 反馈** | AlertDialog、Loading、Message、ProgressBar、Toast |
| **Input 输入** | Button、Checkbox / CheckboxGroup、Chip、ColorPicker、DateInput、DateTimeInput、FilePicker / DirPicker、ImagePicker、Input、MultiSelect、NumberInput、RadioGroup、Rating、SearchBar、SegmentedButton、SelectBox、Slider、Switch、Cascader |
| **Layout 布局** | Card、Column、Container、Divider、Expander、GridView、ListView、PageLayout、Row、Stack、Step、Table、Tabs、View |
| **Navigation 导航** | AppBar、BreadCrumb、Paging |

**双范式**：
- **静态组件**（`Button` / `Table` / `Rating` / `Step` / 图表 …）直接继承 Flet 控件，构造即用。
- **交互式组件**（`Input` / `Checkbox` / `Switch` / `SelectBox` / `MultiSelect` / `Pdf` …）
  是 `@ft.component` 函数组件，状态用 hooks 声明，返回值直接进控件树。

## 设计令牌与主题

组件内部不写裸色值 / 裸圆角 / 裸字号 —— 全部取自 `ui.core.tokens`。
这样"换主题"和"换主色"是**框架级**操作，不需要逐个组件改颜色。

### 一、应用主题

用 `ThemeProvider` 包住根视图，`build` 返回你的路由：

```python
import flet as ft
from ui import ThemeProvider, Router, Route

def App() -> ft.Control:
    return ThemeProvider(
        build=lambda: ft.Router(ROUTES, not_found=NotFoundPage, manage_views=False)
    )

def main(page: ft.Page):
    page.render(App)
```

`ThemeProvider` 用 `use_memo(build, [])` 构建子树 —— **切主题不会重建控件树**，
所以表单里已输入的内容不会丢（这一点有真机日志佐证：切到暗色后 `use_state` 的值完好）。

### 二、明暗模式与主色

```python
from ui import theme_state, use_theme, ThemeSwitcher, PRIMARY_SEEDS

@ft.component
def TopBar() -> ft.Control:
    state = use_theme()                    # 订阅全局主题（必须在组件体内）
    ft.Button("切换明暗", on_click=lambda e: state.toggle_mode())
    ft.Button("换主色", on_click=lambda e: state.set_primary(PRIMARY_SEEDS["violet"]))
```

`ThemeSwitcher` 是一个现成的顶栏控件（主色色板 + 明暗开关），可以直接放进去。
`ThemeState` 的三档语义：

| 方法 | 行为 |
|------|------|
| `toggle_mode()` | 永远切到与**当前可见**相反的那档（☀/🌙 按钮用这个，点了必定看得见变化） |
| `cycle_mode()` | `system → light → dark → system` 三态循环（下拉选择用这个） |
| `set_mode(name)` | 直接落到指定档；`"system"` 跟随系统亮度 |
| `set_primary(hex)` | 换品牌色种子，整套 M3 色板重新推导 |

### 三、令牌

**主题感知令牌**（值是 `ft.Colors` 的角色名，由 Flutter 在绘制时解析，
换主题**零 Python 重渲染成本**）：

```python
ft.Colors.PRIMARY, ft.Colors.SURFACE_CONTAINER_LOWEST, ft.Colors.ON_SURFACE_VARIANT
```

**框架解析令牌**（M3 没有的语义角色，由 `ui.core.tokens` 补齐）：

```python
from ui import SPACE, RADIUS, FONT_SIZE, GAP, PAD, elevation, overlay, hairline

SPACE["4"]          # 16 —— 4pt 阶梯，(0,1,2,3,4,5,6,8,10,12,16,20,24,32,40)
RADIUS["lg"]        # 8
FONT_SIZE["body"]   # 13
elevation(2)        # 五档阴影，阴影色用 'shadow,0.1' 角色名，自动跟随明暗
overlay(0.06)       # 'onsurface,0.06' —— 半透明遮罩，明暗自适应
hairline()          # 1px 分隔线
```

**语义色三档**（重要）：一个语义色不能一个值用到底，必须拆成

| 函数 | 用途 | 浅色 | 暗色 |
|------|------|------|------|
| `semantic("success")` | 实心填充（徽标底 / 状态点 / 进度段） | `#047857` | `#34D399` |
| `on_semantic("success")` | 该填充上的前景文字 | `#FFFFFF` | `#04231A` |
| `semantic_text("success")` | 页面上的文字 / 图标 / 细边框 | `#047857` | `#34D399` |

原因：WCAG 对比度实测，原先的 `#10B981` 对白底只有 **2.54:1**、`#F59E0B` 只有 **2.15:1** ——
压白字同样只有 2.54 / 2.15，徽标文字根本读不出来。现在三档各自都 ≥ 4.5:1
（`scripts/_theme_logic.py` 里有断言守着）。

**可用语义角色**：`success` / `warning` / `danger` / `info` / `neutral`。

### 四、一个重要陷阱

在 flet 1.0.5 里，**读取 observable 对象的字段并不会订阅它**。
订阅只发生在三处：组件参数是 `Observable`、`use_state`、`use_context`。

```python
state = theme_state()
mode = state.mode          # ❌ 只是读了一次，不会触发重渲染
state = use_theme()        # ✅ use_context(theme_context)，flet 自动挂订阅
```

同理，**主题感知色（角色名）与 Python 侧算出的色值，代价完全不同**：
角色名交给 Flutter 解析 → 切主题不需要 Python 参与；
而 `semantic("success")` 这类算出来的 hex，组件自己订阅了主题才会更新。

## 多语言（i18n）

### 一、注册文案

`zh-CN` / `zh-TW` / `en-US` 三种语言**框架已内置** —— 不只是语言列表，连
按钮（确定 / 取消 / 清除 / 全选）、日历（月份名 / 星期名 / 每周首日）、分页、
表格、取色器、PDF / 音频播放器这些**组件自己的文案**都已翻好，应用侧只要给自己的文案：

```python
from ui import register_messages

register_messages("zh-CN", {
    "app": {"title": "我的应用"},
    "hello": "你好，{name}",
    "files": {"one": "{n} 个文件", "other": "{n} 个文件"},
    "cities": ["北京", "上海"],        # 成组文案：取用 tr.list("cities")
})
register_messages("en-US", {
    "app.title": "My App",            # 平铺写法和嵌套写法等价
    "hello": "Hello, {name}",
    "files": {"one": "{n} file", "other": "{n} files"},
    "cities": ["Beijing", "Shanghai"],
})
```

键在**装表时**拍平成 `"app.title"` 这样的点号串，查表是一次 `dict.get` ——
不在每次渲染里 `split` 再逐层下钻（一个界面几百条文案，这个差别是可测的）。

### 二、接入页面

```python
@ft.component
def App():
    return I18nProvider(build=MainShell)     # 和 ThemeProvider 并列放根视图

@ft.component
def Toolbar():
    tr = use_t()                              # 订阅：切语言自动重绘
    return ft.Text(tr("app.title"))           # 插值：tr("hello", name="Shawn")

t("app.title")                                # 组件外（日志 / 菜单构造）：不订阅
```

`LanguageSwitcher()` 是现成的顶栏语言菜单（显示母语名、当前项打勾），直接放进 `Row` 即可。

> **为什么必须用 `use_t()`**：flet 只在三处订阅 observable —— 组件参数是 `Observable`、
> `use_state`、`use_context`。在组件体里直接调全局 `t()` 只会读一次，切语言不重绘。

`I18nProvider` 用 `use_memo(build, [])` 复用控件树，所以**切语言不会清空表单内容**
（示例里输入框打几个字再切语言，内容还在）。代价是只有订阅过的组件会更新 —— 这正是
`use_t()` 存在的理由。

### 三、回退与缺键

查表链路是 `当前语言 → 同语言基础档 → 全局兜底`，内置关系为 `繁 → 简 → 英`：
繁体只翻了一半时，剩下的自动落简体，简体再缺就落英文。

缺键**不抛异常**（UI 不该因为漏翻一句就白屏）：返回键名本身，日志里只警告一次，
`missing_keys()` 可查运行期漏了哪些。CI 里打开严格模式，缺键立即报错：

```python
from ui import configure, validate

configure(strict=True)        # 缺键 → KeyError
validate("zh-CN")             # {"zh_TW": ["a.b"], "en_US": []} —— 以简体为基准查缺
```

### 四、格式也是文案

只剩"没翻译"是最容易发现的国际化问题；**"翻译了但格式还是中文的"**才是常态：
英文界面里冒出 `2026 年 9 月`、`1,286 项`、日历表头写死"一二三四五六日"。
这些值和文案一样必须跟着语言走，统一从 `ui.core.format` 取：

```python
from ui import (format_number, format_date, format_time, format_list,
                month_name, weekday_names, first_weekday, calendar_title)

format_number(1286)                    # 1,286
format_date(date(2026, 9, 26))         # 2026-09-26   /  09/26/2026
format_date(d, long=True)              # 2026年9月26日 /  September 26, 2026
calendar_title(2026, 9)                # 2026年9月     /  September 2026
weekday_names()                        # ('一','二',…,'日') / ('Mo','Tu',…)
first_weekday()                        # 中文 0=周一，英文 6=周日
format_list(["A", "B", "C"])           # A、B、C       /  A, B, C
```

组件已经全部走这一层：`DateInput` / `DateTimeInput` / `CalendarPanel` 的标题、
月份格、星期表头、每周首日都由语言决定（`first_day_weekday=None` 即跟随语言），
`Paging` 的总数走千分位，`MultiSelect` 的已选项走本地化连接符。

### 五、扩语言

加一种语言 = 一行 `register_language` + 一份文案；想交给译者，就放 JSON 包：

```python
from ui import Language, load_catalogs, register_language

register_language(Language("ja", "日本語", "Japanese", fallback="en"))
load_catalogs("assets/i18n")     # fr.json / de.json …（含 _meta 时可自动注册语言）
```

```json
{
  "_meta": {"native_name": "Français", "english_name": "French", "fallback": "en"},
  "messages": {"app": {"title": "Mon App"}}
}
```

语言标签写 `zh-CN` / `zh_TW` / `en-US` 都能认：归一规则是**地区优先于文字**
（`zh-CN → zh_CN`、`zh-Hant-TW → zh_TW`、`zh-Hant-HK → zh_TW`），查询时再按
语言 / 文字宽松匹配 —— 只注册了 `en` 时 `en-US` / `en-GB` 都命中 `en`，
注册了 `zh_CN` / `zh_TW` 时 `zh-Hans` / `zh-Hant` 各自落位。

### 六、持久化

用户切过的语言写进本地配置（`FLET_APP_STORAGE_DATA`，或 Windows `%LOCALAPPDATA%\cs-ui`、
macOS `Application Support`、Linux `$XDG_CONFIG_HOME`），**首帧之前同步读回**，
所以启动不会先闪一下默认语言。没切过就跟随系统语言（Windows 读
`GetUserDefaultUILanguage`，其他平台读 `LANG`）。

`MemoryStore()` 用于测试或临时会话；自定义存储只要实现 `read()` / `write()` 两个方法。

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

### 导入是懒加载的

`import ui` 只加载 `flet` 本身（约 0.2s），组件在**第一次被访问**时才从所属子包导入。
改造前全量 star-import 的实测代价是 **1.4s**：`ui.chart` 单它就把 matplotlib + plotly
拖进来（约 0.62s），`ft_init` 里 536 个逐属性反射再花约 0.59s。

```python
import ui              # ~0.2s
ui.Container           # ~35ms，顺带把 ui.layout 导进来（一次性）
ui.BarChart            # 只有真用到图表时才会导入 ui.chart（matplotlib）
```

`dir(ui)` 仍然返回完整名字表，IDE 补全与 `from ui import *` 的行为不变（star-import
本来就意味着"全都要"，它照样会付全款）。名字 → 子包的映射在 `src/ui/_registry.py`，
由脚本生成：

```bash
python scripts/gen_ui_registry.py           # 新增/删除组件后重新生成
python scripts/gen_ui_registry.py --check   # 校验是否与源码一致
```

## 设计原则

- 基于 Flet 原生控件继承，`from ui import *` 即可使用
- 颜色 / 圆角 / 间距 / 字号一律取自设计令牌，不写字面值
- 语义色必须三档（填充 / 填充上的前景 / 页面文字），保证明暗都过 WCAG AA
- 以包的形式组织代码，一个 `.py` 一般只实现一个控件
- 包内代码对外尽量无依赖
- 事件处理函数命名：`on_xx`
- 所有组件采用绝对路径导入
- 基于 Python 3.12+ 语法实现
- 优先使用 flet 1.0.5 声明式 API（`@ft.component` + hooks），少用命令式 `update()`

## 示例

运行演示程序查看所有组件效果（11 个分类页 + 404 页）：

```bash
python examples/demo.py
```

| 路由 | 内容 |
|------|------|
| `/` | 首页导航（按分类进入各页） |
| `/general` | 文本 / 按钮 / 图标 / 标签 |
| `/layout` | 容器 / 列表 / 表格 / 步骤条 |
| `/navigation` | 面包屑 / 标签页 / 分页 |
| `/form` | 输入框 / 选择器 / 滑块 / 评分 |
| `/upload` | 文件 / 目录 / 保存 / 图片 |
| `/feedback` | Toast / 消息 / 对话框 / 进度 |
| `/display` | 日志 / 代码 / 图片 |
| `/charts` | 折线 / 面积 / 柱状 / 散点图 |
| `/media` | 音频 / 视频 / PDF |
| `/about` | 迁移速查与设计说明 |

其他测试文件：

- `examples/test_home.py` — 最小首页
- `examples/test_form.py` — 表单组件
- `examples/test_feedback.py` — 反馈组件（对话框、消息提示、加载、进度条）
- `examples/test_i18n.py` — 多语言（顶栏切换简 / 繁 / 英，实时跟随）
- `examples/test_chart.py` — 图表组件
- `examples/test_line_chart.py` — 折线图
- `examples/test_button.py` — 按钮变体
- `examples/test_minimal.py` / `test_simple.py` — 最小示例
- `examples/my_control.py` — 自定义控件示例

## MCP 服务（ui-mcp）

给 AI agent 用的组件库 API 服务，思路同 [flet-mcp](https://flet.dev/docs/cookbook/flet-mcp/)：
模型对 cs-ui 的记忆必然是过期的、而且是编造的，与其让它猜，不如让它**查**。

索引是**运行时内省**出来的（`@ft.control` 会把构造器拍平、`@ft.observable`
会造代理类，静态扫描看不到真实签名），随包分发三份 JSON，服务期不 import `ui`：

| 产物 | 内容 |
|------|------|
| `data/api.json` | 约 80 个组件、60 个函数、9 个枚举，外加组件继承到的 40+ 个外部类成员表 |
| `data/examples.json` | `examples/demo.py` 拆页 + **每个组件的真实调用片段** |
| `data/docs.json` | README / TODO / 项目记忆切段，可检索 |

工具（12 个，可用 `UI_MCP_ENABLE_{API,ICONS,EXAMPLES,DOCS,GUIDE}=0` 关掉整组）：

| 工具 | 用途 |
|------|------|
| `get_api(name, member=, query=, format=)` | 主验证器。查组件/数据类/函数/枚举/外部基类；`query` 能搜继承链 |
| `list_components(category=, pattern=, kind=)` | 按分类 / 范式（static / observable / function）浏览 |
| `search_components(query)` | 中英文语义检索（"翻页表格" → Table） |
| `get_enum` / `search_enum_members` / `enum_has_member` | 枚举查证 |
| `find_icon(query)` | 按概念找 Material 图标（内置中文映射） |
| `search_examples` / `get_example` | 找 demo 页、读真实源码（支持分段） |
| `search_docs` / `get_doc` | 搜文档段落 |
| `get_guidelines(topic)` | **经验条款**：frozen 树、`page.render`、颜色串顺序、令牌… |

```bash
pip install -e ".[mcp]"      # 装 fastmcp 依赖
ui-mcp                        # stdio 服务（默认子命令）
ui-mcp build                  # 改了 src/ui 之后重建索引
ui-mcp check                  # 索引是否落后于源码
ui-mcp guide frozen           # 终端里直接看经验条款
```

MCP 客户端配置（Claude Desktop / Cursor / WorkBuddy…）：

```json
{
  "mcpServers": {
    "ui": { "command": "ui-mcp" }
  }
}
```

> ⚠️ 改了组件后记得 `ui-mcp build`；`ui-mcp check` 会列出比索引新的文件。
> 新增组件要往 `src/ui_mcp/aliases.py` 补一行中文别名，否则中文搜不到它（英文名不受影响）。

## 参考资料

- <https://github.com/flet-dev/examples.git>
- <https://flet.dev/>
