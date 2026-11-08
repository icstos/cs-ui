"""PDF 阅读器 (Pdf)。

桌面端 PDF 查看器的直觉形态：**工具条（文件名 / 打开 / 重载）+ 进度 + 正文区**。
正文交给 ``flet-webview`` 里的原生 PDF 引擎（翻页、缩放、搜索都由它负责），
组件只做外壳与加载反馈。

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

.. warning::
    PDF 是 WebView 渲染的，而 flet-webview 目前只在 macOS / iOS / Android / Web
    上有实现。Windows / Linux 桌面端这个控件会是一块空白 —— 工具条、空态照常，
    正文没有内容，要换平台或换渲染方案。
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import PurePath

import flet as ft
import flet_webview as fwv

from ui.core.doc import Api, Example, Spec, info, run, tip, warn
from ui.core.empty import empty_block
from ui.core.i18n import t, use_t
from ui.core.tokens import FONT_SIZE, ICON_SIZE, RADIUS, SPACE, elevation, overlay

__all__ = ["SPEC", "Pdf", "pdf_url"]

_REMOTE_PREFIXES = ("http://", "https://", "file://", "data:")

#: 工具条高 36：放得下一个小图标与一行 12px 字，又不至于把阅读区顶掉一块
TOOLBAR_H = 36
#: 加载进度条厚度。压在正文上沿而不是单独占行 —— 占一行会让文档加载完整体下移一格
PROGRESS_H = 2


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


def _progress_fraction(data: object) -> float:
    """把 ``on_progress`` 的 ``data`` 折成 0~1。

    内嵌引擎回报的是**整数百分比**（0~100）。直接拿它当 0~1 的比例用，
    ``0 < p < 1`` 就只对 0 成立，那条进度条一辈子不出现。个别平台给的是
    0~1，所以只有大于 1 才除以 100 —— 两种量纲都落到正确区间。
    """
    raw = min(100.0, max(0.0, float(data or 0)))
    return raw / 100 if raw > 1 else raw


@ft.component
def Pdf(
    src: str = "",
    *,
    title: str = "",
    height: float = 420,
    width: float | None = None,
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
    use_t()  # 订阅语言：工具条按钮与空态 / 失败态文案都要跟着切
    url = pdf_url(src)
    name = title or _file_name(src)
    progress, set_progress = ft.use_state(0.0)
    failed, set_failed = ft.use_state(False)
    #: 重载计数。它进 WebView 的 key —— key 一变，协调器就换一个新实例，
    #: 这才是"重新加载"；只把进度归零并不会让引擎重新拉一次文档。
    reloads, set_reloads = ft.use_state(0)

    # 换 src 时进度与失败标记归零，否则会挂着上一份文档的状态
    def _reset_on_src() -> None:
        set_progress(0.0)
        set_failed(False)

    ft.use_effect(_reset_on_src, [url])

    def _reload(_e: ft.ControlEvent) -> None:
        set_progress(0.0)
        set_failed(False)
        set_reloads(reloads + 1)

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
                padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                border_radius=ft.BorderRadius.all(RADIUS["md"]),
                bgcolor=overlay(0.06),
                ink=True,
                on_click=lambda _e: on_open(),
                tooltip=t("ui.pdf.open_tooltip"),
                content=ft.Row(
                    spacing=4,
                    tight=True,
                    controls=[
                        ft.Icon(
                            ft.Icons.FOLDER_OPEN,
                            size=ICON_SIZE["md"],
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        ft.Text(t("ui.pdf.open"), size=FONT_SIZE["small"]),
                    ],
                ),
            )
        )
    if url:
        head.append(
            ft.Container(
                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                border_radius=ft.BorderRadius.all(RADIUS["md"]),
                bgcolor=overlay(0.06),
                ink=True,
                on_click=_reload,
                tooltip=t("ui.pdf.reload"),
                content=ft.Icon(
                    ft.Icons.REFRESH,
                    size=ICON_SIZE["md"],
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
            )
        )

    if not url:
        # 与全框架的整块空态同一套：图标垫圆底 + 一行说明。
        body: ft.Control = ft.Container(
            expand=True,
            alignment=ft.Alignment.CENTER,
            content=empty_block(t("ui.pdf.empty"), icon=ft.Icons.PICTURE_AS_PDF, height=None),
        )
    elif failed:
        body = ft.Container(
            expand=True,
            alignment=ft.Alignment.CENTER,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=6,
                controls=[
                    ft.Icon(ft.Icons.ERROR_OUTLINE, size=36, color=ft.Colors.ERROR),
                    ft.Text(t("ui.pdf.failed"), size=FONT_SIZE["body"]),
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
            key=f"{url}#{reloads}",
            url=url,
            expand=True,
            on_progress=lambda e: set_progress(_progress_fraction(e.data)),
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
                            height=TOOLBAR_H,
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
                                    height=PROGRESS_H,
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


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
@ft.component
def _empty() -> ft.Control:
    return Pdf(src="", title="未选择", height=300)


@ft.component
def _with_open() -> ft.Control:
    """传了 on_open 才出现「打开」；重载按钮则要等有 url。"""
    hits, set_hits = ft.use_state(0)
    return ft.Column(
        spacing=6,
        controls=[
            Pdf(
                src="",
                title="合同 A-2026-031.pdf",
                height=220,
                on_open=lambda: set_hits(hits + 1),
            ),
            ft.Text(
                f"on_open 已触发 {hits} 次 —— 真实用法里在这里弹文件选择器，"
                "组件不替你选文件，也不替你下载。",
                size=FONT_SIZE["caption"],
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
        ],
    )


@ft.component
def _urls() -> ft.Control:
    """src 的三种写法：本地路径会被转义成 file:// URL。"""
    samples = [
        r"D:/docs/合同 2026.pdf",
        "https://example.com/report.pdf?v=2",
        "",
    ]
    rows: list[ft.Control] = []
    for sample in samples:
        rows.append(
            ft.Column(
                spacing=2,
                controls=[
                    ft.Text(
                        sample or "（空串）",
                        size=FONT_SIZE["small"],
                        style=ft.TextStyle(letter_spacing=-0.1),
                    ),
                    ft.Row(
                        spacing=6,
                        controls=[
                            ft.Icon(
                                ft.Icons.SUBDIRECTORY_ARROW_RIGHT,
                                size=ICON_SIZE["sm"],
                                color=ft.Colors.OUTLINE,
                            ),
                            ft.Text(
                                pdf_url(sample) or "（空态）",
                                size=FONT_SIZE["caption"],
                                color=ft.Colors.ON_SURFACE_VARIANT,
                                selectable=True,
                                max_lines=2,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                        ],
                    ),
                ],
            )
        )

    return ft.Column(
        spacing=SPACE["3"],
        controls=[
            ft.Text(
                "pdf_url(src) 的三种结果：空格与中文都会被转义，粘路径即可。",
                size=FONT_SIZE["small"],
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
            *rows,
        ],
    )


_MAIN_CODE = """from ui.display.media.pdf import Pdf

Pdf(
    src=r"D:/docs/manual.pdf",   # 本地路径或 https 地址
    title="使用手册",             # 留空则从 src 里取文件名
    height=520,
)

# 需要「打开…」按钮就传回调，组件不内置文件选择器：
Pdf(src="", title="未选择", on_open=pick_file)"""

_TOOLBAR_CODE = """Pdf(src="", title="合同 A-2026-031.pdf", on_open=pick_file)
Pdf(src="", toolbar=False)   # 纯正文区，文件名/按钮/进度一起消失"""

SPEC = Spec(
    name="Pdf",
    summary="把 PDF 嵌进页面：工具条、加载进度、空态与失败态都配好了。",
    definition=(
        "Pdf 是一个内嵌阅读器：正文交给 WebView 里的原生 PDF 引擎，翻页、缩放、搜索"
        "都不必自己实现；组件只负责外壳 —— 36px 工具条（文件名 / 打开 / 重载）、一条"
        "2px 的加载进度，以及没给 src 或加载失败时的两种占位。src 既收本地路径也收 "
        "http(s) 地址，本地路径会被归一成 file:// URL。"
    ),
    anatomy=[
        (
            "工具条",
            "36px 高、SURFACE_CONTAINER 底。左边文件名，右边「打开」「重载」，都是次要文字色。",
        ),
        (
            "文件名",
            "取 title，留空则从 src 里取最后一段（去掉 query 与锚点）；单行省略，不换行挤高工具条。",
        ),
        (
            "打开",
            "只有传了 on_open 才出现。组件不内置文件选择器 —— 选什么文件是业务的事。",
        ),
        (
            "重载",
            "只在有 url 时出现。它换掉 WebView 的 key 让引擎重新拉文档，而不只是把进度归零。",
        ),
        (
            "加载进度",
            "2px 主色细条压在正文上沿，不占高度：占一行会让文档在加载完的瞬间整体下移一格。",
        ),
        (
            "正文区",
            "WebView 铺满剩余空间；翻页、缩放、文字选择、搜索全由内嵌引擎提供。",
        ),
    ],
    when=[
        "合同、发票、手册这类文档要在页面里直接翻阅，而不是先下载再打开",
        "文档由后端给 URL，页码与缩放交给内嵌引擎，自己不想实现分页渲染",
        "桌面工具里做「预览 + 另存为」：用 on_open 接自己的文件选择与保存逻辑",
    ],
    avoid=[
        "要抽取文字或表格做检索、统计：WebView 只负责画，解析得用专门的库",
        "只是给一个下载链接：Link 或 Button 更直接，不必占一块 420px 高的区域",
        "Windows / Linux 桌面端：flet-webview 没有这两个平台的实现，正文会空白",
    ],
    examples=[
        Example(
            "空态",
            _empty,
            hint="没给 src 就是「未选择 PDF」；有 url 时这条位置换成 WebView，右上角多一个重载。",
            code=_MAIN_CODE,
        ),
        Example(
            "工具条组合",
            _with_open,
            hint="on_open 决定「打开」在不在；没有 url 就没有「重载」。点一下按钮看回调。",
            code=_TOOLBAR_CODE,
        ),
        Example(
            "src 的三种写法",
            _urls,
            hint="本地路径统一转 file://：盘符、空格、中文都替你转义，全平台一致。",
        ),
    ],
    api=[
        Api("src", "str", "''", "本地路径或 http(s) 地址；空串显示空态"),
        Api("title", "str", "''", "工具条上的名字；留空从 src 取文件名"),
        Api("height", "float", "420", "阅读区总高度（含工具条）"),
        Api("width", "float | None", "None", "整体宽度，留空撑满父级"),
        Api("toolbar", "bool", "True", "关掉后文件名、按钮、进度条一起消失"),
        Api(
            "on_open",
            "Callable[[], None] | None",
            "None",
            "「打开」按钮回调；不传则不显示该按钮",
        ),
        Api(
            "pdf_url(src)",
            "str",
            "—",
            "模块函数：本地路径 → file:// URL，远程地址原样返回",
        ),
    ],
    notes=[
        warn(
            "PDF 由 WebView 渲染，而 flet-webview 目前只支持 macOS / iOS / Android / Web。"
            "Windows / Linux 桌面上工具条与空态正常，正文是空白 —— 这不是分支问题，换平台"
            "或换渲染方案才能解决。"
        ),
        tip(
            "「重载」换的是 WebView 的 key，让协调器换一个新实例；只把进度归零不会让引擎"
            "重新拉一次文档，用户看到的就是「点了没反应」。"
        ),
        info(
            "on_progress 的 data 是整数百分比（0~100），组件内部统一折成 0~1 再用；"
            "自己接这个事件时别把 0~100 直接塞给 0~1 的进度条，那样它永远不显示。"
        ),
    ],
    tags=("PDF", "文档", "阅读器", "预览", "document"),
)


if __name__ == "__main__":
    run(SPEC)
