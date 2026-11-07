"""只读代码查看器 (CodeView) —— 演示控件 + 可折叠源码，带语言与复制。

CodeView 是组件文档里「效果 + 源码」的那一块：上面放正在演示的控件（可选），
下面一条折叠标题收住源码。代码本身不在这里渲染 —— 内部直接用
:class:`ui.display.text.Code`，行号、高亮、横向滚动都由它负责；本组件只补上
语言标签、复制按钮与折叠这一层壳。

用法::

    CodeView(
        code=source,
        component=ft.Switch(label="启用"),
        language=fce.CodeLanguage.PYTHON,
        expanded=True,
    )
"""

from __future__ import annotations

import logging
from collections.abc import Callable

import flet as ft
import flet_code_editor as fce

from ui.core.doc import Api, Example, Spec, info, run, tip, warn
from ui.core.i18n import t
from ui.core.tokens import FONT_SIZE, SPACE
from ui.display.text import Code
from ui.layout.expander import Expander

__all__ = ["CodeView"]

_log = logging.getLogger(__name__)

#: 语言枚举 → 标题栏上的短标签。没列到的语言退回 ``value`` 的首字母大写形式。
_LANG_LABEL: dict[fce.CodeLanguage, str] = {
    fce.CodeLanguage.PYTHON: "Python",
    fce.CodeLanguage.SQL: "SQL",
    fce.CodeLanguage.BASH: "Bash",
    fce.CodeLanguage.JAVASCRIPT: "JavaScript",
    fce.CodeLanguage.TYPESCRIPT: "TypeScript",
    fce.CodeLanguage.JSON: "JSON",
    fce.CodeLanguage.YAML: "YAML",
    fce.CodeLanguage.CPP: "C++",
    fce.CodeLanguage.CS: "C#",
    fce.CodeLanguage.GO: "Go",
    fce.CodeLanguage.RUST: "Rust",
    fce.CodeLanguage.JAVA: "Java",
    fce.CodeLanguage.MARKDOWN: "Markdown",
    fce.CodeLanguage.PLAINTEXT: "Text",
}


def _language_label(language: fce.CodeLanguage) -> str:
    """标题栏上的语言名：用人类写法（C++ / C# / JavaScript），不用枚举名。"""
    return _LANG_LABEL.get(language, language.value.replace("-", " ").title())


