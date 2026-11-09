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
from ui.core.responsive import apply_responsive

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
    # 最小宽度跟着响应式断点走：窄于 768 就是 compact（侧栏收进抽屉、目录收起），
    # 站点自己不吃自己的规矩就没法验证框架的窄屏行为。
    page.window.min_width = 360
    page.window.min_height = 520
    if FONT_FILE.exists():
        page.fonts = {FONT_FAMILY: str(FONT_FILE)}
        theme_state().font_family = FONT_FAMILY

    # 响应式引擎要有人喂宽度：读一次当前窗口，之后跟着 on_resize 走，且只在
    # 跨档（compact / medium / expanded）时通知组件重绘 —— 拖动窗口不会变成幻灯片。
    # 外壳里的 ``use_responsive()`` 全部依赖这一句。
    apply_responsive(page)


def main(page: ft.Page) -> None:
    configure_page(page)
    page.render(App)


if __name__ == "__main__":
    ft.run(main)
