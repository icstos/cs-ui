"""文档站截图宿主：临时把窗口标题设成 ASCII，方便探针按标题找窗口。

支持三个环境变量：

``CS_UI_DOCS_ROUTE``
    起始路由，默认 ``/``。
``CS_UI_DOCS_TITLE``
    窗口标题，默认 ``CSUIDOCS``（探针按标题找窗口，必须是 ASCII）。
``CS_UI_DOCS_MODE``
    ``light`` / ``dark``，覆盖起始明暗模式。
``CS_UI_DOCS_WIDTH`` / ``CS_UI_DOCS_HEIGHT``
    覆盖起始窗口尺寸（用于窄屏验收：``CS_UI_DOCS_WIDTH=640``）。
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

ROUTE = os.environ.get("CS_UI_DOCS_ROUTE", "/").strip() or "/"
if ":" in ROUTE:
    # Git Bash 会把 ``/components/x`` 当 Unix 绝对路径改写成 ``C:/Program Files/...``，
    # 这里认得出已知前缀就还原，省得每次都要记得加 ``MSYS_NO_PATHCONV=1``。
    hits = [ROUTE.find(prefix) for prefix in ("/components/", "/docs/", "/about")]
    hits = [index for index in hits if index >= 0]
    ROUTE = ROUTE[min(hits) :] if hits else "/"
TITLE = os.environ.get("CS_UI_DOCS_TITLE", "CSUIDOCS")
MODE = os.environ.get("CS_UI_DOCS_MODE", "")
WIDTH = int(os.environ.get("CS_UI_DOCS_WIDTH", "0") or 0)
HEIGHT = int(os.environ.get("CS_UI_DOCS_HEIGHT", "0") or 0)


def main(page: ft.Page) -> None:
    configure_page(page)
    page.title = TITLE
    if WIDTH:
        page.window.width = WIDTH
    if HEIGHT:
        page.window.height = HEIGHT
    if MODE in ("light", "dark"):
        theme_state().mode = MODE
    # 深链要在**渲染前**写好：``page.navigate()`` 只是往事件循环里排一个任务，
    # 客户端还没就绪时那次跳转会丢，首帧就停在 "/"。
    if ROUTE not in ("", "/"):
        page.route = ROUTE
    page.render(App)
    page.update()

    if os.environ.get("CS_UI_DOCS_DEBUG"):
        import asyncio as _asyncio

        from ui.core.responsive import viewport as _vp

        async def _diag() -> None:
            # 首帧之后 page.width 才是真值（启动尺寸不触发 on_resize），所以隔几拍各打一次，
            # 用来确认"响应式引擎已经被喂到宽度"。
            for delay in (0.2, 0.6, 1.2, 2.4):
                await _asyncio.sleep(delay)
                v = _vp()
                print(
                    f"DIAG page.width={page.width} vp={v.width} cls={v.size_class}",
                    flush=True,
                )

        page.run_task(_diag)


if __name__ == "__main__":
    ft.run(main)
