# Roadmap
- 多语言：i18n
- 代码即文档，ui代码生成文档网站（docs/）
- ui-mcp：

一套跨平台的Python UI组件库
- 组件：简洁、易用、功能强大
- 跨平台：一套代码支持多个平台
扁平化设计（Flat Design）

## 方向
色彩、排版、布局、图片、图标、组件、动画
- 可定制性
- 开发者体验
- 一致性：提升整体感
  - 排版：行高、字距
  - 字体、字号、字重
  - 配色方案：参考WCAG 2.1 / M3 色彩体系，对表面、前景、交互、强调、数据
- 对比与强调：通过对比不同元素之间的差异，突出页面中的重点。比如不同的颜色、字体大小、字重，使标题、正文等具有层次感。
- **一致** — 静态组件与交互式组件各守一套范式；同样的"划过"在菜单、分页、日历、穿梭框里
  是同一个轻重。
- **反馈** — 每一次操作都要有可见的回应：悬停、选中、加载、结果。点了没反应比报错更糟。
- **效率** — 默认值对得起"直接用"；异常路径不静默（不报错但画出灰块是这里最大的敌人）。
- **可控** — 颜色、间距、字号都能从令牌推翻，组件里没有裸值。

字号：一般说是14px（客户端） -16px（网页），
字重：正文使用 400（Regular）
字号：

颜色
- 语义化颜色
- 清晰的层级
- 有意识的强调
light, dark
accent
accent-hover
accent-foreground
accent-soft-hover
accent-soft-foregound
使用语义命名（primary、secondary、tertiary、danger），而非视觉描述（solid、flat、bordered）

一般圆角：4px
反馈类圆角：4px
卡片圆角：8px

行高：1.5
文字粗细：normal

状态：
Success
Error
Warning
Waiting
Running
Skipped
Canceled
Invalid
Initial
## UI框架
[HeroUI - Never start from scratch again](https://heroui.com/)
## TODO

- [ ] 声明式范式收敛：把仍用 `@ft.observable` + `.ui()` 的组件（`Input` / `Checkbox` /
      `Switch` / `SelectBox` / `MultiSelect` …）迁到 `@ft.component` + hooks，统一成一套心智模型
- [ ] 补齐数据展示类控件：Statistic / Result / Skeleton / Avatar / Badge
- [ ] 补齐输入类控件：AutoComplete（联想建议）、Dropdown 菜单（多级 + 分组）
- [ ] `PageLayout` 的限宽目前靠 `on_size_change` 运行期写 `width`，在 `@ft.component` 的冻结树里
      只能静态化。改成 `Container(max_width=...)` + `alignment` 把限宽交给渲染层
      （`docs.kit.bounded` 已是这个写法），顺带去掉 8px 量化那条重绘路径
- [ ] 验证脚本收敛为 `tests/`：`_*_logic.py` 仍是"文件名即注册表"的临时约定，
      `check_all.py` 靠目录扫描而不是测试框架
- [ ] 组件清单与 API 文档自动生成（现在 `ui-mcp` 已能看到全部签名，README 不必再手抄）


## 参考
[github.com](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill)：没啥大用，可以参考下demo
