# CS-UI 项目长期记忆

## 环境
- Python：`C:/Softwares/Python-V3.12.10.x64/python.exe`（不要用裸 `python`，容易指向别的解释器）
- 屏幕 3840×2160，DPR 1.75（截图尺寸 = 逻辑尺寸 × 1.75）
- 依赖：`flet[all]>=1.0.0`、`flet-code-editor`、`flet-charts`、`flet-video`、`flet-audio`、`flet-webview`
- 跑 demo：`python examples/demo.py`；跑测试脚本要先 `sys.path.insert(0, "src")`

## 项目约定
- `from ui import *` 会导出 flet 全部内容 + 所有 CS UI 组件（617 个名字）
- **不要在 `src/ui/__init__.py` 写 `__name__ = "cs-ui"`**：会让 `from ui import X`
  在 X 缺失时报出误导性的 `ModuleNotFoundError: No module named 'cs-ui'`。
  产品名走 `__pkg_name__`
- **已下线组件**：`ColorPicker`（`input/color_picker.py` 空文件）、
  `ECharts`（`display/echarts.py` 仅 `# TODO`）——两者都已从包导出移除，别再引用
- **两套组件范式**：
  - *无状态控件*：直接继承 flet 控件（`Button` / `Table` / `ECharts` / `Rating` / `Timeline` / 图表），构造即用
  - *有状态组件*：`@ft.observable` 数据对象 + `@ft.component ui()`；**必须调用 `.ui()`** 放进控件树，
    否则渲染成空白或灰块（`Input` / `Checkbox` / `Switch` / `SelectBox` / `MultiSelect` …）
- 组件统一用绝对路径导入
- 事件回调命名 `on_xx`
- **日期时间组件三件套**：`input/calendar_panel.py` 是 `CalendarPanel` 混入 —— 月历渲染、
  输入框外壳、面板外壳、浮层定位全在里面，宿主只需覆写 `_cal_bounds()` / `_cal_pick()`，
  可选覆写 `_cal_is_selected()` / `_cal_day_enabled()` / `_cal_is_month_selected()`。
  `DateInput` / `DateTimeInput` 都写成 `class X(CalendarPanel, Label)` 继承它。
  **两者面板等高 309**（并排进表单不会出现高度差）；`DateTimeInput` 只额外补
  「时/分(/秒) 三列环形时间轮盘 + 页脚」，且**点日期不收起**。
  改日期类选择器一律优先动混入，别在 `date_input.py` / `datetime_input.py` 里复制代码。
  `calendar_panel.py` 是**纯混入、没有 `App()`**，所以 `_ui_audit.py ui.input.calendar_panel`
  必然报 `no attribute 'App'`（预期行为，不是回归）。

## flet 1.0.0 关键差异（本项目踩过的坑）
- `ft.app(main)` → `ft.run(main)`；`page.add()` → `page.render(Component)` / `page.render_views(Component)`
- `page.go(route)` → `page.navigate(route)`（**异步**，需等事件循环轮次）
- 手工维护 `page.views` → `ft.Router(routes, not_found=..., manage_views=False)`（见下"渲染路径"）；
  `not_found` 必须返回**控件**，不是 `ft.View`
- `@ft.control` 子类**不要重声明基类字段**：重声明会让该字段退回基类的靠前位置，
  把 `content` / `src` 等挤出首位（`_positional_audit.py` 可扫描）。需要改默认值就在 `init()` 里赋值，
  或加 `field(kw_only=True)`
- `ft.TextButton(url_target=...)` 已移除 → `url=ft.Url(u, target=ft.UrlTarget.BLANK)`
- `ft.Audio` / `ft.Video` 这类 Service 不放进控件树（构造时自动注册到 `page._services`）
- **输入边框按状态给色** → `FormFieldControl.border` 收 `{ControlState: InputBorder}` 字典；
  `OutlineInputBorder.side` 只收**单个** `BorderSide`（塞 dict 会静默退化成黑色）。
  只用 `DEFAULT` / `FOCUSED` / `ERROR` / `DISABLED`；**`HOVERED` 无效**，悬停用 `hover_color`。
  统一走 `ui.core.styles.outline_input()` / `underline_input()`（**返回 dict**，不是 InputBorder）
- `ChartAxis.label_size` 默认 22 太小，多位数标签会逐字换行并溢出到相邻文本上；
  用 `ui.chart._data.y_axis_label_size` / `x_axis_label_size` 估算，并设 `show_min=False, show_max=False`
