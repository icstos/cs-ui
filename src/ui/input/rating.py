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

两种使用场景，两种预览通道
--------------------------

``Rating`` 是 ``ft.Control`` 子类，可以直接 ``page.add``，此时悬停预览由组件自己
重绘那五颗星（最省：只下发五个图标更新）。

但在 ``@ft.component`` 渲染出的树里，flet 1.1.2 给**整棵子树**打了冻结标记，
之后 ``icon.icon = ...`` 直接抛 ``Frozen controls cannot be updated``，而 patch
也会因 ``frozen and src is dst`` 把这棵子树整个跳过 —— 改了也上不了屏。所以那种
场景下预览必须走**受控**通道：调用方给 ``preview`` 并把悬停意图接在 ``on_preview``
上，由它重渲染出一棵新树。不接 ``on_preview`` 也不会崩，只是没有预览。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import field

import flet as ft

from ui.core.doc import Api, Example, Spec, info, run, tip
from ui.core.tokens import (
    CONTROL_HEIGHT,
    FONT_SIZE,
    ICON_SIZE,
    SPACE,
    disabled_layer,
)

__all__ = ["Rating"]

#: 星标尺寸与可点区域。可点区域取控件基线高 36：与同排的表单控件等高，
#: 半星的左右判定也刚好以格子中线为界（图标居中，中线即星心）。
STAR_ICON_SIZE = ICON_SIZE["2xl"]
CELL = CONTROL_HEIGHT["md"]

#: 三档图标：整星 / 半星 / 空星
STAR_FULL = ft.Icons.STAR_ROUNDED
STAR_HALF = ft.Icons.STAR_HALF_ROUNDED
STAR_EMPTY = ft.Icons.STAR_OUTLINE_ROUNDED

#: 颜色走角色色：填充是主色，空星是次要文字色，禁用走 on-surface 38%。
#: 此前写死的 GREY / BLUE 换主色或切深色主题后整排星都不跟随。
FILLED = ft.Colors.PRIMARY
EMPTY = ft.Colors.ON_SURFACE_VARIANT
DIMMED = disabled_layer()

MUTED = ft.Colors.ON_SURFACE_VARIANT


def _is_true(payload: object) -> bool:
    """hover 载荷归一：可能是 ``True``，也可能是 ``"true"`` 字符串。"""
    if isinstance(payload, bool):
        return payload
    return str(payload).strip().lower() == "true"


def _normalize(value: float | None, count: int, step: float) -> float | None:
    """夹进 0..count，并按 ``step`` 吸附；0 归一成「未评分」。"""
    if value is None:
        return None
    score = min(max(float(value), 0.0), float(count))
    score = round(round(score / step) * step, 2)
    return score or None


def _fill(score: float, index: int) -> float:
    """第 ``index`` 颗星拿到多少（0~1）：≥1 整星、≥0.5 半星、其余空星。"""
    return max(0.0, min(1.0, score - index))


def _icon(score: float, index: int) -> str:
    fill = _fill(score, index)
    if fill >= 1:
        return STAR_FULL
    return STAR_HALF if fill >= 0.5 else STAR_EMPTY


