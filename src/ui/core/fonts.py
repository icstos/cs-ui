"""字体：cs-ui 自带的那一款（阿里巴巴普惠体 3.55）的**唯一出处**。

为什么字体要收进框架
--------------------

在 flet 里让自定义字体生效，必须同时做对两件事：

1. 把字体注册到 ``page.fonts``（族名 → 字体来源）；
2. 让主题 / 文本样式**指名**这个族名。

少做第一步 → 字体文件根本没加载；少做第二步 → 拿不到族名，静默退回系统字体。
两个"静默"叠在一起，就是"代码看着都对，界面上却是微软雅黑"。每个应用各写一遍
这两行，必然有一天某个应用漏掉其中一行，而且没有任何报错。

所以字体和主题一样，只有框架一个事实源：本模块管字体文件与注册，:func:`apply_fonts`
把两个动作收成一次调用，:func:`ui.core.typography.text_style` 再保证**每一处**由
框架排版的文字都带上族名（原因见下）。

为什么路径是绝对的
------------------

``page.fonts`` 的值可以是"相对 assets 目录的路径"，也可以是绝对路径。相对路径
要求字体落在**应用自己的** assets 目录里；框架自带的字体在 site-packages 下，
拷贝一份到每个应用的 assets 里既浪费也早晚不同步。绝对路径能以零拷贝的方式
直指包内文件（flet 1.1.2 桌面端两种形式实测都生效）。

代价只有一个：Web 视图没有与之对应的 URL。Web 应用请把字体放进自己的 assets，
再用 ``page.fonts = {"AlibabaPuHuiTi": "fonts/AlibabaPuHuiTi-3-55-Regular.otf"}``
覆盖 —— :func:`apply_fonts` 看到同族名已声明就直接尊重，不会覆盖你的设置。

为什么样式里必须显式写族名
--------------------------

flet 把 ``TextStyle`` 下发给 Flutter 时是**整体替换**而不是合并：一个只写了字号和
颜色的 ``TextStyle`` 会把主题里的 ``fontFamily`` 一并清掉（同一个坑还会清掉
``color``，见 :func:`ui.core.theme.text_theme` 的说明）。所以"主题里设了
``font_family``"并不够 —— 凡是用 ``text_style()`` 排的字，都必须自己带上族名。
这条实测结论对应 :func:`ui.core.typography.text_style` 里的 ``family`` 参数。
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ui.core.config import logger

if TYPE_CHECKING:  # pragma: no cover - 只为类型标注，运行期不需要 flet
    import flet as ft

__all__ = [
    "FONT_DIR",
    "FONT_FAMILY",
    "FONT_FILE_NAME",
    "active_family",
    "apply_fonts",
    "font_file",
    "font_map",
    "font_source",
]

#: 字体族名。与 :func:`ui.core.theme.build_theme` 下发的 ``font_family`` 必须一致 ——
#: 客户端认的是这个名字，和字体文件内部的 family name 无关。
FONT_FAMILY: str = "AlibabaPuHuiTi"

#: 随包分发的字体文件。
FONT_FILE_NAME: str = "AlibabaPuHuiTi-3-55-Regular.otf"

#: 字体目录：``ui/data/fonts``（本模块在 ``ui/core`` 下，往上一级就是包根）。
FONT_DIR: Path = Path(__file__).resolve().parents[1] / "data" / "fonts"


def font_file() -> Path:
    """内置字体文件的绝对路径。**不做存在性判断**，由调用方决定缺失时怎么办。"""
    return FONT_DIR / FONT_FILE_NAME


def font_source() -> str | None:
    """``page.fonts`` 里该写什么（绝对路径）；字体缺失时返回 ``None``。"""
    path = font_file()
    return str(path) if path.exists() else None


def font_map() -> dict[str, str]:
    """``{族名: 来源}`` —— 需要自己拼 ``page.fonts`` 时的便捷形式，缺失则为空表。"""
    source = font_source()
    return {FONT_FAMILY: source} if source is not None else {}


def active_family() -> str | None:
    """当前该用的字体族名。

    优先用主题状态里显式设过的族名（应用可以换成别的字体），否则用内置的这一款；
    内置字体不存在时返回 ``None``，让样式保持"不指定族名"——由系统兜底，
    而不是指向一个永远加载不到的族名。
    """
    from ui.core.theme import theme_state

    return theme_state().font_family or (FONT_FAMILY if font_file().exists() else None)


def apply_fonts(page: ft.Page, family: str | None = None) -> str | None:
    """把字体注册到页面，并把族名写回主题状态。

    幂等：重复调用（例如每次 ``apply_theme``）都不会重复写 ``page.fonts``。

    Args:
        page: 目标页面。
        family: 指定族名。留空时沿用主题状态里已有的族名，再退到内置字体。

    Returns:
        实际生效的族名；字体缺失且未自带字体时返回 ``None``。
    """
    from ui.core.theme import theme_state

    state = theme_state()
    declared = dict(page.fonts or {})
    wanted = family or state.font_family or FONT_FAMILY

    if wanted in declared:
        # 应用自己声明过这一族（可能指向它自己的字体文件或 Web 用的相对路径）：
        # 尊重既有设置，不拿内置的绝对路径去覆盖它。
        state.font_family = wanted
        return wanted

    source = font_source()
    if source is None:
        logger.warning("cs-ui 内置字体缺失，界面回退系统字体：%s", font_file())
        return None

    declared[wanted] = source
    page.fonts = declared
    state.font_family = wanted
    return wanted