- `ft.Padding.symmetric` 只接受关键字参数
- **`GestureDetector.on_scroll` 真机可用**（本项目实测，时间轮盘就靠它做滚轮步进）：
  `ScrollEvent.scroll_delta` 是 **`ft.Offset`**（向下滚一格 ≈ `Offset(0, 57.14)`，
  同结构还带 `transform_hit_tests` / `filter_quality`），取值一律
  `getattr(getattr(e, "scroll_delta", None), "y", 0)`。挂在**非滚动容器**上也能收到滚轮，
  不会被祖先滚动容器抢走。注意 `ft.Container` **没有** `on_scroll` 字段，必须用
  `GestureDetector` 包一层；`ft.Column.on_scroll` / `Column.scroll_to` 是另一套。
- **行内"等高管内容 + 竖直拉伸"必须开 `ft.Row.intrinsic_height=True`**（= Flutter
  `IntrinsicHeight`）。时间线每行是 `Row`，其中轴轨要用 `STRETCH` 拉到与内容等高；
  但父级给行的高度约束是**无界**的 —— 少了 `intrinsic_height`，`Row` 会拿着无界高度去
  拉伸子项，**整行炸到无限高**（症状：第一行占满整屏、后续行全被挤出视口）。
  开了之后 Row 先用子项**固有高度**量一遍（`Stack` 的固有高度是 0，行高因此完全由内容
  决定），再以 **tight** 约束下发，`STRETCH` 才生效。
  **同理**：不要在无界高度里用 `Column` + `expand` 子项撑线（`expand` 沿主轴分配空间，
  父级无界时直接撑爆）—— 要画"绝对定位的线"用 `Stack` + `Container(left=/top=/bottom=/width=)`。
- **`@ft.component` / `page.render` 构建出的控件树是 frozen 的**：flet 会给每个控件打
  `_frozen`（`components/component.py`），**声明式下禁止命令式 `control.update()`**，
  会抛 `RuntimeError: Frozen control cannot be updated.`
  → hover 高亮之类的状态反馈**不要**用 `on_hover` 回写 `bgcolor`；
  改用 **`ft.Container.ink = True` + `ink_color`**，悬停高亮与点击水波纹交给 Flutter 的
  Material 绘（不重绘、不掉帧）。`ft.Container` 在 flet 1.0.0 **没有** `hover_color` 字段。
  另：`ft.BorderStyle` 只有 `NONE` / `SOLID`（没有 `DASHED`），虚线边框画不出来；
  `ft.Colors` 没有 `SUCCESS` / `WARNING` / `INFO`（语义色需自定义固定值，
  项目里统一 `#10b981` / `#f59e0b` / `#ef4444` / `#6b7280`）。
- **渲染路径统一用 `page.render` + `Router(routes, manage_views=False)`（根视图）**，
  不要用 `page.render_views` 的视图栈：
  - 视图栈会把**整个页面浮层盖住** —— `page.overlay` / `page.show_dialog` 零像素渲染，
    不报错、`len(page.overlay)` 正确、回调照打。下拉面板/弹层因此全失效。
  - 代价：**页面组件不能再返回 `ft.View`**（根视图下当普通控件用 → Flutter 反复抛
    `Bad state: No element`、整页灰块）。顶栏用 `Container + Row` 自绘
    —— `ft.AppBar` 是 `AdaptiveControl`，只能挂 `View.appbar`，进不了 `Column.controls`。
  - demo 里对应 `top_bar()` + `page_shell(...) -> ft.Control`（`examples/demo.py`）。
- **浮层工具 `ui/core/float_layer.py`**：`overlay_usable(page)`（判据
  `isinstance(page.views, list)`）+ `use_float_layer(...)`（`page.overlay` 挂
  `Stack(clip=NONE)`：近透明全屏遮罩 + 绝对定位面板，`hole=` 给锚点挖洞放行点击）。
  向上翻转的面板用 `bottom=` 锚定（不必预知面板高度，也就没有估算误差造成的缝）。
  `MultiSelect` 据此把面板做成真正的悬浮；浮层不可用时自动降级为流内展开（`float_panel=False` 可强制）。
- **浮层定位靠 `GestureDetector.on_tap` 的 `global_position - local_position`**
  （= 控件左上角）；`Container.on_click` 的事件**不带坐标**。锚点必须用**父子结构**
  （Stack 兄弟层里前景 `Container` 命中后不再测背景层）；内层小按钮（Chip 的 `×`）
  也要用 `GestureDetector`，同类 tap 识别器才按"内层优先"决策。
  另外 `Stack(clip_behavior=NONE)` 的溢出资控件**画得出来但点不到**
  （Flutter `RenderBox.hitTest` 拒绝自身 size 之外的坐标）。
