"""自适应栅格 (Grid) —— 给一个最小格宽，剩下的交给 Flutter。

栅格最容易写坏的地方是"在 Python 里算列数"：窗口每拖一像素就重算一次、重排一次，
拖动时画面会一顿一顿。:class:`Grid` 的做法是把列数**预先翻成每个断点的虚拟列数**
下发一次，之后换列发生在渲染层：

* ``columns = {"xs": 1, "sm": 2, "md": 3, "lg": 4, "xl": 4, "xxl": 4}``
  —— 虚拟列数**就是每行几格**；
* 每个子项 ``col = 1`` —— 于是"一行 n 格"必然等宽，不会出现末行缺一角。

这样写的好处不只是快：等宽来自结构，而不是"12 除以 3 正好整除"这种巧合。
12 栅格里放 5 格会剩下 2 列没法分，而"虚拟列数 = 格数"永远分得干净。

用法::

    Grid(
        min_col_width=260,          # 每格至少 260 宽
        max_cols=4,                 # 再宽也就 4 格（32 寸屏上别摆八个小方块）
        controls=[card(1), card(2), card(3), card(4)],
    )

    Grid(per_row={"compact": 1, "medium": 2, "expanded": 3}, controls=form_rows)
"""

from __future__ import annotations

from dataclasses import field

import flet as ft

from ui.core.doc import Api, Example, Spec, info, run, tip, warn
from ui.core.responsive import size_class
from ui.core.tokens import BREAKPOINT, FONT_SIZE, FONT_WEIGHT, RADIUS, SPACE, overlay

__all__ = ["Grid"]

#: ``min_col_width`` 的默认值：一张"卡片"能装下标题 + 两行说明的最小宽度。
DEFAULT_MIN_COL_WIDTH: int = 260

#: 每行格数的兜底上限。列数不是越多越好 —— 1440 宽的屏上放 6 格，
#: 每格只有 220 宽，标题会开始折行，扫读反而变慢。
DEFAULT_MAX_COLS: int = 4


