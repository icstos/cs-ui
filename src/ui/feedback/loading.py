"""Loading 加载态。

一个按档位缩放的转圈。它只负责"这件事还没完"，不表达进度 —— 能算出百分比时
请用 :class:`~ui.feedback.progress_bar.ProgressBar`，让用户知道还要多久。

三档尺寸，对应三种用法：

* ``small``（20）—— 行内，跟在文字左边，如「正在保存…」；
* ``normal``（32）—— 区块中央，一块内容整体还没到位；
* ``large``（48）—— 整页或整块空状态，页面上只有这一件事在等。

用法::

    Row([Loading("small"), Text("正在保存…")])

    Container(
        height=180,
        alignment=ft.Alignment.CENTER,
        content=Column([Loading(), Text("正在加载组件清单…")]),
    )

设计取舍
--------
- **尺寸走档位而不是随手传像素**：行内 20、区块 32、整页 48 是三档稳定的节奏，
  同一屏里混用 24 / 28 / 36 只会显得没对齐。
- **线宽跟着尺寸走**（直径的 1/10，最低 2px）：20px 的圈用 4px 线会糊成一坨。
- **宽高只在没显式传时才套档位**：``Loading(width=16)`` 不会被悄悄改回 32。
"""

from __future__ import annotations

import flet as ft

from ui.core.doc import Api, Example, Spec, info, run, tip, warn
from ui.core.tokens import FONT_SIZE, RADIUS, SPACE, overlay

__all__ = ["Loading"]

#: 档位 → 直径。行内 / 区块 / 整页，三档就够，中间值反而难对齐
_SIZE_MAP: dict[str, int] = {"small": 20, "normal": 32, "large": 48}
_DEFAULT_SIZE = _SIZE_MAP["normal"]


@ft.control
class Loading(ft.ProgressRing):
    size_name: str = "normal"

    def init(self):
        size = _SIZE_MAP.get(str(self.size_name).lower(), _DEFAULT_SIZE)

        # 只在调用方没显式给宽高时套档位：Loading(width=16) 应该被尊重
        if self.width is None:
            self.width = size
        if self.height is None:
            self.height = size

        if self.stroke_width is None:
            diameter = float(self.width or self.height or size)
            self.stroke_width = max(2.0, round(diameter / 10, 1))


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
def _caption(text: str) -> ft.Control:
    return ft.Text(text, size=FONT_SIZE["small"], color=ft.Colors.ON_SURFACE_VARIANT)


def _muted(text: str) -> ft.Control:
    return ft.Text(text, size=FONT_SIZE["body"], color=ft.Colors.ON_SURFACE_VARIANT)


def _bone(width: int | None = None, height: int = 10) -> ft.Control:
    """骨架块：一层 on-surface 的 8%，形状照着真实内容画。"""
    return ft.Container(
        width=width,
        height=height,
        border_radius=RADIUS["full"],
        bgcolor=overlay(0.08),
        expand=width is None,
    )


@ft.component
def _inline() -> ft.Control:
    """行内：转圈贴在文字左边，用 small —— 默认档位会把行高撑开。"""
    return ft.Column(
        spacing=SPACE["4"],
        controls=[
            ft.Row(
                spacing=SPACE["2"],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[Loading("small"), _muted("正在保存 3 项修改…")],
            ),
            ft.Row(
                spacing=SPACE["3"],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    Loading("small"),
                    Loading(),
                    Loading("large"),
                    _caption("small 20 · normal 32 · large 48"),
                ],
            ),
            _caption(
                "一行文字旁边的转圈用 small：20px 与 14px 正文的行高接近，"
                "不会把这一行顶高。"
            ),
        ],
    )


@ft.component
def _block() -> ft.Control:
    """区块：一块内容整体没到位时，转圈放在它正中，配一句在等什么。"""
    return ft.Column(
        spacing=SPACE["3"],
        controls=[
            ft.Container(
                height=168,
                border_radius=RADIUS["lg"],
                border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                alignment=ft.Alignment.CENTER,
                content=ft.Column(
                    spacing=SPACE["3"],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[Loading(), _muted("正在加载组件清单…")],
                ),
            ),
            _caption(
                "占位区的高度按真实内容预估：加载完成后布局不跳，"
                "转圈换成列表时也不会把下面的内容顶走。"
            ),
        ],
    )


@ft.component
def _skeleton() -> ft.Control:
    """骨架屏：用占位块画出内容的形状，比一颗转圈更能说明「在等什么」。"""
    return ft.Column(
        spacing=SPACE["3"],
        controls=[
            ft.Row(
                spacing=SPACE["3"],
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.Container(
                        width=40,
                        height=40,
                        border_radius=RADIUS["full"],
                        bgcolor=overlay(0.08),
                    ),
                    ft.Column(
                        expand=True,
                        spacing=SPACE["2"],
                        controls=[_bone(160), _bone(), _bone(220)],
                    ),
                ],
            ),
            ft.Column(spacing=SPACE["2"], controls=[_bone(), _bone(320)]),
            _caption(
                "骨架块用 on-surface 的 8%：形状照着真实内容画，"
                "行数与宽度都对得上，换上去时几乎没有跳动。"
            ),
        ],
    )


