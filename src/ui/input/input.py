"""文本输入 (Input) —— 标签、占位提示、前后缀与失焦校验。

``Input`` 不是 :class:`flet.TextField` 的薄封装：它把「标签 + 输入框」的排版、
36px 基线、描边状态色一起定死，让一列表单控件不必各自调内边距。标签放在左侧还是
上方由 ``is_vertical`` 决定，冒号自动补（``label`` 自带 ``:`` 时不重复），必填只在
标签前加一枚 ``*``。

输入内容始终写回 ``self.value``：组件是受控的，调用方读 ``value`` 就是最新值，不需要
关心 flet 的事件对象。数字类型（``data_type="int" / "float"``）不在这里处理，直接转交
:class:`~ui.input.number_input.NumberInput` —— 两套数值逻辑各自漂移过一次，代价是
范围与精度在两处行为不一致。

用法::

    name = Input(label="用户名", hint_text="6-20 位字母或数字", is_required=True)
    Column([name.ui()])
    print(name.value)
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import flet as ft

from ui.core.doc import Api, Example, Spec, info, run, tip, warn
from ui.core.styles import outline_input
from ui.core.tokens import FONT_SIZE, RADIUS, SPACE

__all__ = ["Input", "Label"]

ICON_SIZE = 16
#: 标签字号：比正文大一档（正文 13），标签仍然略重，但不至于压过输入内容。
#: 以前写死 16，比输入文字大一号，两行挤在一起时读起来像两个标题。
LABEL_SIZE = FONT_SIZE["subtitle"]
BORDER_RADIUS = RADIUS["lg"]
DEFAULT_FORM_HEIGHT = 36
SPACING = SPACE["2"]  # 标签与输入框之间


def _is_true(payload: object) -> bool:
    """把 hover / toggle 事件载荷归一成布尔（可能是 ``True``，也可能是 ``"true"``）。"""
    if isinstance(payload, bool):
        return payload
    return str(payload).strip().lower() in {"true", "1", "yes"}


@ft.observable
@dataclass
class Label:
    label: str | None = None
    label_width: int = 150
    is_vertical: bool = False
    is_required: bool = False
    spacing: ft.Number = 10
    run_spacing: ft.Number = 10

    @property
    def v_label(self):
        if self.label is not None:
            if self.is_required:
                spans = [
                    # 必填星号走 ERROR 角色色：写死 RED 在深色主题下会和其他语义红脱节
                    ft.TextSpan(text="*", style=ft.TextStyle(color=ft.Colors.ERROR)),
                    ft.TextSpan(self.label),
                ]
            else:
                spans = [ft.TextSpan(text=self.label)]
            if self.label.endswith(":") or self.label.endswith("："):
                pass
            else:
                #     self.label = self.label + ": " # NOTE, 在前面走这处，程序就死机了
                spans.append(ft.TextSpan(text=": "))
            return ft.Text(
                spans=spans,
                text_align=ft.TextAlign.START if self.is_vertical else ft.TextAlign.END,
                width=self.label_width,
                size=LABEL_SIZE,
            )
        else:
            return None


@ft.observable
@dataclass
class Input(Label):
    """单行 / 多行文本输入：标签、占位提示、前后缀、帮助与错误文案。

    Args:
        value: 当前值。``None`` 与空串等价，都会显示 ``hint_text``。
        hint_text: 空值时的占位提示，写"应该填什么"，不要写"请输入"。
        helper_text: 输入框下方的常驻说明；有 ``error_text`` 时让位给错误。
        error_text: 校验失败文案；非空时描边走 ``ERROR`` 状态并显示这一行。
        password: 密码框，内容以圆点显示，并可点眼睛临时查看。
        disabled: 整体禁用；``None`` 值仍会以 ``""`` 显示。
        on_submit: 回车时回调，入参是当前文本。
        on_blur: 失焦时回调，入参是当前文本；校验通常挂在这里。
    """

    value: int | float | Decimal | str | Path | None = None
    last_value: int | float | Decimal | str | Path | None = None
    hint_text: str | None = None
    multiline: bool = False
    data_type: str = "str"
    step: int | float = 0.01
    width: int = 500
    helper_text: str | None = None
    error_text: str | None = None
    password: bool = False
    disabled: bool = False
    on_submit: Callable[[str], None] | None = None
    on_blur: Callable[[str], None] | None = None

    def __post_init__(self):
        self.last_value = self.value
        # 数字类型（int / float）的实现在 NumberInput 里，这里只持有实例并桥接取值。
        self._num = None

    # min_value: ft.Number = -math.inf
    # max_value: ft.Number = math.inf
    @property
    def path(self) -> Path | None:
        if self.value is None or len(str(self.value).strip()) == 0:
            return None
        else:
            return Path(str(self.value).strip().strip('"').strip("'"))

    def on_change(self, e):
        """文本类输入的回写（数字类型走 :meth:`_on_number_change`）。"""
        self.value = e.data

    def _text(self) -> str:
        return "" if self.value is None else str(self.value)

    def _on_number_change(self, value: float | None) -> None:
        """NumberInput 的值回写到 ``Input.value``，外部读到的始终是最新值。"""
        self.value = value
        self.last_value = value
        self.notify()

    def _number_ui(self) -> ft.Control:
        """数字类型：渲染交给 :class:`~ui.input.number_input.NumberInput`。

        步进 / 精度 / 范围 / 单位都在那边实现，这里只做「标签参数 + 值」的搬运，
        避免两套数值处理逻辑各自漂移。

        ``NumberInput`` 继承自本模块的 :class:`Label`，所以在函数内延迟导入，
        避免模块级循环依赖。
        """
        from ui.input.number_input import NumberInput

        if self._num is None:
            self._num = NumberInput(
                label=self.label,
                label_width=self.label_width,
                is_vertical=self.is_vertical,
                is_required=self.is_required,
                spacing=self.spacing,
                run_spacing=self.run_spacing,
                value=self.value,
                step=1 if self.data_type == "int" else (self.step or 0.01),
                precision=0 if self.data_type == "int" else None,
                width=self.width,
                hint_text=self.hint_text,
                disabled=self.disabled,
                on_change=self._on_number_change,
            )
        # 外部改了 Input.value 时同步下来；值没变时 set_value 内部直接返回
        self._num.set_value(self.value)
        return self._num.ui()

    async def handle_file_picker(self, e):
        self.selected_files = await e.control.pick_files(allow_multiple=False)
        if self.selected_files is not None and len(self.selected_files) > 0:
            self.value = str(self.selected_files[0].path)

    @ft.component
    def ui(
        self,
        prefix: ft.Control | None = None,
        suffix: ft.Control | None = None,
        prefix_icon: ft.Control | None = None,
    ):
        """构建输入控件。

        数字类型（``data_type="int"/"float"``）直接交给
        :class:`~ui.input.number_input.NumberInput`，``prefix`` / ``suffix`` /
        ``prefix_icon`` 只对文本与文件类型生效 —— 数字框的单位请用
        ``NumberInput`` 的 ``prefix`` / ``suffix`` 字符串参数。
        """
        if self.data_type == "int" or self.data_type == "float":
            return self._number_ui()

        keyboard_type: ft.KeyboardType = ft.KeyboardType.TEXT
        if self.data_type == "file" or self.data_type == "dir":
            is_pick, set_is_pick = ft.use_state(False)
            content_padding: ft.Padding = ft.Padding.only(
                left=5, right=10, top=0, bottom=0
            )

            async def handle_file_picker(e):
                selected_files = await v_file_picker.pick_files(allow_multiple=False)
                if selected_files is not None and len(selected_files) > 0:
                    self.value = str(selected_files[0].path)
                    # 选完文件立刻重绘，否则框里还是旧路径（取值成功但界面不动）
                    self.notify()

            async def handle_dir_picker(e):
                seleted_dir = await v_file_picker.get_directory_path()
                if seleted_dir is not None:
                    self.value = str(seleted_dir)
                    self.notify()

            v_file_picker = ft.FilePicker()
            # NOTE: prefix的话，需要移到上面才会显示
            prefix_icon = ft.Container(
                content=ft.Icon(
                    icon=ft.Icons.FILE_OPEN_OUTLINED
                    if self.data_type == "file"
                    else ft.Icons.FOLDER_OPEN_OUTLINED,
                    size=ICON_SIZE,
                    color=ft.Colors.ON_PRIMARY if is_pick else None,
                ),
                on_click=handle_file_picker
                if self.data_type == "file"
                else handle_dir_picker,
                bgcolor=ft.Colors.PRIMARY if is_pick else None,
                # e.data 是 "true"/"false" 字符串，直接塞进 state 会让"离开"也被当成 True
                on_hover=lambda e: set_is_pick(_is_true(e.data)),
                border_radius=ft.BorderRadius(
                    top_left=BORDER_RADIUS,
                    top_right=0,
                    bottom_left=BORDER_RADIUS,
                    bottom_right=0,
                ),
            )

        else:
            if prefix and not suffix:
                content_padding = ft.Padding.only(left=10, right=5)
            elif suffix and not prefix:
                content_padding = ft.Padding.only(left=5, right=10)
            elif prefix and suffix:
                content_padding = ft.Padding.symmetric(horizontal=10)
            else:
                content_padding = ft.Padding.all(1)

        def _on_change(e):
            self.on_change(e)
            self.notify()

        def _on_submit(e):
            if self.on_submit is not None:
                self.on_submit(self._text())

        def _on_blur(e):
            if self.on_blur is not None:
                self.on_blur(self._text())

        # 有 helper / error 时不能再锁 36 高：第二行会顶出框外被裁掉
        has_message = bool(self.helper_text or self.error_text)
        v_ui = ft.TextField(
            value=self._text(),
            cursor_color=ft.Colors.PRIMARY,
            selection_color=ft.Colors.with_opacity(0.24, ft.Colors.PRIMARY),
            hover_color=ft.Colors.with_opacity(0.08, ft.Colors.PRIMARY),
            border=outline_input(
                BORDER_RADIUS, ft.Colors.OUTLINE_VARIANT, ft.Colors.PRIMARY
            ),
            cursor_width=1,
            hint_text=self.hint_text,
            helper=self.helper_text,
            error=self.error_text,
            multiline=self.multiline,
            min_lines=3 if self.multiline else None,
            # 描边 + 透明底。以前铺 ``SURFACE_CONTAINER_HIGHEST``：那是 M3 里
            # 最重的一档容器色，在 1.1 的中性表面下就成了一块灰 —— 和卡片底、
            # 和旁边的只读框全糊在一起，边界只剩一圈比它更淡的线。
            filled=False,
            height=None if self.multiline or has_message else DEFAULT_FORM_HEIGHT,
            text_align=ft.TextAlign.START,
            keyboard_type=keyboard_type,
            content_padding=content_padding,
            suffix=suffix,
            prefix=prefix,
            prefix_icon=prefix_icon,
            password=self.password,
            can_reveal_password=self.password,
            disabled=self.disabled,
            on_change=None if self.disabled else _on_change,
            on_submit=None if self.disabled else _on_submit,
            on_blur=None if self.disabled else _on_blur,
            width=self.width,
        )
        if self.v_label is not None:
            if self.is_vertical:
                return ft.Column(
                    controls=[self.v_label, v_ui],
                    spacing=SPACE["1"],
                )
            else:
                return ft.Row(
                    controls=[self.v_label, v_ui],
                    spacing=SPACING,
                    # 36 高的输入框要跟标签的中线对齐；默认 START 时标签会浮在框顶
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    width=self.label_width + self.width + SPACING,
                )
        else:
            return v_ui


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
def _caption(text: str) -> ft.Control:
    return ft.Text(text, size=FONT_SIZE["small"], color=ft.Colors.ON_SURFACE_VARIANT)


@ft.component
def _basic() -> ft.Control:
    """标签 + 占位提示 + 帮助文字；密码框是同一套输入框的另一种形态。"""
    username = ft.use_memo(
        lambda: Input(
            label="用户名",
            hint_text="6-20 位字母或数字",
            helper_text="登录后不可修改",
            is_required=True,
            width=300,
        ),
        [],
    )
    password = ft.use_memo(
        lambda: Input(
            label="密码",
            hint_text="至少 8 位",
            password=True,
            width=300,
        ),
        [],
    )
    return ft.Column(
        spacing=14,
        controls=[
            username.ui(),
            password.ui(),
            _caption(
                f"用户名「{username.value or ''}」 · 密码 {len(str(password.value or ''))} 位"
            ),
        ],
    )


@ft.component
def _affixes() -> ft.Control:
    """前缀给语义（搜索图标 / 协议），后缀做清除 —— 都长在框里，不额外占一行。"""
    keyword = ft.use_memo(
        lambda: Input(label="关键词", hint_text="搜索项目名称", width=320),
        [],
    )
    site = ft.use_memo(
        lambda: Input(label="站点", hint_text="example", width=320),
        [],
    )

    def clear(_e):
        keyword.value = ""
        keyword.notify()

    # 没内容时不显示清除键：一个点了没反应的叉，比没有更差
    suffix = (
        ft.IconButton(
            icon=ft.Icons.CLOSE,
            icon_size=14,
            width=26,
            height=26,
            tooltip="清空",
            style=ft.ButtonStyle(padding=ft.Padding.all(0)),
            on_click=clear,
        )
        if keyword.value
        else None
    )

    return ft.Column(
        spacing=14,
        controls=[
            keyword.ui(
                prefix=ft.Icon(
                    ft.Icons.SEARCH, size=16, color=ft.Colors.ON_SURFACE_VARIANT
                ),
                suffix=suffix,
            ),
            site.ui(
                prefix=ft.Text(
                    "https://",
                    size=FONT_SIZE["small"],
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
                suffix=ft.Text(
                    ".com", size=FONT_SIZE["small"], color=ft.Colors.ON_SURFACE_VARIANT
                ),
            ),
            _caption("前缀写协议或图标；后缀只做展示与清空，不进入 value。"),
        ],
    )


def _email_input() -> Input:
    field = Input(
        label="邮箱",
        hint_text="name@example.com",
        helper_text="用于接收通知",
        is_required=True,
        width=300,
    )

    def check(_value: str = "") -> None:
        text = str(field.value or "").strip()
        if not text:
            field.error_text = "请填写邮箱"
        elif "@" not in text or "." not in text.rsplit("@", 1)[-1]:
            field.error_text = "邮箱格式不正确"
        else:
            field.error_text = None
        field.notify()  # type: ignore[attr-defined]

    # 失焦与回车各校验一次；边敲边报错会把用户按在错误里
    field.on_blur = check
    field.on_submit = check
    return field


def _staff_input() -> Input:
    field = Input(label="工号", hint_text="A-1024", width=300)

    def check(_value: str = "") -> None:
        text = str(field.value or "").strip()
        field.error_text = None if text.upper().startswith("A-") else "工号以 A- 开头"
        field.notify()  # type: ignore[attr-defined]

    field.on_blur = check
    field.on_submit = check
    return field


@ft.component
def _validation() -> ft.Control:
    """校验失败态：错误文案走 ERROR 角色色，描边同时切成错误色。"""
    email = ft.use_memo(_email_input, [])
    staff = ft.use_memo(_staff_input, [])

    def reset(_e):
        for field in (email, staff):
            field.value = ""
            field.error_text = None
            field.notify()  # type: ignore[attr-defined]

    return ft.Column(
        spacing=14,
        controls=[
            email.ui(),
            staff.ui(),
            ft.Row(
                controls=[ft.Button(content="重置", on_click=reset)],
            ),
            _caption("失焦或回车才校验：空值报「请填写邮箱」，缺域名报格式错误。"),
        ],
    )


_BASIC_CODE = """username = Input(
    label="用户名",
    hint_text="6-20 位字母或数字",
    helper_text="登录后不可修改",
    is_required=True,
    width=300,
)
Column([username.ui()])"""

_AFFIX_CODE = """def clear(_e):
    keyword.value = ""
    keyword.notify()

