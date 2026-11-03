"""cs-ui 官网入口。

运行::

    python docs/main.py

改文案后重新生成三语语言包::

    python scripts/build_docs_i18n.py          # 写盘
    python scripts/build_docs_i18n.py --check  # 只校验

无头冒烟（三种语言各跑一遍）::

    python scripts/smoke_test.py docs.main main --routes /,/docs/quickstart,/components

截图（真实窗口）::

    CS_UI_DOCS_ROUTE=/docs/theming python scripts/_probe_demo.py --app scripts/_shot_docs.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for entry in (ROOT, ROOT / "src"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

import flet as ft

from docs.app import App
from docs.site import FONT_FAMILY, FONT_FILE
from ui import theme_state

TITLE = "cs-ui · 用 Python 构建桌面界面"


def configure_page(page: ft.Page) -> None:
    """窗口、字体与内边距。

    主题交给 ``ThemeProvider``；这里只登记字体，并让主题状态引用同一个族名 ——
    两处必须一致，否则字体会在首帧与重绘之间来回跳。
    """
    page.title = TITLE
    page.padding = 0
    page.window.width = 1360
    page.window.height = 880
    page.window.min_width = 1040
    page.window.min_height = 680
    if FONT_FILE.exists():
        page.fonts = {FONT_FAMILY: str(FONT_FILE)}
        theme_state().font_family = FONT_FAMILY


def main(page: ft.Page) -> None:
    configure_page(page)
    page.render(App)


if __name__ == "__main__":
    ft.run(main)
