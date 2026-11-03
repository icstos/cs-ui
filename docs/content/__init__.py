"""文档内容注册表：页面 key → 内容块。

内容层是**纯数据**，所以外壳可以静态算出每页的目录、搜索引擎可以静态建索引。
"""

from __future__ import annotations

from docs.blocks import Doc
from docs.content.about import ABOUT
from docs.content.components.charts import CHARTS
from docs.content.components.display import DISPLAY
from docs.content.components.feedback import FEEDBACK
from docs.content.components.form import FORM
from docs.content.components.general import GENERAL
from docs.content.components.layout import LAYOUT
from docs.content.components.media import MEDIA
from docs.content.components.navigation import NAVIGATION
from docs.content.components.upload import UPLOAD
from docs.content.gallery import GALLERY
from docs.content.guides import ARCHITECTURE, I18N, THEMING
from docs.content.start import QUICKSTART

DOCS: dict[str, Doc] = {
    "quickstart": QUICKSTART,
    "architecture": ARCHITECTURE,
    "theming": THEMING,
    "i18n": I18N,
    "components": GALLERY,
    "general": GENERAL,
    "layout": LAYOUT,
    "navigation": NAVIGATION,
    "form": FORM,
    "feedback": FEEDBACK,
    "display": DISPLAY,
    "charts": CHARTS,
    "media": MEDIA,
    "upload": UPLOAD,
    "about": ABOUT,
}

__all__ = ["DOCS"]
