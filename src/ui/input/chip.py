"""胶囊选择 (Chip) —— 单选 / 多选的一组可点标签。

参考 Radio 的 observable + dataclass + component 模式：选中结果写回
``value``（单选）或 ``selected_values``（多选），控件只负责把状态画出来。

用法::

    chip = Chip(label="优先级", options=["高", "中", "低"])
    Column([chip.ui()])
    print(chip.value)          # 选中的选项，未选为 None
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import flet as ft

from ui.core.constants import LayoutType
from ui.core.doc import Api, Example, Spec, info, run, tip
from ui.core.tokens import FONT_SIZE
from ui.input.input import Label

__all__ = ["Chip"]


@ft.observable
@dataclass
class Chip(Label):
    """Chip 选择组件，支持单选和多选模式。

    Attributes:
        value: 单选模式下存储选中的选项值，多选模式下存储选中的选项值列表。
        options: 可选项列表，每个元素为选项的文本标签。
        multi_select: 是否为多选模式，默认 False（单选）。
        chip_layout_type: 布局方向，水平或垂直，默认水平。
    """

    text: ft.StrOrControl | None = None
    value: str | None = None
    selected_values: list[str] = field(default_factory=list)
    options: list[str] = field(default_factory=list)
    multi_select: bool = False
    chip_layout_type: LayoutType = LayoutType.HORIZONTAL
    on_change: Callable | None = None

    def _on_change(self, option: str, selected: bool, e) -> None:
        """芯片选择状态变化时的回调。

        子类可重写此方法以处理自定义逻辑。

        Args:
            option: 被点击的选项文本。
            selected: 该选项被点击后的选中状态。
        """
        if self.on_change:
            self.on_change(e)

    @ft.component
    def ui(self):
        """构建 Chip 组件的 UI。

        Returns:
            ft.Control: 包含所有 Chip 控件的行或列布局。
        """
        chips: list[ft.Control] = []

        for option in self.options:
            is_selected: bool
            if self.multi_select:
                is_selected = option in self.selected_values
            else:
                is_selected = self.value == option

            def make_on_click(opt: str):
                """为每个 chip 创建闭包捕获当前选项值。"""

                def _on_click(e=None) -> None:
                    """芯片点击事件处理。

                    Args:
                        e: flet 事件对象（可选）。
                    """
                    if self.multi_select:
                        if opt in self.selected_values:
                            self.selected_values = [
                                v for v in self.selected_values if v != opt
                            ]
                        else:
                            self.selected_values = self.selected_values + [opt]
                    else:
                        if self.value == opt:
                            self.value = None
                        else:
                            self.value = opt
                    self._on_change(
                        opt,
                        opt
                        in (
                            self.selected_values
                            if self.multi_select
                            else [self.value]
                            if self.value
                            else []
                        ),
                        e,
                    )
                    self.notify()

                return _on_click

            chip = ft.Chip(
                label=ft.Text(
                    option,
                    # 选中时底色是主色，文字必须走 on_primary：深色主题下
                    # 主色变浅、on_primary 变深，对比度仍然成立。
                    color=ft.Colors.ON_PRIMARY if is_selected else ft.Colors.ON_SURFACE,
                ),
                selected=is_selected,
                # 以前写死 GREEN：换主题种子后胶囊还是绿的，和整页脱离。
                selected_color=ft.Colors.PRIMARY,
                check_color=ft.Colors.ON_PRIMARY,
                on_click=make_on_click(option),
            )
            chips.append(chip)

        if self.chip_layout_type == LayoutType.HORIZONTAL:
            chip_content = ft.Row(
                controls=chips,
                spacing=self.spacing,
                run_spacing=self.run_spacing,
                wrap=True,
            )
        else:
            chip_content = ft.Column(
                controls=chips,
                # 和横排用同一个间距。原先写死 2px，选中项几乎粘在一起，
                # 与横排的 10px 也不是一套节奏。
                spacing=self.spacing,
                run_spacing=self.run_spacing,
            )

        if self.v_label is not None:
            if self.is_vertical:
                return ft.Column(
                    controls=[self.v_label, chip_content],
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                )
            # 让胶囊在标签右侧换行，而不是把整行撑出容器 —— 选项一多就能看出来。
            chip_content.expand = 1
            return ft.Row(
                controls=[self.v_label, chip_content],
                vertical_alignment=ft.CrossAxisAlignment.START,
            )
        else:
            return chip_content


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
@ft.component
def _echo(chip: Chip) -> ft.Control:
    """把当前选中值读出来：说明 Chip 是受控的，选中结果只是一份状态。"""
    if chip.multi_select:
        text = "、".join(chip.selected_values) or "未选择"
    else:
        text = chip.value or "未选择"
    return ft.Text(
        f"当前值：{text}",
        size=FONT_SIZE["small"],
        color=ft.Colors.ON_SURFACE_VARIANT,
    )


@ft.component
def _single() -> ft.Control:
    chip = ft.use_memo(
        lambda: Chip(label="优先级", label_width=64, options=["高", "中", "低"]), []
    )
    return ft.Column(spacing=12, controls=[chip.ui(), _echo(chip)])


@ft.component
def _multi() -> ft.Control:
    chip = ft.use_memo(
        lambda: Chip(
            label="通知方式",
            label_width=64,
            is_vertical=True,
            multi_select=True,
            options=["邮件", "短信", "站内信", "企业微信"],
        ),
        [],
    )
    return ft.Column(spacing=12, controls=[chip.ui(), _echo(chip)])


@ft.component
def _wrapped() -> ft.Control:
    """选项多时在固定宽度里换行，不会变成一条横向滚动条。"""
    chip = ft.use_memo(
        lambda: Chip(
            multi_select=True,
            spacing=8,
            run_spacing=8,
            options=[
                "全部",
                "进行中",
                "已完成",
                "已取消",
                "待审核",
                "已驳回",
                "草稿",
                "已归档",
            ],
        ),
        [],
    )
    return ft.Column(
        spacing=12,
        controls=[
            ft.Container(width=420, content=chip.ui()),
            _echo(chip),
        ],
    )


_BASIC_CODE = """chip = Chip(label="优先级", label_width=64, options=["高", "中", "低"])
Column([chip.ui()])

