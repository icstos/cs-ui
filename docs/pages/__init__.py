"""官网与文档页面。"""

from __future__ import annotations

from docs.pages.about import about_page
from docs.pages.architecture import architecture_page
from docs.pages.components import components_page
from docs.pages.getting_started import getting_started_page
from docs.pages.home import home_page
from docs.pages.i18n import i18n_page
from docs.pages.not_found import not_found_page
from docs.pages.search import search_page
from docs.pages.theming import theming_page

__all__ = [
    "about_page",
    "architecture_page",
    "components_page",
    "getting_started_page",
    "home_page",
    "i18n_page",
    "not_found_page",
    "search_page",
    "theming_page",
]
