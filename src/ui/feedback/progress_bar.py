"""ProgressBar 进度条。

两种形态，靠 ``progress`` 是否为空区分：

* **确定进度** —— ``progress`` 给 0–1 的小数或 0–100 的整数，条子按比例填满，
  用户知道"还要多久"；
* **不确定** —— ``progress=None``，一段来回滑动的动画，只说明"在做事"，
  不承诺完成时间。

用法::

    ProgressBar(progress=0.62)        # 62%
    ProgressBar(progress=62)          # 也是 62%
    ProgressBar(color=semantic_text("success"))
    ProgressBar()                     # 不确定动画

设计取舍
--------
- **整数一律是百分比，小数一律是比例**：``progress=1`` 是 1%，``1.0`` 才是满格。
  旧实现把整数 1 也当成满格，滑块拖到 1% 时进度条会突然跳到 100%。
- **轨道跟随前景色**：给了 ``color`` 就用同色的 15% 画轨道。写死 ``GREY_700``
  的轨道在深色主题下是一条突出的灰杠。
"""

from __future__ import annotations

import flet as ft

from ui.core.doc import Api, Example, Spec, info, run, tip, warn
from ui.core.tokens import FONT_SIZE, FONT_WEIGHT, SPACE, semantic_text

__all__ = ["ProgressBar"]


def _as_ratio(progress: float | None) -> float | None:
    """把百分比或比例统一成 flet 要的 0–1。

    整数走百分比（``62`` → ``0.62``），浮点走比例（``0.62`` → ``0.62``）；
    两者都夹到合法区间，免得调用方传了 120 直接触发 flet 的校验。
    """
    if progress is None:
        return None
    if isinstance(progress, int) and not isinstance(progress, bool):
        return min(max(progress, 0), 100) / 100
    return min(max(float(progress), 0.0), 1.0)


@ft.control
class ProgressBar(ft.ProgressBar):
    progress: int | float | None = None
    color: str | None = None

    def init(self):
        self.value = _as_ratio(self.progress)
        if self.color is not None:
            # 轨道 = 同一个颜色的 15%。比固定灰更贴主题，也顺带说明了"这条是谁的"
            self.bgcolor = ft.Colors.with_opacity(0.15, self.color)
            # 前景保持原色：再压一层 0.85 透明度会把主色冲淡成另一个颜色


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
def _caption(text: str) -> ft.Control:
    return ft.Text(text, size=FONT_SIZE["small"], color=ft.Colors.ON_SURFACE_VARIANT)


def _label(text: str) -> ft.Control:
    return ft.Text(text, size=FONT_SIZE["body"], color=ft.Colors.ON_SURFACE)


def _percent_label(value: int) -> ft.Control:
    return ft.Text(
        f"{value}%",
        size=FONT_SIZE["body"],
        color=ft.Colors.ON_SURFACE_VARIANT,
        weight=FONT_WEIGHT["medium"],
    )


@ft.component
def _determinate() -> ft.Control:
    """拖滑块，进度与百分比标签一起动。"""
    percent, set_percent = ft.use_state(62)

    def on_change(e: ft.Event[ft.Slider]) -> None:
        raw = getattr(e, "data", None)
        if raw in (None, ""):
            raw = getattr(e.control, "value", 0)
        set_percent(round(float(raw)))

    return ft.Column(
        spacing=SPACE["2"],
        controls=[
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[_label("正在上传 12 个文件"), _percent_label(percent)],
            ),
            ProgressBar(progress=percent),
            ft.Slider(
                value=percent,
                min=0,
                max=100,
                divisions=100,
                label="{value}%",
                on_change=on_change,
            ),
            _caption("整数按百分比解释：0 是空条、100 是满格，1 就是 1%。"),
        ],
    )


@ft.component
def _indeterminate() -> ft.Control:
    """不知道要多久时才用：动画只说「在做事」。"""
    return ft.Column(
        spacing=SPACE["2"],
        controls=[
            _label("正在连接服务器…"),
            ProgressBar(),
            _caption(
                "progress=None：一段来回滑动的动画，不表达进度。"
                "既然不知道还要多久，就别在旁边写百分比。"
            ),
        ],
    )


@ft.component
def _semantic_colors() -> ft.Control:
    """颜色表达状态，高度表达层级：同一条进度条换个色就能读成「成功 / 警告」。"""
    return ft.Column(
        spacing=SPACE["4"],
        controls=[
            _tone("主色 · 默认", 42, None),
            _tone("成功 · 已完成", 100, semantic_text("success")),
            _tone("警告 · 接近配额", 86, semantic_text("warning")),
            _caption(
                "color 只改前景，轨道自动取同色的 15%；"
                "亮色与深色主题下都不会出现一条突兀的灰底。"
            ),
        ],
    )


