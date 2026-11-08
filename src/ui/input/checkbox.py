"""复选框 (Checkbox) —— 单个勾选、复选组（全选 / 半选）与禁用态。

勾选表达的是「这些项里我要哪几个」，和开关的「现在开还是关」不同：它允许零个、
一个、多个同时成立，并且在提交前一直保持原样。所以单个 ``Checkbox`` 只有一个布尔，
``CheckboxGroup`` 持有一份选中项列表，全选框由这份列表反推（全选 / 半选 / 未选），
而不是自己再存一个布尔 —— 两份状态迟早会打架。

用法::

    agree = Checkbox(label="我已阅读并同意用户协议")
    skills = CheckboxGroup(label="技能", options=["Python", "Go", "Rust"])
    Column([agree.ui(), skills.ui()])
    print(agree.value, skills.value)
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import flet as ft

from ui.core.constants import LayoutType
from ui.core.doc import Api, Example, Spec, info, run, tip
from ui.core.i18n import t
from ui.core.tokens import FONT_SIZE, RADIUS, SPACE, disabled_layer
from ui.input.input import Label

__all__ = ["Checkbox", "CheckboxGroup"]

BORDER_RADIUS = RADIUS["lg"]

# ---------------------------------------------------------------------------
# 配色：全部走主题角色。原来写死 BLUE / GREY / BLACK，换主色或切到深色主题后
# 选中色和页面主色对不上，未选中的方框还在深底上糊成一片。
# ---------------------------------------------------------------------------
CHECK_BG = ft.Colors.PRIMARY
CHECK_FG = ft.Colors.ON_PRIMARY
CHECK_BORDER = ft.Colors.OUTLINE
DISABLED_FG = disabled_layer()
DISABLED_BG = disabled_layer()


def _box(
    label: str | None,
    value: bool | None,
    on_change: Callable,
    *,
    disabled: bool = False,
    tristate: bool = False,
) -> ft.Checkbox:
    """一个勾选框：选中填充主色、对勾反白；禁用时整体降到 38% 的两档灰。"""
    return ft.Checkbox(
        label=label,
        value=value,
        tristate=tristate,
        disabled=disabled,
        on_change=on_change,
        check_color=ft.Colors.SURFACE if disabled else CHECK_FG,
        active_color=DISABLED_BG if disabled else CHECK_BG,
        border_side=ft.BorderSide(1, DISABLED_FG if disabled else CHECK_BORDER),
        label_style=ft.TextStyle(
            size=FONT_SIZE["body"],
            color=DISABLED_FG if disabled else ft.Colors.ON_SURFACE,
        ),
    )


@ft.observable
@dataclass
class Checkbox(Label):
    """单个勾选框：一个布尔值，加可选的外置标签。

    Args:
        value: 是否勾选。
        disabled: 禁用；不响应点击、不参与 Tab 走焦。
    """

    value: bool = False
    disabled: bool = False

    def on_change(self, e):
        # e.data 是字符串，"false" 也是真值，用过一次就会「取消不掉」。
        # 控件自身的 value 才是布尔。
        self.value = bool(e.control.value)

    @ft.component
    def ui(self):
        def _on_change(e):
            self.on_change(e)
            self.notify()  # type: ignore[attr-defined]

        v_ui = _box(
            None,
            self.value,
            _on_change,
            disabled=self.disabled,
        )

        if self.v_label is not None:
            if self.is_vertical:
                return ft.Column(
                    controls=[self.v_label, v_ui],
                    spacing=SPACE["1"],
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                )
            return ft.Row(
                controls=[self.v_label, v_ui],
                spacing=SPACE["2"],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        return v_ui


@ft.observable
@dataclass
class CheckboxGroup(Label):
    """复选组：一份选中列表 + 一个「全选」行（支持全选 / 半选 / 未选）。

    Args:
        value: 已选中的选项文本列表。
        options: 可选项；顺序即渲染顺序。
        checkbox_layout_type: VERTICAL 竖排；HORIZONTAL 横排并自动换行。
        disabled: 整组禁用。
    """

    value: list[str] = field(default_factory=list)
    options: list[str] = field(default_factory=list)
    checkbox_layout_type: LayoutType = LayoutType.VERTICAL
    disabled: bool = False

    def on_change(self, option: str, checked: bool):
        if checked:
            if option not in self.value:
                self.value = [*self.value, option]
        else:
            if option in self.value:
                self.value = [v for v in self.value if v != option]

    def select_all(self, select: bool):
        self.value = list(self.options) if select else []

    @ft.component
    def ui(self):
        picked = [option for option in self.options if option in self.value]
        total_options = len(self.options)
        all_selected = total_options > 0 and len(picked) == total_options
        half_selected = 0 < len(picked) < total_options

        def _on_select_all(e):
            # 不读 e.data：三态下点击的下一态由 Flutter 决定，这里按「是否已全选」
            # 反推目标，保证「半选 → 全选」「全选 → 全不选」两种动作稳定。
            self.select_all(not all_selected)
            self.notify()  # type: ignore[attr-defined]

        check_all: ft.Checkbox = _box(
            t("ui.common.select_all"),
            True if all_selected else (None if half_selected else False),
            _on_select_all,
            disabled=self.disabled,
            tristate=True,
        )

        def make_on_change(option: str):
            def _on_change(e):
                self.on_change(option, bool(e.control.value))
                self.notify()  # type: ignore[attr-defined]

            return _on_change

        checkbox_controls: list[ft.Control] = [check_all]

        if self.checkbox_layout_type == LayoutType.HORIZONTAL:
            # 竖排用 Divider 横线；横排用 1px 竖线，原来那块 2px 纯黑在深色下直接消失
            checkbox_controls.append(
                ft.Container(width=1, height=16, bgcolor=ft.Colors.OUTLINE_VARIANT)
            )
        else:
            checkbox_controls.append(ft.Divider(color=ft.Colors.OUTLINE_VARIANT))

        for option in self.options:
            checkbox_controls.append(
                _box(
                    option,
                    option in self.value,
                    make_on_change(option),
                    disabled=self.disabled,
                )
            )

        if self.checkbox_layout_type == LayoutType.HORIZONTAL:
            group_content = ft.Row(
                controls=checkbox_controls,
                spacing=SPACE["2"],
                run_spacing=SPACE["1"],
                # 选项一多就往下一行走，窄容器里不会把内容顶出屏幕
                wrap=True,
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        else:
            group_content = ft.Column(
                controls=checkbox_controls,
                spacing=0,
                alignment=ft.MainAxisAlignment.START,
            )

        v_ui = ft.Container(
            content=group_content,
            padding=ft.Padding.all(0),
        )

        if self.v_label is not None:
            if self.is_vertical:
                return ft.Column(
                    controls=[self.v_label, v_ui],
                    spacing=SPACE["1"],
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                )
            return ft.Row(
                controls=[self.v_label, v_ui],
                spacing=SPACE["2"],
                # 组比单行高，标签与第一行对齐而不是垂直居中
                vertical_alignment=ft.CrossAxisAlignment.START,
            )
        return v_ui


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
def _caption(text: str) -> ft.Control:
    return ft.Text(text, size=FONT_SIZE["small"], color=ft.Colors.ON_SURFACE_VARIANT)


@ft.component
def _single() -> ft.Control:
    """单个勾选：点一下，value 立刻回写，旁边的回显跟着变。"""
    agree = ft.use_memo(
        lambda: Checkbox(
            label="我已阅读并同意用户协议",
            is_required=True,
            # 默认 150 装不下 11 个汉字，会折成两行；长标签显式给足宽度
            label_width=190,
        ),
        [],
    )
    notice = ft.use_memo(lambda: Checkbox(label="接收产品更新邮件", value=True), [])
    return ft.Column(
        spacing=12,
        controls=[
            agree.ui(),
            notice.ui(),
            _caption(
                f"协议：{'已同意' if agree.value else '未同意'} · "
                f"邮件：{'订阅' if notice.value else '不订阅'}"
            ),
        ],
    )


_OPTIONS = ["设计", "前端", "后端", "数据"]


@ft.component
def _group() -> ft.Control:
    """复选组：初始只选了一项，全选框显示半选横线；点它一次变全选。"""
    group = ft.use_memo(
        lambda: CheckboxGroup(
            label="参与方向",
            options=_OPTIONS,
            value=["前端"],
            is_required=True,
        ),
        [],
    )
    picked = "、".join(group.value) if group.value else "无"
    return ft.Column(
        spacing=12,
        controls=[
            group.ui(),
            _caption(f"已选 {len(group.value)} / {len(_OPTIONS)}：{picked}"),
        ],
    )


@ft.component
def _disabled() -> ft.Control:
    """禁用态：勾选状态照样看得见，但不接受任何点击。"""
    signed = Checkbox(label="已签署（不可修改）", value=True, disabled=True)
    pending = Checkbox(label="暂不可选", disabled=True)
    group = CheckboxGroup(
        label="权限",
        options=["读取", "写入"],
        value=["读取"],
        disabled=True,
        is_vertical=True,
    )
    return ft.Column(
        spacing=12,
        controls=[
            signed.ui(),
            pending.ui(),
            group.ui(),
            _caption("禁用不是隐藏：值仍然可读，只是不再响应操作。"),
        ],
    )


_BASIC_CODE = """agree = Checkbox(label="我已阅读并同意用户协议", is_required=True)
Column([
    agree.ui(),
    Text(f"当前：{agree.value}"),      # 勾选后 value 立刻回写
])

