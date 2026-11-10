"""文档内容 DSL —— 页面是**数据**，不是控件树。

好处有三个：正文与排版解耦（换皮不用改内容）、右侧目录能从标题自动生成、
三份语言包只需要按 key 对齐。渲染见 :mod:`docs.render`。
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Literal

import flet as ft

#: 组件的「工厂」：真正的 ``@ft.component`` 函数或返回控件的普通函数。
type Factory = Callable[[], ft.Control]

type Tone = Literal["primary", "success", "warning", "danger", "info", "neutral"]
type CalloutKind = Literal["info", "success", "warning", "danger", "tip"]


@dataclass(frozen=True, slots=True)
class Heading:
    """章节标题。``level=2`` 进右侧目录，``level=3`` 只在大纲里缩进。"""

    key: str
    level: Literal[2, 3] = 2

    @property
    def anchor(self) -> str:
        """锚点：取 key 最后一段，点号换连字符（``arch.routing`` → ``routing``）。"""
        return self.key.rsplit(".", 1)[-1].replace("_", "-")


@dataclass(frozen=True, slots=True)
class Prose:
    """一段正文。"""

    key: str


@dataclass(frozen=True, slots=True)
class Bullets:
    """要点列表。"""

    keys: tuple[str, ...]
    tone: Tone = "primary"


@dataclass(frozen=True, slots=True)
class Code:
    """代码块。``filename`` 同时是代码标签页的名字。"""

    source: str
    filename: str | None = None
    language: str = "python"


@dataclass(frozen=True, slots=True)
class CodeTabs:
    """多文件 / 多方案的标签页代码块。"""

    items: tuple[Code, ...]


@dataclass(frozen=True, slots=True)
class Callout:
    """提示框。``tip`` 用主色，``danger`` 用错误色。

    ``params`` 是文案里的占位符实参（如 ``{"flet": FLET_VERSION}``）。版本号这类
    会随依赖升级而变的值必须走占位符 —— 直接写进语言包，升级时就得记得回来改
    三份翻译，漏一次站点上就是旧话术。
    """

    kind: CalloutKind
    body_key: str
    title_key: str | None = None
    params: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Demo:
    """实时演示：控件本身是真的，``code`` 给"查看代码"用。"""

    factory: Factory
    title_key: str | None = None
    hint_key: str | None = None
    code: str | None = None
    padded: bool = True
    stretch: bool = True
    tall: bool = False


@dataclass(frozen=True, slots=True)
class Split:
    """左说明、右演示的两栏区块（说明部分仍是 blocks）。

    ``ratio`` 默认取三分法则 1:2（说明占三分之一、演示占三分之二）：读者一眼
    先扫到左侧的"这是什么"，视线再往右落到能动手的演示上。两栏等宽会让两边
    都不够用 —— 说明被拉成一整行、演示里的表单挤成两行。
    """

    left: tuple[Block, ...]
    right: Factory
    ratio: tuple[int, int] = (1, 2)


@dataclass(frozen=True, slots=True)
class Custom:
    """逃生口：完全自定义的区块。"""

    factory: Factory


type Block = (
    Heading | Prose | Bullets | Code | CodeTabs | Callout | Demo | Split | Custom
)

#: 一篇文档。
type Doc = tuple[Block, ...]


# ---------------------------------------------------------------------------
# 书写糖：让内容文件读起来像文档，而不是像构造函数调用
# ---------------------------------------------------------------------------


def h2(key: str) -> Heading:
    return Heading(key, 2)


def h3(key: str) -> Heading:
    return Heading(key, 3)


def p(key: str) -> Prose:
    return Prose(key)


def ul(*keys: str, tone: Tone = "primary") -> Bullets:
    return Bullets(keys, tone)


def code(source: str, filename: str | None = None, language: str = "python") -> Code:
    return Code(source.strip("\n"), filename, language)


def tabs(*items: Code) -> CodeTabs:
    return CodeTabs(items)


def tip(body_key: str, title_key: str | None = None) -> Callout:
    return Callout("tip", body_key, title_key)


def note(
    body_key: str,
    title_key: str | None = None,
    /,
    **params: str,
) -> Callout:
    return Callout("info", body_key, title_key, params)


def warn(body_key: str, title_key: str | None = None) -> Callout:
    return Callout("warning", body_key, title_key)


def danger(body_key: str, title_key: str | None = None) -> Callout:
    return Callout("danger", body_key, title_key)


def demo(
    factory: Factory,
    *,
    title_key: str | None = None,
    hint_key: str | None = None,
    code: str | None = None,
    padded: bool = True,
    stretch: bool = True,
    tall: bool = False,
) -> Demo:
    return Demo(factory, title_key, hint_key, code, padded, stretch, tall)


def split(
    left: tuple[Block, ...], right: Factory, *, ratio: tuple[int, int] = (1, 2)
) -> Split:
    return Split(left, right, ratio)


def custom(factory: Factory) -> Custom:
    return Custom(factory)


__all__ = [
    "Block",
    "Bullets",
    "Callout",
    "CalloutKind",
    "Code",
    "CodeTabs",
    "Custom",
    "Demo",
    "Doc",
    "Factory",
    "Heading",
    "Prose",
    "Split",
    "Tone",
    "code",
    "custom",
    "danger",
    "demo",
    "h2",
    "h3",
    "note",
    "p",
    "split",
    "tabs",
    "tip",
    "ul",
    "warn",
]
