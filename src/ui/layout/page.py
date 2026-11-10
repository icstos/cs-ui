"""页面布局容器 (PageLayout)。

把一个页面的内容统一收敛到「页头 + 可滚动的内容列」的标准骨架，避免每个页面
重复书写 padding / spacing / scroll。侧栏与页脚不在它里面 —— 那是外壳的事，
套一层 Row / Column 就好。

.. note::
   这里刻意命名为 ``PageLayout`` 而非 ``Page``，以免在 ``from ui import *``
   时覆盖 Flet 原生的 :class:`flet.Page`。

用法::

    PageLayout(
        title="用户管理",
        subtitle="管理系统用户、角色与权限",
        controls=[user_table, Pagination(...)],
    )
"""

from __future__ import annotations

from dataclasses import field

import flet as ft

from ui.core.doc import Api, Example, Spec, info, run, tip, warn
from ui.core.responsive import size_class, viewport
from ui.core.tokens import (
    CONTENT_MAX,
    FONT_SIZE,
    FONT_WEIGHT,
    PAGE_PAD,
    RADIUS,
    SPACE,
    overlay,
)

__all__ = ["PageLayout"]

#: 页头字号：标题走 headline 档，副标题与正文同号。
TITLE_SIZE = FONT_SIZE["headline"]
SUBTITLE_SIZE = FONT_SIZE["body"]