- **`ft.TextField` 会吞掉全部指针事件**，真机逐项实测：普通 / `read_only=True` /
  `can_request_focus=False+show_cursor=False+enable_interactive_selection=False`
  **都拦**外层 `GestureDetector`（连 `on_tap_down` 都不触发，不是"先于竞技场"那种事件）；
  只有 **`ignore_pointers=True`** 放行（`TapEvent` 带坐标）。而 `TextField.on_click`
  （`always_call_on_tap=True` 时连点也触发）事件是 `ControlEvent`，**只有 `data`、无坐标**。
  → 「整框可点开面板 + 点进去能打字」的做法：`ignore_pointers = 面板未展开`；
  图标不挂事件（点击自然冒泡到外层，收起时展开、展开时收起）。
  另：`ft.Container` **没有** `mouse_cursor` 字段，光标要挂在外层 `GestureDetector` 上。
- `page.width/height` 是逻辑像素，与 `TapEvent.global_position`/`local_position` 同坐标系；
  控件左上角全局坐标 = `global_position - local_position`
- 选项行做"整行可点"时不要用 `ft.Checkbox`：整行 `on_click` 与复选框自身 `on_change` 会重复
  触发，而 `on_change=None` 的 Checkbox 会渲染成**禁用灰**。用 `ft.Icons.CHECK_BOX*` 画指示器
- **SnackBar 族（`Toast` / `Message`）的目标页面必须写成 `page=page`**：
  它们的 `show()` 第一个位置参数是 `content`，`.show(page)` 会把**页面对象绑到 content 上**，
  于是 `Page -> Dialogs -> Toast -> content=Page` 成环 → 配置控件树永不终止 → `RecursionError`。
  `ft.Page` 是 `ft.Control` 的子类（`Page → BasePage → AdaptiveControl → Control`），
  所以 flet 自带的 `V.str_or_visible_control()` **拦不住**它；
  由 `ui.core.snackbar.ensure_snackbar_content(...)` 显式挡下并抛可读的 `TypeError`。
  （`AlertDialog.show(page)` 第一参数就是 page，无此问题。）

## 验证工装（scripts/）
Python 侧不抛异常 ≠ Flutter 侧渲染成功：裸字符串混进 `controls` 只会渲染成灰色 ErrorWidget。
所以**改完 demo 必须跑截图视觉检查**，不能只看 Python 断言。

```
python scripts/smoke_test.py examples.demo main --routes /,/general,/layout,/navigation,/form,/upload,/feedback,/display,/charts,/media,/about
python scripts/_page_render_probe.py <PageName>      # 加 -W error::DeprecationWarning 可当零告警门槛
python scripts/_page_render_probe.py <Page> --find '<正则>'   # 断言某控件确实在该页（按类型/文本/图标名搜）
python scripts/_demo_route_probe.py                  # 路由 + 各页关键控件归属
python scripts/_ui_audit.py <module>                  # 单模块渲染（默认入口 App，可 --entry main）
python scripts/_visual_check.py [--pages A B]        # 真机截图 + 灰块检测
python scripts/_probe_demo.py --app <宿主> --click x,y   # 真机点击；--hover x,y 只移动光标（测 hover）
python scripts/_probe_demo.py --app <宿主> --do click:207,469 --do wheel:400,500,-20 --do shot:before
                                                     # 有序动作序列：click / wheel / hover / shot:名字
python scripts/_config_depth_probe.py --app <宿主>      # 配置递归深度 + 环形引用检测
CS_UI_SHOT_PAGE=FeedbackPage python scripts/_probe_demo.py \
    --app scripts/_shot_page.py --title "CS UI · FeedbackPage" \
    --boot 6 --out output/x.png                       # 单页真机截图/点击（别再现写临时宿主）
```

**跑真机探针前必须清场，但只按 PID 清**（本项目实测教训）：`_probe_demo.py` 收尾已经
`taskkill /F /T /PID <launcher pid>`，会连同它拉起的 `flet.exe` 一起收掉，**不用也不该**
再执行 `taskkill /F /IM flet.exe` —— 用户机器上可能同时跑着**别的 flet 应用**
（本次就有一个标题「Markdown 编辑器」的窗口），全局杀会把用户的窗口一起干掉。
`taskkill /F /IM python.exe` 也**杀不掉 `flet.exe`**（Dart/Flutter 的视图进程）。
残留的 `flet.exe` 顶着**同名窗口标题**会让 `FindWindowW` 连到**旧窗口**
（症状：截图停在 Working… 加载态 / 点击全无反应 / 日志里 `fg_ok=True` 却没有交互回调）。
要确认没有残留：写个 `EnumWindows` 小脚本按标题查，命中再 `taskkill /F /PID <那个 pid>`。

