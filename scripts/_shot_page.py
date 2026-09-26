"""真机截图用的宿主应用：按 CS_UI_SHOT_PAGE 渲染 examples/demo.py 里的单个页面。

被 ``scripts/_visual_check.py`` 调用（也会被人工用于单页截图）：

    CS_UI_SHOT_PAGE=ChartsPage python scripts/_probe_demo.py \
        --app scripts/_shot_page.py --title "CS UI · ChartsPage" \
        --boot 9 --out output/final_charts.png
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

PAGE = os.environ.get("CS_UI_SHOT_PAGE", "HomePage")


def main(page: ft.Page) -> None:
    page.title = f"CS UI · {PAGE}"
    page.window.width = 1180
    page.window.height = 840
    demo._configure_page(page)
    page.render(lambda: getattr(demo, PAGE)())


if __name__ == "__main__":
    ft.run(main)
