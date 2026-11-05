"""框架内置语言包：``zh-CN`` / ``zh-TW`` / ``en-US``。

这里只放**框架自己的界面文案** —— 分页器、月历、选择器页脚、媒体控件这些
由组件库画出来、调用方既没传参也管不到的文字。业务文案归应用，
用 :func:`ui.core.i18n.register_messages` 或 ``load_catalogs`` 注册。

三条约定：

1. **键按"归属 + 角色"命名**（``ui.pagination.total``）。``ui.`` 前缀是留给框架的
   命名空间，应用自己的键不要用，避免将来扩展时撞车。
2. **全部用 ``str.format`` 占位**，并且只占"短句内"的位置。语序差异靠
   *整句模板* 吸收（``"{n} {unit}"`` 与 ``"共 {n} {unit}"``），绝不把一句话
   拆成几段拼 —— 那是翻译腔和语序错误的根源。
3. **数字、日期、月份名、星期名也进语言包**（``ui.calendar.months`` /
   ``ui.format.*``）。写死 ``"1月"`` 或 ``","`` 是最常见的"假国际化"：
   界面翻译了，但日历里还是中文月份。

新增一门语言 = 复制 :data:`CATALOGS` 里任意一份改文案，然后在应用入口
``register_language(Language(...))`` 注册。三份表结构必须一致，
:func:`missing_translations` 会在提测前把漏翻的键列出来。
"""

from __future__ import annotations

from collections.abc import Mapping

__all__ = ["CATALOGS", "DEFAULT_LOCALE", "FALLBACK_LOCALE", "MESSAGES", "missing_translations"]

#: 缺省语言（首帧未存过选择、系统语言也认不出时用它）
DEFAULT_LOCALE = "zh-CN"

#: 回退链的终点：任何键在本地语言里翻不出来时，最终落到这里
FALLBACK_LOCALE = "en-US"