@ft.control
class Rating(ft.Row):
    """星级评分：一排可点的星，值落在分数上。

    Args:
        value: 当前分数，1 起；``None`` 表示未评分。
        elements: 星星数量，默认 5。
        precision: 精度，``1`` 为整星、``0.5`` 为半星。
        readonly: 只读：外观不变，但点击与悬停预览都关掉。
        disabled: 禁用：整排降灰且不可点；与只读的区别是「看起来就不能用」。
        preview: 受控预览值（1 起）。给了它就完全由外部决定「亮几颗」，
            ``None`` 表示没有预览。``@ft.component`` 里必须用这种方式。
        on_change: 分数变化回调，入参是分数；清空时收到 0。
        on_preview: 悬停预览变化回调，入参是预览分数或 ``None``。接上它就进入
            受控预览模式（组件自己不重绘，交给调用方重渲染）。
    """

    value: float | None = None
    elements: int = 5
    precision: float = 1.0
    readonly: bool = False
    # disabled 继承自 ft.Row 的 kw_only 字段，重新声明时必须显式 kw_only=True，
    # 否则它会变成第 0 个位置参数（详见 ui.input.button.Button）。
    disabled: bool = field(default=False, kw_only=True)
    preview: float | None = None
    on_change: Callable[[float], None] | None = None
    on_preview: Callable[[float | None], None] | None = None

    def init(self):
        self.precision = 0.5 if 0 < float(self.precision) < 1 else 1.0
        self.elements = max(1, int(self.elements))
        self.value = self._normalize(self.value)
        self.preview = self._normalize(self.preview)
        self.on_change = self.on_change or (lambda _score: None)
        self._local_preview: float | None = None
        self._icons: list[ft.Icon] = []
        self.controls = [self._build_star(index) for index in range(self.elements)]
        self.spacing = 0
        self._paint(self._shown())

    # -- 取值 ---------------------------------------------------------------
    @property
    def _interactive(self) -> bool:
        return not (self.readonly or self.disabled)

    @property
    def _frozen_tree(self) -> bool:
        """是否处在 ``@ft.component`` 渲染出的冻结树里。

        冻结之后写子控件属性会抛 ``Frozen controls``，而且 patch 会把这棵子树
        整个跳过（``frozen and src is dst`` 直接 return）—— 写了也上不了屏。
        所以这时只能把状态变化交给回调，由调用方重渲染出新实例。
        """
        return hasattr(self, "_frozen")

    def _normalize(self, value: float | None) -> float | None:
        return _normalize(value, self.elements, self.precision)

    def _shown(self) -> float:
        """这一刻该画几分：受控预览 > 本地预览 > 真实值。"""
        if self.preview is not None:
            return float(self.preview)
        if self._local_preview is not None:
            return self._local_preview
        return self.value or 0.0

    # -- 构建 ---------------------------------------------------------------
    def _build_star(self, index: int) -> ft.Container:
        """一颗星：整块可点，``data`` 记住下标，半星判定靠点击的横向位置。"""
        icon = ft.Icon(icon=STAR_EMPTY, size=STAR_ICON_SIZE, color=EMPTY)
        self._icons.append(icon)
        return ft.Container(
            width=CELL,
            height=CELL,
            alignment=ft.Alignment.CENTER,
            border_radius=CELL // 2,
            data=index,
            tooltip=f"{index + 1} 分" if not self.readonly else None,
            # 可交互才挂处理器。这里曾经写成 ``None if self._interactive else ...``
            # （条件反了）：可交互的星表一个处理器都没挂，只读/禁用的反而全挂上 ——
            # 于是在 @ft.component 树里悬停只读示例就会撞上冻结树直接抛异常。
            on_hover=None if not self._interactive else self._handle_hover,
            on_tap_down=None if not self._interactive else self._handle_tap,
            content=icon,
        )

    def _paint(self, score: float) -> None:
        """按分数重画整排星。

        每一颗取 ``score - index`` 的剩余量：≥1 整星、≥0.5 半星、其余空星。
        这样 4.5 分在第 5 颗上是半星，4 分则是整星。

        **只在未冻结的树上调用** —— 冻结树里这个写入会抛异常。
        """
        for index, icon in enumerate(self._icons):
            icon.icon = _icon(score, index)
            icon.color = (
                DIMMED if self.disabled else (FILLED if _fill(score, index) >= 0.5 else EMPTY)
            )

    # -- 交互 ---------------------------------------------------------------
    def _handle_hover(self, e: ft.ControlEvent) -> None:
        """悬停预览：进入第 n 颗就先画 n 分，移出恢复真实分数。

        只重置自己那一档的预览 —— 从第 3 颗滑到第 4 颗时，第 3 颗的移出事件
        不该把第 4 颗刚点亮的预览抹掉。
        """
        if not self._interactive:
            return
        index = float(int(e.control.data)) + 1.0
        current = self.preview if self.preview is not None else self._local_preview
        if _is_true(e.data):
            wanted: float | None = index
        elif current == index:
            wanted = None
        else:
            return
        # 受控优先：外部给了 on_preview 就由它重渲染，组件不自己动。
        if self.on_preview is not None:
            self.on_preview(wanted)
            return
        if self._frozen_tree:
            return  # 冻结树里写不了也刷不动，静默降级（不预览，但不崩）
        self._local_preview = wanted
        self._paint(self._shown())
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
        score = self._normalize(value)
        if self._frozen_tree:
            # 冻结树里改不动自己，把结果交给调用方 —— 它重渲染时传入新 value。
            self.on_change(score if score is not None else 0)  # type: ignore[misc]
            return
        self.value = score
        self._local_preview = None
        self._paint(self._shown())
        self.on_change(score if score is not None else 0)  # type: ignore[misc]
        self.update()

    # -- 外部赋值 -----------------------------------------------------------
    def set_value(self, value: float | None) -> None:
        """外部改分并重绘，不触发 ``on_change`` —— 数据源回流不该再发一次事件。

        冻结树里无事可做（写不进去、patch 也跳过）：那种场景请改 ``value`` 参数
        让调用方重渲染。
        """
        if self._frozen_tree:
            return
        self.value = self._normalize(value)
        self._local_preview = None
        self._paint(self._shown())
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
    preview, set_preview = ft.use_state(None)
    return ft.Column(
        spacing=SPACE["2"],
        controls=[
            Rating(
                value=score,
                preview=preview,
                on_change=set_score,
                on_preview=set_preview,
            ),
            _caption(f"当前评分：{_score_text(score)}（点同一颗星可取消）"),
        ],
    )


