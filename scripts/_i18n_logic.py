"""国际化 (i18n) 纯逻辑单测（不需要窗口）。

覆盖：语言标签归一（zh-CN / zh-TW / zh-Hant-HK / en-US）、注册表解析与回退链、
消息表拍平（含列表）、插值（缺参数不崩）、复数分档、缺键降级与 strict 模式、
成组文案 tl()、本地化格式化（数字/日期/月份/星期/列表）、JSON 语言包装载、
持久化文件读写、完整性体检、hook 在组件外调用是否明确报错。

用法::

    python scripts/_i18n_logic.py
"""

from __future__ import annotations

import datetime as _dt
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ui.core import i18n as i18n_mod
from ui.core import locales as locales_mod
from ui.core.format import (
    calendar_title,
    first_weekday,
    format_date,
    format_list,
    format_number,
    format_time,
    month_cell,
    month_name,
    weekday_names,
)
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
    tl,
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
print("\n== 语言标签归一（地区优先于文字）==")
check("zh-CN → 地区码", canonical("zh-CN"), "zh_CN")
check("zh_CN 幂等", canonical("zh_CN"), "zh_CN")
check("zh-TW → 地区码", canonical("zh-TW"), "zh_TW")
check("zh-Hant-TW → 地区优先", canonical("zh-Hant-TW"), "zh_TW")
check("en-US 保留地区", canonical("en-US"), "en_US")
check("单独语言码", canonical("en"), "en")
check("空串", canonical(""), "")
check("只有文字没有地区", canonical("ZH-hans"), "zh_Hans")

# ---------------------------------------------------------------------------
print("\n== 注册表解析与回退 ==")
reset_registry()
reg = i18n_registry
check(
    "内置三种语言（顺序 = 菜单顺序）",
    [item.code for item in reg.languages()],
    ["zh_CN", "zh_TW", "en_US"],
)
check("Language.tag 转 BCP 47", reg.get("zh_TW").tag, "zh-TW")
check("en-US 精确命中", reg.resolve("en-US"), "en_US")
check("zh-TW 命中繁体", reg.resolve("zh-TW"), "zh_TW")
check("zh-CN 命中简体", reg.resolve("zh-CN"), "zh_CN")
check("只有文字 zh-Hant 也能落到繁体", reg.resolve("zh-Hant"), "zh_TW")
check("zh-Hant-HK 落到繁体", reg.resolve("zh-Hant-HK"), "zh_TW")
check("未注册的德语", reg.resolve("de-DE"), None)
check("繁体的回退是简体", reg.fallback_of("zh_TW"), "zh_CN")
check("简体的回退是英文", reg.fallback_of("zh_CN"), "en_US")
check("英文没有回退", reg.fallback_of("en_US"), None)

# 只注册 en 时，en_GB / en-AU 都要接住
solo = LanguageRegistry()
solo.add_language(Language("en", "English"))
check("只注册 en 时 en-GB 命中 en", solo.resolve("en-GB"), "en")
check("只注册 en 时 zh-CN 不命中", solo.resolve("zh-CN"), None)
# 同语言多地区：没声明 fallback 时按「同语言其他地区」推断
solo.add_language(Language("zh_CN", "简体中文"))
solo.add_language(Language("zh_TW", "繁體中文"))
check("未声明 fallback 时推断到同语言其他地区", solo.fallback_of("zh_TW"), "zh_CN")

# ---------------------------------------------------------------------------
print("\n== 消息表拍平 ==")
check(
    "嵌套拍平",
    flatten({"app": {"title": "标题", "menu": {"file": "文件"}}}),
    {"app.title": "标题", "app.menu.file": "文件"},
)
check("数字转字符串", flatten({"n": 3}), {"n": "3"})
check(
    "列表按下标展开",
    flatten({"cities": ["北京", "上海"]}),
    {"cities.0": "北京", "cities.1": "上海"},
)
check("非法值报错", raiser(flatten, {"bad": object()}), "TypeError")

# ---------------------------------------------------------------------------
print("\n== 查表 / 回退 / 插值 ==")
register_messages(
    "zh_CN",
    {
        "app.title": "我的应用",
        "hello": "你好，{name}",
        "files": {"one": "{n} 个文件", "other": "{n} 个文件"},
        "only_hans": "只有简体有",
        "cities": ["北京", "上海", "广州"],
    },
)
register_messages("zh_TW", {"app.title": "我的應用"})
register_messages(
    "en_US",
    {
        "app.title": "My App",
        "hello": "Hello, {name}",
        "files": {"one": "{n} file", "other": "{n} files"},
        "cities": ["Beijing", "Shanghai"],
    },
)

check("简体查表", (set_locale("zh-CN"), t("app.title"))[1], "我的应用")
set_locale("zh-TW")
check("繁体查自己的键", t("app.title"), "我的應用")
check("繁体缺的键回退简体", t("only_hans"), "只有简体有")
check("切到英文", (set_locale("en-US"), t("app.title"))[1], "My App")
check("英文回退链不含简体独有键 → 返回键名", t("only_hans"), "only_hans")
check("插值", t("hello", name="Shawn"), "Hello, Shawn")
check("缺参数保留占位符", t("hello"), "Hello, {name}")
check("未注册语言切不过去", set_locale("de"), False)
check("切换后 locale 未变", i18n_mod.current_locale(), "en_US")

set_locale("zh-CN")
check("成组文案（中文 3 项）", tl("cities"), ["北京", "上海", "广州"])
set_locale("en-US")
check("成组文案（英文 2 项，长度各写各的）", tl("cities"), ["Beijing", "Shanghai"])
check("取不存在的成组键返回空表", tl("nope.list"), [])

