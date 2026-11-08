"""单选组 (Radio) —— 互斥选项：横排、竖排与带描述的卡片。

一组单选回答的是「这几个里选哪一个」：选中新的，旧的自动取消，永远只有一个成立，
而且可以一个都不选（``value`` 为 ``None``）。它和下拉框的区别不在数据，而在**可见性**：
选项少于五六个、且用户需要一眼看全时，摊在页面上比藏进弹层更快；选项多到要滚动，
就该换成 :class:`~ui.input.select_box.SelectBox`。

``options`` 里可以放三种东西：字符串（等价的文本与值）、现成的 :class:`flet.Radio`
（需要自定义样式时）、以及 :class:`RadioCard`（标题 + 说明的卡片，整块可点）。

用法::

    gender = Radio(label="性别", options=["男", "女", "其他"], value="男")
    Column([gender.ui()])
    print(gender.value)
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import flet as ft

from ui.core.constants import LayoutType
from ui.core.doc import Api, Example, Spec, info, run, tip
from ui.core.tokens import FONT_SIZE, RADIUS, SPACE, disabled_layer, selected_layer
from ui.input.input import Label

__all__ = ["Radio", "RadioCard"]

#: 单选点：选中填充主色。原来写死 BLUE，换主色后整页只有它不跟随
ACTIVE = ft.Colors.PRIMARY

#: 文字三档：正文 / 说明 / 禁用
TEXT = ft.Colors.ON_SURFACE
MUTED = ft.Colors.ON_SURFACE_VARIANT
TEXT_DISABLED = disabled_layer()

#: 选中卡片：主色淡底 + 主色描边，靠两层一起表态，单靠描边在深色主题下太弱
CARD_BORDER = ft.Colors.OUTLINE_VARIANT
CARD_BORDER_SELECTED = ft.Colors.PRIMARY
CARD_BG_SELECTED = selected_layer("subtle")


@dataclass(frozen=True)
class RadioCard:
    """单选卡：标题 + 说明，整块可点。

    Args:
        value: 选中后写进 ``Radio.value`` 的值。
        label: 卡片标题，一句话说清这个选项是什么。
        description: 标题下的说明，写适用场景或代价，可以留空。
        disabled: 单独禁用这一张卡；整组禁用仍由 ``Radio.disabled`` 控制。
    """

    value: str
    label: str
    description: str = ""
    disabled: bool = False


@ft.observable
@dataclass
class Radio(Label):
    """单选组：一组互斥选项，值落在 ``value`` 上。

    Args:
        value: 当前选中项的 value；``None`` 表示一个都没选。
        options: 选项，字符串 / ``ft.Radio`` / :class:`RadioCard` 可以混排。
        radio_layout_type: HORIZONTAL 横排并自动换行；VERTICAL 竖排。
        disabled: 整组禁用：不响应点击，值仍然可读。
        on_select: 选中回调，入参是新的 value；联动别的控件时用它。
    """

    value: str | None = None
    options: list[str | ft.Radio | RadioCard] = field(default_factory=list)
    radio_layout_type: LayoutType = LayoutType.HORIZONTAL
    disabled: bool = False
    on_select: Callable[[str], None] | None = None

    def on_change(self, e):
        """把选中值写回 ``value``。

        ``e.data`` 与 ``e.control.value`` 同源，但控件属性不做字符串转换，
        直接读它更稳。
        """
        self.value = getattr(e.control, "value", None) or None

    def _emit(self) -> None:
        if self.on_select is not None and self.value is not None:
            self.on_select(self.value)

    def _pick(self, value: str) -> None:
        """卡片被点：整块生效，不用非得点到那个小圆点。"""
        if self.disabled or self.value == value:
            return
        self.value = value
        self._emit()
        self.notify()  # type: ignore[attr-defined]

    def _radio(self, option: str) -> ft.Radio:
        return ft.Radio(
            label=option,
            value=option,
            label_position=ft.LabelPosition.RIGHT,
            # 禁用时不指定主色，交给 M3 的禁用色走灰
            active_color=None if self.disabled else ACTIVE,
            disabled=self.disabled,
            label_style=ft.TextStyle(
                size=FONT_SIZE["body"],
                color=TEXT_DISABLED if self.disabled else TEXT,
            ),
        )

    def _card(self, card: RadioCard) -> ft.Control:
        selected = self.value == card.value
        disabled = self.disabled or card.disabled
        title_color = TEXT_DISABLED if disabled else TEXT
        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=SPACE["3"], vertical=SPACE["2"]),
            border_radius=RADIUS["lg"],
            border=ft.Border.all(1, CARD_BORDER_SELECTED if selected else CARD_BORDER),
            bgcolor=CARD_BG_SELECTED if selected else None,
            on_click=None if disabled else lambda _e: self._pick(card.value),
            content=ft.Row(
                spacing=SPACE["2"],
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.Radio(
                        value=card.value,
                        disabled=disabled,
                        active_color=None if disabled else ACTIVE,
                    ),
                    ft.Column(
                        spacing=2,
                        tight=True,
                        expand=True,
                        controls=[
                            ft.Text(
                                card.label, size=FONT_SIZE["body"], color=title_color
                            ),
                            *(
                                [
                                    ft.Text(
                                        card.description,
                                        size=FONT_SIZE["small"],
                                        color=TEXT_DISABLED if disabled else MUTED,
                                    )
                                ]
                                if card.description
                                else []
                            ),
                        ],
                    ),
                ],
            ),
        )

    @ft.component
    def ui(self):
        """渲染单选组：选项按 ``radio_layout_type`` 排列，外面可挂标签。"""

        def _on_change(e):
            self.on_change(e)
            self._emit()
            self.notify()  # type: ignore[attr-defined]

        has_card = any(isinstance(option, RadioCard) for option in self.options)
        controls: list[ft.Control] = []
        for option in self.options:
            if isinstance(option, RadioCard):
                controls.append(self._card(option))
            elif isinstance(option, str):
                controls.append(self._radio(option))
            else:
                controls.append(option)

        if has_card or self.radio_layout_type == LayoutType.VERTICAL:
            content: ft.Control = ft.Column(
                controls=controls,
                spacing=SPACE["2"] if has_card else SPACE["1"],
                alignment=ft.MainAxisAlignment.START,
            )
        else:
            content = ft.Row(
                controls=controls,
                spacing=self.spacing,
                run_spacing=self.run_spacing,
                # 选项一多就换行，窄容器里不会把最后一个挤到屏幕外
                wrap=True,
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )

        v_ui = ft.RadioGroup(
            value=self.value,
            content=content,
            on_change=_on_change,
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
                # 一组有好几行，标签与第一行对齐而不是垂直居中
                vertical_alignment=ft.CrossAxisAlignment.START,
            )
        return v_ui


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
def _caption(text: str) -> ft.Control:
    return ft.Text(text, size=FONT_SIZE["small"], color=MUTED)


@ft.component
def _basic() -> ft.Control:
    """横排用于短选项，竖排用于需要逐条读的选项。"""
    gender, set_gender = ft.use_state("男")
    plan, set_plan = ft.use_state("按月")
    return ft.Column(
        spacing=16,
        controls=[
            Radio(
                label="性别",
                options=["男", "女", "其他"],
                value=gender,
                is_required=True,
                on_select=set_gender,
            ).ui(),
            Radio(
                label="付费方式",
                options=["按月", "按年", "一次性"],
                value=plan,
                radio_layout_type=LayoutType.VERTICAL,
                is_vertical=True,
                label_width=90,
                on_select=set_plan,
            ).ui(),
            _caption(f"性别：{gender} · 付费方式：{plan}"),
        ],
    )


@ft.component
def _cards() -> ft.Control:
    """单选卡：标题 + 说明，点标题、说明或圆点都能选中。"""
    plan, set_plan = ft.use_state("standard")
    return ft.Column(
        spacing=12,
        controls=[
            Radio(
                label="套餐",
                options=[
                    RadioCard("free", "免费版", "单人使用，保留 7 天历史"),
                    RadioCard("standard", "标准版", "5 人协作，保留 90 天历史"),
                    RadioCard(
                        "enterprise",
                        "企业版",
                        "需要管理员开通，暂不可选",
                        disabled=True,
                    ),
                ],
                value=plan,
                is_vertical=True,
                label_width=90,
                on_select=set_plan,
            ).ui(),
            _caption(f"当前套餐：{plan}"),
        ],
    )


@ft.component
def _disabled() -> ft.Control:
    """整组禁用：选中项照样显示，但点不动。"""
    level = Radio(
        label="权限",
        options=["只读", "编辑", "管理"],
        value="只读",
        disabled=True,
        is_required=True,
    )
    return ft.Column(
        spacing=12,
        controls=[
            level.ui(),
            _caption(f"禁用组的 value 仍可读：{level.value}"),
        ],
    )


_BASIC_CODE = """gender = Radio(
    label="性别",
    options=["男", "女", "其他"],
    value="男",
)
Column([gender.ui(), Text(f"当前：{gender.value}")])

