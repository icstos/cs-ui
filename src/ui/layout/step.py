"""步骤条组件 (Step)。

把"一件事分几步、做到第几步"讲清楚。参考 layui-vue ``lay-step`` 与
Element Plus ``el-steps`` 的共识能力，收敛成桌面端形态：

- **状态机**：每步只会是 ``wait`` / ``process`` / ``finish`` / ``error`` 之一。
  默认按 ``active`` 推导（``index < active`` 已完成、``== active`` 进行中、
  ``> active`` 未开始），也可以在 :class:`StepItem` 上用 ``status`` 单独钉死；
- **两种排布**：``horizontal``（横向平铺，默认）/ ``vertical``（左侧轴轨）；
- **简洁模式**：``simple=True`` 收成一行 "① 标题 › ② 标题"，适合放在工具栏或
  页面顶部，点击即跳转；
- **进度着色**：只给"已经走过"的连接段上色，没走到的是灰线 —— 进度感来自颜色，
  不靠额外装饰；
- **可点击**：``clickable=True``（简洁模式默认开）时整步都是热区，回传
  ``on_change(index)``；组件同时就地更新 ``active``，使用方接不接都有反馈。

.. note::
    组件是**受控**的：``active`` 由使用方给定，点击时的就地更新只是让反馈即时，
    真正的状态源仍在调用方 —— 这样"上一步 / 下一步 / 点击跳转"三条路径行为一致。

.. note::
    圆点永远与**标题首行**垂直居中：横向时标题块顶在圆点行下沿，垂直时标题装进
    与圆点等高的行盒。所以改 ``dot_size`` 轴线也不会歪。

.. note::
    flet 没有"边框虚线"，也未提供步骤条原生控件，连接线由两侧 ``expand`` 的
    半段线拼成 —— 圆点因此在格心，改步骤数量也不会跑偏。

用法::

    Step(
        steps=[
            StepItem("填写信息", "账号与联系方式"),
            StepItem("验证邮箱", "点击邮件里的链接"),
            StepItem("完成", "开始使用"),
        ],
        active=1,
    )
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import flet as ft

from ui.core.doc import Api, Example, Spec, info, run, tip
from ui.core.tokens import FONT_SIZE

__all__ = ["Step", "StepItem"]

# ---------------------------------------------------------------------------
# 尺寸
# ---------------------------------------------------------------------------
DOT = 26  # 圆点直径
DOT_SMALL = 22  # 简洁模式的序号徽章
LINE = 2  # 连接线粗细

TITLE_SIZE = FONT_SIZE["body"]  # 14
DESC_SIZE = FONT_SIZE["small"]  # 12
TEXT_GAP = 10  # 圆点行与标题的间距
DESC_GAP = 3  # 标题与描述的间距

ROW_GAP = 20  # 垂直模式每步的下边距
RAIL_GAP = 12  # 垂直模式轴轨与文字的间距

MUTED = ft.Colors.ON_SURFACE_VARIANT
HIDDEN = ft.Colors.TRANSPARENT

#: 步骤状态：``wait`` 未开始 / ``process`` 进行中 / ``finish`` 已完成 / ``error`` 出错。
STATUSES = ("wait", "process", "finish", "error")
STATUS_ALIASES = {"fail": "error", "success": "finish"}

#: 状态 → 文字色（``finish`` 落回常规前景色）。
TEXT_COLORS: dict[str, ft.ColorValue] = {
    "process": ft.Colors.PRIMARY,
    "error": ft.Colors.ERROR,
    "wait": ft.Colors.OUTLINE,
}


@dataclass
class StepItem:
    """一个步骤。

    Args:
        title: 步骤标题（一句话说清这一步做什么）。
        description: 次要说明，显示在标题下方。
        icon: 圆点里的图标。不给时按状态自动取：已完成对勾、出错叉、其余用序号。
        status: 钉死该步状态（``wait`` / ``process`` / ``finish`` / ``error``，
            也接受 ``fail`` / ``success``），不给则跟随 :attr:`Step.active` 推导。
    """

    title: str
    description: str = ""
    icon: ft.IconData | None = None
    status: str | None = None


@ft.control
class Step(ft.Container):
    """步骤条，继承自 :class:`flet.Container`。

    Args:
        steps: :class:`StepItem` 列表，也接受 ``{"title": ..., "description": ...}``
            这种字典写法。
        active: 当前进行到第几步（从 0 开始）；``-1`` 表示一步都没开始。
        direction: ``horizontal``（默认）或 ``vertical``。
        process_status: 当前步的状态，默认 ``process``；想让当前步报错就给 ``error``。
        finish_status: 当前步之前那些步的状态，默认 ``finish``。
        align_center: 横向模式文字是否居中（默认 ``True``）；``False`` 时左对齐。
        simple: 简洁模式 —— 一行序号 + 标题，步骤间用 ``›`` 分隔。
        clickable: 整步可点（触发 :attr:`on_change`）；简洁模式默认开启。
        on_change: 点击回调，参数是被点中的步骤下标。
        dot_size: 圆点直径，默认 26。
    """

    steps: list[StepItem | dict[str, Any]] = field(default_factory=list)
    active: int = 0
    direction: str = "horizontal"
    process_status: str = "process"
    finish_status: str = "finish"
    align_center: bool = True
    simple: bool = False
    clickable: bool = False
    on_change: Callable[[int], None] | None = None
    dot_size: int = DOT

    def init(self):
        self._items: list[StepItem] = [_as_item(s) for s in self.steps]
        self.content = self._build()

    # ------------------------------------------------------------------
    # 状态推导
    # ------------------------------------------------------------------
    @property
    def _current(self) -> int:
        """当前步下标，自动夹在 ``[-1, len-1]`` 内。"""
        if not self._items:
            return -1
        return max(-1, min(self.active, len(self._items) - 1))

    @property
    def _centered(self) -> bool:
        """文字是否居中 —— 只有横向平铺才居中；垂直轴轨和简洁模式一律左对齐。"""
        return self.align_center and not self.simple and self.direction != "vertical"

    def _status(self, index: int) -> str:
        """该步状态：显式 ``status`` 优先，否则按与 active 的位置关系推导。"""
        pinned = _norm_status(self._items[index].status)
        if pinned is not None:
            return pinned
        current = self._current
        if index < current:
            return _norm_status(self.finish_status) or "finish"
        if index == current:
            return _norm_status(self.process_status) or "process"
        return "wait"

    def _line_color(self, segment: int) -> ft.ColorValue | None:
        """第 ``segment`` 段（连接 ``segment-1`` 与 ``segment``）的颜色。

        ``None`` 表示这一段不存在 —— 首步左边、末步右边都该空着，但**占位宽度
        要留着**，否则圆点会往一侧偏。已经走过的段用主色，其余灰。
        """
        if segment <= 0 or segment >= len(self._items):
            return None
        return (
            ft.Colors.PRIMARY if self._current >= segment else ft.Colors.OUTLINE_VARIANT
        )

    def _seg(self, segment: int) -> ft.Control:
        """横向的一段连接线（永远占位，只是可能透明）。"""
        return ft.Container(
            expand=True,
            height=LINE,
            bgcolor=self._line_color(segment) or HIDDEN,
        )

    # ------------------------------------------------------------------
    # 圆点
    # ------------------------------------------------------------------
    def _dot(self, index: int, status: str, side: float | None = None) -> ft.Control:
        """圆点 / 徽章：``finish`` 实心、``process`` 淡底描边、``error`` 实心红、``wait`` 灰描边。"""
        size = side or self.dot_size
        item = self._items[index]
        icon = item.icon or _default_icon(status)
        radius = ft.BorderRadius.all(size / 2)
        common = {"width": size, "height": size, "border_radius": radius}

        if status in ("finish", "error"):
            return ft.Container(
                **common,
                bgcolor=(ft.Colors.PRIMARY if status == "finish" else ft.Colors.ERROR),
                alignment=ft.Alignment.CENTER,
                content=_glyph(icon, size, index, ft.Colors.ON_PRIMARY),
            )
        if status == "process":
            return ft.Container(
                **common,
                border=ft.Border.all(LINE, ft.Colors.PRIMARY),
                bgcolor=ft.Colors.with_opacity(0.10, ft.Colors.PRIMARY),
                alignment=ft.Alignment.CENTER,
                content=_glyph(icon, size, index, ft.Colors.PRIMARY),
            )
        return ft.Container(
            **common,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            alignment=ft.Alignment.CENTER,
            content=_glyph(icon, size, index, ft.Colors.OUTLINE),
        )

    # ------------------------------------------------------------------
    # 文字
    # ------------------------------------------------------------------
    def _title(self, index: int, status: str, *, boxed: bool = False) -> ft.Control:
        """标题。``boxed`` 用于垂直模式：塞进与圆点等高的行盒，与圆点对中。"""
        text = ft.Text(
            self._items[index].title,
            size=TITLE_SIZE,
            weight=(ft.FontWeight.W_600 if status in ("process", "finish") else None),
            color=TEXT_COLORS.get(status, ft.Colors.ON_SURFACE),
            text_align=ft.TextAlign.CENTER if self._centered else ft.TextAlign.LEFT,
            no_wrap=True,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        if boxed:
            return ft.Container(
                height=self.dot_size,
                alignment=ft.Alignment.CENTER_LEFT,
                content=text,
            )
        return ft.Container(
            alignment=(
                ft.Alignment.CENTER if self._centered else ft.Alignment.CENTER_LEFT
            ),
            content=text,
        )

    def _desc(self, index: int) -> ft.Control | None:
        """描述文字；空描述返回 ``None``（调用方直接跳过）。"""
        desc = self._items[index].description
        if not desc:
            return None
        return ft.Container(
            alignment=(
                ft.Alignment.CENTER if self._centered else ft.Alignment.CENTER_LEFT
            ),
            content=ft.Text(
                desc,
                size=DESC_SIZE,
                color=MUTED,
                text_align=ft.TextAlign.CENTER if self._centered else ft.TextAlign.LEFT,
                max_lines=2,
                overflow=ft.TextOverflow.ELLIPSIS,
            ),
        )

    # ------------------------------------------------------------------
    # 三种布局
    # ------------------------------------------------------------------
    def _build(self) -> ft.Control:
        if not self._items:
            return ft.Row()
        if self.simple:
            return self._simple_row()
        if self.direction == "vertical":
            return self._vertical()
        return self._horizontal()

    def _horizontal(self) -> ft.Control:
        """横向：每步等宽，圆点在格心，相邻两半线拼成连续的一条。"""
        cells: list[ft.Control] = []
        for index in range(len(self._items)):
            status = self._status(index)
            head = ft.Row(
                spacing=0,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    self._seg(index),
                    self._dot(index, status),
                    self._seg(index + 1),
                ],
            )
            cells.append(
                self._cell(
                    index,
                    ft.Column(
                        spacing=TEXT_GAP,
                        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                        controls=[
                            c
                            for c in (
                                head,
                                self._title(index, status),
                                self._desc(index),
                            )
                            if c is not None
                        ],
                    ),
                )
            )
        return ft.Row(
            spacing=0,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=cells,
        )

    def _vertical(self) -> ft.Control:
        """垂直：左侧一条轴轨，圆点与标题首行居中对齐。"""
        rows: list[ft.Control] = []
        last = len(self._items) - 1
        for index in range(len(self._items)):
            status = self._status(index)
            side = self.dot_size
            rail = ft.Stack(
                width=side,
                controls=[
                    # 轴轨按圆点拆成两段：以上是「进入这一步」的那一段，以下是
                    # 「离开」的那一段。整条同色会让当前步上方的线提前变灰，
                    # 和横向模式画出来的进度对不上。
                    ft.Container(
                        left=(side - LINE) / 2,
                        top=0,
                        height=side / 2,
                        width=LINE,
                        bgcolor=self._line_color(index) or HIDDEN,
                    ),
                    ft.Container(
                        left=(side - LINE) / 2,
                        top=side / 2,
                        bottom=0,
                        width=LINE,
                        bgcolor=self._line_color(index + 1) or HIDDEN,
                    ),
                    ft.Container(
                        left=0,
                        top=0,
                        width=side,
                        height=side,
                        alignment=ft.Alignment.CENTER,
                        content=self._dot(index, status),
                    ),
                ],
            )
            body = ft.Container(
                expand=True,
                padding=ft.Padding.only(
                    left=RAIL_GAP, bottom=0 if index == last else ROW_GAP
                ),
                content=ft.Column(
                    spacing=DESC_GAP,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                    controls=[
                        c
                        for c in (
                            self._title(index, status, boxed=True),
                            self._desc(index),
                        )
                        if c is not None
                    ],
                ),
            )
            self._make_hot(index, body)
            rows.append(
                ft.Row(
                    spacing=0,
                    # intrinsic_height + STRETCH：轴轨 Stack 的固有高度是 0，
                    # 先按内容量出整行高度再把轴轨拉满；少了它整行会炸到无界高。
                    intrinsic_height=True,
                    vertical_alignment=ft.CrossAxisAlignment.STRETCH,
                    controls=[rail, body],
                )
            )
        return ft.Column(spacing=0, controls=rows)

    def _simple_row(self) -> ft.Control:
        """简洁模式：``① 标题 › ② 标题``，当前步高亮，整块可点。"""
        cells: list[ft.Control] = []
        for index in range(len(self._items)):
            status = self._status(index)
            chip = ft.Container(
                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                border_radius=8,
                content=ft.Row(
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        self._dot(index, status, side=DOT_SMALL),
                        ft.Text(
                            self._items[index].title,
                            size=TITLE_SIZE,
                            weight=(
                                ft.FontWeight.W_600
                                if status in ("process", "finish")
                                else None
                            ),
                            color=TEXT_COLORS.get(status, ft.Colors.ON_SURFACE),
                            no_wrap=True,
                        ),
                    ],
                ),
            )
            cells.append(self._make_hot(index, chip))
            if index < len(self._items) - 1:
                cells.append(
                    ft.Icon(
                        ft.Icons.CHEVRON_RIGHT,
                        size=16,
                        color=ft.Colors.OUTLINE_VARIANT,
                    )
                )
        # 不用 ``wrap``：Row 交给 Flutter 的是 Wrap，宽度约束是 loose 时会塌成
        # "一项一行"。步骤条本就该是一行，放不下时横向滚动更符合桌面直觉。
        return ft.Row(
            spacing=2,
            scroll=ft.ScrollMode.AUTO,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=cells,
        )

    # ------------------------------------------------------------------
    # 交互
    # ------------------------------------------------------------------
    def _interactive(self) -> bool:
        return bool(self.simple or self.clickable) and self.on_change is not None

    def _make_hot(self, index: int, box: ft.Container) -> ft.Container:
        """把一个已经定好尺寸的容器就地变成点击热区（不再套壳 —— 套壳会打断 flex）。"""
        if not self._interactive():
            return box
        # 水波纹与悬停高亮交给 Material ink，不需要 Python 侧重绘。
        box.ink = True
        box.ink_color = ft.Colors.with_opacity(0.06, ft.Colors.PRIMARY)
        box.on_click = lambda _e, i=index: self._select(i)
        return box

    def _cell(self, index: int, content: ft.Control) -> ft.Container:
        """横向的一格：本身是 Row 的 flex 子项（``expand``），所以整格等宽。

        横向不留内边距 —— 相邻两格各自的半段线要严丝合缝地对上，
        留一点缝就会露出断口。
        """
        box = ft.Container(
            expand=True,
            padding=ft.Padding.only(top=4, bottom=8),
            border_radius=8,
            content=content,
        )
        return self._make_hot(index, box)

    def _select(self, index: int) -> None:
        """点击某一步：就地更新 ``active`` 再回调，反馈与状态源都不落空。"""
        if index == self._current:
            return
        self.active = index
        try:
            self.content = self._build()
            self.update()
        except Exception:  # noqa: BLE001, S110 - 尚未挂到页面时只回调，不刷新
            pass
        if self.on_change is not None:
            self.on_change(index)


# ---------------------------------------------------------------------------
# 小工具
# ---------------------------------------------------------------------------
def _as_item(raw: StepItem | dict[str, Any]) -> StepItem:
    return raw if isinstance(raw, StepItem) else StepItem(**raw)


def _norm_status(value: str | None) -> str | None:
    """归一状态名：``fail`` → ``error``、``success`` → ``finish``；非法返回 ``None``。"""
    if not value:
        return None
    name = STATUS_ALIASES.get(value, value)
    return name if name in STATUSES else None


def _default_icon(status: str) -> ft.IconData | None:
    if status == "finish":
        return ft.Icons.CHECK
    if status == "error":
        return ft.Icons.CLOSE
    return None


def _glyph(
    icon: ft.IconData | None, side: float, index: int, color: ft.ColorValue
) -> ft.Control:
    """圆点内容：有图标画图标，没有就画序号（从 1 开始）。"""
    if icon is not None:
        return ft.Icon(icon, size=side * 0.54, color=color)
    return ft.Text(
        str(index + 1),
        size=max(12.0, side * 0.46),
        weight=ft.FontWeight.W_600,
        color=color,
    )


# ---------------------------------------------------------------------------
# 示例（也是本组件的视觉验收页）
# ---------------------------------------------------------------------------
_MUTED = ft.Colors.ON_SURFACE_VARIANT


def _echo(active: int, steps: tuple[StepItem, ...]) -> ft.Control:
    """把当前步读出来 —— 步骤条是受控的，它只画「第几步」，流程归调用方。"""
    index = min(max(active, 0), len(steps) - 1)
    return ft.Text(
        f"active = {active} · 第 {index + 1} 步「{steps[index].title}」",
        size=FONT_SIZE["small"],
        color=_MUTED,
    )


_STEPS = (
    StepItem("填写信息", "账号与联系方式"),
    StepItem("验证邮箱", "点击邮件里的链接"),
    StepItem("设置偏好", "语言、时区与通知"),
    StepItem("完成", "开始使用"),
)


@ft.component
def _basic() -> ft.Control:
    """横向四步：已完成打勾，当前步高亮，点哪步跳哪步。"""
    active, set_active = ft.use_state(1)
    return ft.Column(
        spacing=16,
        controls=[
            Step(
                steps=list(_STEPS),
                active=active,
                clickable=True,
                on_change=set_active,
            ),
            _echo(active, _STEPS),
        ],
    )


_VERTICAL_STEPS = (
    StepItem("准备镜像", "约 1.2 GB，走内网仓库"),
    StepItem("构建容器", "缓存命中时约 30 秒"),
    StepItem("推送镜像", "推送到 registry.example"),
    StepItem("滚动更新", "每批 2 个实例，失败自动回滚"),
)


@ft.component
def _vertical() -> ft.Control:
    """竖向：左侧一条轴轨，描述跟在标题下面。"""
    active, set_active = ft.use_state(1)
    return ft.Column(
        spacing=12,
        controls=[
            ft.Container(
                width=360,
                content=Step(
                    steps=list(_VERTICAL_STEPS),
                    active=active,
                    direction="vertical",
                    clickable=True,
                    on_change=set_active,
                ),
            ),
            _echo(active, _VERTICAL_STEPS),
        ],
    )


@ft.component
def _simple_and_error() -> ft.Control:
    """简洁模式收成一行；出错态把当前步换成红色叉。"""
    active, set_active = ft.use_state(2)
    return ft.Column(
        spacing=12,
        controls=[
            ft.Text(
                "simple：一行装下整条流程，适合放进工具栏",
                size=FONT_SIZE["small"],
                color=_MUTED,
            ),
            Step(steps=list(_STEPS), active=active, simple=True, on_change=set_active),
            ft.Text(
                "error：第 3 步失败，前面的步骤仍然算已完成",
                size=FONT_SIZE["small"],
                color=_MUTED,
            ),
            Step(
                steps=[
                    StepItem("校验文件"),
                    StepItem("上传"),
                    StepItem("写入", "磁盘已满", status="error"),
                    StepItem("完成"),
                ],
                active=2,
            ),
        ],
    )


_BASIC_CODE = """@ft.component
def Wizard():
    active, set_active = ft.use_state(1)
    return Step(
        steps=[
            StepItem("填写信息", "账号与联系方式"),
            StepItem("验证邮箱", "点击邮件里的链接"),
            StepItem("完成", "开始使用"),
        ],
        active=active,        # 下标小于它的步骤自动打勾
        clickable=True,       # 整步可点，回调给下标
        on_change=set_active,
    )"""

_VERTICAL_CODE = """Step(
    steps=[StepItem("准备镜像", "约 1.2 GB"), StepItem("构建容器", "约 30 秒")],
    active=0,
    direction="vertical",
    clickable=True,
    on_change=lambda index: print(index),
)"""

SPEC = Spec(
    name="Step",
    summary="把一件事拆成几步，并指出现在走到第几步。",
    definition=(
        "步骤条把有先后顺序的流程摊平：一步一个圆点，圆点之间用线连起来，颜色走过哪段就"
        "算到哪段。状态只有四种 —— 未开始、进行中、已完成、出错，默认按 active 的位置推导，"
        "也可以在单步上钉死。横向用于页头，竖向用于侧栏，简洁模式收成一行放进工具栏。"
    ),
    anatomy=[
        (
            "圆点",
            (
                "26px。进行中是淡主色底 + 主色描边，已完成主色实底 + 对勾，"
                "出错实底红 + 叉，未开始灰描边 + 序号。"
            ),
        ),
        (
            "连接线",
            (
                "2px。走过的段用主色，没走到的是 OUTLINE_VARIANT；"
                "首尾两端留空占位，圆点才不会偏向一侧。"
            ),
        ),
        (
            "标题",
            "当前步与已完成加粗，进行中转主色、出错转红；横向超长省略，不折行。",
        ),
        ("描述", "标题下方 12px 次要色，最多两行 —— 再多就把步骤条撑成正文了。"),
        (
            "序号与图标",
            "没给自定义图标时画 1、2、3；已完成与出错改用对勾 / 叉，避免和序号混着看。",
        ),
    ],
    when=[
        "注册、下单、部署这类有明确先后顺序的多步流程",
        "需要让用户知道「还剩几步」，而不只是「正在等」",
        "提交之后展示处理链路：校验 → 排队 → 执行 → 完成",
    ],
    avoid=[
        "只是并列的几个视图：用 Tabs，步骤条会让人以为其中有依赖关系",
        "回答「我在哪一层」：用面包屑，步骤条表达的是进度不是层级",
        "只有两步：一个按钮或一句说明更直接，两条连线的仪式感大于信息量",
    ],
    examples=[
        Example(
            "基础用法",
            _basic,
            hint="四步流程停在第 2 步；点任意一步即可跳转，state 跟着回写。",
            code=_BASIC_CODE,
        ),
        Example(
            "竖向",
            _vertical,
            hint="左侧一条轴轨，圆点与标题首行居中对齐；描述最多两行。",
            code=_VERTICAL_CODE,
        ),
        Example(
            "简洁模式与出错",
            _simple_and_error,
            hint="simple 收成一行「① 标题 › ② 标题」；第二条把第 3 步钉成 error。",
        ),
    ],
    api=[
        Api(
            "steps",
            "list[StepItem | dict]",
            "[]",
            '步骤列表；也接受 {"title": ...} 的字典写法',
        ),
        Api("active", "int", "0", "当前步下标（0 起）；-1 表示一步都没开始"),
        Api(
            "direction",
            "str",
            '"horizontal"',
            "horizontal 横向平铺 / vertical 左侧轴轨",
        ),
        Api("process_status", "str", '"process"', "当前步的状态；想报错就传 error"),
        Api("finish_status", "str", '"finish"', "当前步之前那些步的状态"),
        Api("align_center", "bool", "True", "横向时标题居中；竖向与简洁模式始终左对齐"),
        Api("simple", "bool", "False", "简洁模式：一行序号 + 标题，用 › 分隔"),
        Api(
            "clickable",
            "bool",
            "False",
            "整步可点；简洁模式下默认就是可点的（仍需接 on_change）",
        ),
        Api(
            "on_change",
            "Callable[[int], None] | None",
            "None",
            "点击回调，参数是被点中的下标",
        ),
        Api("dot_size", "int", "26", "圆点直径；改它轴轨仍与圆点对齐"),
    ],
    notes=[
        tip(
            "点击时组件会先就地改 active 再回调。放进 @ft.component 的树里时控件是冻结的，"
            "就地刷新会静默失败 —— 请用 on_change 回写状态让父组件重绘，示例都是这么写的。"
        ),
        info(
            "竖向轴轨按圆点拆成上下两段：以上属于「进入这一步」的那段、以下属于「离开」"
            "的那段。整条同色会让当前步上方的线提前变灰，和横向模式对不上。"
        ),
        info(
            "StepItem.status 钉死的状态优先于 active 推导，适合「流程停在第 3 步、但第 2 步"
            "其实已经失败」这种真实场景。"
        ),
    ],
    tags=("步骤", "步骤条", "流程", "steps", "wizard"),
)


if __name__ == "__main__":
    run(SPEC)