def _tone(title: str, percent: int, color: str | None) -> ft.Control:
    return ft.Column(
        spacing=SPACE["1"] + 2,
        controls=[
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[_label(title), _percent_label(percent)],
            ),
            ProgressBar(progress=percent, color=color, bar_height=6),
        ],
    )


_DETERMINATE_CODE = """from ui.feedback import ProgressBar

ProgressBar(progress=0.62)     # 62%
ProgressBar(progress=62)       # 同样 62%，整数按百分比

# 跟着业务状态走：data 变，控件就重建
ProgressBar(progress=uploaded / total, bar_height=6)"""

_INDETERMINATE_CODE = """# 不知道还要多久：给 None，条子自己来回滑
ProgressBar()

# 需要配色时传 color；轨道自动取同色的 15%
ProgressBar(color=semantic_text("success"))"""


SPEC = Spec(
    name="ProgressBar",
    summary="一条横向进度：确定进度按比例填满，不确定时来回滑动。",
    definition=(
        "ProgressBar 回答的是「还要多久」。能算出百分比时它是一条按比例填充的横条，"
        "算不出来时退化成来回滑动的动画。判断标准只有一条：进度是不是真的可测 —— "
        "可测就给数字，不可测就别给，一条走到 90% 停住的进度条比转圈更让人焦虑。"
    ),
    anatomy=[
        (
            "填充段",
            "从左侧按 value（0–1）铺开，颜色默认主色，也可用 color 换成语义色。",
        ),
        (
            "轨道",
            "填充段还没走到的部分。给了 color 时自动取同色的 15%，否则跟随主题。",
        ),
        (
            "高度",
            (
                "bar_height 控制条子粗细，默认跟随主题；嵌在卡片里时 4–8px 就够，"
                "再粗会抢标题。"
            ),
        ),
        (
            "不确定动画",
            "progress=None 时的一段往返滑动。它没有终点，只表示任务还在跑。",
        ),
    ],
    when=[
        "上传、下载、导入这类能算出百分比的长任务",
        "步骤明确的流程：3 / 5 步，条子跟着走",
        "批量操作里需要让用户看到「确实在动」",
    ],
    avoid=[
        "几秒内就结束的请求：一闪而过的进度条只是闪烁，用 Loading 转圈",
        "没有真实进度却硬填数字：会走到 99% 卡住，比不确定动画更糟",
        "只需说明「在做事」：用 Loading，圆环比方条更不占横向空间",
    ],
    examples=[
        Example(
            "确定进度",
            _determinate,
            hint="拖滑块：进度与右侧百分比一起变，整数按百分比解释。",
            code=_DETERMINATE_CODE,
        ),
        Example(
            "不确定动画",
            _indeterminate,
            hint="progress=None：只说「在做事」，不承诺完成时间。",
            code=_INDETERMINATE_CODE,
        ),
        Example(
            "语义色与高度",
            _semantic_colors,
            hint="成功 / 警告换个颜色就能读懂状态；bar_height 收细一档。",
        ),
    ],
    api=[
        Api(
            "progress",
            "int | float | None",
            "None",
            "0–1 的比例或 0–100 的百分比；None 为不确定动画",
        ),
        Api("color", "str | None", "None", "填充色；轨道自动取同色的 15%"),
        Api("bar_height", "int | None", "None", "条子粗细，默认跟随主题"),
        Api("border_radius", "int | None", "None", "两端圆角，默认直角"),
        Api("value", "float | None", "None", "派生的 0–1 值；一般通过 progress 传"),
        Api(
            "semantics_label", "str | None", "None", "读屏软件念的名称，如「上传进度」"
        ),
        Api("semantics_value", "str | None", "None", "读屏软件念的进度值，如「62%」"),
    ],
    notes=[
        tip(
            "整数按百分比、小数按比例：progress=1 是 1%，progress=1.0 才是满格。"
            "旧实现把整数 1 也当满格，滑块拖到 1% 时条子会突然跳满。"
        ),
        info(
            "color 只改前景，轨道自动取同色的 15% —— 不再写死 GREY_700，"
            "深色主题下不会出现一条比页面还亮的灰杠。"
        ),
        warn(
            "不确定形态不要配百分比文案：动画本身不表达进度，旁边写「62%」会让人"
            "以为它卡住了。要么给真实数字，要么只写「正在处理」。"
        ),
    ],
    tags=("进度条", "progress", "进度", "加载", "反馈"),
)


if __name__ == "__main__":
    run(SPEC)