@ft.control
class PageLayout(ft.Container):
    """标准页面骨架容器，继承自 :class:`flet.Container`。

    Args:
        controls: 页面内容控件列表。
        title: 页面标题，为空则不渲染标题区。
        subtitle: 页面副标题。
        actions: 标题右侧的操作区控件（如按钮）；**窄窗口自动折到标题下方**。
        padding: 页面内边距；``None``（默认）表示跟着窗口档位走
            （16 / 24 / 32，见 :data:`~ui.core.tokens.PAGE_PAD`）。
        max_content_width: 内容最大宽度 —— ``"reading"``（720）/ ``"content"``（1120）/
            ``"wide"``（1440）/ 具体像素。``None`` 表示不限宽。窄窗口下自动失效。
        spacing: 内容间距，默认 12。
        scroll: 滚动模式，默认 ``AUTO``；传 ``None`` 关闭滚动。
        horizontal_alignment: 内容水平对齐方式。
        bgcolor: 页面背景色。

    Notes:
        响应式只做三件事，且**都不重建内容**：换内边距、按上限居中、窄屏把页头
        操作折到第二行。跨档时才执行一次（拖动窗口的过程中不参与），
        所以它不会成为滚动与拖拽的负担。这些都在 ``init`` 与 ``on_size_change``
        里完成 —— 因此组件树（冻结）中它是静态的，见 ``SPEC`` 里的 warn。
    """

    controls: list[ft.Control] = field(default_factory=list)
    title: str = ""
    subtitle: str = ""
    actions: list[ft.Control] = field(default_factory=list)
    padding: ft.PaddingValue | None = None
    max_content_width: int | str | None = None
    spacing: int = SPACE["3"]
    scroll: ft.ScrollMode | None = ft.ScrollMode.AUTO
    horizontal_alignment: ft.CrossAxisAlignment = ft.CrossAxisAlignment.START
    bgcolor: ft.ColorValue = ft.Colors.TRANSPARENT

    # ---- 运行时状态（不属于公开 API） ----
    #
    # 注意：这些**不能写成带类型注解的字段**。``@ft.control`` 会把它变成 dataclass
    # 字段，而 flet 序列化时会遍历所有 ``ft.Control`` 类型的字段 —— 于是 ``_column``
    # 会被当成 PageLayout 的另一个子控件，和 ``content`` 里那一份**各挂一次**。
    # 之后对 ``_column`` 调 update()，补丁会打到客户端那份看不见的副本上：
    # 对象状态全对、界面纹丝不动。不带注解的类属性不参与 dataclass，也就不会被序列化。
    _column = None  # ft.Column | None
    _header = None  # ft.Control | None
    _centered = False
    _pad_user = None  # ft.PaddingValue | None
    _cls = "expanded"
    _header_compact = False
    _width = None  # float | None
    _limit_applied = None  # int | None

    def init(self):
        if self.expand is None:
            self.expand = True

        # 初始档位只能先按窗口猜一次：控件此刻还没量过，首个 on_size_change 会纠正它。
        self._cls = size_class(viewport().width)

        body: list[ft.Control] = []
        self._header_compact = self._header_shape()
        self._header = self._build_header()
        if self._header is not None:
            body.append(self._header)
        body.extend(self.controls)

        self._column = ft.Column(
            controls=body,
            spacing=self.spacing,
            scroll=self.scroll,
            horizontal_alignment=self.horizontal_alignment,
            expand=True,
        )
        # 用户显式给的内边距要留住 —— 否则第二次计算时会把自己的结果当成"显式值"。
        self._pad_user = self.padding
        self.padding = self._pad()

        # 限宽只在**要求**限宽时才套一层 Row：不需要的页面不该多一次布局。
        # 结构在构建期定死，运行期只改里面那个 Container 的宽度 —— 换档不重挂子树。
        if self.max_content_width is not None:
            self._limit_applied = self._limit()
            self.content = ft.Row(
                expand=True,
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.STRETCH,
                controls=[
                    ft.Container(width=self._limit_applied, content=self._column)
                ],
            )
            self._centered = True
        else:
            self.content = self._column

        # 量**自己**的宽度，不看窗口：PageLayout 可能放在侧栏、分栏、对话框里，
        # 那些场景下"窗口很宽"与"我很窄"同时成立，按窗口判断必然错。
        self.on_size_change = self._on_self_size

    # ------------------------------------------------------------------
    # 响应式
    # ------------------------------------------------------------------
    def _on_self_size(self, e: ft.LayoutSizeChangeEvent) -> None:
        """自身宽度变了：跨档就换内边距与页头排布，限宽则每 8px 跟一次。

        限宽必须跟着**实际宽度**走，不能只在跨档时算一次：容器从 1200 收到 900
        仍属同一档，若宽度还钉在 1120，内容就会溢出被裁掉。所以这里按 8px 量化 ——
        一整段拖动只触发上百次属性更新，而不是每像素一次。

        在 ``@ft.component`` 渲染出的**冻结树**里，这里的每一次赋值都会被 flet
        拒绝（``Frozen controls cannot be updated``），连 ``update()`` 也调不动。
        那种场景下的响应式要走 ``use_responsive()`` + 整页重渲染（档位一变重新
        构建页面），所以这里直接返回：初始值来自 ``init()`` 时的档位，页面照常渲染。
        """
        if self._column is None or hasattr(self, "_frozen"):
            return
        width = getattr(e, "width", None)
        self._width = width
        cls = size_class(width)

        if cls != self._cls:
            self._cls = cls
            self.padding = self._pad()
            # 只有**形态真的变了**才重建页头（紧凑 ↔ 非紧凑）。同一形态只是宽度
            # 不同时重建毫无意义，而且白送一次结构补丁 —— 那是最贵也最容易出事
            # 的一种更新（见 ``_swap_header`` 的说明）。
            if self._header_shape() != self._header_compact:
                self._swap_header()
            self.update()

        if not self._centered:
            return
        limit = self._limit()
        if limit is None or limit == self._limit_applied:
            return
        self._limit_applied = limit
        inner = self.content.controls[0] if self.content is not None else None
        if isinstance(inner, ft.Container):
            inner.width = limit
            self.update()

    def _header_shape(self) -> bool:
        """页头是不是"紧凑形态"（操作折到第二行）。没有操作时两种形态一样。"""
        return self._cls == "compact" and bool(self.actions)

    def _swap_header(self) -> None:
        """换掉页头那一格。

        只动 ``controls[0]`` 这一格、不做整列重建：列表按格替换是 flet 补丁里
        最稳的一种（新增/删除整棵子树时，客户端会在布局过程中重挂，容易把整帧
        卡住）。代价是这一格必须"一格换一格"。
        """
        header = self._build_header()
        if header is None or self._header is None:
            return
        self._header_compact = self._header_shape()
        self._column.controls[0] = header
        self._header = header
        self._column.update()

    def _hpad(self) -> int:
        """左右内边距之和。``padding`` 允许是 int / Padding / 字符串，都得认。"""
        pad = self._pad()
        if isinstance(pad, (int, float)):
            return int(pad) * 2
        if isinstance(pad, ft.Padding):
            return int(pad.left or 0) + int(pad.right or 0)
        return 0

    def _pad(self) -> ft.PaddingValue:
        """内边距：显式给了就照给的，否则按档位取。"""
        if self._pad_user is not None:
            return self._pad_user
        return ft.Padding.all(PAGE_PAD[self._cls])

    def _limit(self) -> int | None:
        """内容宽度：不超过 ``max_content_width``，也不超过自己装得下的宽度。

        两件事一次做完：宽屏居中限宽（``cap`` 生效），窄屏自然铺满
        （``cap`` 被可用宽度压住）。所以"窄容器上自动失效"不是特判，
        是 min() 的必然结果 —— 也就不会出现"宽度钉死、内容溢出"。
        """
        value = self.max_content_width
        if value is None:
            return None
        cap = (
            CONTENT_MAX.get(value.strip().lower())
            if isinstance(value, str)
            else int(value)
        )
        if cap is None:
            return None
        if self._width is None:
            return cap
        avail = int(max(0, self._width - self._hpad()))
        # 8px 量化：一整段拖动只改上百次，而不是每像素一次。
        return max(8, min(int(cap), avail) // 8 * 8)

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _build_header(self) -> ft.Control | None:
        """构建标题区；无标题且无操作按钮时返回 None。"""
        has_title = bool(self.title or self.subtitle)
        if not has_title and not self.actions:
            return None

        left: list[ft.Control] = []
        if self.title:
            # 页头只允许一行：标题变长时该省略，而不是把右侧操作挤出屏幕，
            # 或者把页头撑成三行、把内容整体往下推。
            left.append(
                ft.Text(
                    self.title,
                    size=TITLE_SIZE,
                    weight=FONT_WEIGHT["bold"],
                    no_wrap=True,
                    overflow=ft.TextOverflow.ELLIPSIS,
                )
            )
        if self.subtitle:
            left.append(
                ft.Text(
                    self.subtitle,
                    size=SUBTITLE_SIZE,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                    no_wrap=True,
                    overflow=ft.TextOverflow.ELLIPSIS,
                )
            )

        compact = self._cls == "compact"
        title_block = ft.Column(controls=left, spacing=2, expand=not compact)
        if compact and self.actions:
            # 窄窗口：操作折到标题下方一行。挤在同一行里，要么标题被压成省略号、
            # 要么按钮被裁掉一半 —— 都不如换行体面。
            return ft.Column(
                spacing=SPACE["2"],
                controls=[
                    title_block,
                    ft.Row(
                        controls=list(self.actions),
                        wrap=True,
                        spacing=SPACE["2"],
                        run_spacing=SPACE["2"],
                    ),
                ],
            )

        return ft.Row(
            controls=[title_block, *self.actions],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=SPACE["3"],
        )


# ---------------------------------------------------------------------------
# 示例（也是本组件的视觉验收页）
# ---------------------------------------------------------------------------
_MUTED = ft.Colors.ON_SURFACE_VARIANT


def _frame(
    content: ft.Control, *, height: int | None = None, width: int | None = None
) -> ft.Container:
    """给示例裹一圈「窗口」：PageLayout 默认 expand，需要父级给边界。"""
    return ft.Container(
        height=height,
        width=width,
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        border_radius=RADIUS["lg"],
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        content=content,
    )


def _stat(label: str, value: str, color: ft.ColorValue) -> ft.Control:
    return ft.Container(
        padding=SPACE["4"],
        border_radius=RADIUS["lg"],
        bgcolor=ft.Colors.SURFACE,
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        content=ft.Column(
            spacing=2,
            controls=[
                ft.Text(
                    value,
                    size=FONT_SIZE["headline"],
                    weight=FONT_WEIGHT["bold"],
                    color=color,
                ),
                ft.Text(label, size=FONT_SIZE["small"], color=_MUTED),
            ],
        ),
    )


def _chip(text: str) -> ft.Control:
    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=10, vertical=4),
        border_radius=RADIUS["full"],
        bgcolor=overlay(0.06),
        content=ft.Text(text, size=FONT_SIZE["small"], color=_MUTED),
    )


