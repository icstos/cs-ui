"""文档内容注册表：页面 key → 内容块。

内容层是**纯数据**，所以外壳可以静态算出每页的目录、搜索引擎可以静态建索引。

组件说明不在这里 —— 它们在各自的实现文件里（``SPEC``），由
:mod:`ui.core.catalog` 按需装配。这里只留下"文章型"页面。
"""

from __future__ import annotations

from docs.blocks import Doc
from docs.content.about import ABOUT
from docs.content.gallery import GALLERY
from docs.content.guides import ARCHITECTURE, I18N, THEMING
from docs.content.start import QUICKSTART

DOCS: dict[str, Doc] = {
    "quickstart": QUICKSTART,
    "architecture": ARCHITECTURE,
    "theming": THEMING,
    "i18n": I18N,
    "components": GALLERY,
    "about": ABOUT,
}

__all__ = ["DOCS"]
