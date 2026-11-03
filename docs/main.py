"""cs-ui 官方文档站入口。

运行::

    python docs/main.py

无头冒烟::

    python scripts/smoke_test.py docs.main App --routes /,/docs/getting-started,/about
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
from docs.core.assets import FONT_FAMILY, FONT_FILE
from ui import theme_state


def configure_page(page: ft.Page) -> None:
    """窗口与字体等页面级设置。

    主题交给 ``ThemeProvider``；这里只登记字体，再让主题状态引用同一族名，
    两处必须保持一致，否则界面字体会在首帧与重绘之间来回跳。
    """
    page.title = "cs-ui · 用 Python 构建桌面界面"
    page.padding = 0
    page.window.width = 1360
    page.window.height = 900
    page.window.min_width = 980
    page.window.min_height = 680
    if FONT_FILE.exists():
        page.fonts = {FONT_FAMILY: str(FONT_FILE)}
        theme_state().font_family = FONT_FAMILY


def main(page: ft.Page) -> None:
    configure_page(page)
    page.render(App)


if __name__ == "__main__":
    ft.run(main)