_ZH_CN: dict[str, object] = {
    "ui": {
        "common": {
            "ok": "确定",
            "cancel": "取消",
            "close": "关闭",
            "clear": "清除",
            "done": "完成",
            "reset": "重置",
            "select_all": "全选",
            "search": "搜索",
            "empty": "暂无数据",
            "placeholder": "请选择",
            "revert": "还原",
        },
        "language": {"tooltip": "界面语言"},
        "theme": {
            "primary": "主色 · {name}",
            "mode": "明暗：{mode}（{setting}）",
            "dark": "深色",
            "light": "浅色",
            "system": "跟随系统",
            "seeds": {
                "blue": "蓝",
                "indigo": "靛蓝",
                "violet": "紫罗兰",
                "teal": "青碧",
                "green": "绿",
                "orange": "橙",
                "red": "红",
                "slate": "石板灰",
            },
        },
        "pagination": {
            "total": "共 {n} {unit}",
            "first": "首页",
            "prev": "上一页",
            "next": "下一页",
            "last": "尾页",
            "page": "第 {n} 页",
            "goto": "前往",
            "page_unit": "页",
            "per_page": "每页",
            "unit": "项",
        },
        "table": {"number": "编号"},
        "codeview": {"title": "查看代码"},
        "menu": {
            "collapse": "收起菜单",
            "expand": "展开菜单",
        },
        "carousel": {
            "prev": "上一张",
            "next": "下一张",
            "slide": "第 {n} 张",
            "empty": "暂无内容",
        },
        "calendar": {
            "title_day": "{year}年{num}月",
            "title_year": "{year}年",
            "title_years": "{a} 年 - {b} 年",
            "cell_month": "{num}月",
            "prev_month": "上一月",
            "next_month": "下一月",
            "prev_year": "上一年",
            "next_year": "下一年",
            "mode": {"month": "月", "year": "年"},
            "first_weekday": "0",
            "weekdays": {
                1: "一",
                2: "二",
                3: "三",
                4: "四",
                5: "五",
                6: "六",
                7: "日",
            },
            "months": {
                1: "1月",
                2: "2月",
                3: "3月",
                4: "4月",
                5: "5月",
                6: "6月",
                7: "7月",
                8: "8月",
                9: "9月",
                10: "10月",
                11: "11月",
                12: "12月",
            },
            "months_short": {
                1: "1月",
                2: "2月",
                3: "3月",
                4: "4月",
                5: "5月",
                6: "6月",
                7: "7月",
                8: "8月",
                9: "9月",
                10: "10月",
                11: "11月",
                12: "12月",
            },
        },
        "date": {
            "placeholder": "请选择日期",
            "today": "今天",
            "week": "{year} 年第 {n} 周",
            "ph": {
                "date": "请选择日期",
                "week": "请选择周",
                "month": "请选择月份",
                "year": "请选择年份",
                "dates": "请选择日期（可多选）",
                "months": "请选择月份（可多选）",
                "years": "请选择年份（可多选）",
                "daterange": "开始日期 ~ 结束日期",
                "monthrange": "开始月份 ~ 结束月份",
            },
        },
        "datetime": {
            "placeholder": "请选择日期时间",
            "now": "此刻",
            "done": "完成",
            "hour": "时",
            "minute": "分",
            "second": "秒",
            "prev_step": "上一格（滚轮同样可用）",
            "next_step": "下一格（滚轮同样可用）",
        },
        "multiselect": {"selected": "已选 {n} / {total}", "empty": "暂无可选项"},
        "transfer": {
            "source": "待选",
            "target": "已选",
            "search": "搜索",
            "move_right": "移入已选",
            "move_left": "移回待选",
            "empty_source": "没有可选项",
            "empty_source_hint": "可选项都已移到右侧",
            "empty_target": "还没有选中任何项",
            "empty_target_hint": "在左侧勾选后点中间的箭头",
        },
        "tree": {"empty": "暂无节点"},
        "cascader": {"placeholder": "请选择", "empty": "暂无数据"},
        "color": {
            "placeholder": "请选择颜色",
            "revert": "还原到打开面板时的颜色",
            "format": "数值记法：{format}（点击切换）",
            "range": "{name}：0 ~ {max}",
        },
        "image": {"size": "缩略图尺寸", "unit": "张"},
        "pdf": {
            "open": "打开",
            "open_tooltip": "打开本地 PDF",
            "reload": "重新加载",
            "empty": "未选择 PDF",
            "failed": "文档加载失败",
        },
        "audio": {
            "title": "音频",
            "idle": "未播放",
            "playing": "播放中",
            "paused": "已暂停",
            "toggle": "播放 / 暂停",
        },
        "app": {"not_found": "当前页未定义", "back_home": "回到首页"},
        "file": {
            "choose": "选择文件",
            "choose_dir": "选择文件夹",
            "save": "保存文件",
        },
        "format": {
            "list_sep": "、",
            "thousand": ",",
            "decimal": ".",
            "range_sep": " ~ ",
            "date": "{y:04d}-{m:02d}-{d:02d}",
            "date_long": "{y:04d}年{m}月{d}日",
            "time": "{h:02d}:{mi:02d}",
            "time_seconds": "{h:02d}:{mi:02d}:{s:02d}",
        },
        "heatmap": {
            "less": "少",
            "more": "多",
            "empty": "暂无数据",
            "tooltip": "{date} · {value}",
        },
    }
}