@ft.control
class CodeView(ft.Column):
    """演示控件 + 可折叠源码的只读查看器。

    Args:
        code: 源码文本。空字符串时不出现复制按钮。
        component: 放在源码上方的演示控件；``None`` 时只有代码。
        language: 高亮语言，决定代码着色与标题栏标签。
        title: 折叠标题；留空跟随界面语言（「查看代码 / View code」）。
        expanded: 初始是否展开，默认收起。
        height: 代码区可视高度；``None`` 时由内容撑开。
        copyable: 是否在标题栏放复制按钮，默认 ``True``。
        on_copy: 复制后的回调，示例里用它回写一行「已复制」。
    """

    code: str = ""
    component: ft.Control | None = None
    language: fce.CodeLanguage = fce.CodeLanguage.PYTHON
    title: str = ""
    expanded: bool = False
    height: int | None = None
    copyable: bool = True
    on_copy: Callable[[], None] | None = None

    def init(self) -> None:
        """flet 生命周期：演示控件在上，代码面板在下，一次性搭好。"""
        #: 首次复制时创建的 Clipboard 服务；Service 会自动注册到当前页。
        self._clipboard: ft.Clipboard | None = None
        trailing: list[ft.Control] = [
            ft.Text(
                _language_label(self.language),
                size=FONT_SIZE["caption"],
                color=ft.Colors.OUTLINE,
            )
        ]
        if self.copyable and self.code:
            trailing.append(
                ft.IconButton(
                    icon=ft.Icons.CONTENT_COPY,
                    icon_size=14,
                    icon_color=ft.Colors.ON_SURFACE_VARIANT,
                    tooltip="复制代码",
                    width=26,
                    height=26,
                    padding=ft.Padding.all(2),
                    on_click=self._handle_copy,
                )
            )

        # 演示控件必须在第一帧就位；放进 did_mount 再 insert 的话，
        # 首次渲染拿不到它，要等下一次 update 才出现。
        if self.component is not None:
            self.controls.insert(0, self.component)
        self.controls.append(
            Expander(
                title=self.title or t("ui.codeview.title"),
                trailing=ft.Row(
                    spacing=SPACE["1"],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=trailing,
                ),
                controls=[
                    Code(
                        value=self.code,
                        language=self.language,
                        height=self.height,
                    )
                ],
                dense=True,
                expanded=self.expanded,
            )
        )
        # 代码块要吃掉整行：否则长行会把 Column 撑宽，而不是在框内横向滚动。
        self.horizontal_alignment = ft.CrossAxisAlignment.STRETCH

    async def _handle_copy(self, _event) -> None:
        """把整段源码写进剪贴板，成功后再回调调用方做回显。

        这里在点击时才创建 :class:`ft.Clipboard`，而不是在 ``init`` 里构造
        ``ft.CopyToClipboard``：后者会立刻读取 ``ft.context.page``，组件在页面
        之外先建好（很常见的组装方式）就会直接抛 RuntimeError。
        """
        clipboard = self._clipboard
        if clipboard is None:
            clipboard = ft.Clipboard()
            self._clipboard = clipboard
        try:
            await clipboard.set(self.code)
        except (ft.FletException, RuntimeError, TimeoutError, OSError) as exc:
            # 系统剪贴板不可用（或客户端已断开）不该拖垮整个页面。
            _log.warning("复制代码到剪贴板失败：%s", exc)
            return
        if self.on_copy is not None:
            self.on_copy()


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
#: 取自本框架分页器的真实片段：21 行，够长到能看出行号与高亮的节奏。
_FRAMEWORK_SNIPPET = '''def _page_width(label: str) -> int:
    """两位数以内是正方形，三位数起按字数往外让。"""
    return max(32, 8 * 2 + 8 * len(label))


def _hover_handler(key: str, set_hovered: Callable) -> Callable:
    def handler(e, _key=key, _set=set_hovered):
        _set(_key if str(e.data) == "true" else "")

    return handler


def get_center_pages(current: int, total: int) -> list:
    """当前页居中，两侧放省略号。"""
    match (total, current):
        case (s, _) if s <= 6:
            return list(range(1, s + 1))
        case (s, c) if c < 5:
            return list(range(1, 6)) + [-1, s]
        case (s, c):
            return [1, -1] + list(range(c - 2, c + 3)) + [-1, s]
'''

#: 一行 160 字符：代码区不折行，只能在框内横向滚动。
_LONG_LINE_SNIPPET = """# 下面这行是一条完整的查询，故意不换行
QUERY = "SELECT id, name, email, created_at, updated_at FROM users WHERE tenant_id = 'acme' AND deleted_at IS NULL ORDER BY created_at DESC LIMIT 20 OFFSET 40"

cursor.execute(QUERY)
for row in cursor.fetchall():
    print(row)
"""


