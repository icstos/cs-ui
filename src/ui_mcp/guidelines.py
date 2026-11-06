"""项目级"经验条款"：那些查 API 查不到、但写错必炸的规矩。

flet-mcp 那类工具只解决"符号存不存在"；cs-ui 真正踩人的地方在
**范式**：frozen 控件树不能 ``update()``、有状态组件必须 ``.ui()``、
颜色串是 ``#AARRGGBB`` 而不是 CSS 的 ``#RRGGBBAA`` …
这些条款沉淀在项目记忆与 demo 的模块 docstring 里，这里做结构化整理，
让 agent 一次读全，而不是靠试错。

每条都是"结论 + 为什么 + 正确写法"，别只抄结论 —— 坑往往在适用条件里。
"""

from __future__ import annotations

from typing import Any

GUIDELINES: list[dict[str, Any]] = [
    {
        "topic": "overview",
        "title": "cs-ui 是什么 / 怎么导入",
        "tags": ["入门", "导入", "结构"],
        "body": """\
cs-ui 是 flet 1.x 的组件库（产品名 cs-ui，Python 包名 `ui`），70+ 组件，
按 `input / layout / display / feedback / navigation / chart / core / utils` 分目录。

导入（二选一）：
    from ui import *            # flet 全部 + 所有 cs-ui 组件
    from ui import Button, Table, Input   # 显式具名导入（推荐，便于 diff）

`ui` 会把 flet 的内容一并导出，所以 `ft.Text` 可以写成 `Text`。

**两套组件范式**（决定你怎么用，先判断再写代码）：
1. 静态控件 —— `@ft.control` 继承 flet 控件，构造即用：
       Button(content="保存", on_click=handler)
2. 有状态组件 —— `@ft.observable` 数据对象 + `ui()` 渲染方法：
       input_ = ft.use_ref(lambda: Input(label="名称")).current
       Column(controls=[input_.ui()])
   漏掉 `.ui()` 会渲染成空白/灰块，且**不报错**。

浏览清单：`list_components(category="input")`；查具体符号：`get_api("SelectBox")`。
示例页：`search_examples("表单")`，路由见 `examples/demo.py` 的 ROUTES。""",
    },
    {
        "topic": "rendering",
        "title": "渲染路径：page.render + Router(manage_views=False)",
        "tags": ["路由", "overlay", "对话框", "View"],
        "body": """\
入口必须走**根视图**：

    def main(page: ft.Page) -> None:
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
        "title": "frozen 控件树：禁止命令式 update()",
        "tags": ["Frozen control cannot be updated", "use_state", "hooks"],
        "body": """\
`@ft.component` / `page.render` 构建出来的树是 **frozen** 的：
任何 `control.update()` 都会抛 `RuntimeError: Frozen control cannot be updated.`

推论：
- 回调里只改状态（`use_state` 的 setter、observable 字段），别碰控件对象；
- 需要"点一下变颜色"之类的效果，用 `ft.Container.ink` + `ink_color` 交给
  Material 画，别自己写 hover 回调改 `bgcolor`；
- `@ft.control` 子类挂在 render 树上**同样 frozen**，老组件里的 `self.update()`
  必须重写成 `use_state`（`Table` 就是这么改的，见 `get_api("Table")`）；
- `Table` / `Pagination` 这类换页组件：页码是 `use_state`，行数据由页码**纯函数派生**，
  别在回调里改 `DataTable.rows`。

`use_state` 的初值参数**每次渲染都会求值**：外部 observable 一变就会形成
"没人点、页码自己跳"的循环。用 `use_ref` 锁首次值，回写外部状态放
`use_effect` 且只在值不同时写。""",
    },
    {
        "topic": "state-components",
        "title": "有状态组件：.ui() 与 use_ref 固定实例",
        "tags": ["Input", "Checkbox", "SelectBox", ".ui()", "state", "use_ref"],
        "body": """\
走「数据对象 + `ui()`」范式的组件（`list_components(pattern="observable")` 可查全）：

    Input / Checkbox / CheckboxGroup / Switch / Radio / SelectBox / MultiSelect /
    Chip / Slider / RangeSlider / ColorPicker / DateInput / DateTimeInput /
    FilePicker / DirPicker / FileSaver / ImagePicker / ImageGridView / LogContainer

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
   （注意：`state()` 只是 demo 里的封装，**没有**从 `ui` 导出，要自己写或抄
   `examples/demo.py:207`。）
3. 读值用数据对象字段（`name.value`），不是控件属性。
4. **别把自己的内部方法叫 `_notify`**（也不要用 `notify`）。`@ft.observable` 已经
   注入了 `_notify(name)` 做属性变更通知，签名不同 —— 覆盖它之后第一次给字段赋值
   就 `TypeError: _notify() takes 1 positional argument but 2 were given`。
   想主动请求重绘就另起名字（本项目用 `_repaint()` 里调 `self.notify()`）。

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
        "title": "布局陷阱：无界高度里不能 expand",
        "tags": ["Row", "Column", "expand", "intrinsic_height", "Stack"],
        "body": """\
- 在**无界高度**的容器（如可滚动的 `Column` / `ListView` 项）里给子控件
  `expand=True` 会抛 "RenderFlex children have non-zero flex but incoming
  height constraints are unbounded" 之类，或者直接不显示。
- 行内要"等高 + 竖直拉伸"：用 `ft.Row(intrinsic_height=True)`，不要 `expand`。
- 画绝对定位的线/装饰：`Stack` + `Container(left=/top=/bottom=/width=)`，
  不要用 `expand` 硬撑。
- 要让子控件横向撑满又不想被撑高：`Row(..., expand=True)` 配
  `Container(expand=True)` 要看父级约束，拿不准就用 `stretch`/`intrinsic_height` 组合。""",
    },
    {
        "topic": "colors",
        "title": "颜色串：flet 是 #AARRGGBB，不是 CSS 顺序",
        "tags": ["颜色", "with_opacity", "hex8", "ColorPicker"],
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
  拿不到，必须"原值透传"给 Flutter 解析。""",
    },
    {
        "topic": "tokens",
        "title": "设计令牌：别写裸色值 / 裸圆角 / 裸字号",
        "tags": ["tokens", "semantic", "WCAG", "主题"],
        "body": """\
组件里**不写裸色值、裸圆角、裸字号**，一律走 `ui/core/tokens.py`：

- 主题感知令牌 = `ft.Colors` 角色名（`ft.Colors.PRIMARY`、`SURFACE_CONTAINER_LOW`），
  Flutter 绘制时解析 ⇒ 切主题**零 Python 重渲染**；
- 框架解析令牌：`SPACE`（4pt 阶梯）、`RADIUS`、`FONT_SIZE`、`DURATION`、
  `elevation(0..4)`、`overlay(a)`、`scrim()`、`hairline()`；
- **语义色必须三档**（实测 `#10B981` 对白底只有 2.54:1，压白字也读不出来）：
  `semantic("success")` 实心填充 / `on_semantic("success")` 填充上的前景 /
  `semantic_text("success")` 页面文字。角色：success / warning / danger / info / neutral。

验证：`python scripts/_theme_logic.py`（含 WCAG 对比度断言，三档在明暗下都要 ≥4.5:1）。""",
    },
    {
        "topic": "theme",
        "title": "主题：ThemeProvider / theme_state 三档语义",
        "tags": ["ThemeProvider", "theme_state", "toggle_mode", "主色"],
        "body": """\
- `ThemeProvider(build=...)` 用 `use_memo(build, [])` 构建子树 ⇒ **切主题不重建控件树**，
  表单已输入内容不丢；它必须包在**最外层**（放在页面组件里会晚一帧，切换时闪旧配色）。
- 换主色：`ft.Theme(color_scheme_seed=...)` 一个种子推导整套 M3 色板，
  `theme_state().set_primary(PRIMARY_SEEDS["violet"])`；8 个种子见 `PRIMARY_SEEDS`。
- 三档语义别混：
  `toggle_mode()` 切到与**当前可见**相反那档（☀/🌙 按钮用，点了必定看得见变化）；
  `cycle_mode()` 走 `system→light→dark→system`（下拉用）；
  `set_mode("system")` 跟随系统亮度。
- 页面字体在 `page.fonts` 注册后由 Theme 的 `font_family` 使用（demo 用 AlibabaPuHuiTi）。""",
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
        "tags": ["验证", "测试", "探针", "截图"],
        "body": """\
Python 侧不抛异常 **≠** Flutter 侧渲染成功：裸字符串混进 `controls` 只会渲染成
灰色 ErrorWidget，日志一片安静。所以改完按下表跑：

    python scripts/_theme_logic.py                    # 令牌 + 主题逻辑（含 WCAG 断言）
    python scripts/_table_logic.py                    # Table 分页纯函数（34 条）
    python scripts/_heatmap_logic.py                  # Heatmap 网格 / 色阶（76 条）
    python scripts/_feedback_logic.py                 # Message / Notification 栈（54 条）
    python scripts/_calendar_logic.py                 # Calendar 网格 / 状态机（74 条）
    python scripts/_color_picker_logic.py             # 颜色逻辑单测
    python scripts/_ui_audit.py <module>              # 单模块渲染审计（输出 @@OK@@）
    python scripts/smoke_test.py examples.demo main --routes /,/layout,/form,...
    python scripts/_demo_route_probe.py               # 路由 + 关键控件归属（bad=0 且 missing=0）
    python scripts/_visual_check.py --pages HomePage GeneralPage   # 分批跑，12 页一次会被超时杀

真机交互验证要按 PID 清场（`taskkill /F /T /PID`），**绝不** `taskkill /IM flet.exe`。
截图坐标别靠肉眼估：界面缩略图与实际图像尺寸差 2 倍多，用
`scripts/_locate.py` 按像素特征定位。

Python 解释器用 `C:/Softwares/Python-V3.12.10.x64/python.exe`；
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
