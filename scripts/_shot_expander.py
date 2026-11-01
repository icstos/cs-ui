"""Expander 视觉验收宿主：把 layout/expander.py 自带的 App 渲染成独立窗口。

    python scripts/_probe_demo.py --app scripts/_shot_expander.py \
        --title "CS UI · Expander" --boot 8 --out output/final_expander.png
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

import flet as ft  # noqa: E402

from ui.layout.expander import App  # noqa: E402

FONT_FILE = ROOT / "src" / "ui" / "data" / "fonts" / "AlibabaPuHuiTi-3-55-Regular.otf"
DARK = os.environ.get("CS_UI_THEME", "light").lower() == "dark"


def main(page: ft.Page) -> None:
    page.title = "CS UI · Expander"
    page.window.width = 900
    page.window.height = 1180
    if FONT_FILE.exists():
        page.fonts = {"AlibabaPuHuiTi": str(FONT_FILE)}
        page.theme = ft.Theme(
            color_scheme_seed="#1F6FEB", font_family="AlibabaPuHuiTi"
        )
        page.dark_theme = ft.Theme(
            color_scheme_seed="#1F6FEB", font_family="AlibabaPuHuiTi"
        )
    page.theme_mode = ft.ThemeMode.DARK if DARK else ft.ThemeMode.LIGHT
    page.render(App)


if __name__ == "__main__":
    ft.run(main)