def fit_columns(
    width: float,
    min_col_width: int = DEFAULT_MIN_COL_WIDTH,
    gap: int = SPACE["4"],
    max_cols: int = DEFAULT_MAX_COLS,
) -> int:
    """给定可用宽度，算出**放得下几格**（含间距）。

    ``n`` 格占 ``n * min + (n - 1) * gap``，所以 ``n = (width + gap) / (min + gap)``。

    取的是**断点下界**（见 :data:`~ui.core.tokens.BREAKPOINT`），也就是宁可少放一格：
    少放一格只是右侧多一点留白，多放一格则是内容被压到最小宽度以下 ——
    挤压会溢出、会被裁切，留白只是不好看。
    """
    if min_col_width <= 0:
        return max(1, int(max_cols))
    usable = max(0.0, float(width))
    n = int((usable + gap) // (min_col_width + gap))
    return max(1, min(n, max(1, int(max_cols))))


def _counts(
    per_row: int | dict[str, int] | None,
    min_col_width: int,
    gap: int,
    max_cols: int,
) -> dict[str, int]:
    """每行格数 → 每个断点的虚拟列数（键与 :data:`BREAKPOINT` 完全一致）。"""
    if isinstance(per_row, dict):
        # 键用**窗口类**（compact / medium / expanded），不是 xs…xxl —— 组件思考的
        # 是"这个宽度下放几格"，而不是"第几个断点"。同一张表里也容忍直接写断点名。
        table: dict[str, int] = {}
        last = 1
        for bp, width in BREAKPOINT.items():
            keys = (size_class(width), bp)
            for key in keys:
                if key in per_row:
                    last = max(1, int(per_row[key]))
                    break
            table[bp] = last
        return table
    if per_row is not None:
        return dict.fromkeys(BREAKPOINT, max(1, int(per_row)))
    return {
        bp: fit_columns(width, min_col_width, gap, max_cols)
        for bp, width in BREAKPOINT.items()
    }


@ft.control
class Grid(ft.ResponsiveRow):
    """自适应栅格，继承自 :class:`flet.ResponsiveRow`。

    Args:
        controls: 格子内容。子项自己设了 ``col`` 就按它的跨度走（``col=2`` 表示
            占两格宽），没设的统一占一格。
        min_col_width: 每格最小宽度，默认 260。宽度不够时会自动减格数，而不是把
            格子压扁。
        max_cols: 每行最多几格，默认 4。
        per_row: 直接指定每行几格；``int`` 对所有档位生效，``dict`` 按断点给
            （``{"compact": 1, "medium": 2, "expanded": 3}``）。给了它就不再按
            ``min_col_width`` 算。
        gap: 格与格之间的水平间距，默认 16；行距默认同值。
        run_gap: 行距，默认跟随 ``gap``。

    Notes:
        列数在**构建时**算好并下发，拖动窗口时由 Flutter 按断点换列，Python 侧
        不再参与 —— 这是它与"用 ``use_responsive`` 自己算列数"的根本区别。
    """

    controls: list[ft.Control] = field(default_factory=list)
    min_col_width: int = DEFAULT_MIN_COL_WIDTH
    max_cols: int = DEFAULT_MAX_COLS
    per_row: int | dict[str, int] | None = None
    gap: int = SPACE["4"]
    run_gap: int | None = None

    def init(self):
        gap = max(0, int(self.gap))
        counts = _counts(self.per_row, self.min_col_width, gap, self.max_cols)

        # 虚拟列数 = 每行格数，于是"n 格一行"数学上必然等宽。
        self.columns = counts
        # 断点表用框架自己的那份：``col`` 里写的键必须和这里一致，否则 Flutter
        # 认不出来会静默回落成"整行一个"。
        self.breakpoints = dict(BREAKPOINT)
        self.spacing = gap
        self.run_spacing = gap if self.run_gap is None else max(0, int(self.run_gap))

        for control in self.controls:
            # ``ft.Control.col`` 的默认值是 12（整行）。在"虚拟列数 = 每行格数"的
            # 体系里 12 没有意义，所以它等同于"没设过" —— 一并按一格处理。
            if getattr(control, "col", None) in (None, 12):
                control.col = 1


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
_MUTED = ft.Colors.ON_SURFACE_VARIANT


def _tile(index: int, *, height: int = 84) -> ft.Control:
    """格子内容：编号 + 一句说明，用来观察等宽与换行。"""
    return ft.Container(
        height=height,
        padding=SPACE["4"],
        border_radius=RADIUS["lg"],
        bgcolor=overlay(0.04),
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        content=ft.Column(
            spacing=2,
            controls=[
                ft.Text(
                    f"格 {index}",
                    size=FONT_SIZE["body"],
                    weight=FONT_WEIGHT["semibold"],
                ),
                ft.Text(
                    "拖动窗口，列数会自己变；格子始终等宽。",
                    size=FONT_SIZE["small"],
                    color=_MUTED,
                ),
            ],
        ),
    )


@ft.component
def _auto() -> ft.Control:
    """按最小格宽自动分列：这是最常用的写法。"""
    return Grid(
        min_col_width=200,
        max_cols=4,
        controls=[_tile(i) for i in range(1, 7)],
    )


@ft.component
def _fixed() -> ft.Control:
    """直接指定每行格数：内容自己知道"一屏该有几列"时用它。"""
    return Grid(
        per_row={"compact": 1, "medium": 2, "expanded": 3},
        controls=[_tile(i) for i in range(1, 7)],
    )


@ft.component
def _span() -> ft.Control:
    """跨格：子项自己写 ``col=2`` 就占两格宽。"""
    wide = ft.Container(
        col=2,
        height=84,
        padding=SPACE["4"],
        border_radius=RADIUS["lg"],
        bgcolor=overlay(0.08),
        border=ft.Border.all(1, ft.Colors.PRIMARY),
        content=ft.Text(
            "col=2：占两格宽（窄屏上仍是一整行）",
            size=FONT_SIZE["small"],
            color=ft.Colors.PRIMARY,
        ),
    )
    return Grid(min_col_width=160, max_cols=3, controls=[_tile(1), wide, _tile(2)])


_AUTO_CODE = """Grid(
    min_col_width=200,      # 每格至少 200 宽
    max_cols=4,             # 再宽也就 4 格
    controls=[card(1), card(2), card(3), card(4)],
)"""

_FIXED_CODE = """Grid(
    per_row={"compact": 1, "medium": 2, "expanded": 3},
    controls=rows,
)"""

_SPAN_CODE = """Grid(
    min_col_width=160,
    max_cols=3,
    controls=[
        tile(1),
        Container(col=2, content=Text("占两格")),   # 跨度由子项自己声明
        tile(2),
    ],
)"""


SPEC = Spec(
    name="Grid",
    summary="给一个最小格宽，列数随窗口自己变 —— 换列在渲染层完成。",
    definition=(
        "栅格解决的是「卡片墙一到窄窗口就挤成一条缝」：列数应当跟着可用宽度走。"
        "但列数不能每拖一个像素就算一次（那是 Python 与渲染层来回打乒乓，拖动会卡），"
        "所以 Grid 在构建时把每个断点的列数一次算好下发，换列交给 Flutter。"
        "它与 ResponsiveRow 的区别在写法：ResponsiveRow 要求每个子项都手写一份 "
        "断点字典，Grid 只要一个 min_col_width —— 「一格至少多宽」是设计上的事实，"
        "「第几档放几列」是它的计算结果，不该让人手动重复。"
    ),
    anatomy=[
        ("格子", "等宽，由「虚拟列数 = 每行格数」保证，不依赖 12 能否整除。"),
        (
            "最小格宽",
            "min_col_width 是「再窄就少放一格」的阈值，不是格子的固定宽度。",
        ),
        (
            "间距",
            "gap 同时决定水平间距与行距；两者分开看不出必要，除非内容自己带外边距。",
        ),
        (
            "跨格",
            "子项自己设 col=2 就占两格；窄到只有一格时它自然退化成整行。",
        ),
    ],
    when=[
        "卡片墙 / 指标块：数量不定、宽度不定，都要排得整齐",
        "表单分组：窄屏一列、宽屏两列，字段顺序不变",
        "图片墙、快捷入口、仪表盘小面板",
    ],
    avoid=[
        "表格用它排：表格要列对齐，用 Table",
        "整页三段式布局（侧栏 + 内容 + 大纲）：那是外壳，用 Row + 断点判断",
        "只有一个子项：直接放，栅格只在「多个格子要换行」时才有意义",
    ],
    examples=[
        Example(
            "自动分列",
            _auto,
            hint="最常用：给最小格宽，列数自己算。窄窗口一格一行，宽窗口四格一行。",
            code=_AUTO_CODE,
        ),
        Example(
            "指定每行格数",
            _fixed,
            hint="内容自己知道一屏该几列时用它；缺的档位沿窄档继承。",
            code=_FIXED_CODE,
        ),
        Example(
            "跨格",
            _span,
            hint="col=2 占两格宽；窄到只剩一格时自动退化成整行，不用写特例。",
            code=_SPAN_CODE,
        ),
    ],
    api=[
        Api("controls", "list[Control]", "[]", "格子内容"),
        Api(
            "min_col_width",
            "int",
            str(DEFAULT_MIN_COL_WIDTH),
            "每格最小宽度；宽度不够时减格数，而不是压扁格子",
        ),
        Api("max_cols", "int", str(DEFAULT_MAX_COLS), "每行最多几格"),
        Api(
            "per_row",
            "int | dict[str, int] | None",
            "None",
            "直接指定每行格数；给了它就不再按 min_col_width 算",
        ),
        Api("gap", "int", "16", "格间距，同时作为默认行距"),
        Api("run_gap", "int | None", "None", "行距；None 表示跟随 gap"),
        Api("col", "int | dict", "None", "继承自 ResponsiveRow：Grid 自身在父栅格里的跨度"),
    ],
    notes=[
        info(
            "列数在构建时算好并写成每个断点的虚拟列数，子项各占 1 列。"
            "所以拖动窗口时换列由 Flutter 完成，Python 侧一次都不重算。"
        ),
        tip(
            "min_col_width 取「一张卡片能装下标题 + 两行说明」的宽度，通常 240~280。"
            "把它设得比实际内容还小，等于放弃保护 —— 格子会缩到内容溢出。"
        ),
        warn(
            "断点表固定为框架的 BREAKPOINT（与 flet 的 ResponsiveRow 同值）。"
            "自己改 breakpoints 会让 col 里的键与 Flutter 认的键对不上，"
            "表现是所有格子退回「整行一个」，且不会报错。"
        ),
    ],
    tags=("栅格", "grid", "响应式", "卡片墙", "自适应"),
)


if __name__ == "__main__":
    run(SPEC)
