"""文档站截图宿主：临时把窗口标题设成 ASCII，方便探针按标题找窗口。

支持三个环境变量：

``CS_UI_DOCS_ROUTE``
    起始路由，默认 ``/``。
``CS_UI_DOCS_TITLE``
    窗口标题，默认 ``CSUIDOCS``（探针按标题找窗口，必须是 ASCII）。
``CS_UI_DOCS_MODE``
    ``light`` / ``dark``，覆盖起始明暗模式。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import flet as ft

from docs.app import App
from docs.main import configure_page
from ui.core.theme import theme_state

ROUTE = os.environ.get("CS_UI_DOCS_ROUTE", "/")
TITLE = os.environ.get("CS_UI_DOCS_TITLE", "CSUIDOCS")
MODE = os.environ.get("CS_UI_DOCS_MODE", "")


def main(page: ft.Page) -> None:
    configure_page(page)
    page.title = TITLE
    if MODE in ("light", "dark"):
        theme_state().mode = MODE
    page.render(App)
    if ROUTE not in ("", "/"):
        page.navigate(ROUTE)
    page.update()


if __name__ == "__main__":
    ft.run(main)
