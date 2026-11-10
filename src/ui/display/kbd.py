"""键帽 (Kbd) —— 把「Ctrl+E」这样的快捷键显示成一枚小键帽。

为什么值得单独一个组件
----------------------
快捷键提示最容易被写成一行灰色小字（"Ctrl+E"），于是它和旁边的说明文字长得
一模一样 —— 用户读到的是一条**普通文案**，而不是"这是一个键"。键帽的形状本身
就是信息：它有边界、有底、比正文矮一档，扫一眼就知道"按这个"。

三条硬规则
----------
1. **字号取 ``caption``（11），不跟正文**。键帽是标注不是内容；和正文同号时，
   它会把菜单行撑高、把提示区读成正文。
2. **描边 + 透明底，不填实色**。实底键帽在深色主题下会变成一块块亮斑，反而
   比文字更抢眼；描边在明暗两种主题下都是同一种"轻边界"。
3. **``+`` 拆分**。``"Ctrl+E"`` 渲染成两枚键帽加一个加号；单个键（``"Enter"``、
   ``"Esc"``）就是一顶。一个键一顶才符合"按下去"的物理直觉。

用法::

    Kbd("Ctrl+E")
    Kbd("Enter")
    Row([Text("复制路径"), Container(expand=True), Kbd("Ctrl+D")])
"""

from __future__ import annotations

import flet as ft

from ui.core.doc import Api, Example, Spec, info, run, tip
from ui.core.tokens import FONT_SIZE, FONT_WEIGHT, RADIUS, SPACE

__all__ = ["Kbd"]

#: 键帽是标注，比正文矮一档：11px 的注入到 14px 正文里读起来是"附注"而不是"内容"。
SIZE = FONT_SIZE["caption"]
#: 键帽高度。与字号、行高解耦，见 ``_cap`` 的注释。
CAP = 16


@ft.control
class Kbd(ft.Container):
    """一枚（或一组）键帽。

    Args:
        text: 键名，或 ``"Ctrl+E"`` 这样的组合键。``+`` 会被拆成多个键帽。
        dim: 弱化一档（用在已经失焦的菜单项上）。默认不弱化。
    """

    text: str = ""
    dim: bool = False

    def init(self):
        # ⚠️ 本类继承 Container，**第一个位置参数是 content 而不是 text** ——
        # 所以 ``Kbd("Ctrl+E")`` 会把字符串落到 content 上。这种写法太自然了
        # （flet 的 Button / Text 都接受首位置传文本），直接报错或静默渲染一顶
        # 空键帽都是坏的，于是这里把字符串 content 认作文本。
        if not self.text and isinstance(self.content, str):
            self.text = self.content

        self.bgcolor = ft.Colors.TRANSPARENT
        parts = [part for part in self.text.split("+") if part] or [""]
        color = ft.Colors.OUTLINE if self.dim else ft.Colors.ON_SURFACE_VARIANT

        controls: list[ft.Control] = []
        for index, part in enumerate(parts):
            if index:
                controls.append(
                    ft.Text("+", size=SIZE, color=color, style=ft.TextStyle(height=1.0))
                )
            controls.append(self._cap(part, color))

        self.content = ft.Row(
            spacing=SPACE["1"],
            tight=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=controls,
        )

    def _cap(self, label: str, color: ft.ColorValue) -> ft.Control:
        """单个键帽：1px 描边 + 左右各 4px 内边距，**高度固定 16**。

        为什么高度写死而不是靠内边距撑：键帽的高度必须与字体行高无关。主题一改
        行距、或换一款行高偏大的字体，靠 padding 撑出来的键帽就会长到 25px ——
        塞进 30px 高的菜单行里上下各只剩 2px，看着像被夹住。固定 16 之后，
        一排键帽在任何字号下都是同一种"矮块"，与 12px 的同行文字齐平。
        """
        return ft.Container(
            height=CAP,
            padding=ft.Padding(SPACE["1"], 0, SPACE["1"], 0),
            border_radius=RADIUS["xs"],
            alignment=ft.Alignment.CENTER,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            content=ft.Text(
                label,
                size=SIZE,
                weight=FONT_WEIGHT["medium"],
                color=color,
                no_wrap=True,
                style=ft.TextStyle(height=1.0),
            ),
        )


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
@ft.component
def _basic() -> ft.Control:
    return ft.Column(
        spacing=SPACE["3"],
        controls=[
            ft.Row(
                spacing=SPACE["2"],
                controls=[
                    ft.Text("单个键", size=FONT_SIZE["small"]),
                    Kbd("Enter"),
                    Kbd("Esc"),
                    Kbd("F5"),
                ],
            ),
            ft.Row(
                spacing=SPACE["2"],
                controls=[
                    ft.Text("组合键", size=FONT_SIZE["small"]),
                    Kbd("Ctrl+A"),
                    Kbd("Ctrl+Shift+F"),
                ],
            ),
        ],
    )


