"""状态标签 (Tag) —— 一枚静态的语义标签：分支名、状态、计数、可见性。

Tag 与 Chip 的分界
------------------
``Chip`` 是**可选的**：它背后有一个值、点一下会变，属于表单控件。
``Tag`` 是**只读的**：它只是把一段短文字染上语义色，点了什么也不会发生。
两者的 DOM 长得像，职责完全不同 —— 用 Chip 表示只读状态，用户会以为能点。

为什么不用 ``Text`` + ``Container`` 拼
--------------------------------------
拼一次很容易，拼十次就开始漂：底色一处 0.10 一处 0.12、文字一处用 ``OUTLINE``
一处用实色、圆角一处 6 一处 999。Tag 把"标签"这件事固定成四个决定：

1. **底色走 ``accent_soft``（12% 淡底）**，文字走 ``accent_text`` —— 同一个语义色
   的两档表达，不是"随便挑一个浅色 + 随便挑一个深色"。
2. **``OUTLINE`` 永远不参与**：它是边框角色，压在 12% 的淡底上只有 3:1 左右的
   对比度，读起来发灰。标签文字是**内容**，该用语义色的 text 档。
3. **高度由内边距 + 字号决定，不写死**：``dense`` 只换字号（11/12），字号一动
   高度跟着走，两档标签并排时底色块的高度差正好是"一档"。
4. **描边用同色 16%**，不是 ``OUTLINE_VARIANT``：灰描边套彩色底会把颜色"熄掉"，
   深色主题下尤其明显。

用法::

    Tag("main", role="info", icon=ft.Icons.ALT_ROUTE)
    Tag("3 个待推送", role="warning", dense=True)
    Tag("已推送", role="success", solid=True)   # 实底：用于必须一眼看到的极少数场合
"""

from __future__ import annotations

import flet as ft

from ui.core.doc import Api, Example, Spec, info, run, tip, warn
from ui.core.tokens import (
    FONT_SIZE,
    FONT_WEIGHT,
    ICON_SIZE,
    RADIUS,
    SPACE,
    accent_fill,
    accent_on,
    accent_soft,
    accent_text,
)

__all__ = ["Tag"]

#: 描边相对语义色的透明度。取 16% 而不是直接用淡底同色：比底色重一档才看得出
#: "有个边界"，但仍远低于实线 —— 标签不该比它标注的内容更抢眼。
EDGE = 0.16

#: 标签的可用语气：M3 的三个强调角色 + 框架补的五个语义角色。
ROLES: tuple[str, ...] = (
    "primary",
    "secondary",
    "tertiary",
    "success",
    "warning",
    "danger",
    "info",
    "neutral",
)


@ft.control
class Tag(ft.Container):
    """一枚只读的语义标签。

    Args:
        text: 标签文字。首位置参数传字符串也可以（``Tag("main")``）。
        role: 语气，取 :data:`ROLES`；未知值退回 ``neutral``。
        icon: 文字左侧的小图标。图标与文字同色，尺寸跟 ``dense`` 走。
        dense: 紧凑档：字号 11、图标 12、左右 10px。用于卡片内的标签行。
        solid: 实底档：``accent_fill`` 打底 + ``accent_on`` 文字。只在必须一眼
            看到时才用 —— 一屏超过两枚实底标签就变成"到处在喊"。
    """

    text: str = ""
    role: str = "neutral"
    icon: ft.IconData | None = None
    dense: bool = False
    solid: bool = False

    def init(self):
        # 本类继承 Container，第一个位置参数是 content —— 传字符串时当文字用，
        # 否则 `Tag("main")` 会静默渲染成一枚只有底色的空胶囊。
        if not self.text and isinstance(self.content, str):
            self.text = self.content

        role = self.role if self.role in ROLES else "neutral"
        size = FONT_SIZE["caption"] if self.dense else FONT_SIZE["small"]
        icon_size = ICON_SIZE["xs"] if self.dense else ICON_SIZE["sm"]
        fg = accent_on(role) if self.solid else accent_text(role)
        bg = accent_fill(role) if self.solid else accent_soft(role)

        self.bgcolor = bg
        self.border_radius = RADIUS["full"]
        self.padding = ft.Padding.symmetric(
            horizontal=SPACE["2"] + 2 if not self.dense else SPACE["2"],
            vertical=2,
        )
        self.border = (
            None
            if self.solid
            else ft.Border.all(1, ft.Colors.with_opacity(EDGE, accent_text(role)))
        )
        # 不设 ``self.alignment``：Container 一旦有 alignment，Flutter 会把它包进
        # 一层 Align，而 Align 在**有界**约束下会撑满可用宽度 —— 于是标签在
        # Wrap 里每枚都占满整行、在 Column 里变成一条横贯的色带。
        # 标签的天性就是"包住自己的文字"，垂直居中交给 Row 的 crossAxisAlignment。
        self.content = ft.Row(
            spacing=SPACE["1"],
            tight=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                *(
                    [ft.Icon(self.icon, size=icon_size, color=fg)]
                    if self.icon is not None
                    else []
                ),
                ft.Text(
                    self.text,
                    size=size,
                    weight=FONT_WEIGHT["medium"],
                    color=fg,
                    no_wrap=True,
                    # 行高钉死 1.3：标签是高 20/24 的小块，默认行高会把文字顶着走，
                    # 上下留白就不对称了。
                    style=ft.TextStyle(height=1.3),
                ),
            ],
        )


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
@ft.component
def _roles() -> ft.Control:
    """八种语气并排：同一份视觉重量，只有色相不同。"""
    return ft.Column(
        spacing=SPACE["3"],
        controls=[
            ft.Row(
                spacing=SPACE["2"],
                wrap=True,
                controls=[Tag(role, role=role) for role in ROLES],
            ),
            ft.Row(
                spacing=SPACE["2"],
                wrap=True,
                controls=[
                    Tag(role, role=role, solid=True, dense=True)
                    for role in ("success", "warning", "danger", "primary")
                ],
            ),
        ],
    )


