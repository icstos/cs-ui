"""日志容器 (LogContainer) —— 等宽、自动贴底、按级别着色。

日志和普通文本的差别在「一直在长」：用户不会从头读，只盯最新几行和红色那几行。
所以这个组件把三件事做死：

* **等宽**：时间戳、级别、消息是三列，比例字体下 ``WARN`` 与 ``INFO`` 宽度不同，
  列会歪；等宽族（Consolas / Menlo / DejaVu Sans Mono）才对齐；
* **贴底**：``auto_scroll`` 把视图钉在队尾，``auto_scroll_animation=0`` 让追加
  立即生效 —— 默认的 1s 缓动会让日志「追着跑」；
* **级别色**：行内第一个级别词映射到语义色（``semantic_text``），ERROR 红、
  WARN 黄、SUCCESS 绿、INFO 蓝、DEBUG 灰，明暗主题各一套。

颜色不再写 ``ft.Colors.BLACK`` / ``RED``：前者在深色主题下与底色几乎同色，
后者是不随主题变的一档死色。

用法::

    logs = LogContainer(height=200)
    Column([logs.ui(), Button("追加", on_click=lambda e: ...)])
    await logs.add("10:12:01  INFO     接口返回 200")

``add`` / ``set`` 是 async 的：``await`` 之后让出一帧，界面才会一行行刷出来。
"""

from __future__ import annotations

import asyncio
import re
import time
from dataclasses import dataclass, field

import flet as ft

from ui.core.doc import Api, Example, Spec, info, run, tip, warn
from ui.core.i18n import t, use_t
from ui.core.tokens import FONT_SIZE, RADIUS, SPACE, semantic_text

__all__ = ["LogContainer"]

# ---------------------------------------------------------------------------
# 视觉常量
# ---------------------------------------------------------------------------
TEXT = ft.Colors.ON_SURFACE
MUTED = ft.Colors.ON_SURFACE_VARIANT
LINE = ft.Colors.OUTLINE_VARIANT
PANEL = ft.Colors.SURFACE_CONTAINER_LOW

#: 等宽族：三个平台各取一个实际存在的，最后退回通用族。
MONO = "Consolas"
MONO_FALLBACK = ["Menlo", "DejaVu Sans Mono", "Courier New", "monospace"]

#: 级别词 → 语义角色。取**行内第一个**命中，而不是按严重程度排序扫。
#: 按严重程度扫的话「INFO 重试完毕，fail=0」会被 fail 抢成红色，整块日志就红了。
_LEVEL = re.compile(
    r"(?<![A-Za-z])("
    r"ERROR|FATAL|EXCEPTION|FAIL(?:ED|URE)?|"
    r"WARN(?:ING)?|SUCCESS|PASS(?:ED)?|OK|"
    r"INFO|DEBUG|TRACE|NOTICE"
    r")(?![A-Za-z])",
    re.IGNORECASE,
)

_ROLE: dict[str, str] = {
    "error": "danger",
    "fatal": "danger",
    "exception": "danger",
    "fail": "danger",
    "failed": "danger",
    "failure": "danger",
    "warn": "warning",
    "warning": "warning",
    "success": "success",
    "pass": "success",
    "passed": "success",
    "ok": "success",
    "info": "info",
    # 调试信息不该和正常输出抢注意力，降到中性灰
    "debug": "neutral",
    "trace": "neutral",
    "notice": "info",
}


def _color(line: str) -> ft.ColorValue:
    """这一行的文字颜色：有级别词按级别，没有就是正文色。

    在渲染期调用（而不是模块加载时算成常量），主题一换颜色跟着换。
    """
    match = _LEVEL.search(line)
    if match is None:
        return TEXT
    return semantic_text(_ROLE[match.group(1).lower()])


def _log_text(line: str) -> ft.Text:
    return ft.Text(
        line,
        size=FONT_SIZE["small"],
        color=_color(line),
        font_family=MONO,
        font_family_fallback=MONO_FALLBACK,
        style=ft.TextStyle(height=1.6),
    )


