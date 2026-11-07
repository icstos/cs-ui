"""可编辑代码框 (CodeEditor) —— 多行、行号、语法高亮与 Tab 缩进。

它只做一件事：把 ``flet_code_editor`` 的编辑器内核收成本框架的默认值。代码输入
不是「多行文本 + 等宽字体」：缩进、行号、高亮、撤销重做都影响它能不能用，所以
这里不自己拼键盘处理，直接复用编辑器内核，再把语言、配色、字号、内边距固定成
一套可预期的值。

用法::

    CodeEditor(value=source, height=240, language=fce.CodeLanguage.PYTHON)
"""

from __future__ import annotations

import flet as ft
import flet_code_editor as fce

from ui.core.doc import Api, Example, Spec, info, run, tip, warn
from ui.core.tokens import FONT_SIZE, SPACE

__all__ = ["CodeEditor"]


@ft.control
class CodeEditor(fce.CodeEditor):
    """可编辑 / 只读的代码框。

    Args:
        value: 初始源码文本。
        language: 高亮语言，默认 Python。
        code_theme: 语法配色；默认暗色，明暗页面下都有一块明确边界。
        read_only: 只读；仍可选中、复制、滚动，适合展示。
        height: 可视高度；留空时至少保留 140px，避免空编辑器缩成一条线。
    """

    language: fce.CodeLanguage = fce.CodeLanguage.PYTHON
    code_theme: fce.CodeTheme = fce.CodeTheme.ATOM_ONE_DARK

    def init(self) -> None:
        """flet 生命周期：补齐编辑器自身没给的三项默认（留白 / 字号 / 最小高）。"""
        if self.padding is None:
            self.padding = ft.Padding.all(SPACE["3"])
        if self.text_style is None:
            self.text_style = ft.TextStyle(size=12.5, height=1.55)
        # 空内容时 CodeEditor 会缩成一条线；只给「没有显式高度」的情况兜底，
        # 调用方写了 height 就完全按调用方的来。
        if self.height is None and self.min_height is None:
            self.min_height = 140


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
_EDITOR_SNIPPET = '''def page_offset(page: int, size: int = 20) -> int:
    """第 1 页从 0 开始。"""
    return (page - 1) * size


for page in range(1, 4):
    print(page, page_offset(page))
'''

_LONG_SNIPPET = """queries = {
    "recent": "SELECT id, name, email, created_at FROM users WHERE tenant_id = 'acme' ORDER BY created_at DESC LIMIT 20",
    "count": "SELECT COUNT(*) FROM users WHERE tenant_id = 'acme' AND deleted_at IS NULL",
}

for name, sql in queries.items():
    print(name, sql)
"""


def _caret(text: str, offset: int) -> tuple[int, int]:
    """字符偏移 → (行, 列)，都从 1 开始。只做几次字符串查找，不做高亮计算。"""
    offset = max(0, min(offset, len(text)))
    line = text.count("\n", 0, offset) + 1
    column = offset - text.rfind("\n", 0, offset)
    return line, column


