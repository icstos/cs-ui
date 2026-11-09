"""框架底座：设计令牌、主题、多语言、格式化、日志、文档套件。

**这个包的门面是惰性的**（PEP 562），理由和 :mod:`ui` 顶层一样，但代价更隐蔽：

``ui.core`` 是每个组件模块的父包 —— ``from ui.core.doc import Spec`` 这行看起来
只想要一个文档数据类，实际会先执行本文件的 ``__init__``。历史上这里写着十几组
star-import，于是**只要 import 任何一个组件**，就要连带加载 i18n（651 键 × 3 语的
文案表）、theme、config、logger（拖进 ``logging.handlers`` + ``pickle``）、format……
实测单项组件导入因此多付约 90~170ms，其中通常八成是当次根本用不到的。

现在改成 ``_ORIGIN`` 名字表 + 模块级 ``__getattr__``：

* ``from ui.core import t`` → 首次访问才导入 ``ui.core.i18n``，之后是普通属性；
* ``from ui.core.tokens import SPACE``（框架内部的常规写法）→ 只导入 tokens，
  不再因为父包 ``__init__`` 把整套底座拖进来；
* ``dir(ui.core)`` 仍返回完整名字表，IDE 补全与 ``from ui.core import *`` 不变。

新增导出时必须同时登记到 ``_ORIGIN``，否则 ``from ui.core import x`` 会报
``AttributeError``。
"""

from __future__ import annotations

import importlib
from typing import Any

