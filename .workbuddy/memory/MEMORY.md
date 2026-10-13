# CS-UI 项目长期记忆

> 详细内容按主题拆到附录，点标题进：
> [flet-1x-gotchas.md](flet-1x-gotchas.md)（flet 1.x API 差异与真机踩坑）
> [probe-tooling.md](probe-tooling.md)（验证工装与真机探针的用法）

## 环境
- Python：`C:/Softwares/Python-V3.12.10.x64/python.exe`（**不要用裸 `python`**——shell 里裸
  `python` 指向托管的 3.13.12，**没装 flet**，会报 `ModuleNotFoundError: No module named 'flet'`）
- **flet 1.0.4**（已装）。`pyproject.toml` 已收紧为 `flet[all]~=1.0.4` + 补上漏声明的 `flet-webview`
- 屏幕 3840×2160，DPR 1.75（截图尺寸 = 逻辑尺寸 × 1.75）；**页面内容原点 = 客户区 (10,10)**
- 跑 demo：`python examples/demo.py`；跑脚本要先 `sys.path.insert(0, "src")`

## 规模（2026-10-12）
70 个组件模块 / 12660 行。分布：input 19、layout 14、display 9、core 7、chart 5、feedback 5、
navigation 3、utils 3。

## 设计令牌 + 主题（2026-09-27 起）
`src/ui/core/tokens.py` + `src/ui/core/theme.py`。组件里**不写裸色值 / 裸圆角 / 裸字号**。

- **主题感知令牌** = `ft.Colors` 角色名，Flutter 绘制时解析 → 切主题**零 Python 重渲染**
- **框架解析令牌**：M3 没有的语义角色。`SPACE`（4pt 阶梯 15 档）/ `RADIUS`（7 档）/
  `FONT_SIZE`（7 档）/ `DURATION` / `elevation(0..4)` / `overlay(a)` / `scrim()` / `hairline()`
- **语义色必须三档**（实测 WCAG：`#10B981` 对白底仅 **2.54:1**、`#F59E0B` 仅 **2.15:1**，
  压白字同样读不出来）：
  `semantic(role)` 实心填充 / `on_semantic(role)` 填充上的前景 / `semantic_text(role)` 页面文字。
  三档在明暗下各自 ≥ 4.5:1，`scripts/_theme_logic.py` 有断言守着。角色：
  `success` / `warning` / `danger` / `info` / `neutral`
- **换主色**：`ft.Theme(color_scheme_seed=...)` 一个种子推导整套 M3 色板 →
  `theme_state().set_primary(PRIMARY_SEEDS["violet"])`。8 个种子见 `PRIMARY_SEEDS`
- `ThemeProvider(build=...)` 用 `use_memo(build, [])` 构建子树 → **切主题不重建控件树，
  表单已输内容不丢**（真机日志确认 `use_state` 值完好）
- `ThemeState` 三档语义别混：`toggle_mode()` = 切到与**当前可见**相反那档（☀/🌙 按钮，
  点了必定看得见变化）；`cycle_mode()` = `system→light→dark→system`（下拉用）；
  `set_mode("system")` 跟随系统亮度

## 项目约定
- `from ui import *` 导出 flet 全部内容 + 所有 CS UI 组件
- **不要在 `src/ui/__init__.py` 写 `__name__ = "cs-ui"`**：会让 `from ui import X` 在 X 缺失时
  报出误导性的 `ModuleNotFoundError: No module named 'cs-ui'`。产品名走 `__pkg_name__`
- 组件统一用**绝对路径导入**；事件回调命名 `on_xx`
- **两套组件范式**：
  - *静态组件*：直接继承 flet 控件，构造即用（`Button` / `Table` / `Rating` / `Timeline` / 图表）
  - *交互式组件*：`@ft.observable` 数据对象 + `@ft.component ui()`；**必须调用 `.ui()`** 放进
    控件树，否则渲染成空白或灰块（`Input` / `Checkbox` / `Switch` / `SelectBox` / `MultiSelect` …）
    —— 迁移到纯 `@ft.component` + hooks 风格是 TODO 里的 Batch 2
  - ⚠️ **`ui()` 只能在组件渲染上下文里调用**（`@ft.component` 或 `page.render` 内），
    在 `main()` 函数体里直接调会抛 `No current renderer is set`。宿主要包一层
    `@ft.component def Body()`。
