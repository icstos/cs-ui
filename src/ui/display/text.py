"""文本与富文本 (Text / Heading / Quote / Link / Markdown / Code / Json)。

这一组组件都在解决「一段内容怎么显示」：

* :class:`Text` 是正文；:class:`Header_1` … :class:`Header_6` 是六级标题；
* :class:`Quote` 给一段话划出边界，:class:`Link` 让文字可点；
* :class:`Markdown` / :class:`Code` / :class:`Json` 负责三种「来自别处」的文本 ——
  markdown 文档、源码、JSON 数据。

颜色与字号全部走 :mod:`ui.core.tokens` 和 ``ft.Colors`` 的角色色，明暗主题与
主色切换时不需要改一行组件代码。
"""

from __future__ import annotations

import webbrowser
from dataclasses import field

import flet as ft
import flet_code_editor as fce

from ui.core import typography
from ui.core.doc import Api, Example, Spec, info, run, tip, warn
from ui.core.tokens import FONT_SIZE, FONT_WEIGHT, RADIUS, SPACE, disabled_layer

__all__ = [
    "SPECS",
    "Code",
    "Header",
    "Header_1",
    "Header_2",
    "Header_3",
    "Header_4",
    "Header_5",
    "Header_6",
    "Json",
    "Link",
    "Markdown",
    "Quote",
    "SubHeader",
    "SubTitle",
    "Text",
    "Title",
]

Text = ft.Text


# ---------------------------------------------------------------------------
# 标题：六级
#
# 字号不再交给 M3 的 theme_style 槽位：那条路会把"类名"与"像素"隔开一层，
# 主题一改映射，H2 就可能比 H3 还小（实测发生过：headline_large→24、
# headline_medium→28，层级在视觉上反了）。现在每级直接对应字阶里的一个档：
#
#   H1  36  display_lg   700      整页只有一个
#   H2  28  display      700      分区
#   H3  24  headline_lg  600      小节
#   H4  20  headline     600      段落组
#   H5  16  title        600      卡片 / 弹窗标题
#   H6  14  body         600      与正文同号，只靠字重站住
#
# 行高与字距跟着字号走（见 ui.core.typography）：36px 的 1.222 与 14px 的 1.618
# 不是同一个数，写死一个必然有一头难看。
# ---------------------------------------------------------------------------
def _apply_heading(heading: ft.Text, level: int) -> None:
    """把某级的四件套（字号 / 字重 / 行高 / 字距）落到控件上。

    只补**没被调用方覆盖**的那几项：``Header_3(..., size=30)`` 仍然生效，行高与
    字距按 30px 重新算一遍（见 :func:`ui.core.typography.tracking` 的插值分支），
    不会出现"字号变了、行高还是 24px 那一档"的错位。
    """
    spec = typography.role(typography.HEADING[level])
    if heading.size is None:
        heading.size = spec.size
    if heading.weight is None:
        heading.weight = FONT_WEIGHT[typography.HEADING_WEIGHT[level]]
    if heading.style is None:
        heading.style = ft.TextStyle(
            height=typography.leading(heading.size),
            letter_spacing=(
                spec.tracking
                if heading.size == spec.size
                else typography.tracking(heading.size)
            ),
        )


@ft.control
class Header_1(ft.Text):
    """一级标题：36px / 700，整页只应出现一个。"""

    _LEVEL = 1

    def init(self):
        _apply_heading(self, self._LEVEL)


Title = Header_1
Header = Header_1


@ft.control
class Header_2(ft.Text):
    """二级标题：28px / 700，用于分区。"""

    _LEVEL = 2

    def init(self):
        _apply_heading(self, self._LEVEL)


SubTitle = Header_2
SubHeader = Header_2


@ft.control
class Header_3(ft.Text):
    """三级标题：24px / 600。"""

    _LEVEL = 3

    def init(self):
        _apply_heading(self, self._LEVEL)


@ft.control
class Header_4(ft.Text):
    """四级标题：20px / 600。"""

    _LEVEL = 4

    def init(self):
        _apply_heading(self, self._LEVEL)


@ft.control
class Header_5(ft.Text):
    """五级标题：16px / 600，卡片与弹窗的标题档。"""

    _LEVEL = 5

    def init(self):
        _apply_heading(self, self._LEVEL)


@ft.control
class Header_6(ft.Text):
    """六级标题：14px / 600 —— 与正文同号，靠字重区分层级。"""

    _LEVEL = 6

    def init(self):
        _apply_heading(self, self._LEVEL)


# ---------------------------------------------------------------------------
# 引用：左侧竖条 + 浅底 + 斜体正文，署名单独一行
# ---------------------------------------------------------------------------
@ft.control
class Quote(ft.Container):
    """引用块。

    Args:
        value: 引文正文，多行用 ``\\n`` 分隔。
        attribution: 出处 / 作者。留空则只有引文。
    """

    value: str = ""
    attribution: str = ""

    def init(self):
        # Container 的第一个位置参数是 content：``Quote("一句话")`` 会落进
        # content 而不是 value，这里接回来，老写法继续可用。
        text = self.value
        if isinstance(self.content, str):
            text = text or self.content
            self.content = None
        # 回写一份：init 若被再次调用（重建 / 重新挂载），内容不会丢
        self.value = text

        if self.bgcolor is None:
            # 5% 主色：比 surface 高一档，又不至于抢正文的注意力
            self.bgcolor = ft.Colors.with_opacity(0.05, ft.Colors.PRIMARY)
        if self.border_radius is None:
            self.border_radius = RADIUS["sm"]
        if self.padding is None:
            self.padding = ft.Padding.symmetric(
                horizontal=SPACE["4"], vertical=SPACE["3"]
            )

        # 引文的行高取"长文档"（1.75）而不是 UI 正文的 1.618：引用是要逐字读完的，
        # 比旁边的正文松半档，"这不是我的叙述"这件事连行距都在说。
        lines: list[ft.Control] = [
            ft.Text(
                text,
                style=typography.text_style(
                    "body",
                    color=ft.Colors.ON_SURFACE_VARIANT,
                    leading=typography.LEADING_PROSE,
                    italic=True,
                ),
            )
        ]
        if self.attribution:
            lines.append(
                ft.Text(
                    f"—— {self.attribution}",
                    style=typography.text_style(
                        "small", color=ft.Colors.ON_SURFACE_VARIANT
                    ),
                )
            )

        # 竖条用子控件而不是 border-left：Flutter 不允许「非均匀边框 + 圆角」，
        # 而引用块恰恰要圆角。竖条随 Row 的 STRETCH 自动占满块高。
        #
        # intrinsic_height 不能省：STRETCH 会给竖条一个「等于 Row 高度」的紧约束，
        # 而 Row 在 Column 里高度是无界的 —— Flutter 侧因 infinite height 断言失败，
        # 整棵渲染树退回错误态，页面上所有控件缩成 0 高、全叠在左上角（文档站的
        # Quote 页曾整页重叠）。这是 Descriptions / Steps 踩过的同一个坑，解法
        # 也只有这一个：先按内容量出固有高度，再把竖条拉满。
        self.content = ft.Row(
            spacing=SPACE["3"],
            intrinsic_height=True,
            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[
                ft.Container(
                    width=3,
                    border_radius=RADIUS["full"],
                    bgcolor=ft.Colors.PRIMARY,
                ),
                ft.Container(
                    expand=True,
                    content=ft.Column(
                        spacing=SPACE["1"],
                        tight=True,
                        controls=lines,
                    ),
                ),
            ],
        )