# ---------------------------------------------------------------------------
# 名字 → 所属子模块。一张表就是全部事实：既驱动 __getattr__，也生成 __all__。
# 键按子模块聚类，顺序与原先的 import 分组一致。
# ---------------------------------------------------------------------------
_ORIGIN: dict[str, str] = {
    # config —— 全局配置对象与 logger 实例
    "config": ".config",
    "logger": ".config",
    # constants —— 枚举与轻量标记类型
    "RUN_MODE": ".constants",
    "ButtonShape": ".constants",
    "FeedbackStyle": ".constants",
    "FormValueType": ".constants",
    "LayoutType": ".constants",
    "SizeType": ".constants",
    "StyleType": ".constants",
    # float_layer —— 浮层可用性探测与 hook
    "overlay_usable": ".float_layer",
    "use_float_layer": ".float_layer",
    # format —— 日期 / 数字 / 列表的本地化格式化
    "calendar_title": ".format",
    "first_weekday": ".format",
    "format_date": ".format",
    "format_datetime": ".format",
    "format_list": ".format",
    "format_number": ".format",
    "format_time": ".format",
    "month_cell": ".format",
    "month_name": ".format",
    "weekday_names": ".format",
    # i18n —— 语言注册、翻译查表、声明式切换
    "FileStore": ".i18n",
    "I18nProvider": ".i18n",
    "I18nState": ".i18n",
    "Language": ".i18n",
    "LanguageRegistry": ".i18n",
    "LanguageSwitcher": ".i18n",
    "LocaleStore": ".i18n",
    "MemoryStore": ".i18n",
    "Translator": ".i18n",
    "available_languages": ".i18n",
    "canonical": ".i18n",
    "configure": ".i18n",
    "current_language": ".i18n",
    "current_locale": ".i18n",
    "i18n_context": ".i18n",
    "i18n_registry": ".i18n",
    "i18n_state": ".i18n",
    "load_catalogs": ".i18n",
    "missing_keys": ".i18n",
    "plural_category": ".i18n",
    "register_language": ".i18n",
    "register_messages": ".i18n",
    "register_plural_rule": ".i18n",
    "reset_registry": ".i18n",
    "set_locale": ".i18n",
    "system_locale": ".i18n",
    "t": ".i18n",
    "tl": ".i18n",
    "tn": ".i18n",
    "use_i18n": ".i18n",
    "use_t": ".i18n",
    "validate": ".i18n",
    # icons —— 语义图标（一个动作一个图标，见 ui.core.icons）
    # 只导出"表达约定"的那几个；CLOSE / SEARCH 这类通用名留在 ui.core.icons 里，
    # 免得 ui.core 顶层出现一堆看不出用途的单词。
    "DISCLOSURE": ".icons",
    "PANEL_CLOSE": ".icons",
    "PANEL_OPEN": ".icons",
    "STEP_DOWN": ".icons",
    "STEP_UP": ".icons",
    # styles —— 输入类控件的统一外观
    "INPUT_HEIGHT": ".styles",
    "INPUT_RADIUS": ".styles",
    "outline_input": ".styles",
    "underline_input": ".styles",
    # theme —— 明暗模式、表面策略、主色种子
    "MODES": ".theme",
    "ThemeProvider": ".theme",
    "ThemeState": ".theme",
    "ThemeSwitcher": ".theme",
    "apply_theme": ".theme",
    "build_theme": ".theme",
    "current_mode": ".theme",
    "theme_context": ".theme",
    "theme_state": ".theme",
    "use_theme": ".theme",
    # tokens —— 设计令牌（间距 / 圆角 / 字号 / 图标 / 控件高 / 状态层 / 语义色）
    "CONTROL_HEIGHT": ".tokens",
    "DISABLED_OPACITY": ".tokens",
    "DURATION": ".tokens",
    "ELEVATION": ".tokens",
    "FONT_SIZE": ".tokens",
    "FONT_WEIGHT": ".tokens",
    "GAP": ".tokens",
    "GAP_LOOSE": ".tokens",
    "GAP_TIGHT": ".tokens",
    "ICON_SIZE": ".tokens",
    "PAD": ".tokens",
    "PAD_LOOSE": ".tokens",
    "PRIMARY_SEEDS": ".tokens",
    "RADIUS": ".tokens",
    "SELECTED_OPACITY": ".tokens",
    "SEMANTIC": ".tokens",
    "SEMANTIC_ON": ".tokens",
    "SEMANTIC_ROLES": ".tokens",
    "SEMANTIC_TEXT": ".tokens",
    "SEMANTIC_TINT": ".tokens",
    "SEMANTIC_WASH": ".tokens",
    "SPACE": ".tokens",
    "SPACE_STEPS": ".tokens",
    "STATE": ".tokens",
    "ACCENT_ROLES": ".tokens",
    "M3_ACCENT": ".tokens",
    "accent_fill": ".tokens",
    "accent_on": ".tokens",
    "accent_soft": ".tokens",
    "accent_text": ".tokens",
    "accent_wash": ".tokens",
    "disabled_layer": ".tokens",
    "elevation": ".tokens",
    "focus_border": ".tokens",
    "hairline": ".tokens",
    "on_semantic": ".tokens",
    "overlay": ".tokens",
    "scrim": ".tokens",
    "selected_layer": ".tokens",
    "semantic": ".tokens",
    "semantic_text": ".tokens",
    "state_layer": ".tokens",
}

# __all__ 由 _ORIGIN 表推导（数量不写死在这里，手写两遍必然漂移）；
# ruff 只能看到字面量，认不出 sorted() 返回的就是 list。
__all__ = sorted(_ORIGIN)  # noqa: PLE0605


def __getattr__(name: str) -> Any:
    """按需导入并缓存（PEP 562）。未登记的名字按子模块兜底。"""
    origin = _ORIGIN.get(name)
    if origin is not None:
        value = getattr(importlib.import_module(origin, __name__), name)
    else:
        try:
            value = importlib.import_module(f".{name}", __name__)
        except ModuleNotFoundError:
            raise AttributeError(
                f"module {__name__!r} has no attribute {name!r}"
            ) from None
    globals()[name] = value  # 缓存：后续访问不再走 __getattr__
    return value


def __dir__() -> list[str]:
    """完整名字表（含尚未加载的），供 IDE 补全与 ``from ui.core import *``。"""
    return sorted({*globals(), *_ORIGIN})
