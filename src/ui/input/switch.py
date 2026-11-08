"""开关 (Switch) —— 即时生效的二元设置。

开关表达的是「现在就打开 / 关掉」，一按就生效，没有「保存」这一步。所以它出现在
设置面板里，而不是提交式表单里：在表单里摆一排开关，用户会以为还要点提交，或者
反过来以为已经保存了。

状态始终写在 ``value`` 上（布尔），点了就回写，调用方读它即可。两种「不能改」
要分清：``disabled`` 是整体降灰、连指针都不响应，用于无权限或条件未满足；
``readonly`` 保留正常外观但拒绝改动，用于「看得到当前状态、但只有管理员能改」。
两者的值都可读。

用法::

    notify = Switch(label="桌面通知", description="有 @ 提醒时弹窗", value=True)
    Column([notify.ui()])
    print(notify.value)
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import flet as ft

from ui.core.doc import Api, Example, Spec, info, run, tip
from ui.core.tokens import FONT_SIZE, ICON_SIZE, SPACE
from ui.input.input import Label

__all__ = ["Switch"]

#: 开关内勾/叉：与 subtitle 文字同级，不至于把一行撑高
SWITCH_ICON_SIZE = ICON_SIZE["lg"]

#: 开启态：主色轨道 + 反白滑块。两处都走角色色 —— 写死 BLUE / WHITE 的开关
#: 换主题后会和页面主色对不上，深色主题下白滑块也失去对比。
TRACK_ON = ft.Colors.PRIMARY
THUMB_ON = ft.Colors.ON_PRIMARY

#: 说明行与图标：次要信息统一用 ON_SURFACE_VARIANT，避免和标签抢注意力
MUTED = ft.Colors.ON_SURFACE_VARIANT


@ft.observable
@dataclass
class Switch(Label):
    """开关：一个布尔值加可选的标签、说明与前置图标。

    Args:
        value: 是否开启。
        description: 标签下的一行说明，写「打开后会发生什么」，一行能读完。
        icon: 标签前的图标，给一列设置项一个可扫读的锚点。
        icon_size: 图标边长。
        disabled: 禁用：整体降灰，不响应点击，也不参与 Tab 走焦。
        readonly: 只读：外观与可用时一致，但点击会被忽略、滑块弹回。
        on_toggle: 状态变化回调，入参是新的布尔值；联动别的控件时用它。
    """

    value: bool = False
    description: str | None = None
    icon: ft.IconData | str | None = None
    icon_size: int = SWITCH_ICON_SIZE
    disabled: bool = False
    readonly: bool = False
    on_toggle: Callable[[bool], None] | None = None

    def on_change(self, e):
        """把控件的新状态写回 ``value``。

        ``e.data`` 是 ``"true"`` / ``"false"`` 字符串，拿来当布尔用会永远为真；
        开关自身的 ``value`` 才是布尔。
        """
        self.value = bool(e.control.value)

    def _label_block(self) -> ft.Control | None:
        """标签 +（可选）说明。说明与标签同宽，换行时左边缘对齐。"""
        label = self.v_label
        if label is None:
            return None
        if not self.description:
            return label
        return ft.Column(
            spacing=SPACE["1"],
            tight=True,
            controls=[
                label,
                ft.Text(
                    self.description,
                    size=FONT_SIZE["small"],
                    color=MUTED,
                    width=self.label_width,
                ),
            ],
        )

    def _label_row(self) -> ft.Control | None:
        block = self._label_block()
        if block is None:
            return None
        if self.icon is None:
            return block
        return ft.Row(
            spacing=SPACE["2"],
            # 图标对齐标签那一行，而不是标签 + 说明整块的中间
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                ft.Icon(self.icon, size=self.icon_size, color=MUTED),
                block,
            ],
        )

    @ft.component
    def ui(self) -> ft.Control:
        """渲染开关：滑块 + 标签（+ 说明 / 图标）。"""

        def _on_change(e):
            if self.readonly:
                # 只读：不改值，重绘一次让滑块回到原位
                self.notify()
                return
            self.on_change(e)
            if self.on_toggle is not None:
                self.on_toggle(self.value)
            self.notify()

        v_ui = ft.Switch(
            value=self.value,
            disabled=self.disabled,
            on_change=_on_change,
            # 禁用时把颜色交还给主题：显式给的 active 色会盖掉 M3 的禁用灰，
            # 让一个点不动的开关看起来仍然「开着」
            active_color=None if self.disabled else THUMB_ON,
            active_track_color=None if self.disabled else TRACK_ON,
        )

        label = self._label_row()
        if label is None:
            return v_ui
        if self.is_vertical:
            return ft.Column(
                controls=[label, v_ui],
                spacing=SPACE["1"],
                horizontal_alignment=ft.CrossAxisAlignment.START,
            )
        return ft.Row(
            controls=[label, v_ui],
            spacing=SPACE["2"],
            # 滑块比一行文字高，靠中线对齐才不显得浮在标签上方
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
def _caption(text: str) -> ft.Control:
    return ft.Text(text, size=FONT_SIZE["small"], color=MUTED)


@ft.component
def _basic() -> ft.Control:
    """最常用的形态：标签 + 说明，改动立刻回写。"""
    desktop, set_desktop = ft.use_state(True)
    digest, set_digest = ft.use_state(False)
    return ft.Column(
        spacing=12,
        controls=[
            Switch(
                label="桌面通知",
                description="有 @ 提醒时弹窗",
                value=desktop,
                label_width=180,
                on_toggle=set_desktop,
            ).ui(),
            Switch(
                label="每周摘要",
                description="周一 9:00 发邮件",
                value=digest,
                is_vertical=True,
                label_width=180,
                on_toggle=set_digest,
            ).ui(),
            _caption(
                f"桌面通知：{'开' if desktop else '关'} · "
                f"每周摘要：{'开' if digest else '关'}"
            ),
        ],
    )


@ft.component
def _variants() -> ft.Control:
    """图标、禁用与只读：三种「不能改」要分清，禁用才降灰。"""
    wifi, set_wifi = ft.use_state(True)
    bluetooth, set_bluetooth = ft.use_state(False)
    return ft.Column(
        spacing=12,
        controls=[
            Switch(
                label="Wi-Fi",
                icon=ft.Icons.WIFI,
                value=wifi,
                on_toggle=set_wifi,
            ).ui(),
            Switch(
                label="蓝牙",
                icon=ft.Icons.BLUETOOTH,
                icon_size=16,
                value=bluetooth,
                on_toggle=set_bluetooth,
            ).ui(),
            Switch(label="自动更新（策略锁定）", value=True, disabled=True).ui(),
            Switch(label="云同步（仅管理员可改）", value=True, readonly=True).ui(),
            _caption("禁用整行降灰、点不动；只读外观不变，点了滑块会弹回。"),
        ],
    )


@ft.component
def _linked() -> ft.Control:
    """总开关关掉后，子项一起变灰 —— 联动靠 on_toggle 把值送回父组件。"""
    master, set_master = ft.use_state(True)
    email, set_email = ft.use_state(True)
    sms, set_sms = ft.use_state(False)
    return ft.Column(
        spacing=10,
        controls=[
            Switch(
                label="全部通知",
                description="关掉后下面的渠道不可单独设置",
                value=master,
                label_width=260,
                on_toggle=set_master,
            ).ui(),
            ft.Container(
                padding=ft.Padding.only(left=SPACE["6"]),
                content=ft.Column(
                    spacing=6,
                    controls=[
                        Switch(
                            label="邮件提醒",
                            value=email,
                            disabled=not master,
                            on_toggle=set_email,
                        ).ui(),
                        Switch(
                            label="短信提醒",
                            value=sms,
                            disabled=not master,
                            on_toggle=set_sms,
                        ).ui(),
                    ],
                ),
            ),
            _caption(
                f"总开关：{'开' if master else '关'} · "
                f"邮件：{'开' if email else '关'} · "
                f"短信：{'开' if sms else '关'}"
            ),
        ],
    )


_BASIC_CODE = """desktop = Switch(
    label="桌面通知",
    description="有 @ 提醒时弹窗",
    value=True,
)