@ft.observable
@dataclass
class LogContainer:
    """一块可滚动的日志面板。

    Args:
        logs: 日志行，一条一个字符串；直接 append 也会触发重绘。
        height: 面板固定高度，内容超出纵向滚动（默认 200）。
    """

    logs: list[str] = field(default_factory=list)
    height: int = 200

    async def add(self, log: str | list[str]):
        """追加一条或一批，然后让出一帧给界面重绘。"""
        if isinstance(log, str):
            self.logs.append(log)
        elif isinstance(log, list):
            self.logs.extend(log)
        await asyncio.sleep(0)

    async def set(self, log: str | list[str]):
        """清空后重新写入一批 —— 「重跑任务」用它。"""
        self.logs = []
        await self.add(log)

    def clear(self):
        """清空并立即回到空态。"""
        self.logs = []

    @ft.component
    def ui(self):
        """渲染成控件。放进页面时调它：``Column([logs.ui()])``。"""
        use_t()
        lines = [_log_text(text) for text in self.logs]
        if not lines:
            # 空面板不能是一块空框：深色主题下它和「加载失败」长得一模一样。
            lines = [
                ft.Container(
                    padding=ft.Padding.only(top=SPACE["6"]),
                    alignment=ft.Alignment.TOP_CENTER,
                    content=ft.Text(
                        t("ui.common.empty"),
                        size=FONT_SIZE["small"],
                        color=MUTED,
                    ),
                )
            ]
        return ft.Container(
            height=self.height,
            bgcolor=PANEL,
            border=ft.Border.all(1, LINE),
            border_radius=RADIUS["md"],
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=ft.SelectionArea(
                content=ft.ListView(
                    expand=1,
                    spacing=2,
                    padding=ft.Padding.all(SPACE["2"]),
                    auto_scroll=True,
                    # 默认 1s 缓动：追加得快时视图一直在追。日志要「立刻在底部」。
                    auto_scroll_animation=0,
                    controls=lines,
                )
            ),
        )


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
def _line(stamp: str, level: str, message: str) -> str:
    """时间戳 + 级别 + 消息，级别左对齐到 7 列 —— 等宽字体下才是三列。"""
    return f"{stamp}  {level:<7}  {message}"


def _stamp() -> str:
    return time.strftime("%H:%M:%S")


_BOOT: tuple[str, ...] = tuple(
    _line(stamp, level, message)
    for stamp, level, message in (
        ("10:11:58", "INFO", "加载 config/prod.toml，环境 prod"),
        ("10:11:58", "INFO", "worker 启动：并发 4，队列 orders.sync"),
        ("10:12:01", "DEBUG", "拉取批次 #1（20 条）"),
        ("10:12:02", "INFO", "批次 #1 写入 18 条，跳过 2 条重复"),
        ("10:12:04", "WARN", "订单 SO-88213 缺少收货地址，已暂存"),
        ("10:12:06", "INFO", "批次 #2 写入 20 条"),
        ("10:12:09", "ERROR", "支付回调签名不匹配（order=SO-88240）"),
        ("10:12:09", "INFO", "已加入重试队列，第 1 / 3 次"),
        ("10:12:14", "SUCCESS", "重试成功，耗时 4.8s"),
        ("10:12:15", "INFO", "同步完成：38 成功 / 2 跳过 / 1 重试"),
    )
)

#: 点「追加一行」时轮流追加的内容
_EXTRA: tuple[tuple[str, str], ...] = (
    ("INFO", "轮询到 3 条待同步订单"),
    ("DEBUG", "批次 #3 开始，预取 20 条"),
    ("WARN", "订单 SO-88251 金额为 0，本轮跳过"),
    ("ERROR", "库存服务超时 800ms，放弃本轮"),
    ("SUCCESS", "批次 #3 完成，12 / 12"),
)

