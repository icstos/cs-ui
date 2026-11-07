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

from ui.core.doc import Api, Example, Spec, info, run, tip
from ui.core.tokens import FONT_SIZE, FONT_WEIGHT, RADIUS, SPACE, overlay

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
        actions: 标题右侧的操作区控件（如按钮）。
        padding: 页面内边距，默认 20。
        spacing: 内容间距，默认 12。
        scroll: 滚动模式，默认 ``AUTO``；传 ``None`` 关闭滚动。
        horizontal_alignment: 内容水平对齐方式。
        bgcolor: 页面背景色。
    """

    controls: list[ft.Control] = field(default_factory=list)
    title: str = ""
    subtitle: str = ""
    actions: list[ft.Control] = field(default_factory=list)
    padding: ft.PaddingValue = SPACE["5"]
    spacing: int = SPACE["3"]
    scroll: ft.ScrollMode | None = ft.ScrollMode.AUTO
    horizontal_alignment: ft.CrossAxisAlignment = ft.CrossAxisAlignment.START
    bgcolor: ft.ColorValue = ft.Colors.TRANSPARENT

    def init(self):
        if self.expand is None:
            self.expand = True

        body: list[ft.Control] = []
        header = self._build_header()
        if header is not None:
            body.append(header)
        body.extend(self.controls)

        self.content = ft.Column(
            controls=body,
            spacing=self.spacing,
            scroll=self.scroll,
            horizontal_alignment=self.horizontal_alignment,
            expand=True,
        )

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

        return ft.Row(
            controls=[
                ft.Column(controls=left, spacing=2, expand=True),
                *self.actions,
            ],
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
                    size=FONT_SIZE["subtitle"],
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
                    left=SPACE["3"], top=SPACE["3"], bottom=SPACE["2"]
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
                    padding=ft.Padding.symmetric(horizontal=SPACE["3"], vertical=7),
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
                    padding=ft.Padding.symmetric(horizontal=SPACE["3"]),
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
            "controls 依次排下去，间距 12、四周留白 20，默认 ScrollMode.AUTO。",
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
        Api("actions", "list[ft.Control]", "[]", "页头右侧的操作控件"),
        Api("controls", "list[ft.Control]", "[]", "页面内容，按 spacing 依次排列"),
        Api("padding", "ft.PaddingValue", "20", "页头与内容四周的留白"),
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