- **`examples/demo.py` 用的是显式具名导入**（`from ui import (...)`），**不是** `from ui import *`
  —— 新增组件必须手动加进导入清单，否则 `NameError` 且路由探针会报 `missing=NN`
- **已下线组件**：`ECharts`（`display/echarts.py` 仅 `# TODO`）——已从包导出移除，别再引用。
  `ColorPicker` 曾被下线，**2026-09-26 已从零重构完成并恢复导出**
- **`Pdf`**（`display/media/pdf.py`）在 git 里长期是**空文件**却一直被导出 + 被 demo import
  → `from ui import Pdf` 早就是坏的、demo 长期跑不起来。**2026-09-27 已从零实现**

## 架构：选择器家族共用外壳
`input/panel_field.py` 的 `PanelField` 混入 = 「折叠态输入框 + 页面浮层面板」的通用外壳
（圆角 / 描边 / 阴影 / 定位 / 外点收起 / 清空按钮 / Label 排版），外加模块级
`place_panel()` / `panel_shell()` 与全套尺寸配色常量。
`input/calendar_panel.py` 的 `CalendarPanel(PanelField)` 只管月历并**重导出**旧名保持兼容；
`DateInput` / `DateTimeInput` / `ColorPicker` 都是 `class X(PanelField, Label)`。
**新增"框 + 浮层面板"类组件一律继承 `PanelField`**，别再复制外壳代码。
两个 `calendar_panel` / `panel_field` 是**纯混入、没有 `App()`**，
`_ui_audit.py` 对它们报 `no attribute 'App'` 属预期，不是回归。

## 三条最容易再踩的（详见附录）
1. **frozen 控件**：`@ft.component` / `page.render` 构建的树禁止命令式 `control.update()` →
   hover 高亮一律用 `ft.Container.ink` + `ink_color` 交给 Material 绘。
   **`@ft.control` 子类挂在 `page.render` 树上时同样 frozen** —— 老组件里的
   `self.update()` 一律要改成 `use_state`（`Table` 已这样重写，见下）
2. **无界高度里不能 `expand`**：行内要"等高 + 竖直拉伸"必须 `ft.Row(intrinsic_height=True)`；
   画绝对定位的线用 `Stack` + `Container(left=/top=/bottom=/width=)`
3. **渲染路径统一 `page.render` + `Router(routes, manage_views=False)`**：视图栈会把
   `page.overlay` / `page.show_dialog` 整层盖住（零像素、不报错），下拉面板全失效；
   代价是页面不能返回 `ft.View`，顶栏用 `Container + Row` 自绘

## Table 的范式（已重写，是其他组件的样板）
`src/ui/layout/table.py`。原为 `@ft.control` 子类 + `self.update()` 换页 →
在 `page.render` 树上**必崩** `Frozen control cannot be updated.`。
现为 `@ft.component` 函数组件 + `TableState`（`@ft.observable @dataclass`）：
页码是 `use_state`，行数据由页码**纯函数派生**（`page_slice` / `columns` / `build_rows`）。
新增这类组件照这个结构抄，别再写 `self.update()`。

三条必须遵守：
- **`use_state` 的初值参数每次渲染都求值** → 用 `use_ref` 锁死首次值，
  否则外部 observable 漂移会形成"没人点、页码自己跳"的循环
- 回写外部 observable 放 `use_effect` **且只在值不同时写**，无条件写 = 循环
- `@ft.component` **不保留自身类型**，按类型断言的探针要改成断言它渲染出的真实控件
  （`_demo_route_probe` 的 `/layout` 期望已从 `Table` 改成 `Card`+`DataTable`）

