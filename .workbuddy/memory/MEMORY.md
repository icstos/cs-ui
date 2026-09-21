# CS-UI 项目长期记忆

## 环境
- Python：`C:/Softwares/Python-V3.12.10.x64/python.exe`（不要用裸 `python`，容易指向别的解释器）
- 屏幕 3840×2160，DPR 1.75（截图尺寸 = 逻辑尺寸 × 1.75）
- 依赖：`flet[all]>=1.0.0`、`flet-code-editor`、`flet-charts`、`flet-video`、`flet-audio`、`flet-webview`
- 跑 demo：`python examples/demo.py`；跑测试脚本要先 `sys.path.insert(0, "src")`

## 项目约定
- `from ui import *` 会导出 flet 全部内容 + 所有 CS UI 组件（617 个名字）
- **两套组件范式**：
  - *无状态控件*：直接继承 flet 控件（`Button` / `Table` / `ECharts` / `Rating` / `Timeline` / 图表），构造即用
  - *有状态组件*：`@ft.observable` 数据对象 + `@ft.component ui()`；**必须调用 `.ui()`** 放进控件树，
    否则渲染成空白或灰块（`Input` / `Checkbox` / `Switch` / `SelectBox` / `MultiSelect` …）
- 组件统一用绝对路径导入
- 事件回调命名 `on_xx`

## flet 1.0.0 关键差异（本项目踩过的坑）
- `ft.app(main)` → `ft.run(main)`；`page.add()` → `page.render(Component)` / `page.render_views(Component)`
- `page.go(route)` → `page.navigate(route)`（**异步**，需等事件循环轮次）
- 手工维护 `page.views` → `ft.Router(routes, not_found=..., manage_views=True)`；
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

## 验证工装（scripts/）
Python 侧不抛异常 ≠ Flutter 侧渲染成功：裸字符串混进 `controls` 只会渲染成灰色 ErrorWidget。
所以**改完 demo 必须跑截图视觉检查**，不能只看 Python 断言。

```
python scripts/smoke_test.py examples.demo main --routes /,/general,/layout,/navigation,/form,/upload,/feedback,/display,/charts,/media,/about
python scripts/_page_render_probe.py <PageName>      # 加 -W error::DeprecationWarning 可当零告警门槛
python scripts/_demo_route_probe.py                  # 路由 + 各页关键控件归属
python scripts/_ui_audit.py <module>[ --entry main]  # 单模块 App() 渲染
python scripts/_visual_check.py [--pages A B]        # 真机截图 + 灰块检测
python scripts/_probe_demo.py --app <宿主> --click x,y   # 真机点击；--hover x,y 只移动光标（测 hover）
```

样式/颜色类回归用 `scripts/_outline_probe_app.py`：同屏摆 6 个变体（刺眼颜色），
再用逐像素 `ImageChops.difference(...).getbbox()` 判定，**必须带"已知会变"的控制组**。
