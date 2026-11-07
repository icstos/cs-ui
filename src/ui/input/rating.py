"""评分 (Rating) —— 点星星打分，支持半星、悬停预览与只读展示。

评分是「用图形代替数字」的输入：五颗星比一个 1-5 的输入框更快，也更像一次表态。
组件把每一颗星做成一整块可点区域，悬停时先把分数预览出来，移开就恢复 —— 用户
在按下之前就能看到「点这里会得几分」。

``value`` 就是分数本身（1 起，最大 ``elements``）：``value=4`` 是四星，
``precision=0.5`` 时 ``value=4.5`` 是四星半。``None``（或 0）表示还没评。
点击已经选中的那一档会清空评分，回调收到 0。

用法::

    rating = Rating(value=4, on_change=lambda score: print(score))
    Column([rating])

只读展示把 ``readonly`` 打开：外观不变，但点不动、也不吃悬停预览。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import field

import flet as ft

from ui.core.doc import Api, Example, Spec, info, run, tip
from ui.core.tokens import FONT_SIZE, SPACE, overlay

__all__ = ["Rating"]

#: 星标尺寸与可点区域。可点区域比图标大一圈，半星的左右判定才有余量
ICON_SIZE = 26
CELL = 34

#: 三档图标：整星 / 半星 / 空星
STAR_FULL = ft.Icons.STAR_ROUNDED
STAR_HALF = ft.Icons.STAR_HALF_ROUNDED
STAR_EMPTY = ft.Icons.STAR_OUTLINE_ROUNDED

#: 颜色走角色色：填充是主色，空星是次要文字色，禁用走 on-surface 38%。
#: 此前写死的 GREY / BLUE 换主色或切深色主题后整排星都不跟随。
FILLED = ft.Colors.PRIMARY
EMPTY = ft.Colors.ON_SURFACE_VARIANT
DIMMED = overlay(0.38)

MUTED = ft.Colors.ON_SURFACE_VARIANT


def _is_true(payload: object) -> bool:
    """hover 载荷归一：可能是 ``True``，也可能是 ``"true"`` 字符串。"""
    if isinstance(payload, bool):
        return payload
    return str(payload).strip().lower() == "true"


@ft.control
class Rating(ft.Row):
    """星级评分：一排可点的星，值落在分数上。

    Args:
        value: 当前分数，1 起；``None`` 表示未评分。
        elements: 星星数量，默认 5。
        precision: 精度，``1`` 为整星、``0.5`` 为半星。
        readonly: 只读：外观不变，但点击与悬停预览都关掉。
        disabled: 禁用：整排降灰且不可点；与只读的区别是「看起来就不能用」。
        on_change: 分数变化回调，入参是分数；清空时收到 0。
    """

    value: float | None = None
    elements: int = 5
    precision: float = 1.0
    readonly: bool = False
    # disabled 继承自 ft.Row 的 kw_only 字段，重新声明时必须显式 kw_only=True，
    # 否则它会变成第 0 个位置参数（详见 ui.input.button.Button）。
    disabled: bool = field(default=False, kw_only=True)
    on_change: Callable[[float], None] | None = None

    def init(self):
        self.precision = 0.5 if 0 < float(self.precision) < 1 else 1.0
        self.elements = max(1, int(self.elements))
        self.value = self._normalize(self.value)
        self.on_change = self.on_change or (lambda _score: None)
        self._preview: float | None = None
        self._icons: list[ft.Icon] = []
        self.controls = [self._build_star(index) for index in range(self.elements)]
        self.spacing = 0
        self._paint(self.value or 0.0)

    # -- 取值 ---------------------------------------------------------------
    @property
    def _interactive(self) -> bool:
        return not (self.readonly or self.disabled)

    def _normalize(self, value: float | None) -> float | None:
        """夹进 0..elements，并按 ``precision`` 吸附；0 归一成「未评分」。"""
        if value is None:
            return None
        score = min(max(float(value), 0.0), float(self.elements))
        score = round(round(score / self.precision) * self.precision, 2)
        return score or None

    # -- 构建 ---------------------------------------------------------------
    def _build_star(self, index: int) -> ft.Container:
        """一颗星：整块可点，``data`` 记住下标，半星判定靠点击的横向位置。"""
        icon = ft.Icon(icon=STAR_EMPTY, size=ICON_SIZE, color=EMPTY)
        self._icons.append(icon)
        return ft.Container(
            width=CELL,
            height=CELL,
            alignment=ft.Alignment.CENTER,
            border_radius=CELL // 2,
            data=index,
            tooltip=f"{index + 1} 分" if not self.readonly else None,
            on_hover=None if self._interactive else self._handle_hover,
            on_tap_down=None if self._interactive else self._handle_tap,
            content=icon,
        )

    def _paint(self, score: float) -> None:
        """按分数重画整排星。

        每一颗取 ``score - index`` 的剩余量：≥1 整星、≥0.5 半星、其余空星。
        这样 4.5 分在第 5 颗上是半星，4 分则是整星。
        """
        for index, icon in enumerate(self._icons):
            fill = max(0.0, min(1.0, score - index))
            if fill >= 1:
                icon.icon, color = STAR_FULL, FILLED
            elif fill >= 0.5:
                icon.icon, color = STAR_HALF, FILLED
            else:
                icon.icon, color = STAR_EMPTY, EMPTY
            icon.color = DIMMED if self.disabled else color

    # -- 交互 ---------------------------------------------------------------
    def _handle_hover(self, e: ft.ControlEvent) -> None:
        """悬停预览：进入第 n 颗就先画 n 分，移出恢复真实分数。

        只重置自己那一档的预览 —— 从第 3 颗滑到第 4 颗时，第 3 颗的移出事件
        不该把第 4 颗刚点亮的预览抹掉。
        """
        index = int(e.control.data)
        if _is_true(e.data):
            self._preview = float(index) + 1.0
        elif self._preview == float(index) + 1.0:
            self._preview = None
        self._paint(self._preview if self._preview is not None else (self.value or 0.0))
        self.update()

    def _handle_tap(self, e: ft.ControlEvent) -> None:
        """点击落点决定分数：半星模式下左半边是 x.5，右半边是整星。"""
        if not self._interactive:
            return
        index = int(e.control.data)
        score = float(index) + 1.0
        position = getattr(e, "local_position", None)
        if self.precision == 0.5 and position is not None and position.x < CELL / 2:
            score -= 0.5
        # 再点同一档 = 取消评分：让「打错了」不必去别处找清除按钮
        if self.value is not None and abs(score - float(self.value)) < 1e-9:
            score = 0.0
        self._set(score)

    def _set(self, value: float | None) -> None:
        self.value = self._normalize(value)
        self._preview = None
        self._paint(self.value or 0.0)
        self.on_change(self.value if self.value is not None else 0)  # type: ignore[misc]
        self.update()

    # -- 外部赋值 -----------------------------------------------------------
    def set_value(self, value: float | None) -> None:
        """外部改分并重绘，不触发 ``on_change`` —— 数据源回流不该再发一次事件。"""
        self.value = self._normalize(value)
        self._preview = None
        self._paint(self.value or 0.0)
        if self.parent is not None:
            self.update()


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
def _caption(text: str) -> ft.Control:
    return ft.Text(text, size=FONT_SIZE["small"], color=MUTED)


def _score_text(score: float) -> str:
    return "未评分" if not score else f"{score:g} 分"


@ft.component
def _basic() -> ft.Control:
    """基础五星：悬停预览、点击落分、再点同一档取消。"""
    score, set_score = ft.use_state(0.0)
    return ft.Column(
        spacing=SPACE["2"],
        controls=[
            Rating(value=score, on_change=set_score),
            _caption(f"当前评分：{_score_text(score)}（点同一颗星可取消）"),
        ],
    )


@ft.component
def _half() -> ft.Control:
    """半星精度：点左半边是半星，点右半边是整星。"""
    score, set_score = ft.use_state(3.5)
    return ft.Column(
        spacing=SPACE["2"],
        controls=[
            Rating(value=score, precision=0.5, on_change=set_score),
            _caption(f"当前评分：{_score_text(score)}（precision=0.5）"),
        ],
    )


@ft.component
def _readonly() -> ft.Control:
    """只读展示：4.5 分，外观与可用时一致，但点不动。"""
    return ft.Column(
        spacing=SPACE["2"],
        controls=[
            Rating(value=4.5, precision=0.5, readonly=True),
            _caption("综合评分 4.5 / 5，来自 128 条评价（只读）"),
        ],
    )


_BASIC_CODE = """rating = Rating(value=4, on_change=lambda score: print(score))
Column([rating])