# 选项要逐条读时改竖排：
Radio(label="付费方式", options=["按月", "按年"], is_vertical=True)"""

_CARD_CODE = """Radio(
    label="套餐",
    options=[
        RadioCard("free", "免费版", "单人使用，保留 7 天历史"),
        RadioCard("standard", "标准版", "5 人协作，保留 90 天历史"),
        RadioCard("enterprise", "企业版", "需要管理员开通", disabled=True),
    ],
    value="standard",
).ui()"""


SPEC = Spec(
    name="Radio",
    summary="互斥选项里选一个：横排、竖排，或带说明的整块卡片。",
    definition=(
        "单选组把「只能选一个」这件事画出来：每个选项前一枚圆点，选中新的，旧的自动"
        "取消。选项全部可见，所以用户不需要先点开才知道有哪些 —— 这正是它相对下拉框"
        "的价值。选项一旦多到要滚动、或者标签长到放不下，可见性就变成了负担，那时"
        "应当换成 SelectBox。"
    ),
    anatomy=[
        ("单选点", "选中时填充主色，未选是 1px 描边的空心圆；走角色色，跟随主色。"),
        ("选项文字", "圆点右侧，点文字等同点圆点；横排自动换行，竖排逐行左对齐。"),
        (
            "单选卡",
            "标题 + 说明 + 圆点组成一张卡，选中时淡主色底 + 主色描边，点整块都能选。",
        ),
        ("外置标签", "整组的标题，冒号自动补；必填只在标签前加一枚星号。"),
        ("禁用态", "圆点与文字一起降到 38% 的灰，整组禁用时所有选项同时失效。"),
    ],
    when=[
        "选项三到六个，摆出来比藏进下拉更容易比较",
        "选项需要一句说明才能决定（套餐、配送方式）",
        "必须让用户看到全部候选，而不是先点开弹层",
    ],
    avoid=[
        "允许同时选多个：用 CheckboxGroup，单选组点第二个会把第一个取消",
        "选项超过七八个：用 SelectBox，一屏单选点会淹没表单",
        "两三个短选项只是在切视图：用 SegmentedButton，它更紧凑、也更像工具条",
    ],
    examples=[
        Example(
            "横排与竖排",
            _basic,
            hint="短选项横排并自动换行；需要逐条读的选项改竖排，标签置顶。",
            code=_BASIC_CODE,
        ),
        Example(
            "单选卡",
            _cards,
            hint="标题与说明都能点；禁用卡保留说明但整块不响应，值仍可读。",
            code=_CARD_CODE,
        ),
        Example(
            "整组禁用",
            _disabled,
            hint="整组禁用后所有选项一起变灰，value 仍然是「只读」而不是空。",
        ),
    ],
    api=[
        Api("value", "str | None", "None", "当前选中项的 value；None 表示未选"),
        Api(
            "options",
            "list[str | ft.Radio | RadioCard]",
            "[]",
            "选项；字符串的文本即值，顺序即渲染顺序",
        ),
        Api(
            "radio_layout_type",
            "LayoutType",
            "HORIZONTAL",
            "HORIZONTAL 横排并自动换行 / VERTICAL 竖排",
        ),
        Api("disabled", "bool", "False", "整组禁用：不响应点击，值仍可读"),
        Api(
            "on_select",
            "Callable[[str], None] | None",
            "None",
            "选中回调，入参是新的 value；联动别的控件时用它",
        ),
        Api("label", "str | None", "None", "整组的外置标签；冒号自动补"),
        Api("is_vertical", "bool", "False", "标签放选项上方（True）还是左侧"),
        Api("is_required", "bool", "False", "标签前加星号；是否必填由调用方校验"),
        Api("label_width", "int", "150", "横排时标签列宽，一列表单项靠它对齐"),
        Api(
            "RadioCard",
            "value / label / description / disabled",
            "",
            "options 里的卡片项：标题下可带一句说明，整块可点",
        ),
    ],
    notes=[
        tip(
            "取消选中是把 ``value`` 置回 ``None``，不是填空串 —— 空串会和「值为空串"
            "的选项」撞车，而单选组的「没选」是一个合法的独立状态。"
        ),
        info(
            "横排从固定 Row 改成 ``wrap=True``：原来选项一多就横向溢出，最后一个被"
            "挤出可视区且无法滚动。换行后窄容器里也不会丢选项。"
        ),
        info(
            "单选点从写死的 BLUE 换成 PRIMARY，禁用文字走 on-surface 38% —— 深色"
            "主题下原来的纯蓝会和主色脱节。禁用态不指定主色，交给 M3 的禁用色走灰。"
        ),
    ],
    tags=("单选", "radio", "互斥", "选项", "表单"),
)


if __name__ == "__main__":
    run(SPEC)