@ft.component
def _basic() -> ft.Control:
    """21 行框架源码：行号、语言标签与复制按钮都在标题栏上。"""
    copied, set_copied = ft.use_state(False)
    return ft.Column(
        spacing=SPACE["2"],
        controls=[
            CodeView(
                code=_FRAMEWORK_SNIPPET,
                language=fce.CodeLanguage.PYTHON,
                expanded=True,
                on_copy=lambda: set_copied(True),
            ),
            ft.Text(
                "已复制 21 行到剪贴板"
                if copied
                else "点标题栏右侧的复制图标，整段代码进剪贴板",
                size=FONT_SIZE["small"],
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
        ],
    )


@ft.component
def _long_line() -> ft.Control:
    """长行不折行：固定高度后，横向滚动条留在代码框内部。"""
    return CodeView(
        code=_LONG_LINE_SNIPPET,
        language=fce.CodeLanguage.PYTHON,
        expanded=True,
        height=146,
    )


@ft.component
def _with_component() -> ft.Control:
    """component 放在标题上方：上面是效果，下面是源码，默认收起。"""
    return CodeView(
        code="Pagination(PaginationState(sum_data_nums=1_286))",
        component=ft.Text(
            "这一行是 component：它永远在折叠标题上方。",
            size=FONT_SIZE["body"],
            color=ft.Colors.ON_SURFACE_VARIANT,
        ),
        expanded=False,
    )


_BASIC_CODE = """CodeView(
    code=source,
    language=fce.CodeLanguage.PYTHON,
    expanded=True,
    on_copy=lambda: set_copied(True),   # 只做回显，复制在组件里完成
)

# 需要演示区就再加一个控件：它永远在折叠标题上方
CodeView(code=source, component=ft.Switch(label="启用"), expanded=False)"""


SPEC = Spec(
    name="CodeView",
    summary="演示控件 + 可折叠源码：行号、高亮、语言标签与一键复制。",
    definition=(
        "CodeView 解决的是「组件文档要同时给出效果和源码」：上面放正在运行的控件，"
        "下面用一条折叠标题收住对应源码，读者看完效果就能把代码拿走。它不重新实现"
        "代码渲染，内部就是 display.text 里的 Code；多出来的只是语言标签、复制按钮"
        "和折叠这一层壳。"
    ),
    anatomy=[
        (
            "演示区",
            "component 非空时置顶，原样显示被说明的控件；为空时整块只剩代码面板。",
        ),
        (
            "折叠标题",
            "默认「查看代码」，整条可点；compact 密度 36 高，收起时只占一行。",
        ),
        (
            "语言标签",
            "language 换成 Python / SQL / C++ 这类人类写法，排在复制按钮左侧。",
        ),
        (
            "复制按钮",
            "标题栏右侧的图标，点击把整段源码写进剪贴板，并在示例里回显一行状态。",
        ),
        (
            "代码区",
            "内部是 Code：等宽字体、行号、语法高亮；长行不折行，横向滚动。",
        ),
    ],
    when=[
        "组件文档要同时给「效果」与「源码」，且源码不必一直占着屏幕",
        "源码较长，默认收起，读者需要时再展开",
        "希望读者一键把整段示例复制到自己的编辑器里",
    ],
    avoid=[
        "只摆一段代码、不需要演示区：直接用 Code，少一层折叠与标题",
        "需要用户修改代码：用 CodeEditor，CodeView 的 code 是只读文本",
        "代码是长文档的一部分：用 Markdown 的围栏代码块，能跟着正文排版",
    ],
    examples=[
        Example(
            "基础用法",
            _basic,
            hint="21 行框架源码；标题栏上有 Python 标签与复制按钮，点击后下方回显一行状态。",
            code=_BASIC_CODE,
            height=560,
        ),
        Example(
            "长行",
            _long_line,
            hint="一行近 160 字符的查询：不折行、不撑宽，横向滚动条留在代码框内部。",
            height=240,
        ),
        Example(
            "带演示控件",
            _with_component,
            hint="component 放在折叠标题上方；源码默认收起，只留一行标题。",
            height=160,
        ),
    ],
    api=[
        Api("code", "str", "''", "源码文本；为空时不显示复制按钮"),
        Api("component", "ft.Control | None", "None", "放在源码上方的演示控件"),
        Api("language", "CodeLanguage", "PYTHON", "高亮语言，同时决定标题栏标签"),
        Api("title", "str", "''", "折叠标题；留空跟随界面语言"),
        Api("expanded", "bool", "False", "初始是否展开；之后由 Flutter 持有"),
        Api("height", "int | None", "None", "代码区可视高度；留空由内容撑开"),
        Api("copyable", "bool", "True", "是否显示复制按钮"),
        Api(
            "on_copy",
            "Callable[[], None] | None",
            "None",
            "复制后的回调，用来回显「已复制」",
        ),
    ],
    notes=[
        tip(
            "复制在点击时创建 Clipboard 服务，而不是在 init 里构造 CopyToClipboard ——"
            "后者会立刻读页面上下文，组件在加入页面之前先建好就会抛 RuntimeError。"
            "剪贴板本身不可用时只记一条警告，on_copy 不会被调用，不会出现假的「已复制」。"
        ),
        info(
            "component 在 init 阶段就插到 controls 最前面，而不是等 did_mount 再插入 ——"
            "后者要等下一次页面更新才出现，首帧会少一块。"
        ),
        warn(
            "height 只限制可视高度，不改变换行策略：长行仍然横向滚动。"
            "要整段看完就把 height 留空，让内容自己撑开。"
        ),
    ],
    tags=("代码查看", "源码", "code view", "查看代码", "复制代码"),
)


if __name__ == "__main__":
    run(SPEC)