@ft.component
def _in_row() -> ft.Control:
    """真实用法：一枚分支标签 + 两枚状态标签，跟在仓库名后面。"""
    return ft.Container(
        padding=SPACE["4"],
        border_radius=RADIUS["lg"],
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        content=ft.Row(
            spacing=SPACE["2"],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text("cs-ui", size=FONT_SIZE["title"]),
                Tag("main", role="info", icon=ft.Icons.ALT_ROUTE, dense=True),
                Tag("已配置远程", role="success", icon=ft.Icons.CHECK_CIRCLE, dense=True),
                Tag("未提交 2 个文件", role="warning", icon=ft.Icons.WARNING_AMBER_ROUNDED, dense=True),
            ],
        ),
    )


SPEC = Spec(
    name="Tag",
    summary="一枚只读的语义标签：分支名、状态、计数、可见性。",
    definition=(
        "Tag 把一段短文字染上语义色，用来标注它旁边那块内容的状态。它不可点、"
        "没有值，也不进入表单；点一下会变的那种标签是 Chip。标签最容易被写成"
        "「Text + Container」的随手拼装，于是同一个页面上出现五六种淡底色和圆角 —— "
        "Tag 把底色、文字色、描边、内边距四件事固定下来，只留语气这一个变量。"
    ),
    anatomy=[
        ("底色", "accent_soft：语义色的 12% 淡底。大面积铺满用 accent_wash，这里是小块。"),
        ("文字", "accent_text + medium 字重，11（dense）/ 12。不用 OUTLINE 当文字色。"),
        ("图标", "可选，与文字同色；dense 时 12px，常规 14px，永远比文字略小一档。"),
        ("描边", "同色 16% 的 1px 细边：给出边界又不把颜色压暗。solid 档无描边。"),
        ("圆角", "RADIUS.full：胶囊形。方角小色块会被读成按钮。"),
    ],
    when=[
        "标注分支名、可见性、状态（已推送 / 未配置远程）",
        "显示计数（3 个待提交文件）—— 数字用 dense 档，不抢标题",
        "表格或卡片里给某一列加一层语义色，又不希望它像可点的控件",
    ],
    avoid=[
        "需要点一下切换状态时用 Chip；只读的标签会让用户白点一次",
        "一屏出现十枚以上实底（solid=True）标签：颜色会从「强调」变成「噪音」",
        "超过六个字的句子：标签是标注不是正文，长句请用一行说明文字",
    ],
    examples=[
        Example("八种语气", _roles, hint="淡底档是默认；实底档留给必须一眼看到的状态。"),
        Example("跟在标题后面", _in_row, hint="dense 档与 16px 标题并排时不撑高行。"),
    ],
    target=Tag,
    api=[
        Api("text", "str", "''", "标签文字；也可用首位置参数传字符串"),
        Api("role", "str", "'neutral'", "语气：primary/secondary/tertiary/success/warning/danger/info/neutral"),
        Api("icon", "ft.IconData | None", "None", "文字左侧的小图标，与文字同色"),
        Api("dense", "bool", "False", "紧凑档：字号 11、图标 12、左右 8px"),
        Api("solid", "bool", "False", "实底档：accent_fill 打底 + accent_on 文字"),
    ],
    notes=[
        info(
            "文字色取 accent_text 而不是 OUTLINE：OUTLINE 在 12% 淡底上只有约 3:1 的"
            "对比度，标签会读成「灰掉的禁用项」。"
        ),
        tip("同一行里三种以上的语气就开始变花：状态标签优先用 success / warning / neutral。"),
        warn("role 传了未登记的值会静默退回 neutral —— 拼错一个角色名不会报错，只是颜色不对。"),
    ],
    tags=("标签", "状态", "徽标", "tag", "badge", "pill", "语义色"),
)


if __name__ == "__main__":
    run(SPEC)
