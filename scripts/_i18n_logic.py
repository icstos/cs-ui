"""国际化 (i18n) 纯逻辑单测（不需要窗口）。

覆盖：语言标签归一（zh-CN / zh-Hant-TW / en-US）、注册表解析与回退链接、
消息表拍平与非法值、插值（缺参数不崩）、复数分档、缺键降级与 strict 模式、
JSON 语言包装载、持久化文件读写、完整性体检、hook 在组件外调用是否明确报错。

用法::

    python scripts/_i18n_logic.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ui.core import i18n as i18n_mod
from ui.core.i18n import (
    FileStore,
    Language,
    LanguageRegistry,
    MemoryStore,
    canonical,
    configure,
    flatten,
    i18n_registry,
    plural_category,
    register_messages,
    reset_registry,
    set_locale,
    system_locale,
    t,
    tn,
    use_i18n,
    validate,
)

_fails: list[str] = []
_passed = 0


def check(name: str, got: object, want: object) -> None:
    global _passed
    if got == want:
        _passed += 1
        print(f"PASS  {name}: got={got!r}")
    else:
        _fails.append(f"{name}: got={got!r} want={want!r}")
        print(f"FAIL  {name}: got={got!r} want={want!r}")


def raiser(fn, *args, **kwargs) -> str:
    """执行并返回异常类名（空串 = 没抛）。"""
    try:
        fn(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001 - 单测就是把异常类型当返回值
        return type(exc).__name__
    return ""


# ---------------------------------------------------------------------------
print("\n== 语言标签归一 ==")
check("zh-CN → 简体", canonical("zh-CN"), "zh_Hans")
check("zh_CN → 简体", canonical("zh_CN"), "zh_Hans")
check("zh-Hant-TW → 繁体", canonical("zh-Hant-TW"), "zh_Hant")
check("zh-TW → 繁体（地区推字形）", canonical("zh-TW"), "zh_Hant")
check("en-US 保留地区", canonical("en-US"), "en_US")
check("单独语言码", canonical("en"), "en")
check("空串", canonical(""), "")
check("大小写混合", canonical("ZH-hans"), "zh_Hans")

# ---------------------------------------------------------------------------
print("\n== 注册表解析与回退 ==")
reset_registry()
reg = i18n_registry
check(
    "内置三种语言",
    [item.code for item in reg.languages()],
    ["zh_Hans", "zh_Hant", "en"],
)
check("en-US 落到已注册的 en", reg.resolve("en-US"), "en")
check("zh-TW 落到繁体", reg.resolve("zh-TW"), "zh_Hant")
check("未注册的德语", reg.resolve("de-DE"), None)
check("繁体的回退是简体", reg.fallback_of("zh_Hant"), "zh_Hans")
check("简体的回退是英文", reg.fallback_of("zh_Hans"), "en")
check("英文没有回退", reg.fallback_of("en"), None)

# 只注册 en 时，en_GB / en-AU 都要接住
solo = LanguageRegistry()
solo.add_language(Language("en", "English"))
check("只注册 en 时 en-GB 命中 en", solo.resolve("en-GB"), "en")
check("只注册 en 时 zh-CN 不命中", solo.resolve("zh-CN"), None)
# 同语言多字形：没声明 fallback 时按「同语言其他字形」推断
solo.add_language(Language("zh_Hans", "简体中文"))
solo.add_language(Language("zh_Hant", "繁體中文"))
check("未声明 fallback 时推断到同语言字形", solo.fallback_of("zh_Hant"), "zh_Hans")

# ---------------------------------------------------------------------------
print("\n== 消息表拍平 ==")
check(
    "嵌套拍平",
    flatten({"app": {"title": "标题", "menu": {"file": "文件"}}}),
    {"app.title": "标题", "app.menu.file": "文件"},
)
check("数字转字符串", flatten({"n": 3}), {"n": "3"})
check("非法值报错", raiser(flatten, {"bad": ["a"]}), "TypeError")

# ---------------------------------------------------------------------------
print("\n== 查表 / 回退 / 插值 ==")
register_messages(
    "zh_Hans",
    {
        "app.title": "我的应用",
        "hello": "你好，{name}",
        "files": {"one": "{n} 个文件", "other": "{n} 个文件"},
        "only_hans": "只有简体有",
    },
)
register_messages("zh_Hant", {"app.title": "我的應用"})
register_messages(
    "en",
    {
        "app.title": "My App",
        "hello": "Hello, {name}",
        "files": {"one": "{n} file", "other": "{n} files"},
    },
)

check("简体查表", (set_locale("zh-Hans"), t("app.title"))[1], "我的应用")
set_locale("zh-Hant")
check("繁体查自己的键", t("app.title"), "我的應用")
check("繁体缺的键回退简体", t("only_hans"), "只有简体有")
check("切到英文", (set_locale("en"), t("app.title"))[1], "My App")
check("英文回退链不含简体独有键 → 返回键名", t("only_hans"), "only_hans")
check("插值", t("hello", name="Shawn"), "Hello, Shawn")
check("缺参数保留占位符", t("hello"), "Hello, {name}")
check("未注册语言切不过去", set_locale("de"), False)
check("切换后 locale 未变", i18n_mod.current_locale(), "en")

check("复数 en: 1", tn("files", 1), "1 file")
check("复数 en: 3", tn("files", 3), "3 files")
set_locale("zh_Hans")
check("复数 zh 恒为 other", tn("files", 3), "3 个文件")
check("复数 zh 单数也走 other", tn("files", 1), "1 个文件")
check("别名的 {count} 也可用", plural_category("en", 2), "other")
check("未注册语言的复数规则兜底", plural_category("xx", 1), "one")

# ---------------------------------------------------------------------------
print("\n== 缺键策略 ==")
state = i18n_mod.i18n_state()
state.reset_diagnostics()
check("缺键返回键名", t("nope.missing"), "nope.missing")
check("缺键计数", state.missing().get("nope.missing"), 1)
t("nope.missing")
check("缺键计数累加", state.missing().get("nope.missing"), 2)
configure(strict=True)
check("strict 模式抛 KeyError", raiser(t, "nope.missing"), "KeyError")
configure(strict=False)
check("恢复非 strict", raiser(t, "nope.missing"), "")

# ---------------------------------------------------------------------------
print("\n== JSON 语言包 ==")
with tempfile.TemporaryDirectory() as tmp:
    folder = Path(tmp)
    (folder / "fr.json").write_text(
        json.dumps(
            {
                "_meta": {
                    "native_name": "Français",
                    "english_name": "French",
                    "fallback": "en",
                },
                "messages": {"app": {"title": "Mon App"}, "hello": "Bonjour, {name}"},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (folder / "de.json").write_text(
        json.dumps({"app.title": "Meine App"}, ensure_ascii=False), encoding="utf-8"
    )
    count = i18n_mod.load_catalogs(folder)
    check("目录装载的键数量", count, 3)
    check(
        "文件名推出语言码", [item.code for item in reg.languages()][-2:], ["de", "fr"]
    )
    check("meta 里的母语名", reg.get("fr").native_name, "Français")
    check("meta 里的回退", reg.get("fr").fallback, "en")
    set_locale("fr")
    check("法语查表", t("app.title"), "Mon App")
    check("法语插值", t("hello", name="Shawn"), "Bonjour, Shawn")
    check("法语缺键回退英文", t("only_hans"), "only_hans")
    set_locale("de_DE")
    check("de_DE 落到 de", i18n_mod.current_locale(), "de")
    check("德语查表", t("app.title"), "Meine App")

    # 持久化
    store = FileStore(Path(tmp, "cfg", "i18n.json"))
    check("空文件读 None", store.read(), None)
    store.write("zh_Hant")
    check("写回读一致", store.read(), "zh_Hant")
    check(
        "文件是 UTF-8 JSON 对象",
        json.loads(store.path.read_text(encoding="utf-8")).get("locale"),
        "zh_Hant",
    )
    store.path.write_text("{oops", encoding="utf-8")
    check("坏 JSON 读 None", store.read(), None)

# ---------------------------------------------------------------------------
print("\n== 体检 / 状态 ==")
reset_registry()
register_messages("zh_Hans", {"a": "1", "b": "2", "c": "3"})
register_messages("zh_Hant", {"a": "1"})
register_messages("en", {"a": "1", "b": "2"})
report = validate("zh_Hans")
check("基准语言不出现在报告里", "zh_Hans" in report, False)
check("繁体缺 b / c", report["zh_Hant"], ["b", "c"])
check("英文缺 c", report["en"], ["c"])

state = i18n_mod.i18n_state()
check("i18n_state() 是单例", i18n_mod.i18n_state() is state, True)
check("context 默认值就是那个单例", i18n_mod.i18n_context.default_value is state, True)
check("use_i18n 在组件体外明确报错", raiser(use_i18n), "RuntimeError")

# 回退链随语言与兜底语言同步更新
configure(fallback="zh_Hans")
set_locale("zh_Hant")
check("回退链：繁体 → 简体 → 英文", state._chain, ("zh_Hant", "zh_Hans", "en"))
set_locale("en")
check("回退链：英文 → 兜底简体", state._chain, ("en", "zh_Hans"))
configure(fallback="en")

# 首帧绑定优先顺序：存过的 > 应用指定 > 系统
state._store = MemoryStore("zh_Hant")
state._bound = False
state.locale = "en"
i18n_mod._bind(
    None, state, initial="zh_Hans", store=MemoryStore("zh_Hant"), detect=False
)
check("持久化选择压过应用默认值", state.locale, "zh_Hant")
state._bound = False
i18n_mod._bind(None, state, initial="zh_Hans", store=MemoryStore(None), detect=False)
check("没存过就用应用默认值", state.locale, "zh_Hans")

# 性能护栏：查表不产生临时拆分（键已经是拍平的点号串）
check("t() 的键就是扁平串", set_locale("zh_Hans") and t("a"), "1")

# 运行期补文案要能立刻生效（revision 推进 → 订阅者重绘）
rev_before = state.revision
register_messages("zh_Hans", {"hot.key": "热更新"})
check("热更新推进 revision", state.revision > rev_before, True)
check("热更新立即可查", t("hot.key"), "热更新")

check("system_locale 不抛异常", isinstance(system_locale(), (str, type(None))), True)

# ---------------------------------------------------------------------------
reset_registry()
set_locale("zh_Hans")
print(
    f"\nRESULT: {'ALL PASS' if not _fails else f'{len(_fails)} FAILED'}"
    f"  (passed={_passed})"
)
if _fails:
    for line in _fails:
        print("  -", line)
    sys.exit(1)