**`--title` 必须与宿主自己设的 `page.title` 完全一致**（本次踩过）：宿主里
`page.title = "X"` 会盖掉一切，探针找的是**运行时窗口标题**，不是宿主文件名；
宿主没设 `page.title` 时才轮到 `--title` 说话。症状是干等 45 秒然后 `! 未找到窗口`，
而 app 侧日志里 `page size = ...` 照常打印。
坐标系标定**不要背常数，按 `geometry=` 那行现算**：探针启动时会打印
`geometry=(left, top, w, h, client_x, client_y)`，截图是**窗口矩形**（宽高就是 `w × h`），
所以 **逻辑 (lx, ly) → 图像 = (client_x − left + lx × DPR, client_y − top + ly × DPR)**。
本项目 3840×2160 / DPR 1.75、窗口被探针摆到 (60,60) 时实测 `client=(72,112)` →
**图像 x = 12 + 逻辑 x × 1.75**、**图像 y = 52 + 逻辑 y × 1.75**。
（图像包含标题栏，`Container(padding=top=20)` 的内容在图像里 y ≈ 52 + 20×1.75 = 87，
可用它反查偏移对不对。页面内容原点 = 客户区 (10,10)。）
注意带 `label` 的字段会被 label 推到右侧，点它之前先用应用侧日志里的
`anchor=(x,y)` 校准，别靠肉眼读截图。

**`_probe_demo.py` 的三条硬规矩**：
1. 截图**滞后一帧**（PrintWindow 返回上一次合成帧）→ 已内置"连抓两次"；**任何
   "点了没反应"的结论都必须有应用侧日志佐证**，只凭单张点击后截图下的结论一律作废。
2. 默认每个 `--click` **连点两次**（第一次用于激活窗口），切换类交互会被互相抵消
   （开→关、选→撤，看着像"完全没反应"）→ 切换类一律加 `--once`。
3. **有序交互用 `--do`**（给了它就不再走 `--click/--hover/--wheel`）：`click:x,y` /
   `wheel:x,y,notches`（负=向下，一次给多格才稳）/ `hover:x,y` / `shot:名字`，
   按命令行顺序执行，每个动作后自动存 `<out>_<序号>.png`。
   视口外的控件必须先 `wheel` 滚到可视区才能点到。
   ⚠️ 探针以 `os._exit(0)` 收尾，**不 flush 会丢掉全部 print**（已加 `sys.stdout.flush()`）。

**验证"浮层没推动下方内容"**：不能只看 `getbbox()` 非空（1% 遮罩会把整页压暗约 3 个灰度级，
看着像全变了）。做法：① 对照组用**同状态、同滚动位置的两次独立运行**（实测 `max|Δ|=0`，
渲染是确定性的）；② 实验组差值扣掉**均匀偏移**后看残差；③ 做 **dy 位移搜索**，
必须唯一选中 `dy=0`。面板边界要用**像素行扫描**量，肉眼看截图会读出差 20px 的假间距。

**排查 `RecursionError` 只用 `_config_depth_probe.py`**：报错行（比如 `ft.Button`
校验里的 `isinstance`）是随机的——栈刚好用尽时执行的下一个调用而已。
正常树实测只有 16~24 层（上限 1000），够了 1000 层基本就是**控件树里有环**。
注意直接自引用会被 flet 拦（`Parent is the same as item`），**间接环**才会漏到 RecursionError。

**已知的成环套路：`page.show_dialog(X)` 而 `X` 的内容/字段又指回 page。**
典型是"把 page 当参数传错了位置"，探针会打印
`CYCLE! Toast -> Page -> Dialogs -> list(1) -> Toast`。
排查顺序：① 看报错处那个控件（如 `Toast`）有没有字段**意外持有了 page / page 的子对象**；
② 用 `dataclasses.fields()` 核对 `@ft.control` 子类的**字段顺序**（重声明基类字段会改变位置参数映射）。

样式/颜色类回归用 `scripts/_outline_probe_app.py`：同屏摆 6 个变体（刺眼颜色），
再用逐像素 `ImageChops.difference(...).getbbox()` 判定，**必须带"已知会变"的控制组**。
