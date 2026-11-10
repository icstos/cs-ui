# CS-UI

[![Flet](https://img.shields.io/badge/Flet-1.1.2-blue)](https://flet.dev)
[![Python](https://img.shields.io/badge/Python-3.12%2B-green)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

基于 [Flet](https://flet.dev/) 的 Python UI 组件库：72 个组件、一套算出来的配色、一套排印律。

## 特点

- **颜色是算出来的** — 一个品牌色经 `ui.core.palette` 展开成 46 个 M3 角色（明暗各一套）。
  不走 `color_scheme_seed`：Flutter 的 `tonalSpot` 会把 `#1F6FEB` 推成 `#465D91`，
  品牌蓝被抽掉一半彩度。
- **前景按对比度解，不按档位取** — 11 档色阶按对数梯度排明度，前景色二分求解明度，
  正文 ≥ 4.5:1、大标题 ≥ 3:1。于是"成功"和"警告"这两个明度天差地别的色相，
  落在纸上却是同一份视觉重量。
- **排印是律，不是手挑的数** — 字号（11 / 12 / 14 / 16 / 20 / 24 / 28 / 36）推出另外三件：
  行高 `φ − 0.018 × (size − 14)`、字距按 em 做光学补偿、字重四档。
  组件里不写 `height=` / `letter_spacing=`，四件套只能成套下发。
- **间距走 4px 网格，行高不走** — `RHYTHM` 六级（4 / 8 / 12 / 20 / 32 / 52，相邻比 1.4~2.1
  贴着 φ）管块与块之间；正文行高 22.65px 夹在 20 与 24 之间，量化到网格就是偏离 φ 一档。
- **响应式只有跨档才重绘** — 六个断点（0 / 576 / 768 / 992 / 1200 / 1400，与 `ResponsiveRow`
  逐项相同）归成 compact / medium / expanded 三档。精确宽度放在不可变的 `Viewport` 快照里，
  更新它不触发任何重绘，拖动窗口不会把界面拖成幻灯片。
- **一套配色，五个分层** — 表面 / 前景 / 交互 / 强调 / 数据各用一种表达手段，不跨层借用。
  "成功"按钮和"成功"提示条是同一个绿；图表分类色与热力图色阶由品牌色按 OKLCH 派生。
- **双范式** — 静态组件继承 Flet 原生控件（`Button(ft.Button)`），交互式组件是
  `@ft.component` 函数，状态用 `use_state` / `use_memo` / `use_effect` 声明。
- **国际化是真的翻完了** — 简中 / 繁中 / 英三语，按钮、日历、分页、取色器、播放器这些
  **组件自己的文案**都已翻好，还包括日期 / 数字 / 列表连接符的格式。

## 环境要求

- Python >= 3.12
- flet[all] >= 1.1.2, < 1.2
- flet-code-editor / flet-charts / flet-video / flet-audio / flet-webview

## 安装

```bash
uv pip install cs-ui          # 或
pip install -e .              # 从源码，可编辑模式
```

## 快速开始

```python
import flet as ft
from ui import Button, Card, Checkbox, Column, Container, Input, Row, Text


@ft.component
def HomePage() -> ft.Control:
    name = ft.use_ref(lambda: Input(label="姓名", value="Shawn", width=260)).current
    agree = ft.use_ref(lambda: Checkbox(label="我已阅读")).current

    return Container(
        expand=True,
        padding=24,
        content=Column(
            spacing=16,
            controls=[
                Text("CS UI", size=24, weight=ft.FontWeight.BOLD),
                name.ui(),
                agree.ui(),
                Button("点我", on_click=lambda _: print("clicked!")),
            ],
        ),
    )


def main(page: ft.Page) -> None:
    page.title = "CS UI Demo"
    page.render(HomePage)


if __name__ == "__main__":
    ft.run(main)
```

### 三条必须知道的规矩

1. **根视图走 `page.render` + `Router(manage_views=False)`，不要用 `page.render_views`。**
   视图栈会把整个页面浮层盖住 —— `page.overlay` 里挂什么都是零像素、`page.show_dialog`
   同样失效，**而且不报错**（Python 侧 `len(page.overlay)` 正确、回调照常触发）。
2. **`ft.View` 不能当普通控件用。** 塞进控件树，Flutter 侧反复抛 `Bad state: No element`，
   整页变灰块。同理 `ft.AppBar` 只能挂 `View.appbar`，顶栏请用 `Container` + `Row` 自绘。
3. **交互式组件必须构造后调 `.ui()`。** `Input` / `Checkbox` / `Switch` / `SelectBox` /
   `MultiSelect` 由 `@ft.observable` 数据对象 + `@ft.component ui()` 组成，直接放进控件树
   只会得到一块空白。

若宿主必须用视图栈（`manage_views=True`），`MultiSelect` 会自动降级为流内展开
（面板占布局高度、把下方内容推下去），也可用 `float_panel=False` 显式关闭浮层。

## 模块划分

| 子包 | 装什么 |
|---|---|
| `ui.core` | 底座：`tokens`（设计令牌）、`palette`（配色引擎）、`typography`（排印律）、`theme`、`i18n`、`format`、`responsive`、`doc`（文档套件） |
| `ui.chart` | `BarChart` / `LineChart` / `AreaChart` / `ScatterChart`，共用一套数据解析与派生配色 |
| `ui.display` | `Text` 系列（`Header_1..6` / `Quote` / `Link` / `Code` / `Markdown` / `Json`）、`Calendar`、`Carousel`、`Heatmap`、`Descriptions`、`Tree`、`ListTile`、`Image`、`LogContainer` |
| `ui.display.media` | `Audio` / `AudioPlayer` / `Video` / `Pdf` |
| `ui.feedback` | `AlertDialog`、`Message`（主动操作的回执）、`Notification`（系统级通报）、`Loading`、`ProgressBar` |
| `ui.input` | 全部表单控件：`Input`、`Checkbox`、`Radio`、`Switch`、`SelectBox`、`MultiSelect`、`Cascader`、`Transfer`、`Slider`、`Rating`、`Chip`、`ColorPicker`、`DateInput`、`DateTimeInput`、`FilePicker`、`ImagePicker`、`NumberInput`、`SearchBar`、`SegmentedButton`、`Button` |
| `ui.layout` | `PageLayout`、`Grid`、`Card`、`Column` / `Row` / `Stack` / `Container`、`Table`（含分页）、`Tabs`、`Step`、`Expander`、`Divider` |
| `ui.navigation` | `AppBar`、`BreadCrumb`、`Menu`、`Pagination` |
| `ui.utils` | `CodeEditor`、`CodeView`（带折叠与复制的代码展示） |

精确定位某个组件、函数或令牌属于哪个模块，查 `ui-mcp` 的 `list_components` 比翻目录快。

## 设计令牌与主题

组件内部不写裸色值 / 裸圆角 / 裸字号，全部取自 `ui.core.tokens`。所以"换主题"和"换主色"
是框架级操作，不需要逐个组件改颜色。

### 一、应用主题

```python
import flet as ft
from ui import ThemeProvider, Router, Route

def App() -> ft.Control:
    return ThemeProvider(
        build=lambda: ft.Router(ROUTES, not_found=NotFoundPage, manage_views=False)
    )
```

`ThemeProvider` 用 `use_memo(build, [])` 构建子树：切主题不重建控件树，表单里已输入的内容
不会丢。

### 二、明暗与主色

```python
from ui import theme_state, use_theme, ThemeSwitcher, PRIMARY_SEEDS

@ft.component
def TopBar() -> ft.Control:
    state = use_theme()                    # 订阅全局主题（必须在组件体内）
    ft.Button("切换明暗", on_click=lambda e: state.toggle_mode())
    ft.Button("换主色", on_click=lambda e: state.set_primary(PRIMARY_SEEDS["violet"]))
```

| 方法 | 行为 |
|---|---|
| `toggle_mode()` | 永远切到与**当前可见**相反的那档（点了必定看得见变化） |
| `cycle_mode()` | `system → light → dark → system` |
| `set_mode(name)` | 直接落档；`"system"` 跟随系统亮度 |
| `set_primary(hex)` | 换品牌色：46 个角色按新色相重算，明暗两套一起下发 |

### 三、令牌

**主题感知令牌**（值是角色名，Flutter 在绘制时解析，换主题零 Python 重渲染）：

```python
ft.Colors.PRIMARY, ft.Colors.SURFACE_CONTAINER_LOWEST, ft.Colors.ON_SURFACE_VARIANT
```

**框架解析令牌**（M3 没有的语义，由 `ui.core.tokens` 补齐）：

```python
from ui import SPACE, RADIUS, FONT_SIZE, elevation, hairline, state_layer, selected_layer, disabled_layer

SPACE["4"]                  # 16 —— 4pt 阶梯 (0,1,2,3,4,5,6,8,10,12,16,20,24,32,40)
RADIUS["lg"]                # 8
FONT_SIZE["body"]           # 14 —— 其余档位 11 / 12 / 16 / 20 / 24 / 28 / 36
elevation(2)                # 五档阴影，阴影色走 'shadow' 角色，自动跟随明暗
state_layer("hover")        # 'onsurface,0.08'
selected_layer("normal")    # 'primary,0.12'
disabled_layer()            # 'onsurface,0.38' —— 禁用文字 / 图标
disabled_layer("container") # 'onsurface,0.12' —— 禁用控件的底 / 边
hairline()                  # 1px 分隔线
```

**排印令牌**（`ui.core.typography`）：

```python
from ui import typography as tp

tp.leading(14)              # 1.618 —— 正文拿到 φ，不用手填 height
tp.leading(36)              # 1.222 —— 标题该紧
tp.leading(11)              # 1.672 —— 小字该松
tp.tracking(14)             # 0.0    —— 字距以 em 记，±0.025 内做光学补偿
tp.tracking(36)             # -0.80  —— 大字收紧（-0.022em）
tp.tracking(30)             # -0.62  —— 字阶外按 em 在相邻两档间插值
tp.role("body")             # Role(size=14, leading=1.618, tracking=0.0, weight=w400)
tp.text_style("title", color=..., weight=...)   # 组件侧唯一该用的排字入口
tp.RHYTHM["section"]        # 32 — hair 4 / block 8 / paragraph 12 / group 20 / section 32 / page 52
tp.LEADING_PROSE            # 1.75 —— 长文正文比 UI 正文松一档
tp.LEADING_CODE             # 1.55
tp.cols("thirds")           # 12 栏上的 2:1（8 + 4）
tp.cols("golden")           # 7 + 5（φ:1）
tp.cols("aside")            # 4 + 8 —— 说明左、演示右
```

**语义色三档**：一个语义色不能一个值用到底。

| 函数 | 用途 | 浅色 | 暗色 |
|---|---|---|---|
| `semantic("success")` | 实心填充（徽标底 / 状态点 / 进度段） | `#007F5B` | `#38B98B` |
| `on_semantic("success")` | 该填充上的前景文字 | `#FFFFFF` | `#002014` |
| `semantic_text("success")` | 页面上的文字 / 图标 / 细边框 | `#007F5B` | `#38B98B` |

早先手挑的 `#10B981` 对白底只有 **2.54:1**、`#F59E0B` 只有 **2.15:1**，压白字同样读不出来。
现在每个语义色由 `palette.semantic_scale` **解到同一目标对比度**（浅色 5.0:1、深色 7.0:1），
四个角色落在同一份视觉重量上（亮度极差 < 0.02）。深色模式的前景是**深墨**而不是白字 ——
`#F28948` 压白字只有 2.0:1，压深墨是 7.0:1。可用角色：`success` / `warning` / `danger` /
`info` / `neutral`。

**强调角色四联**：同一个强调色有四种用法，取值不可能一样。

| 函数 | 用途 |
|---|---|
| `accent_fill(role)` | 实底（主按钮、徽标、进度段） |
| `accent_on(role)` | 实底上的前景 |
| `accent_text(role)` | 压在**表面色**上的文字 / 图标 |
| `accent_soft(role)` | 12% 淡底，小面积（图标底座、计数徽标） |
| `accent_wash(role)` | 8% 淡底，大面积（对话框标题带、提示条整行） |

`role` 取 `primary` / `secondary` / `tertiary`（M3 角色，Flutter 运行时解析，切主题不重建控件）
或五个语义角色。淡底按**面积**分两档：同一个透明度，面积越大看着越重。

### 四、色板

```python
from ui.core.palette import build_scheme, tonal

build_scheme("#1F6FEB", "light")   # 46 个角色一次算清
tonal("#1F6FEB")[50]               # '#F4F8FF' —— 11 档色阶（50…950）
tonal("#1F6FEB")[600]              # '#3271D7'
```

三条规则撑着它：明度按**对数梯度**排十一个档（相邻约差 0.075，符合韦伯定律，"淡一档"在
任何色相上都是同一种淡）；彩度走**钟形包络**（50 档 0.10 → 500 档 1.00 → 950 档 0.50）；
前景**按对比度二分**求明度，不按"第几档"取 —— 同一个 tone 上黄色与蓝色的相对亮度能差三倍，
"等 tone"从来不等于"等可读"。中性色注入 215° 冷蓝相再掺一丝主色相，是冷灰而不是死灰。

**配色分层**，每层只有一种表达手段，不要跨层借用：

| 层 | 用什么 | 谁解析 |
|---|---|---|
| 表面 | `SURFACE` / `SURFACE_CONTAINER_LOWEST..HIGHEST` | Flutter |
| 前景 | `ON_SURFACE` / `ON_SURFACE_VARIANT` / `OUTLINE` / `OUTLINE_VARIANT` | Flutter |
| 交互 | `state_layer()` / `selected_layer()` / `disabled_layer()` | Flutter |
| 强调 | `accent_fill/on/text/soft/wash()` | 混合 |
| 数据 | `chart_palette()`、热力图色阶（`ui.core.color` 派生） | Python |

数据层的分类色由品牌色**按 OKLCH 派生**：首色与品牌同色相、整张表等亮度、色相环等间隔 45°。
换主色时图表跟着换，热力图末级正好落在品牌色板的锚色上。

### 五、一个陷阱

在 flet 1.x 里，**读取 observable 对象的字段并不会订阅它**。订阅只发生在三处：组件参数是
`Observable`、`use_state`、`use_context`。

```python
state = theme_state()
mode = state.mode          # ❌ 只是读了一次，不会触发重渲染
state = use_theme()        # ✅ 自动挂订阅
```

同理，**角色名与 Python 侧算出的 hex 代价完全不同**：角色名交给 Flutter 解析，切主题不需要
Python 参与；`semantic("success")` 这类 hex 只有在组件订阅了主题后才会更新。

## 多语言

### 一、注册文案

`zh-CN` / `zh-TW` / `en-US` 已经内置，应用侧只要给自己的文案：

```python
from ui import register_messages

register_messages("zh-CN", {
    "app": {"title": "我的应用"},
    "hello": "你好，{name}",
    "files": {"one": "{n} 个文件", "other": "{n} 个文件"},
    "cities": ["北京", "上海"],        # 成组文案：tr.list("cities")
})
register_messages("en-US", {
    "app.title": "My App",            # 平铺与嵌套等价
    "hello": "Hello, {name}",
    "files": {"one": "{n} file", "other": "{n} files"},
})
```

键在**装表时**拍平成 `"app.title"` 这样的点号串，查表是一次 `dict.get` —— 不在每次渲染里
`split` 再逐层下钻。

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

`LanguageSwitcher()` 是现成的顶栏语言菜单。**必须用 `use_t()` 而不是全局 `t()`** ——
理由同上一节的订阅陷阱：直接调 `t()` 只读一次，切语言不重绘。`I18nProvider` 用
`use_memo` 复用控件树，所以切语言也不会清空表单内容。

### 三、回退与缺键

查表链路是 `当前语言 → 同语言基础档 → 全局兜底`，内置关系 `繁 → 简 → 英`。缺键**不抛异常**
（UI 不该因为漏翻一句就白屏）：返回键名本身、日志只警告一次、`missing_keys()` 可查。
CI 里打开严格模式：

```python
from ui import configure, validate

configure(strict=True)        # 缺键 → KeyError
validate("zh-CN")             # {"zh_TW": ["a.b"], "en_US": []}
```

### 四、格式也是文案

只剩"没翻译"是最容易发现的国际化问题；**"翻译了但格式还是中文的"**才常见：英文界面里冒出
`2026 年 9 月`、`1,286 项`、日历表头写死"一二三四五六日"。这些统一从 `ui.core.format` 取：

```python
from ui import format_number, format_date, calendar_title, weekday_names, first_weekday, format_list

format_number(1286)                    # 1,286
format_date(date(2026, 9, 26))         # 2026-09-26   /  09/26/2026
format_date(d, long=True)              # 2026年9月26日 /  September 26, 2026
calendar_title(2026, 9)                # 2026年9月     /  September 2026
weekday_names()                        # ('一','二',…,'日') / ('Mo','Tu',…)
first_weekday()                        # 中文 0=周一，英文 6=周日
format_list(["A", "B", "C"])           # A、B、C       /  A, B, C
```

`DateInput` / `DateTimeInput` / `CalendarPanel` 的标题、月份格、星期表头、每周首日都由语言
决定（`first_day_weekday=None` 即跟随语言）；`Pagination` 的总数走千分位。

### 五、扩语言与持久化

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

语言标签写 `zh-CN` / `zh_TW` / `en-US` 都认，归一规则是**地区优先于文字**（`zh-Hant-HK → zh_TW`），
查询时按语言 / 文字宽松匹配 —— 只注册了 `en` 时 `en-US` / `en-GB` 都命中。

用户切过的语言写进本地配置（`FLET_APP_STORAGE_DATA`，或 Windows `%LOCALAPPDATA%\cs-ui`、
macOS `Application Support`、Linux `$XDG_CONFIG_HOME`），**首帧之前同步读回**，不会先闪默认
语言。没切过就跟随系统。`MemoryStore()` 用于测试，自定义存储只需实现 `read()` / `write()`。

## 导入

```python
from ui import Button, Card, Column, Container, Divider, Row, Text, TextField, ft
```

`ui.__all__` 是 780 个名字（flet 全部公开名 + 各子包 `__all__` + 子模块名 + `ft`）。

**导入是懒的**：`import ui` 只加载 `flet` 本身（约 0.2s），组件在第一次被访问时才从所属子包
导入。全量 star-import 的实测代价是 **1.4s** —— `ui.chart` 单它就把 matplotlib + plotly 拖进来
（约 0.62s），536 个逐属性反射再花约 0.59s。

```python
import ui              # ~0.2s
ui.Container           # ~35ms，顺带把 ui.layout 导进来（一次性）
ui.BarChart            # 只有真用到图表时才会导入 ui.chart
```

`dir(ui)` 仍返回完整名字表，IDE 补全与 `from ui import *` 行为不变。名字 → 子包的映射在
`src/ui/_registry.py`，由脚本生成，**改了组件必须重生成**：

```bash
python scripts/gen_ui_registry.py           # 新增 / 删除组件后
python scripts/gen_ui_registry.py --check   # 校验是否与源码一致
```

## 回归

一致性靠"记得跑"是守不住的，所有检查都在一个入口里：

```bash
python scripts/check_all.py                 # 31 项 / 约 53s
python scripts/check_all.py --stage fast    # 只跑静态门禁与令牌审计（改样式时够用）
python scripts/check_all.py --stage visual  # 真机截图 + 灰块检测（会开窗口）
```

| 检查 | 守住什么 |
|---|---|
| `ruff --select F821,F811,F841,F401` | 未定义名 / 重复定义 / 无用局部变量与导入 |
| `audit_consistency.py` | 裸色值、字号 / 图标 / 圆角越界、奇数留白、`OUTLINE` 当文字色、暗色失效色、静态色名 |
| `_tokens_logic.py` | 令牌契约：门面一致、刻度单调、状态层递进、强调四联与 `SEMANTIC` 同源 |
| `_palette_logic.py` | 色板契约：46 角色齐全、11 档等步长且色相不漂、17 组对比度达标（8 种子 × 2 模式）、语义四色重量一致 |
| `_color_logic.py` | 配色引擎：OKLCH 往返无损、分类色等亮度、色相间距、色阶单调 |
| `_typography_logic.py` | 排印律：行高公式、字距在字阶上与档位逐项相等、六级标题单调、86 条 |
| `_responsive_logic.py` | 断点表与 `ResponsiveRow` 逐项相同、档位单调且边界左闭右开、同档不重绘、限宽取 `min()`、私有字段不漏进序列化树 |
| `_*_logic.py` | 各组件纯逻辑（状态推导、取值边界、回调、冻结树降级） |
| `_ui_mcp_logic.py` | MCP 索引契约：范式与代码一致、常量只收底座、同名可分辨、中文别名不指向已删符号 |
| `_doc_check.py` | 72 个组件的 SPEC / 示例 / API 完整性（示例真跑一遍） |
| `gen_ui_registry.py --check` | `ui.__all__` 与注册表不漂移 |
| `build_docs_i18n.py --check` | 站点三语文案同步 |

**测试断言写"规则"不写"色值"**：写死 `#047857` 的断言在换色相时会假报警，应断言
"四色对比度极差 < 0.3"这类不变量。

## 文档站与示例

组件文档站本身就是示例库：72 个组件各自带可运行示例与 API 说明，路由即页面。

```bash
python docs/main.py
```

| 路由 | 内容 |
|---|---|
| `/` | 首页 |
| `/docs/quickstart` `/docs/architecture` `/docs/theming` `/docs/i18n` `/docs/responsive` | 指南 |
| `/components/<分类>/<组件>` | 定义 / 组件构成 / 何时使用 / 示例 / API / 备注 |
| `/about` | 关于 |

改完样式想确认"窗口里真的画出来了"（灰块 = Flutter 端渲染失败，黄色斜纹 = 文字撑破了固定
高度的盒子）：

```bash
python scripts/_visual_check.py                    # 13 个代表页，浅色
python scripts/_visual_check.py --mode dark        # 暗色
python scripts/_visual_check.py --scroll 14 --routes /components/layout/table
```

`examples/` 下是最小可运行宿主（`test_form.py` / `test_feedback.py` / `test_i18n.py` /
`test_chart.py` …），`scripts/ui_demo.py` 是旧的单文件全量演示。

## MCP 服务（ui-mcp）

给 AI agent 用的组件库 API 服务，思路同 [flet-mcp](https://flet.dev/docs/cookbook/flet-mcp/)：
模型对 cs-ui 的记忆必然是过期的、而且是编造的，与其让它猜，不如让它**查**。

索引是**运行时内省**出来的（`@ft.control` 把构造器拍平、`@ft.observable` 造代理类，静态扫描
看不到真实签名），随包分发三份 JSON，服务期不 import `ui`：

| 产物 | 内容 |
|---|---|
| `data/api.json` | 95 个组件、28 个数据类、185 个函数、8 个枚举、52 个令牌常量，外加组件继承到的 45 个外部类成员表 |
| `data/examples.json` | `examples/` 拆页 + 每个组件的真实调用片段 |
| `data/docs.json` | README / TODO / 项目记忆切段，可检索 |

12 个工具，可用 `UI_MCP_ENABLE_{API,ICONS,EXAMPLES,DOCS,GUIDE}=0` 关掉整组：

| 工具 | 用途 |
|---|---|
| `get_api(name, member=, query=, format=)` | 主验证器。查组件 / 数据类 / 函数 / 枚举 / 令牌常量 / 外部基类 |
| `list_components(category=, pattern=, kind=)` | 按分类 / 范式（static / observable / function）浏览 |
| `search_components(query)` | 中英文语义检索（"翻页表格" → Table，"间距" → SPACE） |
| `get_enum` / `search_enum_members` / `enum_has_member` | 枚举查证 |
| `find_icon(query, family=)` | 按概念找图标（Material + Cupertino，内置中文映射） |
| `search_examples` / `get_example` | 找示例页、读真实源码 |
| `search_docs` / `get_doc` | 搜文档段落 |
| `get_guidelines(topic)` | **经验条款**：frozen 树、STRETCH 陷阱、响应式、色板、令牌、验证脚本 |

```bash
pip install -e ".[mcp]"      # 装 fastmcp 依赖
ui-mcp                        # stdio 服务（默认子命令）
ui-mcp build                  # 改了 src/ui 之后重建索引
ui-mcp check                  # 索引是否落后：源码 mtime + ui/flet 版本漂移
ui-mcp guide responsive       # 终端里直接看经验条款
```

```json
{
  "mcpServers": {
    "ui": { "command": "ui-mcp" }
  }
}
```

新增组件要往 `src/ui_mcp/aliases.py` 补一行中文别名，否则中文搜不到它。

## 参考

- <https://flet.dev/>
- <https://github.com/flet-dev/examples>
