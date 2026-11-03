"""cs-ui 官方文档站。

文档站本身完全由 ``ui`` 组件库构建，同时充当框架的能力演示：主题、多语言、
声明式路由、命令面板与组件画廊。

结构（一层一件事）::

    site.py      站点数据：页面清单、分组、搜索索引（纯数据，不认识控件）
    blocks.py    正文 DSL：Heading / Prose / Code / Demo / Split …
    content/     各页正文，全是数据；三语靠 key 对齐语言包
    render.py    把 blocks 变成控件，并抽"本页目录"
    kit.py       视觉基础件：卡片面、代码块、提示条、演示框
    shell.py     外壳：顶栏 / 侧边栏 / 本页目录 / 页脚
    search.py    命令面板（⌘K 式搜索，浮层）
    pages.py     通用文档页组件 + 404
    home.py      首页
    app.py       路由与 Provider 组装
    main.py      桌面入口
    i18n/site/   三语语言包，由 ``scripts/build_docs_i18n.py`` 生成
"""

from __future__ import annotations
