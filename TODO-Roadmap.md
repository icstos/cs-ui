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

# TODO
- [ ] 2026-09-02：添加全局主题切换：暗黑模式
- [ ] 2026-09-02：添加全局主颜色切换
- [ ] 2026-09-02：标准组件样式，统一风格
- [ ] 添加全局主颜色切换（当前仅明暗切换）
- [ ] 标准组件样式，统一风格
- [ ] 将 `_probe_*` / `_audit` 等验证脚本收敛为 `tests/` 下的正式测试
- [ ] README 组件清单与 API 文档自动生成（当前手工维护）