keyword = Input(label="关键词", hint_text="搜索项目名称", width=320)
Column([
    keyword.ui(
        prefix=ft.Icon(ft.Icons.SEARCH, size=16),
        suffix=ft.IconButton(icon=ft.Icons.CLOSE, icon_size=14, on_click=clear),
    ),
])"""

_VALIDATION_CODE = """email = Input(
    label="邮箱", hint_text="name@example.com", is_required=True, width=300,
)

def validate(_value: str = "") -> None:
    text = str(email.value or "").strip()
    if not text:
        email.error_text = "请填写邮箱"
    elif "@" not in text or "." not in text.rsplit("@", 1)[-1]:
        email.error_text = "邮箱格式不正确"
    else:
        email.error_text = None
    email.notify()

email.on_blur = validate      # 离开输入框
email.on_submit = validate    # 回车"""


SPEC = Spec(
    name="Input",
    summary="单行文本输入：标签、占位提示、前后缀，以及失焦时的校验。",
    definition=(
        "文本框负责收一段自由文本。它把标签排版、36px 基线与四种描边状态一起收进"
        "组件，表单里并排的字段才不会一行高一行矮。值始终落在 ``value`` 上，改动"
        "即回写，调用方不需要从事件对象里再取一次。错误文案不是另贴一行红字，而是"
        "交给输入框自己的 error 行 —— 边框、文案、间距一起进入失败态。"
    ),
    anatomy=[
        ("标签", "左侧或上方，冒号自动补；必填只在标签前加一枚星号，不另占一行。"),
        ("输入框", "默认 36px 高、8px 圆角、1px 描边；聚焦转主色，失败转错误色。"),
        (
            "占位提示",
            "空值时才出现，写清格式（「6-20 位字母或数字」），而不是重复标签。",
        ),
        (
            "前后缀",
            "前缀放图标或协议（https://），后缀放单位或清除键；它们不进入 value。",
        ),
        (
            "帮助 / 错误行",
            "输入框下方一行小字：常态是帮助，校验失败时换成错误并改用错误色。",
        ),
    ],
    when=[
        "用户名、邮箱、标题这类自由文本，长度或格式需要提示",
        "表单里要一列左标签、右输入框的整齐排版",
        "需要在框内提示输入范围（域名前缀、搜索图标、清空键）",
    ],
    avoid=[
        "数字、金额、百分比：用 NumberInput，它有步进、精度和范围夹紧",
        "只能在几个固定值里选：用 SelectBox / Radio，文本框会让人以为可以随便填",
        "需要边输入边筛选的弹层选择：用 SelectBox / MultiSelect，别自己拼下拉",
    ],
    examples=[
        Example(
            "基础与密码",
            _basic,
            hint="标签、占位提示、帮助文字各一层；密码框复用同一个组件，眼睛可临时查看。",
            code=_BASIC_CODE,
        ),
        Example(
            "前后缀与清除",
            _affixes,
            hint="前缀给语义，后缀放清除键；没有内容时清除键不出现，避免空点。",
            code=_AFFIX_CODE,
        ),
        Example(
            "失焦校验",
            _validation,
            hint="空值与格式错误分别给文案；修正后再次失焦即恢复常态。",
            code=_VALIDATION_CODE,
        ),
    ],
    api=[
        Api(
            "value",
            "str | int | float | Path | None",
            "None",
            "当前值；改动即回写，读它就是最新文本",
        ),
        Api("label", "str | None", "None", "标签文案；冒号自动补，自带冒号不重复"),
        Api(
            "data_type",
            "str",
            "'str'",
            "str / int / float / file / dir；数字类型转交 NumberInput",
        ),
        Api(
            "hint_text", "str | None", "None", "空值时的占位提示，写格式而非「请输入」"
        ),
        Api("helper_text", "str | None", "None", "框下常驻说明；有错误时让位给错误"),
        Api("error_text", "str | None", "None", "失败文案；非空时描边切成错误色"),
        Api("password", "bool", "False", "密码框，圆点显示并带「眼睛」临时查看"),
        Api("width", "int", "500", "输入框宽度；标签宽度另由 label_width 控制"),
        Api("is_required", "bool", "False", "标签前加星号；校验仍由调用方决定"),
        Api(
            "on_blur",
            "Callable[[str], None] | None",
            "None",
            "失焦回调，入参为当前文本；回车校验用 on_submit，签名相同",
        ),
    ],
    notes=[
        info(
            "有 helper / error 时组件不再锁 36px 高：固定高度会把第二行裁掉，"
            "错误文案等于没显示。没有消息时仍回到 36px，和按钮、下拉框对齐。"
        ),
        tip(
            "校验挂在 on_blur / on_submit，而不是 on_change。边敲边报错会让用户"
            "在还没输完时就看到失败；失焦才判定，符合「填完这一格」的心理节奏。"
        ),
        warn(
            "数字类型别指望这里的 prefix / suffix：data_type 是 int / float 时"
            "整段渲染交给 NumberInput，单位请用它自己的 prefix / suffix。"
        ),
    ],
    tags=("输入", "文本框", "input", "textfield", "表单"),
)


if __name__ == "__main__":
    run(SPEC)