@ft.component
def _basic() -> ft.Control:
    """最常用的一段：页头 + 操作 + 内容列。"""
    return _frame(
        height=350,
        content=PageLayout(
            title="用户管理",
            subtitle="管理系统用户、角色与权限",
            actions=[
                ft.Button("导出"),
                ft.Button("新建用户", icon=ft.Icons.ADD),
            ],
            controls=[
                ft.Row(
                    wrap=True,
                    spacing=SPACE["3"],
                    run_spacing=SPACE["3"],
                    controls=[
                        _stat("总用户", "1,286", ft.Colors.PRIMARY),
                        _stat("活跃用户", "942", ft.Colors.TERTIARY),
                        _stat("待审核", "37", ft.Colors.SECONDARY),
                    ],
                ),
                ft.Divider(),
                ft.Text(
                    "最近登录",
                    size=FONT_SIZE["body"],
                    weight=FONT_WEIGHT["semibold"],
                ),
                ft.ListTile(
                    title=ft.Text("内边距与间距只写一次"),
                    subtitle=ft.Text("每个页面不用再各自设 padding / spacing"),
                ),
                ft.ListTile(
                    title=ft.Text("内容超长自动滚动"),
                    subtitle=ft.Text("scroll 默认 AUTO，要固定页头时传 None 自己接管"),
                ),
            ],
        ),
    )