@ft.component
def _menu() -> ft.Control:
    """在菜单行里的真实用法：左标签、右键帽，键帽贴右。"""
    rows = [("打开", "Enter"), ("打开所在文件夹", "Ctrl+E"), ("复制路径", "Ctrl+D")]
    return ft.Container(
        width=280,
        padding=SPACE["1"],
        border_radius=RADIUS["lg"],
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        content=ft.Column(
            spacing=0,
            tight=True,
            controls=[
                ft.Container(
                    height=32,
                    padding=ft.Padding(SPACE["2"], 0, SPACE["2"], 0),
                    border_radius=RADIUS["md"],
                    content=ft.Row(
                        spacing=SPACE["2"],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text(label, size=FONT_SIZE["body"], expand=True),
                            Kbd(keys),
                        ],
                    ),
                )
                for label, keys in rows
            ],
        ),
    )


SPEC = Spec(
    name="Kbd",
    summary="把「Ctrl+E」这样的快捷键显示成一枚小键帽。",
    definition=(
        "快捷键提示常常被写成一行灰色小字，于是它和旁边的说明文字长得一模一样 —— "
        "用户读到的是一条普通文案，而不是「这是一个键」。键帽的形状本身就是信息："
        "有边界、有底、比正文矮一档，扫一眼就知道该按下去。"
    ),
    anatomy=[
        ("键帽", "1px 描边 + 透明底 + 11px 字。描边而不是实底：深色主题下实底会变成亮斑。"),
        ("加号", "组合键之间用一个 11px 的「+」连接，与键帽同色。"),
        ("拆分规则", "text 按 + 拆成多枚键帽；单个键（Enter / Esc）就是一顶。"),
    ],
    when=[
        "菜单项、工具栏提示里说明快捷键",
        "帮助文档里标注「按这个键」",
        "表单旁提示提交方式（Enter 提交 / Esc 取消）",
    ],
    avoid=[
        "正文里顺便提到某个键：直接写「按回车」更像人话，键帽只用于标注",
        "一屏十几个键帽：视觉重量会盖过正文，改成一段说明文字",
    ],
    examples=[
        Example("基础用法", _basic, hint="单个键与组合键；+ 自动拆成两顶。"),
        Example("菜单行", _menu, hint="左标签吃满宽度，键帽永远贴右。"),
    ],
    target=Kbd,
    api=[
        Api("text", "str", "''", "键名或组合键；按 + 拆成多枚键帽"),
        Api("dim", "bool", "False", "弱化一档：描边转 OUTLINE，用于禁用/失焦的行"),
        Api(
            "content",
            "str",
            "None",
            "首位置参数（Kbd(\"Ctrl+E\")）：给字符串时等价于 text",
        ),
        Api("CAP", "int", "16", "键帽高度的模块级取值（模块常量，不随字号变）"),
    ],
    notes=[
        info(
            "字号取 caption（11）而不是跟正文：键帽是标注，和正文同号时会把菜单行撑高，"
            "提示区也会被读成正文。"
        ),
        tip("弱化的菜单项传 dim=True：描边转成 OUTLINE，和禁用文字同一档。"),
    ],
    tags=("键帽", "快捷键", "kbd", "shortcut", "标注"),
)


if __name__ == "__main__":
    run(SPEC)