Column([
    desktop.ui(),
    Text(f"当前：{'开' if desktop.value else '关'}"),
])"""

_VARIANTS_CODE = """Switch(label="Wi-Fi", icon=ft.Icons.WIFI, value=True).ui()

# 禁用：降灰 + 不响应；只读：外观不变，但改不动
Switch(label="自动更新", value=True, disabled=True).ui()
Switch(label="云同步", value=True, readonly=True).ui()"""


SPEC = Spec(
    name="Switch",
    summary="即时生效的二元设置：一个开关 + 可选的标签、说明与图标。",
    definition=(
        "开关负责一件「现在开还是关」的事，改动立刻生效，不需要再点保存。它和复选框"
        "的分工就在这里：勾选是在攒选择、等提交，开关是当场拨动。正因为它看起来就"
        "生效，标签必须说清「打开之后会发生什么」，所以组件把说明行也收进了布局，"
        "而不是让调用方另拼一行小字去对齐。"
    ),
    anatomy=[
        ("轨道与滑块", "开启是主色轨道 + 反白滑块；关闭交给主题的中性轨道，不写死灰。"),
        ("标签", "滑块左侧（或上方），冒号自动补；必填只在标签前加一枚星号。"),
        (
            "说明行",
            "标签下方一行小字，与标签同宽；写触发条件或后果，不写「开关」二字。",
        ),
        ("前置图标", "标签左侧 18px 图标，给一列设置项一个可扫读的锚点。"),
        (
            "禁用 / 只读",
            "禁用整行降灰且不接受点击；只读外观不变，点击后滑块弹回原位。",
        ),
    ],
    when=[
        "设置面板里的单项开关（通知、自动保存、深色模式），改完即生效",
        "需要把「关」当成明确状态、而不是「没填」",
        "父开关控制一组子项是否可编辑（总开关关掉，子项变灰）",
    ],
    avoid=[
        "需要用户逐项确认后一起提交：用 Checkbox，开关会让人以为已经保存",
        "两个以上互斥选项：用 Radio，开关只有开 / 关两种，选不了第三项",
        "选项很多且允许同时成立：用 CheckboxGroup，一列开关读起来像一排灯",
    ],
    examples=[
        Example(
            "基础用法",
            _basic,
            hint="标签 + 说明两行，改动立刻回写到 value；下方回显直接读值。",
            code=_BASIC_CODE,
        ),
        Example(
            "图标、禁用与只读",
            _variants,
            hint="图标给扫读锚点；禁用降灰不可点，只读外观不变但点了会弹回。",
            code=_VARIANTS_CODE,
        ),
        Example(
            "父子联动",
            _linked,
            hint="总开关关掉后，两个子项一起变灰；再打开时各自的旧值仍保留。",
        ),
    ],
    api=[
        Api("value", "bool", "False", "当前状态；改动即回写，读它就是最新值"),
        Api("label", "str | None", "None", "外置标签文案；冒号自动补"),
        Api(
            "description",
            "str | None",
            "None",
            "标签下的说明行，写「打开后会发生什么」",
        ),
        Api("icon", "IconData | str | None", "None", "标签前的图标"),
        Api("icon_size", "int", "18", "图标边长；紧凑列表可收到 16"),
        Api("disabled", "bool", "False", "禁用：降灰、不响应点击、不参与走焦"),
        Api("readonly", "bool", "False", "只读：外观不变，点击被忽略并弹回"),
        Api(
            "on_toggle",
            "Callable[[bool], None] | None",
            "None",
            "状态变化回调，联动别的控件时用它",
        ),
        Api("is_vertical", "bool", "False", "标签放开关上方（True）还是左侧"),
        Api("label_width", "int", "150", "标签列宽，一列表单项靠它对齐"),
    ],
    notes=[
        tip(
            "回写读 ``e.control.value`` 而不是 ``e.data``：事件里的 data 是"
            "「true」/「false」字符串，两个都是真值，取消不掉开关。"
        ),
        info(
            "只读不改 value，只重绘一次让滑块弹回 —— 它保留「这是个开关」的外观，"
            "而禁用的是「这块不可用」。两种语义都别混用：需要表达无权限时用 disabled，"
            "需要表达「只有特定角色能改」时用 readonly。"
        ),
        info(
            "配色从写死的 WHITE / BLUE 换成了 ON_PRIMARY / PRIMARY，换主色或切深色"
            "主题时自动跟随；禁用时不指定颜色，让 M3 的禁用色走灰 —— 显式给的主色"
            "会盖掉禁用态，一个点不动的开关看起来仍然「开着」。"
        ),
    ],
    tags=("开关", "switch", "toggle", "设置", "表单"),
)


if __name__ == "__main__":
    run(SPEC)