_SIDE_ITEMS = ("总览", "用户", "角色", "审计日志")


def _sidebar() -> ft.Control:
    return ft.Column(
        spacing=2,
        controls=[
            ft.Container(
                padding=ft.Padding.only(
                    left=SPACE["4"], top=SPACE["4"], bottom=SPACE["2"]
                ),
                content=ft.Text(
                    "侧栏",
                    size=FONT_SIZE["caption"],
                    weight=FONT_WEIGHT["semibold"],
                    color=_MUTED,
                ),
            ),
            *[
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=SPACE["4"], vertical=8),
                    border_radius=RADIUS["sm"],
                    bgcolor=overlay(0.08) if name == "用户" else None,
                    content=ft.Text(
                        name,
                        size=FONT_SIZE["body"],
                        color=ft.Colors.PRIMARY
                        if name == "用户"
                        else ft.Colors.ON_SURFACE,
                    ),
                )
                for name in _SIDE_ITEMS
            ],
        ],
    )


@ft.component
def _skeleton() -> ft.Control:
    """完整骨架：侧栏 + 页头 + 内容 + 页脚，侧栏可折叠对比。"""
    collapsed, set_collapsed = ft.use_state(False)

    inner = ft.Container(
        expand=True,
        bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
        content=PageLayout(
            title="用户管理",
            subtitle="页头由 PageLayout 出，侧栏与页脚在外面拼",
            actions=[
                ft.IconButton(
                    icon=ft.Icons.CHEVRON_LEFT
                    if not collapsed
                    else ft.Icons.CHEVRON_RIGHT,
                    icon_size=18,
                    tooltip="收起侧栏" if not collapsed else "展开侧栏",
                    on_click=lambda _e: set_collapsed(not collapsed),
                )
            ],
            controls=[
                ft.Text(
                    "内容区：表格、图表、表单都放这里，滚动由 PageLayout 负责。",
                    size=FONT_SIZE["body"],
                ),
                ft.Divider(),
                ft.Text(
                    "侧栏宽度从 164 收到 0，页头与内容自动补位 —— 它们本来就是兄弟关系。",
                    size=FONT_SIZE["body"],
                    color=_MUTED,
                ),
            ],
        ),
    )

    frame = _frame(
        height=380,
        content=ft.Column(
            spacing=0,
            controls=[
                ft.Row(
                    expand=True,
                    spacing=0,
                    controls=[
                        ft.Container(
                            width=0 if collapsed else 164,
                            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
                            border=(
                                ft.Border(
                                    right=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)
                                )
                                if not collapsed
                                else None
                            ),
                            content=None if collapsed else _sidebar(),
                        ),
                        inner,
                    ],
                ),
                ft.Container(
                    height=36,
                    padding=ft.Padding.symmetric(horizontal=SPACE["4"]),
                    bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
                    border=ft.Border(top=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
                    alignment=ft.Alignment.CENTER_LEFT,
                    content=ft.Text(
                        "页脚：拼在 PageLayout 外面，才不会跟着内容滚走",
                        size=FONT_SIZE["small"],
                        color=_MUTED,
                    ),
                ),
            ],
        ),
    )
    return ft.Column(
        spacing=SPACE["2"],
        controls=[
            frame,
            ft.Text(
                f"侧栏：{'收起' if collapsed else '展开'}（点右上角箭头切换）",
                size=FONT_SIZE["small"],
                color=_MUTED,
            ),
        ],
    )