# ---------------------------------------------------------------------------
# 链接：主色 + 下划线，点击交给系统浏览器
# ---------------------------------------------------------------------------
def _link_style() -> ft.TextStyle:
    """默认样式：主色下划线。每次新建，避免多个 Link 共用同一个可变对象。"""
    return ft.TextStyle(
        decoration=ft.TextDecoration.UNDERLINE,
        decoration_color=ft.Colors.PRIMARY,
        decoration_thickness=1,
    )


@ft.control
class Link(ft.Text):
    """文字链。

    Args:
        value: 链接文字。
        link: 目标地址；留空则不可点。
    """

    color: ft.Colors = ft.Colors.PRIMARY
    style: ft.TextStyle = field(default_factory=_link_style)
    link: str | None = None

    def init(self):
        # on_tap 在 ft.Text 上是**字段**，子类同名方法会被 __init__ 赋的 None
        # 覆盖掉（写成方法等于永远不触发）。真正的处理函数换个名字再挂上去。
        if self.on_tap is None and self.link and not self.disabled:
            self.on_tap = self._open

        # 禁用态的视觉由组件自己负责：只靠 Flutter 的 disabled，
        # 文字仍然是主色蓝，看起来完全能点。
        if not self.disabled:
            return
        muted = disabled_layer()
        self.color = muted
        self.style = ft.TextStyle(
            decoration=ft.TextDecoration.UNDERLINE,
            decoration_color=muted,
            decoration_thickness=1,
        )

    def _open(self, e: ft.TapEvent):
        if self.disabled or not self.link:
            return
        webbrowser.open(self.link)


# ---------------------------------------------------------------------------
# 代码块：只读的 CodeEditor
# ---------------------------------------------------------------------------
@ft.control
class Code(fce.CodeEditor):
    """只读代码块。

    Args:
        value: 源码文本。
        language: 高亮语言，见 ``fce.CodeLanguage``。
    """

    language: fce.CodeLanguage = fce.CodeLanguage.PYTHON
    code_theme: fce.CodeTheme = fce.CodeTheme.ATOM_ONE_LIGHT
    read_only: bool = True

    def init(self):
        # 编辑器自身没有留白与字号，贴边时会和卡片描边粘在一起。
        if self.padding is None:
            self.padding = ft.Padding.all(SPACE["3"])
        if self.text_style is None:
            # 等宽字体**不加字距**：每个字宽度相同，tracking 会把代码栅格撕开。
            self.text_style = typography.text_style(
                "small", leading=typography.LEADING_CODE, tracking=0
            )
        # 空内容时 CodeEditor 会缩成一条线，示例舞台跟着塌掉。
        if self.min_height is None:
            self.min_height = 44


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------
@ft.control
class Markdown(ft.Markdown):
    """markdown 渲染器。

    Args:
        value: markdown 源文本。
        extension_set: 方言，默认 GitHub Web。
    """

    selectable: bool = True
    extension_set: ft.MarkdownExtensionSet = ft.MarkdownExtensionSet.GITHUB_WEB
    code_theme: ft.MarkdownCodeTheme = ft.MarkdownCodeTheme.MONOKAI
    # flet 默认 False：文档里的链接点了没反应，读者会以为组件坏了。
    auto_follow_links: bool = True


# ---------------------------------------------------------------------------
# JSON：固定语言、默认不显示行号
# ---------------------------------------------------------------------------
@ft.control
class Json(fce.CodeEditor):
    """JSON 查看器。

    Args:
        value: JSON 文本（字符串，不是 dict）。
    """

    language: fce.CodeLanguage = fce.CodeLanguage.JSON
    code_theme: fce.CodeTheme = fce.CodeTheme.ATOM_ONE_LIGHT
    read_only: bool = True
    # 行号由 gutter 控制：CodeEditor 没有 line_numbers 字段，写它不会生效。
    # 配置文件的行号没有意义，折叠柄才是读深层结构的手段，所以只关行号。
    gutter_style: fce.GutterStyle = field(
        default_factory=lambda: fce.GutterStyle(show_line_numbers=False)
    )

    def init(self):
        if self.padding is None:
            self.padding = ft.Padding.all(SPACE["3"])
        if self.text_style is None:
            self.text_style = typography.text_style(
                "small", leading=typography.LEADING_CODE, tracking=0
            )
        if self.min_height is None:
            self.min_height = 44


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
_LONG = (
    "这是一段用来测试截断的说明文字。它的长度明显超过一行，"
    "在窄容器里必须决定是折行、还是收成省略号。"
)


