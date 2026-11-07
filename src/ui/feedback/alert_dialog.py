"""AlertDialog 确认对话框。

用在**必须被回答**的地方：删除前确认、离开未保存的表单、权限申请。它盖住页面、
挡住背后的操作，用户只能选「取消」或「确定」—— 这正是它与轻提示的分界。

用法::

    AlertDialog(
        title="删除这 3 个组件？",
        msg="删除后无法恢复。",
        style_type=StyleType.ERROR,   # 标题与确定按钮同时转红
        on_yes_click=lambda e: remove(),
        on_no_click=lambda e: log("取消"),
    ).show(page)

设计取舍
--------
- **标题条染色，而不是整框染色**：8% 的语义色只铺在标题条上，正文仍是正常面色。
  整框染色会让对话框比页面上的任何内容都响，反而看不清字。
- **图标是可选的**：``style_type=DEFAULT`` 不画图标 —— 只是问一句「确定吗」时，
  一个感叹号会把语气升级成事故。
- **确定按钮跟随语义**：``style_type=ERROR`` 时确定按钮变红，避免"红色警告 +
  蓝色确定"的割裂。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import field
from typing import Any

import flet as ft

from ui.core.constants import StyleType
from ui.core.doc import Api, Example, Spec, info, run, tip, warn
from ui.core.i18n import t
from ui.core.tokens import FONT_SIZE, FONT_WEIGHT, RADIUS, SPACE
from ui.input.button import Button

from ._look import accent as _accent
from ._look import icon_chip

__all__ = ["AlertDialog", "show_alert_dialog"]

#: 标题条的圆角，必须与对话框本体的圆角一致，否则上沿会露出白边
BORDER_RADIUS = RADIUS["xl"]
#: 操作按钮的高度：对话框里的按钮比页面上的主按钮矮一档，避免抢标题
ACTION_HEIGHT = 28


def _action_style() -> ft.ButtonStyle:
    """操作按钮的内边距。

    每次现造一份：``Button.init`` 会就地往传给它的 ``ButtonStyle`` 上写颜色，
    两个按钮共用一个对象会互相染色（取消按钮长出确定的底色）。
    """
    return ft.ButtonStyle(
        padding=ft.Padding.symmetric(horizontal=SPACE["3"], vertical=0)
    )


@ft.control
class AlertDialog(ft.AlertDialog):
    title: ft.Control | str | None = None
    msg: ft.StrOrControl = ""
    on_yes_click: Callable | None = None
    on_no_click: Callable | None = None
    style_type: StyleType = field(default_factory=lambda: StyleType.DEFAULT)

    def init(self):
        self.actions_padding = ft.Padding.only(right=SPACE["2"], bottom=SPACE["2"])
        #: 每个操作按钮四周的留白。原来是上下 16：两个 28px 的按钮撑出 60px 的操作区，
        #: 比标题条还高，视觉上把正文压没了。
        self.action_button_padding = ft.Padding.symmetric(
            horizontal=SPACE["1"], vertical=SPACE["2"]
        )
        self.actions_overflow_button_spacing = SPACE["2"]
        #: 对话框与窗口边缘的最小距离。写 0 时窄窗口下对话框会直接贴住窗口边。
        self.inset_padding = ft.Padding.symmetric(
            horizontal=SPACE["8"], vertical=SPACE["6"]
        )
        self.actions_alignment = ft.MainAxisAlignment.END
        self.shape = ft.RoundedRectangleBorder(radius=BORDER_RADIUS)

        # 自带标题才换成标题条；调用方传控件时保留原生标题的内边距
        if isinstance(self.title, str):
            self.title_padding = 0
            self.build_title(self.title)
        if self.content is None:
            # 只有自带的正文才去掉原生内边距：调用方传 content 时保留 24px 的默认留白
            self.content_padding = 0
            self.build_content()
        if len(self.actions) == 0:
            self.build_actions()

    # ------------------------------------------------------------------
    # 拼装
    # ------------------------------------------------------------------

    def build_title(self, title: str) -> None:
        """标题条：语义色 8% 的底 + 正文色标题，上沿圆角跟着对话框走。"""
        self.title = ft.Container(
            content=ft.Text(
                title,
                size=FONT_SIZE["title"],
                weight=FONT_WEIGHT["semibold"],
                color=ft.Colors.ON_SURFACE,
            ),
            bgcolor=ft.Colors.with_opacity(0.08, _accent(self.style_type)),
            padding=ft.Padding.symmetric(
                horizontal=SPACE["4"], vertical=SPACE["2"] + 2
            ),
            border_radius=ft.BorderRadius(
                top_left=BORDER_RADIUS,
                top_right=BORDER_RADIUS,
                bottom_left=0,
                bottom_right=0,
            ),
        )

    def build_content(self) -> None:
        """正文：图标块 + 一段说明。DEFAULT 不画图标，语气更轻。"""
        if isinstance(self.msg, str):
            body: ft.Control = ft.Text(
                self.msg,
                size=FONT_SIZE["body"],
                color=ft.Colors.ON_SURFACE_VARIANT,
                expand=True,
            )
        else:
            body = self.msg

        controls: list[ft.Control] = []
        if self.style_type != StyleType.DEFAULT:
            # 用淡底图标块而不是实底方块：黄底白图标只有 2:1 的对比度，读不出来
            controls.append(icon_chip(self.style_type, size=26, icon_size=17))
        controls.append(body)

        self.content = ft.Container(
            content=ft.Row(
                controls=controls,
                spacing=SPACE["3"],
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
            padding=ft.Padding.only(
                left=SPACE["4"],
                right=SPACE["4"],
                top=SPACE["3"],
                bottom=SPACE["3"],
            ),
        )

    def build_actions(self) -> None:
        """取消在左、确定在右。确定按钮的配色跟随 style_type。"""
        self.actions = []

        if self.on_no_click is not None:
            self.actions.append(
                Button(
                    content=ft.Text(t("ui.common.cancel")),
                    height=ACTION_HEIGHT,
                    style=_action_style(),
                    on_click=self._on_no_click,
                )
            )
        if self.on_yes_click is not None:
            self.actions.append(
                Button(
                    content=ft.Text(t("ui.common.ok")),
                    height=ACTION_HEIGHT,
                    style=_action_style(),
                    on_click=self._on_yes_click,
                    style_type=(
                        StyleType.ERROR
                        if self.style_type == StyleType.ERROR
                        else StyleType.PRIMARY
                    ),
                )
            )

        self.actions_alignment = ft.MainAxisAlignment.END

    # ------------------------------------------------------------------
    # 生命周期
    # ------------------------------------------------------------------

    def _on_yes_click(self, e):
        if self.on_yes_click is not None:
            self.on_yes_click(e)
        self.close(e.page)

    def _on_no_click(self, e):
        if self.on_no_click is not None:
            self.on_no_click(e)
        self.close(e.page)

    def show(self, page: ft.Page):
        """打开对话框。同一个实例要先关掉才能再次 show。"""
        page.show_dialog(self)

    def close(self, page: ft.Page):
        """关闭本对话框（只动这一层，不影响回调里新开的对话框）。"""
        self.open = False
        page.update()


def show_alert_dialog(page: ft.Page, alert_dialog: ft.AlertDialog):
    """把任意 ``ft.AlertDialog`` 以模态方式打开（点遮罩不关闭）。"""
    alert_dialog.modal = True
    page.show_dialog(alert_dialog)


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
def _caption(text: str) -> ft.Control:
    return ft.Text(text, size=FONT_SIZE["small"], color=ft.Colors.ON_SURFACE_VARIANT)


@ft.component
def _confirm() -> ft.Control:
    """最普通的确认：一句话 + 取消 / 确定，返回值写回按钮下方。"""
    page = ft.context.page
    result, set_result = ft.use_state("")

    def open_dialog(_e: Any) -> None:
        AlertDialog(
            title="保存并退出？",
            msg="「组件文档」还有 2 处修改没有发布，退出后会保留为草稿。",
            on_yes_click=lambda _ev: set_result("已保存并退出"),
            on_no_click=lambda _ev: set_result("留在当前页"),
        ).show(page)

    return ft.Column(
        spacing=12,
        controls=[
            Button(
                "打开确认框",
                style_type=StyleType.PRIMARY,
                plain=True,
                on_click=open_dialog,
            ),
            _caption(result or "点按钮：标题条染色、正文一行，底部「取消 / 确定」。"),
        ],
    )


@ft.component
def _danger() -> ft.Control:
    """危险操作：style_type=ERROR 时标题与确定按钮一起转红。"""
    page = ft.context.page
    result, set_result = ft.use_state("")

    def open_dialog(_e: Any) -> None:
        AlertDialog(
            title="删除这 3 个组件？",
            msg="删除后无法恢复，引用它们的页面会显示为空白。",
            style_type=StyleType.ERROR,
            on_yes_click=lambda _ev: set_result("已删除 3 个组件"),
            on_no_click=lambda _ev: set_result("已取消"),
        ).show(page)

    return ft.Column(
        spacing=12,
        controls=[
            Button(
                "打开危险确认",
                style_type=StyleType.ERROR,
                plain=True,
                on_click=open_dialog,
            ),
            _caption(
                result
                or "红色只出现在标题条、图标和确定按钮上：整框染红会让人先看见颜色，"
                "后看见字。"
            ),
        ],
    )


@ft.component
def _custom_content() -> ft.Control:
    """自定义正文：传 content 就完全接管中间那块，msg 不再生效。"""
    page = ft.context.page
    result, set_result = ft.use_state("")

    def open_dialog(_e: Any) -> None:
        AlertDialog(
            title="导出为 CSV",
            content=ft.Container(
                content=ft.Column(
                    spacing=SPACE["2"] + 2,
                    controls=[
                        ft.Text(
                            "导出范围",
                            size=FONT_SIZE["small"],
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        _fact(ft.Icons.TABLE_ROWS_OUTLINED, "当前页 · 第 3 页"),
                        _fact(ft.Icons.TAG_OUTLINED, "共 128 行，含表头"),
                        _fact(ft.Icons.DESCRIPTION_OUTLINED, "组件清单-2026-11-06.csv"),
                    ],
                ),
                padding=ft.Padding.only(
                    left=SPACE["4"],
                    right=SPACE["4"],
                    top=SPACE["3"],
                    bottom=SPACE["3"],
                ),
            ),
            on_yes_click=lambda _ev: set_result("文件已开始下载"),
            on_no_click=lambda _ev: set_result("已取消导出"),
        ).show(page)

    return ft.Column(
        spacing=12,
        controls=[
            Button("打开自定义正文", plain=True, on_click=open_dialog),
            _caption(result or "content 自己带内边距与排版，组件只负责外壳与按钮。"),
        ],
    )


def _fact(icon: ft.IconData, text: str) -> ft.Control:
    return ft.Row(
        spacing=SPACE["2"],
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Icon(icon, size=16, color=ft.Colors.PRIMARY),
            ft.Text(text, size=FONT_SIZE["body"], color=ft.Colors.ON_SURFACE),
        ],
    )


_CONFIRM_CODE = """from ui.core.constants import StyleType
from ui.feedback import AlertDialog

