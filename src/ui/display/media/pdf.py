"""PDF 阅读器 (Pdf)。

桌面端 PDF 查看器的直觉形态：**工具条（文件名 / 打开 / 重载）+ 进度 + 正文区**。
基于 ``flet-webview``（桌面端走 WebView2 / WKWebView，能原生渲染 PDF），
所以翻页、缩放、搜索全由内嵌引擎负责，我们只管外壳与加载反馈。

刻意做成**声明式函数组件**而不是 :class:`ft.Container` 子类：加载进度是高频变化的
运行期状态，用 ``ft.use_state`` 驱动重绘比"命令式控件 + ``self.update()``"更直白，
也不会踩到声明式下控件树 frozen 的坑。

用法::

    Pdf(src="D:/docs/manual.pdf", height=520)
    Pdf(src="https://example.com/a.pdf", title="在线文档")

.. note::
    ``src`` 既接受**本地路径**也接受 **http(s) 地址**。本地路径会转成 ``file://``
    URL（Windows 的盘符、反斜杠、空格、中文都由 :meth:`pathlib.PurePath.as_uri`
    统一处理），所以直接把资源管理器里复制的路径粘进来就能用。
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import PurePath

import flet as ft
import flet_webview as fwv

from ui.core.tokens import FONT_SIZE, RADIUS, elevation, overlay

__all__ = ["Pdf", "pdf_url"]

_REMOTE_PREFIXES = ("http://", "https://", "file://", "data:")


def pdf_url(src: str) -> str:
    """把 ``src`` 归一成 WebView 能吃的 URL。

    - 已是 ``http(s)://`` / ``file://`` / ``data:`` → 原样返回；
    - 其余一律当**本地路径**处理（``PurePath.as_uri`` 负责盘符与转义）；
    - 空串 → 空串（调用方据此显示占位，而不是去加载一个空白页）。
    """
    text = (src or "").strip()
    if not text:
        return ""
    if text.lower().startswith(_REMOTE_PREFIXES):
        return text
    return PurePath(text).as_uri()


def _file_name(src: str) -> str:
    """从 ``src`` 里取出可读的文件名（取不到就返回空串）。"""
    text = (src or "").strip()
    if not text:
        return ""
    if text.lower().startswith(("http://", "https://", "file://")):
        tail = text.replace("\\", "/").rstrip("/").rsplit("/", 1)[-1]
        return tail.split("?", 1)[0].split("#", 1)[0]
    return PurePath(text).name


@ft.component
def Pdf(
    src: str = "",
    *,
    title: str = "",
    height: int | float = 420,
    width: int | float | None = None,
    toolbar: bool = True,
    on_open: Callable[[], None] | None = None,
) -> ft.Control:
    """内嵌 PDF 阅读器。

    Args:
        src: 本地路径或 http(s) 地址；本地路径会归一成 ``file://``。
        title: 工具条上显示的名字；留空则从 ``src`` 里取文件名。
        height: 阅读区高度。
        width: 整体宽度，默认撑满。
        toolbar: 是否显示工具条（文件名 / 打开 / 重载 / 进度）。
        on_open: 「打开」按钮的回调；不传则该按钮不显示。

    加载进度由 ``WebView.on_progress`` 驱动：进度未满时在正文区**上沿**压一条
    2px 细进度条 —— 不占额外高度（占高度会让文档区每次加载完往下跳一格）。
    """
    url = pdf_url(src)
    name = title or _file_name(src)
    progress, set_progress = ft.use_state(0.0)
    failed, set_failed = ft.use_state(False)
    # 换 src 时进度归零，否则会挂着上一份文档的进度条
    ft.use_effect(lambda: set_progress(0.0), [url])

    def _reset(_e: ft.ControlEvent) -> None:
        set_progress(0.0)
        set_failed(False)

    head: list[ft.Control] = []
    if name:
        head.append(
            ft.Container(
                expand=True,
                padding=ft.Padding.symmetric(horizontal=10),
                alignment=ft.Alignment.CENTER_LEFT,
                content=ft.Text(
                    name,
                    size=FONT_SIZE["small"],
                    color=ft.Colors.ON_SURFACE_VARIANT,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
            )
        )
    if on_open is not None:
        head.append(
            ft.Container(
                padding=ft.Padding.symmetric(horizontal=10, vertical=5),
                border_radius=ft.BorderRadius.all(RADIUS["md"]),
                bgcolor=overlay(0.06),
                ink=True,
                on_click=lambda _e: on_open(),
                tooltip="打开本地 PDF",
                content=ft.Row(
                    spacing=4,
                    tight=True,
                    controls=[
                        ft.Icon(ft.Icons.FOLDER_OPEN, size=15,
                                color=ft.Colors.ON_SURFACE_VARIANT),
                        ft.Text("打开", size=FONT_SIZE["small"]),
                    ],
                ),
            )
        )
    if url:
        head.append(
            ft.Container(
                padding=ft.Padding.symmetric(horizontal=8, vertical=5),
                border_radius=ft.BorderRadius.all(RADIUS["md"]),
                bgcolor=overlay(0.06),
                ink=True,
                on_click=_reset,
                tooltip="重新加载",
                content=ft.Icon(ft.Icons.REFRESH, size=15,
                                color=ft.Colors.ON_SURFACE_VARIANT),
            )
        )

    if not url:
        body: ft.Control = ft.Container(
            expand=True,
            alignment=ft.Alignment.CENTER,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=6,
                controls=[
                    ft.Icon(ft.Icons.PICTURE_AS_PDF, size=40,
                             color=ft.Colors.OUTLINE_VARIANT),
                    ft.Text("未选择 PDF", size=FONT_SIZE["small"],
                            color=ft.Colors.ON_SURFACE_VARIANT),
                ],
            ),
        )
    elif failed:
        body = ft.Container(
            expand=True,
            alignment=ft.Alignment.CENTER,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=6,
                controls=[
                    ft.Icon(ft.Icons.ERROR_OUTLINE, size=36,
                            color=ft.Colors.ERROR),
                    ft.Text("文档加载失败", size=FONT_SIZE["body"]),
                    ft.Text(
                        url,
                        size=FONT_SIZE["caption"],
                        color=ft.Colors.ON_SURFACE_VARIANT,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                ],
            ),
        )
    else:
        body = fwv.WebView(
            url=url,
            expand=True,
            on_progress=lambda e: set_progress(float(getattr(e, "data", None) or 0.0)),
            on_web_resource_error=lambda _e: set_failed(True),
        )

    return ft.Container(
        width=width,
        height=height,
        border_radius=ft.BorderRadius.all(RADIUS["lg"]),
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        bgcolor=ft.Colors.SURFACE,
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        shadow=elevation(2),
        content=ft.Column(
            spacing=0,
            tight=True,
            controls=[
                *(
                    [
                        ft.Container(
                            height=36,
                            bgcolor=ft.Colors.SURFACE_CONTAINER,
                            content=ft.Row(
                                spacing=2,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=head,
                            ),
                        ),
                        ft.Stack(
                            expand=True,
                            controls=[
                                body,
                                ft.Container(
                                    height=2,
                                    bgcolor=ft.Colors.PRIMARY,
                                    visible=0.0 < progress < 1.0,
                                ),
                            ],
                        ),
                    ]
                    if toolbar
                    else [body]
                ),
            ],
        ),
    )


@ft.component
def App() -> ft.Control:
    """Pdf 组件运行示例。"""
    return Pdf(src="", title="未选择", height=360)