_INLINE_CODE = """from ui.feedback import Loading

# 行内：跟在一句话左边
Row([Loading("small"), Text("正在保存…")])

# 区块中央：一块内容整体没到位
Container(
    height=180,
    alignment=ft.Alignment.CENTER,
    content=Column([Loading(), Text("正在加载组件清单…")]),
)"""

_SKELETON_CODE = """# 骨架屏不是内置能力：用占位块照着内容形状画
def bone(width: int | None = None) -> Control:
    return Container(
        width=width, height=10, border_radius=999,
        bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.ON_SURFACE),
        expand=width is None,
    )

Column(spacing=8, controls=[bone(160), bone(), bone(220)])"""


SPEC = Spec(
    name="Loading",
    summary="按档位缩放的转圈：只说明「还没完」，不表达进度。",
    definition=(
        "Loading 是加载态的兜底：当进度不可测、又不能让界面看起来没反应时，"
        "用一颗转圈占住位置。它按 20 / 32 / 48 三档缩放，分别对应行内、区块与整页。"
        "能算出百分比时不要用它 —— 一颗不动的圈会让人怀疑是真的在跑，还是已经卡住。"
    ),
    anatomy=[
        (
            "圆环",
            (
                "Material 的不确定进度圈，默认主色。直径由 size_name 决定，"
                "线宽取直径的 1/10（最低 2px），小圈才不会糊成一坨。"
            ),
        ),
        (
            "档位",
            (
                "small 20 / normal 32 / large 48。行内配文字用 20，区块中央用 32，"
                "整页空状态才用 48。"
            ),
        ),
        (
            "说明文字",
            (
                "圈本身不说明在等什么，必须配一句「正在加载组件清单」。"
                "只有转圈的区域，用户读到的信息量为零。"
            ),
        ),
        (
            "占位区",
            "区块加载时给容器一个按真实内容预估的高度；加载完换成内容时布局不跳。",
        ),
    ],
    when=[
        "请求只有几秒，进度不可测，也不需要给百分比",
        "提交按钮正在处理：小圈替换按钮文字旁边，禁用重复点击",
        "一块区域整体还没到位，先用转圈占住它的位置",
    ],
    avoid=[
        "能算出百分比：用 ProgressBar，用户需要知道还要多久",
        "首屏大区块：用骨架屏，形状比一颗转圈更能预告内容",
        "超过十几秒的任务：给出阶段文案或取消入口，光转圈会让人以为卡死",
    ],
    examples=[
        Example(
            "行内小转圈",
            _inline,
            hint="三档尺寸并排：行内用 small，默认档位会把这一行顶高。",
            code=_INLINE_CODE,
        ),
        Example(
            "区块加载",
            _block,
            hint="占位区按真实内容预估高度，转圈居中，下方一句在等什么。",
        ),
        Example(
            "骨架屏",
            _skeleton,
            hint="占位块照着内容形状画；骨架是拼出来的，组件只负责转圈。",
            code=_SKELETON_CODE,
        ),
    ],
    api=[
        Api(
            "size_name",
            "str",
            '"normal"',
            "尺寸档位：small 20 / normal 32 / large 48，未知值回退 normal",
        ),
        Api("color", "ColorValue | None", "None", "圆环颜色，默认主色"),
        Api("bgcolor", "ColorValue | None", "None", "圆环轨道的底色"),
        Api("stroke_width", "int | None", "None", "线宽；默认直径的 1/10，最低 2px"),
        Api("value", "float | None", "None", "0–1 的确定进度；留空表示一直转"),
        Api("semantics_label", "str | None", "None", "读屏文案，例如「加载组件清单」"),
    ],
    notes=[
        tip(
            "宽高只在你没显式传的时候才套档位：Loading(width=16) 会被保留，"
            "线宽也跟着 16 算。size_name 拼错时回退到 normal，不报错。"
        ),
        info(
            "骨架屏不是组件内置的能力：它是用容器拼出来的占位块（on-surface 8%），"
            "Loading 只负责那颗圈。要骨架就别再叠一颗转圈。"
        ),
        warn(
            "一块区域只放一个加载指示。三颗转圈同时开会让人以为界面坏了；"
            "列表用骨架，按钮用行内小圈，互不叠加。"
        ),
    ],
    tags=("加载", "loading", "转圈", "spinner", "骨架屏", "反馈"),
)


if __name__ == "__main__":
    run(SPEC)