# 选中结果：
chip.value            # 单选：选项文本或 None
chip.selected_values  # 多选：选项文本列表

# 多选只要加一个开关：
Chip(options=["邮件", "短信"], multi_select=True)"""


SPEC = Spec(
    name="Chip",
    summary="把单选项或多选项压成一排可点的胶囊，适合筛选项与短标签。",
    definition=(
        "Chip 是「选项不多、又不想占一整列」时的选择控件。它把单选 / 多选的语义装进"
        "一枚胶囊：点一下选中，再点一下取消。选项换行后仍然是一整块，比一列竖排的"
        "Radio 省纵向空间，也比下拉框少一次点击。"
    ),
    anatomy=[
        (
            "选项胶囊",
            "每个 option 一枚 ft.Chip：选中是主色实底 + 对勾，未选中是浅底 + 正文色。",
        ),
        (
            "标签",
            "继承自 Label：横向布局时在左侧右对齐，is_vertical 时在上方左对齐。",
        ),
        (
            "布局",
            "chip_layout_type 决定横排还是竖排；横排自动换行，行距由 run_spacing 控制。",
        ),
        (
            "取值",
            "单选写 value，多选写 selected_values；两者都只是状态，点击时回写并重绘。",
        ),
    ],
    when=[
        "筛选条件只有 3-8 个短词：状态、优先级、渠道",
        "多选标签，用户需要一眼看到自己选了哪些",
        "表单里选项少，希望一屏放下更多字段",
    ],
    avoid=[
        "选项超过十个：一堵胶囊墙反而难扫，改用下拉或多选列表",
        "选项文字很长（超过六个字）：胶囊会被撑成条状，换成列表",
        "需要「全选 / 反选」这类批量操作：Chip 只处理单个选项",
    ],
    examples=[
        Example(
            "基础单选",
            _single,
            hint="三个选项、单选；再点一次已选项即取消。下方实时显示 value。",
            code=_BASIC_CODE,
        ),
        Example(
            "多选",
            _multi,
            hint="multi_select=True，选中项累积在 selected_values；纵向排列。",
        ),
        Example(
            "选项换行",
            _wrapped,
            hint="固定 420px 宽：超出的胶囊换到下一行，而不是横向溢出。",
        ),
    ],
    api=[
        Api("options", "list[str]", "[]", "选项文本，每项渲染成一枚胶囊"),
        Api("multi_select", "bool", "False", "多选模式；关闭时 value 只保存一个"),
        Api("value", "str | None", "None", "单选结果；None 表示未选"),
        Api("selected_values", "list[str]", "[]", "多选结果；顺序即点击顺序"),
        Api(
            "chip_layout_type",
            "LayoutType",
            "LayoutType.HORIZONTAL",
            "横向（可换行）或纵向排列",
        ),
        Api(
            "on_change",
            "Callable | None",
            "None",
            "点击回调；新值读 value / selected_values",
        ),
        Api("label", "str | None", "None", "左侧或上方的说明文字"),
        Api("label_width", "int", "150", "标签占位宽度；横向布局时右对齐"),
        Api("is_vertical", "bool", "False", "标签放到控件上方，适合窄容器"),
        Api("spacing", "Number", "10", "胶囊之间 / 竖排行距"),
    ],
    notes=[
        tip(
            "on_change 只收到 flet 事件对象，不带选项值。新的选中结果要从 value（单选）"
            "或 selected_values（多选）读，回调触发时它们已经写好了。"
        ),
        info(
            "Chip 是选择控件，不是展示标签：没有图标和删除按钮，也不支持只读。"
            "需要可关闭的标签时，直接用 ft.Chip 的 leading / delete_icon 拼。"
        ),
        info(
            "竖排原先写死 2px 间距，和横排的 10px 不是一套节奏；现在两边都走 spacing，"
            "选项多时更易扫读。"
        ),
    ],
    tags=("胶囊", "chip", "筛选", "标签", "多选"),
)


if __name__ == "__main__":
    run(SPEC)
