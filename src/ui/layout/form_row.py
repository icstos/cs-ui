"""表单行 (FormRow) —— 左边一列标签，右边一个控件，说明文字跟在控件下面。

它解决的是「一张表单里的字段对不齐」
-----------------------------------
标签是 96、还是 120？冒号加不加？必填星号放哪、什么颜色？错误说明缩进到哪？
每一处各写各的，单看每一行都还行，一列排下来就会发现标签右边缘参差、控件左边缘
参差、说明文字贴着表单左边界 —— 用户读起来是"这表单没做完"，而不是"某个字段有问题"。

FormRow 把这四件事固定死：

============  ==========================================================
标签列        固定宽度（默认 96）、右对齐、补全角冒号、``ON_SURFACE_VARIANT``
必填标记      星号贴在标签前，走 ERROR 角色色，不额外占地
控件          吃掉标签之外的全部宽度，左边缘自然对齐成一条竖线
说明          缩进到与控件左边齐，而不是退回表单左边
============  ==========================================================

为什么标签在左边而不是浮在框里
------------------------------
浮动标签（Material 的 TextField 默认样式）收起时占位、聚焦后升到边框上，一个
字段就有两种形态；一列表单里文字一会儿在框内、一会儿在框上，眼睛要来回适应。
左标签只有一种形态，扫读时**沿着一条竖线**就能把字段名读完，也更容易和右侧的
值对应起来 —— 这是桌面端表单更常见的做法。

用法::

    FormRow(label="项目名称", required=True, control=TextField(hint_text="例如：cs-ui"))
    FormRow(label="本地路径", control=Row([...]), hint=hint_row(...))
    FormRow(label="提交说明", vertical=True, control=TextField(multiline=True))

``vertical=True`` 时标签挪到控件上方：多行输入、窄容器、或者控件本身是
一大块（上传区、代码框）时，左侧一列标签会把可用宽度切得太碎。
"""

from __future__ import annotations

import flet as ft

from ui.core.doc import Api, Example, Spec, info, run, tip, warn
from ui.core.tokens import FONT_SIZE, SPACE
from ui.input.input import field_label

__all__ = ["FormRow"]

#: 标签列宽。表单里的标签只是字段名（"项目名称"、"可见性"），96 放得下四个
#: 汉字加冒号；Input / Switch 那个 150 是给"推送所有远程："这类成句标签用的，
#: 拿进表单会让控件整体右移，窄弹窗里直接被挤出边界。
FORM_LABEL_WIDTH = 96
#: 说明文字与控件之间的纵向间距（一行小字贴着控件下沿）
HINT_GAP = SPACE["1"]


