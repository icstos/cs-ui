"""项目级"经验条款"：那些查 API 查不到、但写错必炸的规矩。

flet-mcp 那类工具只解决"符号存不存在"；cs-ui 真正踩人的地方在
**范式**：frozen 控件树不能 ``update()``、有状态组件必须 ``.ui()``、
``CrossAxisAlignment.STRETCH`` 少一行 ``intrinsic_height`` 就让整页叠在左上角、
颜色串是 ``#AARRGGBB`` 而不是 CSS 的 ``#RRGGBBAA`` …
这些条款沉淀在项目记忆、README 与组件源码的注释里，这里做结构化整理，
让 agent 一次读全，而不是靠试错。

每条都是"结论 + 为什么 + 正确写法"，别只抄结论 —— 坑往往在适用条件里。
"""

from __future__ import annotations

from typing import Any

GUIDELINES: list[dict[str, Any]] = [
    {
        "topic": "overview",
        "title": "cs-ui 是什么 / 怎么导入",
        "tags": ["入门", "导入", "结构", "范式"],
        "body": """\
cs-ui 是 flet 1.x 的组件库（产品名 cs-ui，Python 包名 `ui`），90+ 组件，
按 `input / layout / display / feedback / navigation / chart / core / utils` 分目录，
另有三层框架能力：**设计令牌**（tokens）、**主题与色板**（theme / palette）、
**响应式**（responsive）。

导入（二选一）：
    from ui import *                      # flet 全部 + 所有 cs-ui 组件
    from ui import Button, Table, Input   # 显式具名导入（推荐，便于 diff）

`ui` 会把 flet 的内容一并导出，所以 `ft.Text` 可以写成 `Text`。

**两套组件范式**（决定你怎么用，先判断再写代码）：
1. 静态控件 —— `@ft.control` 继承 flet 控件，构造即用：
       Button(content="保存", on_click=handler)
2. 有状态组件 —— `@ft.observable` 数据对象 + `ui()` 渲染方法：
       input_ = ft.use_ref(lambda: Input(label="名称")).current
       Column(controls=[input_.ui()])
   漏掉 `.ui()` 会渲染成空白/灰块，且**不报错**。

浏览清单：`list_components(category="input")`；查具体符号：`get_api("SelectBox")`；
查令牌取值：`get_api("SPACE")` / `get_api("BREAKPOINT")`（常量也在索引里）。
改代码前先读 `get_guidelines("frozen")` 与 `get_guidelines("layout")` 两条。
示例页：`search_examples("表单")`。""",
    },
    {
        "topic": "rendering",
        "title": "渲染路径：page.render + Router(manage_views=False)",
        "tags": ["路由", "overlay", "对话框", "View"],
        "body": """\
入口必须走**根视图**：

    def main(page: ft.Page) -> None:
        apply_theme(page)                     # 主题（可选，推荐）
        apply_responsive(page)                # 响应式（用到 use_responsive 就必调）
        page.render(App)                      # 不是 page.render_views

    @ft.component
    def App():
        return ThemeProvider(build=lambda: ft.Router(ROUTES, not_found=NotFoundPage,
                                                     manage_views=False))

理由：`manage_views=True` 的视图栈会**整层盖住 page.overlay 与
page.show_dialog**（零像素、且不报错），MultiSelect / DateInput / ColorPicker
这类需要悬挂面板的组件会全部失效。

代价（必须记住）：
- 页面组件**不能返回 `ft.View`** —— 在 manage_views=False 下把 View 塞进控件树，
  Flutter 会连抛 `Bad state: No element`，整页变灰块。要顶栏就 `Container + Row` 自绘。
- `ft.AppBar` 是 AdaptiveControl，只能挂 `View.appbar`，进不了 `Column.controls`。

真机现象：整页灰色 + 控制台 `Bad state: No element` ⇒ 先查这条。""",
    },
    {
        "topic": "frozen",
        "title": "frozen 控件树：禁止 update()，结构改动只在构建期",
        "tags": ["Frozen control cannot be updated", "use_state", "hooks", "结构补丁"],
        "body": """\
`@ft.component` / `page.render` 构建出来的树是 **frozen** 的：
任何 `control.update()` 都会抛 `RuntimeError: Frozen control cannot be updated.`

推论一（状态）：
- 回调里只改状态（`use_state` 的 setter、observable 字段），别碰控件对象；
- 需要"点一下变颜色"之类的效果，用 `ft.Container.ink` + `ink_color` 交给
  Material 画，别自己写 hover 回调改 `bgcolor`；
- `@ft.control` 子类挂在 render 树上**同样 frozen**，老组件里的 `self.update()`
  必须重写成 `use_state`（`Table` 就是这么改的，见 `get_api("Table")`）。

推论二（结构）—— flet 1.1.x 的实测结论：
**已挂载子树的结构补丁不保证上屏**。换 `content`、整列换一份新列表、甚至切
`visible`，都可能"Python 状态全对、屏幕纹丝不动"；**属性补丁**（padding /
width / 文本 / 颜色）一定生效。所以：

- 结构在**构建期**定死，或交给"组件重渲染"整棵重建；
- 运行期只改属性。要跟着窗口档位换布局，就把页面写成组件、在组件里
  `use_responsive()` —— 跨档时整页重渲染，而不是去改子控件的 `controls`。

`use_state` 的初值参数**每次渲染都会求值**：外部 observable 一变就会形成
"没人点、页码自己跳"的循环。用 `use_ref` 锁首次值，回写外部状态放
`use_effect` 且只在值不同时写。""",
    },
    {
        "topic": "state-components",
        "title": "有状态组件：.ui() 与 use_ref 固定实例",
        "tags": ["Input", "Checkbox", "SelectBox", ".ui()", "state", "use_ref"],
        "body": """\
走「数据对象 + `ui()`」范式的组件（`list_components(pattern="observable")` 可查全，
28 个：Input / Checkbox / Switch / Radio / SelectBox / MultiSelect / Chip / Slider /
RangeSlider / ColorPicker / DateInput / DateTimeInput / NumberInput / Cascader /
Transfer / Tree / FilePicker / DirPicker / FileSaver / ImagePicker / ImageGridView /
Calendar / Carousel / Heatmap / LogContainer / NumberAnimation / Menu …）

正确写法（必须在 `@ft.component` 里）：

    def state(factory):                     # 库外的辅助函数，demo 就是这么写的
        return ft.use_ref(factory).current  # 跨渲染保住同一个实例

    @ft.component
    def Form():
        name = state(lambda: Input(label="名称", value=""))
        return Column(controls=[name.ui()])

三条硬规矩：
1. **`.ui()` 只能在渲染上下文里调用**（`@ft.component` 函数体或 `page.render` 内）。
   在 `main()` 里直接调会抛 `No current renderer is set`；
2. 实例必须用 `ft.use_ref` 固定 —— 父组件每次重渲染都会重新执行函数体，
   裸 `Input(...)` 会被重建，表单内容随之丢失。
   （注意：`state()` 只是 demo 里的封装，**没有**从 `ui` 导出，要自己写。）
3. 读值用数据对象字段（`name.value`），不是控件属性。
4. **别把自己的内部方法叫 `_notify`**（也不要用 `notify`）。`@ft.observable` 已经
   注入了 `_notify(name)` 做属性变更通知，签名不同 —— 覆盖它之后第一次给字段赋值
   就 `TypeError: _notify() takes 1 positional argument but 2 were given`。

另有**函数组件**：`Table`、`Pagination`、`ThemeProvider`、`ThemeSwitcher` ——
它们是 `@ft.component` 函数，直接当控件用，不需要 `.ui()`。

想确认某个组件属于哪一类：`get_api("组件名")` 的 `pattern:` 行，
`observable` = 必须 `.ui()`，`static` = 直接构造，`function` = 直接调用。""",
    },
    {
        "topic": "selectors",
        "title": "选择器家族：PanelField 外壳",
        "tags": ["PanelField", "DateInput", "ColorPicker", "下拉面板"],
        "body": """\
`PanelField`（`ui/input/panel_field.py`）是「折叠态输入框 + 页面浮层面板」的
通用外壳：圆角、描边、阴影、定位、外点收起、清空按钮、Label 排版都在里面。

家族成员：`DateInput`、`DateTimeInput`、`ColorPicker`（都是
`class X(PanelField, Label)`），`CalendarPanel` 只管月历并重导出旧名。

新增"框 + 浮层面板"类组件**一律继承 PanelField**，别再复制外壳代码；
面板摆放用模块级 `place_panel()` / `panel_shell()`。

它们依赖 `page.overlay`，所以又回到 `rendering` 那条：必须
`page.render` + `Router(manage_views=False)`，否则面板一片空白。

已知限制（flet 1.x，非本项目 bug）：`Pagination` 的"前往 __ 页"输入框、
`ImageGridView` 的下拉在 frozen 树里点不开。""",
    },
    {
        "topic": "table",
        "title": "Table 范式：use_state + 纯函数派生",
        "tags": ["Table", "TableState", "分页", "DataTable"],
        "body": """\
`Table` 是本项目里"声明式重写"的样板，新写这类组件照抄：

    @ft.observable
    @dataclass
    class TableState:          # 只存页码 + 数据源
        data_table: ft.DataTable
        rows_per_page: int = 10
        page: int = 1

    @ft.component
    def Table(state: TableState | None = None, ...): ...
    # 页码 → use_state；行 = page_slice(state) 纯函数派生

要点：
- **别再写 `@ft.control` 子类 + `self.update()` 换页**，frozen 树下必崩；
- 状态对象可外部持有（`TableState(...)`），方便"外部读页码/换页"；
- `@ft.component` 函数**不保留自身类型**：按类型断言的探针要断言它渲染出的
  真实控件（`/layout` 页现在是 `Card` + `DataTable`）。
- 辅助函数：`pandas_to_datatable(df)` 直接把 DataFrame 转成表。""",
    },
    {
        "topic": "layout",
        "title": "布局陷阱：无界高度、STRETCH、限宽",
        "tags": ["Row", "Column", "expand", "intrinsic_height", "STRETCH", "Stack", "Grid"],
        "body": """\
**一、无界高度里不能 expand。** 在可滚动 `Column` / `ListView` 项里给子控件
`expand=True`，会抛 `RenderFlex children have non-zero flex but incoming height
constraints are unbounded`，或者干脆不显示。

**二、`CrossAxisAlignment.STRETCH` 必须配 `intrinsic_height=True`。**
STRETCH 会给交叉轴一个"等于容器尺寸"的紧约束，而 Row 在 Column 里高度是
**无界**的 —— Flutter 收到 infinite height 直接断言失败。

致命之处：**Python 侧毫无异常**。控件树、`copy`、`update` 全部正常，只是渲染端
退回错误态：所有控件按 0 高布局、内容溢出绘制，看上去像"整页重叠"。
（Quote 组件页就这么整页叠过一次。）

    # 等高 + 竖条拉满，正确写法：
    ft.Row(
        intrinsic_height=True,                          # ← 不能省
        vertical_alignment=ft.CrossAxisAlignment.STRETCH,
        controls=[ft.Container(width=3, bgcolor=ft.Colors.PRIMARY),  # 不写 height
                  ft.Container(expand=True, content=body)],
    )

`Descriptions` / `Steps` / `Quote` 都靠这条活着。诊断顺序：先确认根控件有
`expand`/`scroll`（无 expand 的 Column 高度为 0，子项溢出同样"看起来像重叠"），
再二分到具体控件，最后查这个开关。

**三、画绝对定位的线/装饰用 `Stack` + `left/top/bottom`**，
不要用 `expand` 硬撑，也不要用 `border-left`（Flutter 不允许「非均匀边框 + 圆角」）。

**四、一行 n 格等宽用 `Grid`**，别自己算宽度：

    Grid(controls=cards, min_col_width=260, max_cols=4)

它内部是 `ResponsiveRow`，虚拟列数 = 每行格数、子项恒 `col=1`。

**五、限宽用 `min(cap, 可用宽度)`，字段名避开父类已有字段。**
`PageLayout(max_content_width=...)` 量的是**自身**宽度（侧栏、分栏、对话框里
同样正确）；宽度过 `max_width` 时必须是 `max_content_width`，写成 `max_width`
会撞 flet 自带字段，Dart 侧报 `type 'String' is not a subtype of type 'double?'` 白屏。""",
    },
    {
        "topic": "responsive",
        "title": "响应式：三档、只在跨档通知、量自己",
        "tags": ["响应式", "断点", "use_responsive", "viewport", "Grid", "apply_responsive"],
        "body": """\
**断点表与 `ft.ResponsiveRow` 逐项相同**（`0 / 576 / 768 / 992 / 1200 / 1400`，
Bootstrap 那套，见 `get_api("BREAKPOINT")`）。六个断点归三档窗口类：

    compact   < 768     单列、侧栏收起、页头操作折行、内边距 16
    medium    768–1199  两列、侧栏可常驻、内边距 24
    expanded  ≥ 1200    侧栏 + 内容 + 大纲、内容居中限宽、内边距 32

为什么必须同源：另采 Material 的 600/840/1200 会出现"栅格已换列、页面还以为
自己是窄屏"。md(768) / xl(1200) 正好是两处分界。

**只有跨档才通知。** `ResponsiveState` 只有 `size_class` 一个 observable 字段，
赋值前先比较；精确宽度在不可变的 `Viewport` 快照里，更新它不触发重绘。
所以拖窗口不会把界面拖成幻灯片。

    @ft.component
    def Page():
        r = use_responsive()                 # 跨档时本组件重绘
        return PageLayout(
            title="用户管理",
            controls=[Grid(min_col_width=260, controls=cards)]
            if r.is_compact else
            [Row(controls=[Grid(min_col_width=260, controls=cards, expand=True),
                           ViewPanel])],
        )

三条硬规矩：
1. **`apply_responsive(page)` 必须在 `main()` 里调一次**，否则 `use_responsive()`
   永远停在 expanded。它内部还会"首帧后补读"：窗口的**启动尺寸不触发
   `on_resize`**，`main()` 里读到的 `page.width` 是上一次的尺寸（实测 640 的窗口
   读到 1266）。没这一步，"启动就是窄屏"的应用会按宽屏建整页且再也回不来。
2. **量自己，不量窗口。** `PageLayout` / `Descriptions` 用 `on_size_change` 读自身
   宽度 —— 窗口很宽、但控件在侧栏里很窄，两种情况同时成立。
3. **连续性变化交给 Flutter**（`Grid` / `ResponsiveRow` / `expand` /
   `on_size_change`），结构性变化交给 Python（跨档 → 组件重渲染）。
   不要用 `size_class` 做逐像素算术。

辅助函数：`size_class(w)`、`at_least(w, "md")`、`pick(w, compact=..., expanded=...)`、
`resolve(value, w)`（属性支持断点字典时用它）。""",
    },
    {
        "topic": "colors",
        "title": "颜色串：flet 是 #AARRGGBB，不是 CSS 顺序",
        "tags": ["颜色", "with_opacity", "hex8", "ColorPicker", "色板"],
        "body": """\
flet / Flutter 的 8 位十六进制是 **`#AARRGGBB`（透明度在前）**，
与 CSS 的 `#RRGGBBAA` **正好相反**。搞反会得到"完全透明"或"颜色乱掉"。

- 组件 `value` 必须回 **flet 原生色串**：不透明用 `"#RRGGBB"`；
  带透明度用 `ft.Colors.with_opacity(a, "#RRGGBB")`，产物形如 `"#RRGGBB,0.8"`；
- 需要 CSS 顺序的 8 位时另给 `hex8` 属性（`hex6` / `hex8` / `native_color` /
  `parse_color` 都在 `ui/input/color_picker.py`）；
- 透明度取 **3 位小数**，才能让 256 档往返零漂移；
- `ft.Colors` 里只有 **Material 基础色名**（`red` / `teal` …）Python 侧能拿到 RGB；
  带色阶的（`red500`）、强调色（`redAccent`）、主题角色（`primary` / `onsurface`）
  拿不到，必须"原值透传"给 Flutter 解析。

**自己配色时不要用 `ft.Theme(color_scheme_seed=...)`。** M3 的 tonalSpot 会把
种子映射到固定 tone 并大幅降彩度（`#1F6FEB` → `#465D91`，品牌色被抽掉一半彩度）。
本项目走 `ui.core.palette.build_scheme()`：色相不动、只按对比度解算明度，
46 个角色一次算全。详见 `get_guidelines("theme")`。""",
    },
    {
        "topic": "tokens",
        "title": "设计令牌：别写裸色值 / 裸圆角 / 裸字号",
        "tags": ["tokens", "semantic", "WCAG", "间距", "字号", "圆角"],
        "body": """\
组件里**不写裸色值、裸圆角、裸字号**，一律走 `ui/core/tokens.py`。
取值不用猜，索引里有：

    get_api("SPACE")        # {"0":0,"1":4,"2":8,"3":12,"4":16,"5":20,"6":24,"8":32,…}
    get_api("RADIUS")       # none/xs 2/sm 4/md 6/lg 8/xl 12/full 999
    get_api("FONT_SIZE")    # caption 11 / small 12 / **body 14** / title 16 / headline 20 …
    get_api("BREAKPOINT")   # xs 0 / sm 576 / md 768 / lg 992 / xl 1200 / xxl 1400
    get_api("CONTENT_MAX")  # reading 720 / content 1120 / wide 1440

- **主题感知令牌** = `ft.Colors` 角色名（`ft.Colors.PRIMARY`、
  `SURFACE_CONTAINER_LOW`），Flutter 绘制时解析 ⇒ 切主题**零 Python 重渲染**；
- **框架解析令牌**：`SPACE`、`RADIUS`、`FONT_SIZE`（正文 14）、`FONT_WEIGHT`、
  `CONTROL_HEIGHT`、`ICON_SIZE`、`DURATION`、`elevation(0..4)`、`overlay(a)`、
  `scrim()`、`hairline()`、`state_layer()` / `selected_layer()` / `disabled_layer()`；
- **语义色必须三档**（实测 `#10B981` 对白底只有 2.54:1，压白字也读不出来）：
  `semantic("success")` 实心填充 / `on_semantic("success")` 填充上的前景 /
  `semantic_text("success")` 页面文字。角色：success / warning / danger / info / neutral。
  三档由 `palette.semantic_scale` 解到"浅色 5.0:1 / 深色 7.0:1"，视觉重量一致；
- 强调色四联：`accent_fill` / `accent_on` / `accent_text` / `accent_soft`（+`accent_wash`）。

配色分五层（表面 / 前景 / 交互 / 强调 / 数据），**不要跨层借用**：
跨层就是"同一种绿在五个地方长得不一样"的来源。

验证：`python scripts/_tokens_logic.py`、`python scripts/_palette_logic.py`
（含 WCAG 对比度断言）。""",
    },
    {
        "topic": "theme",
        "title": "主题：品牌色 → 46 个角色，明暗两套一起下发",
        "tags": ["ThemeProvider", "theme_state", "toggle_mode", "主色", "build_scheme"],
        "body": """\
**主题只有一个出口**：品牌色 → `ui.core.palette.build_scheme()` → 46 个 M3 角色
→ `ft.ColorScheme(**scheme)`。**不要再引入 `color_scheme_seed`**：Flutter 的
tonalSpot 会把 `#1F6FEB` 推成 `#465D91`，品牌色被改掉一半彩度。
`build_theme` 已把种子字段删掉，留着会误导。

- `ThemeProvider(build=...)` 用 `use_memo(build, [])` 构建子树 ⇒ **切主题不重建
  控件树**，表单已输入内容不丢；它必须包在**最外层**（放在页面组件里会晚一帧，
  切换时闪旧配色）。
- 换主色：`theme_state().set_primary(PRIMARY_SEEDS["violet"])`；8 个种子见
  `get_api("PRIMARY_SEEDS")`。`ThemeState` 还有 `surfaces`（中性色掺多少品牌色相：
  `neutral` / `tonal`）与 `font_family`。
- 明暗三档别混：
  `toggle_mode()` 切到与**当前可见**相反那档（☀/🌙 按钮用，点了必定看得见变化）；
  `cycle_mode()` 走 `system→light→dark→system`（下拉用）；
  `set_mode("system")` 跟随系统亮度。
- 手写入口（不用 ThemeProvider 时）：

      apply_theme(page)        # 同时写 page.theme 与 page.dark_theme，
                              # 并补 page.bgcolor = ft.Colors.SURFACE

  只写 `page.theme` 等于没有深色模式（flet 在 `theme_mode=DARK` 时用的是
  `page.dark_theme`）；不补 `bgcolor` 页面底色会是 Flutter 默认的 `#121212`。

**一个陷阱：读 observable 字段不会订阅。** 订阅只发生在三处：组件参数是
`Observable`、`use_state`、`use_context`。所以组件里要用 `use_theme()`（内部是
`use_context(theme_context)`），直接 `theme_state().mode` 只会读一次。
同理，`semantic("success")` 这类 Python 算出的 hex 需要组件订阅主题才会更新；
而 `ft.Colors.PRIMARY` 这种角色名由 Flutter 解析，切主题零成本。""",
    },
    {
        "topic": "i18n",
        "title": "多语言：组件内 use_t，组件外 t",
        "tags": ["i18n", "翻译", "use_t", "语言切换", "格式化"],
        "body": """\
文案全部走 `ui.core.i18n`，语言包按 key 组织（内置 zh-CN / en-US，可注册新语言）。

    from ui import use_t, t

    @ft.component
    def Toolbar():
        tr = use_t()                        # 订阅：切语言时本组件重绘
        return Text(tr("app.title"))

    t("app.title")                          # 组件外（日志 / 构造菜单）：不订阅

**为什么必须用 `use_t()`**：flet 只在三处订阅 observable（组件参数是
`Observable`、`use_state`、`use_context`），组件体里直接调全局 `t()` 只读一次，
切语言不重绘。用 `use_t()` 的代价是"只有订阅过的组件更新" —— 这正是要的
（表单内容不会因为切语言被重建）。

- 注册自己的文案：`register_messages("zh-CN", {"app.title": "..."})`；
- 带数量用 `tn(key, n)`（复数规则按语言注册），富文本用 `tl(...)`；
- 缺 key 会沿 `zh-CN` 回退并记进 `missing_keys()`，不会抛异常；
- 日期 / 数字 / 列表也用这一层：`format_date` / `format_number` / `format_list`，
  `DateInput` / `CalendarPanel` 的标题与星期名已全部走它；
- 切换语言：`set_locale("en-US")`；持久化用 `FileStore`（见 `get_api("FileStore")`）。""",
    },
    {
        "topic": "overlay",
        "title": "浮层：page.overlay 的三条硬规则",
        "tags": ["overlay", "浮层", "TransparentPointer", "Message", "Notification", "点击穿透"],
        "body": """\
- **撑满宽度的浮层节点会吞掉自己那条横带里的全部点击**。`left=0, right=0` 或
  `expand=True` 的节点，即使里面只有一个居中卡片，也会挡住它下面的按钮（实测：
  10×10 的节点不吞、撑满的吞）。居中摆放改用 `ft.TransparentPointer`（空白穿透、
  子控件照常响应）；`ignore_interactions=True` **不行** —— 它连子控件一起放行，
  关闭按钮就点不到了。四角摆放用普通 `Container`，保证 `on_click` 只触发一次。
- **同一 page + 同一位置只挂一个节点**，新卡片只改里面 `Column.controls`。每次
  push 都 `page.overlay.append` 的话，浮层节点会随消息条数线性增长，还会让
  进出场动画互相打断。
- **计时不要指望取消句柄**：`page.run_task` 返回的 Future 没有 `cancel()`。
  用自增 token（`token += 1`，旧回调发现 token 不是最新就 return），合并计数与
  悬停续计时才不会出现两个计时器抢着关同一条。
- 进出场只动 `opacity` / `offset`（隐式动画在 Flutter 端插值，无逐帧回调）：
  首帧以"透明 + 偏移"挂上，隔一帧（16ms）再改终值。见 `feedback/_overlay.py`。""",
    },
    {
        "topic": "verify",
        "title": "改完怎么验证（脚本清单）",
        "tags": ["验证", "测试", "探针", "截图", "check_all"],
        "body": """\
Python 侧不抛异常 **≠** Flutter 侧渲染成功：裸字符串混进 `controls` 只会渲染成
灰色 ErrorWidget，日志一片安静；`STRETCH` 少个 `intrinsic_height` 更是整页叠在
左上角、Python 全绿。所以改完按下表跑：

    python scripts/check_all.py                 # 唯一入口，29 项 ≈ 52s
    python scripts/check_all.py --stage fast    # 改样式时够用
    python scripts/check_all.py --stage visual  # 才开窗口截图

分项（多数是纯逻辑断言，不开窗）：

    python scripts/_tokens_logic.py             # 令牌取值与阶梯
    python scripts/_palette_logic.py            # 色板规则 + WCAG 对比度
    python scripts/_theme_logic.py              # 主题装配（明暗两棵树）
    python scripts/_responsive_logic.py         # 响应式契约（100 条）
    python scripts/_text_logic.py               # Quote/Heading 结构不变量
    python scripts/_table_logic.py              # Table 分页纯函数
    python scripts/_heatmap_logic.py            # Heatmap 网格 / 色阶
    python scripts/_feedback_logic.py           # Message / Notification 栈
    python scripts/_calendar_logic.py           # Calendar 网格 / 状态机
    python scripts/_color_picker_logic.py       # 颜色数学与 hex 往返
    python scripts/_doc_check.py                # 组件文档（--strict table）

真机 / 截图（要开窗，分批跑）：

    python scripts/_ui_audit.py <module>        # 单模块渲染审计（输出 @@OK@@）
    python scripts/smoke_test.py examples.test_form main --routes /,...
    python scripts/_demo_route_probe.py         # 路由 + 关键控件归属
    python scripts/_visual_check.py --pages HomePage GeneralPage

真机交互验证要按 PID 清场（`taskkill /F /T /PID`），**绝不** `taskkill /IM flet.exe`。
截图坐标别靠肉眼估：界面缩略图与实际图像尺寸差 2 倍多，用
`scripts/_locate.py` 按像素特征定位。

Python 解释器用 `C:/Softwares/Python-V3.12.10.x64/python.exe`（或 `py -3.12`）；
shell 里裸 `python` 指向另一个没装 flet 的版本。""",
    },
]


def topics() -> list[dict[str, str]]:
    return [
        {
            "topic": g["topic"],
            "title": g["title"],
            "tags": ", ".join(g["tags"]),
            "chars": len(g["body"]),
        }
        for g in GUIDELINES
    ]


def get(topic: str | None = None) -> dict[str, Any]:
    if topic is None or not topic.strip():
        return {
            "topics": topics(),
            "note": "用 get_guidelines('<topic>') 读全文；这些是查 API 查不到的范式条款。",
        }
    wanted = topic.strip().lower()
    for guide in GUIDELINES:
        if wanted in (guide["topic"].lower(), guide["title"].lower()):
            return guide
    for guide in GUIDELINES:
        haystack = " ".join([guide["topic"], guide["title"], *guide["tags"]]).lower()
        if wanted in haystack:
            return guide
    return {
        "error": f"没有 '{topic}' 这条",
        "topics": [t["topic"] for t in topics()],
    }
