"""生成 docs/i18n/site 下的三份语言包。

三语并排写在一个表里，是为了保证**键集完全一致**：少写一条 key，另一边的
``missing_translations()`` 立刻就能发现。产物是扁平点号键的 JSON，方便翻译
工具直接消费。

用法::

    python scripts/build_docs_i18n.py            # 重写三份 JSON
    python scripts/build_docs_i18n.py --check    # 只校验，不写盘
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "i18n" / "site"

#: key → (简体中文, 繁體中文, English)
M: dict[str, tuple[str, str, str]] = {
    # ---------------------------------------------------------------- 导航
    "nav.group.start": ("开始", "開始", "Getting started"),
    "nav.group.guide": ("指南", "指南", "Guides"),
    "nav.group.components": ("组件", "元件", "Components"),
    "nav.group.project": ("项目", "專案", "Project"),
    "nav.home.title": ("首页", "首頁", "Home"),
    "nav.home.desc": ("cs-ui 是什么，以及它长什么样", "cs-ui 是什麼，以及它長什麼樣", "What cs-ui is, and what it looks like"),
    "nav.quickstart.title": ("快速开始", "快速開始", "Quick start"),
    "nav.quickstart.desc": ("五分钟装好，渲染第一个界面", "五分鐘裝好，算繪第一個介面", "Install and render your first window in five minutes"),
    "nav.architecture.title": ("架构", "架構", "Architecture"),
    "nav.architecture.desc": ("分层、两类组件、Provider 顺序与路由", "分層、兩類元件、Provider 順序與路由", "Layers, two kinds of components, providers and routing"),
    "nav.theming.title": ("主题与令牌", "主題與權杖", "Theme & tokens"),
    "nav.theming.desc": ("Material 3 配色、明暗模式与设计令牌", "Material 3 配色、明暗模式與設計權杖", "Material 3 colors, light/dark modes and design tokens"),
    "nav.i18n.title": ("多语言", "多語言", "Internationalization"),
    "nav.i18n.desc": ("运行时切换语言，连日期与数字格式一起变", "執行時切換語言，連日期與數字格式一起變", "Switch language at runtime — dates and numbers follow"),
    "nav.components.title": ("组件总览", "元件總覽", "All components"),
    "nav.components.desc": ("按分类浏览 cs-ui 的全部组件", "依分類瀏覽 cs-ui 的全部元件", "Browse every cs-ui component by category"),
    "nav.general.title": ("通用", "通用", "General"),
    "nav.general.desc": ("文本、按钮、图标、标签与 Markdown", "文字、按鈕、圖示、標籤與 Markdown", "Text, buttons, icons, chips and Markdown"),
    "nav.layout.title": ("布局", "版面", "Layout"),
    "nav.layout.desc": ("容器、列表、折叠面板、时间线与表格", "容器、清單、摺疊面板、時間軸與表格", "Containers, lists, expanders, timelines and tables"),
    "nav.navigation.title": ("导航", "導覽", "Navigation"),
    "nav.navigation.desc": ("面包屑、标签页、分页器与应用外壳", "麵包屑、頁籤、分頁器與應用外殼", "Breadcrumbs, tabs, paging and app shells"),
    "nav.form.title": ("表单", "表單", "Form"),
    "nav.form.desc": ("输入、选择、日期、滑块与取色", "輸入、選擇、日期、滑桿與取色", "Inputs, choices, dates, sliders and colors"),
    "nav.feedback.title": ("反馈", "回饋", "Feedback"),
    "nav.feedback.desc": ("轻提示、消息条、对话框与进度", "輕提示、訊息列、對話框與進度", "Toasts, messages, dialogs and progress"),
    "nav.display.title": ("数据展示", "資料展示", "Display"),
    "nav.display.desc": ("列表项、代码编辑器与代码视图", "清單項、程式碼編輯器與程式碼檢視", "List tiles, code editors and code views"),
    "nav.charts.title": ("图表", "圖表", "Charts"),
    "nav.charts.desc": ("折线、面积、柱状与散点", "折線、面積、長條與散佈", "Line, area, bar and scatter charts"),
    "nav.media.title": ("媒体", "媒體", "Media"),
    "nav.media.desc": ("音频、视频与 PDF", "音訊、影片與 PDF", "Audio, video and PDF"),
    "nav.upload.title": ("文件选择", "檔案選擇", "Files"),
    "nav.upload.desc": ("文件、目录、保存与图片", "檔案、目錄、儲存與圖片", "Files, folders, saving and images"),
    "nav.about.title": ("关于", "關於", "About"),
    "nav.about.desc": ("版本、设计原则与相关链接", "版本、設計原則與相關連結", "Version, principles and links"),
    # ---------------------------------------------------------------- 外壳
    "site.copy": ("复制", "複製", "Copy"),
    "site.copied": ("已复制", "已複製", "Copied"),
    "site.next": ("下一页", "下一頁", "Next"),
    "site.prev": ("上一页", "上一頁", "Previous"),
    "site.on_this_page": ("本页内容", "本頁內容", "On this page"),
    "site.edit_page": ("在 GitHub 上编辑", "在 GitHub 上編輯", "Edit on GitHub"),
    "site.github": ("GitHub 仓库", "GitHub 儲存庫", "GitHub repository"),
    "site.tab.docs": ("文档", "文件", "Docs"),
    "site.tab.components": ("组件", "元件", "Components"),
    "site.tab.about": ("关于", "關於", "About"),
    "site.search.placeholder": ("搜索文档与组件", "搜尋文件與元件", "Search docs and components"),
    "site.search.tooltip": ("打开搜索", "開啟搜尋", "Open search"),
    "site.search.close": ("关闭", "關閉", "Close"),
    "site.search.enter": ("打开第一条", "開啟第一條", "Open the first result"),
    "site.search.count": ("{n} 条结果", "{n} 筆結果", "{n} results"),
    "site.search.empty": ("没有找到“{query}”", "找不到「{query}」", "No results for “{query}”"),
    "site.search.pages": ("页面", "頁面", "Pages"),
    "site.search.components": ("组件", "元件", "Components"),
    "site.theme.to_light": ("切到浅色", "切到淺色", "Switch to light"),
    "site.theme.to_dark": ("切到深色", "切到深色", "Switch to dark"),
    "site.sidebar.runtime": ("Flet {flet} · Python {python}", "Flet {flet} · Python {python}", "Flet {flet} · Python {python}"),
    "site.sidebar.license": ("MIT License", "MIT License", "MIT License"),
    "site.footer.tagline": (
        "基于 Flet 的声明式 Python 桌面界面组件库",
        "基於 Flet 的宣告式 Python 桌面介面元件庫",
        "A declarative Python UI kit for desktop, built on Flet",
    ),
    "site.footer.license": ("© 2026 cs-ui · MIT · v{version}", "© 2026 cs-ui · MIT · v{version}", "© 2026 cs-ui · MIT · v{version}"),
    "site.crumb.docs": ("文档", "文件", "Docs"),
    "site.crumb.components": ("组件", "元件", "Components"),
    "site.demo.preview": ("预览", "預覽", "Preview"),
    "site.demo.code": ("代码", "程式碼", "Code"),
    "site.notfound.title": ("这个页面不存在", "這個頁面不存在", "This page doesn't exist"),
    "site.notfound.desc": (
        "链接可能已经失效，或者地址敲错了。\n用搜索找找看，或者回到首页。",
        "連結可能已經失效，或位址打錯了。\n用搜尋找找看，或回到首頁。",
        "The link may be out of date, or the address is off.\nTry searching, or head back home.",
    ),
    "site.notfound.home": ("回到首页", "回到首頁", "Back home"),
    "site.notfound.search": ("搜索文档", "搜尋文件", "Search docs"),
    # ---------------------------------------------------------------- 首页
    "home.eyebrow": ("v{version} · 声明式桌面界面", "v{version} · 宣告式桌面介面", "v{version} · declarative desktop UI"),
    "home.title": ("用 Python\n构建桌面界面", "用 Python\n建構桌面介面", "Build desktop UIs\nin Python"),
    "home.lead": (
            (
                "cs-ui 在 Flet 之上补上真正需要的那一层：Material 3 主题、完整的表单控件、"
        "运行时多语言与声明式路由。写 Python，得到原生桌面体验。"
    ),
            (
                "cs-ui 在 Flet 之上補上真正需要的那一層：Material 3 主題、完整的表單元件、"
        "執行時多語言與宣告式路由。寫 Python，得到原生桌面體驗。"
    ),
            (
                "cs-ui adds the layer Flet leaves to you: Material 3 theming, complete form controls, "
        "runtime i18n and declarative routing. Write Python, ship a native desktop app."
    ),
    ),
    "home.cta.start": ("快速开始", "快速開始", "Get started"),
    "home.cta.components": ("浏览组件", "瀏覽元件", "Browse components"),
    "home.cta.title": ("准备好开始了吗？", "準備好開始了嗎？", "Ready when you are"),
    "home.cta.desc": ("从安装到第一个可交互界面，只需要几分钟。", "從安裝到第一個可互動介面，只需要幾分鐘。", "From install to your first interactive window in a few minutes."),
    "home.cta.source": ("查看源码", "檢視原始碼", "View source"),
    "home.meta.python": ("Python {version}", "Python {version}", "Python {version}"),
    "home.meta.license": ("MIT 许可", "MIT 授權", "MIT licensed"),
    "home.window.title": ("运行概览", "執行概覽", "Overview"),
    "home.window.subtitle": ("今天的活跃用户", "今天的活躍使用者", "Active users today"),
    "home.window.stat1": ("1,286", "1,286", "1,286"),
    "home.window.stat1_label": ("活跃用户", "活躍使用者", "Active users"),
    "home.window.stat2": ("42.8k", "42.8k", "42.8k"),
    "home.window.stat2_label": ("会话", "工作階段", "Sessions"),
    "home.window.chart": ("近 8 周趋势", "近 8 週趨勢", "Last 8 weeks"),
    "home.stats.components": ("组件", "元件", "components"),
    "home.stats.categories": ("分类", "分類", "categories"),
    "home.stats.languages": ("语言", "語言", "languages"),
    "home.stats.typed": ("类型注解", "型別註解", "typed"),
    "home.feature.title": ("一次把重复的界面工程做完", "一次把重複的介面工程做完", "Do the boring UI work once"),
    "home.feature.subtitle": (
        "组件、主题、语言与路由都在框架里，页面只描述“界面长什么样”。",
        "元件、主題、語言與路由都在框架裡，頁面只描述「介面長什麼樣」。",
        "Components, theme, language and routing live in the framework — pages just describe the UI.",
    ),
    "home.feature.reactive.title": ("声明式状态", "宣告式狀態", "Declarative state"),
    "home.feature.reactive.desc": (
        "use_state 改一个值，用到它的控件自动重绘 —— 不用手动 update。",
        "use_state 改一個值，用到它的元件自動重繪 —— 不用手動 update。",
        "Change a use_state value and every control that reads it re-renders. No manual update.",
    ),
    "home.feature.reactive.unit": ("次点击", "次點擊", "clicks"),
    "home.feature.reactive.reset": ("重置", "重設", "Reset"),
    "home.feature.themed.title": ("主题即状态", "主題即狀態", "Theme as state"),
    "home.feature.themed.desc": (
        "一个主色种子推导整套 M3 色板，明暗切换即时生效。",
        "一個主色種子推導整套 M3 色盤，明暗切換即時生效。",
        "One seed color derives the whole M3 palette; light/dark flips instantly.",
    ),
    "home.feature.themed.action": ("主要操作", "主要操作", "Primary"),
    "home.feature.themed.secondary": ("次要操作", "次要操作", "Secondary"),
    "home.feature.i18n.title": ("运行时多语言", "執行時多語言", "Runtime i18n"),
    "home.feature.i18n.desc": (
        "中英繁三语实时切换，日期与数字格式一起变。",
        "中英繁三語即時切換，日期與數字格式一起變。",
        "Chinese and English switch live — date and number formats follow.",
    ),
    "home.feature.typed.title": ("全程类型注解", "全程型別註解", "Fully typed"),
    "home.feature.typed.desc": (
        "面向 Python 3.12+，公开 API 都有类型签名。",
        "面向 Python 3.12+，公開 API 都有型別簽章。",
        "Python 3.12+ only, every public API signed. Editors complete reliably.",
    ),
    "home.feature.modular.title": ("可组合", "可組合", "Composable"),
    "home.feature.modular.desc": (
        "布局、表单、反馈共享同一套设计令牌。",
        "版面、表單、回饋共用同一套設計權杖。",
        "Layout, form and feedback share one token set.",
    ),
    "home.feature.desktop.title": ("桌面优先", "桌面優先", "Desktop first"),
    "home.feature.desktop.desc": (
        "为鼠标与键盘优化：悬停、密度与滚动。",
        "為滑鼠與鍵盤最佳化：懸停、密度與捲動。",
        "Tuned for mouse and keyboard: hover, density, scrolling.",
    ),
    "home.showcase.title": ("组件都在这儿", "元件都在這裡", "Every component, live"),
    "home.showcase.subtitle": ("下面是真控件，不是截图。", "下面是真元件，不是截圖。", "Real controls below — not screenshots."),
    "home.showcase.all": ("查看全部", "檢視全部", "See all"),
    "home.tile.buttons": ("按钮 Button", "按鈕 Button", "Buttons"),
    "home.tile.inputs": ("输入 Input", "輸入 Input", "Inputs"),
    "home.tile.choices": ("选择 Choice", "選擇 Choice", "Choices"),
    "home.tile.chips": ("标签 Chip", "標籤 Chip", "Chips"),
    "home.tile.progress": ("进度 Progress", "進度 Progress", "Progress"),
    "home.tile.paging": ("分页 Paging", "分頁 Paging", "Paging"),
    "home.tile.page": ("第 {n} 页", "第 {n} 頁", "{n}"),
    "home.code.eyebrow": ("代码示例", "程式碼範例", "Code"),
    "home.code.title": ("一屏写完一个页面", "一屏寫完一個頁面", "A whole page, one screen"),
    "home.code.desc": (
        "状态、缓存与副作用都在组件内部声明，页面读起来就是界面本身。",
        "狀態、快取與副作用都在元件內部宣告，頁面讀起來就是介面本身。",
        "State, caching and side effects are declared inside the component — the page reads like the UI.",
    ),
    "home.code.point1": (
        "use_state 管状态，use_memo 做缓存，use_ref 固定实例。",
        "use_state 管狀態，use_memo 做快取，use_ref 固定實例。",
        "use_state for state, use_memo for caching, use_ref to pin instances.",
    ),
    "home.code.point2": (
        "表单控件自带标签与布局，不用再包一层 Row / Column。",
        "表單元件自帶標籤與版面，不用再包一層 Row / Column。",
        "Form controls carry their own label and layout — no extra Row/Column.",
    ),
    "home.play.title": ("试一试", "試一試", "Try it"),
    "home.play.desc": (
        "切换右上角的主题或语言，这里的输入不会丢。",
        "切換右上角的主題或語言，這裡的輸入不會遺失。",
        "Switch theme or language up top — nothing you typed is lost.",
    ),
    "home.play.badge": ("状态保留", "狀態保留", "State kept"),
    "home.play.checkbox": ("接收更新通知", "接收更新通知", "Email me updates"),
    "home.play.switch": ("启用实验特性", "啟用實驗特性", "Enable experiments"),
    "home.play.toast": ("弹出提示", "彈出提示", "Show a toast"),
    "home.play.toast_text": ("一切正常，组件工作正常。", "一切正常，元件運作正常。", "All good — components work."),
    # ---------------------------------------------------------------- 快速开始
    "start.intro": (
        "五分钟后，你会有一个能跑、能切主题、能切语言的桌面窗口。",
        "五分鐘後，你會有一個能跑、能切主題、能切語言的桌面視窗。",
        "Five minutes from now you'll have a window that runs, re-themes and re-languages itself.",
    ),
    "start.install.title": ("安装", "安裝", "Install"),
    "start.install.desc": ("任选一种方式。升级时让 cs-ui 与 Flet 保持同步。", "任選一種方式。升級時讓 cs-ui 與 Flet 保持同步。", "Pick one. Keep cs-ui and Flet in step when upgrading."),
    "start.install.note_title": ("环境要求", "環境需求", "Requirements"),
    "start.install.note": (
        "Python 3.12+、Flet 1.0.5。Windows / macOS / Linux 桌面都可以运行。",
        "Python 3.12+、Flet 1.0.5。Windows / macOS / Linux 桌面都可以執行。",
        "Python 3.12+, Flet 1.0.5. Runs on Windows, macOS and Linux desktops.",
    ),
    "start.first.title": ("第一个界面", "第一個介面", "First window"),
    "start.first.desc": ("新建 main.py，渲染一个带主题的计数器。", "新增 main.py，算繪一個帶主題的計數器。", "Create main.py and render a themed counter."),
    "start.first.tip_title": ("为什么是 page.render", "為什麼是 page.render", "Why page.render"),
    "start.first.tip": (
        "根视图渲染让 page.overlay 与对话框正常工作；用 render_views 会把它们盖住。",
        "根視圖算繪讓 page.overlay 與對話框正常運作；用 render_views 會把它們蓋住。",
        "Root-view rendering keeps page.overlay and dialogs working; render_views covers them.",
    ),
    "start.run.title": ("运行", "執行", "Run"),
    "start.run.desc": ("保存即热重载；同一份代码也能直接在浏览器里跑。", "儲存即熱重載；同一份程式碼也能直接在瀏覽器裡跑。", "Hot reload on save — and the same file runs in a browser."),
    "start.layout.title": ("目录结构", "目錄結構", "Project layout"),
    "start.layout.desc": ("页面、组合控件与文案分开摆，项目变大也不乱。", "頁面、組合元件與文案分開擺，專案變大也不亂。", "Pages, composite widgets and copy in separate folders — it scales."),
    "start.next.title": ("下一步", "下一步", "Next"),
    "start.next.desc": ("建议按这个顺序继续读：", "建議依這個順序繼續讀：", "Read these in order:"),
    "start.next.point1": ("读架构，理解两类组件与 Provider 顺序。", "讀架構，理解兩類元件與 Provider 順序。", "Architecture: the two component kinds and provider order."),
    "start.next.point2": ("看主题，用一个种子换掉整套配色。", "看主題，用一個種子換掉整套配色。", "Theming: swap the whole palette with one seed."),
    "start.next.point3": ("看多语言，把文案从代码里搬出去。", "看多語言，把文案從程式碼裡搬出去。", "i18n: move copy out of your code."),
    # ---------------------------------------------------------------- 架构
    "arch.intro": (
            (
                "cs-ui 不重写 Flet，而是在它之上补一层：更准的默认值、可订阅的主题与语言，"
        "以及一套能组合的界面语言。"
    ),
            (
                "cs-ui 不重寫 Flet，而是在它之上補一層：更準的預設值、可訂閱的主題與語言，"
        "以及一套能組合的介面語言。"
    ),
            (
                "cs-ui doesn't replace Flet — it adds a layer on top: sharper defaults, subscribable "
        "theme and language, and a composable UI vocabulary."
    ),
    ),
    "arch.layers.title": ("分层", "分層", "Layers"),
    "arch.layers.desc": ("四层，各管一件事：", "四層，各管一件事：", "Four layers, one job each:"),
    "arch.layers.point1": ("控件层 —— 继承 Flet 原生控件，只改默认值与样式。", "控制項層 —— 繼承 Flet 原生控制項，只改預設值與樣式。", "Controls — subclass Flet controls, change defaults only."),
    "arch.layers.point2": ("状态层 —— use_state / use_ref / use_memo 与 observable 数据对象。", "狀態層 —— use_state / use_ref / use_memo 與 observable 資料物件。", "State — use_state / use_ref / use_memo plus observable objects."),
    "arch.layers.point3": ("基础设施 —— 主题、语言、路由、格式化与设计令牌。", "基礎設施 —— 主題、語言、路由、格式化與設計權杖。", "Infrastructure — theme, i18n, routing, formatting, tokens."),
    "arch.layers.point4": ("应用层 —— 页面只负责组合，不关心底层细节。", "應用層 —— 頁面只負責組合，不關心底層細節。", "Application — pages only compose; they never touch the plumbing."),
    "arch.kinds.title": ("两类组件", "兩類元件", "Two kinds of components"),
    "arch.kinds.desc": ("静态的继承控件；有状态的用数据对象加 ui() 方法。", "靜態的繼承控制項；有狀態的用資料物件加 ui() 方法。", "Static ones subclass a control; stateful ones pair a data object with ui()."),
    "arch.kinds.note_title": ("常见陷阱", "常見陷阱", "Common trap"),
    "arch.kinds.note": (
            (
                "有状态组件必须在 @ft.component 里构造，并用 use_ref 固定实例；"
        "否则父组件重绘会重建对象，输入就丢了。"
    ),
            (
                "有狀態元件必須在 @ft.component 裡建構，並用 use_ref 固定實例；"
        "否則父元件重繪會重建物件，輸入就遺失了。"
    ),
            (
                "Build stateful components inside @ft.component and pin them with use_ref. Otherwise a "
        "parent re-render recreates the object and the user's input is gone."
    ),
    ),
    "arch.providers.title": ("Provider 顺序", "Provider 順序", "Provider order"),
    "arch.providers.desc": ("语言在最外，主题其次，路由最内 —— 顺序决定首帧的颜色与文案。", "語言在最外，主題其次，路由最內 —— 順序決定首幀的顏色與文案。", "Language outermost, theme next, router innermost — order decides the first frame."),
    "arch.providers.tip_title": ("build 必须是函数", "build 必須是函式", "build must be a function"),
    "arch.providers.tip": (
            (
                "Provider 用 use_memo 缓存 build() 的结果：切语言只重绘订阅了 use_t() 的组件，"
        "不会重建整棵控件树，表单内容因此不会丢。"
    ),
            (
                "Provider 用 use_memo 快取 build() 的結果：切語言只重繪訂閱了 use_t() 的元件，"
        "不會重建整棵控制項樹，表單內容因此不會遺失。"
    ),
            (
                "Providers memoize build(): switching language re-renders only components that called "
        "use_t(), so the tree — and your form state — survives."
    ),
    ),
    "arch.routing.title": ("声明式路由", "宣告式路由", "Declarative routing"),
    "arch.routing.desc": ("根视图渲染加 manage_views=False，浮层与悬挂面板才正常。", "根視圖算繪加 manage_views=False，浮層與懸掛面板才正常。", "Root-view rendering plus manage_views=False keeps overlays and flyouts alive."),
    "arch.routing.danger_title": ("不要用 render_views", "不要用 render_views", "Don't use render_views"),
    "arch.routing.danger": (
            (
                "render_views 会建立视图栈并盖住 page.overlay：MultiSelect 的下拉、"
        "DateInput 的月历会静默失效。"
    ),
            (
                "render_views 會建立視圖堆疊並蓋住 page.overlay：MultiSelect 的下拉、"
        "DateInput 的月曆會靜默失效。"
    ),
            (
                "render_views builds a view stack over page.overlay: MultiSelect flyouts and DateInput "
        "calendars silently stop working."
    ),
    ),
    "arch.state.title": ("状态管理", "狀態管理", "State management"),
    "arch.state.desc": ("局部状态用 hooks；跨页面状态用模块级 observable 单例。", "區域狀態用 hooks；跨頁面狀態用模組級 observable 單例。", "Local state via hooks; cross-page state via a module-level observable singleton."),
    "arch.state.hooks": ("三个 hook 的分工", "三個 hook 的分工", "Three hooks, three jobs"),
    "arch.state.point1": ("use_state：组件内部状态，改了就重绘。", "use_state：元件內部狀態，改了就重繪。", "use_state — component-local state; change it and the component re-renders."),
    "arch.state.point2": ("use_ref：固定跨渲染实例，表单控件放这里。", "use_ref：固定跨算繪實例，表單元件放這裡。", "use_ref — pin an instance across renders; form controls live here."),
    "arch.state.point3": ("use_memo：按依赖缓存昂贵计算。", "use_memo：依相依性快取昂貴計算。", "use_memo — cache expensive work against dependencies."),
    "arch.perf.title": ("性能取向", "效能取向", "Performance"),
    "arch.perf.desc": ("重绘按订阅粒度发生，切主题或语言不会重建控件树。", "重繪依訂閱粒度發生，切主題或語言不會重建控制項樹。", "Re-renders follow subscriptions; switching theme or language never rebuilds the tree."),
    "arch.perf.point1": ("只有读了 use_t() / use_theme() 的组件会重绘。", "只有讀了 use_t() / use_theme() 的元件會重繪。", "Only components that read use_t() / use_theme() re-render."),
    "arch.perf.point2": ("路由切换保留外壳，顶栏与侧边栏不重建。", "路由切換保留外殼，頂欄與側邊欄不重建。", "Route changes keep the shell: top bar and sidebar stay mounted."),
    "arch.perf.point3": ("表单实例复用，输入过程中不反复创建对象。", "表單實例重用，輸入過程中不反覆建立物件。", "Form instances are reused, so typing never recreates objects."),
    # ---------------------------------------------------------------- 主题
    "theme.intro": (
        "主题不是一堆颜色常量，而是一个可订阅的状态：换主色、切明暗，界面自己跟上。",
        "主題不是一堆顏色常數，而是一個可訂閱的狀態：換主色、切明暗，介面自己跟上。",
            (
                "A theme isn't a pile of color constants — it's subscribable state. Change the seed or the "
        "mode and the UI follows."
    ),
    ),
    "theme.live.title": ("实时主题", "即時主題", "Live theme"),
    "theme.live.desc": ("这块面板用的是同一套令牌，切换后立刻变色。", "這塊面板用的是同一套權杖，切換後立刻變色。", "This panel uses the same tokens — it recolors the moment you switch."),
    "theme.live.point1": ("模式：跟随系统 / 浅色 / 深色。", "模式：跟隨系統 / 淺色 / 深色。", "Mode: system, light or dark."),
    "theme.live.point2": ("主色：一个种子推导整套 M3 色板。", "主色：一個種子推導整套 M3 色盤。", "Seed: one color derives the whole M3 palette."),
    "theme.live.primary": ("主色种子", "主色種子", "Seed color"),
    "theme.live.input": ("主题输入框", "主題輸入框", "Themed input"),
    "theme.live.value": ("随便输点什么", "隨便輸入點什麼", "Type something"),
    "theme.live.action": ("主要操作", "主要操作", "Primary"),
    "theme.live.secondary": ("次要操作", "次要操作", "Secondary"),
    "theme.tokens.title": ("设计令牌", "設計權杖", "Design tokens"),
    "theme.tokens.desc": ("间距、圆角、字号与阴影统一从 ui 导入，页面里不写魔法数字。", "間距、圓角、字級與陰影統一從 ui 匯入，頁面裡不寫魔法數字。", "Spacing, radius, type scale and elevation come from ui — no magic numbers in pages."),
    "theme.tokens.scale": ("刻度", "刻度", "Scales"),
    "theme.tokens.scale_desc": ("刻度只有有限几档：挑最接近的一档，不要现编数字。", "刻度只有有限幾檔：挑最接近的一檔，不要現編數字。", "The scales are finite: pick the nearest step instead of inventing numbers."),
    "theme.token.space": ("间距 SPACE", "間距 SPACE", "Spacing"),
    "theme.token.radius": ("圆角 RADIUS", "圓角 RADIUS", "Radius"),
    "theme.semantic.title": ("语义色", "語意色", "Semantic colors"),
    "theme.semantic.desc": ("success / warning / danger / info / neutral 与主题解耦：", "success / warning / danger / info / neutral 與主題解耦：", "success / warning / danger / info / neutral are decoupled from the theme:"),
    "theme.semantic.desc2": ("深浅模式下都保证 4.5:1 以上对比度，所以状态永远读得出来。", "深淺模式下都保證 4.5:1 以上對比度，所以狀態永遠讀得出來。", "They keep ≥4.5:1 contrast in both modes, so status is always readable."),
    "theme.role.success": ("成功", "成功", "Success"),
    "theme.role.warning": ("警告", "警告", "Warning"),
    "theme.role.danger": ("危险", "危險", "Danger"),
    "theme.role.info": ("信息", "資訊", "Info"),
    "theme.role.neutral": ("中性", "中性", "Neutral"),
    "theme.modes.title": ("明暗模式", "明暗模式", "Light and dark"),
    "theme.modes.desc": ("ThemeProvider 负责写 page.theme，并提供可订阅的状态入口。", "ThemeProvider 負責寫 page.theme，並提供可訂閱的狀態入口。", "ThemeProvider writes page.theme and exposes subscribable state."),
    "theme.trap_title": ("不要在页面里直接改 page.theme", "不要在頁面裡直接改 page.theme", "Never set page.theme in a page"),
    "theme.trap": (
        "页面组件晚一帧执行，直接改会先闪一帧旧配色。统一走 ThemeProvider 与 use_theme()。",
        "頁面元件晚一幀執行，直接改會先閃一幀舊配色。統一走 ThemeProvider 與 use_theme()。",
            (
                "Page components run a frame late, so a direct write flashes the old palette. Go through "
        "ThemeProvider and use_theme()."
    ),
    ),
    "theme.mode.system": ("跟随系统", "跟隨系統", "System"),
    "theme.mode.light": ("浅色", "淺色", "Light"),
    "theme.mode.dark": ("深色", "深色", "Dark"),
    # ---------------------------------------------------------------- 多语言
    "i18n.intro": (
        "文案、日期、数字、月份名、每周首日 —— 这些都该跟着语言变，而不是只有按钮文字。",
        "文案、日期、數字、月份名、每週首日 —— 這些都該跟著語言變，而不是只有按鈕文字。",
            (
                "Copy, dates, numbers, month names, even the first day of the week — all of it should follow "
        "the language, not just button labels."
    ),
    ),
    "i18n.live.title": ("实时切换", "即時切換", "Switch live"),
    "i18n.live.desc": ("换一种语言，格式化的输出也跟着变。", "換一種語言，格式化的輸出也跟著變。", "Change the language and the formatted output changes with it."),
    "i18n.live.point1": ("三份语言包在启动时一次载入。", "三份語言包在啟動時一次載入。", "All three catalogs load once at startup."),
    "i18n.live.point2": ("输入框里的内容不会因为切语言而丢失。", "輸入框裡的內容不會因為切語言而遺失。", "What you typed survives the switch."),
    "i18n.live.input": ("姓名", "姓名", "Name"),
    "i18n.live.value": ("肖恩", "肖恩", "Shawn"),
    "i18n.live.date": ("长日期", "長日期", "Long date"),
    "i18n.live.number": ("数字", "數字", "Number"),
    "i18n.live.list": ("列表", "清單", "List"),
    "i18n.live.time": ("短日期", "短日期", "Short date"),
    "i18n.register.title": ("注册文案", "註冊文案", "Registering copy"),
    "i18n.register.desc": ("register_messages 接受嵌套字典，也接受平铺的点号键。", "register_messages 接受巢狀字典，也接受平鋪的點號鍵。", "register_messages takes nested dicts or flat dotted keys."),
    "i18n.register.tip_title": ("回退链", "回退鏈", "Fallback chain"),
    "i18n.register.tip": (
        "繁体缺的键回退简体，再回退英文 —— 永远不会出现空白或键名。",
        "繁體缺的鍵回退簡體，再回退英文 —— 永遠不會出現空白或鍵名。",
        "Missing Traditional keys fall back to Simplified, then English — never a blank or a raw key.",
    ),
    "i18n.use.title": ("在组件里取词", "在元件裡取詞", "Reading strings"),
    "i18n.use.desc": ("组件开头调用一次 use_t()，之后用 tr(key) 取文案；它同时完成了订阅。", "元件開頭呼叫一次 use_t()，之後用 tr(key) 取文案；它同時完成了訂閱。", "Call use_t() once at the top, then tr(key): that call is also the subscription."),
    "i18n.format.title": ("格式化", "格式化", "Formatting"),
    "i18n.format.desc": ("日期、数字与日历标题都从同一层取，语言变了输出就变。", "日期、數字與月曆標題都從同一層取，語言變了輸出就變。", "Dates, numbers and calendar titles come from one layer; the language drives them."),
    "i18n.format.note_title": ("格式化也是 i18n", "格式化也是 i18n", "Formatting is i18n"),
    "i18n.format.note": (
        "“翻译了但格式还是中文的”比“没翻译”更常见：英文界面里冒出 2026 年 9 月，就是这一类。",
        "「翻譯了但格式還是中文的」比「沒翻譯」更常見：英文介面裡冒出 2026 年 9 月，就是這一類。",
            (
                "“Translated, but formatted Chinese” is more common than “untranslated”: 2026 年 9 月 in an "
        "English UI is exactly that bug."
    ),
    ),
    "i18n.fallback.title": ("回退", "回退", "Fallback"),
    "i18n.fallback.desc": ("语言包可以只翻一部分，其余按链回退。", "語言包可以只翻一部分，其餘依鏈回退。", "A catalog can be partly translated; the rest falls back."),
    "i18n.fallback.point1": ("zh_TW → zh_CN → en_US。", "zh_TW → zh_CN → en_US。", "zh_TW → zh_CN → en_US."),
    "i18n.fallback.point2": ("缺键不抛异常，只在日志里警告一次。", "缺鍵不拋例外，只在日誌裡警告一次。", "Missing keys never raise — one warning in the log."),
    "i18n.fallback.point3": ("strict=True 时缺键直接抛错，适合放进 CI。", "strict=True 時缺鍵直接拋錯，適合放進 CI。", "strict=True raises instead — put it in CI."),
    # ---------------------------------------------------------------- 组件总览
    "comp.intro": (
        "每个分类都是一个页面，页面里全是能点的真控件 —— 不是截图，也不是静态示例。",
        "每個分類都是一個頁面，頁面裡全是能點的真元件 —— 不是截圖，也不是靜態範例。",
        "Each category is a page full of real, clickable controls — not screenshots, not static samples.",
    ),
    "comp.count": ("{n} 个组件", "{n} 個元件", "{n} components"),
    "comp.stats.components": ("组件", "元件", "components"),
    "comp.stats.categories": ("分类", "分類", "categories"),
    "comp.stats.languages": ("语言", "語言", "languages"),
    "comp.stats.typed": ("类型注解", "型別註解", "typed"),
    "comp.stats.python": ("Python", "Python", "Python"),
    "comp.search.title": ("找不到想要的？", "找不到想要的？", "Can't find it?"),
    "comp.search.desc": ("打开搜索，按名称或功能快速定位。", "開啟搜尋，依名稱或功能快速定位。", "Open search and jump by name or purpose."),
    "comp.search.button": ("打开搜索", "開啟搜尋", "Open search"),
}

# ---------------------------------------------------------------- 分类页
M |= {
    "cat.general.intro": (
        "文本、按钮与图标是界面的基本颗粒。cs-ui 把它们的默认值调到“不用改就好看”。",
        "文字、按鈕與圖示是介面的基本顆粒。cs-ui 把它們的預設值調到「不用改就好看」。",
            (
                "Text, buttons and icons are the atoms of any UI. cs-ui tunes their defaults until they look "
        "right without edits."
    ),
    ),
    "cat.general.type.title": ("文本 Text", "文字 Text", "Text"),
    "cat.general.type.hint": ("五级标题、正文、引用与链接，字号取自 M3 字阶。", "五級標題、內文、引用與連結，字級取自 M3 字階。", "Five heading levels, body, quote and link — sized by the M3 type scale."),
    "cat.general.typo.body": ("正文用 14px、1.75 倍行高；中文在长段落里更耐读。", "內文用 14px、1.75 倍行高；中文在長段落裡更耐讀。", "Body copy is 14px at 1.75 line height — easier on long paragraphs."),
    "cat.general.typo.quote": ("引用块保留呼吸感，不抢正文的注意力。", "引用區塊保留呼吸感，不搶內文的注意力。", "Quotes keep their breathing room without stealing attention."),
    "cat.general.typo.link": ("链接文本", "連結文字", "A link"),
    "cat.general.button.title": ("按钮 Button", "按鈕 Button", "Buttons"),
    "cat.general.button.hint": ("六种语义样式、三种形状，plain 变体适合次要操作。", "六種語意樣式、三種形狀，plain 變體適合次要操作。", "Six semantic styles, three shapes; the plain variant suits secondary actions."),
    "cat.general.chip.title": ("标签 Chip", "標籤 Chip", "Chips"),
    "cat.general.chip.hint": ("单选与多选两种模式，选项来自语言包也能来自接口。", "單選與多選兩種模式，選項來自語言包也能來自介面。", "Single and multi-select modes; options can come from a catalog or an API."),
    "cat.general.chip.single": ("单选标签", "單選標籤", "Pick one"),
    "cat.general.chip.multi": ("多选标签", "多選標籤", "Pick several"),
    "cat.general.icon.title": ("图标与徽章 Icon", "圖示與徽章 Icon", "Icons and badges"),
    "cat.general.icon.hint": ("图标按钮、带角标的实心按钮、以及可换行的富文本提示。", "圖示按鈕、帶角標的實心按鈕，以及可換行的富文字提示。", "Icon buttons, filled buttons with badges, and a rich tooltip."),
    "cat.general.icon.love": ("收藏", "收藏", "Save"),
    "cat.general.icon.delete": ("删除", "刪除", "Delete"),
    "cat.general.icon.rich": ("悬停看富文本提示", "懸停看富文字提示", "Hover for a rich tooltip"),
    "cat.general.icon.rich_tip": ("Tooltip 支持多行文本与自定义内边距。", "Tooltip 支援多行文字與自訂內距。", "Tooltips take multi-line text and custom padding."),
    "cat.general.md.title": ("Markdown 与 JSON", "Markdown 與 JSON", "Markdown and JSON"),
    "cat.general.md.hint": ("仓库说明、变更日志这类内容可以直接渲染，不用拆成控件。", "儲存庫說明、變更日誌這類內容可以直接算繪，不用拆成元件。", "Render READMEs and changelogs directly instead of splitting them into controls."),
    "cat.general.note1": ("标题默认字号取自 M3 字阶，跨平台一致。", "標題預設字級取自 M3 字階，跨平台一致。", "Heading sizes come from the M3 scale, consistent across platforms."),
    "cat.general.note2": ("按钮高度固定 36px，横排不会参差。", "按鈕高度固定 36px，橫排不會參差。", "Buttons are 36px tall, so rows stay flush."),
    "cat.general.note3": ("Markdown 与 JSON 都是只读控件，适合展示文档与接口返回。", "Markdown 與 JSON 都是唯讀元件，適合展示文件與介面回傳。", "Markdown and JSON are read-only — good for docs and API payloads."),
    "cat.general.tip_title": ("组合优先", "組合優先", "Compose, don't configure"),
    "cat.general.tip": ("没有“超级按钮”。需要徽章就套 Badge，需要提示就套 Tooltip。", "沒有「超級按鈕」。需要徽章就套 Badge，需要提示就套 Tooltip。", "There is no mega-button. Need a badge? Wrap a Badge. A hint? Wrap a Tooltip."),

    "cat.layout.intro": (
        "布局组件决定“东西放在哪”。它们都只做一件事，组合起来才能搭出整个界面。",
        "佈局元件決定「東西放在哪」。它們都只做一件事，組合起來才能搭出整個介面。",
        (
            "Layout decides where things go. Each piece does one job; together they b"
            "uild the screen."
            ""
        ),
    ),
    "cat.layout.flex.title": ("容器与弹性布局", "容器與彈性版面", "Containers and flex"),
    "cat.layout.flex.hint": ("Row / Column 控制方向，Stack 做叠放，Container 负责留白与描边。", "Row / Column 控制方向，Stack 做疊放，Container 負責留白與描邊。", "Row/Column set direction, Stack layers, Container handles padding and borders."),
    "cat.layout.flex.container": ("Container 里的内容", "Container 裡的內容", "Inside a Container"),
    "cat.layout.list.title": ("列表与网格", "清單與格狀", "Lists and grids"),
    "cat.layout.list.hint": ("ListView 适合长列表，GridView 适合缩略图；两者都按需构建。", "ListView 適合長清單，GridView 適合縮圖；兩者都按需建構。", "ListView for long lists, GridView for thumbnails — both build lazily."),
    "cat.layout.list.item": ("第 {n} 行", "第 {n} 列", "Row {n}"),
    "cat.layout.expander.title": ("折叠面板 Expander", "摺疊面板 Expander", "Expanders"),
    "cat.layout.expander.hint": ("三种外观：描边、填充、纯文本；折叠时只占一行高度。", "三種外觀：描邊、填滿、純文字；摺疊時只佔一列高度。", "Three looks: outlined, filled and plain. Collapsed, it's one row tall."),
    "cat.layout.expander.basic": ("基础用法", "基礎用法", "Basic"),
    "cat.layout.expander.basic_sub": ("默认描边样式，适合设置项分组", "預設描邊樣式，適合設定項分組", "Outlined by default — good for settings groups"),
    "cat.layout.expander.filled": ("填充样式", "填滿樣式", "Filled"),
    "cat.layout.expander.filled_sub": ("带图标与强调色，适合放重要内容", "帶圖示與強調色，適合放重要內容", "Icon plus accent — for content that matters"),
    "cat.layout.expander.plain": ("纯文本样式", "純文字樣式", "Plain"),
    "cat.layout.expander.body1": ("展开后的内容可以是任意控件，包括表格和图表。", "展開後的內容可以是任意元件，包括表格和圖表。", "Expanded content can be anything — tables, charts, forms."),
    "cat.layout.expander.body2": ("紧凑密度下，行高与内边距同步收窄。", "緊湊密度下，列高與內距同步收窄。", "Compact density tightens rows and padding together."),
    "cat.layout.timeline.title": ("时间线 Timeline", "時間軸 Timeline", "Timeline"),
    "cat.layout.timeline.hint": ("轴在左、左右交替两种排布；done 自动变对勾，pending 在末尾挂空心环。", "軸在左、左右交替兩種排布；done 自動變對勾，pending 在末尾掛空心環。", "Left-rail or alternating; done turns into a check, pending hangs an open ring."),
    "cat.layout.timeline.t1": ("构建完成", "建置完成", "Build finished"),
    "cat.layout.timeline.t2": ("等待评审", "等待審查", "Awaiting review"),
    "cat.layout.timeline.t3": ("已排期发布", "已排程發佈", "Release scheduled"),
    "cat.layout.timeline.t4": ("文档更新", "文件更新", "Docs update"),
    "cat.layout.timeline.d1": ("3 分 12 秒，产物已上传", "3 分 12 秒，產物已上傳", "3m 12s, artifacts uploaded"),
    "cat.layout.timeline.d2": ("需要两位维护者批准", "需要兩位維護者批准", "Needs two maintainer approvals"),
    "cat.layout.timeline.d3": ("今晚 20:00 灰度 10%", "今晚 20:00 灰度 10%", "Tonight 20:00, 10% rollout"),
    "cat.layout.timeline.d4": ("等待翻译校对", "等待翻譯校對", "Waiting on translation review"),
    "cat.layout.timeline.pending": ("进行中", "進行中", "In progress"),
    "cat.layout.timeline.alt1": ("设计评审", "設計審查", "Design review"),
    "cat.layout.timeline.alt2": ("接口联调", "介面聯調", "API integration"),
    "cat.layout.timeline.alt3": ("灰度发布", "灰度發佈", "Canary release"),
    "cat.layout.table.title": ("表格 Table", "表格 Table", "Table"),
    "cat.layout.table.hint": ("表头、斑马纹与分页器打包在一起；列宽自适应内容。", "表頭、斑馬紋與分頁器打包在一起；欄寬自適應內容。", "Header, zebra rows and paging in one control; columns size to content."),
    "cat.layout.page.title": ("页面骨架 PageLayout", "頁面骨架 PageLayout", "Page layout"),
    "cat.layout.page.hint": ("标题、副标题、右侧操作区与内容区，一次给齐。", "標題、副標題、右側操作區與內容區，一次給齊。", "Title, subtitle, actions and content area in one shot."),
    "cat.layout.page.name": ("用户管理", "使用者管理", "Users"),
    "cat.layout.page.subtitle": ("共 1,286 位，本周新增 42 位", "共 1,286 位，本週新增 42 位", "1,286 total, 42 new this week"),
    "cat.layout.page.export": ("导出", "匯出", "Export"),
    "cat.layout.page.create": ("新建用户", "新增使用者", "New user"),
    "cat.layout.page.total": ("总用户", "總使用者", "Total"),
    "cat.layout.page.active": ("活跃", "活躍", "Active"),
    "cat.layout.page.pending": ("待审核", "待審核", "Pending"),
    "cat.layout.page.content": ("内容区可以放任意控件：表格、图表、表单。", "內容區可以放任意元件：表格、圖表、表單。", "The content area takes anything: tables, charts, forms."),
    "cat.layout.note1": ("列表默认按需构建，几千行也不卡。", "清單預設按需建構，幾千列也不卡。", "Lists build lazily — thousands of rows stay smooth."),
    "cat.layout.note2": ("表格分页由 PagingState 驱动，切每页条数会回到第一页。", "表格分頁由 PagingState 驅動，切每頁筆數會回到第一頁。", "Table paging is driven by PagingState; changing page size resets to page one."),
    "cat.layout.note3": ("时间线的整行可点，悬停高亮由 Material ink 绘制，不触发 Python 重绘。", "時間軸的整列可點，懸停高亮由 Material ink 繪製，不觸發 Python 重繪。", "Timeline rows are clickable; hover ink is painted by Material, not Python."),
    "cat.layout.tip_title": ("先想骨架", "先想骨架", "Start with the skeleton"),
    "cat.layout.tip": ("先用 PageLayout 定好标题与操作区，再往里塞列表或表格，比反过来快。", "先用 PageLayout 定好標題與操作區，再往裡塞清單或表格，比反過來快。", "Lay out PageLayout first, then fill it with a list or table — faster than the reverse."),

    "cat.navigation.intro": (
        "导航回答两个问题：我在哪，能去哪。面包屑答第一个，标签页与分页答第二个。",
        "導覽回答兩個問題：我在哪，能去哪。麵包屑答第一個，頁籤與分頁答第二個。",
        (
            "Navigation answers two questions: where am I, where can I go. Breadcrumb"
            "s answer the first, tabs and pagination the second."
            ""
        ),
    ),
    "cat.navigation.crumb.title": ("面包屑 BreadCrumb", "麵包屑 BreadCrumb", "Breadcrumbs"),
    "cat.navigation.crumb.hint": ("支持字符串、元组与 Crumb 三种写法，最后一项自动当当前页。", "支援字串、元組與 Crumb 三種寫法，最後一項自動當目前頁。", "Accepts strings, tuples or Crumb objects; the last item is the current page."),
    "cat.navigation.crumb.home": ("首页", "首頁", "Home"),
    "cat.navigation.crumb.components": ("组件", "元件", "Components"),
    "cat.navigation.crumb.current": ("反馈", "回饋", "Feedback"),
    "cat.navigation.crumb.a": ("工作区", "工作區", "Workspace"),
    "cat.navigation.crumb.b": ("当前页", "目前頁", "Current"),
    "cat.navigation.tabs.title": ("标签页 Tabs", "頁籤 Tabs", "Tabs"),
    "cat.navigation.tabs.hint": ("TabBar 与 TabBarView 分开挂，标签可以带图标。", "TabBar 與 TabBarView 分開掛，標籤可以帶圖示。", "TabBar and TabBarView mount separately; tabs can carry icons."),
    "cat.navigation.tabs.overview": ("概览", "概覽", "Overview"),
    "cat.navigation.tabs.detail": ("明细", "明細", "Detail"),
    "cat.navigation.tabs.settings": ("设置", "設定", "Settings"),
    "cat.navigation.tabs.overview_body": ("概览页通常放关键指标与趋势图。", "概覽頁通常放關鍵指標與趨勢圖。", "Overview pages usually hold key metrics and trends."),
    "cat.navigation.tabs.detail_body": ("明细页放可分页的表格，列多时横向滚动。", "明細頁放可分頁的表格，欄多時橫向捲動。", "Detail pages hold a paged table that scrolls sideways when wide."),
    "cat.navigation.tabs.settings_body": ("设置页多用折叠面板分组，避免一屏塞满。", "設定頁多用摺疊面板分組，避免一屏塞滿。", "Settings pages group with expanders instead of one long scroll."),
    "cat.navigation.paging.title": ("分页器 Paging", "分頁器 Paging", "Paging"),
    "cat.navigation.paging.hint": ("总数、页码、每页条数一体；数字格式与语序都跟着语言走。", "總數、頁碼、每頁筆數一體；數字格式與語序都跟著語言走。", "Total, page and page size in one control — number format and word order follow the language."),
    "cat.navigation.shell.title": ("应用外壳", "應用外殼", "App shell"),
    "cat.navigation.shell.desc": ("NavigationRail 与 AppBar 要放在外壳层，页面通过 use_route_outlet() 进来。", "NavigationRail 與 AppBar 要放在外殼層，頁面透過 use_route_outlet() 進來。", "NavigationRail and AppBar belong to the shell; pages arrive through use_route_outlet()."),
    "cat.navigation.shell.tip_title": ("外壳只渲染一次", "外殼只算繪一次", "The shell renders once"),
    "cat.navigation.shell.tip": ("外壳放在父路由上，切页时侧栏与顶栏不重建，滚动位置也更稳。", "外殼放在父路由上，切頁時側欄與頂欄不重建，捲動位置也更穩。", "Keep the shell on the parent route: sidebars and top bars survive navigation."),
    "cat.navigation.note1": ("面包屑最后一项默认不可点，因为它就是当前页。", "麵包屑最後一項預設不可點，因為它就是目前頁。", "The last crumb isn't clickable — it is the current page."),
    "cat.navigation.note2": ("分页器的单位（项 / 頁 / items）留空时跟随语言，要业务量词再显式传。", "分頁器的單位（項 / 頁 / items）留空時跟隨語言，要業務量詞再明確傳。", "Leave the paging unit empty to follow the language; pass a business noun when you need one."),
    "cat.navigation.tip_title": ("少一层导航", "少一層導覽", "One less layer"),
    "cat.navigation.tip": ("三个以上层级就别用面包屑了，换成标签页或侧边栏更清楚。", "三個以上層級就別用麵包屑了，換成頁籤或側邊欄更清楚。", "Beyond three levels, drop breadcrumbs for tabs or a sidebar."),

    "cat.form.intro": (
        "表单是最容易露怯的地方：标签对不齐、宽度乱跳、切语言丢内容。这一页的控件都处理过这些。",
        "表單是最容易露怯的地方：標籤對不齊、寬度亂跳、切語言丟內容。這一頁的元件都處理過這些。",
        (
            "Forms expose sloppiness fastest: ragged labels, jumping widths, input lo"
            "st on language switch. These controls handle it."
            ""
        ),
    ),
    "cat.form.input.title": ("输入框 Input", "輸入框 Input", "Text inputs"),
    "cat.form.input.hint": ("带标签、必填星号与类型校验；data_type 决定回读的类型。", "帶標籤、必填星號與型別驗證；data_type 決定回讀的型別。", "Label, required marker and type validation; data_type decides the read-back type."),
    "cat.form.choice.title": ("勾选、开关与单选", "勾選、開關與單選", "Checks, switches, radios"),
    "cat.form.choice.hint": ("CheckboxGroup 与 Radio 的选项横排竖排都行，必填会标星号。", "CheckboxGroup 與 Radio 的選項橫排直排都行，必填會標星號。", "CheckboxGroup and Radio lay out either way; required fields get a star."),
    "cat.form.select.title": ("下拉与多选", "下拉與多選", "Selects"),
    "cat.form.select.hint": ("SelectBox 单选，MultiSelect 多选；面板悬挂在内容之上，不推动布局。", "SelectBox 單選，MultiSelect 多選；面板懸掛在內容之上，不推動版面。", "SelectBox picks one, MultiSelect many; the panel floats above content without pushing layout."),
    "cat.form.date.title": ("日期与时间", "日期與時間", "Dates and times"),
    "cat.form.date.hint": ("月历、时间轮盘与本地化格式；每周首日跟着语言走。", "月曆、時間輪盤與本地化格式；每週首日跟著語言走。", "Calendar, time wheel and localized formats; the week starts on the language's first day."),
    "cat.form.slider.title": ("滑块 Slider", "滑桿 Slider", "Sliders"),
    "cat.form.slider.hint": ("单值与区间两种；刻度、提示气泡与步长都可调。", "單值與區間兩種；刻度、提示氣泡與步長都可調。", "Single value or range; ticks, value bubble and step are configurable."),
    "cat.form.rating.title": ("评分 Rating", "評分 Rating", "Rating"),
    "cat.form.rating.hint": ("可交互、只读与禁用三态。", "可互動、唯讀與停用三態。", "Interactive, read-only and disabled."),
    "cat.form.segment.title": ("分段按钮 SegmentedButton", "分段按鈕 SegmentedButton", "Segmented button"),
    "cat.form.segment.hint": ("三五个互斥选项用分段按钮，比下拉少一次点击。", "三五個互斥選項用分段按鈕，比下拉少一次點擊。", "For three to five exclusive options, segmented beats a dropdown by a click."),
    "cat.form.color.title": ("取色器 ColorPicker", "取色器 ColorPicker", "Color picker"),
    "cat.form.color.hint": ("支持带透明度的十六进制值，预设色板可调列数。", "支援帶透明度的十六進位值，預設色盤可調欄數。", "Accepts hex with alpha; preset swatch columns are adjustable."),
    "cat.form.search.title": ("搜索 SearchBar", "搜尋 SearchBar", "Search bar"),
    "cat.form.search.hint": ("点击后展开建议列表，适合从一长串候选项里挑。", "點擊後展開建議清單，適合從一長串候選項裡挑。", "Expands a suggestion list — good for picking from long candidates."),
    "cat.form.note1": ("标签宽度统一，横排时不会参差。", "標籤寬度統一，橫排時不會参差。", "Labels share one width, so columns line up."),
    "cat.form.note2": ("必填项在标签前加红星，不需要另写提示。", "必填項在標籤前加紅星，不需要另寫提示。", "Required fields get a red star — no extra hint needed."),
    "cat.form.note3": ("下拉面板与月历通过 page.overlay 悬挂，展开不改变布局高度。", "下拉面板與月曆透過 page.overlay 懸掛，展開不改變版面高度。", "Flyouts and calendars hang in page.overlay; opening them never shifts layout."),
    "cat.form.tip_title": ("用 use_ref 固定实例", "用 use_ref 固定實例", "Pin instances with use_ref"),
    "cat.form.tip": ("表单控件放 use_ref，父组件重绘不会重建，用户输入才留得住。", "表單元件放 use_ref，父元件重繪不會重建，使用者輸入才留得住。", "Keep form controls in use_ref so parent re-renders don't rebuild them."),
    "cat.form.tip2_title": ("切语言不丢内容", "切語言不遺失內容", "Language switches keep values"),
    "cat.form.tip2": ("切语言只会重绘文案；控件实例被复用，所以填了一半的表单还是原来那份。", "切語言只會重繪文案；元件實例被重用，所以填了一半的表單還是原來那份。", "Switching language re-renders labels only; instances are reused, so a half-filled form stays filled."),

    "cat.feedback.intro": (
        "反馈要分层：不打断的用轻提示，需要确认的用对话框，长任务用进度。",
        "回饋要分層：不打斷的用輕提示，需要確認的用對話框，長任務用進度。",
        (
            "Feedback comes in layers: toasts that do not interrupt, dialogs that con"
            "firm, progress for long tasks."
            ""
        ),
    ),
    "cat.feedback.toast.title": ("轻提示 Toast", "輕提示 Toast", "Toasts"),
    "cat.feedback.toast.hint": ("六种语义样式，右下角浮出，两秒后自动消失。", "六種語意樣式，右下角浮出，兩秒後自動消失。", "Six semantic styles, floating bottom-right, gone in two seconds."),
    "cat.feedback.style.default": ("默认", "預設", "Default"),
    "cat.feedback.style.primary": ("主要", "主要", "Primary"),
    "cat.feedback.style.info": ("信息", "資訊", "Info"),
    "cat.feedback.style.success": ("成功", "成功", "Success"),
    "cat.feedback.style.warning": ("警告", "警告", "Warning"),
    "cat.feedback.style.error": ("错误", "錯誤", "Error"),
    "cat.feedback.toast.msg": ("这是一条{kind}提示", "這是一條{kind}提示", "A {kind} toast"),
    "cat.feedback.dialog.title": ("对话框与消息条", "對話框與訊息列", "Dialogs and messages"),
    "cat.feedback.dialog.hint": ("确认类操作走对话框，说明类信息走底部消息条。", "確認類操作走對話框，說明類資訊走底部訊息列。", "Confirmations use a dialog; explanations use a bottom message bar."),
    "cat.feedback.dialog.open": ("打开对话框", "開啟對話框", "Open dialog"),
    "cat.feedback.dialog.title2": ("删除这个文件？", "刪除這個檔案？", "Delete this file?"),
    "cat.feedback.dialog.msg": ("删除后无法恢复，请确认。", "刪除後無法復原，請確認。", "This can't be undone. Are you sure?"),
    "cat.feedback.dialog.done": ("已删除", "已刪除", "Deleted"),
    "cat.feedback.dialog.cancel": ("已取消", "已取消", "Cancelled"),
    "cat.feedback.message.open": ("显示消息条", "顯示訊息列", "Show message"),
    "cat.feedback.message.body": ("这是一条消息条，适合放不需要用户决策的说明。", "這是一條訊息列，適合放不需要使用者決策的說明。", "A message bar — for notes that need no decision."),
    "cat.feedback.progress.title": ("进度与加载", "進度與載入", "Progress and loading"),
    "cat.feedback.progress.hint": ("确定的进度用进度条，不确定的用环形加载。", "確定的進度用進度條，不確定的用環形載入。", "Known progress gets a bar; unknown gets a ring."),
    "cat.feedback.progress.download": ("下载中 72%", "下載中 72%", "Downloading 72%"),
    "cat.feedback.progress.index": ("索引中（按百分比传值）", "索引中（依百分比傳值）", "Indexing (percent in)"),
    "cat.feedback.progress.loading": ("三种尺寸的加载环", "三種尺寸的載入環", "Three ring sizes"),
    "cat.feedback.note1": ("轻提示不会抢焦点，也不阻塞操作。", "輕提示不會搶焦點，也不阻塞操作。", "Toasts never steal focus and never block."),
    "cat.feedback.note2": ("对话框的按钮文案来自语言包，切的不是主色而是语义。", "對話框的按鈕文案來自語言包，切的不是主色而是語意。", "Dialog buttons come from the catalog — semantics, not colors, pick them."),
    "cat.feedback.note3": ("进度条接受 0–1 的小数，也接受 0–100 的整数。", "進度條接受 0–1 的小數，也接受 0–100 的整數。", "Progress bars take 0–1 floats or 0–100 ints."),
    "cat.feedback.tip_title": ("别用对话框做提示", "別用對話框做提示", "Don't use dialogs for notices"),
    "cat.feedback.tip": ("只告知不询问，就用轻提示或消息条；对话框留给“必须选一个”的时刻。", "只告知不詢問，就用輕提示或訊息列；對話框留給「必須選一個」的時刻。", "If nothing to decide, use a toast or message. Dialogs are for “pick one”."),
    "cat.feedback.tip2_title": ("错误要说清下一步", "錯誤要說清下一步", "Errors need a next step"),
    "cat.feedback.tip2": ("“保存失败”不如“磁盘已满，请清理后重试”。", "「儲存失敗」不如「磁碟已滿，請清理後重試」。", "“Save failed” is worse than “Disk full — free some space and retry”."),

    "cat.display.intro": (
        "展示型控件负责把数据摆好看：列表项、代码与日志。",
        "展示型元件負責把資料擺好看：清單項、程式碼與日誌。",
        (
            "Display controls make data presentable: list tiles, code and logs."
            ""
            ""
        ),
    ),
    "cat.display.tile.title": ("列表项 ListTile", "清單項 ListTile", "List tiles"),
    "cat.display.tile.hint": ("头像、标题、副标题与尾部操作，一行说清一件事。", "頭像、標題、副標題與尾端操作，一列說清一件事。", "Avatar, title, subtitle and trailing action — one row, one thing."),
    "cat.display.tile.more": ("更多", "更多", "More"),
    "cat.display.editor.title": ("代码编辑器 CodeEditor", "程式碼編輯器 CodeEditor", "Code editor"),
    "cat.display.editor.hint": ("带行号与语法高亮的可编辑区域，read_only 即为代码块。", "帶行號與語法高亮的可編輯區域，read_only 即為程式碼區塊。", "Editable with line numbers and highlighting; read_only turns it into a code block."),
    "cat.display.view.title": ("代码视图 CodeView", "程式碼檢視 CodeView", "Code view"),
    "cat.display.view.hint": ("一个组件配一段可展开的源码，适合做“这个控件怎么用”。", "一個元件配一段可展開的原始碼，適合做「這個元件怎麼用」。", "A live control plus collapsible source — perfect for “how do I use this”."),
    "cat.display.view.preview": ("这是预览区", "這是預覽區", "This is the preview"),
    "cat.display.note1": ("代码主题跟随明暗模式，浅色界面里也能看清。", "程式碼主題跟隨明暗模式，淺色介面裡也能看清。", "Code themes follow light/dark so contrast always holds."),
    "cat.display.note2": ("ListTile 的 trailing 可以放开关、按钮或角标。", "ListTile 的 trailing 可以放開關、按鈕或角標。", "ListTile trailing takes switches, buttons or badges."),
    "cat.display.note3": ("CodeView 折叠时只占一行，展开后不挤压周围内容。", "CodeView 摺疊時只佔一列，展開後不擠壓周圍內容。", "Collapsed CodeView is one row; expanded it doesn't squeeze neighbours."),
    "cat.display.tip_title": ("代码也属于界面", "程式碼也屬於介面", "Code is UI too"),
    "cat.display.tip": ("技术产品的文档里，代码块的可读性和正文一样重要。", "技術產品的文件裡，程式碼區塊的可讀性和內文一樣重要。", "In developer docs a code block matters as much as the prose."),

    "cat.charts.intro": (
        "图表封装了配色、轴范围与提示气泡；传数据就能出图。",
        "圖表封裝了配色、軸範圍與提示氣泡；傳資料就能出圖。",
        (
            "Charts bundle colours, axis ranges and tooltips — pass data, get a chart"
            "."
            ""
        ),
    ),
    "cat.charts.line.title": ("折线与面积", "折線與面積", "Line and area"),
    "cat.charts.line.hint": ("多列即多条线，x 轴数值与分类通吃。", "多欄即多條線，x 軸數值與分類通吃。", "Multiple columns become multiple lines; x takes numbers or categories."),
    "cat.charts.bar.title": ("柱状", "長條", "Bar"),
    "cat.charts.bar.hint": ("分组与堆叠两种，柱子圆角统一。", "分組與堆疊兩種，柱子圓角統一。", "Grouped or stacked, with consistent corner radius."),
    "cat.charts.scatter.title": ("散点", "散佈", "Scatter"),
    "cat.charts.scatter.hint": ("传 (x, y) 元组列表即可，适合看相关性。", "傳 (x, y) 元組清單即可，適合看相關性。", "Feed it (x, y) tuples — good for spotting correlation."),
    "cat.charts.tip_title": ("颜色跟着主题", "顏色跟著主題", "Colors follow the theme"),
    "cat.charts.tip": ("不传 color 时使用与主题协调的色板，换主色后图表也跟着变。", "不傳 color 時使用與主題協調的色盤，換主色後圖表也跟著變。", "Omit color to inherit a palette that tracks your seed color."),

    "cat.media.intro": (
        "媒体控件把播放状态、进度与封面打包好，直接放进内容流里。",
        "媒體元件把播放狀態、進度與封面打包好，直接放進內容流裡。",
        (
            "Media controls wrap playback state, progress and cover art for the conte"
            "nt flow."
            ""
        ),
    ),
    "cat.media.audio.title": ("音频 Audio", "音訊 Audio", "Audio"),
    "cat.media.audio.hint": ("AudioPlayer 是卡片式播放器；Audio 本身是 Service，构造即注册。", "AudioPlayer 是卡片式播放器；Audio 本身是 Service，建構即註冊。", "AudioPlayer is the card player; Audio itself is a service — constructing it registers it."),
    "cat.media.audio.track": ("夜航", "夜航", "Night drive"),
    "cat.media.audio.track2": ("第二首", "第二首", "Second track"),
    "cat.media.audio.artist": ("示例音轨 · SoundHelix", "範例音軌 · SoundHelix", "Sample track · SoundHelix"),
    "cat.media.video.title": ("视频 Video", "影片 Video", "Video"),
    "cat.media.video.hint": ("单视频或播放列表；控件自带播放条与全屏。", "單一影片或播放清單；元件自帶播放列與全螢幕。", "Single file or playlist; the player ships with controls and fullscreen."),
    "cat.media.video.playlist": ("播放列表", "播放清單", "Playlist"),
    "cat.media.pdf.title": ("PDF 阅读 Pdf", "PDF 閱讀 Pdf", "PDF"),
    "cat.media.pdf.hint": ("内嵌阅读器，支持滚动与翻页。", "內嵌閱讀器，支援捲動與翻頁。", "An embedded reader with scrolling and paging."),
    "cat.media.pdf.doc": ("示例文档", "範例文件", "Sample document"),
    "cat.media.note1": ("播放状态是 observable 的，界面可以跟着变。", "播放狀態是 observable 的，介面可以跟著變。", "Playback state is observable, so the UI can react."),
    "cat.media.note2": ("远程地址与本地路径都接受，网络资源需要允许访问。", "遠端位址與本機路徑都接受，網路資源需要允許存取。", "Remote URLs and local paths both work, given network permission."),
    "cat.media.tip_title": ("大文件别内嵌", "大檔案別內嵌", "Don't inline big files"),
    "cat.media.tip": ("几十页的 PDF 嵌在页面里会很重，给出入口比内嵌更合适。", "幾十頁的 PDF 嵌在頁面裡會很重，給出入口比內嵌更合適。", "A 40-page PDF inline is heavy; link out instead."),

    "cat.upload.intro": (
        "文件链路有三段：选文件、选目录、选保存位置。三者的结果都直接读 value。",
        "檔案鏈路有三段：選檔案、選目錄、選儲存位置。三者的結果都直接讀 value。",
        (
            "Files come in three steps: pick a file, a folder, a save target. All exp"
            "ose value."
            ""
        ),
    ),
    "cat.upload.picker.title": ("文件、目录与保存", "檔案、目錄與儲存", "Files, folders, saving"),
    "cat.upload.picker.hint": ("allowed_extensions 限定类型；allow_multiple 控制多选。", "allowed_extensions 限定型別；allow_multiple 控制多選。", "allowed_extensions filters types; allow_multiple enables multi-select."),
    "cat.upload.read": ("读取选择结果", "讀取選擇結果", "Read the values"),
    "cat.upload.dump": ("文件 {files} 个 · 目录 {folder} · 保存到 {save}", "檔案 {files} 個 · 目錄 {folder} · 儲存到 {save}", "{files} file(s) · folder {folder} · save to {save}"),
    "cat.upload.image.title": ("图片选择 ImagePicker", "圖片選擇 ImagePicker", "Image picker"),
    "cat.upload.image.hint": ("带缩略预览的图片选择器，适合头像与封面。", "帶縮圖預覽的圖片選擇器，適合頭像與封面。", "An image picker with thumbnail preview — avatars, covers."),
    "cat.upload.image.label": ("头像", "頭像", "Avatar"),
    "cat.upload.tip_title": ("先校验再上传", "先驗證再上傳", "Validate before uploading"),
    "cat.upload.tip": ("allowed_extensions 只是第一道门；大小与内容还得在提交时再查一次。", "allowed_extensions 只是第一道門；大小與內容還得在提交時再查一次。", "allowed_extensions is only the first gate — check size and content on submit."),
    "cat.upload.tip2_title": ("路径可能为空", "路徑可能為空", "Paths can be empty"),
    "cat.upload.tip2": ("用户取消选择时 value 保持原值或为空，回读前先判空。", "使用者取消選擇時 value 保持原值或為空，回讀前先判空。", "If the user cancels, value stays empty — guard before reading."),

    # ---------------------------------------------------------------- 关于
    "about.intro": (
        "cs-ui 是一个开源项目：MIT 许可，代码在 GitHub 上，问题是公开的，改动也是。",
        "cs-ui 是一個開源專案：MIT 授權，程式碼在 GitHub 上，問題是公開的，改動也是。",
        "cs-ui is open source: MIT licensed, code on GitHub, issues and changes in the open.",
    ),
    "about.runtime.title": ("运行时", "執行時", "Runtime"),
    "about.row.version": ("版本", "版本", "Version"),
    "about.row.flet": ("Flet", "Flet", "Flet"),
    "about.row.python": ("Python", "Python", "Python"),
    "about.row.license": ("许可", "授權", "License"),
    "about.row.components": ("组件数", "元件數", "Components"),
    "about.principles.title": ("设计原则", "設計原則", "Principles"),
    "about.principles.desc": ("这几条决定了 cs-ui 长什么样，也决定了它不做什么。", "這幾條決定了 cs-ui 長什麼樣，也決定了它不做什麼。", "These rules decide what cs-ui looks like — and what it refuses to do."),
    "about.principle1": ("默认值优先：组件不传参数就该好看，参数只用来表达差异。", "預設值優先：元件不傳參數就該好看，參數只用來表達差異。", "Defaults first: a component with no arguments should already look right."),
    "about.principle2": ("令牌而不是常量：颜色、间距、圆角都从一处来，换肤不用搜代码。", "權杖而不是常數：顏色、間距、圓角都從一處來，換膚不用搜程式碼。", "Tokens, not constants: color, spacing and radius come from one place."),
    "about.principle3": ("订阅而不是广播：只有真正读了状态的组件才重绘。", "訂閱而不是廣播：只有真正讀了狀態的元件才重繪。", "Subscriptions, not broadcasts: only components that read state re-render."),
    "about.principle4": ("可组合而不是可配置：需要新外观就组合，不要加第十个布尔参数。", "可組合而不是可配置：需要新外觀就組合，不要加第十個布林參數。", "Compose, don't configure: new looks come from composition, not a tenth boolean."),
    "about.links.title": ("相关链接", "相關連結", "Links"),
    "about.link.github": ("GitHub 仓库", "GitHub 儲存庫", "GitHub repository"),
    "about.link.flet": ("Flet 官方文档", "Flet 官方文件", "Flet documentation"),
    "about.link.license": ("许可与贡献指南", "授權與貢獻指南", "License and contributing"),
}

#: 数组型文案（模板按顺序取 ``key.0`` / ``key.1`` …）
L: dict[str, tuple[list[str], list[str], list[str]]] = {
    "demo.options": (
        ["选项 A", "选项 B", "选项 C"],
        ["選項 A", "選項 B", "選項 C"],
        ["Option A", "Option B", "Option C"],
    ),
    "demo.stack": (
        ["Python", "Flet", "Material 3"],
        ["Python", "Flet", "Material 3"],
        ["Python", "Flet", "Material 3"],
    ),
    "demo.tags": (
        ["设计", "工程", "文档", "发布"],
        ["設計", "工程", "文件", "發佈"],
        ["Design", "Engineering", "Docs", "Release"],
    ),
    "demo.cities": (
        ["北京", "上海", "广州", "深圳", "杭州"],
        ["北京", "上海", "廣州", "深圳", "杭州"],
        ["Beijing", "Shanghai", "Guangzhou", "Shenzhen", "Hangzhou"],
    ),
    "demo.plans": (
        ["免费版", "专业版", "团队版"],
        ["免費版", "專業版", "團隊版"],
        ["Free", "Pro", "Team"],
    ),
    "demo.hobbies": (
        ["阅读", "徒步", "摄影"],
        ["閱讀", "健行", "攝影"],
        ["Reading", "Hiking", "Photography"],
    ),
    "demo.views": (
        ["列表", "网格", "看板"],
        ["清單", "格狀", "看板"],
        ["List", "Grid", "Board"],
    ),
    "demo.chart.months": (
        ["1 月", "2 月", "3 月", "4 月", "5 月", "6 月", "7 月", "8 月"],
        ["1 月", "2 月", "3 月", "4 月", "5 月", "6 月", "7 月", "8 月"],
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"],
    ),
}

#: 单独补的短键（上面按主题分了块，这里集中放零散的演示字段）
M |= {
    "demo.field.name": ("姓名", "姓名", "Name"),
    "demo.field.age": ("年龄", "年齡", "Age"),
    "demo.field.budget": ("预算", "預算", "Budget"),
    "demo.field.folder": ("项目目录", "專案目錄", "Project folder"),
    "demo.field.agree": ("我已阅读并同意条款", "我已閱讀並同意條款", "I accept the terms"),
    "demo.field.hobbies": ("兴趣爱好", "興趣愛好", "Interests"),
    "demo.field.notify": ("接收通知", "接收通知", "Notifications"),
    "demo.field.compact": ("紧凑模式", "緊湊模式", "Compact mode"),
    "demo.field.plan": ("订阅方案", "訂閱方案", "Plan"),
    "demo.field.city": ("城市", "城市", "City"),
    "demo.field.tags": ("标签", "標籤", "Tags"),
    "demo.field.birthday": ("生日", "生日", "Birthday"),
    "demo.field.meeting": ("会议时间", "會議時間", "Meeting"),
    "demo.field.volume": ("音量", "音量", "Volume"),
    "demo.field.price": ("价格区间", "價格區間", "Price range"),
    "demo.field.brand": ("品牌色", "品牌色", "Brand color"),
    "demo.field.overlay": ("叠加色（带透明度）", "疊加色（帶透明度）", "Overlay (with alpha)"),
    "demo.rating.editable": ("可交互", "可互動", "Interactive"),
    "demo.rating.readonly": ("只读", "唯讀", "Read-only"),
    "demo.rating.disabled": ("禁用", "停用", "Disabled"),
    "demo.search.bar": ("搜索城市", "搜尋城市", "Search cities"),
    "demo.search.view": ("输入城市名", "輸入城市名", "Type a city"),
    "demo.search.hint": ("点击后展开建议列表。", "點擊後展開建議清單。", "Click to expand suggestions."),
    "demo.col.name": ("用户名", "使用者名稱", "User"),
    "demo.col.email": ("邮箱", "電子郵件", "Email"),
    "demo.col.age": ("年龄", "年齡", "Age"),
    "demo.col.status": ("状态", "狀態", "Status"),
    "demo.col.active": ("活跃", "活躍", "Active"),
    "demo.col.paused": ("已暂停", "已暫停", "Paused"),
    "demo.chart.month": ("月份", "月份", "Month"),
    "demo.chart.online": ("线上", "線上", "Online"),
    "demo.chart.offline": ("线下", "線下", "Offline"),
}


def build() -> dict[str, dict[str, str]]:
    """按语言装配三份扁平表。"""
    locales = ("zh-CN", "zh-TW", "en-US")
    for table, name in ((M, "M"), (L, "L")):
        for key, triple in table.items():
            # 写成裸字符串会静默取到首字符（"表单…" → "表"），所以在装配前就拦住。
            if not isinstance(triple, tuple) or len(triple) != len(locales):
                raise SystemExit(f"{name}[{key!r}] 必须是 {len(locales)} 元组，实际是 {triple!r}")
    tables: dict[str, dict[str, str]] = {code: {} for code in locales}
    for key, triple in M.items():
        for index, code in enumerate(locales):
            tables[code][key] = triple[index]
    for key, triple in L.items():
        for index, code in enumerate(locales):
            for position, item in enumerate(triple[index]):
                tables[code][f"{key}.{position}"] = item
    return tables


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="生成文档站三语语言包")
    parser.add_argument("--check", action="store_true", help="只校验，不写盘")
    args = parser.parse_args(argv)

    tables = build()
    sizes = {code: len(table) for code, table in tables.items()}
    if len(set(sizes.values())) != 1:
        print(f"键数不一致：{sizes}", file=sys.stderr)
        return 1

    if not args.check:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        for code, table in tables.items():
            (OUT_DIR / f"{code.replace('-', '_')}.json").write_text(
                json.dumps(table, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
    print(f"{len(tables['zh-CN'])} keys × {len(tables)} languages → {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