_ZH_TW: dict[str, object] = {
    "ui": {
        "common": {
            "ok": "確定",
            "cancel": "取消",
            "close": "關閉",
            "clear": "清除",
            "done": "完成",
            "reset": "重設",
            "select_all": "全選",
            "search": "搜尋",
            "empty": "暫無資料",
            "placeholder": "請選擇",
            "revert": "還原",
        },
        "language": {"tooltip": "介面語言"},
        "theme": {
            "primary": "主色 · {name}",
            "mode": "明暗：{mode}（{setting}）",
            "dark": "深色",
            "light": "淺色",
            "system": "跟隨系統",
            "seeds": {
                "blue": "藍",
                "indigo": "靛藍",
                "violet": "紫羅蘭",
                "teal": "青碧",
                "green": "綠",
                "orange": "橙",
                "red": "紅",
                "slate": "石板灰",
            },
        },
        "pagination": {
            "total": "共 {n} {unit}",
            "first": "首頁",
            "prev": "上一頁",
            "next": "下一頁",
            "last": "末頁",
            "page": "第 {n} 頁",
            "goto": "前往",
            "page_unit": "頁",
            "per_page": "每頁",
            "unit": "項",
        },
        "table": {"number": "編號"},
        "codeview": {"title": "檢視程式碼"},
        "menu": {
            "collapse": "收合選單",
            "expand": "展開選單",
        },
        "carousel": {
            "prev": "上一張",
            "next": "下一張",
            "slide": "第 {n} 張",
            "empty": "暫無內容",
        },
        "calendar": {
            "title_day": "{year}年{num}月",
            "title_year": "{year}年",
            "title_years": "{a} 年 - {b} 年",
            "cell_month": "{num}月",
            "prev_month": "上一月",
            "next_month": "下一月",
            "prev_year": "上一年",
            "next_year": "下一年",
            "mode": {"month": "月", "year": "年"},
            "first_weekday": "0",
            "weekdays": {
                1: "一",
                2: "二",
                3: "三",
                4: "四",
                5: "五",
                6: "六",
                7: "日",
            },
            "months": {
                1: "1月",
                2: "2月",
                3: "3月",
                4: "4月",
                5: "5月",
                6: "6月",
                7: "7月",
                8: "8月",
                9: "9月",
                10: "10月",
                11: "11月",
                12: "12月",
            },
            "months_short": {
                1: "1月",
                2: "2月",
                3: "3月",
                4: "4月",
                5: "5月",
                6: "6月",
                7: "7月",
                8: "8月",
                9: "9月",
                10: "10月",
                11: "11月",
                12: "12月",
            },
        },
        "date": {
            "placeholder": "請選擇日期",
            "today": "今天",
            "week": "{year} 年第 {n} 週",
            "ph": {
                "date": "請選擇日期",
                "week": "請選擇週",
                "month": "請選擇月份",
                "year": "請選擇年份",
                "dates": "請選擇日期（可多選）",
                "months": "請選擇月份（可多選）",
                "years": "請選擇年份（可多選）",
                "daterange": "開始日期 ~ 結束日期",
                "monthrange": "開始月份 ~ 結束月份",
            },
        },
        "datetime": {
            "placeholder": "請選擇日期時間",
            "now": "此刻",
            "done": "完成",
            "hour": "時",
            "minute": "分",
            "second": "秒",
            "prev_step": "上一格（滾輪同樣可用）",
            "next_step": "下一格（滾輪同樣可用）",
        },
        "multiselect": {"selected": "已選 {n} / {total}", "empty": "暫無選項"},
        "transfer": {
            "source": "待選",
            "target": "已選",
            "search": "搜尋",
            "move_right": "移入已選",
            "move_left": "移回待選",
            "empty_source": "沒有可選項",
            "empty_source_hint": "可選項都已移到右側",
            "empty_target": "還沒有選中任何項",
            "empty_target_hint": "在左側勾選後點中間的箭頭",
        },
        "tree": {"empty": "暫無節點"},
        "cascader": {"placeholder": "請選擇", "empty": "暫無數據"},
        "color": {
            "placeholder": "請選擇顏色",
            "revert": "還原為開啟面板時的顏色",
            "format": "數值記法：{format}（點擊切換）",
            "range": "{name}：0 ~ {max}",
        },
        "image": {"size": "縮圖尺寸", "unit": "張"},
        "pdf": {
            "open": "開啟",
            "open_tooltip": "開啟本機 PDF",
            "reload": "重新載入",
            "empty": "未選擇 PDF",
            "failed": "文件載入失敗",
        },
        "audio": {
            "title": "音訊",
            "idle": "未播放",
            "playing": "播放中",
            "paused": "已暫停",
            "toggle": "播放 / 暫停",
        },
        "app": {"not_found": "目前頁面未定義", "back_home": "回到首頁"},
        "file": {
            "choose": "選擇檔案",
            "choose_dir": "選擇資料夾",
            "save": "儲存檔案",
        },
        "format": {
            "list_sep": "、",
            "thousand": ",",
            "decimal": ".",
            "range_sep": " ~ ",
            "date": "{y:04d}-{m:02d}-{d:02d}",
            "date_long": "{y:04d}年{m}月{d}日",
            "time": "{h:02d}:{mi:02d}",
            "time_seconds": "{h:02d}:{mi:02d}:{s:02d}",
        },
        "heatmap": {
            "less": "少",
            "more": "多",
            "empty": "暫無資料",
            "tooltip": "{date} · {value}",
        },
    }
}

