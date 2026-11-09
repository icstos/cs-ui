"""Expander 视觉验收宿主：把 ``ui.layout.expander`` 渲染成独立窗口。

    python scripts/_probe_demo.py --app scripts/_shot_expander.py \
        --title "CS UI · Expander" --boot 8 --out output/final_expander.png

配色核对也用它：``CS_UI_THEME=dark`` 再截一张，明暗两版都过一遍眼。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

import flet as ft  # noqa: E402

from ui.core.theme import ThemeState, apply_theme  # noqa: E402
from ui.layout.expander import Expander  # noqa: E402

FONT_FILE = ROOT / "src" / "ui" / "data" / "fonts" / "AlibabaPuHuiTi-3-55-Regular.otf"
DARK = os.environ.get("CS_UI_THEME", "light").lower() == "dark"


def _body(*lines: str) -> list[ft.Control]:
    return [
        ft.Text(line, size=14, color=ft.Colors.ON_SURFACE_VARIANT) for line in lines
    ]


def _page() -> ft.Control:
    """四种形态 + 四档强调色：一张截图能核对描边、箭头、淡底与文字层次。"""
    return ft.Container(
        padding=24,
        expand=True,
        content=ft.Column(
            spacing=12,
            tight=True,
            controls=[
                ft.Text("Expander", size=20, weight=ft.FontWeight.W_600),
                ft.Text(
                    "四种形态 × 四档强调色，用来核对描边、箭头、淡底与文字层次。",
                    size=14,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
                Expander(
                    title="高级设置",
                    subtitle="仅在需要时调整，改动立即生效",
                    leading=ft.Icons.TUNE,
                    expanded=True,
                    controls=_body(
                        "请求超时 30 秒，失败自动重试 2 次。",
                        "展开态由 Flutter 持有，收起再展开不会重建内容。",
                    ),
                ),
                Expander(
                    title="filled 形态",
                    subtitle="底色比表面深一档",
                    leading=ft.Icons.LAYERS,
                    variant="filled",
                    controls=_body("用于分区里再分区。"),
                ),
                Expander(
                    title="plain 形态",
                    subtitle="只有分隔线，没有外框",
                    leading=ft.Icons.HORIZONTAL_RULE,
                    variant="plain",
                    controls=_body("密集列表用。"),
                ),
                Expander(
                    title="禁用态",
                    subtitle="expandable=False：箭头消失、文字置灰",
                    leading=ft.Icons.LOCK,
                    expandable=False,
                    controls=_body("点不动。"),
                ),
                ft.Row(
                    spacing=12,
                    wrap=True,
                    controls=[
                        Expander(
                            title=role,
                            leading=ft.Icons.CIRCLE,
                            accent=role,
                            variant="filled",
                            width=200,
                            controls=_body(f"accent={role}"),
                        )
                        for role in ("primary", "success", "warning", "danger")
                    ],
                ),
            ],
        ),
    )


def main(page: ft.Page) -> None:
    page.title = "CS UI · Expander"
    page.window.width = 900
    page.window.height = 1180
    # 走真实主题装配，别自己拼 ft.Theme —— 否则截图验的不是产品里的那套颜色。
    # 用独立的 ThemeState，不碰全局状态与本地配置。
    font = None
    if FONT_FILE.exists():
        page.fonts = {"AlibabaPuHuiTi": str(FONT_FILE)}
        font = "AlibabaPuHuiTi"
    apply_theme(page, ThemeState(mode="dark" if DARK else "light", font_family=font))
    page.add(_page())


if __name__ == "__main__":
    ft.run(main)
