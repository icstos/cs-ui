"""真机截图用的宿主应用：按 CS_UI_SHOT_PAGE 渲染 examples/demo.py 里的单个页面。

被 ``scripts/_visual_check.py`` 调用（也会被人工用于单页截图）：

    CS_UI_SHOT_PAGE=ChartsPage python scripts/_probe_demo.py \
        --app scripts/_shot_page.py --title "CS UI · ChartsPage" \
        --boot 9 --out output/final_charts.png

多语言截图：再给一个 ``CS_UI_SHOT_LOCALE``（``zh-CN`` / ``zh-TW`` / ``en-US``）::

    CS_UI_SHOT_PAGE=FormPage CS_UI_SHOT_LOCALE=en-US python scripts/_probe_demo.py ...
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

import flet as ft  # noqa: E402
import examples.demo as demo  # noqa: E402
from ui.core.i18n import set_locale  # noqa: E402

PAGE = os.environ.get("CS_UI_SHOT_PAGE", "HomePage")
LOCALE = os.environ.get("CS_UI_SHOT_LOCALE", "")
#: 探针按窗口标题找窗口，标题里有中文标点时命令行编码容易失真，截图时用 ASCII 标题更稳
TITLE = os.environ.get("CS_UI_SHOT_TITLE") or f"CS UI · {PAGE}"


def main(page: ft.Page) -> None:
    page.title = TITLE
    page.window.width = 1180
    page.window.height = 840
    if LOCALE:
        set_locale(LOCALE, persist=False)
    demo._configure_page(page)
    page.render(lambda: getattr(demo, PAGE)())


if __name__ == "__main__":
    ft.run(main)