@ft.component
def _narrow() -> ft.Control:
    """340px 宽的容器：标题省略、内容换行，页头不会长成三行。"""
    frame = _frame(
        height=300,
        width=340,
        content=PageLayout(
            title="标题很长也不会把右侧操作挤出去",
            subtitle="标题与副标题各占一行，超出部分省略",
            actions=[
                ft.IconButton(icon=ft.Icons.MORE_HORIZ, icon_size=18, tooltip="更多")
            ],
            controls=[
                ft.Row(
                    wrap=True,
                    spacing=SPACE["2"],
                    run_spacing=SPACE["2"],
                    controls=[
                        _chip("已启用"),
                        _chip("管理员"),
                        _chip("双因子"),
                        _chip("上次登录 2 小时前"),
                    ],
                ),
                ft.Text(
                    "内容按可用宽度换行，没必要为窄容器再写一套布局。",
                    size=FONT_SIZE["body"],
                    color=_MUTED,
                ),
            ],
        ),
    )
    return ft.Column(
        spacing=SPACE["2"],
        controls=[
            frame,
            ft.Text(
                "窄容器下的退化：页头保持两行，操作始终可见。",
                size=FONT_SIZE["small"],
                color=_MUTED,
            ),
        ],
    )


_BASIC_CODE = """PageLayout(
    title="用户管理",
    subtitle="管理系统用户、角色与权限",
    actions=[Button("新建用户", icon=Icons.ADD)],
    controls=[user_table, Pagination(state)],
)"""

_SKELETON_CODE = """ft.Column([
    ft.Row([
        sidebar,                                  # 收起到 width=0 即可
        ft.Container(
            expand=True,
            content=PageLayout(title="用户管理", controls=[...]),
        ),
    ], spacing=0, expand=True),
    footer,                                       # 固定页脚在 PageLayout 之外
])"""