# 半星：点星星左半边得 x.5，右半边得整星
Rating(value=4.5, precision=0.5, on_change=print)

# 只读展示（评分结果页、商品卡片）
Rating(value=4.5, precision=0.5, readonly=True)"""


SPEC = Spec(
    name="Rating",
    summary="点星星打分：五颗星、半星精度，悬停先预览、点击再落分。",
    definition=(
        "评分把「打几分」这件事画成排成一行的星：比数字输入快，也比下拉框更像一次"
        "表态。组件负责三件容易做漏的事 —— 悬停时预览将要选中的分数、按点击落在"
        "星星的哪半边决定半星、以及把分数写回 ``value`` 供调用方读取。只读模式保留"
        "完整外观，用于商品卡片、评价列表这类「只展示结果」的位置。"
    ),
    anatomy=[
        ("星标", "每颗星占 34px 的可点区域，整星 / 半星 / 空星三种图标按分数切换。"),
        (
            "填色",
            "已得分走主色，空星走次要文字色；两者都跟随主题，不在代码里写死灰蓝。",
        ),
        (
            "悬停预览",
            "指针移到第 n 颗先把整排画成 n 分，移开恢复真实分数；按下前就能看到结果。",
        ),
        (
            "半星落点",
            "precision=0.5 时按点击的横向位置判定：左半边 x.5，右半边整星。",
        ),
        (
            "只读 / 禁用",
            "只读外观不变但点不动；禁用整排降到 38% 灰，明确表达「不可用」。",
        ),
    ],
    when=[
        "商品、文章、服务结束后收集主观评分（1-5 星）",
        "列表或卡片里展示已有评分，只读即可",
        "需要半星表达更细的差异（4.5 比 4 更接近真实感受）",
    ],
    avoid=[
        "需要可比较的客观分数（NPS、考试分）：用 NumberInput，星星不适合精确数值",
        "要收集「为什么给这个分」：在评分下面接一个 TextField，别把理由塞进 tooltip",
        "选项本身不是程度递进（满意 / 一般 / 不满意）：用 Radio，星级暗示了等差",
    ],
    examples=[
        Example(
            "基础五星",
            _basic,
            hint="悬停预览、点击落分；再点同一颗星清空，回调收到 0。",
            code=_BASIC_CODE,
        ),
        Example(
            "半星精度",
            _half,
            hint="precision=0.5：点星星左半边得半星，右半边得整星。",
        ),
        Example(
            "只读展示",
            _readonly,
            hint="4.5 分只读：外观与可用时一致，但没有悬停预览、点了也不动。",
        ),
    ],
    api=[
        Api("value", "float | None", "None", "当前分数，1 起；None 或 0 表示未评分"),
        Api("elements", "int", "5", "星星数量；常规评分保持 5，满意度可用 3"),
        Api("precision", "float", "1.0", "精度：1 整星，0.5 支持半星"),
        Api("readonly", "bool", "False", "只读：外观不变，但点击与悬停预览都关掉"),
        Api("disabled", "bool", "False", "禁用：整排降灰且不可点，值与只读一样可读"),
        Api(
            "on_change",
            "Callable[[float], None] | None",
            "None",
            "分数变化回调；清空时收到 0，用于回写表单或触发提交",
        ),
        Api(
            "set_value",
            "method",
            "—",
            "外部改分并重绘，不触发 on_change",
        ),
    ],
    notes=[
        tip(
            "每颗星是一整块 34px 的可点区域，而不是裸图标：图标本身只有 26px，半星的"
            "左右判定需要余量，手指点起来也不至于总差半颗。"
        ),
        info(
            "``value`` 现在就是分数（1 起），与 ``on_change`` 回传的值一致。此前内部存"
            "的是 0 基下标，``Rating(value=4)`` 读出来是 3，和回调差 1，调用方很容易"
            "在「显示」与「提交」之间错一档。"
        ),
        info(
            "颜色从写死的 GREY / BLUE 换成 ON_SURFACE_VARIANT / PRIMARY，禁用走"
            "on-surface 38%：换主色或切深色主题时整排星自动跟随。"
        ),
    ],
    tags=("评分", "rating", "星级", "打分", "表单"),
)


if __name__ == "__main__":
    run(SPEC)
