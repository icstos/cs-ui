# Roadmap
企业级、开箱即用
- api友好，使用灵活
- 细致
- 文档：
- 

## 设计原则
- 一致与差异：统一的设计样式、
- 反馈与：组件的样式与交互动效让用户可清晰地感知自己的操作。
- 效率：简洁直观地使用、清晰明确地表达，符合用户体验的使用
- 可控
# 已完成
- [x] 2026-09-21：全量适配 flet 1.0.0（`ft.run` / `page.render_views` / `@ft.component` / hooks）
- [x] 2026-09-21：所有组件均有可运行 demo（42 个模块审计通过）
- [x] 2026-09-21：重写 `examples/demo.py`（11 个分类页 + 404 页，声明式路由）
- [x] 2026-09-26：渲染路径改为**根视图** `page.render` + `Router(manage_views=False)`。
      原因：`page.render_views` 的视图栈会把 `page.overlay` / `page.show_dialog` 整层盖住
      （零像素且不报错）。代价是页面不能再返回 `ft.View`（会整页灰块），
      页面外壳改用 `Container` + 自绘顶栏（`ft.AppBar` 是 `AdaptiveControl`，进不了 `Column`）。
      同步改动：`examples/demo.py`（`top_bar()`）、`src/ui/app.py`（`Template`）
- [x] 2026-09-26：`MultiSelect` 改为真正的**悬浮面板**：折叠态高度 = 整个组件高度，
      展开面板挂 `page.overlay`（不占布局、不推下方内容），全屏近透明遮罩实现"点外部收起"
      （遮罩给输入框挖洞，Chip 的 × 仍可点）。浮层不可用时自动降级为流内展开。
      新增 `src/ui/core/float_layer.py`（`overlay_usable` / `use_float_layer`）
- [x] 2026-09-26：修 `Toast` / `Message` 的 `RecursionError`（报错落在 `Button.icon` 的
      `isinstance` 上，实际是控件树成环）：`show()` 的第一个位置参数是 `content`，
      写成 `.show(page)` 会把 page 绑到 content 上，`page.show_dialog(self)` 之后形成
      `Page -> Dialogs -> Toast -> Page` 的环。新增 `src/ui/core/snackbar.py`
      （`ensure_snackbar_content`，`ft.Page` 是 `ft.Control` 子类，flet 自带校验器挡不住），
      `show()` 的 `style_type` / `duration` / `page` 改为关键字限定，并修好 `Message.show`
      里一直是死参数的 `page`
- [x] 2026-09-26：`DateInput` 从「年 / 月 / 日三下拉框」重构为**桌面级日期选择器**：
      输入框 + 悬浮月历（挂 `page.overlay`，不占布局高度）。面板含翻月 / 翻年、
      点标题切年月网格、点日期即选即收、"今天" / "清除"、外点收起、上下自动翻转、
      左右边界收拢；框内可直接键入（`2026-09-26` / `20260926` / `2026年9月26日`），
      非法输入标红还原；`min_date` / `max_date` 越界日灰字禁用。
      关键技术点：`TextField` 在 flet 1.0.0 会吞掉全部指针事件，只有
      `ignore_pointers=True` 能放行外层 `GestureDetector`（`read_only` /
      `can_request_focus=False` 都不行），因此收起态置 `ignore_pointers`、
      展开后恢复，从而同时拿到"整框可点开"与"点进去能输入"
- [x] 2026-09-26：`DateTimeInput` 从「年/月/日/时/分/秒六下拉框」重构为**桌面级日期时间
      选择器**：同一个悬浮面板内 **月历与「时 / 分 / 秒」三列时间轮盘并排**（高 309，
      与 `DateInput` 逐像素等高，并排进表单不会出现高度差）。共同逻辑抽成
      `input/calendar_panel.py` 的 `CalendarPanel` 混入（`DateInput` 由 970 行瘦身到约
      400 行），`DateTimeInput` 只补「时间轮盘 + 页脚 + 三个日历钩子」。
      交互取舍：**点日期不收起**（接着还要调时间），日期 / 时间 / 轮盘点击全部**即改
      即生效**，点「完成」或面板外部才收起；轮盘选中项居中填色、上下各 3 格递减淡出
      （`WHEEL_FADE`），`▲▼` 步进 + **滚轮步进** + 点任意可见值跳转，三列**环形**
      （`23→00`、`55分→00分`）；当前值不在步长网格里时自动补入（`minute_step=5` 且值为
      37 → 出现 `… 35, 37, 40 …`）。页脚 `今天 / 此刻 / 清除 / 完成`；
      `with_seconds=False` 时秒**强制归零**（框里显示什么，`value` 就是什么）。
      键入支持 `2026-09-26 09:30` / `2026/9/26 9:30:15` / `20260926 0930` /
      `2026年9月26日 9时30分` / `09:30`；**只给日期则保留原时间、只给时间则保留原日期**。
      关键技术点：`GestureDetector.on_scroll` 在 flet 1.0.0 真机可用（`ScrollEvent.scroll_delta`
      是 `ft.Offset`，取值用 `getattr(delta, "y", 0)`），且普通非滚动容器上也能收到滚轮
