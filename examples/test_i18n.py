"""CS UI 多语言 (i18n) 示例 —— 顶栏切语言，界面即时跟随。

演示四件事：

1. **只注册文案就行**：``zh-CN`` / ``zh-TW`` / ``en-US`` 三种语言框架已内置，
   应用侧只要 ``register_messages``。要加第四种语言，一行 ``register_language``
   加一份表（或一个 ``fr.json``，见 :func:`ui.core.i18n.load_catalogs`）。
2. **组件内用 ``use_t()``**：切语言时这些组件自动重绘，不需要手动 update。
3. **切换不丢状态**：下面输入框里打几个字再切语言 —— 内容还在
   （``I18nProvider`` 用 ``use_memo`` 复用了控件树，只让订阅者重绘）。
4. **复数与插值**：拖动滑块看 ``{n} 个文件 / {n} files``。

用法::

    python examples/test_i18n.py
"""

import os
import sys
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_root, "src"))
sys.path.insert(0, _root)

import flet as ft

from ui import I18nProvider, LanguageSwitcher, register_messages, t, use_i18n, use_t
from ui.core.i18n import MemoryStore
from ui.core.tokens import FONT_SIZE, RADIUS, SPACE

# ---------------------------------------------------------------------------
# 文案：键用点号分层，装表时可嵌套写法；缺翻译自动回退（繁 → 简 → 英）
# ---------------------------------------------------------------------------
MESSAGES: dict[str, dict[str, object]] = {
    "zh-CN": {
        "app": {"title": "CS UI · 多语言"},
        "hero": {
            "title": "界面语言，随时切换",
            "body": "所有文案都走键值表。切换语言只重绘用到翻译的组件，"
            "你在下面输入的内容不会被清空。",
        },
        "form": {
            "name": "姓名",
            "hint": "随便输点什么，切换语言后它还在",
            "subscribe": "接收更新通知",
        },
        "stats": {
            "label": "文件数量",
            "files": {"one": "{n} 个文件", "other": "{n} 个文件"},
        },
        "note": {
            "persist": "语言选择会写入本地配置，下次启动沿用；没选过则跟随系统语言。"
            "（本示例用内存存储，正式使用去掉 store 参数即可落盘。）",
            "api": "组件里用 use_t()，组件外用 t()。",
        },
    },
    "zh-TW": {
        "app": {"title": "CS UI · 多語言"},
        "hero": {
            "title": "介面語言，隨時切換",
            "body": "所有文案都走鍵值表。切換語言只重繪用到翻譯的元件，"
            "你在下面輸入的內容不會被清空。",
        },
        "form": {
            "name": "姓名",
            "hint": "隨便輸入點什麼，切換語言後它還在",
            "subscribe": "接收更新通知",
        },
        "stats": {
            "label": "檔案數量",
            "files": {"one": "{n} 個檔案", "other": "{n} 個檔案"},
        },
        "note": {
            "persist": "語言選擇會寫入本機設定，下次啟動沿用；沒選過則跟隨系統語言。"
            "（本範例用記憶體儲存，正式使用去掉 store 參數即可寫入磁碟。）",
            "api": "元件裡用 use_t()，元件外用 t()。",
        },
    },
    "en-US": {
        "app": {"title": "CS UI · i18n"},
        "hero": {
            "title": "Switch language at any time",
            "body": "Every label comes from the message table. Switching only re-renders "
            "the components that use translations — whatever you typed below stays put.",
        },
        "form": {
            "name": "Name",
            "hint": "Type something; it survives the switch",
            "subscribe": "Receive update notifications",
        },
        "stats": {
            "label": "Files",
            "files": {"one": "{n} file", "other": "{n} files"},
        },
        "note": {
            "persist": "Your choice is saved to a local config file and reused next launch; "
            "if you never chose, the system language wins. "
            "(This demo uses in-memory storage — drop the store argument to persist.)",
            "api": "use_t() inside components, t() outside.",
        },
    },
}

for _code, _messages in MESSAGES.items():
    register_messages(_code, _messages)


