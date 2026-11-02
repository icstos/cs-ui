"""【已迁移】多语言实现移到了框架包内：``ui.core.i18n``。

这个文件保留下来只为两件事：一是让老的 ``from i18n import t`` 继续能用，
二是给出新旧写法的对照。**新代码请直接从 ui 导入**：

    from ui import I18nProvider, LanguageSwitcher, register_messages, use_t

为什么搬走：i18n 是框架能力（``I18nProvider`` 要写 ``page``、``use_t()`` 是 hook、
``LanguageSwitcher`` 是组件），留在仓库根目录既进不了 wheel，也没法和
``ui.core.theme`` 共用同一套 observable + context 订阅。

旧写法 → 新写法：

    I18n(langs={"zh_CN": {...}}, fallback="zh_CN")   →  register_messages("zh_Hans", {...})
                                                        configure(fallback="zh_Hans")
    t("a.b")                                         →  t("a.b")            # 组件里用 use_t()
    i18n.set_lang("en")                              →  set_locale("en")
    i18n.get_lang()                                  →  current_locale()

语言持久化也不再依赖 ``page.client_storage``（flet 1.0 里它变成了异步的
``SharedPreferences`` 服务）：默认写本地 JSON 文件，首帧即可同步读回，
所以启动时不会先闪一下默认语言。
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from ui.core.i18n import (  # noqa: F401
    FileStore,
    I18nProvider,
    I18nState,
    Language,
    LanguageRegistry,
    LanguageSwitcher,
    LocaleStore,
    MemoryStore,
    Translator,
    available_languages,
    canonical,
    configure,
    current_language,
    current_locale,
    i18n_context,
    i18n_registry,
    i18n_state,
    load_catalogs,
    missing_keys,
    register_language,
    register_messages,
    reset_registry,
    set_locale,
    t,
    tn,
    use_i18n,
    use_t,
    validate,
)


class I18n:
    """旧 API 的兼容壳（**已废弃**，只为不改老调用方）。

    ``I18n(langs={...}, fallback=...)`` 现在等于「注册语言 + 注册文案 + 设兜底语言」，
    真正的渲染接入要另外用 :class:`I18nProvider` 包一层根视图。
    ``config_dir`` / ``prefix`` / ``defmode`` 三个老参数已无意义，忽略。
    """

    def __init__(
        self,
        langs: dict[str, dict],
        fallback: str,
        config_dir: str = "",
        defmode: bool = True,
        client_storage: Any = None,
        prefix: str = "",
    ) -> None:
        for code, messages in langs.items():
            register_language(code)
            register_messages(code, messages)
        configure(fallback=fallback)

    def get_lang(self) -> str:
        return current_locale()

    def set_lang(self, lang: str) -> str:
        set_locale(lang)
        return current_locale()

    def get_locale_key(self, key: str | list) -> str:
        return t(".".join(key) if isinstance(key, list) else key)


if __name__ == "__main__":
    # 最小自检：注册一份文案 → 切语言 → 打印
    register_messages("zh_Hans", {"demo.hello": "你好，{name}"})
    register_messages("en", {"demo.hello": "Hello, {name}"})
    for code in ("zh_Hans", "en"):
        set_locale(code)
        print(f"{code}: {t('demo.hello', name='Shawn')}  (当前={current_locale()})")
    print("可用语言：", [item.code for item in available_languages()])