- [x] 2026-09-26：`Timeline` 从「垂直单侧、固定样式」重构为**桌面级时间线**
      （`layout/time_line.py` 218 → 727 行）。对齐收敛为 `mode` 三档
      （轴在左 / 轴在右 / 左右交替中轴居中）；时间戳 `time_position` 四档 ——
      **`opposite` 走对侧独立成列**（默认，VS Code 时间线 / GitHub 提交列表的形态）、
      `top`（标题上方，Element Plus 形态）、`inline`（同行分居两端，旧版行为）、`hidden`；
      节点用 `type` 给语义色（primary / success / warning / danger / info / neutral）、
      `variant` 给形态（filled / outlined / plain）、`size` 给三档（18 / 26 / 34），
      每项都可在 `TimelineItem` 上单独覆盖；`done=True` 是「对勾 + 绿点」的语法糖，
      `pending` 在末尾挂空心环「进行中」节点；`density` 三档调节奏，`reverse` 倒序
      （pending 仍在末尾），`line_fade` 让末段渐隐，`line_style="none"` 去掉线只留节点，
      富内容走 `item.content`。交互：整行可点（`on_item_click` / `item.on_click`），
      `disabled` 置灰且不响应。
      三个关键技术点（都是真机踩出来的，见 MEMORY）：
      ① 每行是 `Row` 但**必须开 `intrinsic_height=True`** —— 否则父级给的是**无界高度**，
      `STRETCH` 会把整行拉到无限高（第一行占满整屏、后面全被挤出视口）；开了之后 Row
      先用「固有高度」量一遍（轴轨那条 `Stack` 的固有高度是 0，行高因此完全由内容决定），
      再以 tight 约束下发，`STRETCH` 才能把轴轨拉到与内容等高。
      ② 轴轨用 `Stack` + `Container(left/top/bottom/width)` **绝对定位**画线，
      **不能**用 `Column([线, 节点, 线])` + `线.expand=True`（同 ①，垂直无界时 expand 会撑爆）；
      ③ `@ft.component` 构建出的控件树是 **frozen** 的，`on_hover` 回写 `bgcolor` 会抛
      `RuntimeError: Frozen control cannot be updated.` —— 悬停高亮与点击水波纹一律交给
      Material 的 `Container.ink` / `ink_color` 绘制（不重绘、不掉帧）。
      轴轨宽度与「首行行盒」都取**最大节点**口径算一次（`_dot_max` / `_node_h`），
      所以混排 18 / 26 / 34 三档尺寸时节点仍共用同一条中轴、且各自与标题垂直居中。
- [x] 2026-09-27：新增**设计令牌 + Material 3 主题运行时**（`src/ui/core/tokens.py` +
      `src/ui/core/theme.py`），并接入 demo 全部 11 个页面。
      - **令牌层**：组件里不再出现裸色值 / 裸圆角 / 裸字号。间距 4pt 阶梯
        （`SPACE`，15 档）、`RADIUS` 七档、`FONT_SIZE` 七档、`DURATION` 四档；
        主题感知令牌直接用 `ft.Colors` 角色名（Flutter 绘制时解析，切主题**零 Python
        重渲染**）；框架补齐 M3 缺失的语义色、elevation 五档、overlay/scrim/hairline。
      - **主题层**：`ft.Theme(color_scheme_seed=...)` 让**一个品牌色种子**推导出整套 M3
        色板（52 个 `ColorScheme` 角色）→ 换主色只改一个字符串；`ThemeProvider` /
        `ThemeSwitcher` / `use_theme()` / `theme_state()` 构成运行时，支持
        system / light / dark 三档与 8 个品牌种子。
      - **WCAG 修正（真缺陷）**：原语义色 `#10B981` 对白底仅 **2.54:1**、`#F59E0B` 仅
        **2.15:1** —— 压白字同样只有 2.54 / 2.15，徽标文字读不出来。解法不是调断言而是
        **把语义色拆三档**：`SEMANTIC`（实心填充）/ `SEMANTIC_ON`（填充上的前景）/
        `SEMANTIC_TEXT`（页面文字），三档在明暗下各自 ≥ 4.5:1，`scripts/_theme_logic.py`
        有断言守着。
      - **关键技术点（血泪）**：flet 1.0.4 **读 observable 字段不会订阅**。订阅只发生在
        三处：组件参数是 `Observable`、`use_state`、`use_context`。原先
        `use_theme()` 写成"读一次字段"，点击回调照跑、状态照改、**界面零重渲染**。
        正确解法是 `ft.use_context(ft.create_context(default_value=state))`
        （flet 会自动给 Observable 类型的 context 值挂订阅），并把 `state` 作为
        **Observable 组件参数**传进内部 bridge 组件。
      - **切主题不清空表单**：`ThemeProvider` 用 `use_memo(build, [])` 构建子树，
        切主题不重建控件树；真机日志确认切到暗色后 `use_state` 的值完好。
      - 顺带修好一个长期坏掉的东西：`display/media/pdf.py` 在 git 里一直是空文件，
        却一直被 `__init__` 导出、被 demo import → **`from ui import Pdf` 早就是坏的、
        demo 长期跑不起来**。本轮从 0 实现（纯声明式函数组件，`WebView` 是 `Control`
        可进控件树；进度条**压**在正文区上沿不占高度，避免加载完文档区跳动）。
      - 验证：`_theme_logic.py` 125 断言全过；smoke 12 路由 `ok=12 fail=0`；
        `_visual_check.py` 12 页灰块检测全绿（灰占比 0.000~0.014，阈值 0.55）；
        真机三张截图像素量测确认主色种子生效（pill 底色 `#D9E2FF`→`#2D4578`→`#4F3D74`）。