_EN_US: dict[str, object] = {
    "ui": {
        "common": {
            "ok": "OK",
            "cancel": "Cancel",
            "close": "Close",
            "clear": "Clear",
            "done": "Done",
            "reset": "Reset",
            "select_all": "Select all",
            "search": "Search",
            "empty": "No data",
            "placeholder": "Select…",
            "revert": "Revert",
        },
        "language": {"tooltip": "Interface language"},
        "theme": {
            "primary": "Primary · {name}",
            "mode": "Appearance: {mode} ({setting})",
            "dark": "Dark",
            "light": "Light",
            "system": "System",
            "seeds": {
                "blue": "Blue",
                "indigo": "Indigo",
                "violet": "Violet",
                "teal": "Teal",
                "green": "Green",
                "orange": "Orange",
                "red": "Red",
                "slate": "Slate",
            },
        },
        "pagination": {
            "total": "{n} {unit}",
            "first": "First page",
            "prev": "Previous page",
            "next": "Next page",
            "last": "Last page",
            "page": "Page {n}",
            "goto": "Go to",
            "page_unit": "",
            "per_page": "Rows per page",
            "unit": "items",
        },
        "table": {"number": "#"},
        "codeview": {"title": "View code"},
        "menu": {
            "collapse": "Collapse menu",
            "expand": "Expand menu",
        },
        "carousel": {
            "prev": "Previous slide",
            "next": "Next slide",
            "slide": "Slide {n}",
            "empty": "Nothing to show",
        },
        "calendar": {
            "title_day": "{name} {year}",
            "title_year": "{year}",
            "title_years": "{a} – {b}",
            "cell_month": "{short}",
            "prev_month": "Previous month",
            "next_month": "Next month",
            "prev_year": "Previous year",
            "next_year": "Next year",
            "mode": {"month": "Month", "year": "Year"},
            "first_weekday": "6",
            "weekdays": {
                1: "Mo",
                2: "Tu",
                3: "We",
                4: "Th",
                5: "Fr",
                6: "Sa",
                7: "Su",
            },
            "months": {
                1: "January",
                2: "February",
                3: "March",
                4: "April",
                5: "May",
                6: "June",
                7: "July",
                8: "August",
                9: "September",
                10: "October",
                11: "November",
                12: "December",
            },
            "months_short": {
                1: "Jan",
                2: "Feb",
                3: "Mar",
                4: "Apr",
                5: "May",
                6: "Jun",
                7: "Jul",
                8: "Aug",
                9: "Sep",
                10: "Oct",
                11: "Nov",
                12: "Dec",
            },
        },
        "date": {
            "placeholder": "Select a date",
            "today": "Today",
            "week": "Week {n}, {year}",
            "ph": {
                "date": "Select a date",
                "week": "Select a week",
                "month": "Select a month",
                "year": "Select a year",
                "dates": "Select dates",
                "months": "Select months",
                "years": "Select years",
                "daterange": "Start date ~ End date",
                "monthrange": "Start month ~ End month",
            },
        },
        "datetime": {
            "placeholder": "Select date & time",
            "now": "Now",
            "done": "Done",
            "hour": "HH",
            "minute": "MM",
            "second": "SS",
            "prev_step": "Step back (mouse wheel also works)",
            "next_step": "Step forward (mouse wheel also works)",
        },
        "multiselect": {"selected": "{n} of {total} selected", "empty": "No options"},
        "transfer": {
            "source": "Available",
            "target": "Selected",
            "search": "Search",
            "move_right": "Move to selected",
            "move_left": "Move back",
            "empty_source": "Nothing left to pick",
            "empty_source_hint": "Everything has moved to the right",
            "empty_target": "Nothing selected yet",
            "empty_target_hint": "Tick items on the left, then use the arrows",
        },
        "tree": {"empty": "No nodes"},
        "cascader": {"placeholder": "Select", "empty": "No data"},
        "color": {
            "placeholder": "Select a color",
            "revert": "Revert to the color when the panel opened",
            "format": "Numeric notation: {format} (click to switch)",
            "range": "{name}: 0 – {max}",
        },
        "image": {"size": "Thumbnail size", "unit": "images"},
        "pdf": {
            "open": "Open",
            "open_tooltip": "Open a local PDF",
            "reload": "Reload",
            "empty": "No PDF selected",
            "failed": "Failed to load the document",
        },
        "audio": {
            "title": "Audio",
            "idle": "Not playing",
            "playing": "Playing",
            "paused": "Paused",
            "toggle": "Play / Pause",
        },
        "app": {"not_found": "Page not found", "back_home": "Back to home"},
        "file": {
            "choose": "Choose file",
            "choose_dir": "Choose folder",
            "save": "Save file",
        },
        "format": {
            "list_sep": ", ",
            "thousand": ",",
            "decimal": ".",
            "range_sep": " – ",
            "date": "{m:02d}/{d:02d}/{y:04d}",
            "date_long": "{name} {d}, {y:04d}",
            "time": "{h:02d}:{mi:02d}",
            "time_seconds": "{h:02d}:{mi:02d}:{s:02d}",
        },
        "heatmap": {
            "less": "Less",
            "more": "More",
            "empty": "No data",
            "tooltip": "{date} · {value}",
        },
    }
}