SPEC = Spec(
    name="PageLayout",
    summary="页面骨架：页头 + 可滚动内容列，内边距与间距一次定好。",
    definition=(
        "每个业务页都长着同一副骨架：一行标题（配副标题与右侧操作），下面是一列内容，"
        "内容长了要能滚。PageLayout 把这层骨架固化下来，页面只需要交出 title 与 controls。"
        "它只管页头与内容列 —— 侧栏、页脚是外壳的事，在它外面套一层 Row / Column，"
        "切换折叠时互不影响。"
    ),
    anatomy=[
        (
            "标题",
            "页头最左边一行，headline 档 + 粗体；单行省略 —— 标题再长也不该把操作挤走。",
        ),
        ("副标题", "标题下方 12px 次要色，同样单行省略；留空则不占位。"),
        (
            "操作区",
            "标题右侧的一组控件，与标题垂直居中。超过两个就该考虑收进「更多」。",
        ),
        (
            "内容列",
            "controls 依次排下去，间距 12，四周留白按自身宽度在 16 / 24 / 32 之间取，"
            "默认 ScrollMode.AUTO。",
        ),
        (
            "边界",
            "expand 默认打开：它要填满父容器的剩余空间，所以父级必须给定高度。",
        ),
    ],
    when=[
        "每个业务页的根容器：标题 + 操作 + 内容一次写完",
        "内容长度不定、需要默认滚动而不是自己包一层 ListView",
        "多个页面要保持同样的留白与标题层级",
    ],
    avoid=[
        "页面里再套页面：只保留最外层一个 PageLayout，内层用 Column",
        "固定高度的看板/仪表盘：用 Row + Column 自己分栏，自带滚动会和外层打架",
        "弹窗、抽屉里的内容：父级没有剩余高度，用 Column 或面板组件",
    ],
    examples=[
        Example(
            "基础用法",
            _basic,
            hint="标题、副标题、两个操作，下面是统计卡 + 列表；内容超长时整列滚动。",
            code=_BASIC_CODE,
        ),
        Example(
            "完整骨架",
            _skeleton,
            hint="侧栏 + 页头 + 内容 + 页脚：点右上角箭头折叠侧栏，比较前后的补位效果。",
            code=_SKELETON_CODE,
        ),
        Example(
            "窄容器",
            _narrow,
            hint="340px 宽：标题省略、内容换行，页头始终是两行，操作不会被挤掉。",
        ),
    ],
    api=[
        Api("title", "str", "''", "页面标题；留空且无 actions 时整个页头不渲染"),
        Api("subtitle", "str", "''", "标题下方的说明，单行省略"),
        Api("actions", "list[ft.Control]", "[]", "页头右侧的操作控件；窄容器上折到标题下方"),
        Api("controls", "list[ft.Control]", "[]", "页面内容，按 spacing 依次排列"),
        Api(
            "padding",
            "ft.PaddingValue | None",
            "None",
            "四周留白；None = 跟着自身宽度档位走（16 / 24 / 32）",
        ),
        Api(
            "max_content_width",
            "int | str | None",
            "None",
            "内容最大宽度：reading(720) / content(1120) / wide(1440) / 像素值；窄容器自动失效",
        ),
        Api("spacing", "int", "12", "页头与内容、内容各块之间的行距"),
        Api("scroll", "ft.ScrollMode | None", "AUTO", "传 None 关闭滚动，由调用方接管"),
        Api(
            "horizontal_alignment",
            "ft.CrossAxisAlignment",
            "START",
            "内容列的水平对齐；表格这类要撑满的用 STRETCH",
        ),
        Api(
            "bgcolor",
            "ft.ColorValue",
            "TRANSPARENT",
            "页面底色；默认透明，露出外壳的背景",
        ),
    ],
    notes=[
        tip(
            "页头收进了设计令牌：标题从 22px 落到 headline 档（20），内边距与行距改走"
            " SPACE；标题与副标题都改成单行省略 —— 页面标题变长时，正确的结果是省略，"
            "而不是把右侧操作挤出屏幕、或把页头撑成三行。"
        ),
        info(
            "响应式量的是**自身宽度**（on_size_change），不是窗口宽度。所以把它放进"
            "侧栏、分栏、对话框里同样正确：「窗口很宽，我很窄」时它会按窄的排版。"
            "同一档内拖动只改内边距与限宽两个属性，不重建任何子树；页头形态在构建期"
            "按档位定下来 —— 页面用组件挂载时，档位一变整页重渲染，形态自然跟着换。"
        ),
        warn(
            "把 PageLayout 放进 @ft.component 渲染出的树里时，它是**冻结**的："
            "on_size_change 里的赋值会被 flet 拒绝（Frozen controls cannot be updated）。"
            "那种场景要在组件里 use_responsive()，档位一变整页重渲染，而不是让 "
            "PageLayout 在事件里改自己。"
        ),
        info(
            "max_content_width 在窄容器上自动失效 —— 小屏幕上再限宽等于把内容挤没。"
            "宽屏上则相反：一行文字超过约 75 个字符就会难读，限宽居中比拉满更专业。"
        ),
        info(
            "侧栏与页脚不在这里。PageLayout 的职责只有「页头 + 可滚动内容」，侧栏用 Row "
            "放在它左边、页脚用 Column 放在它下面 —— 这样折叠侧栏不会牵连内容区。"
        ),
        info(
            "expand 默认为 True，父容器必须给定高度（固定高度的卡片、或填充整个视图）。"
            "放在无界高度里，内部的 Column 会拿到无穷大约束。"
        ),
    ],
    tags=("页面", "布局", "骨架", "页头", "page layout"),
)


if __name__ == "__main__":
    run(SPEC)