## 颜色串（血泪，务必记牢）
flet / Flutter 的 8 位十六进制是 **`#AARRGGBB`（透明度在前）**，与 CSS 的 `#RRGGBBAA` **相反**。
组件的 `value` 必须回 **flet 原生色串**：不透明 `"#RRGGBB"`，带透明度用
`ft.Colors.with_opacity(a, "#RRGGBB")` 的产物 `"#RRGGBB,0.8"`。需要 CSS 顺序的 8 位时
另给 `hex8` 属性。透明度取 **3 位小数** 才能让 256 档往返零漂移。
`ft.Colors` 里只有 **Material 基础色名**（`red` / `teal` …）能解析；带色阶的（`red500`）、
强调色（`redAccent`）、**主题角色**（`primary` / `onsurface`）Python 侧拿不到 RGB，
必须走"原值透传"降级路径（把原对象直接交给 Flutter）。

## 验证（改完必须跑，详见附录）
Python 侧不抛异常 ≠ Flutter 侧渲染成功 —— 裸字符串混进 `controls` 只会渲染成灰色 ErrorWidget。

```
python scripts/_theme_logic.py            # 令牌 + 主题逻辑（含 WCAG 对比度断言）
python scripts/_table_logic.py            # Table 分页纯函数逻辑（34 条）
python scripts/_color_picker_logic.py     # 逻辑单测（本项目范式：scripts/_*_logic.py）
python scripts/_ui_audit.py <module>      # 单模块渲染审计（@@OK@@）
python scripts/smoke_test.py examples.demo main --routes /,/general,/layout,...
python scripts/_demo_route_probe.py      # 路由 + 关键控件归属（bad=0 且 missing=0）
python scripts/_visual_check.py --pages HomePage GeneralPage   # 分批跑！12 页一次跑会被超时杀
python scripts/_locate.py <截图> --buttons # 按像素特征定位页码按钮 → 逻辑坐标
python scripts/_probe_demo.py --app <宿主> --title "<宿主设的 page.title>" \
    --once --do click:x,y --do shot:名字   # 真机点击；切换类必须 --once
```
真机探针三条硬规矩：① 截图滞后一帧，"点了没反应"的结论必须有**应用侧日志**佐证；
② 默认连点两次，切换类加 `--once`；③ 有序交互用 `--do`（click/wheel/hover/shot）。
**清场只按 PID**（`taskkill /F /T /PID`），绝不 `taskkill /IM flet.exe` —— 用户机器上可能
同时跑着别的 flet 应用。

### 【血泪】别靠肉眼从截图估点击坐标
本次连续点空 4 次。界面缩略图是 1080 宽、实际图像是 2240 宽，差 2 倍多；
而且**页面滚动位置随窗口高度变**，同一个 y 值在不同截图里指向完全不同的控件。
正解：
① 先跑**零偏移标定宿主**（`padding=0` + 已知尺寸的高饱和色块），
   按颜色扫描反推映射 —— 实测 `图像 = 12 + 逻辑 × 1.75`（x）、
   `图像 = 52 + 逻辑 × 1.75`（y），DPR 纵横一致；
② 之后用 `scripts/_locate.py --buttons`：先找**当前页按钮的蓝色边框**
   （分页器里唯一的蓝色）定出行的 y，再按白色块外推等距按钮 —— 页面怎么滚都不用重估。

## 已知待办
- `core/constants.py` 的 `StyleType` 仍在用不随主题走的 M2 硬色（`BLUE`/`GREEN`/`RED`/`YELLOW_600`）
- `display/media/audio.py` 有从未被提交包含的遗留改动，需复核去留
- `scripts/_*_logic.py` 应收敛为 `tests/` pytest；README 组件清单仍是手工维护
- `ImageGridView` / `Input` / `Checkbox` / `Switch` / `SelectBox` / `MultiSelect` 等
  仍是 `@ft.observable` + `.ui()` 范式，**尚未按 Table 的样板收敛**（Batch 2）
- `Paging` 的「前往 __ 页」输入框、`ImageGridView` 的下拉在 frozen 树里点不开
  （flet 1.0.4 限制，非本项目 bug）