#: 语言码 → 消息表。键用 BCP 47 写法（``zh-CN``），装表时归一成 ``zh_CN``。
#: 语言码与 :class:`ui.core.i18n.Language` 的 ``code`` 一一对应。
CATALOGS: dict[str, dict[str, object]] = {
    "zh-CN": _ZH_CN,
    "zh-TW": _ZH_TW,
    "en-US": _EN_US,
}


def _walk(messages: Mapping[str, object], prefix: str = "") -> dict[str, str]:
    """把嵌套消息表拍平成 ``{"ui.pagination.total": "..."}``（只读用途）。"""
    flat: dict[str, str] = {}
    for key, value in messages.items():
        path = f"{prefix}{key}"
        if isinstance(value, Mapping):
            flat.update(_walk(value, f"{path}."))
        else:
            flat[path] = str(value)
    return flat


#: 拍平后的只读视图（键 → 文案），诊断与完整性校验都基于它
MESSAGES: dict[str, dict[str, str]] = {
    code: _walk(messages) for code, messages in CATALOGS.items()
}


def missing_translations(reference: str = "en-US") -> dict[str, list[str]]:
    """以 ``reference`` 为基准，列出其它语言缺哪些键。

    框架升级新增了文案、却忘了补另外两种语言时，这里会直接暴露出来 ——
    比"某个弹窗上出现一行英文键名"要早得多。
    """
    base = MESSAGES.get(reference, {})
    base_keys = set(base)
    return {
        code: sorted(base_keys - set(messages))
        for code, messages in MESSAGES.items()
        if code != reference
    }
