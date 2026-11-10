# Roadmap

## 方向

- **一致** — 静态组件与交互式组件各守一套范式；同样的"划过"在菜单、分页、日历、穿梭框里
  是同一个轻重。
- **反馈** — 每一次操作都要有可见的回应：悬停、选中、加载、结果。点了没反应比报错更糟。
- **效率** — 默认值对得起"直接用"；异常路径不静默（不报错但画出灰块是这里最大的敌人）。
- **可控** — 颜色、间距、字号都能从令牌推翻，组件里没有裸值。

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