- [x] 2026-09-27：`pyproject.toml` 收紧 flet 到 `~=1.0.4`（声明式 API 在 1.0.x 内仍有
      差异，`>=1.0.0` 会静默升到不兼容版本），补上漏声明的 `flet-webview` 依赖，
      版本号 0.0.5 → 0.1.0。
- [x] 2026-09-27：README / README_CN 同步：新增「设计令牌与主题」章节（双语）、
      `Pdf` 恢复到组件清单、下线的 `ECharts` 从清单与包结构树移除、
      双范式描述改为「静态组件 / 交互式组件」、flet 版本 1.0.0 → 1.0.4。

- [x] 2026-10-12：`Table` 从 `@ft.control` 子类重写为 `@ft.component` 函数组件
      （用户报的 `RuntimeError: Frozen control cannot be updated.`）。
      **根因**：`set_page()` 用 `self.update()` 换页，而 demo 走 `page.render(App)` 根视图路径，
      flet 1.0.4 把整棵树标记 frozen，`update()` 第一件事就查 `_frozen` → 点「下一页」必崩。
      代码里原有的 `# TODO: bad design: need add TableState` 就是当时的自述。
      - 新增 `TableState`（`@ft.observable @dataclass`）：承载数据与页码，
        抽出它才能让调用方在组件外读页码；**必须是 observable** —— 否则表格翻页了、
        旁读 `state.current_page` 的标题还停在旧值（真机踩到）。
      - 抽出纯函数 `page_slice()` / `columns()` / `build_rows()` / `clamp_page()`，
        全部无头可测 → 新增 `scripts/_table_logic.py`（34 条断言）。
      - **顺带修掉 `Paging` 的下拉缺陷**：候选只有 5/10/15/20/30/40/50，
        而 `Table` 用 `rows_per_page=8` → Flutter 匹配不到 value，下拉框显示空白。
        现在会把当前值补进候选并按数值排序。
      - **踩到的三个真坑（已写进记忆）**：
        ① `use_state(初值)` 的**初值参数每次渲染都求值**，不能让它跟着外部 observable 漂移
        —— 用 `use_ref` 锁死首次值，否则出现"没人点、页码自己往上跳"的渲染循环；
        ② 回写外部 observable 必须放 `use_effect` **且只在值真的不同时写**，
        无条件写会让订阅者重渲染、带动本组件重建，形成循环；
        ③ `@ft.component` **不保留自身类型**，渲染出来的是它 return 的控件 →
        `_demo_route_probe` 里 `/layout` 期望的 `Table` 要改成 `Card` + `DataTable`。
      - `demo.py` 里 `state(lambda: Table(...))` 的 `use_ref` 包装不再需要（纯函数组件），
        直接 `Table(...)` 即可。
      - 验证：34 条逻辑断言全过；真机点击序列 `1→2→1→2→4` 与末页 `6`（编号 41-43）
        全部正确且静置无循环；`_visual_check` LayoutPage / NavigationPage 灰占比 0.001。

# TODO
- [ ] 声明式范式收敛：把仍用 `@ft.observable` + `.ui()` 的组件（`Input` / `Checkbox` /
      `Switch` / `SelectBox` / `MultiSelect` …）迁到 `@ft.component` + hooks 风格，
      统一成一套心智模型
- [ ] 补齐数据展示类控件：Descriptions / Statistic / Empty / Result / Skeleton / Avatar / Badge
- [ ] 补齐导航与输入类控件：Tree / Dropdown 菜单 / Transfer / Cascader / AutoComplete
- [ ] `src/ui/core/constants.py` 的 `StyleType` 仍在用不随主题走的 M2 硬色
      （`ft.Colors.BLUE` / `GREEN` / `RED` / `YELLOW_600`），迁到语义色三档
- [ ] `src/ui/display/media/audio.py` 有未提交的遗留改动，需复核后决定去留
- [ ] 将 `_probe_*` / `_audit` / `_theme_logic` 等验证脚本收敛为 `tests/` 下的正式测试
- [ ] README 组件清单与 API 文档自动生成（当前手工维护）