# 需要「全选 / 半选」联动时用 CheckboxGroup：
group = CheckboxGroup(
    label="参与方向",
    options=["设计", "前端", "后端", "数据"],
    value=["前端"],                    # 只选一项 → 全选框显示半选
)
Column([group.ui(), Text(f"已选 {group.value}")])"""

_GROUP_CODE = """group = CheckboxGroup(
    options=["设计", "前端", "后端", "数据"],
    value=["前端"],
    checkbox_layout_type=LayoutType.HORIZONTAL,
)
Column([group.ui(), Text(f"已选 {len(group.value)} 项")])"""


SPEC = Spec(
    name="Checkbox",
    summary="从若干项里勾选任意个：单个勾选、复选组与禁用态。",
    definition=(
        "复选框回答的是「哪些项成立」，答案可以是一个、多个，也可以是零个。"
        "它不像开关那样一按就生效，而是先把选择攒在 value 里，等表单提交时一起交出去。"
        "复选组因此把「全选」也算作一种选择状态：全部选中、部分选中（半选）、"
        "一项未选，三种都由同一份列表推导，不另存一个布尔去和它对齐。"
    ),
    anatomy=[
        ("方框", "18px 见方、1px 描边；选中填充主色并压一个反白对勾。"),
        ("标签", "方框右侧，整块可点；组的外置标签自动补冒号，必填加星号。"),
        (
            "全选行",
            "组的第一行，三态：全选打勾、部分选中显示横线、未选为空。",
        ),
        ("分隔", "竖排在下方拉一条发丝线，横排用一根 1px 竖线隔开全选与选项。"),
        ("禁用态", "填充与文字一起降到 38% 的灰，值仍可读，只是不响应点击。"),
    ],
    when=[
        "同一组里可以同时成立多项（技能、权限、通知渠道）",
        "提交前需要一次性确认（协议、条款）",
        "需要「全选」快速批量勾选，又允许逐项取消",
    ],
    avoid=[
        "设置项一按就生效：用 Switch，勾选加提交的节奏会让人以为没保存",
        "选项互斥只能选一个：用 Radio，复选框允许同时打勾会误导",
        "选项超过七八个：用 MultiSelect 收进下拉，一屏复选框会淹没表单",
    ],
    examples=[
        Example(
            "单个勾选",
            _single,
            hint="点方框或标签都能切换；下方回显直接读 value，不走额外事件。",
            code=_BASIC_CODE,
        ),
        Example(
            "复选组与半选",
            _group,
            hint="初始只选一项，全选框是半选；点一次变全选，再点一次清空。",
            code=_GROUP_CODE,
        ),
        Example(
            "禁用态",
            _disabled,
            hint="已签署仍是勾上的，但点不动；整组禁用时全选框也一起失效。",
        ),
    ],
    api=[
        Api(
            "value",
            "bool | list[str]",
            "False / []",
            "选中状态：单个是布尔，组是选中项列表",
        ),
        Api("options", "list[str]", "[]", "组的可选项；顺序即渲染顺序"),
        Api(
            "checkbox_layout_type",
            "LayoutType",
            "VERTICAL",
            "VERTICAL 竖排 / HORIZONTAL 横排并自动换行",
        ),
        Api("disabled", "bool", "False", "禁用：不响应点击，也不参与 Tab 走焦"),
        Api("label", "str | None", "None", "外置标签文案；冒号自动补"),
        Api("is_vertical", "bool", "False", "标签放控件上方（True）还是左侧"),
        Api("is_required", "bool", "False", "标签前加星号；是否必填由调用方校验"),
        Api("label_width", "int", "150", "横排时标签列宽，组与组之间靠它对齐"),
        Api(
            "select_all",
            "bool -> None",
            "",
            "组方法：一次全选或全不选，不改变选项本身",
        ),
    ],
    notes=[
        tip(
            "「全选」用 tristate=True + value=None 画半选横线。点击时不读 e.data，"
            "而是按「当前是否已全选」反推目标态 —— 三态下点击的下一态由 Flutter 决定，"
            "读事件反而会让「半选」点一次变成清空。"
        ),
        info(
            "回写从 e.data 改成 e.control.value：事件里的 data 是字符串，"
            "「false」也是真值，会出现取消勾选后 value 仍是 True 的情况。"
        ),
        info(
            "配色改成 PRIMARY / ON_PRIMARY / OUTLINE 三个角色，禁用走 on-surface 的"
            "38% 透明度；原来写死 BLUE / GREY / BLACK，换主色或深色主题时不跟随。"
        ),
    ],
    tags=("复选框", "多选", "checkbox", "全选", "半选", "表单"),
)


if __name__ == "__main__":
    run(SPEC)