@ft.component
def _editable() -> ft.Control:
    """可输入：行列与字符数随光标 / 内容变化，初始内容是一小段 Python。"""
    info_state, set_info = ft.use_state((1, 1, len(_EDITOR_SNIPPET)))

    def track(event) -> None:
        text = event.control.value or ""
        selection = getattr(event, "selection", None)
        if selection is None:
            # on_change 只带文本：字符数立刻更新，行列沿用上一次光标位置。
            set_info(lambda old: (old[0], old[1], len(text)))
            return
        line, column = _caret(text, selection.extent_offset)
        set_info((line, column, len(text)))

    editor = ft.use_memo(
        lambda: CodeEditor(
            value=_EDITOR_SNIPPET,
            height=230,
            on_change=track,
            on_selection_change=track,
        ),
        [],
    )

    line, column, chars = info_state
    return ft.Column(
        spacing=SPACE["2"],
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        controls=[
            editor,
            ft.Text(
                f"第 {line} 行 · 第 {column} 列 · {chars} 字符",
                size=FONT_SIZE["small"],
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
        ],
    )


def _panel(title: str, editor: CodeEditor) -> ft.Control:
    """一个带说明的编辑器：说明在上，编辑器撑满列宽。"""
    return ft.Column(
        expand=True,
        spacing=SPACE["1"],
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        controls=[
            ft.Text(
                title,
                size=FONT_SIZE["small"],
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
            editor,
        ],
    )


@ft.component
def _read_only() -> ft.Control:
    """同一个内容、同一个高度：左边能改，右边只读但仍可选中复制。"""
    return ft.Row(
        spacing=SPACE["4"],
        vertical_alignment=ft.CrossAxisAlignment.START,
        controls=[
            _panel("可编辑：直接输入", CodeEditor(value=_EDITOR_SNIPPET, height=170)),
            _panel(
                "只读：能选中复制，改不了",
                CodeEditor(value=_EDITOR_SNIPPET, height=170, read_only=True),
            ),
        ],
    )


@ft.component
def _long_line() -> ft.Control:
    """缩进与长行：Tab 由内核处理，长行不折行，横向滚动。"""
    return ft.Column(
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        controls=[
            CodeEditor(
                value=_LONG_SNIPPET,
                language=fce.CodeLanguage.PYTHON,
                height=170,
            )
        ],
    )


_BASIC_CODE = """editor = CodeEditor(
    value=source,
    height=230,
    on_change=track,             # (event) -> None，文本变化
    on_selection_change=track,   # 光标移动也走同一个处理
)

Column([editor, Text(f"第 {line} 行 · 第 {column} 列")])

# 示例用 ft.use_memo 持有同一个编辑器实例：每次重绘重建 CodeEditor
# 并把 value 回写一遍，光标会跳回开头、滚动也会回到顶部。"""

_READONLY_CODE = """CodeEditor(value=source, height=170)                  # 可编辑
CodeEditor(value=source, height=170, read_only=True)    # 只读，仍可选中复制"""


SPEC = Spec(
    name="CodeEditor",
    summary="可编辑代码框：行号、语法高亮、Tab 缩进，取值仍走 value。",
    definition=(
        "代码输入不是「多行文本加等宽字体」。缩进、行号、高亮、括号与撤销重做都影响"
        "它能不能用，所以 CodeEditor 直接复用 flet_code_editor 的内核，只把默认值收成"
        "框架的一套：Python 高亮、12.5px、12px 内边距、140px 最小高度。它不接管取值，"
        "内容仍在 value 里，改完由调用方自己读。"
    ),
    anatomy=[
        (
            "编辑区",
            "多行文本；Tab 缩进、撤销重做、选中复制由编辑器内核处理，不用自己拦键盘。",
        ),
        (
            "行号槽",
            "gutter_style 控制行号、折叠柄与错误标记；默认三者全开，方便对照报错行。",
        ),
        (
            "语法高亮",
            "language 选规则，code_theme 选配色；换语言只换着色，不改内容。",
        ),
        (
            "光标与选择",
            "selection 与 on_selection_change 给出字符偏移，示例据此算出行列。",
        ),
        (
            "只读",
            "read_only=True 时键盘输入无效，但选中、复制、滚动仍然可用。",
        ),
        (
            "尺寸",
            "height 固定可视高度，超出在框内滚动；不折行，长行横向滚动。",
        ),
    ],
    when=[
        "用户要改脚本、配置、SQL 或一段结构化文本",
        "需要行号与高亮来定位错误（第几行、哪一段字符串）",
        "只读展示但仍希望读者能选中复制：read_only=True",
    ],
    avoid=[
        "一两行普通文本：用 Input(multiline=True)，它带标签、帮助文字与表单语义",
        "只是展示代码：用 Code 或 Json，省掉焦点、键盘与编辑器的开销",
        "运行日志：用 Text 或日志容器，语法高亮对日志没有增益",
    ],
    examples=[
        Example(
            "基础编辑",
            _editable,
            hint="初始内容是一小段 Python；下方实时显示行、列与字符数。",
            code=_BASIC_CODE,
            height=320,
        ),
        Example(
            "只读与可编辑",
            _read_only,
            hint="同一个片段、同一个高度：左边可改，右边只读但能选中复制。",
            code=_READONLY_CODE,
            height=250,
        ),
        Example(
            "缩进与长行",
            _long_line,
            hint="Tab 缩进由内核处理；长行不折行，在固定高度里横向滚动。",
            height=220,
        ),
    ],
    api=[
        Api("value", "str | None", "None", "初始 / 当前源码文本"),
        Api("language", "CodeLanguage", "PYTHON", "高亮语言，见 fce.CodeLanguage"),
        Api(
            "code_theme", "CodeTheme", "ATOM_ONE_DARK", "语法配色；固定调色板，不跟主题"
        ),
        Api("read_only", "bool", "False", "只读；仍可选中复制与滚动"),
        Api("text_style", "TextStyle | None", "None", "默认 12.5px / 行高 1.55"),
        Api("padding", "PaddingValue | None", "None", "默认 12px 内边距"),
        Api("height", "int | None", "None", "可视高度；留空时最小 140px"),
        Api(
            "gutter_style",
            "GutterStyle | None",
            "None",
            "行号 / 折叠柄 / 错误标记；默认全开",
        ),
        Api(
            "on_change",
            "Callable[[ControlEvent], None] | None",
            "None",
            "文本变化回调；取值用 event.control.value",
        ),
        Api(
            "on_selection_change",
            "Callable[[TextSelectionChangeEvent], None] | None",
            "None",
            "光标 / 选区变化回调，event.selection 是字符偏移",
        ),
    ],
    notes=[
        tip(
            "示例用 ft.use_memo 持有同一个编辑器实例。若每次 on_change 都重建 "
            "CodeEditor 并把 value 再写一遍，光标会跳回开头、滚动也会回到顶部。"
        ),
        info(
            "默认 code_theme 取 ATOM_ONE_DARK：语法配色是固定调色板，不随明暗主题走；"
            "选暗色是为了在浅色页面上也有一块明确的边界，要贴合页面就传 ATOM_ONE_LIGHT。"
        ),
        warn(
            "编辑器不会给长行折行。不给 height 时只保留 140px 的最小高度，内容多了"
            "在框内滚动；放进 Row 时记得给列 expand 或固定宽度。"
        ),
    ],
    tags=("代码编辑", "编辑器", "code editor", "代码框", "语法高亮"),
)


if __name__ == "__main__":
    run(SPEC)
