"""响应式视觉验收宿主：同一份页面，在三个宽度下各截一张。

窗口宽度由环境变量给，方便一次跑三档：

    for w in 1400 900 640; do
        CS_UI_PROBE_WIDTH=$w python scripts/_probe_demo.py \
            --app scripts/_shot_responsive.py --title "RSPROBE" --boot 8 \
            --out output/_rsp_$w.png
    done

页面里刻意把三个会翻车的地方摆在一起：

* 页头（标题 + 两个操作）—— 窄了会不会把按钮挤掉；
* 六张卡片（Grid）—— 列数会不会跟着宽度变；
* 一张宽表（Table）—— 窄了会不会横滚而不是撑破外框。
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

import flet as ft  # noqa: E402

from ui.core.responsive import apply_responsive, viewport  # noqa: E402
from ui.core.theme import ThemeState, apply_theme  # noqa: E402
from ui.core.tokens import FONT_SIZE, FONT_WEIGHT, RADIUS, SPACE, overlay  # noqa: E402
from ui.display.descriptions import Descriptions, DescriptionsItem  # noqa: E402
from ui.layout.grid import Grid  # noqa: E402
from ui.layout.page import PageLayout  # noqa: E402
from ui.layout.table import Table  # noqa: E402

FONT_FILE = ROOT / "src" / "ui" / "data" / "fonts" / "AlibabaPuHuiTi-3-55-Regular.otf"
WIDTH = int(os.environ.get("CS_UI_PROBE_WIDTH", "1400"))
HEIGHT = int(os.environ.get("CS_UI_PROBE_HEIGHT", "900"))
DARK = os.environ.get("CS_UI_THEME", "light").lower() == "dark"

_DESC: ft.Control | None = None  # 诊断用的 Descriptions 引用


def _card(i: int) -> ft.Control:
    return ft.Container(
        height=92,
        padding=SPACE["4"],
        border_radius=RADIUS["lg"],
        bgcolor=ft.Colors.SURFACE,
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        content=ft.Column(
            spacing=2,
            controls=[
                ft.Text(f"指标 {i}", size=FONT_SIZE["small"], color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Text(
                    f"{i * 137}",
                    size=FONT_SIZE["headline"],
                    weight=FONT_WEIGHT["bold"],
                ),
            ],
        ),
    )


def _table() -> ft.Control:
    """一张列数偏多的表：窄窗口下它必须横滚，而不是撑破卡片。"""
    return ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text(name))
            for name in ("订单号", "客户", "金额", "状态", "下单时间", "负责人", "备注")
        ],
        rows=[
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(f"SO-2026-{i:04d}")),
                    ft.DataCell(ft.Text(f"客户 {i}")),
                    ft.DataCell(ft.Text(f"¥{i * 1370:,}")),
                    ft.DataCell(ft.Text("已发货")),
                    ft.DataCell(ft.Text("2026-11-09 10:24")),
                    ft.DataCell(ft.Text("张三")),
                    ft.DataCell(ft.Text("—")),
                ]
            )
            for i in range(1, 8)
        ],
    )


def _page() -> ft.Control:
    global _DESC
    _DESC = Descriptions(
        title="订单概览",
        column={"compact": 1, "medium": 2, "expanded": 3},
        items=[
            DescriptionsItem(label="订单号", value="SO-2026-0001"),
            DescriptionsItem(label="客户", value="客户 1"),
            DescriptionsItem(label="金额", value="¥1,370.00"),
            DescriptionsItem(label="状态", value="已发货"),
            DescriptionsItem(label="下单时间", value="2026-11-09 10:24"),
            DescriptionsItem(label="负责人", value="张三"),
        ],
    )
    return PageLayout(
        title="响应式验收",
        subtitle="同一份代码，三个宽度",
        max_content_width="content",
        actions=[
            ft.Button("导出", icon=ft.Icons.DOWNLOAD),
            ft.Button("新建", icon=ft.Icons.ADD),
        ],
        controls=[
            Grid(min_col_width=220, max_cols=4, controls=[_card(i) for i in range(1, 7)]),
            _DESC,
            ft.Divider(),
            ft.Container(
                bgcolor=overlay(0.03),
                border_radius=RADIUS["lg"],
                padding=SPACE["2"],
                content=ft.Row(scroll=ft.ScrollMode.AUTO, controls=[_table()]),
            ),
        ],
    )


def main(page: ft.Page) -> None:
    page.title = "RSPROBE"
    page.window.width = WIDTH
    page.window.height = HEIGHT
    font = None
    if FONT_FILE.exists():
        page.fonts = {"AlibabaPuHuiTi": str(FONT_FILE)}
        font = "AlibabaPuHuiTi"
    apply_theme(page, ThemeState(mode="dark" if DARK else "light", font_family=font))
    apply_responsive(page)
    layout: ft.Control | None = None

    # 等一拍再**建**再挂：窗口尺寸是"异步落地"的，main() 里读到的 page.width 还是
    # 启动时那个值。等 apply_responsive 收到 resize 之后再构造，viewport() 才是真的
    # —— 这也是应用里"页面依赖启动宽度"时的正确写法（建在 try 之前也没用，
    # 因为控件的 init() 在构造时就跑了）。
    async def _mount() -> None:
        nonlocal layout
        await asyncio.sleep(0.8)
        layout = _page()
        page.add(layout)
        print(
            f"probe width={WIDTH} -> viewport={viewport().width}"
            f" class={viewport().size_class}",
            flush=True,
        )

    page.run_task(_mount)

    if os.environ.get("CS_UI_PROBE_DEBUG"):
        # 首帧之后再对账一次：page.width / viewport / PageLayout 自己量到的宽度与档位。
        # 用来区分"事件没来"和"事件来了但没上屏"。
        async def _diag() -> None:
            await asyncio.sleep(2.5)
            if layout is None:
                print("DIAG not mounted yet", flush=True)
                return
            inner = layout.content.controls[0] if layout._centered else None
            col = layout._column
            head = col.controls[0] if col and col.controls else None
            print(
                f"DIAG page.width={page.width} vp={viewport().width}"
                f" vp_cls={viewport().size_class} self_w={layout._width}"
                f" cls={layout._cls} hdr={type(head).__name__}"
                f" padL={getattr(layout.padding, 'left', layout.padding)}"
                f" inner={getattr(inner, 'width', None)}"
                f" desc_col={getattr(_DESC, 'column', None)}",
                flush=True,
            )

        page.run_task(_diag)


if __name__ == "__main__":
    ft.run(main)
