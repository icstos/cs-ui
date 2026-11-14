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
    "nav.home.desc": (
        "cs-ui 是什么，以及它长什么样",
        "cs-ui 是什麼，以及它長什麼樣",
        "What cs-ui is, and what it looks like",
    ),
    "nav.quickstart.title": ("快速开始", "快速開始", "Quick start"),
    "nav.quickstart.desc": (
        "五分钟装好，渲染第一个界面",
        "五分鐘裝好，算繪第一個介面",
        "Install and render your first window in five minutes",
    ),
    "nav.architecture.title": ("架构", "架構", "Architecture"),
    "nav.architecture.desc": (
        "分层、两类组件、Provider 顺序与路由",
        "分層、兩類元件、Provider 順序與路由",
        "Layers, two kinds of components, providers and routing",
    ),
    "nav.theming.title": ("主题与令牌", "主題與權杖", "Theme & tokens"),
    "nav.theming.desc": (
        "Material 3 配色、明暗模式与设计令牌",
        "Material 3 配色、明暗模式與設計權杖",
        "Material 3 colors, light/dark modes and design tokens",
    ),
    "nav.i18n.title": ("多语言", "多語言", "Internationalization"),
    "nav.i18n.desc": (
        "运行时切换语言，连日期与数字格式一起变",
        "執行時切換語言，連日期與數字格式一起變",
        "Switch language at runtime — dates and numbers follow",
    ),
    "nav.responsive.title": ("响应式", "響應式", "Responsive"),
    "nav.responsive.desc": (
        "窗口变窄时，栅格与页头怎么自己适应",
        "視窗變窄時，柵格與頁首怎麼自己適應",
        "How grids and page headers adapt when the window narrows",
    ),
    "nav.components.title": ("组件总览", "元件總覽", "All components"),
    "nav.components.desc": (
        "按分类浏览 cs-ui 的全部组件",
        "依分類瀏覽 cs-ui 的全部元件",
        "Browse every cs-ui component by category",
    ),
    "nav.general.title": ("通用", "通用", "General"),
    "nav.general.desc": (
        "文本、按钮、图标、标签与 Markdown",
        "文字、按鈕、圖示、標籤與 Markdown",
        "Text, buttons, icons, chips and Markdown",
    ),
    "nav.layout.title": ("布局", "版面", "Layout"),
    "nav.layout.desc": (
        "容器、列表、折叠面板、步骤条与表格",
        "容器、清單、摺疊面板、步驟條與表格",
        "Containers, lists, expanders, steps and tables",
    ),
    "nav.navigation.title": ("导航", "導覽", "Navigation"),
    "nav.navigation.desc": (
        "面包屑、标签页、分页器与应用外壳",
        "麵包屑、頁籤、分頁器與應用外殼",
        "Breadcrumbs, tabs, paging and app shells",
    ),
    "nav.form.title": ("表单", "表單", "Form"),
    "nav.form.desc": (
        "输入、选择、日期、滑块与取色",
        "輸入、選擇、日期、滑桿與取色",
        "Inputs, choices, dates, sliders and colors",
    ),
    "nav.feedback.title": ("反馈", "回饋", "Feedback"),
    "nav.feedback.desc": (
        "消息提示、通知、对话框与进度",
        "訊息提示、通知、對話框與進度",
        "Messages, notifications, dialogs and progress",
    ),
    "nav.display.title": ("数据展示", "資料展示", "Display"),
    "nav.display.desc": (
        "列表项、代码、树与描述列表",
        "清單項、程式碼、樹與描述清單",
        "List tiles, code, trees and descriptions",
    ),
    "nav.charts.title": ("图表", "圖表", "Charts"),
    "nav.charts.desc": (
        "折线、面积、柱状与散点",
        "折線、面積、長條與散佈",
        "Line, area, bar and scatter charts",
    ),
    "nav.media.title": ("媒体", "媒體", "Media"),
    "nav.media.desc": ("音频、视频与 PDF", "音訊、影片與 PDF", "Audio, video and PDF"),
    "nav.upload.title": ("文件选择", "檔案選擇", "Files"),
    "nav.upload.desc": (
        "文件、目录、保存与图片",
        "檔案、目錄、儲存與圖片",
        "Files, folders, saving and images",
    ),
    "nav.about.title": ("关于", "關於", "About"),
    "nav.about.desc": (
        "版本、设计原则与相关链接",
        "版本、設計原則與相關連結",
        "Version, principles and links",
    ),
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
    "site.nav.open": ("打开导航", "開啟導航", "Open navigation"),
    "site.search.placeholder": (
        "搜索文档与组件",
        "搜尋文件與元件",
        "Search docs and components",
    ),
    "site.search.tooltip": ("打开搜索", "開啟搜尋", "Open search"),
    "site.search.close": ("关闭", "關閉", "Close"),
    "site.search.enter": ("打开第一条", "開啟第一條", "Open the first result"),
    "site.search.count": ("{n} 条结果", "{n} 筆結果", "{n} results"),
    "site.search.empty": (
        "没有找到“{query}”",
        "找不到「{query}」",
        "No results for “{query}”",
    ),
    "site.search.pages": ("页面", "頁面", "Pages"),
    "site.search.components": ("组件", "元件", "Components"),
    "site.theme.to_light": ("切到浅色", "切到淺色", "Switch to light"),
    "site.theme.to_dark": ("切到深色", "切到深色", "Switch to dark"),
    "site.sidebar.runtime": (
        "Flet {flet} · Python {python}",
        "Flet {flet} · Python {python}",
        "Flet {flet} · Python {python}",
    ),
    "site.sidebar.license": ("MIT License", "MIT License", "MIT License"),
    "site.footer.tagline": (
        "基于 Flet 的声明式 Python 桌面界面组件库",
        "基於 Flet 的宣告式 Python 桌面介面元件庫",
        "A declarative Python UI kit for desktop, built on Flet",
    ),
    "site.footer.license": (
        "© 2026 cs-ui · MIT · v{version}",
        "© 2026 cs-ui · MIT · v{version}",
        "© 2026 cs-ui · MIT · v{version}",
    ),
    "site.crumb.docs": ("文档", "文件", "Docs"),
    "site.crumb.components": ("组件", "元件", "Components"),
    "site.demo.preview": ("预览", "預覽", "Preview"),
    "site.demo.code": ("代码", "程式碼", "Code"),
    "site.notfound.title": (
        "这个页面不存在",
        "這個頁面不存在",
        "This page doesn't exist",
    ),
    "site.notfound.desc": (
        "链接可能已经失效，或者地址敲错了。\n用搜索找找看，或者回到首页。",
        "連結可能已經失效，或位址打錯了。\n用搜尋找找看，或回到首頁。",
        "The link may be out of date, or the address is off.\nTry searching, or head back home.",
    ),
    "site.notfound.home": ("回到首页", "回到首頁", "Back home"),
    "site.notfound.search": ("搜索文档", "搜尋文件", "Search docs"),
    # ---------------------------------------------------------------- 首页
    "home.eyebrow": (
        "v{version} · 声明式桌面界面",
        "v{version} · 宣告式桌面介面",
        "v{version} · declarative desktop UI",
    ),
    "home.title": (
        "用 Python\n构建桌面界面",
        "用 Python\n建構桌面介面",
        "Build desktop UIs\nin Python",
    ),
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
    "home.cta.desc": (
        "从安装到第一个可交互界面，只需要几分钟。",
        "從安裝到第一個可互動介面，只需要幾分鐘。",
        "From install to your first interactive window in a few minutes.",
    ),
    "home.cta.source": ("查看源码", "檢視原始碼", "View source"),
    "home.meta.python": ("Python {version}", "Python {version}", "Python {version}"),
    "home.meta.license": ("MIT 许可", "MIT 授權", "MIT licensed"),
    "home.window.title": ("运行概览", "執行概覽", "Overview"),
    "home.window.subtitle": (
        "今天的活跃用户",
        "今天的活躍使用者",
        "Active users today",
    ),
    "home.window.stat1": ("1,286", "1,286", "1,286"),
    "home.window.stat1_label": ("活跃用户", "活躍使用者", "Active users"),
    "home.window.stat2": ("42.8k", "42.8k", "42.8k"),
    "home.window.stat2_label": ("会话", "工作階段", "Sessions"),
    "home.window.chart": ("近 8 周趋势", "近 8 週趨勢", "Last 8 weeks"),
    "home.stats.components": ("组件", "元件", "components"),
    "home.stats.categories": ("分类", "分類", "categories"),
    "home.stats.languages": ("语言", "語言", "languages"),
    "home.stats.typed": ("类型注解", "型別註解", "typed"),
    "home.feature.title": (
        "一次把重复的界面工程做完",
        "一次把重複的介面工程做完",
        "Do the boring UI work once",
    ),
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
        "一个品牌色算出整套 M3 色板（46 个角色），明暗切换即时生效。",
        "一個品牌色算出整套 M3 色盤（46 個角色），明暗切換即時生效。",
        "One brand color becomes all 46 M3 roles; light/dark flips instantly.",
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
        "为鼠标与键盘优化：悬停、密度与滚动；窗口变窄自动收起侧栏与目录。",
        "為滑鼠與鍵盤最佳化：懸停、密度與捲動；視窗變窄自動收起側欄與目錄。",
        "Tuned for mouse and keyboard — hover, density, scrolling — and it folds the sidebar and "
        "outline away when the window narrows.",
    ),
    "home.showcase.title": ("组件都在这儿", "元件都在這裡", "Every component, live"),
    "home.showcase.subtitle": (
        "下面是真控件，不是截图。",
        "下面是真元件，不是截圖。",
        "Real controls below — not screenshots.",
    ),
    "home.showcase.all": ("查看全部", "檢視全部", "See all"),
    "home.tile.buttons": ("按钮 Button", "按鈕 Button", "Buttons"),
    "home.tile.inputs": ("输入 Input", "輸入 Input", "Inputs"),
    "home.tile.choices": ("选择 Choice", "選擇 Choice", "Choices"),
    "home.tile.chips": ("标签 Chip", "標籤 Chip", "Chips"),
    "home.tile.progress": ("进度 Progress", "進度 Progress", "Progress"),
    "home.tile.pagination": ("分页 Pagination", "分頁 Pagination", "Pagination"),
    "home.tile.page": ("第 {n} 页", "第 {n} 頁", "{n}"),
    "home.code.eyebrow": ("代码示例", "程式碼範例", "Code"),
    "home.code.title": (
        "一屏写完一个页面",
        "一屏寫完一個頁面",
        "A whole page, one screen",
    ),
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
    "home.play.notify": ("弹一条通知", "彈一則通知", "Show a notification"),
    "home.play.notify_text": (
        "一切正常，组件工作正常。",
        "一切正常，元件運作正常。",
        "All good — components work.",
    ),
    # ---------------------------------------------------------------- 快速开始
    "start.intro": (
        "五分钟后，你会有一个能跑、能切主题、能切语言的桌面窗口。",
        "五分鐘後，你會有一個能跑、能切主題、能切語言的桌面視窗。",
        "Five minutes from now you'll have a window that runs, re-themes and re-languages itself.",
    ),
    "start.install.title": ("安装", "安裝", "Install"),
    "start.install.desc": (
        "任选一种方式。升级时让 cs-ui 与 Flet 保持同步。",
        "任選一種方式。升級時讓 cs-ui 與 Flet 保持同步。",
        "Pick one. Keep cs-ui and Flet in step when upgrading.",
    ),
    "start.install.note_title": ("环境要求", "環境需求", "Requirements"),
    "start.install.note": (
        "Python 3.12+、Flet {flet}。Windows / macOS / Linux 桌面都可以运行。",
        "Python 3.12+、Flet {flet}。Windows / macOS / Linux 桌面都可以執行。",
        "Python 3.12+, Flet {flet}. Runs on Windows, macOS and Linux desktops.",
    ),
    "start.first.title": ("第一个界面", "第一個介面", "First window"),
    "start.first.desc": (
        "新建 main.py，渲染一个带主题的计数器。",
        "新增 main.py，算繪一個帶主題的計數器。",
        "Create main.py and render a themed counter.",
    ),
    "start.first.tip_title": (
        "为什么是 page.render",
        "為什麼是 page.render",
        "Why page.render",
    ),
    "start.first.tip": (
        "根视图渲染让 page.overlay 与对话框正常工作；用 render_views 会把它们盖住。",
        "根視圖算繪讓 page.overlay 與對話框正常運作；用 render_views 會把它們蓋住。",
        "Root-view rendering keeps page.overlay and dialogs working; render_views covers them.",
    ),
    "start.run.title": ("运行", "執行", "Run"),
    "start.run.desc": (
        "保存即热重载；同一份代码也能直接在浏览器里跑。",
        "儲存即熱重載；同一份程式碼也能直接在瀏覽器裡跑。",
        "Hot reload on save — and the same file runs in a browser.",
    ),
    "start.layout.title": ("目录结构", "目錄結構", "Project layout"),
    "start.layout.desc": (
        "页面、组合控件与文案分开摆，项目变大也不乱。",
        "頁面、組合元件與文案分開擺，專案變大也不亂。",
        "Pages, composite widgets and copy in separate folders — it scales.",
    ),
    "start.next.title": ("下一步", "下一步", "Next"),
    "start.next.desc": (
        "建议按这个顺序继续读：",
        "建議依這個順序繼續讀：",
        "Read these in order:",
    ),
    "start.next.point1": (
        "读架构，理解两类组件与 Provider 顺序。",
        "讀架構，理解兩類元件與 Provider 順序。",
        "Architecture: the two component kinds and provider order.",
    ),
    "start.next.point2": (
        "看主题，用一个种子换掉整套配色。",
        "看主題，用一個種子換掉整套配色。",
        "Theming: swap the whole palette with one seed.",
    ),
    "start.next.point3": (
        "看多语言，把文案从代码里搬出去。",
        "看多語言，把文案從程式碼裡搬出去。",
        "i18n: move copy out of your code.",
    ),
    "start.next.point4": (
        "看响应式，理解同一份界面怎么适配三档窗口。",
        "看響應式，理解同一份介面怎麼適配三檔視窗。",
        "Responsive: how one layout adapts to three window classes.",
    ),
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
    "arch.layers.desc": (
        "四层，各管一件事：",
        "四層，各管一件事：",
        "Four layers, one job each:",
    ),
    "arch.layers.point1": (
        "控件层 —— 继承 Flet 原生控件，只改默认值与样式。",
        "控制項層 —— 繼承 Flet 原生控制項，只改預設值與樣式。",
        "Controls — subclass Flet controls, change defaults only.",
    ),
    "arch.layers.point2": (
        "状态层 —— use_state / use_ref / use_memo 与 observable 数据对象。",
        "狀態層 —— use_state / use_ref / use_memo 與 observable 資料物件。",
        "State — use_state / use_ref / use_memo plus observable objects.",
    ),
    "arch.layers.point3": (
        "基础设施 —— 主题、语言、路由、格式化与设计令牌。",
        "基礎設施 —— 主題、語言、路由、格式化與設計權杖。",
        "Infrastructure — theme, i18n, routing, formatting, tokens.",
    ),
    "arch.layers.point4": (
        "应用层 —— 页面只负责组合，不关心底层细节。",
        "應用層 —— 頁面只負責組合，不關心底層細節。",
        "Application — pages only compose; they never touch the plumbing.",
    ),
    "arch.kinds.title": ("两类组件", "兩類元件", "Two kinds of components"),
    "arch.kinds.desc": (
        "静态的继承控件；有状态的用数据对象加 ui() 方法。",
        "靜態的繼承控制項；有狀態的用資料物件加 ui() 方法。",
        "Static ones subclass a control; stateful ones pair a data object with ui().",
    ),
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
    "arch.providers.desc": (
        "语言在最外，主题其次，路由最内 —— 顺序决定首帧的颜色与文案。",
        "語言在最外，主題其次，路由最內 —— 順序決定首幀的顏色與文案。",
        "Language outermost, theme next, router innermost — order decides the first frame.",
    ),
    "arch.providers.tip_title": (
        "build 必须是函数",
        "build 必須是函式",
        "build must be a function",
    ),
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
    "arch.routing.desc": (
        "根视图渲染加 manage_views=False，浮层与悬挂面板才正常。",
        "根視圖算繪加 manage_views=False，浮層與懸掛面板才正常。",
        "Root-view rendering plus manage_views=False keeps overlays and flyouts alive.",
    ),
    "arch.routing.danger_title": (
        "不要用 render_views",
        "不要用 render_views",
        "Don't use render_views",
    ),
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
    "arch.state.desc": (
        "局部状态用 hooks；跨页面状态用模块级 observable 单例。",
        "區域狀態用 hooks；跨頁面狀態用模組級 observable 單例。",
        "Local state via hooks; cross-page state via a module-level observable singleton.",
    ),
    "arch.state.hooks": (
        "三个 hook 的分工",
        "三個 hook 的分工",
        "Three hooks, three jobs",
    ),
    "arch.state.point1": (
        "use_state：组件内部状态，改了就重绘。",
        "use_state：元件內部狀態，改了就重繪。",
        "use_state — component-local state; change it and the component re-renders.",
    ),
    "arch.state.point2": (
        "use_ref：固定跨渲染实例，表单控件放这里。",
        "use_ref：固定跨算繪實例，表單元件放這裡。",
        "use_ref — pin an instance across renders; form controls live here.",
    ),
    "arch.state.point3": (
        "use_memo：按依赖缓存昂贵计算。",
        "use_memo：依相依性快取昂貴計算。",
        "use_memo — cache expensive work against dependencies.",
    ),
    "arch.perf.title": ("性能取向", "效能取向", "Performance"),
    "arch.perf.desc": (
        "重绘按订阅粒度发生，切主题或语言不会重建控件树。",
        "重繪依訂閱粒度發生，切主題或語言不會重建控制項樹。",
        "Re-renders follow subscriptions; switching theme or language never rebuilds the tree.",
    ),
    "arch.perf.point1": (
        "只有读了 use_t() / use_theme() 的组件会重绘。",
        "只有讀了 use_t() / use_theme() 的元件會重繪。",
        "Only components that read use_t() / use_theme() re-render.",
    ),
    "arch.perf.point2": (
        "路由切换保留外壳，顶栏与侧边栏不重建。",
        "路由切換保留外殼，頂欄與側邊欄不重建。",
        "Route changes keep the shell: top bar and sidebar stay mounted.",
    ),
    "arch.perf.point3": (
        "表单实例复用，输入过程中不反复创建对象。",
        "表單實例重用，輸入過程中不反覆建立物件。",
        "Form instances are reused, so typing never recreates objects.",
    ),
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
    "theme.live.desc": (
        "这块面板用的是同一套令牌，切换后立刻变色。",
        "這塊面板用的是同一套權杖，切換後立刻變色。",
        "This panel uses the same tokens — it recolors the moment you switch.",
    ),
    "theme.live.point1": (
        "模式：跟随系统 / 浅色 / 深色。",
        "模式：跟隨系統 / 淺色 / 深色。",
        "Mode: system, light or dark.",
    ),
    "theme.live.point2": (
        "主色：一个品牌色算出整套 M3 色板（46 个角色）。",
        "主色：一個品牌色算出整套 M3 色盤（46 個角色）。",
        "Seed: one brand color becomes the whole M3 palette (46 roles).",
    ),
    "theme.live.primary": ("主色种子", "主色種子", "Seed color"),
    "theme.live.input": ("主题输入框", "主題輸入框", "Themed input"),
    "theme.live.value": ("随便输点什么", "隨便輸入點什麼", "Type something"),
    "theme.live.action": ("主要操作", "主要操作", "Primary"),
    "theme.live.secondary": ("次要操作", "次要操作", "Secondary"),
    "theme.tokens.title": ("设计令牌", "設計權杖", "Design tokens"),
    "theme.tokens.desc": (
        "间距、圆角、字号与阴影统一从 ui 导入，页面里不写魔法数字。",
        "間距、圓角、字級與陰影統一從 ui 匯入，頁面裡不寫魔法數字。",
        "Spacing, radius, type scale and elevation come from ui — no magic numbers in pages.",
    ),
    "theme.tokens.scale": ("刻度", "刻度", "Scales"),
    "theme.tokens.scale_desc": (
        "刻度只有有限几档：挑最接近的一档，不要现编数字。",
        "刻度只有有限幾檔：挑最接近的一檔，不要現編數字。",
        "The scales are finite: pick the nearest step instead of inventing numbers.",
    ),
    "theme.token.space": ("间距 SPACE", "間距 SPACE", "Spacing"),
    "theme.token.radius": ("圆角 RADIUS", "圓角 RADIUS", "Radius"),
    "theme.semantic.title": ("语义色", "語意色", "Semantic colors"),
    "theme.semantic.desc": (
        "success / warning / danger / info / neutral 与主题解耦：",
        "success / warning / danger / info / neutral 與主題解耦：",
        "success / warning / danger / info / neutral are decoupled from the theme:",
    ),
    "theme.semantic.desc2": (
        "深浅模式下都保证 4.5:1 以上对比度，所以状态永远读得出来。",
        "深淺模式下都保證 4.5:1 以上對比度，所以狀態永遠讀得出來。",
        "They keep ≥4.5:1 contrast in both modes, so status is always readable.",
    ),
    "theme.role.success": ("成功", "成功", "Success"),
    "theme.role.warning": ("警告", "警告", "Warning"),
    "theme.role.danger": ("危险", "危險", "Danger"),
    "theme.role.info": ("信息", "資訊", "Info"),
    "theme.role.neutral": ("中性", "中性", "Neutral"),
    "theme.modes.title": ("明暗模式", "明暗模式", "Light and dark"),
    "theme.modes.desc": (
        "ThemeProvider 会同时写下明暗两套主题（page.theme 与 page.dark_theme）—— 切模式只是换一棵现成的树，颜色不在运行时重算。",
        "ThemeProvider 會同時寫下明暗兩套主題（page.theme 與 page.dark_theme）—— 切模式只是換一棵現成的樹，顏色不在執行時重算。",
        "ThemeProvider writes both themes (page.theme and page.dark_theme) — switching mode swaps a ready-made tree instead of recomputing colors at runtime.",
    ),
    "theme.surfaces.title": ("表面与层次", "表面與層次", "Surfaces"),
    "theme.surfaces.desc": (
        "表面是一组设计好的中性色阶：浅色近白、深色深石板，灰里掺了一丝主色相（不是三通道相等的死灰）。卡片之间靠 1px 描边与半透明覆盖分层，不靠硬拉色阶对比。",
        "表面是一組設計好的中性色階：淺色近白、深色深石板，灰裡摻了一絲主色相（不是三通道相等的死灰）。卡片之間靠 1px 描邊與半透明覆蓋分層，不靠硬拉色階對比。",
        "Surfaces are a designed neutral ramp: near-white in light mode, deep slate in dark, with a trace of the brand hue in the grey (never a dead neutral). Cards are separated by 1px outlines and translucent overlays rather than by brute-forcing container tones.",
    ),
    "theme.surfaces.tonal": (
        "想要更明显的着色表面，把 surfaces 设成 tonal：同一组色阶会带上更多品牌色相，组件一处都不用改。",
        "想要更明顯的著色表面，把 surfaces 設成 tonal：同一組色階會帶上更多品牌色相，元件一處都不用改。",
        "Want visibly tinted surfaces? Set surfaces to tonal: the same ramp takes on more of the brand hue and no component changes.",
    ),
    "theme.palette.title": ("品牌色 → 整套色板", "品牌色 → 整套色板", "One seed → a whole scheme"),
    "theme.palette.desc": (
        "把种子交给 color_scheme_seed，Flutter 会用 tonalSpot 推导整套色板 —— 而它会把 #1F6FEB 推成 #465D91，品牌蓝被抽掉一半彩度。所以 46 个角色由 palette 一次算清，明暗各一套。",
        "把種子交給 color_scheme_seed，Flutter 會用 tonalSpot 推導整套色板 —— 而它會把 #1F6FEB 推成 #465D91，品牌藍被抽掉一半彩度。所以 46 個角色由 palette 一次算清，明暗各一套。",
        "Hand the seed to color_scheme_seed and Flutter derives the palette with tonalSpot — which turns #1F6FEB into #465D91, stripping half the brand chroma. So palette computes all 46 roles up front, one set per mode.",
    ),
    "theme.palette.desc2": (
        "换任何种子都得到同构的一套：十一档色阶的明度步长恒定在 0.075 左右，色相漂移小于 4°，明暗两套的容器次序互为镜像。",
        "換任何種子都得到同構的一套：十一檔色階的明度步長恆定在 0.075 左右，色相漂移小於 4°，明暗兩套的容器次序互為鏡像。",
        "Any seed yields an isomorphic scheme: the eleven tone steps keep a constant ~0.075 lightness interval, hue drifts less than 4°, and the container ladder mirrors itself between modes.",
    ),
    "theme.palette.point1": (
        "色相不动，只解明度：品牌色可以被压暗到扛得住白字，但不该被改色相。",
        "色相不動，只解明度：品牌色可以被壓暗到扛得住白字，但不該被改色相。",
        "Hue never moves, only lightness: a brand color may be darkened to carry white text, but its hue must not change.",
    ),
    "theme.palette.point2": (
        "明度按对比度解算：主色对底色解到 5:1，深色模式的实底解到 7:1 —— 同样的 tone 40，黄色与蓝色的对比度能差三倍。",
        "明度按對比度解算：主色對底色解到 5:1，深色模式的實底解到 7:1 —— 同樣的 tone 40，黃色與藍色的對比度能差三倍。",
        "Lightness is solved for contrast: 5:1 for accents on the surface, 7:1 for solid fills in dark mode — at equal tone, yellow and blue differ threefold in contrast.",
    ),
    "theme.palette.point3": (
        "中性色掺一丝品牌色相（彩度 0.006）：Slate 之所以显高级，正因为它不是三通道相等的死灰。",
        "中性色摻一絲品牌色相（彩度 0.006）：Slate 之所以顯高級，正因為它不是三通道相等的死灰。",
        "Neutrals carry a trace of the brand hue (chroma 0.006): Slate looks premium precisely because it is not a dead grey.",
    ),
    # ------------------------------------------------------------ 响应式
    "resp.intro": (
        "响应式不是「给每个组件加一个窄屏样式」，而是先定一条规矩：谁负责判断宽度。"
        "本框架的规矩是 —— 结构性变化走 Python，连续性变化走渲染层。栅格换列、"
        "元素拉伸每帧都在变，那是 Flutter 的活；「窄屏要不要收起侧栏」一秒钟最多变一次，"
        "那才轮到 Python。混着来就会两边都做不好：Python 每帧重算会卡，Flutter 不知道"
        "你的业务结构。",
        "響應式不是「給每個元件加一個窄屏樣式」，而是先定一條規矩：誰負責判斷寬度。"
        "本框架的規矩是 —— 結構性變化走 Python，連續性變化走渲染層。柵格換列、"
        "元素拉伸每幀都在變，那是 Flutter 的活；「窄屏要不要收起側欄」一秒鐘最多變一次，"
        "那才輪到 Python。混著來就會兩邊都做不好：Python 每幀重算會卡，Flutter 不知道"
        "你的業務結構。",
        "Responsive design is not “add a narrow variant to every component” — it starts with "
        "one rule: who is allowed to judge width. Here the rule is structural changes in "
        "Python, continuous changes in the renderer. Reflowing a grid and stretching an element "
        "happen every frame — that is Flutter's job. “Should the sidebar collapse?” changes at "
        "most once a second — that is Python's job. Mixing them fails both ways: recomputing every "
        "frame stutters, and Flutter cannot see your business structure.",
    ),
    "resp.rules.title": ("四条规矩", "四條規矩", "Four rules"),
    "resp.rules.desc": (
        "断点、档位、通知时机、改哪儿 —— 四件事定死了，组件才有统一的行为：",
        "斷點、檔位、通知時機、改哪裡 —— 四件事定死了，元件才有統一的行為：",
        "Breakpoints, window classes, notification timing and what you may touch — once these "
        "four are fixed, components behave consistently:",
    ),
    "resp.rules.point1": (
        "断点与 flet 的 ResponsiveRow 逐项相同（0 / 576 / 768 / 992 / 1200 / 1400）。"
        "另采一套边界，就会出现「栅格已经换列、页面还以为自己是窄屏」的错位。",
        "斷點與 flet 的 ResponsiveRow 逐項相同（0 / 576 / 768 / 992 / 1200 / 1400）。"
        "另採一套邊界，就會出現「柵格已經換列、頁面還以為自己是窄屏」的錯位。",
        "Breakpoints are identical to flet's ResponsiveRow (0 / 576 / 768 / 992 / 1200 / 1400). "
        "A second set of boundaries produces the classic mismatch: the grid already reflowed, the "
        "page still thinks it is narrow.",
    ),
    "resp.rules.point2": (
        "六个断点归成三档窗口类：compact（< 768）、medium（768–1199）、expanded（≥ 1200）。"
        "布局策略只需要这三档 —— 再细分就是把同一件事切碎。",
        "六個斷點歸成三檔視窗類：compact（< 768）、medium（768–1199）、expanded（≥ 1200）。"
        "佈局策略只需要這三檔 —— 再細分就是把同一件事切碎。",
        "Six breakpoints collapse into three window classes: compact (< 768), medium (768–1199), "
        "expanded (≥ 1200). Layout strategy needs exactly these three — finer splits chop one "
        "decision into fragments.",
    ),
    "resp.rules.point3": (
        "状态里只有窗口类会触发重绘，且值没变就不写。拖动窗口时宽度每像素都在变，"
        "若每次都通知，界面会变成幻灯片。",
        "狀態裡只有視窗類會觸發重繪，且值沒變就不寫。拖動視窗時寬度每像素都在變，"
        "若每次都通知，介面會變成幻燈片。",
        "Only the window class triggers a repaint, and only when it actually changes. Width changes "
        "on every pixel while dragging; notifying each time turns the UI into a slideshow.",
    ),
    "resp.rules.point4": (
        "运行期只改属性，不改子树。flet 1.1.2 对已挂载控件树的结构补丁不保证上屏："
        "把 content 换成新控件、整列换新列表、甚至切 visible，都可能「Python 里全对、"
        "屏幕纹丝不动」；而组件渲染出的控件树会被冻结，运行期连子控件的属性都改不动。"
        "所以结构只在构建期定，要跟随档位就让 observable 触发整页重渲染（组件）。",
        "執行期只改屬性，不改子樹。flet 1.1.2 對已掛載元件樹的結構補丁不保證上屏："
        "把 content 換成新元件、整列換新列表、甚至切 visible，都可能「Python 裡全對、"
        "螢幕紋絲不動」；而元件渲染出的控件樹會被凍結，執行期連子控件的屬性都改不動。"
        "所以結構只在建構期定，要跟隨檔位就讓 observable 觸發整頁重繪（元件）。",
        "At runtime, change properties only — never the tree. flet 1.1.2 does not guarantee "
        "that structural patches to an already-mounted tree reach the screen: replacing content, "
        "swapping a whole list, even toggling visible can leave Python correct and the screen "
        "unchanged — and the tree a component renders is frozen, so not even a child's properties "
        "can be touched. Decide structure at build time; to follow the window class, let an "
        "observable re-render the page (a component).",
    ),
    "resp.live.title": ("拖一下试试", "拖一下試試", "Drag it"),
    "resp.live.desc": (
        "下面这块栅格换列时，Python 一行都没跑 —— 列数早在构建时就写进了每个断点，"
        "换列完全发生在渲染层。这正是「连续性变化交给 Flutter」的意思。",
        "下面這塊柵格換列時，Python 一行都沒跑 —— 列數早在建構時就寫進了每個斷點，"
        "換列完全發生在渲染層。這正是「連續性變化交給 Flutter」的意思。",
        "When the grid below reflows, Python does not run at all — the column count for every "
        "breakpoint was written in at build time, and reflow happens entirely in the renderer. "
        "That is what “leave continuous changes to Flutter” means.",
    ),
    "resp.grid.title": ("栅格：只说最小格宽", "柵格：只說最小格寬", "Grid: name a minimum, not a count"),
    "resp.grid.desc": (
        "ResponsiveRow 要求每个子项手写一份断点字典；Grid 只要一个最小格宽 —— "
        "「一格至少多宽」是设计上的事实，「第几档放几列」是它的计算结果，不该让人手动重复。",
        "ResponsiveRow 要求每個子項手寫一份斷點字典；Grid 只要一個最小格寬 —— "
        "「一格至少多寬」是設計上的事實，「第幾檔放幾列」是它的計算結果，不該讓人手動重複。",
        "ResponsiveRow asks every child to carry its own breakpoint dictionary; Grid asks for one "
        "minimum cell width. “How narrow may a cell get” is a design fact; “how many columns per "
        "breakpoint” is the computed consequence and should not be retyped by hand.",
    ),
    "resp.grid.tip": (
        "列数按「虚拟列数 = 每行格数」下发，子项各占一列 —— 于是等宽来自结构，"
        "而不是靠 12 能被 3 整除这种巧合。12 栅格里放 5 格会剩下 2 列分不掉。",
        "列數按「虛擬列數 = 每行格數」下發，子項各佔一列 —— 於是等寬來自結構，"
        "而不是靠 12 能被 3 整除這種巧合。12 柵格裡放 5 格會剩下 2 列分不掉。",
        "Column counts are sent as “virtual columns = cells per row” with each child spanning one, "
        "so equal widths come from structure rather than from 12 being divisible by 3. Five cells "
        "in a 12-column grid leave two columns that cannot be split.",
    ),
    "resp.grid.tip_title": ("为什么不是 12 栅格", "為什麼不是 12 柵格", "Why not a 12-column grid"),
    "resp.hook.title": ("需要知道档位时", "需要知道檔位時", "When you need the class"),
    "resp.hook.desc": (
        "有结构性差别（侧栏有没有、表格还是卡片）才用 hook。它跨档时重绘本组件，"
        "所以别在它里面算像素 —— 那是渲染层的事。",
        "有結構性差別（側欄有沒有、表格還是卡片）才用 hook。它跨檔時重繪本元件，"
        "所以別在它裡面算像素 —— 那是渲染層的事。",
        "Reach for the hook only when the difference is structural (sidebar or not, table or "
        "cards). It repaints the component when the class changes, so do not do pixel math inside "
        "it — that belongs to the renderer.",
    ),
    "resp.hook.warn": (
        "use_responsive() 反映的是窗口宽度。组件可能只占窗口的一部分（侧栏、分栏、对话框），"
        "那里应该量自己 —— PageLayout、Descriptions 走的是 on_size_change，不看窗口。",
        "use_responsive() 反映的是視窗寬度。元件可能只佔視窗的一部分（側欄、分欄、對話框），"
        "那裡應該量自己 —— PageLayout、Descriptions 走的是 on_size_change，不看視窗。",
        "use_responsive() reflects the window width. A component may occupy only part of it "
        "(sidebar, split pane, dialog) — there it should measure itself. PageLayout and "
        "Descriptions use on_size_change and ignore the window.",
    ),
    "resp.hook.warn_title": ("窗口宽度 ≠ 你的宽度", "視窗寬度 ≠ 你的寬度", "Window width ≠ your width"),
    "resp.own.title": ("宽屏要限宽", "寬屏要限寬", "Cap the width on wide screens"),
    "resp.own.desc": (
        "响应式的另一半常被忽略：窄屏要挤得下，宽屏不能拉太长。一行超过约 75 个字符，"
        "眼睛回行距离变长，阅读反而变慢；表单拉满 2000px 会显得左一个标签右一个输入框、"
        "中间空一大片。所以宽屏的正解是居中限宽。",
        "響應式的另一半常被忽略：窄屏要擠得下，寬屏不能拉太長。一行超過約 75 個字元，"
        "眼睛回行距離變長，閱讀反而變慢；表單拉滿 2000px 會顯得左一個標籤右一個輸入框、"
        "中間空一大片。所以寬屏的正解是居中限寬。",
        "The other half of responsive design is usually forgotten: narrow screens must fit, and "
        "wide screens must not stretch. Past roughly 75 characters per line the eye has to "
        "travel further and reading slows down; a form stretched to 2000px looks like a label on "
        "the far left and its input on the far right with a desert in between. Centre it and cap it.",
    ),
    "resp.own.note": (
        "PageLayout 的 max_content_width 在窄容器上自动失效 —— 小屏幕上再限宽等于把内容挤没。"
        "同一份代码，宽屏居中、窄屏铺满，不用写两个版本。",
        "PageLayout 的 max_content_width 在窄容器上自動失效 —— 小螢幕上再限寬等於把內容擠沒。"
        "同一份程式碼，寬屏居中、窄屏鋪滿，不用寫兩個版本。",
        "PageLayout's max_content_width switches itself off on narrow containers — capping width there "
        "would squeeze the content away. One piece of code: centred when wide, full-bleed when "
        "narrow, no second variant.",
    ),
    "resp.own.note_title": ("限宽会自动让位", "限寬會自動讓位", "The cap steps aside"),
    "resp.boot.title": ("启动就是窄屏", "啟動就是窄屏", "Booted narrow"),
    "resp.boot.desc": (
        "窗口的启动尺寸不会触发 on_resize，而 main() 里读到的 page.width 还是上一次的尺寸。"
        "apply_responsive 会在首帧后补读几次，所以只要调用过它，首帧之后的档位就是准的；"
        "没调用的话，use_responsive() 会一直停在 expanded —— 侧栏常驻、页头不折行。",
        "視窗的啟動尺寸不會觸發 on_resize，而 main() 裡讀到的 page.width 還是上一次的尺寸。"
        "apply_responsive 會在首幀之後補讀幾次，所以只要呼叫過它，首幀之後的檔位就是準的；"
        "沒呼叫的話，use_responsive() 會一直停在 expanded —— 側欄常駐、頁首不折行。",
        "A window's startup size does not fire on_resize, and page.width in main() still holds the "
        "previous size. apply_responsive re-reads it a few times after the first frame, so once it "
        "has been called the class is right from then on; without it, use_responsive() stays at "
        "expanded — permanent sidebar, no wrapped header.",
    ),
    "theme.trap_title": (
        "不要在页面里直接改 page.theme",
        "不要在頁面裡直接改 page.theme",
        "Never set page.theme in a page",
    ),
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
    "i18n.live.desc": (
        "换一种语言，格式化的输出也跟着变。",
        "換一種語言，格式化的輸出也跟著變。",
        "Change the language and the formatted output changes with it.",
    ),
    "i18n.live.point1": (
        "三份语言包在启动时一次载入。",
        "三份語言包在啟動時一次載入。",
        "All three catalogs load once at startup.",
    ),
    "i18n.live.point2": (
        "输入框里的内容不会因为切语言而丢失。",
        "輸入框裡的內容不會因為切語言而遺失。",
        "What you typed survives the switch.",
    ),
    "i18n.live.input": ("姓名", "姓名", "Name"),
    "i18n.live.value": ("肖恩", "肖恩", "Shawn"),
    "i18n.live.date": ("长日期", "長日期", "Long date"),
    "i18n.live.number": ("数字", "數字", "Number"),
    "i18n.live.list": ("列表", "清單", "List"),
    "i18n.live.time": ("短日期", "短日期", "Short date"),
    "i18n.register.title": ("注册文案", "註冊文案", "Registering copy"),
    "i18n.register.desc": (
        "register_messages 接受嵌套字典，也接受平铺的点号键。",
        "register_messages 接受巢狀字典，也接受平鋪的點號鍵。",
        "register_messages takes nested dicts or flat dotted keys.",
    ),
    "i18n.register.tip_title": ("回退链", "回退鏈", "Fallback chain"),
    "i18n.register.tip": (
        "繁体缺的键回退简体，再回退英文 —— 永远不会出现空白或键名。",
        "繁體缺的鍵回退簡體，再回退英文 —— 永遠不會出現空白或鍵名。",
        "Missing Traditional keys fall back to Simplified, then English — never a blank or a raw key.",
    ),
    "i18n.use.title": ("在组件里取词", "在元件裡取詞", "Reading strings"),
    "i18n.use.desc": (
        "组件开头调用一次 use_t()，之后用 tr(key) 取文案；它同时完成了订阅。",
        "元件開頭呼叫一次 use_t()，之後用 tr(key) 取文案；它同時完成了訂閱。",
        "Call use_t() once at the top, then tr(key): that call is also the subscription.",
    ),
    "i18n.format.title": ("格式化", "格式化", "Formatting"),
    "i18n.format.desc": (
        "日期、数字与日历标题都从同一层取，语言变了输出就变。",
        "日期、數字與月曆標題都從同一層取，語言變了輸出就變。",
        "Dates, numbers and calendar titles come from one layer; the language drives them.",
    ),
    "i18n.format.note_title": (
        "格式化也是 i18n",
        "格式化也是 i18n",
        "Formatting is i18n",
    ),
    "i18n.format.note": (
        "“翻译了但格式还是中文的”比“没翻译”更常见：英文界面里冒出 2026 年 9 月，就是这一类。",
        "「翻譯了但格式還是中文的」比「沒翻譯」更常見：英文介面裡冒出 2026 年 9 月，就是這一類。",
        (
            "“Translated, but formatted Chinese” is more common than “untranslated”: 2026 年 9 月 in an "
            "English UI is exactly that bug."
        ),
    ),
    "i18n.fallback.title": ("回退", "回退", "Fallback"),
    "i18n.fallback.desc": (
        "语言包可以只翻一部分，其余按链回退。",
        "語言包可以只翻一部分，其餘依鏈回退。",
        "A catalog can be partly translated; the rest falls back.",
    ),
    "i18n.fallback.point1": (
        "zh_TW → zh_CN → en_US。",
        "zh_TW → zh_CN → en_US。",
        "zh_TW → zh_CN → en_US.",
    ),
    "i18n.fallback.point2": (
        "缺键不抛异常，只在日志里警告一次。",
        "缺鍵不拋例外，只在日誌裡警告一次。",
        "Missing keys never raise — one warning in the log.",
    ),
    "i18n.fallback.point3": (
        "strict=True 时缺键直接抛错，适合放进 CI。",
        "strict=True 時缺鍵直接拋錯，適合放進 CI。",
        "strict=True raises instead — put it in CI.",
    ),
    # ---------------------------------------------------------------- 组件总览
    "comp.intro": (
        "每个分类都是一个页面，页面里全是能点的真控件 —— 不是截图，也不是静态示例。",
        "每個分類都是一個頁面，頁面裡全是能點的真元件 —— 不是截圖，也不是靜態範例。",
        "Each category is a page full of real, clickable controls — not screenshots, not static samples.",
    ),
    "comp.count": ("{n} 个组件", "{n} 個元件", "{n} components"),
    "comp.examples": ("{n} 个示例", "{n} 個範例", "{n} examples"),
    "comp.run": ("在独立窗口中打开", "在獨立視窗中開啟", "Open in its own window"),
    "site.overview": ("总览", "總覽", "Overview"),
    "comp.stats.components": ("组件", "元件", "components"),
    "comp.stats.categories": ("分类", "分類", "categories"),
    "comp.stats.languages": ("语言", "語言", "languages"),
    "comp.stats.typed": ("类型注解", "型別註解", "typed"),
    "comp.stats.python": ("Python", "Python", "Python"),
    "comp.search.title": ("找不到想要的？", "找不到想要的？", "Can't find it?"),
    "comp.search.desc": (
        "打开搜索，按名称或功能快速定位。",
        "開啟搜尋，依名稱或功能快速定位。",
        "Open search and jump by name or purpose.",
    ),
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
    "cat.general.type.hint": (
        "五级标题、正文、引用与链接，字号取自 M3 字阶。",
        "五級標題、內文、引用與連結，字級取自 M3 字階。",
        "Five heading levels, body, quote and link — sized by the M3 type scale.",
    ),
    "cat.general.typo.body": (
        "正文用 14px、1.75 倍行高；中文在长段落里更耐读。",
        "內文用 14px、1.75 倍行高；中文在長段落裡更耐讀。",
        "Body copy is 14px at 1.75 line height — easier on long paragraphs.",
    ),
    "cat.general.typo.quote": (
        "引用块保留呼吸感，不抢正文的注意力。",
        "引用區塊保留呼吸感，不搶內文的注意力。",
        "Quotes keep their breathing room without stealing attention.",
    ),
    "cat.general.typo.link": ("链接文本", "連結文字", "A link"),
    "cat.general.button.title": ("按钮 Button", "按鈕 Button", "Buttons"),
    "cat.general.button.hint": (
        "六种语义样式、三种形状，plain 变体适合次要操作。",
        "六種語意樣式、三種形狀，plain 變體適合次要操作。",
        "Six semantic styles, three shapes; the plain variant suits secondary actions.",
    ),
    "cat.general.chip.title": ("标签 Chip", "標籤 Chip", "Chips"),
    "cat.general.chip.hint": (
        "单选与多选两种模式，选项来自语言包也能来自接口。",
        "單選與多選兩種模式，選項來自語言包也能來自介面。",
        "Single and multi-select modes; options can come from a catalog or an API.",
    ),
    "cat.general.chip.single": ("单选标签", "單選標籤", "Pick one"),
    "cat.general.chip.multi": ("多选标签", "多選標籤", "Pick several"),
    "cat.general.icon.title": (
        "图标与徽章 Icon",
        "圖示與徽章 Icon",
        "Icons and badges",
    ),
    "cat.general.icon.hint": (
        "图标按钮、带角标的实心按钮、以及可换行的富文本提示。",
        "圖示按鈕、帶角標的實心按鈕，以及可換行的富文字提示。",
        "Icon buttons, filled buttons with badges, and a rich tooltip.",
    ),
    "cat.general.icon.love": ("收藏", "收藏", "Save"),
    "cat.general.icon.delete": ("删除", "刪除", "Delete"),
    "cat.general.icon.rich": (
        "悬停看富文本提示",
        "懸停看富文字提示",
        "Hover for a rich tooltip",
    ),
    "cat.general.icon.rich_tip": (
        "Tooltip 支持多行文本与自定义内边距。",
        "Tooltip 支援多行文字與自訂內距。",
        "Tooltips take multi-line text and custom padding.",
    ),
    "cat.general.md.title": (
        "Markdown 与 JSON",
        "Markdown 與 JSON",
        "Markdown and JSON",
    ),
    "cat.general.md.hint": (
        "仓库说明、变更日志这类内容可以直接渲染，不用拆成控件。",
        "儲存庫說明、變更日誌這類內容可以直接算繪，不用拆成元件。",
        "Render READMEs and changelogs directly instead of splitting them into controls.",
    ),
    "cat.general.note1": (
        "标题默认字号取自 M3 字阶，跨平台一致。",
        "標題預設字級取自 M3 字階，跨平台一致。",
        "Heading sizes come from the M3 scale, consistent across platforms.",
    ),
    "cat.general.note2": (
        "按钮高度固定 36px，横排不会参差。",
        "按鈕高度固定 36px，橫排不會參差。",
        "Buttons are 36px tall, so rows stay flush.",
    ),
    "cat.general.note3": (
        "Markdown 与 JSON 都是只读控件，适合展示文档与接口返回。",
        "Markdown 與 JSON 都是唯讀元件，適合展示文件與介面回傳。",
        "Markdown and JSON are read-only — good for docs and API payloads.",
    ),
    "cat.general.tip_title": ("组合优先", "組合優先", "Compose, don't configure"),
    "cat.general.tip": (
        "没有“超级按钮”。需要徽章就套 Badge，需要提示就套 Tooltip。",
        "沒有「超級按鈕」。需要徽章就套 Badge，需要提示就套 Tooltip。",
        "There is no mega-button. Need a badge? Wrap a Badge. A hint? Wrap a Tooltip.",
    ),
    "cat.layout.intro": (
        "布局组件决定“东西放在哪”。它们都只做一件事，组合起来才能搭出整个界面。",
        "佈局元件決定「東西放在哪」。它們都只做一件事，組合起來才能搭出整個介面。",
        (
            "Layout decides where things go. Each piece does one job; together they b"
            "uild the screen."
            ""
        ),
    ),
    "cat.layout.flex.title": (
        "容器与弹性布局",
        "容器與彈性版面",
        "Containers and flex",
    ),
    "cat.layout.flex.hint": (
        "Row / Column 控制方向，Stack 做叠放，Container 负责留白与描边。",
        "Row / Column 控制方向，Stack 做疊放，Container 負責留白與描邊。",
        "Row/Column set direction, Stack layers, Container handles padding and borders.",
    ),
    "cat.layout.flex.container": (
        "Container 里的内容",
        "Container 裡的內容",
        "Inside a Container",
    ),
    "cat.layout.list.title": ("列表与网格", "清單與格狀", "Lists and grids"),
    "cat.layout.list.hint": (
        "ListView 适合长列表，GridView 适合缩略图；两者都按需构建。",
        "ListView 適合長清單，GridView 適合縮圖；兩者都按需建構。",
        "ListView for long lists, GridView for thumbnails — both build lazily.",
    ),
    "cat.layout.list.item": ("第 {n} 行", "第 {n} 列", "Row {n}"),
    "cat.layout.expander.title": (
        "折叠面板 Expander",
        "摺疊面板 Expander",
        "Expanders",
    ),
    "cat.layout.expander.hint": (
        "三种外观：描边、填充、纯文本；折叠时只占一行高度。",
        "三種外觀：描邊、填滿、純文字；摺疊時只佔一列高度。",
        "Three looks: outlined, filled and plain. Collapsed, it's one row tall.",
    ),
    "cat.layout.expander.basic": ("基础用法", "基礎用法", "Basic"),
    "cat.layout.expander.basic_sub": (
        "默认描边样式，适合设置项分组",
        "預設描邊樣式，適合設定項分組",
        "Outlined by default — good for settings groups",
    ),
    "cat.layout.expander.filled": ("填充样式", "填滿樣式", "Filled"),
    "cat.layout.expander.filled_sub": (
        "带图标与强调色，适合放重要内容",
        "帶圖示與強調色，適合放重要內容",
        "Icon plus accent — for content that matters",
    ),
    "cat.layout.expander.plain": ("纯文本样式", "純文字樣式", "Plain"),
    "cat.layout.expander.body1": (
        "展开后的内容可以是任意控件，包括表格和图表。",
        "展開後的內容可以是任意元件，包括表格和圖表。",
        "Expanded content can be anything — tables, charts, forms.",
    ),
    "cat.layout.expander.body2": (
        "紧凑密度下，行高与内边距同步收窄。",
        "緊湊密度下，列高與內距同步收窄。",
        "Compact density tightens rows and padding together.",
    ),
    "cat.layout.step.title": ("步骤条 Step", "步驟條 Step", "Step"),
    "cat.layout.step.hint": (
        "active 决定进度：走过的段上色、当前步描边高亮；vertical 走左侧轴轨，simple 收成一行序号。",
        "active 決定進度：走過的段上色、當前步描邊高亮；vertical 走左側軸軌，simple 收成一行序號。",
        "active drives progress: walked segments are tinted, the current step is outlined; vertical uses a left rail, simple collapses to numbered chips.",
    ),
    "cat.layout.step.t1": ("填写信息", "填寫資訊", "Account details"),
    "cat.layout.step.d1": (
        "账号与联系方式",
        "帳號與聯絡方式",
        "Account and contact info",
    ),
    "cat.layout.step.t2": ("验证邮箱", "驗證信箱", "Verify email"),
    "cat.layout.step.d2": (
        "点击邮件里的链接",
        "點擊郵件裡的連結",
        "Click the link in the email",
    ),
    "cat.layout.step.t3": ("完善资料", "完善資料", "Complete profile"),
    "cat.layout.step.d3": (
        "头像、简介与偏好",
        "頭像、簡介與偏好",
        "Avatar, bio and preferences",
    ),
    "cat.layout.step.t4": ("开始使用", "開始使用", "Get started"),
    "cat.layout.step.d4": (
        "全部就绪，进入工作台",
        "全部就緒，進入工作台",
        "All set, enter the workspace",
    ),
    "cat.layout.step.v1": ("提交申请", "提交申請", "Submit request"),
    "cat.layout.step.vd1": (
        "材料已上传，等待受理",
        "材料已上傳，等待受理",
        "Files uploaded, awaiting intake",
    ),
    "cat.layout.step.v2": ("部门审批", "部門審批", "Department approval"),
    "cat.layout.step.vd2": (
        "发票校验未通过，需补充凭证",
        "發票校驗未通過，需補充憑證",
        "Invoice check failed, add receipt",
    ),
    "cat.layout.step.v3": ("财务复核", "財務複核", "Finance review"),
    "cat.layout.step.vd3": (
        "审批通过后自动进入复核",
        "審批通過後自動進入複核",
        "Runs automatically after approval",
    ),
    "cat.layout.step.s1": ("选择机型", "選擇機型", "Choose model"),
    "cat.layout.step.s2": ("配置参数", "配置參數", "Configure"),
    "cat.layout.step.s3": ("确认订单", "確認訂單", "Confirm order"),
    "cat.layout.step.s4": ("支付", "支付", "Payment"),
    "cat.layout.table.title": ("表格 Table", "表格 Table", "Table"),
    "cat.layout.table.hint": (
        "表头、斑马纹与分页器打包在一起；列宽自适应内容。",
        "表頭、斑馬紋與分頁器打包在一起；欄寬自適應內容。",
        "Header, zebra rows and paging in one control; columns size to content.",
    ),
    "cat.layout.page.title": (
        "页面骨架 PageLayout",
        "頁面骨架 PageLayout",
        "Page layout",
    ),
    "cat.layout.page.hint": (
        "标题、副标题、右侧操作区与内容区，一次给齐。",
        "標題、副標題、右側操作區與內容區，一次給齊。",
        "Title, subtitle, actions and content area in one shot.",
    ),
    "cat.layout.page.name": ("用户管理", "使用者管理", "Users"),
    "cat.layout.page.subtitle": (
        "共 1,286 位，本周新增 42 位",
        "共 1,286 位，本週新增 42 位",
        "1,286 total, 42 new this week",
    ),
    "cat.layout.page.export": ("导出", "匯出", "Export"),
    "cat.layout.page.create": ("新建用户", "新增使用者", "New user"),
    "cat.layout.page.total": ("总用户", "總使用者", "Total"),
    "cat.layout.page.active": ("活跃", "活躍", "Active"),
    "cat.layout.page.pending": ("待审核", "待審核", "Pending"),
    "cat.layout.page.content": (
        "内容区可以放任意控件：表格、图表、表单。",
        "內容區可以放任意元件：表格、圖表、表單。",
        "The content area takes anything: tables, charts, forms.",
    ),
    "cat.layout.note1": (
        "列表默认按需构建，几千行也不卡。",
        "清單預設按需建構，幾千列也不卡。",
        "Lists build lazily — thousands of rows stay smooth.",
    ),
    "cat.layout.note2": (
        "表格分页由 PaginationState 驱动，切每页条数会回到第一页。",
        "表格分頁由 PaginationState 驅動，切每頁筆數會回到第一頁。",
        "Table paging is driven by PaginationState; changing page size resets to page one.",
    ),
    "cat.layout.note3": (
        "步骤条的整步可点，点击水波纹由 Material ink 绘制，不触发 Python 重绘。",
        "步驟條的整步可點，點擊水波紋由 Material ink 繪製，不觸發 Python 重繪。",
        "Step cells are clickable; the ripple is painted by Material ink, not Python.",
    ),
    "cat.layout.tip_title": ("先想骨架", "先想骨架", "Start with the skeleton"),
    "cat.layout.tip": (
        "先用 PageLayout 定好标题与操作区，再往里塞列表或表格，比反过来快。",
        "先用 PageLayout 定好標題與操作區，再往裡塞清單或表格，比反過來快。",
        "Lay out PageLayout first, then fill it with a list or table — faster than the reverse.",
    ),
    "cat.navigation.intro": (
        "导航回答两个问题：我在哪，能去哪。面包屑答第一个，标签页与分页答第二个。",
        "導覽回答兩個問題：我在哪，能去哪。麵包屑答第一個，頁籤與分頁答第二個。",
        (
            "Navigation answers two questions: where am I, where can I go. Breadcrumb"
            "s answer the first, tabs and pagination the second."
            ""
        ),
    ),
    "cat.navigation.crumb.title": (
        "面包屑 BreadCrumb",
        "麵包屑 BreadCrumb",
        "Breadcrumbs",
    ),
    "cat.navigation.crumb.hint": (
        "支持字符串、元组与 Crumb 三种写法，最后一项自动当当前页。",
        "支援字串、元組與 Crumb 三種寫法，最後一項自動當目前頁。",
        "Accepts strings, tuples or Crumb objects; the last item is the current page.",
    ),
    "cat.navigation.crumb.home": ("首页", "首頁", "Home"),
    "cat.navigation.crumb.components": ("组件", "元件", "Components"),
    "cat.navigation.crumb.current": ("反馈", "回饋", "Feedback"),
    "cat.navigation.crumb.a": ("工作区", "工作區", "Workspace"),
    "cat.navigation.crumb.b": ("当前页", "目前頁", "Current"),
    "cat.navigation.tabs.title": ("标签页 Tabs", "頁籤 Tabs", "Tabs"),
    "cat.navigation.tabs.hint": (
        "TabBar 与 TabBarView 分开挂，标签可以带图标。",
        "TabBar 與 TabBarView 分開掛，標籤可以帶圖示。",
        "TabBar and TabBarView mount separately; tabs can carry icons.",
    ),
    "cat.navigation.tabs.overview": ("概览", "概覽", "Overview"),
    "cat.navigation.tabs.detail": ("明细", "明細", "Detail"),
    "cat.navigation.tabs.settings": ("设置", "設定", "Settings"),
    "cat.navigation.tabs.overview_body": (
        "概览页通常放关键指标与趋势图。",
        "概覽頁通常放關鍵指標與趨勢圖。",
        "Overview pages usually hold key metrics and trends.",
    ),
    "cat.navigation.tabs.detail_body": (
        "明细页放可分页的表格，列多时横向滚动。",
        "明細頁放可分頁的表格，欄多時橫向捲動。",
        "Detail pages hold a paged table that scrolls sideways when wide.",
    ),
    "cat.navigation.tabs.settings_body": (
        "设置页多用折叠面板分组，避免一屏塞满。",
        "設定頁多用摺疊面板分組，避免一屏塞滿。",
        "Settings pages group with expanders instead of one long scroll.",
    ),
    "cat.navigation.menu.title": ("菜单 Menu", "選單 Menu", "Menu"),
    "cat.navigation.menu.hint": (
        (
            "多级侧边导航：分组标题、圆点、徽标、手风琴，折叠后只剩图标条。"
            "选中项淡主色底 + 主色字，父级只转主色不铺底，明暗与主色全自动。"
        ),
        (
            "多層側邊導覽：分組標題、圓點、徽標、手風琴，折疊後只剩圖示列。"
            "選中項淡主色底 + 主色字，父層只轉主色不鋪底，明暗與主色全自動。"
        ),
        (
            "Multi-level sidebar nav: group titles, dots, badges and accordion; collapsed "
            "it keeps icons only. The selected row gets a tint of the primary colour and "
            "primary text, while its parents only take the colour — all theme-driven."
        ),
    ),
    "cat.navigation.pagination.title": (
        "分页器 Pagination",
        "分頁器 Pagination",
        "Pagination",
    ),
    "cat.navigation.pagination.hint": (
        (
            "总数、页码、每页条数一体。配色取自主题角色：切明暗、换主色都自动跟随；"
            "悬停时页码转主色。"
        ),
        (
            "總數、頁碼、每頁筆數一體。配色取自主題角色：切明暗、換主色都自動跟隨；"
            "懸停時頁碼轉主色。"
        ),
        (
            "Total, page and page size in one control. Colours come from theme roles, "
            "so dark mode and brand colour changes follow automatically; hovering a page "
            "turns its border and text to the brand colour."
        ),
    ),
    "cat.navigation.shell.title": ("应用外壳", "應用外殼", "App shell"),
    "cat.navigation.shell.desc": (
        "NavigationRail 与 AppBar 要放在外壳层，页面通过 use_route_outlet() 进来。",
        "NavigationRail 與 AppBar 要放在外殼層，頁面透過 use_route_outlet() 進來。",
        "NavigationRail and AppBar belong to the shell; pages arrive through use_route_outlet().",
    ),
    "cat.navigation.shell.tip_title": (
        "外壳只渲染一次",
        "外殼只算繪一次",
        "The shell renders once",
    ),
    "cat.navigation.shell.tip": (
        "外壳放在父路由上，切页时侧栏与顶栏不重建，滚动位置也更稳。",
        "外殼放在父路由上，切頁時側欄與頂欄不重建，捲動位置也更穩。",
        "Keep the shell on the parent route: sidebars and top bars survive navigation.",
    ),
    "cat.navigation.note1": (
        "面包屑最后一项默认不可点，因为它就是当前页。",
        "麵包屑最後一項預設不可點，因為它就是目前頁。",
        "The last crumb isn't clickable — it is the current page.",
    ),
    "cat.navigation.note2": (
        "分页器的单位（项 / 頁 / items）留空时跟随语言，要业务量词再显式传。",
        "分頁器的單位（項 / 頁 / items）留空時跟隨語言，要業務量詞再明確傳。",
        "Leave the paging unit empty to follow the language; pass a business noun when you need one.",
    ),
    "cat.navigation.tip_title": ("少一层导航", "少一層導覽", "One less layer"),
    "cat.navigation.tip": (
        "三个以上层级就别用面包屑了，换成标签页或侧边栏更清楚。",
        "三個以上層級就別用麵包屑了，換成頁籤或側邊欄更清楚。",
        "Beyond three levels, drop breadcrumbs for tabs or a sidebar.",
    ),
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
    "cat.form.input.hint": (
        "带标签、必填星号与类型校验；data_type 决定回读的类型。",
        "帶標籤、必填星號與型別驗證；data_type 決定回讀的型別。",
        "Label, required marker and type validation; data_type decides the read-back type.",
    ),
    "cat.form.number.title": (
        "数字输入框 NumberInput",
        "數字輸入框 NumberInput",
        "Number input",
    ),
    "cat.form.number.hint": (
        "按钮分左右平铺与右侧堆叠两种；精度、单位、步长、范围由组件兜住。",
        "按鈕分左右平鋪與右側堆疊兩種；精度、單位、步長、範圍由元件兜住。",
        "Buttons either flank the field or stack on the right; precision, unit, step and range are built in.",
    ),
    "cat.form.choice.title": (
        "勾选、开关与单选",
        "勾選、開關與單選",
        "Checks, switches, radios",
    ),
    "cat.form.choice.hint": (
        "CheckboxGroup 与 Radio 的选项横排竖排都行，必填会标星号。",
        "CheckboxGroup 與 Radio 的選項橫排直排都行，必填會標星號。",
        "CheckboxGroup and Radio lay out either way; required fields get a star.",
    ),
    "cat.form.select.title": ("下拉与多选", "下拉與多選", "Selects"),
    "cat.form.cascader.title": (
        "级联选择器 Cascader",
        "級聯選擇器 Cascader",
        "Cascader",
    ),
    "cat.form.cascader.hint": (
        "多列面板逐级展开；支持父子级联多选、任意级选取与关键字过滤。",
        "多列面板逐級展開；支持父子級聯多選、任意級選取與關鍵字過濾。",
        "Multi-column panel expands level by level; cascading multi-select, any-level picking and keyword filtering.",
    ),
    "cat.form.select.hint": (
        "SelectBox 单选，MultiSelect 多选；面板悬挂在内容之上，不推动布局。",
        "SelectBox 單選，MultiSelect 多選；面板懸掛在內容之上，不推動版面。",
        "SelectBox picks one, MultiSelect many; the panel floats above content without pushing layout.",
    ),
    "cat.form.transfer.title": ("穿梭框 Transfer", "穿梭框 Transfer", "Transfer"),
    "cat.form.transfer.hint": (
        (
            "两列常驻，一眼看到「已选 vs 未选」；勾一批、按箭头整批搬过去。"
            "勾选是全局的，搜索只影响可见性。"
        ),
        (
            "兩列常駐，一眼看到「已選 vs 未選」；勾一批、按箭頭整批搬過去。"
            "勾選是全域的，搜尋只影響可見性。"
        ),
        (
            "Two always-on columns show selected vs available at a glance; "
            "tick a batch and move it with one click. "
            "Ticks are global — search only narrows what you see."
        ),
    ),
    "cat.form.transfer.src": ("可授权", "可授權", "Available"),
    "cat.form.transfer.dst": ("已授权", "已授權", "Granted"),
    "cat.form.transfer.name": ("姓名", "姓名", "Name"),
    "cat.form.transfer.dept": ("部门", "部門", "Department"),
    "cat.form.transfer.dept_desc": (
        "一级 / 二级部门",
        "一級 / 二級部門",
        "Top level / sub-unit",
    ),
    "cat.form.transfer.email": ("邮箱", "郵箱", "Email"),
    "cat.form.transfer.email_desc": ("企业邮箱", "企業郵箱", "Work address"),
    "cat.form.transfer.phone": ("手机", "手機", "Phone"),
    "cat.form.transfer.id": ("证件号", "證件號", "ID number"),
    "cat.form.transfer.id_desc": (
        "脱敏存储，任何角色都拿不走",
        "去識別化儲存，任何角色都拿不走",
        "Masked at rest — nobody can move it",
    ),
    "cat.form.transfer.moved": ("移入 {n} 项", "移入 {n} 項", "Moved {n} in"),
    "cat.form.transfer.back": ("移回 {n} 项", "移回 {n} 項", "Moved {n} back"),
    "cat.form.transfer.current": (
        "当前已选：{keys}",
        "目前已選：{keys}",
        "Currently selected: {keys}",
    ),
    "cat.form.transfer.nothing": ("（空）", "（空）", "(none)"),
    "cat.form.transfer.plain_title": (
        "极简 + 单向",
        "極簡 + 單向",
        "Plain and one-way",
    ),
    "cat.form.transfer.plain_hint": (
        "关掉搜索与全选、只留一个方向：适合「一次性挑几个」的轻场景。",
        "關掉搜尋與全選、只留一個方向：適合「一次性挑幾個」的輕場景。",
        (
            "No search, no select-all, one direction only — "
            'for the light "pick a few" case.'
        ),
    ),
    "cat.form.date.title": ("日期与时间", "日期與時間", "Dates and times"),
    "cat.form.date.hint": (
        "九种类型共用一套月历：日 / 周 / 月 / 年、多选三种、范围两种，点标题还能逐层放大到月、到年。",
        "九種類型共用一套月曆：日 / 週 / 月 / 年、多選三種、範圍兩種，點標題還能逐層放大到月、到年。",
        "Nine types share one calendar: date / week / month / year, three multi-select flavours and two ranges — click the title to zoom out to months, then years.",
    ),
    "cat.form.slider.title": ("滑块 Slider", "滑桿 Slider", "Sliders"),
    "cat.form.slider.hint": (
        "单值与区间两种；刻度、提示气泡与步长都可调。",
        "單值與區間兩種；刻度、提示氣泡與步長都可調。",
        "Single value or range; ticks, value bubble and step are configurable.",
    ),
    "cat.form.rating.title": ("评分 Rating", "評分 Rating", "Rating"),
    "cat.form.rating.hint": (
        "可交互、只读与禁用三态。",
        "可互動、唯讀與停用三態。",
        "Interactive, read-only and disabled.",
    ),
    "cat.form.segment.title": (
        "分段按钮 SegmentedButton",
        "分段按鈕 SegmentedButton",
        "Segmented button",
    ),
    "cat.form.segment.hint": (
        "三五个互斥选项用分段按钮，比下拉少一次点击。",
        "三五個互斥選項用分段按鈕，比下拉少一次點擊。",
        "For three to five exclusive options, segmented beats a dropdown by a click.",
    ),
    "cat.form.color.title": (
        "取色器 ColorPicker",
        "取色器 ColorPicker",
        "Color picker",
    ),
    "cat.form.color.hint": (
        "支持带透明度的十六进制值，预设色板可调列数。",
        "支援帶透明度的十六進位值，預設色盤可調欄數。",
        "Accepts hex with alpha; preset swatch columns are adjustable.",
    ),
    "cat.form.search.title": ("搜索 SearchBar", "搜尋 SearchBar", "Search bar"),
    "cat.form.search.hint": (
        "点击后展开建议列表，适合从一长串候选项里挑。",
        "點擊後展開建議清單，適合從一長串候選項裡挑。",
        "Expands a suggestion list — good for picking from long candidates.",
    ),
    "cat.form.note1": (
        "标签宽度统一，横排时不会参差。",
        "標籤寬度統一，橫排時不會参差。",
        "Labels share one width, so columns line up.",
    ),
    "cat.form.note2": (
        "必填项在标签前加红星，不需要另写提示。",
        "必填項在標籤前加紅星，不需要另寫提示。",
        "Required fields get a red star — no extra hint needed.",
    ),
    "cat.form.note3": (
        "下拉面板与月历通过 page.overlay 悬挂，展开不改变布局高度。",
        "下拉面板與月曆透過 page.overlay 懸掛，展開不改變版面高度。",
        "Flyouts and calendars hang in page.overlay; opening them never shifts layout.",
    ),
    "cat.form.tip_title": (
        "用 use_ref 固定实例",
        "用 use_ref 固定實例",
        "Pin instances with use_ref",
    ),
    "cat.form.tip": (
        "表单控件放 use_ref，父组件重绘不会重建，用户输入才留得住。",
        "表單元件放 use_ref，父元件重繪不會重建，使用者輸入才留得住。",
        "Keep form controls in use_ref so parent re-renders don't rebuild them.",
    ),
    "cat.form.tip2_title": (
        "切语言不丢内容",
        "切語言不遺失內容",
        "Language switches keep values",
    ),
    "cat.form.tip2": (
        "切语言只会重绘文案；控件实例被复用，所以填了一半的表单还是原来那份。",
        "切語言只會重繪文案；元件實例被重用，所以填了一半的表單還是原來那份。",
        "Switching language re-renders labels only; instances are reused, so a half-filled form stays filled.",
    ),
    "cat.feedback.intro": (
        "反馈分两档：自己动手后的立即回执走 Message，系统的被动通报走 Notification。",
        "回饋分兩檔：自己動手後的回執走 Message，系統的被動通報走 Notification。",
        "Feedback comes in two tiers: instant receipts for your own actions (Message), and system notices you never asked for (Notification).",
    ),
    "cat.feedback.msg.title": ("消息提示 Message", "訊息提示 Message", "Message"),
    "cat.feedback.msg.hint": (
        "主动操作后的反馈：顶部居中、几秒后自己走开，不打断手上的事。",
        "主動操作後的回饋：頂部置中、幾秒後自己走開，不打斷手上的事。",
        "Feedback after your own action: top center, gone in seconds, never in the way.",
    ),
    "cat.feedback.msg.body": (
        "这是一条{kind}提示",
        "這是一條{kind}提示",
        "A {kind} message",
    ),
    "cat.feedback.msg.closable": ("可关闭", "可關閉", "Closable"),
    "cat.feedback.msg.closablebody": (
        "这条会一直留着，直到你点右边的 ×。",
        "這條會一直留著，直到你點右邊的 ×。",
        "This one stays until you hit the × on the right.",
    ),
    "cat.feedback.msg.grouping": ("合并计数", "合併計數", "Grouping"),
    "cat.feedback.msg.groupbody": ("已保存", "已儲存", "Saved"),
    "cat.feedback.msg.long": ("长文案", "長文案", "Long text"),
    "cat.feedback.msg.longbody": (
        "这条文案故意写长，用来看它会怎么在卡片里折行：文字老老实实待在圆角里，图标仍然垂直居中，不会被挤到卡片外面去。",
        "這條文案故意寫長，用來看看它會怎麼在卡片裡折行：文字老老實實待在圓角裡，圖示仍然垂直置中，不會被擠到卡片外面去。",
        "Deliberately long, to show how it wraps: the text stays inside the rounded card, and the icon stays vertically centred instead of being pushed out.",
    ),
    "cat.feedback.msg.closeall": ("全部关闭", "全部關閉", "Close all"),
    "cat.feedback.style.default": ("默认", "預設", "Default"),
    "cat.feedback.style.primary": ("主要", "主要", "Primary"),
    "cat.feedback.style.info": ("信息", "資訊", "Info"),
    "cat.feedback.style.success": ("成功", "成功", "Success"),
    "cat.feedback.style.warning": ("警告", "警告", "Warning"),
    "cat.feedback.style.error": ("错误", "錯誤", "Error"),
    "cat.feedback.notify.title": (
        "通知 Notification",
        "通知 Notification",
        "Notification",
    ),
    "cat.feedback.notify.hint": (
        "系统级提醒：贴在角落、带标题、可以一直挂着等你处理。",
        "系統級提醒：貼在角落、帶標題、可以一直掛著等你處理。",
        "System notices: pinned to a corner, titled, and able to wait for you.",
    ),
    "cat.feedback.notify.head": ("同步完成", "同步完成", "Sync finished"),
    "cat.feedback.notify.body": (
        "3 个组件已更新到最新版本，重新打开文档即可生效。",
        "3 個元件已更新到最新版本，重新開啟文件即可生效。",
        "3 components were updated. Reopen the document to pick them up.",
    ),
    "cat.feedback.notify.sticky": ("常驻", "常駐", "Sticky"),
    "cat.feedback.notify.stickyTitle": ("需要处理", "需要處理", "Needs a decision"),
    "cat.feedback.notify.stickyBody": (
        "不会自动关闭，处理完再点 ×。",
        "不會自動關閉，處理完再點 ×。",
        "Won't close itself — dismiss it when you're done.",
    ),
    "cat.feedback.notify.pos.tl": ("左上角", "左上角", "Top left"),
    "cat.feedback.notify.pos.tr": ("右上角", "右上角", "Top right"),
    "cat.feedback.notify.pos.bl": ("左下角", "左下角", "Bottom left"),
    "cat.feedback.notify.pos.br": ("右下角", "右下角", "Bottom right"),
    "cat.feedback.notify.posbody": (
        "从{pos}弹出来，新的一条从这里长出去。",
        "從{pos}彈出來，新的一條從這裡長出去。",
        "Pops out of the {pos} corner — new ones grow from there.",
    ),
    "cat.feedback.dialog.title": ("对话框", "對話框", "Dialogs"),
    "cat.feedback.dialog.hint": (
        "只有“必须选一个”的时刻才用对话框——它抢焦点，代价最高。",
        "只有「必須選一個」的時刻才用對話框——它搶焦點，代價最高。",
        "Reserve dialogs for “pick one” moments — they steal focus and cost the most.",
    ),
    "cat.feedback.dialog.open": ("打开对话框", "開啟對話框", "Open dialog"),
    "cat.feedback.dialog.title2": (
        "删除这个文件？",
        "刪除這個檔案？",
        "Delete this file?",
    ),
    "cat.feedback.dialog.msg": (
        "删除后无法恢复，请确认。",
        "刪除後無法復原，請確認。",
        "This can't be undone. Are you sure?",
    ),
    "cat.feedback.dialog.done": ("已删除", "已刪除", "Deleted"),
    "cat.feedback.dialog.cancel": ("已取消", "已取消", "Cancelled"),
    "cat.feedback.dialog.notify": ("发一条通知", "發一條通知", "Send a notification"),
    "cat.feedback.progress.title": ("进度与加载", "進度與載入", "Progress and loading"),
    "cat.feedback.progress.hint": (
        "确定的进度用进度条，不确定的用环形加载。",
        "確定的進度用進度條，不確定的用環形載入。",
        "Known progress gets a bar; unknown gets a ring.",
    ),
    "cat.feedback.progress.download": ("下载中 72%", "下載中 72%", "Downloading 72%"),
    "cat.feedback.progress.index": (
        "索引中（按百分比传值）",
        "索引中（依百分比傳值）",
        "Indexing (percent in)",
    ),
    "cat.feedback.progress.loading": (
        "三种尺寸的加载环",
        "三種尺寸的載入環",
        "Three ring sizes",
    ),
    "cat.feedback.note1": (
        "Message 不抢焦点、不挡点击；Notification 会停在那儿等你处理。",
        "Message 不搶焦點、不擋點擊；Notification 會停在那兒等你處理。",
        "Messages never steal focus or block a click; notifications stay put until handled.",
    ),
    "cat.feedback.note2": (
        "对话框的按钮文案来自语言包，切的不是主色而是语义。",
        "對話框的按鈕文案來自語言包，切的不是主色而是語意。",
        "Dialog buttons come from the catalog — semantics, not colors, pick them.",
    ),
    "cat.feedback.note3": (
        "进度条接受 0–1 的小数，也接受 0–100 的整数。",
        "進度條接受 0–1 的小數，也接受 0–100 的整數。",
        "Progress bars take 0–1 floats or 0–100 ints.",
    ),
    "cat.feedback.tip_title": (
        "别把回执做成长篇通知",
        "別把回執做成長篇通知",
        "Don't dress a receipt as a notice",
    ),
    "cat.feedback.tip": (
        "“已保存”这种一句话的事，用 Message；要用户读三段话再决定的，用 Notification。",
        "「已儲存」這種一句話的事，用 Message；要使用者讀三段話再決定的，用 Notification。",
        "One-liners like “saved” belong in a Message; anything that needs three lines of thought before acting belongs in a Notification.",
    ),
    "cat.feedback.tip2_title": (
        "错误要说清下一步",
        "錯誤要說清下一步",
        "Errors need a next step",
    ),
    "cat.feedback.tip2": (
        "“保存失败”不如“磁盘已满，请清理后重试”。",
        "「儲存失敗」不如「磁碟已滿，請清理後重試」。",
        "“Save failed” is worse than “Disk full — free some space and retry”.",
    ),
    "cat.display.intro": (
        "展示型控件负责把数据摆好看：列表项、代码与日志。",
        "展示型元件負責把資料擺好看：清單項、程式碼與日誌。",
        ("Display controls make data presentable: list tiles, code and logs."),
    ),
    "cat.display.tile.title": ("列表项 ListTile", "清單項 ListTile", "List tiles"),
    "cat.display.tile.hint": (
        "头像、标题、副标题与尾部操作，一行说清一件事。",
        "頭像、標題、副標題與尾端操作，一列說清一件事。",
        "Avatar, title, subtitle and trailing action — one row, one thing.",
    ),
    "cat.display.tile.more": ("更多", "更多", "More"),
    "cat.display.editor.title": (
        "代码编辑器 CodeEditor",
        "程式碼編輯器 CodeEditor",
        "Code editor",
    ),
    "cat.display.editor.hint": (
        "带行号与语法高亮的可编辑区域，read_only 即为代码块。",
        "帶行號與語法高亮的可編輯區域，read_only 即為程式碼區塊。",
        "Editable with line numbers and highlighting; read_only turns it into a code block.",
    ),
    "cat.display.view.title": ("代码视图 CodeView", "程式碼檢視 CodeView", "Code view"),
    "cat.display.view.hint": (
        "一个组件配一段可展开的源码，适合做“这个控件怎么用”。",
        "一個元件配一段可展開的原始碼，適合做「這個元件怎麼用」。",
        "A live control plus collapsible source — perfect for “how do I use this”.",
    ),
    "cat.display.tree.title": ("树形控件 Tree", "樹形控件 Tree", "Tree"),
    "cat.display.tree.hint": (
        "展开折叠、复选联动与关键字过滤；长树给 height 后只构建可见行。",
        "展開摺疊、複選聯動與關鍵字過濾；長樹給 height 後只建構可見列。",
        "Expand/collapse, cascading checkboxes and keyword filtering; with height set, only visible rows are built.",
    ),
    "cat.display.desc.title": (
        "描述列表 Descriptions",
        "描述清單 Descriptions",
        "Descriptions",
    ),
    "cat.display.desc.hint": (
        "一条记录十几个字段时，用可跨列的网格摆整齐；bordered=False 退成轻量对齐排布。",
        "一筆記錄十幾個欄位時，用可跨欄的網格排整齊；bordered=False 退成輕量對齊排布。",
        "Lay a dozen fields on a grid that can span columns; bordered=False drops to a lighter aligned layout.",
    ),
    "cat.display.desc.h1": ("带边框（默认）", "帶邊框（預設）", "Bordered (default)"),
    "cat.display.desc.h2": (
        "垂直方向（标签在上）",
        "垂直方向（標籤在上）",
        "Vertical (label above)",
    ),
    "cat.display.desc.h3": (
        "无边框 · small 档位",
        "無邊框 · small 檔位",
        "Borderless · small",
    ),
    "cat.display.desc.edit": ("编辑", "編輯", "Edit"),
    "cat.display.desc.name": ("用户名", "使用者名稱", "Username"),
    "cat.display.desc.phone": ("手机号", "手機號", "Phone"),
    "cat.display.desc.city": ("居住地", "居住地", "Location"),
    "cat.display.desc.city_value": ("苏州市", "蘇州市", "Suzhou"),
    "cat.display.desc.note": ("备注", "備註", "Note"),
    "cat.display.desc.school": ("学校", "學校", "School"),
    "cat.display.desc.address": ("联系地址", "聯絡地址", "Address"),
    "cat.display.desc.address_value": (
        "江苏省苏州市吴中区吴中大道 1188 号",
        "江蘇省蘇州市吳中區吳中大道 1188 號",
        "1188 Wuzhong Ave, Suzhou, Jiangsu",
    ),
    "cat.display.desc.order_no": ("订单号", "訂單號", "Order"),
    "cat.display.desc.customer": ("客户", "客戶", "Customer"),
    "cat.display.desc.customer_value": (
        "苏州云舟科技有限公司",
        "蘇州雲舟科技有限公司",
        "Suzhou Yunzhou Tech",
    ),
    "cat.display.desc.placed_at": ("下单时间", "下單時間", "Placed at"),
    "cat.display.desc.amount": ("金额", "金額", "Amount"),
    "cat.display.desc.state": ("状态", "狀態", "Status"),
    "cat.display.desc.state_value": ("已发货", "已出貨", "Shipped"),
    "cat.display.desc.ship_to": ("收货地址", "收貨地址", "Ship to"),
    "cat.display.desc.ship_to_value": (
        "江苏省苏州市吴中区吴中大道 1188 号 3 号楼 502 室",
        "江蘇省蘇州市吳中區吳中大道 1188 號 3 號樓 502 室",
        "Room 502, Bldg 3, 1188 Wuzhong Ave, Suzhou, Jiangsu",
    ),
    "cat.display.view.preview": ("这是预览区", "這是預覽區", "This is the preview"),
    "cat.display.num.title": (
        "数值动画 NumberAnimation",
        "數值動畫 NumberAnimation",
        "NumberAnimation",
    ),
    "cat.display.num.hint": (
        (
            "给个终点它就自己滚过去：千分位、小数位、前后缀都按你的写法来。点一下卡片"
            "从头再滚一遍；中途改 end 会从当前值接着走，不会跳回 0。"
        ),
        (
            "給個終點它就自己滾過去：千分位、小數位、前後綴都照你的寫法。點一下卡片"
            "從頭再滾一遍；中途改 end 會從當前值接著走，不會跳回 0。"
        ),
        (
            "Give it a target and it rolls there: grouping, decimals, prefix and suffix "
            "all follow your settings. Click a card to replay; changing end mid-flight "
            "continues from the current value instead of jumping back to zero."
        ),
    ),
    "cat.display.num.amount": ("本月成交额", "本月成交額", "Revenue this month"),
    "cat.display.num.amount_note": ("较上月 +18.2%", "較上月 +18.2%", "+18.2% MoM"),
    "cat.display.num.rate": ("转化率", "轉化率", "Conversion"),
    "cat.display.num.rate_note": ("目标 10.0%", "目標 10.0%", "Target 10.0%"),
    "cat.display.num.online": ("在线设备", "線上裝置", "Devices online"),
    "cat.display.num.online_note": ("峰值 9,120", "峰值 9,120", "Peak 9,120"),
    "cat.display.num.replay": (
        "点任意一张卡片重播",
        "點任意一張卡片重播",
        "Click any card to replay",
    ),
    "cat.display.heat.title": ("热力图 Heatmap", "熱力圖 Heatmap", "Heatmap"),
    "cat.display.heat.hint": (
        "一年 365 天铺成格子，颜色越深越活跃；鼠标划过去看具体数值。",
        "一年 365 天鋪成格子，顏色越深越活躍；滑鼠移過去查看具體數值。",
        "A year of days as a grid — deeper colour, busier day. Hover for the number.",
    ),
    "cat.display.heat.sub": (
        "small 档位 · blue 色阶 · 不带图例",
        "small 檔位 · blue 色階 · 不帶圖例",
        "small · blue · no legend",
    ),
    "cat.display.heat.stats": (
        "总天数 {days} · 有值 {filled} · 峰值 {peak} · 均值 {mean}",
        "總天數 {days} · 有值 {filled} · 峰值 {peak} · 均值 {mean}",
        "{days} days · {filled} active · peak {peak} · mean {mean}",
    ),
    "cat.display.cal.title": ("日历 Calendar", "日曆 Calendar", "Calendar"),
    "cat.display.cal.hint": (
        "整月一张大日历：格子里可以再放内容（这里是小圆点），点标题切年视图，点日期选一天。",
        "整月一張大日曆：格子裡可以再放內容（這裡是小圓點），點標題切年視圖，點日期選一天。",
        "A full month as one panel: cells can carry extra content (dots here), the title zooms out to years, a click picks a day.",
    ),
    "cat.display.cal.selected": ("选中：{date}", "選取：{date}", "Selected: {date}"),
    "cat.display.carousel.title": ("轮播 Carousel", "輪播 Carousel", "Carousel"),
    "cat.display.carousel.hint": (
        (
            "一块地方轮流摆 N 张。悬停才浮出箭头，圆点压在图上；指针停进来自动播放就暂停，"
            "读完再走。宽度不用给，挂载后自己量。"
        ),
        (
            "一塊地方輪流擺 N 張。懸停才浮出箭頭，圓點壓在圖上；指標停進來自動播放就暫停，"
            "讀完再走。寬度不用給，掛載後自己量。"
        ),
        (
            "N slides rotate through one box. Arrows fade in on hover, dots sit on the "
            "image, and autoplay pauses while the pointer rests — so nothing flips away "
            "mid-sentence. Width is measured after mount, never passed in."
        ),
    ),
    "cat.display.carousel.current": (
        "第 {n} 张，共 {total} 张",
        "第 {n} 張，共 {total} 張",
        "Slide {n} of {total}",
    ),
    "cat.display.note1": (
        "代码主题跟随明暗模式，浅色界面里也能看清。",
        "程式碼主題跟隨明暗模式，淺色介面裡也能看清。",
        "Code themes follow light/dark so contrast always holds.",
    ),
    "cat.display.note2": (
        "ListTile 的 trailing 可以放开关、按钮或角标。",
        "ListTile 的 trailing 可以放開關、按鈕或角標。",
        "ListTile trailing takes switches, buttons or badges.",
    ),
    "cat.display.note3": (
        "CodeView 折叠时只占一行，展开后不挤压周围内容。",
        "CodeView 摺疊時只佔一列，展開後不擠壓周圍內容。",
        "Collapsed CodeView is one row; expanded it doesn't squeeze neighbours.",
    ),
    "cat.display.tip_title": ("代码也属于界面", "程式碼也屬於介面", "Code is UI too"),
    "cat.display.tip": (
        "技术产品的文档里，代码块的可读性和正文一样重要。",
        "技術產品的文件裡，程式碼區塊的可讀性和內文一樣重要。",
        "In developer docs a code block matters as much as the prose.",
    ),
    "cat.charts.intro": (
        "图表封装了配色、轴范围与提示气泡；传数据就能出图。",
        "圖表封裝了配色、軸範圍與提示氣泡；傳資料就能出圖。",
        ("Charts bundle colours, axis ranges and tooltips — pass data, get a chart."),
    ),
    "cat.charts.line.title": ("折线与面积", "折線與面積", "Line and area"),
    "cat.charts.line.hint": (
        "多列即多条线，x 轴数值与分类通吃。",
        "多欄即多條線，x 軸數值與分類通吃。",
        "Multiple columns become multiple lines; x takes numbers or categories.",
    ),
    "cat.charts.bar.title": ("柱状", "長條", "Bar"),
    "cat.charts.bar.hint": (
        "分组与堆叠两种，柱子圆角统一。",
        "分組與堆疊兩種，柱子圓角統一。",
        "Grouped or stacked, with consistent corner radius.",
    ),
    "cat.charts.scatter.title": ("散点", "散佈", "Scatter"),
    "cat.charts.scatter.hint": (
        "传 (x, y) 元组列表即可，适合看相关性。",
        "傳 (x, y) 元組清單即可，適合看相關性。",
        "Feed it (x, y) tuples — good for spotting correlation.",
    ),
    "cat.charts.tip_title": ("颜色跟着主题", "顏色跟著主題", "Colors follow the theme"),
    "cat.charts.tip": (
        "不传 color 时使用与主题协调的色板，换主色后图表也跟着变。",
        "不傳 color 時使用與主題協調的色盤，換主色後圖表也跟著變。",
        "Omit color to inherit a palette that tracks your seed color.",
    ),
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
    "cat.media.audio.hint": (
        "AudioPlayer 是卡片式播放器；Audio 本身是 Service，构造即注册。",
        "AudioPlayer 是卡片式播放器；Audio 本身是 Service，建構即註冊。",
        "AudioPlayer is the card player; Audio itself is a service — constructing it registers it.",
    ),
    "cat.media.audio.track": ("夜航", "夜航", "Night drive"),
    "cat.media.audio.track2": ("第二首", "第二首", "Second track"),
    "cat.media.audio.artist": (
        "示例音轨 · SoundHelix",
        "範例音軌 · SoundHelix",
        "Sample track · SoundHelix",
    ),
    "cat.media.note1": (
        "播放状态是 observable 的，界面可以跟着变。",
        "播放狀態是 observable 的，介面可以跟著變。",
        "Playback state is observable, so the UI can react.",
    ),
    "cat.media.note2": (
        "远程地址与本地路径都接受，网络资源需要允许访问。",
        "遠端位址與本機路徑都接受，網路資源需要允許存取。",
        "Remote URLs and local paths both work, given network permission.",
    ),
    "cat.media.tip_title": ("大文件别内嵌", "大檔案別內嵌", "Don't inline big files"),
    "cat.media.tip": (
        "几十页的 PDF 嵌在页面里会很重，给出入口比内嵌更合适。",
        "幾十頁的 PDF 嵌在頁面裡會很重，給出入口比內嵌更合適。",
        "A 40-page PDF inline is heavy; link out instead.",
    ),
    "cat.upload.intro": (
        "文件链路有三段：选文件、选目录、选保存位置。三者的结果都直接读 value。",
        "檔案鏈路有三段：選檔案、選目錄、選儲存位置。三者的結果都直接讀 value。",
        (
            "Files come in three steps: pick a file, a folder, a save target. All exp"
            "ose value."
            ""
        ),
    ),
    "cat.upload.picker.title": (
        "文件、目录与保存",
        "檔案、目錄與儲存",
        "Files, folders, saving",
    ),
    "cat.upload.picker.hint": (
        "allowed_extensions 限定类型；allow_multiple 控制多选。",
        "allowed_extensions 限定型別；allow_multiple 控制多選。",
        "allowed_extensions filters types; allow_multiple enables multi-select.",
    ),
    "cat.upload.read": ("读取选择结果", "讀取選擇結果", "Read the values"),
    "cat.upload.dump": (
        "文件 {files} 个 · 目录 {folder} · 保存到 {save}",
        "檔案 {files} 個 · 目錄 {folder} · 儲存到 {save}",
        "{files} file(s) · folder {folder} · save to {save}",
    ),
    "cat.upload.image.title": (
        "图片选择 ImagePicker",
        "圖片選擇 ImagePicker",
        "Image picker",
    ),
    "cat.upload.image.hint": (
        "带缩略预览的图片选择器，适合头像与封面。",
        "帶縮圖預覽的圖片選擇器，適合頭像與封面。",
        "An image picker with thumbnail preview — avatars, covers.",
    ),
    "cat.upload.image.label": ("头像", "頭像", "Avatar"),
    "cat.upload.tip_title": (
        "先校验再上传",
        "先驗證再上傳",
        "Validate before uploading",
    ),
    "cat.upload.tip": (
        "allowed_extensions 只是第一道门；大小与内容还得在提交时再查一次。",
        "allowed_extensions 只是第一道門；大小與內容還得在提交時再查一次。",
        "allowed_extensions is only the first gate — check size and content on submit.",
    ),
    "cat.upload.tip2_title": ("路径可能为空", "路徑可能為空", "Paths can be empty"),
    "cat.upload.tip2": (
        "用户取消选择时 value 保持原值或为空，回读前先判空。",
        "使用者取消選擇時 value 保持原值或為空，回讀前先判空。",
        "If the user cancels, value stays empty — guard before reading.",
    ),
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
    "about.principles.desc": (
        "这几条决定了 cs-ui 长什么样，也决定了它不做什么。",
        "這幾條決定了 cs-ui 長什麼樣，也決定了它不做什麼。",
        "These rules decide what cs-ui looks like — and what it refuses to do.",
    ),
    "about.principle1": (
        "默认值优先：组件不传参数就该好看，参数只用来表达差异。",
        "預設值優先：元件不傳參數就該好看，參數只用來表達差異。",
        "Defaults first: a component with no arguments should already look right.",
    ),
    "about.principle2": (
        "令牌而不是常量：颜色、间距、圆角都从一处来，换肤不用搜代码。",
        "權杖而不是常數：顏色、間距、圓角都從一處來，換膚不用搜程式碼。",
        "Tokens, not constants: color, spacing and radius come from one place.",
    ),
    "about.principle3": (
        "订阅而不是广播：只有真正读了状态的组件才重绘。",
        "訂閱而不是廣播：只有真正讀了狀態的元件才重繪。",
        "Subscriptions, not broadcasts: only components that read state re-render.",
    ),
    "about.principle4": (
        "可组合而不是可配置：需要新外观就组合，不要加第十个布尔参数。",
        "可組合而不是可配置：需要新外觀就組合，不要加第十個布林參數。",
        "Compose, don't configure: new looks come from composition, not a tenth boolean.",
    ),
    "about.links.title": ("相关链接", "相關連結", "Links"),
    "about.link.github": ("GitHub 仓库", "GitHub 儲存庫", "GitHub repository"),
    "about.link.flet": ("Flet 官方文档", "Flet 官方文件", "Flet documentation"),
    "about.link.license": (
        "许可与贡献指南",
        "授權與貢獻指南",
        "License and contributing",
    ),
    "demo.menu.home": ("概览", "概覽", "Overview"),
    "demo.menu.monitor": ("监控", "監控", "Monitoring"),
    "demo.menu.group": ("运维", "維運", "Operations"),
    "demo.menu.host": ("主机", "主機", "Hosts"),
    "demo.menu.host_list": ("主机列表", "主機清單", "Host list"),
    "demo.menu.host_group": ("主机分组", "主機分組", "Host groups"),
    "demo.menu.host_tag": ("标签管理", "標籤管理", "Tags"),
    "demo.menu.net": ("网络", "網路", "Network"),
    "demo.menu.vpc": ("私有网络", "私有網路", "VPC"),
    "demo.menu.eip": ("弹性 IP", "彈性 IP", "Elastic IP"),
    "demo.menu.setting": ("设置", "設定", "Settings"),
    "demo.menu.audit": ("审计日志", "稽核日誌", "Audit log"),
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
    "demo.tree.search": ("按名称过滤", "按名稱過濾", "Filter by name"),
    "demo.field.qty": ("数量", "數量", "Quantity"),
    "demo.field.rate": ("税率", "稅率", "Tax rate"),
    "demo.field.budget": ("预算", "預算", "Budget"),
    "demo.field.folder": ("项目目录", "專案目錄", "Project folder"),
    "demo.field.agree": (
        "我已阅读并同意条款",
        "我已閱讀並同意條款",
        "I accept the terms",
    ),
    "demo.field.hobbies": ("兴趣爱好", "興趣愛好", "Interests"),
    "demo.field.notify": ("接收通知", "接收通知", "Notifications"),
    "demo.field.compact": ("紧凑模式", "緊湊模式", "Compact mode"),
    "demo.field.plan": ("订阅方案", "訂閱方案", "Plan"),
    "demo.field.city": ("城市", "城市", "City"),
    "demo.field.tags": ("标签", "標籤", "Tags"),
    "demo.field.date": ("日期", "日期", "Date"),
    "demo.field.week": ("周", "週", "Week"),
    "demo.field.month": ("月份", "月份", "Month"),
    "demo.field.year": ("年份", "年份", "Year"),
    "demo.field.dates": ("多个日期", "多個日期", "Dates"),
    "demo.field.daterange": ("日期范围", "日期範圍", "Date range"),
    "demo.field.monthrange": ("月份范围", "月份範圍", "Month range"),
    "demo.field.birthday": ("生日", "生日", "Birthday"),
    "demo.field.meeting": ("会议时间", "會議時間", "Meeting"),
    "demo.field.volume": ("音量", "音量", "Volume"),
    "demo.field.price": ("价格区间", "價格區間", "Price range"),
    "demo.field.brand": ("品牌色", "品牌色", "Brand color"),
    "demo.field.overlay": (
        "叠加色（带透明度）",
        "疊加色（帶透明度）",
        "Overlay (with alpha)",
    ),
    "demo.rating.editable": ("可交互", "可互動", "Interactive"),
    "demo.rating.readonly": ("只读", "唯讀", "Read-only"),
    "demo.rating.disabled": ("禁用", "停用", "Disabled"),
    "demo.search.bar": ("搜索城市", "搜尋城市", "Search cities"),
    "demo.search.view": ("输入城市名", "輸入城市名", "Type a city"),
    "demo.search.hint": (
        "点击后展开建议列表。",
        "點擊後展開建議清單。",
        "Click to expand suggestions.",
    ),
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
                raise SystemExit(
                    f"{name}[{key!r}] 必须是 {len(locales)} 元组，实际是 {triple!r}"
                )
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

    if args.check:
        return _check_against_disk(tables)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for code, table in tables.items():
        (OUT_DIR / f"{code.replace('-', '_')}.json").write_text(
            json.dumps(table, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(f"{len(tables['zh-CN'])} keys × {len(tables)} languages → {OUT_DIR}")
    return 0


#: 每类问题最多列这么多条 —— 全量刷屏反而看不出"哪一类错得最多"。
_REPORT_LIMIT = 8


def _check_against_disk(tables: dict[str, dict[str, str]]) -> int:
    """把内存里的表与磁盘上的 JSON 逐键比对，返回进程退出码。

    只比"三语键数是否相等"是不够的：改了一句中文文案却忘了重新生成，三份 JSON
    依旧键数一致、检查照样通过，站点上却是旧话术 —— 这个洞真的漏过一次
    （``Flet 1.1.0`` 在源码里改成 ``1.1.2`` 之后，生成物仍是旧版本）。
    所以这里必须比**内容**。
    """
    drifted = False
    for code, table in tables.items():
        path = OUT_DIR / f"{code.replace('-', '_')}.json"
        if not path.exists():
            print(
                f"{path.name}: 文件不存在，请运行 build_docs_i18n.py", file=sys.stderr
            )
            drifted = True
            continue

        on_disk: dict[str, str] = json.loads(path.read_text(encoding="utf-8"))
        # 只有在磁盘上、源码里已删掉的键
        stale = sorted(set(on_disk) - set(table))
        # 源码里有、磁盘上还没生成的键
        missing = sorted(set(table) - set(on_disk))
        # 键相同但文案变了
        changed = sorted(
            key for key in table.keys() & on_disk.keys() if on_disk[key] != table[key]
        )
        if not (stale or missing or changed):
            continue

        drifted = True
        print(f"{path.name}:", file=sys.stderr)
        for label, keys in (
            ("已下线但仍留在生成物里", stale),
            ("源码有但生成物缺失", missing),
            ("文案已改但未重新生成", changed),
        ):
            if not keys:
                continue
            print(f"  {label}：{len(keys)} 个", file=sys.stderr)
            for key in keys[:_REPORT_LIMIT]:
                print(f"    - {key}", file=sys.stderr)
            if len(keys) > _REPORT_LIMIT:
                print(f"    … 另有 {len(keys) - _REPORT_LIMIT} 个", file=sys.stderr)

    if drifted:
        print(
            "语言包与源码不一致，请运行：python scripts/build_docs_i18n.py",
            file=sys.stderr,
        )
        return 1

    print(f"{len(tables['zh-CN'])} keys × {len(tables)} languages 已是最新")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