@ft.component
def _half() -> ft.Control:
    """半星精度：点左半边是半星，点右半边是整星。"""
    score, set_score = ft.use_state(3.5)
    preview, set_preview = ft.use_state(None)
    return ft.Column(
        spacing=SPACE["2"],
        controls=[
            Rating(
                value=score,
                precision=0.5,
                preview=preview,
                on_change=set_score,
                on_preview=set_preview,
            ),
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
        ("星标", "每颗星占 36px 的可点区域，整星 / 半星 / 空星三种图标按分数切换。"),
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
            "preview",
            "float | None",
            "None",
            "受控预览值；给了就完全由外部决定亮几颗（@ft.component 里用它）",
        ),
        Api(
            "on_change",
            "Callable[[float], None] | None",
            "None",
            "分数变化回调；清空时收到 0，用于回写表单或触发提交",
        ),
        Api(
            "on_preview",
            "Callable[[float | None], None] | None",
            "None",
            "悬停预览变化回调；接上即进入受控预览模式，由调用方重渲染",
        ),
        Api("set_value", "method", "—", "外部改分并重绘，不触发 on_change"),
    ],
    notes=[
        tip(
            "每颗星是一整块 36px 的可点区域，而不是裸图标：图标本身只有 24px，半星的"
            "左右判定需要余量，手指点起来也不至于总差半颗。可点区域取的是控件基线高"
            "（CONTROL_HEIGHT 的 md 档），换到别的高度标尺时这里跟着走。"
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
        tip(
            "在 ``@ft.component`` 里用要给 ``preview`` + ``on_preview``（受控）。"
            "那种树里的控件是冻结的：``icon.icon = ...`` 会抛 "
            "``Frozen controls cannot be updated``，而 patch 又因 "
            "``frozen and src is dst`` 把整棵子树跳过 —— 组件自己重绘既写不进也刷不动。"
            "不接这两个参数不会崩，只是没有悬停预览。"
        ),
    ],
    tags=("评分", "rating", "星级", "打分", "表单"),
)


if __name__ == "__main__":
    run(SPEC)