@ft.control
class FormRow(ft.Container):
    """一行表单：标签 + 控件（+ 可选说明）。

    Args:
        label: 标签文案。留空则只有控件 —— 整列表单都用 FormRow、个别行不要
            标签时，留空比换一种排版更能保持左右边缘对齐。
        label_width: 标签列宽度，一列表单取同一个值才会齐。
        required: 在标签前加一枚星号（只标记，不校验）。
        vertical: 标签放到控件上方，不占左侧宽度。
        control: 被标注的控件。它会吃掉标签之外的全部宽度。
        hint: 控件下方的一行说明：字符串按次级小字渲染，也可以传 ``hint_row``
            这类现成控件（错误、警告、校验结果）。
        label_align: 标签与控件在行内的横向对齐。控件比标签高（多行输入）时改
            ``START``，让标签贴着控件上沿而不是悬在中间。
    """

    # 名字不能叫 ``align``：``ft.Container`` 已有 ``align``（子控件的对齐方式，
    # 类型是 Alignment）。覆盖它会让客户端收到一个 CrossAxisAlignment ——
    # 整个控件直接渲染成一块灰（ErrorControl），而且 Python 侧一句错都不报。


    label: str | None = None
    label_width: int = FORM_LABEL_WIDTH
    required: bool = False
    vertical: bool = False
    control: ft.Control | None = None
    hint: str | ft.Control | None = None
    label_align: ft.CrossAxisAlignment = ft.CrossAxisAlignment.CENTER

    def init(self):
        label = self._label()
        if self.vertical:
            # STRETCH 而不是 expand：纵向排布里 expand 抢的是**高度**，
            # 输入框会一路撑到卡片底部；这里要的是横向铺满。
            head: ft.Control = ft.Column(
                spacing=SPACE["1"],
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                controls=[c for c in (label, self.control) if c is not None],
            )
            indent = 0
        else:
            head = ft.Row(
                spacing=SPACE["2"],
                vertical_alignment=self.label_align,
                controls=[c for c in (label, self._control()) if c is not None],
            )
            indent = self.label_width + SPACE["2"]

        body: list[ft.Control] = [head]
        hint = self._hint()
        if hint is not None:
            # 说明缩进到控件左边：贴着表单左边界会被读成"对整张表说的话"
            body.append(
                ft.Container(
                    content=hint,
                    padding=ft.Padding.only(left=indent, top=HINT_GAP),
                )
            )

        self.content = ft.Column(
            spacing=0,
            tight=True,
            # 整行占满：Row 里的控件靠 expand 拿走剩余宽度，说明行也要跟着铺开
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=body,
        )

    # ------------------------------------------------------------------ 零件
    def _label(self) -> ft.Control | None:
        if not self.label:
            return None
        return field_label(
            self.label,
            # 纵排不锁宽度也不补冒号：标签就在控件正上方，冒号只是多一个顿点
            width=None if self.vertical else self.label_width,
            required=self.required,
            align=ft.TextAlign.START if self.vertical else ft.TextAlign.END,
            colon=not self.vertical,
        )

    def _control(self) -> ft.Control | None:
        """控件包进 expand 容器：标签之外的宽度全部交给它。

        这里**不去改**调用方传进来的控件（不写 ``control.expand = True``）——
        Field 自带 width 时，expand 与 width 同时存在会让布局互斥；给别人手里的
        对象加属性，调用方也难排查。容器已经在 Row 里拿到剩余宽度，子控件跟着
        铺开即可。
        """
        if self.control is None:
            return None
        return ft.Container(content=self.control, expand=True)

    def _hint(self) -> ft.Control | None:
        if self.hint is None or self.hint == "":
            return None
        if isinstance(self.hint, str):
            return ft.Text(
                self.hint,
                size=FONT_SIZE["small"],
                color=ft.Colors.ON_SURFACE_VARIANT,
            )
        return self.hint


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
def _field(hint: str, *, value: str = "") -> ft.TextField:
    return ft.TextField(value=value, hint_text=hint, dense=True)


@ft.component
def _stacked() -> ft.Control:
    """三行同一列标签：右边缘、左边缘各成一条线，说明跟在控件下面。"""
    return ft.Column(
        width=420,
        spacing=SPACE["3"],
        tight=True,
        controls=[
            FormRow(
                label="项目名称",
                required=True,
                control=_field("例如：cs-project-management"),
            ),
            FormRow(label="仓库地址", control=_field("https://example.com/repo.git")),
            FormRow(
                label="可见性",
                control=ft.Dropdown(
                    value="private",
                    options=[
                        ft.DropdownOption(key="private", text="私有"),
                        ft.DropdownOption(key="public", text="公开"),
                    ],
                ),
                hint="公开项目会在报表中标注为可共享。",
            ),
        ],
    )


@ft.component
def _vertical() -> ft.Control:
    """多行输入把标签挪到上方：左侧一列标签会把输入区挤窄。"""
    return ft.Column(
        width=420,
        spacing=SPACE["3"],
        tight=True,
        controls=[
            FormRow(
                label="提交说明",
                vertical=True,
                control=ft.TextField(
                    multiline=True,
                    min_lines=3,
                    hint_text="写清改了什么，例如：修复登录跳转异常",
                ),
            ),
            FormRow(
                label="通知对象",
                control=_field("可选"),
                hint="留空表示不通知。",
            ),
        ],
    )


_STACKED_CODE = """FormRow(
    label="项目名称",
    required=True,
    control=TextField(hint_text="例如：cs-project-management"),
)
FormRow(label="仓库地址", control=TextField(hint_text="https://..."))
FormRow(label="可见性", control=dropdown, hint="公开项目会在报表中标注为可共享。")"""