AlertDialog(
    title="保存并退出？",
    msg="还有 2 处修改没有发布，退出后会保留为草稿。",
    on_yes_click=lambda e: save_and_exit(),
    on_no_click=lambda e: None,       # 不传则不显示「取消」
).show(page)

# 危险操作：标题条、图标、确定按钮同时转红
AlertDialog(
    title="删除这 3 个组件？",
    msg="删除后无法恢复。",
    style_type=StyleType.ERROR,
    on_yes_click=lambda e: remove(),
    on_no_click=lambda e: None,
).show(page)"""


SPEC = Spec(
    name="AlertDialog",
    summary="必须被回答的确认框：挡住页面，只在「取消 / 确定」之间二选一。",
    definition=(
        "AlertDialog 处理的是「停下来做决定」：删除前确认、离开未保存的表单、"
        "权限申请。它盖住整页、拦住背后的点击，所以一屏里同时只该有一个。"
        "凡是可以用一句话说清、且不需要用户回应的反馈，都不该升级成对话框 —— "
        "用 Message 或 Notification，别用模态换一次点击。"
    ),
    anatomy=[
        (
            "标题条",
            (
                "语义色 8% 的底色 + 16px 半粗标题，上沿圆角与对话框一致。染色停在这"
                "一条上，正文区仍是正常面色，长文案照样好读。"
            ),
        ),
        (
            "图标块",
            (
                "26px 的淡底方块 + 类型图标，与正文同行。style_type=DEFAULT 不画 —— "
                "只是问一句「确定吗」时，一个感叹号会把语气升级成事故。"
            ),
        ),
        (
            "正文",
            (
                "13px 的次要色文字，一行说明「会发生什么」。传 content 时这一整块由"
                "调用方接管，msg 不再生效。"
            ),
        ),
        (
            "操作区",
            (
                "右下角「取消 / 确定」，28px 高、比页面主按钮矮一档。确定在右、"
                "取消在左，与平台习惯一致。"
            ),
        ),
        (
            "遮罩",
            (
                "半透明遮罩盖住背后的页面，挡住所有点击。默认点遮罩等于放弃"
                "（modal=False）；必须二选一时把它置 True。"
            ),
        ),
    ],
    when=[
        "删除、覆盖、退出这类不可逆或会丢数据的动作之前",
        "需要用户明确同意（权限、协议、付费）",
        "一个决定会改变后续流程，且必须留下「用户选了什么」",
    ],
    avoid=[
        "只是通知结果：用 Message，模态框会打断用户手上的事",
        "后台任务完成这类不需要立回应的消息：用 Notification",
        "一屏里连着弹第二个对话框：把两次确认合并成一次，或改成表单里的勾选",
    ],
    examples=[
        Example(
            "确认型",
            _confirm,
            hint="标题、正文、取消 / 确定；点完把结果写回按钮下方。",
            code=_CONFIRM_CODE,
        ),
        Example(
            "危险操作",
            _danger,
            hint="style_type=ERROR：标题条、图标、确定按钮一起转红。",
        ),
        Example(
            "自定义正文",
            _custom_content,
            hint="传 content 接管中间那块，用图标行列出影响范围。",
        ),
    ],
    api=[
        Api("title", "str | Control | None", "None", "标题；传字符串时自动套上标题条"),
        Api("msg", "str | Control", '""', "正文；只在没传 content 时生效"),
        Api(
            "style_type",
            "StyleType",
            "StyleType.DEFAULT",
            "语义类型，决定标题色与确定按钮色",
        ),
        Api("content", "Control | None", "None", "自定义正文；传了就忽略 msg"),
        Api(
            "on_yes_click",
            "Callable | None",
            "None",
            "点「确定」的回调；不传则不显示该按钮",
        ),
        Api(
            "on_no_click",
            "Callable | None",
            "None",
            "点「取消」的回调；不传则不显示该按钮",
        ),
        Api("show(page)", "None", "—", "打开对话框（page.show_dialog）"),
        Api("close(page)", "None", "—", "关闭本对话框，只动这一层"),
        Api(
            "modal",
            "bool",
            "False",
            "为 True 时点遮罩不关闭；show_alert_dialog 会打开它",
        ),
        Api(
            "actions",
            "list[Control]",
            "[]",
            "直接给按钮行；非空时跳过内置的取消 / 确定",
        ),
    ],
    notes=[
        tip(
            "按钮文案固定走语言包的「取消 / 确定」。要「删除」「稍后再说」这类"
            "动词，请自己传 actions —— 一旦 actions 非空，内置按钮就不再生成。"
        ),
        info(
            "标题条、图标与确定按钮共用 style_type：危险操作用 ERROR，三处会一起"
            "转红。标题条只上 8% 的底色，正文仍是正常面色，长文案不会变成一片红。"
            "对话框与窗口之间固定留 24/32 的内缩，窄窗口下也不会贴住边缘。"
        ),
        warn(
            "同一个 AlertDialog 实例不能连续 show 两次：page.show_dialog 对已打开的"
            "对话框会抛「Dialog is already opened」。每次打开请新建实例，或在 "
            "on_yes_click / on_no_click 里关掉它。"
        ),
    ],
    tags=("对话框", "弹窗", "确认", "dialog", "反馈"),
)


if __name__ == "__main__":
    run(SPEC)