@ft.component
def _text_basic() -> ft.Control:
    """四档常用字号：正文 / 次要 / 标签 / 统计数字。

    文字色只有两档：``ON_SURFACE``（正文）与 ``ON_SURFACE_VARIANT``（一切次要
    文字）。**层次交给字号，不交给对比度** —— 曾经给「标签」用过 ``OUTLINE``，
    那是边框角色，浅色主题下对比度只有约 3.2:1，11px 的小字读不清。
    """
    return ft.Column(
        spacing=SPACE["3"],
        controls=[
            Text(
                "正文：14px，段落与表单值的默认档位（不写 size 时就是它）。",
                size=FONT_SIZE["body"],
            ),
            Text(
                "次要：12px，补充说明、时间戳、单位；换 ON_SURFACE_VARIANT。",
                size=FONT_SIZE["small"],
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
            Text(
                "标签：11px，跟在徽标或图表坐标轴旁边；色同次要，只降字号。",
                size=FONT_SIZE["caption"],
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
            Text(
                "1,286",
                size=FONT_SIZE["display"],
                weight=FONT_WEIGHT["bold"],
            ),
        ],
    )


@ft.component
def _text_truncate() -> ft.Control:
    """三种宽度策略：单行省略、两行省略、自由折行。"""
    return ft.Column(
        spacing=SPACE["3"],
        controls=[
            ft.Column(
                spacing=SPACE["1"],
                controls=[
                    ft.Text(
                        "单行：no_wrap + ELLIPSIS",
                        size=FONT_SIZE["caption"],
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                    ft.Container(
                        width=260,
                        content=Text(
                            _LONG,
                            no_wrap=True,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                    ),
                ],
            ),
            ft.Column(
                spacing=SPACE["1"],
                controls=[
                    ft.Text(
                        "两行：max_lines=2 + ELLIPSIS",
                        size=FONT_SIZE["caption"],
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                    ft.Container(
                        width=260,
                        content=Text(
                            _LONG,
                            max_lines=2,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                    ),
                ],
            ),
            ft.Container(
                width=520,
                content=Text(_LONG),
            ),
        ],
    )


@ft.component
def _text_roles() -> ft.Control:
    """颜色写成角色而不是色值：同一份代码在深浅主题里都对。"""
    rows = (
        ("ON_SURFACE", "正文", ft.Colors.ON_SURFACE),
        ("ON_SURFACE_VARIANT", "次要说明", ft.Colors.ON_SURFACE_VARIANT),
        ("PRIMARY", "强调 / 当前项", ft.Colors.PRIMARY),
        ("ERROR", "错误与删除", ft.Colors.ERROR),
    )
    return ft.Column(
        spacing=SPACE["2"],
        controls=[
            ft.Row(
                spacing=SPACE["4"],
                controls=[
                    ft.Container(
                        width=150,
                        content=ft.Text(
                            role,
                            size=FONT_SIZE["caption"],
                            color=ft.Colors.ON_SURFACE_VARIANT,
                            style=ft.TextStyle(letter_spacing=0.2),
                        ),
                    ),
                    Text(label, color=color),
                ],
            )
            for role, label, color in rows
        ],
    )


@ft.component
def _heading_scale() -> ft.Control:
    """六档并排：一眼看清字号与字重的落差。"""
    rows = (
        (Header_1, "显示级：页面主标题", "36"),
        (Header_2, "分区：一个模块的标题", "28"),
        (Header_3, "小节：模块里的第一层", "24"),
        (Header_4, "段落组：更贴近正文", "20"),
        (Header_5, "卡片标题 / 弹窗标题", "16"),
        (Header_6, "最小一级：与正文同号", "14"),
    )
    return ft.Column(
        spacing=SPACE["3"],
        controls=[
            ft.Row(
                spacing=SPACE["4"],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        width=34,
                        content=ft.Text(
                            f"H{index}",
                            size=FONT_SIZE["caption"],
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                    ),
                    ft.Container(
                        expand=True,
                        content=cls(label),
                    ),
                    ft.Text(
                        f"{size}px",
                        size=FONT_SIZE["caption"],
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                ],
            )
            for index, (cls, label, size) in enumerate(rows, start=1)
        ],
    )


@ft.component
def _heading_article() -> ft.Control:
    """放进文章里：标题与正文之间的留白靠外层 spacing，而不是给标题加 margin。"""
    return ft.Container(
        width=560,
        content=ft.Column(
            spacing=SPACE["2"],
            controls=[
                Header_2("变更日志"),
                Text(
                    "0.1.1 起，分页器的每页条数改为受控状态，切换条数会回到第 1 页。",
                    size=FONT_SIZE["body"],
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
                ft.Container(height=SPACE["3"]),
                Header_4("升级方式"),
                Text(
                    "把 Pagination 的 state 换成 PaginationState，回调不变。",
                    size=FONT_SIZE["body"],
                ),
                ft.Container(height=SPACE["3"]),
                Header_6("兼容性"),
                Text(
                    "旧的 data_per_page_nums 字段保留，语义不变。",
                    size=FONT_SIZE["body"],
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
            ],
        ),
    )


@ft.component
def _heading_override() -> ft.Control:
    """同一级标题也可以换颜色或字重，但字号不要动 —— 层级靠字阶传达。"""
    return ft.Column(
        spacing=SPACE["3"],
        controls=[
            Header_3("默认：28px / W_500"),
            Header_3("换颜色：用于强调当前分区", color=ft.Colors.PRIMARY),
            Header_3("换字重：只用于对比，不建议成组使用", weight=ft.FontWeight.W_400),
        ],
    )


@ft.component
def _quote_basic() -> ft.Control:
    return ft.Container(
        width=620,
        content=Quote("好的接口文档不是把实现讲一遍，而是让调用方不必读实现。"),
    )


@ft.component
def _quote_attribution() -> ft.Control:
    """多行引文 + 署名：署名永远单独一行，不混进引文里。"""
    return ft.Container(
        width=620,
        content=Quote(
            "分页器不负责取数据，只把「现在第几页、一共多少、每页几条」说清楚；\n"
            "用户改动其中任何一个，数据由调用方去取。",
            attribution="cs-ui · 组件设计说明",
        ),
    )


@ft.component
def _quote_in_article() -> ft.Control:
    """夹在正文之间：底色给出边界，读者可以整块跳过。"""
    return ft.Container(
        width=620,
        content=ft.Column(
            spacing=SPACE["3"],
            controls=[
                Text(
                    "评审意见里最常见的一条是「这里为什么不做校验」。",
                    size=FONT_SIZE["body"],
                ),
                Quote(
                    "输入框只做格式提醒，真正的约束放在提交接口上；"
                    "前端校验是体验，不是安全边界。",
                    attribution="架构评审 · 2026-03",
                ),
                Text(
                    "所以表单组件不拦截非法值，只把它标红并给出原因。",
                    size=FONT_SIZE["body"],
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
            ],
        ),
    )


_DOC_URL = "https://flet.dev/docs/controls/text"
_REPO_URL = "https://github.com/icstos/cs-ui"


@ft.component
def _link_basic() -> ft.Control:
    """点击后在系统默认浏览器里打开。"""
    return ft.Column(
        spacing=SPACE["2"],
        controls=[
            Link("Flet 文档：Text", link=_DOC_URL),
            Link("cs-ui 仓库", link=_REPO_URL),
        ],
    )


@ft.component
def _link_styles() -> ft.Control:
    """下划线是「可点」的信号；去掉它，链接就退化成普通说明文字。"""
    return ft.Column(
        spacing=SPACE["3"],
        controls=[
            Link("默认：主色 + 下划线", link=_DOC_URL),
            Link(
                "安静：次要色 + 无下划线",
                link=_DOC_URL,
                color=ft.Colors.ON_SURFACE_VARIANT,
                style=ft.TextStyle(decoration=ft.TextDecoration.NONE),
            ),
            ft.Row(
                spacing=SPACE["1"],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text("行内位置：见", size=FONT_SIZE["body"]),
                    Link("Flet 文档", link=_DOC_URL),
                    ft.Text("里的 Text 一节。", size=FONT_SIZE["body"]),
                ],
            ),
        ],
    )


@ft.component
def _link_disabled() -> ft.Control:
    """禁用与无目标都不响应点击；前者只是权限不够，后者本来就不该跳。"""
    return ft.Column(
        spacing=SPACE["2"],
        controls=[
            Link("禁用：当前账号没有文档权限", link=_DOC_URL, disabled=True),
            Link("没有 link：只是一段带下划线的文字"),
        ],
    )


_MARKDOWN_BASIC = """## 接口变更

`GET /users` 新增两个查询参数，**旧的调用方式仍然有效**。

- `page`：页码，从 1 开始
- `size`：每页条数，默认 20
- `total` 改为整数

> 0.1.1 起不再返回 `"total": "1286"` 这样的字符串。

| 参数 | 类型 | 默认 |
| --- | --- | --- |
| page | int | 1 |
| size | int | 20 |
"""

_MARKDOWN_FENCED = """### 取一页数据

```python
state = PaginationState(sum_data_nums=1_286)
Pagination(state)
```

命令行里验证：

```bash
curl "https://api.example.com/users?page=2&size=20"
```

- [x] 服务端分页
- [ ] 前端缓存
"""


@ft.component
def _markdown_basic() -> ft.Control:
    """标题、列表、引用、表格、行内代码一次到位。"""
    return ft.Container(width=640, content=Markdown(_MARKDOWN_BASIC))


@ft.component
def _markdown_code() -> ft.Control:
    """围栏代码块固定深色（MONOKAI），与正文形成「纸与墨」的对比。"""
    return ft.Container(width=640, content=Markdown(_MARKDOWN_FENCED))


_PYTHON_SNIPPET = """from dataclasses import dataclass


@dataclass
class Page:
    index: int = 1
    size: int = 20

    @property
    def offset(self) -> int:
        # 第 1 页从 0 开始
        return (self.index - 1) * self.size


page = Page(index=3)
print(page.offset)  # 40
"""

_BASH_SNIPPET = """#!/usr/bin/env bash
set -euo pipefail

for file in src/ui/**/*.py; do
    ruff check "$file"
done
"""

_JAVASCRIPT_SNIPPET = """const page = { index: 3, size: 20 };

export function offset({ index, size }) {
  return (index - 1) * size;
}

console.log(offset(page)); // 40
"""

_CODE_SNIPPETS: dict[str, tuple[str, fce.CodeLanguage]] = {
    "python": (_PYTHON_SNIPPET, fce.CodeLanguage.PYTHON),
    "bash": (_BASH_SNIPPET, fce.CodeLanguage.BASH),
    "js": (_JAVASCRIPT_SNIPPET, fce.CodeLanguage.JAVASCRIPT),
}


@ft.component
def _code_basic() -> ft.Control:
    return Code(value=_PYTHON_SNIPPET, height=210)


@ft.component
def _code_language() -> ft.Control:
    """换 language 只换高亮规则，代码本身不用动。"""
    current, set_current = ft.use_state("python")
    source, language = _CODE_SNIPPETS[current]

    def pick(event: ft.Event[ft.Container]):
        set_current(event.control.data)

    return ft.Column(
        spacing=SPACE["2"],
        controls=[
            ft.Row(
                spacing=SPACE["1"],
                controls=[
                    ft.Container(
                        padding=ft.Padding.symmetric(
                            horizontal=SPACE["2"], vertical=SPACE["1"]
                        ),
                        border_radius=RADIUS["sm"],
                        bgcolor=(
                            ft.Colors.PRIMARY
                            if key == current
                            else ft.Colors.SURFACE_CONTAINER
                        ),
                        data=key,
                        on_click=pick,
                        content=ft.Text(
                            label,
                            size=FONT_SIZE["small"],
                            color=(
                                ft.Colors.ON_PRIMARY
                                if key == current
                                else ft.Colors.ON_SURFACE_VARIANT
                            ),
                        ),
                    )
                    for key, label in (
                        ("python", "Python"),
                        ("bash", "Bash"),
                        ("js", "JavaScript"),
                    )
                ],
            ),
            Code(value=source, language=language, height=190),
        ],
    )


@ft.component
def _code_long_line() -> ft.Control:
    """长行不折行：编辑器横向滚动，行号留在左边。"""
    source = (
        "SELECT id, name, email, created_at, updated_at "
        "FROM users WHERE tenant_id = 'acme' AND deleted_at IS NULL "
        "ORDER BY created_at DESC LIMIT 20 OFFSET 40;"
    )
    return Code(value=source, language=fce.CodeLanguage.SQL, height=96)


_JSON_CONFIG = """{
  "name": "cs-ui",
  "version": "0.1.1",
  "components": {
    "display": ["text", "heading", "quote", "markdown"],
    "input": ["button", "chip"]
  },
  "theme": {
    "seed": "#1F6FEB",
    "mode": "system",
    "radius": { "sm": 4, "md": 6, "lg": 8 }
  },
  "debug": false
}"""

_JSON_COMPACT = (
    '{"id":1,"name":"cs-ui","tags":["ui","flet"],"active":true,'
    '"meta":{"stars":128,"license":"MIT"}}'
)


@ft.component
def _json_basic() -> ft.Control:
    """折叠柄在行号槽里：点箭头可收起一层，不需要滚动找结构。"""
    return Json(value=_JSON_CONFIG, height=230)


@ft.component
def _json_compact() -> ft.Control:
    """压缩成一行的响应体：横向滚动，不重排内容。"""
    return Json(value=_JSON_COMPACT, height=72)


@ft.component
def _json_numbers() -> ft.Control:
    """需要按行报错时，把行号打开。"""
    return Json(
        value=_JSON_CONFIG,
        height=230,
        gutter_style=fce.GutterStyle(show_line_numbers=True),
    )


# ---------------------------------------------------------------------------
# 示例源码（“查看代码”面板）
# ---------------------------------------------------------------------------
_TEXT_CODE = """Text("正文：默认 14px。")
Text("次要说明。", size=12, color=ft.Colors.ON_SURFACE_VARIANT)
Text("长文在窄容器里收成省略号。", max_lines=2, overflow=ft.TextOverflow.ELLIPSIS)"""

_HEADING_CODE = """Header_1("页面主标题")      # 36 / 700 / 行高 1.222
Header_2("分区标题")        # 28 / 700 / 行高 1.366
Header_3("小节标题")        # 24 / 600 / 行高 1.438
Header_4("段落组标题")      # 20 / 600 / 行高 1.510
Header_5("卡片标题")        # 16 / 600 / 行高 1.582
Header_6("最小一级")        # 14 / 600 / 行高 1.618

# 别名：Title / Header → Header_1，SubTitle / SubHeader → Header_2
SubTitle("仍然指向二级标题")"""

_QUOTE_CODE = """Quote("引文正文，可以多行。", attribution="出处 · 作者")

# 位置参数也照旧可用
Quote("一句话引用")"""

_LINK_CODE = """Link("Flet 文档", link="https://flet.dev/docs/controls/text")

# 去掉下划线就退化成普通说明文字
Link("安静链接", link=url, color=ft.Colors.ON_SURFACE_VARIANT,
     style=ft.TextStyle(decoration=ft.TextDecoration.NONE))

# 禁用：颜色与下划线一起降灰，点击不打开浏览器
Link("无权限", link=url, disabled=True)"""

_MARKDOWN_CODE = '''Markdown("""
## 接口变更

- `total` 改为整数
- 新增 `page` / `size`

> 旧字段保留一个版本。

| 参数 | 类型 |
| --- | --- |
| page | int |
""")'''

_CODE_CODE = """Code(value="print('hello')", height=120)
Code(value=sql, language=fce.CodeLanguage.SQL, height=96)

# 关掉行号（默认打开）
Code(value=src, gutter_style=fce.GutterStyle(show_line_numbers=False))"""

_JSON_CODE = """Json(value=json.dumps(payload, ensure_ascii=False, indent=2), height=230)

# 需要行号时再打开
Json(value=text, gutter_style=fce.GutterStyle(show_line_numbers=True))"""


# ---------------------------------------------------------------------------
# 组件说明
# ---------------------------------------------------------------------------
_TEXT_SPEC = Spec(
    name="Text",
    summary="正文与标签的默认载体：字号、颜色、截断都由属性决定，不额外包容器。",
    definition=(
        "Text 是所有界面文字的终点：标题之外的一切说明、数值、标签、提示都落在它"
        "身上。它直接是 flet.Text 的别名，不带自己的视觉，只在需要时由调用方指定 "
        "size / color / weight —— 这样同一段文字放进卡片、表格或对话框时，不会因为"
        "组件内置样式而显得格格不入。"
    ),
    anatomy=[
        (
            "内容",
            "value 是唯一必填项；多行字符串按 \\n 断行，不做 markdown 解析。",
        ),
        (
            "字号",
            "size 留空继承主题正文（14px）；层级取 FONT_SIZE 里的档位，不写裸数字。",
        ),
        (
            "颜色",
            "正文 ON_SURFACE、次要 ON_SURFACE_VARIANT、强调 PRIMARY —— 全是角色色。",
        ),
        (
            "截断",
            "max_lines + overflow=ELLIPSIS 做多行夹断；单行加 no_wrap=True。",
        ),
        (
            "选择",
            "selectable=True 允许选中复制；只有需要被摘走的说明才值得开。",
        ),
    ],
    when=[
        "段落、标签、数值、单位、辅助说明",
        "需要精确控制字号 / 颜色 / 截断的单行信息",
        "表格单元格、卡片内文这类已有布局的位置",
    ],
    avoid=[
        "标题层级：用 Header_1 … Header_6，字号与字重成套出现",
        "markdown 文档：用 Markdown，不要拿 spans 手拼",
        "可点击的跳转文字：用 Link，它带下划线与禁用态",
    ],
    examples=[
        Example(
            "基础排版",
            _text_basic,
            hint="正文 / 次要 / 标签 / 统计数字四档字号，全部取自令牌。",
            code=_TEXT_CODE,
        ),
        Example(
            "截断",
            _text_truncate,
            hint="260px 宽的容器里：单行省略、两行省略，以及不做限制的折行。",
        ),
        Example(
            "颜色角色",
            _text_roles,
            hint="同一份代码在深浅主题下都成立 —— 因为写的是角色，不是色值。",
        ),
    ],
    api=[
        Api("value", "str", "''", "文字内容；唯一必填项"),
        Api("size", "int | None", "None", "字号（px），留空继承主题正文"),
        Api("weight", "FontWeight | None", "None", "字重；正文一般不动它"),
        Api("color", "ColorValue | None", "None", "文字颜色，建议传角色色"),
        Api(
            "theme_style",
            "TextThemeStyle | None",
            "None",
            "整套排印档位；与 size 二选一",
        ),
        Api("text_align", "TextAlign", "TextAlign.START", "多行文字的水平对齐"),
        Api("max_lines", "int | None", "None", "最多显示几行；超出按 overflow 处理"),
        Api(
            "overflow",
            "TextOverflow",
            "TextOverflow.CLIP",
            "超出时的显示方式，截断用 ELLIPSIS",
        ),
        Api("no_wrap", "bool", "False", "禁止折行，单行信息配 ELLIPSIS"),
        Api("selectable", "bool | None", "None", "允许鼠标选中复制"),
    ],
    notes=[
        tip(
            "overflow 默认是 CLIP 而不是 ELLIPSIS：窄容器里不给 overflow，"
            "文字会被硬切掉半个字，用户看不出下面还有内容。"
        ),
        info(
            "Text 是 flet.Text 的别名而不是子类，isinstance(Text('x'), ft.Text) "
            "成立，所有 flet.Text 的参数原样可用。"
        ),
        warn(
            "同一条文字不要同时给 theme_style 与 size：Flutter 侧 theme_style "
            "会给出整套字号与行高，size 只覆盖字号，行高会与字号脱节。"
        ),
    ],
    tags=("文本", "正文", "文字", "text", "label", "paragraph"),
)

_HEADING_SPEC = Spec(
    name="Heading",
    summary="六档标题：字号与字重取自 M3 字阶，跨平台一致。",
    definition=(
        "标题不是「大一号的正文」。它同时承担层级（谁属于谁）与节奏（两段之间留"
        "多少空），所以字号、字重、行高、字距必须成套出现。这里把六级标题固定成"
        "六个类：字号取自字阶（36 / 28 / 24 / 20 / 16 / 14），字重前两级 700、"
        "其余 600，行高按各自字号现算（大字收紧、小字放宽，见 ui.core.typography）。"
        "调用方只选级别，不再逐处调 size —— 换字体或切换语言时，四件套仍然成组。"
    ),
    anatomy=[
        (
            "H1 · Header_1",
            "36px / 700 / 行高 1.222；整页只出现一个，用于页面主标题。",
        ),
        (
            "H2 · Header_2",
            "28px / 700 / 行高 1.366；分区标题，常见于标题下接一句副标题。",
        ),
        (
            "H3 / H4",
            "24px 与 20px，字重 600；小节与卡片组标题。",
        ),
        (
            "H5 / H6",
            "16px 与 14px，字重 600；最贴近正文的两档，H6 与正文同号只靠字重区分。",
        ),
        (
            "别名",
            "Title / Header 指向 H1，SubTitle / SubHeader 指向 H2；老代码不必改。",
        ),
    ],
    when=[
        "页面、分区、小节需要一眼可辨的三级结构",
        "同一套界面要在 Windows / macOS / Web 上字号一致",
        "需要给标题配副标题（H1/H2 后接一段正文）",
    ],
    avoid=[
        "只是想让字大一点：用 Text(size=...)，不要伪造层级",
        "跳级使用（H2 下直接 H5）：目录与屏幕阅读器都按层级读",
        "把整段话当标题：标题控制在两行以内，长文交给 Text",
    ],
    examples=[
        Example(
            "六档层级",
            _heading_scale,
            hint="从 36px 到 16px，字号与字重成对下降；右侧标出实际像素。",
            code=_HEADING_CODE,
        ),
        Example(
            "放进文章",
            _heading_article,
            hint="标题与正文的距离由外层 spacing 决定，标题自己不背 margin。",
        ),
        Example(
            "覆盖颜色与字重",
            _heading_override,
            hint="同一级标题可以换颜色强调，但不要改字号 —— 层级靠字阶传达。",
        ),
    ],
    api=[
        Api("Header_1", "type[ft.Text]", "", "H1：36px / 700 / 行高 1.222"),
        Api("Header_2", "type[ft.Text]", "", "H2：28px / 700 / 行高 1.366"),
        Api("Header_3", "type[ft.Text]", "", "H3：24px / 600 / 行高 1.438"),
        Api("Header_4", "type[ft.Text]", "", "H4：20px / 600 / 行高 1.510"),
        Api("Header_5", "type[ft.Text]", "", "H5：16px / 600 / 行高 1.582"),
        Api("Header_6", "type[ft.Text]", "", "H6：14px / 600 / 行高 1.618"),
        Api("value", "str", "''", "标题文字，与其他 ft.Text 一致"),
        Api("weight", "FontWeight", "", "覆盖字重；字号请保持本级默认"),
        Api(
            "color", "ColorValue | None", "None", "覆盖颜色，例如用 PRIMARY 标当前分区"
        ),
    ],
    notes=[
        info(
            "六档对到字阶的六个档位（36 / 28 / 24 / 20 / 16 / 14），行高与字距"
            "按各自字号现算。**不要再按 M3 的 theme_style 槽位来想**：那层映射一改，"
            "H2 就可能比 H3 还小（曾经 24 vs 28），层级在视觉上反了。"
        ),
        warn(
            "H6 与正文同为 14px，只靠 600 的字重区分。正文很长时它会被读成「加粗的"
            "一段」，需要明确层级就退回 H5。"
        ),
        tip(
            "别名是同一个类（Title is Header_1），改一处的默认字重，别名一起变 —— "
            "不要给别名再包一层子类。"
        ),
    ],
    tags=("标题", "heading", "h1", "h2", "title", "字阶"),
)

_QUOTE_SPEC = Spec(
    name="Quote",
    summary="引用块：主色竖条 + 浅底，装别人的话，也装需要被单独看见的一段。",
    definition=(
        "引用块的职责是「这段话不属于当前叙述」：它来自文档、用户、日志或另一位"
        "作者。左侧竖条与浅底给出边界，正文用斜体并把颜色降一档，读者可以整块跳过"
        "而不丢上下文；署名单独一行，避免把出处混进引文里。"
    ),
    anatomy=[
        (
            "左侧竖条",
            "3px 主色，随块高拉伸；它是引用与正文之间唯一的分界线。",
        ),
        (
            "引文",
            "斜体 + ON_SURFACE_VARIANT，行高 1.75（比正文松半档）；多行时整块一起缩进。",
        ),
        (
            "署名",
            "attribution 非空才出现，前缀破折号，字号小一档、颜色更浅。",
        ),
        (
            "底与圆角",
            "主色 5% 透明底 + 4px 圆角；不加边框，免得和卡片描边打架。",
        ),
    ],
    when=[
        "引用文档、规范、邮件或用户原话",
        "把一段需要单独阅读的说明从正文里拎出来",
        "需要标注出处（attribution）",
    ],
    avoid=[
        "强调自己的结论：那是提示条 / callout，不是引用",
        "大段可编辑内容：用 Markdown 的 > 引用，能跟着文档一起排版",
        "只是想要缩进：用 padding，别借引用的语义",
    ],
    examples=[
        Example(
            "基础用法",
            _quote_basic,
            hint="一句话引用：竖条 + 浅底划出边界，斜体提示这不是正文。",
            code=_QUOTE_CODE,
        ),
        Example(
            "多行与署名",
            _quote_attribution,
            hint="引文换行保留原样，署名单独一行、字号降一档。",
        ),
        Example(
            "夹在正文中",
            _quote_in_article,
            hint="上下各一段正文，引用块靠底色与竖条自然断开。",
        ),
    ],
    api=[
        Api("value", "str", "''", "引文正文；多行用 \\n 分隔"),
        Api("attribution", "str", "''", "出处 / 作者，留空则只显示引文"),
        Api("bgcolor", "ColorValue | None", "None", "默认主色 5% 透明底"),
        Api("padding", "PaddingValue | None", "None", "默认左右 16 / 上下 12"),
        Api("border_radius", "int | None", "None", "默认 4px"),
    ],
    notes=[
        tip(
            "竖向分割线用子控件画，而不是 border-left：Flutter 不允许「非均匀边框」"
            "配圆角，写了会在渲染期抛断言。竖条靠 Row 的 STRETCH 拉满，所以那个 "
            "Row 必须开 intrinsic_height —— 少了它，父级高度无界时会给竖条一个"
            "「无限高」的紧约束，整块连同整页一起塌成一行。"
        ),
        info(
            '位置参数仍然可用（Quote("一句话")）；但它已是容器，引文样式由组件'
            "统一，size / color 这类 Text 属性不再适用。"
        ),
        warn(
            "底色走 PRIMARY 角色而不是固定蓝：写死的蓝在深色主题下发灰，"
            "也跟不上主色换肤。"
        ),
    ],
    tags=("引用", "引文", "quote", "blockquote", "署名"),
)

_LINK_SPEC = Spec(
    name="Link",
    summary="文字链：下划线 + 主色，点击交给系统浏览器，禁用时整体降灰。",
    definition=(
        "链接与普通文字的区别不在颜色，而在「可点」这件事必须被看出来。这里固定"
        "主色下划线，把目标地址放在 link 里，点击时交给系统默认浏览器 —— 组件不"
        "接管路由：页面内跳转该由 Router 负责，混在一起会让「后退」变得不可预期。"
    ),
    anatomy=[
        ("文字", "value 即链接文字，随容器宽度折行。"),
        ("下划线", "1px 主色，与文字同色；去掉它就从链接退化成强调文字。"),
        ("目标", "link 为空时只是带下划线的文字，不响应点击。"),
        (
            "禁用态",
            "disabled=True 时颜色与下划线一起降到 38% 灰，也不再挂点击处理。",
        ),
    ],
    when=[
        "跳到外部文档、仓库、帮助页",
        "正文里需要一处「更多」入口",
        "需要在表格或说明里放一个轻量跳转，而不想用按钮",
    ],
    avoid=[
        "页面内路由跳转：用 Router / 导航组件，不要开新浏览器窗口",
        "一屏十几个链接：改用按钮或列表，链接串会淹没正文",
        "有明确动作（提交、删除、重试）：用 Button，链接不承担操作语义",
    ],
    examples=[
        Example(
            "基础用法",
            _link_basic,
            hint="点击在系统默认浏览器里打开，当前窗口不跳走。",
            code=_LINK_CODE,
        ),
        Example(
            "几种样式",
            _link_styles,
            hint="默认主色下划线、安静的无下划线、以及跟在文字后面的行内位置。",
        ),
        Example(
            "禁用与空目标",
            _link_disabled,
            hint="两种都点不动：前者是权限不够，后者本来就不该跳。",
        ),
    ],
    api=[
        Api("value", "str", "''", "链接文字"),
        Api("link", "str | None", "None", "目标地址；留空则不可点"),
        Api("color", "ColorValue", "ft.Colors.PRIMARY", "文字颜色"),
        Api("style", "TextStyle", "", "默认主色下划线；传新样式可去掉下划线"),
        Api("disabled", "bool", "False", "禁用：降灰且不打开浏览器"),
        Api(
            "on_tap",
            "Callable[[TapEvent], None] | None",
            "None",
            "点击处理；不传时自动挂载打开 link 的函数",
        ),
    ],
    notes=[
        warn(
            "link 走 webbrowser.open，桌面端可用；Web 端应由页面自己接管"
            "（action / page.launch_url）。组件不猜运行环境，也不替你决定新窗口。"
        ),
        info(
            "禁用态的灰是 ON_SURFACE 38%，与分页器禁用箭头同一档 —— 全框架的"
            "「不可用」是同一个灰度，用户不用重新学。"
        ),
    ],
    tags=("链接", "文字链", "link", "anchor", "url"),
)

_MARKDOWN_SPEC = Spec(
    name="Markdown",
    summary="把一段 markdown 文本渲染成排版：标题、列表、表格、代码块与链接。",
    definition=(
        "Markdown 用于「内容来自别处」的场景：README、接口说明、后端下发的富文本。"
        "组件不解析业务语义，只按 GITHUB_WEB 扩展集把标记转成控件。选 GitHub 方言"
        "是因为表格、任务列表、删除线在技术文档里出现频率最高，纯 CommonMark 会把"
        "这些当普通段落。"
    ),
    anatomy=[
        (
            "块级排版",
            "标题、段落、引用、分隔线按语法分段；段间距由主题的 markdown 样式控制。",
        ),
        (
            "列表与表格",
            "GITHUB_WEB 扩展支持有序 / 无序 / 任务列表与管道表格。",
        ),
        (
            "代码",
            "行内 code 与围栏代码块都走 code_theme（默认 MONOKAI），与正文拉开层次。",
        ),
        (
            "链接",
            "auto_follow_links=True 时点击直接在系统浏览器打开。",
        ),
        (
            "选择",
            "selectable=True，长文可整段复制；默认就开着。",
        ),
    ],
    when=[
        "渲染 README、变更日志、接口文档",
        "内容由用户或后端提供，格式已经写在文本里",
        "需要表格、任务列表这类 GitHub 方言",
    ],
    avoid=[
        "只需要一段粗体 / 斜体：用 Text + spans，省一层解析",
        "需要精确控制每个元素的间距与颜色：用 Row / Column 手写",
        "几 MB 的大文档：先分页或截断，整篇渲染会拖慢首帧",
    ],
    examples=[
        Example(
            "基础排版",
            _markdown_basic,
            hint="标题、列表、引用、表格与行内代码；表格来自 GITHUB_WEB 扩展。",
            code=_MARKDOWN_CODE,
        ),
        Example(
            "代码块",
            _markdown_code,
            hint="两种语言的围栏代码块 + 任务列表，代码块是固定深色。",
        ),
    ],
    api=[
        Api("value", "str", "''", "markdown 源文本"),
        Api("selectable", "bool", "True", "允许选中复制"),
        Api(
            "extension_set",
            "MarkdownExtensionSet",
            "GITHUB_WEB",
            "方言；换 NONE 会丢表格",
        ),
        Api("code_theme", "MarkdownCodeTheme", "MONOKAI", "代码块配色，不随明暗主题变"),
        Api("auto_follow_links", "bool", "True", "点击链接是否直接打开"),
        Api(
            "md_style_sheet",
            "MarkdownStyleSheet | None",
            "None",
            "覆盖标题 / 段落的排版",
        ),
        Api("shrink_wrap", "bool", "True", "宽度贴合内容，而不是撑满父容器"),
        Api(
            "on_tap_link",
            "Callable[[Event], None] | None",
            "None",
            "自定义链接点击，可接管跳转",
        ),
    ],
    notes=[
        tip(
            "auto_follow_links 在 flet 里默认是 False：文档里的链接点不动，读者会"
            "以为组件坏了；这里默认打开。"
        ),
        warn(
            "code_theme 不跟随明暗主题：MONOKAI 在浅色页面上是一块深色面板，这是"
            "刻意的「纸与墨」对比。要完全贴合主题就自己传 code_theme。"
        ),
        info(
            "extension_set 换成 NONE 会退回纯 CommonMark：表格变成一行竖线文本，"
            "任务列表也不再是复选框。"
        ),
    ],
    tags=("markdown", "文档", "富文本", "readme", "表格"),
)

_CODE_SPEC = Spec(
    name="Code",
    summary="只读代码块：语法高亮、行号、横向滚动，按语言着色。",
    definition=(
        "代码要「像代码」才读得下去：等宽字体、行号、语法高亮三者缺一不可。Code "
        "复用 flet_code_editor 的编辑器内核并锁成只读 —— 滚动、选中复制、折叠的"
        "行为与真正的编辑器一致，而不是用 Text 拼一个看起来像代码的色块。"
    ),
    anatomy=[
        (
            "语言",
            "language 决定高亮规则（PYTHON / SQL / BASH …）；选错只是不着色，不报错。",
        ),
        (
            "行号槽",
            "gutter_style 控制行号、折叠柄与错误标记，默认三者全开。",
        ),
        (
            "主题",
            "code_theme 默认 ATOM_ONE_LIGHT；这是编辑器配色，不随页面明暗主题变。",
        ),
        (
            "只读",
            "read_only=True：可选中复制、不可编辑；要编辑请直接用 fce.CodeEditor。",
        ),
        (
            "尺寸",
            "height 决定可视高度，超出纵向滚动；长行不折行，横向滚动。",
        ),
    ],
    when=[
        "展示示例代码、配置片段、命令行",
        "需要行号对照报错（第 12 行）",
        "内容较长，需要滚动与选中复制",
    ],
    avoid=[
        "一行命令或一个字段名：行内 code 用 Text 或 Markdown",
        "需要编辑：用 fce.CodeEditor，read_only 关掉",
        "大段运行日志：用 LogContainer，代码高亮对日志没有增益",
    ],
    examples=[
        Example(
            "Python",
            _code_basic,
            hint="装饰器、注释、字符串各一色；高度固定，超出部分纵向滚动。",
            code=_CODE_CODE,
        ),
        Example(
            "切换语言",
            _code_language,
            hint="同一段内容换个 language 就换一套高亮规则，点击上方标签切换。",
        ),
        Example(
            "长行",
            _code_long_line,
            hint="SQL 写成一行时不折行，编辑器横向滚动，行号固定留在左侧。",
        ),
    ],
    api=[
        Api("value", "str | None", "None", "源码文本"),
        Api("language", "CodeLanguage", "PYTHON", "高亮语言，见 fce.CodeLanguage"),
        Api("code_theme", "CodeTheme", "ATOM_ONE_LIGHT", "编辑器配色，不随页面主题"),
        Api("read_only", "bool", "True", "只读；可选中复制"),
        Api("gutter_style", "GutterStyle | None", "None", "行号 / 折叠柄 / 错误标记"),
        Api("text_style", "TextStyle | None", "None", "默认 12.5px / 行高 1.55"),
        Api("padding", "PaddingValue | None", "None", "默认 12px 内边距"),
        Api("height", "int | None", "None", "可视高度；超出纵向滚动"),
        Api("issues", "list[Issue]", "[]", "行内错误标记，配合行号使用"),
    ],
    notes=[
        warn(
            "长行不会自动折行，只横向滚动；放进窄容器时务必给 height，"
            "否则编辑器会和父容器抢高度，看起来像「没渲染出来」。"
        ),
        info(
            "空 value 保留 44px 最小高度（init 里设 min_height），避免示例舞台"
            "缩成一条线；正常内容不受影响。"
        ),
        tip(
            "隐藏行号传 gutter_style=fce.GutterStyle(show_line_numbers=False)；"
            "CodeEditor 没有 line_numbers 字段，直接写会被静默忽略。"
        ),
    ],
    tags=("代码", "代码块", "code", "highlight", "语法高亮"),
)

_JSON_SPEC = Spec(
    name="Json",
    summary="JSON 查看器：按 JSON 语法高亮，带折叠柄，默认不显示行号。",
    definition=(
        "JSON 的结构靠缩进表达，所以查看器最重要的不是颜色，而是折叠：一个两百行的"
        "响应体，用户往往只想看第一层键。Json 复用代码编辑器内核，固定 JSON 语言、"
        "默认关掉行号（配置文件的行号没有意义），把行号槽留给折叠柄。"
    ),
    anatomy=[
        (
            "语言",
            "固定 JSON，不接受切换；键、字符串、数字、布尔各一色。",
        ),
        (
            "折叠柄",
            "行号槽里的箭头，按对象 / 数组层级收起；读深层结构主要靠它。",
        ),
        (
            "行号",
            "默认关闭（GutterStyle(show_line_numbers=False)），需要按行报错时再开。",
        ),
        (
            "只读",
            "read_only=True：能选中复制，不能改坏原文。",
        ),
    ],
    when=[
        "展示接口响应、配置、事件负载",
        "层级深、需要逐层展开查看",
        "需要复制其中一段原文给同事",
    ],
    avoid=[
        "需要校验或编辑 JSON：用可编辑的 fce.CodeEditor",
        "只有几个键值对：用 Descriptions 或 Text，JSON 语法反而啰嗦",
        "超长数组：先截断，高亮不会让五千行变得可读",
    ],
    examples=[
        Example(
            "嵌套结构",
            _json_basic,
            hint="三层对象 + 数组：点行号槽里的箭头可以逐层收起。",
            code=_JSON_CODE,
        ),
        Example(
            "压缩成一行",
            _json_compact,
            hint="接口返回的原始响应体：不重排、不折行，横向滚动。",
        ),
        Example(
            "打开行号",
            _json_numbers,
            hint="需要按行报错时传 GutterStyle(show_line_numbers=True)。",
        ),
    ],
    api=[
        Api("value", "str | None", "None", "JSON 文本；必须是字符串"),
        Api("code_theme", "CodeTheme", "ATOM_ONE_LIGHT", "编辑器配色"),
        Api(
            "gutter_style",
            "GutterStyle",
            "",
            "默认 GutterStyle(show_line_numbers=False)",
        ),
        Api("read_only", "bool", "True", "只读；可选中复制"),
        Api("text_style", "TextStyle | None", "None", "默认 12.5px / 行高 1.55"),
        Api("padding", "PaddingValue | None", "None", "默认 12px 内边距"),
        Api("height", "int | None", "None", "可视高度；超出纵向滚动"),
    ],
    notes=[
        warn(
            "value 必须是合法 JSON 文本：传 dict 不会自动序列化，先 "
            "json.dumps(data, ensure_ascii=False, indent=2)。"
        ),
        info(
            "行号由 gutter_style.show_line_numbers 控制。CodeEditor 本身没有 "
            "line_numbers 字段，写 line_numbers=False 会被静默忽略。"
        ),
        tip(
            "折叠柄只在有嵌套时出现；单层对象看起来就是一段高亮文本，"
            "别误以为折叠功能没生效。"
        ),
    ],
    tags=("json", "数据", "查看器", "折叠", "配置"),
)


SPECS: dict[str, Spec] = {
    "text": _TEXT_SPEC,
    "heading": _HEADING_SPEC,
    "quote": _QUOTE_SPEC,
    "link": _LINK_SPEC,
    "markdown": _MARKDOWN_SPEC,
    "code": _CODE_SPEC,
    "json": _JSON_SPEC,
}


if __name__ == "__main__":
    run(*SPECS.values())
