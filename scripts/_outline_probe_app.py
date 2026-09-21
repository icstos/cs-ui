"""outline_input / underline_input 边框颜色的真机验证宿主。

回归背景：``OutlineInputBorder.side`` 只接受**单个** ``BorderSide``，
旧实现把 ``{状态: BorderSide}`` 塞进 ``side``，客户端解析不出颜色后
静默退回 ``BorderSide`` 默认值（黑色）——即「颜色效果无效」。

颜色取刺眼值，便于截图判读。期望：

    A  outline_input(6, RED, GREEN)          常规红边
    B  同上 + disabled=True                   灰边（OUTLINE_VARIANT）
    C  同上 + error="..."                    红边（ERROR）
    D  outline_input(6)（不给色）              主题默认灰边
    E  underline_input(ORANGE, GREEN)         橙色下划线
    F  ui.Input(...)（真实组件）               常规灰边，聚焦变蓝
    G  手写 HOVERED 条目                      悬停前后**零像素差异**（反例，见下）

G 的用途：`ControlState.HOVERED` 在 `FormFieldControl.border` 里**不生效**——渲染不报错，
但悬停前后截图逐像素完全相同。想验证悬停反馈，改看 `hover_color`（F 就是控制组：
悬停时填充变 `#E3F2FD`）。判定用 `ImageChops.difference(a, b).getbbox() is None`。

用法::

    python scripts/_probe_demo.py --app scripts/_outline_probe_app.py \
        --title "CS UI · outline" --boot 5 --out output/_outline/after.png
    # 悬停验证（只移动光标、不点击）
    python scripts/_probe_demo.py --app scripts/_outline_probe_app.py \
        --title "CS UI · outline" --hover 300,180 --boot 5 \
        --out output/_outline/hover.png
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import flet as ft  # noqa: E402
from ui.core.styles import outline_input, underline_input  # noqa: E402
from ui.input.input import Input  # noqa: E402

RED = "#ff0000"
GREEN = "#00a000"
ORANGE = "#ff8c00"

RADIUS = 6
W = 300


def cell(tag: str, field: ft.Control) -> ft.Row:
    return ft.Row(
        controls=[ft.Text(tag, size=14, width=70), field],
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )


@ft.component
def App():
    a = ft.TextField(
        value="A",
        border=outline_input(RADIUS, RED, GREEN),
        width=W,
        height=36,
    )
    b = ft.TextField(
        value="B",
        border=outline_input(RADIUS, RED, GREEN),
        disabled=True,
        width=W,
        height=36,
    )
    c = ft.TextField(
        value="C",
        border=outline_input(RADIUS, RED, GREEN),
        error="格式不正确",
        width=W,
        height=36,
    )
    d = ft.TextField(value="D", border=outline_input(RADIUS), width=W, height=36)
    e = ft.TextField(
        value="E",
        border=underline_input(ORANGE, GREEN),
        width=W,
        height=36,
    )
    f = Input(label="F", label_width=70, width=W, value="真实组件").ui()
    # G —— 显式声明 HOVERED：用于验证该状态对输入边框是否真的生效
    g = ft.TextField(
        value="G",
        border={
            ft.ControlState.DEFAULT: ft.OutlineInputBorder(
                border_radius=ft.BorderRadius.all(RADIUS),
                side=ft.BorderSide(1, RED),
            ),
            ft.ControlState.HOVERED: ft.OutlineInputBorder(
                border_radius=ft.BorderRadius.all(RADIUS),
                side=ft.BorderSide(3, ORANGE),
            ),
        },
        width=W,
        height=36,
    )

    return ft.Container(
        padding=ft.Padding.only(left=30, top=20),
        content=ft.Column(
            controls=[
                ft.Text("outline_input 边框颜色对照", size=15, weight=ft.FontWeight.BOLD),
                cell("A", a),
                cell("B", b),
                cell("C", c),
                cell("D", d),
                cell("E", e),
                f,
                cell("G", g),
            ],
            spacing=14,
        ),
    )


def main(page: ft.Page) -> None:
    page.title = "CS UI · outline"
    page.window.width = 620
    page.window.height = 560
    page.bgcolor = ft.Colors.WHITE
    page.render(App)


if __name__ == "__main__":
    ft.run(main)