check("复数 en: 1", tn("files", 1), "1 file")
check("复数 en: 3", tn("files", 3), "3 files")
set_locale("zh-CN")
check("复数 zh 恒为 other", tn("files", 3), "3 个文件")
check("复数 zh 单数也走 other", tn("files", 1), "1 个文件")
check("复数档位查询 en: 2", plural_category("en", 2), "other")
check("未注册语言的复数规则兜底", plural_category("xx", 1), "one")

# ---------------------------------------------------------------------------
print("\n== 本地化格式化 ==")
set_locale("zh-CN")
check("数字分组 zh", format_number(1286), "1,286")
check("固定小数位", format_number(1234567.891, decimals=2), "1,234,567.89")
check("日期 zh", format_date(_dt.date(2026, 9, 26)), "2026-09-26")
check("长日期 zh 不加空格", format_date(_dt.date(2026, 9, 26), long=True), "2026年9月26日")
check("时间 zh", format_time(_dt.time(9, 30)), "09:30")
check("时间带秒", format_time(_dt.time(9, 30, 15), seconds=True), "09:30:15")
check("月份名 zh", month_name(9), "9月")
check("日历标题 zh", calendar_title(2026, 9), "2026年9月")
check("日历单元格 zh", month_cell(9), "9月")
check("每周首日 zh = 周一", first_weekday(), 0)
check("列表连接 zh", format_list(["A", "B", "C"]), "A、B、C")
check("列表折叠", format_list(["A", "B", "C", "D"], limit=2), "A、B、+2")

set_locale("en-US")
check("数字分组 en", format_number(1286), "1,286")
check("日期 en 月在前", format_date(_dt.date(2026, 9, 26)), "09/26/2026")
check(
    "长日期 en",
    format_date(_dt.date(2026, 9, 26), long=True),
    "September 26, 2026",
)
check("月份缩写 en", month_name(9, short=True), "Sep")
check("日历标题 en 月在前", calendar_title(2026, 9), "September 2026")
check("每周首日 en = 周日", first_weekday(), 6)
check("星期名 en 从周一起", weekday_names()[0], "Mo")
check("列表连接 en", format_list(["A", "B"]), "A, B")

set_locale("zh-TW")
check("月份名 zh-TW", month_name(9), "9月")

# ---------------------------------------------------------------------------
print("\n== 框架自带文案完整性 ==")
check(
    "三份语言包无缺键（以 en-US 为基准）",
    locales_mod.missing_translations(),
    {"zh-CN": [], "zh-TW": []},
)
reset_registry()
check(
    "reset 后仍有三份语言包",
    sorted(len(i18n_registry.messages(code)) for code in ("zh_CN", "zh_TW", "en_US")),
    [len(i18n_registry.messages("zh_CN"))] * 3,
)
check("内置键都翻好了", validate("zh_CN"), {"zh_TW": [], "en_US": []})

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
    store.write("zh_TW")
    check("写回读一致", store.read(), "zh_TW")
    check(
        "文件是 UTF-8 JSON 对象",
        json.loads(store.path.read_text(encoding="utf-8")).get("locale"),
        "zh_TW",
    )
    store.path.write_text("{oops", encoding="utf-8")
    check("坏 JSON 读 None", store.read(), None)

# ---------------------------------------------------------------------------
print("\n== 体检 / 状态 ==")
reset_registry()
register_messages("zh_CN", {"a": "1", "b": "2", "c": "3"})
register_messages("zh_TW", {"a": "1"})
register_messages("en_US", {"a": "1", "b": "2"})
report = validate("zh_CN")
check("基准语言不出现在报告里", "zh_CN" in report, False)
check("繁体缺 b / c", report["zh_TW"], ["b", "c"])
check("英文缺 c", report["en_US"], ["c"])

state = i18n_mod.i18n_state()
check("i18n_state() 是单例", i18n_mod.i18n_state() is state, True)
check("context 默认值就是那个单例", i18n_mod.i18n_context.default_value is state, True)
check("use_i18n 在组件体外明确报错", raiser(use_i18n), "RuntimeError")

# 回退链随语言与兜底语言同步更新
configure(fallback="zh_CN")
set_locale("zh_TW")
check("回退链：繁体 → 简体 → 英文", state._chain, ("zh_TW", "zh_CN", "en_US"))
set_locale("en_US")
check("回退链：英文 → 兜底简体", state._chain, ("en_US", "zh_CN"))
configure(fallback="en_US")

# 首帧绑定优先顺序：存过的 > 应用指定 > 系统
state._store = MemoryStore("zh_TW")
state._bound = False
state.locale = "en_US"
i18n_mod._bind(
    None, state, initial="zh_CN", store=MemoryStore("zh_TW"), detect=False
)
check("持久化选择压过应用默认值", state.locale, "zh_TW")
state._bound = False
i18n_mod._bind(None, state, initial="zh_CN", store=MemoryStore(None), detect=False)
check("没存过就用应用默认值", state.locale, "zh_CN")

# 性能护栏：查表不产生临时拆分（键已经是拍平的点号串）
check("t() 的键就是扁平串", set_locale("zh_CN") and t("a"), "1")

# 运行期补文案要能立刻生效（revision 推进 → 订阅者重绘）
rev_before = state.revision
register_messages("zh_CN", {"hot.key": "热更新"})
check("热更新推进 revision", state.revision > rev_before, True)
check("热更新立即可查", t("hot.key"), "热更新")

check("system_locale 不抛异常", isinstance(system_locale(), (str, type(None))), True)

# ---------------------------------------------------------------------------
reset_registry()
set_locale("zh_CN")
print(
    f"\nRESULT: {'ALL PASS' if not _fails else f'{len(_fails)} FAILED'}"
    f"  (passed={_passed})"
)
if _fails:
    for line in _fails:
        print("  -", line)
    sys.exit(1)