_LEVELS: tuple[str, ...] = (
    _line("10:12:01", "DEBUG", "进入批次循环，剩余 18 条"),
    _line("10:12:01", "INFO", "开始同步 orders.sync"),
    _line("10:12:04", "SUCCESS", "批次 #2 完成，20 / 20"),
    _line("10:12:06", "WARN", "限流命中，退避 1.2s"),
    _line("10:12:09", "ERROR", "支付回调签名不匹配（order=SO-88240）"),
    _line("10:12:10", "INFO", "重试窗口剩余 fail=0"),
)


@ft.component
def _stream() -> ft.Control:
    """一屏十行、超出部分已滚到底；点按钮追加，视图跟着贴底。"""
    logs = ft.use_memo(lambda: LogContainer(logs=list(_BOOT), height=180), [])
    cursor, set_cursor = ft.use_state(0)

    async def append(_event: ft.Event[ft.Button]) -> None:
        level, message = _EXTRA[cursor % len(_EXTRA)]
        await logs.add(_line(_stamp(), level, message))
        set_cursor(cursor + 1)

    return ft.Column(
        spacing=SPACE["2"],
        controls=[
            logs.ui(),
            ft.Row(
                spacing=SPACE["3"],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Button("追加一行", on_click=append),
                    ft.Text(
                        f"已追加 {cursor} 行 · 视图自动贴底",
                        size=FONT_SIZE["caption"],
                        color=MUTED,
                    ),
                ],
            ),
        ],
    )


@ft.component
def _colors() -> ft.Control:
    """五个级别的着色；最后一行故意写「fail=0」，它仍是 INFO 的蓝色。"""
    logs = ft.use_memo(lambda: LogContainer(logs=list(_LEVELS), height=170), [])
    return ft.Container(width=620, content=logs.ui())


@ft.component
def _empty() -> ft.Control:
    """空态是一行「暂无数据」；点「开始运行」用 set() 写入整批日志。"""
    logs = ft.use_memo(lambda: LogContainer(height=150), [])
    started, set_started = ft.use_state(False)

    async def start(_event: ft.Event[ft.Button]) -> None:
        set_started(True)
        await logs.set(list(_BOOT))

    return ft.Column(
        spacing=SPACE["2"],
        controls=[
            logs.ui(),
            ft.Row(
                spacing=SPACE["3"],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Button("重跑" if started else "开始运行", on_click=start),
                    ft.Text(
                        "set() 先清空再写入，clear() 只清空",
                        size=FONT_SIZE["caption"],
                        color=MUTED,
                    ),
                ],
            ),
        ],
    )


# ---------------------------------------------------------------------------
# 示例源码（“查看代码”面板）
# ---------------------------------------------------------------------------
_STREAM_CODE = """logs = LogContainer(height=180)


async def append(e):
    await logs.add("10:12:04  WARN     限流命中，退避 1.2s")


Column([
    logs.ui(),                       # 固定高度 + 自动贴底
    Button("追加一行", on_click=append),
])"""

_COLORS_CODE = """# 行内第一个级别词决定颜色，明暗主题各一套语义色
await logs.add("10:12:04  SUCCESS  批次 #2 完成，20 / 20")
await logs.add("10:12:06  WARN     限流命中，退避 1.2s")
await logs.add("10:12:09  ERROR    支付回调签名不匹配")"""

_EMPTY_CODE = """logs = LogContainer(height=150)      # 空态显示「暂无数据」

long_job = ["10:12:01  INFO     开始", "10:12:02  INFO     完成"]
await logs.set(long_job)             # 先清空再写入（重跑任务）

logs.clear()                         # 只清空，回到空态"""