_VERTICAL_CODE = """FormRow(
    label="提交说明",
    vertical=True,
    control=TextField(multiline=True, min_lines=3),
)"""


SPEC = Spec(
    name="FormRow",
    summary="一行表单：左边标签、右边控件，说明文字缩进到控件下面。",
    definition=(
        "表单行负责「字段与字段之间对齐」：标签列宽、右对齐、冒号、必填星号、"
        "说明文字的缩进，全部由它一处决定。它不画输入框，只负责把标签和任意控件"
        "摆成同一条竖线 —— 所以原生 TextField、SelectBox、自定义的「输入框 + "
        "按钮」组合都能塞进来，整张表单的左边缘和右边缘仍然齐。"
    ),
    anatomy=[
        ("标签列", "固定宽度（默认 96）、右对齐、补全角冒号，颜色取次级前景。"),
        ("必填标记", "星号贴在标签前，走 ERROR 角色色；只做标记，校验仍由调用方决定。"),
        ("控件槽", "标签之外的全部宽度都给它；控件不再各写 width，左边缘自然齐。"),
        ("说明", "控件下方一行小字，缩进到与控件左边齐，不退回表单左边界。"),
        ("纵排", "vertical=True 时标签挪到控件上方，不占左侧宽度。"),
    ],
    when=[
        "一张表单里有三个以上字段，需要标签右边缘对齐成一条线",
        "控件本身不自带标签（原生 TextField、Slider、自定义组合控件）",
        "字段需要一行说明或校验结果，且要贴着这个字段而不是整张表单",
    ],
    avoid=[
        "单个字段的临时输入（搜索框、筛选框）：直接给 hint_text，别为它铺一列标签",
        "标签与控件本身是一对并列概念（开关的「推送到所有远程」）：用 Switch 自带的 label",
        "整页只有两个字段：左标签会显得空，考虑把标签放上方",
    ],
    examples=[
        Example(
            "一列字段",
            _stacked,
            hint="宽屏表单的常态：三行同一列标签，说明跟在控件下方。",
            code=_STACKED_CODE,
        ),
        Example(
            "标签在上",
            _vertical,
            hint="多行输入用 vertical：左边不再切掉一列标签，输入区更宽。",
            code=_VERTICAL_CODE,
        ),
    ],
    target=FormRow,
    api=[
        Api("label", "str | None", "None", "标签文案；留空只渲染控件"),
        Api("label_width", "int", "96", "标签列宽度；同一列表单取同一个值才会齐"),
        Api("required", "bool", "False", "标签前加一枚星号（只标记，不校验）"),
        Api("vertical", "bool", "False", "标签放在控件上方而不是左侧"),
        Api("control", "Control | None", "None", "被标注的控件；会铺满标签右边的空间"),
        Api(
            "hint",
            "str | Control | None",
            "None",
            "控件下方说明：字符串按小字渲染，也可传 hint_row 等现成控件",
        ),
        Api(
            "align",
            "CrossAxisAlignment",
            "CENTER",
            "标签与控件的对齐；控件更高时改 START，让标签贴住上沿",
        ),
    ],
    notes=[
        info(
            "标签的样式（宽度、颜色、冒号、星号）与 Input / SelectBox 的左侧标签同源，"
            "都走 ui.input.input.field_label —— 所以「自带标签的输入框」和「FormRow + "
            "原生控件」混排时，看不出两种气质。"
        ),
        tip(
            "控件不要再自己写 width：FormRow 已经把它铺满。写了就会在右边留下一截"
            "空白，一行里两个字段的右边缘反而对不齐。"
        ),
        warn(
            "字段一律用关键字传（``label=`` / ``control=``）。flet 控件的位置参数会落到"
            "基类字段上，组件自己的字段仍是默认值 —— 表现为标签消失、控件也不见了，"
            "而且不报错。"
        ),
        warn(
            "别把 FormRow 放进 wrap=True 的 Row：它内部有 expand 的控件，换行布局里"
            "拿不到确定宽度，Flutter 会画出灰块。整行独占时再用它。"
        ),
    ],
    tags=("表单行", "表单", "字段", "form", "field", "label", "对齐"),
)


if __name__ == "__main__":
    run(SPEC)