def top_bar() -> ft.Control:
    """顶栏：标题在左，语言菜单在右（桌面端惯用位置）。"""
    return ft.Container(
        height=56,
        bgcolor=ft.Colors.SURFACE,
        padding=ft.Padding.symmetric(horizontal=SPACE["4"]),
        border=ft.Border.only(bottom=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
        content=ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(
                    t("app.title"), size=FONT_SIZE["title"], weight=ft.FontWeight.W_600
                ),
                ft.Container(expand=True),
                LanguageSwitcher(),
            ],
        ),
    )


@ft.component
def DemoPage() -> ft.Control:
    tr = use_t()
    state = use_i18n()
    count, set_count = ft.use_state(3)
    name, set_name = ft.use_state("")

    card = ft.Container(
        bgcolor=ft.Colors.SURFACE,
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        border_radius=RADIUS["lg"],
        padding=SPACE["6"],
        content=ft.Column(
            spacing=SPACE["4"],
            controls=[
                ft.Text(
                    tr("hero.title"),
                    size=FONT_SIZE["headline"],
                    weight=ft.FontWeight.W_600,
                ),
                ft.Text(
                    tr("hero.body"),
                    size=FONT_SIZE["body"],
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
                ft.Divider(height=1),
                ft.TextField(
                    label=tr("form.name"),
                    hint_text=tr("form.hint"),
                    value=name,
                    width=340,
                    on_change=lambda e: set_name(e.control.value),
                ),
                ft.Switch(label=tr("form.subscribe"), value=True),
                ft.Row(
                    spacing=SPACE["3"],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text(tr("stats.label"), size=FONT_SIZE["body"]),
                        ft.Slider(
                            value=count,
                            min=0,
                            max=20,
                            divisions=20,
                            width=220,
                            on_change=lambda e: set_count(int(float(e.control.value))),
                        ),
                        ft.Text(
                            tr.n("stats.files", count),
                            size=FONT_SIZE["body"],
                            weight=ft.FontWeight.W_500,
                            color=ft.Colors.PRIMARY,
                        ),
                    ],
                ),
                ft.Divider(height=1),
                ft.Text(
                    tr("note.persist"),
                    size=FONT_SIZE["small"],
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
                ft.Row(
                    spacing=SPACE["2"],
                    controls=[
                        ft.Icon(
                            ft.Icons.TRANSLATE,
                            size=FONT_SIZE["subtitle"],
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        ft.Text(
                            tr("note.api"),
                            size=FONT_SIZE["small"],
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        ft.Container(
                            padding=ft.Padding.symmetric(
                                horizontal=SPACE["2"], vertical=2
                            ),
                            border_radius=RADIUS["sm"],
                            bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.ON_SURFACE),
                            content=ft.Text(
                                f"{state.language.native_name} · {state.locale}",
                                size=FONT_SIZE["caption"],
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                        ),
                    ],
                ),
            ],
        ),
    )

    return ft.Container(
        expand=True,
        bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
        content=ft.Column(
            spacing=0,
            controls=[
                top_bar(),
                ft.Container(
                    expand=True,
                    padding=SPACE["6"],
                    # 内容列定宽 720 并居中：滚动容器里的 Column 沿交叉轴是松约束，
                    # horizontal_alignment 只会相对自身内容宽度对齐（看起来还是靠左），
                    # 所以居中交给外层的 Container(alignment=...)。
                    alignment=ft.Alignment(0, -1),
                    content=ft.Container(
                        width=720,
                        content=ft.Column(
                            scroll=ft.ScrollMode.AUTO,
                            spacing=SPACE["4"],
                            controls=[card],
                        ),
                    ),
                ),
            ],
        ),
    )


@ft.component
def App() -> ft.Control:
    # locale 只是"没存过选择时的默认值"；用户切过就以持久化选择为准。
    return I18nProvider(build=DemoPage, locale="zh-CN", store=MemoryStore())


def main(page: ft.Page) -> None:
    page.title = "CS UI · i18n"
    page.window.width = 900
    page.window.height = 640
    page.render(App)


if __name__ == "__main__":
    ft.run(main)