# ---------------------------------------------------------------------------
# 组件说明
# ---------------------------------------------------------------------------
SPEC = Spec(
    name="LogContainer",
    summary="等宽、自动贴底的日志面板：按行内级别词着色，追加即可读。",
    definition=(
        "LogContainer 给「一直在长的一串输出」一块固定大小的窗口。它不做解析、"
        "不过滤、不搜索 —— 文本进来是什么就显示什么，只负责把可读性做对：等宽字让"
        "时间戳与级别成列、自动滚动让视图停在最新一行、级别词映射到语义色让错误自己"
        "跳出来。需要检索与导出时，那不是一块面板能解决的事。"
    ),
    anatomy=[
        (
            "面板",
            (
                "SURFACE_CONTAINER_LOW 底 + OUTLINE_VARIANT 1px 描边，圆角 6；"
                "高度由 height 固定，日志多少都不塌。"
            ),
        ),
        (
            "日志行",
            "等宽字体 12px / 行高 1.6；时间戳、级别、消息三段靠空格对齐成列。",
        ),
        (
            "级别色",
            (
                "ERROR / FAIL 走 danger，WARN 走 warning，SUCCESS 走 success，"
                "INFO 走 info，DEBUG 走 neutral —— 取行内第一个级别词。"
            ),
        ),
        (
            "滚动",
            "ListView + auto_scroll，追加即贴底；用户往上翻时自动跟随暂停，滚回底部再恢复。",
        ),
        (
            "空态",
            "没有日志时居中一行「暂无数据」，空面板不会被当成加载失败。",
        ),
        (
            "选区",
            "外层 SelectionArea：报错行可以整段选中，直接贴进工单。",
        ),
    ],
    when=[
        "同步、构建、爬取这类长任务的实时输出",
        "需要按级别快速扫出错误与警告，而不是逐行读",
        "日志要能选中复制给同事或贴进问题单",
    ],
    avoid=[
        "代码片段、配置：用 Code，语法高亮比等宽更重要",
        "只有几十行、一屏能看完的短输出：直接铺 Text，少一层滚动",
        "需要搜索、按级别过滤、导出文件：那是日志查看器，得自己加工具栏与过滤",
    ],
    examples=[
        Example(
            "追加与贴底",
            _stream,
            hint="固定 180px 高，十行已滚到底；点「追加一行」看视图跟着走。",
            code=_STREAM_CODE,
            height=280,
        ),
        Example(
            "级别着色",
            _colors,
            hint="五档颜色；最后一行「fail=0」仍是 INFO 蓝 —— 按第一个级别词取色。",
            code=_COLORS_CODE,
            height=220,
        ),
        Example(
            "空态与重跑",
            _empty,
            hint="空面板给「暂无数据」；「开始运行」用 set() 写入整批日志。",
            code=_EMPTY_CODE,
            height=250,
        ),
    ],
    api=[
        Api("logs", "list[str]", "[]", "日志行；append / clear 都会触发重绘"),
        Api("height", "int", "200", "面板高度；内容超出纵向滚动"),
        Api(
            "add(log)",
            "async (str | list[str]) -> None",
            "—",
            "追加一条或一批，await 让出一帧",
        ),
        Api(
            "set(log)",
            "async (str | list[str]) -> None",
            "—",
            "先清空再写入一批",
        ),
        Api("clear()", "() -> None", "—", "清空，面板回到空态"),
        Api("ui()", "() -> Control", "—", "渲染成控件，放进页面时调它"),
    ],
    notes=[
        tip(
            "add() / set() 是 async 的：await 里那次 asyncio.sleep(0) 是为了让出一帧。"
            "循环里逐条 await，界面才会一行行刷出来；不 await 会攒到最后一次重绘。"
        ),
        warn(
            "别再写 ft.Colors.BLACK / RED：前者在深色主题下和底色几乎同色，后者不随主题变。"
            "这里用 semantic_text()（danger / warning / success / info / neutral），"
            "明暗各一套且都过了对比度。"
        ),
        info(
            "auto_scroll 默认带 1s 缓动，追加快时视图一直在追；这里设 auto_scroll_animation=0 "
            "直接贴底。用户手动上翻时跟随暂停，滚回底部才恢复。日志为空时给一行「暂无数据」，"
            "空框在深色主题下和加载失败长得一样。"
        ),
    ],
    tags=("日志", "log", "输出", "控制台", "console", "等宽"),
)


if __name__ == "__main__":
    run(SPEC)
