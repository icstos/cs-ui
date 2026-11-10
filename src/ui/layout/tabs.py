"""标签页 (Tabs) —— TabBar 管标签，TabBarView 管内容。

flet 1.1 把「标签」和「内容」拆成了两个控件，``Tabs`` 只负责把它们绑在同一个
选中索引上：``content`` 里放一个 Column，上面 TabBar、下面 TabBarView，两边按
**下标**对齐，条数由 ``length`` 给出。本模块保留同名的轻包装，只做两件事：

- ``Tab(text=...)`` 少写一个 ``label=``；
- ``TabBar`` 的选中色 / 未选中色 / 指示条默认取主题角色（``PRIMARY`` /
  ``ON_SURFACE_VARIANT``），换主色、切明暗都自动跟随。

用法::

    Tabs(
        length=2,
        content=Column([
            TabBar(tabs=[Tab(text="概览"), Tab(text="明细")]),
            TabBarView(height=160, controls=[overview, detail]),
        ]),
    )

.. note::
    内容不挂在 ``Tab`` 上 —— Material 的 Tab 只是一个标签。``Tab.content`` 只为
    旧代码保留、不会渲染；内容请放进 ``TabBarView.controls``，与标签按下标一一对应。
"""

from __future__ import annotations

import flet as ft

from ui.core.doc import Api, Example, Spec, info, run, warn
from ui.core.tokens import FONT_SIZE, RADIUS, accent_soft

__all__ = ["Tab", "TabBar", "TabBarView", "Tabs"]


# ---------------------------------------------------------------------------
# 控件
# ---------------------------------------------------------------------------
@ft.control
class Tabs(ft.Tabs):
    """标签页容器：把 TabBar 与 TabBarView 绑到同一个选中索引上。"""


@ft.control
class TabBar(ft.TabBar):
    """标签栏。配色默认走主题角色，不再写死蓝色 / 灰色。"""

    label_color: ft.ColorValue | None = ft.Colors.PRIMARY
    unselected_label_color: ft.ColorValue | None = ft.Colors.ON_SURFACE_VARIANT
    indicator_color: ft.ColorValue | None = ft.Colors.PRIMARY


@ft.control
class Tab(ft.Tab):
    """一个标签。``text`` 是 ``label`` 的简写；内容不放在这里。"""

    text: str | ft.Control = ""

    def init(self):
        self.label = self.label or self.text


@ft.control
class TabBarView(ft.TabBarView):
    """标签内容区。不给高度时兜底 1000，卡片里请显式传具体值。"""

    def init(self):
        self.height = self.height or 1000


# ---------------------------------------------------------------------------
# 示例（也是本组件的视觉验收页）
# ---------------------------------------------------------------------------
_MUTED = ft.Colors.ON_SURFACE_VARIANT


def _panel(text: str) -> ft.Control:
    return ft.Container(
        padding=15,
        content=ft.Text(text, size=FONT_SIZE["body"], color=_MUTED),
    )


def _badge(count: int) -> ft.Control:
    """标签里的计数：淡主色底 + 主色字，不抢指示条的位置。"""
    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=6, vertical=1),
        border_radius=RADIUS["full"],
        bgcolor=accent_soft("primary"),
        content=ft.Text(
            str(count),
            size=FONT_SIZE["caption"],
            weight=ft.FontWeight.W_600,
            color=ft.Colors.PRIMARY,
        ),
    )


_TABS = ("概览", "明细", "设置")


@ft.component
def _basic() -> ft.Control:
    """三个页签切换内容，当前页签回显在下面。"""
    index, set_index = ft.use_state(0)
    return ft.Column(
        spacing=12,
        controls=[
            Tabs(
                length=len(_TABS),
                selected_index=index,
                on_change=lambda e: set_index(int(e.data)),
                content=ft.Column(
                    spacing=0,
                    controls=[
                        TabBar(tabs=[Tab(text=name) for name in _TABS]),
                        TabBarView(
                            height=120,
                            controls=[
                                _panel("概览：关键指标与最近 7 天的趋势。"),
                                _panel("明细：列多的表在这里横向滚动。"),
                                _panel("设置：低频选项收进折叠面板。"),
                            ],
                        ),
                    ],
                ),
            ),
            ft.Text(
                f"当前页签：{_TABS[index]}（selected_index = {index}）",
                size=FONT_SIZE["small"],
                color=_MUTED,
            ),
        ],
    )


@ft.component
def _iconic() -> ft.Control:
    """图标、计数徽标，以及一个禁用的页签。"""
    index, set_index = ft.use_state(0)
    return ft.Column(
        spacing=12,
        controls=[
            Tabs(
                length=4,
                selected_index=index,
                on_change=lambda e: set_index(int(e.data)),
                content=ft.Column(
                    spacing=0,
                    controls=[
                        TabBar(
                            tabs=[
                                Tab(text="概览", icon=ft.Icons.DASHBOARD_OUTLINED),
                                Tab(text="待办", icon=ft.Icons.INBOX_OUTLINED),
                                Tab(
                                    label=ft.Row(
                                        spacing=6,
                                        tight=True,
                                        controls=[
                                            ft.Text("告警"),
                                            _badge(3),
                                        ],
                                    )
                                ),
                                Tab(
                                    text="归档",
                                    icon=ft.Icons.ARCHIVE_OUTLINED,
                                    disabled=True,
                                ),
                            ]
                        ),
                        TabBarView(
                            height=100,
                            controls=[
                                _panel("图标放在标签上方，文字仍在指示条中间。"),
                                _panel("待办：5 条待处理。"),
                                _panel("告警：3 条未读，徽标跟着标签一起走。"),
                                _panel("归档页签被禁用，点不到。"),
                            ],
                        ),
                    ],
                ),
            ),
            ft.Text(
                "「归档」是 disabled 的页签：指示条不会停在它上面。",
                size=FONT_SIZE["small"],
                color=_MUTED,
            ),
        ],
    )


_MANY = tuple(f"分区 {i}" for i in range(1, 11))


@ft.component
def _many() -> ft.Control:
    """10 个页签、容器只有 420px：标签栏自己横向滚动。"""
    return ft.Column(
        spacing=10,
        controls=[
            ft.Container(
                width=420,
                content=Tabs(
                    length=len(_MANY),
                    content=ft.Column(
                        spacing=0,
                        controls=[
                            TabBar(
                                scrollable=True,
                                tabs=[Tab(text=name) for name in _MANY],
                            ),
                            TabBarView(
                                height=90,
                                controls=[_panel(f"{name} 的内容") for name in _MANY],
                            ),
                        ],
                    ),
                ),
            ),
            ft.Text(
                "页签不会被压扁或溢出，宽度不够时标签栏横向滚动。",
                size=FONT_SIZE["small"],
                color=_MUTED,
            ),
        ],
    )


_BASIC_CODE = """@ft.component
def Demo():
    index, set_index = ft.use_state(0)
    return Tabs(
        length=3,
        selected_index=index,
        on_change=lambda e: set_index(int(e.data)),
        content=ft.Column([
            TabBar(tabs=[Tab(text="概览"), Tab(text="明细"), Tab(text="设置")]),
            TabBarView(height=160, controls=[overview, detail, settings]),
        ]),
    )"""

_ICON_CODE = """TabBar(tabs=[
    Tab(text="待办", icon=ft.Icons.INBOX_OUTLINED),
    Tab(label=ft.Row([ft.Text("告警"), badge(3)], spacing=6, tight=True)),
    Tab(text="归档", disabled=True),
])"""

SPEC = Spec(
    name="Tabs",
    summary="同一块区域里并列几组内容，一次只看一组。",
    definition=(
        "页签把几组平级的内容叠在同一处，用一排标签决定看哪一组。它不换路由、不重取数据，"
        "所以适合「同一份对象的几个视角」：概览与明细、设置与日志。flet 1.1 把标签栏与"
        "内容区拆成两个控件，Tabs 只负责把两者的选中下标绑在一起 —— 标签和内容按下标对齐。"
    ),
    anatomy=[
        (
            "标签栏",
            "TabBar。标签一多就横向滚动，不压扁也不换行；选中项下方一条 2px 指示条。",
        ),
        ("标签", "文字、图标（图标在上）或任意控件；计数徽标塞进 label 里跟着走。"),
        (
            "内容区",
            (
                "TabBarView，按标签下标取 controls 里对应的那一项；高度要显式给"
                "（默认兜底 1000，只适合整页）。"
            ),
        ),
        (
            "选中态",
            "选中标签与指示条用主色，未选中的标签用次要文字色；两者都随主题与主色自动解析。",
        ),
        (
            "联动",
            "Tabs 持有 selected_index 并与 TabBar 同步；on_change 把新下标交回调用方。",
        ),
    ],
    when=[
        "同一个对象的几个视角：概览 / 明细 / 设置",
        "详情页里的分组信息，切走再切回不该重新加载",
        "需要在有限高度里换内容，而页面路由保持不变",
    ],
    avoid=[
        "有先后顺序的流程：用 Step，页签会让人以为顺序可以随便跳",
        "内容其实属于不同页面、各带各的数据与标题：用导航，页签会误导成同一份数据",
        "页签多到要滚两屏：改成下拉或二级导航，横向滚动只是兜底不是方案",
    ],
    examples=[
        Example(
            "基础用法",
            _basic,
            hint="三个页签切换内容，下方回显 selected_index —— 选中态是受控的。",
            code=_BASIC_CODE,
        ),
        Example(
            "图标、徽标与禁用",
            _iconic,
            hint="图标标签、label 里塞计数徽标，以及一条点不动的 disabled 页签。",
            code=_ICON_CODE,
        ),
        Example(
            "页签很多",
            _many,
            hint="10 个页签挤在 420px 里：标签栏自己横向滚动，页签宽度不被压缩。",
        ),
    ],
    api=[
        Api(
            "content",
            "ft.Control",
            "",
            "Tabs：容器内容，放一个 Column（TabBar + TabBarView）",
        ),
        Api("length", "int", "", "Tabs：页签数量，必须与 TabBar.tabs 的条数一致"),
        Api("selected_index", "int", "0", "Tabs：当前选中的下标；受控时由状态回写"),
        Api(
            "on_change",
            "Callable[[Event], None] | None",
            "None",
            "Tabs：切换回调，e.data 是新的下标",
        ),
        Api("tabs", "list[Tab]", "", "TabBar：标签列表"),
        Api("scrollable", "bool", "True", "TabBar：超宽时横向滚动而不是把标签压扁"),
        Api(
            "label_color", "ft.ColorValue | None", "PRIMARY", "TabBar：选中标签的文字色"
        ),
        Api(
            "unselected_label_color",
            "ft.ColorValue | None",
            "ON_SURFACE_VARIANT",
            "TabBar：未选中标签的文字色",
        ),
        Api(
            "indicator_color",
            "ft.ColorValue | None",
            "PRIMARY",
            "TabBar：选中指示条的颜色",
        ),
        Api(
            "height", "int | None", "1000", "TabBarView：内容区高度，卡片里请显式给小值"
        ),
    ],
    notes=[
        warn(
            "TabBarView 的高度必须给。默认的 1000 只是兜底，它不会自己撑开也不会收缩，"
            "卡片里请按内容传 120 / 200 这类具体值，否则会把整页撑高。"
        ),
        warn(
            "内容不在 Tab 上：Tab.content 只是为旧代码留着，flet 1.1 不会渲染它。"
            "内容放 TabBarView.controls，与标签按下标对齐。"
        ),
        info(
            "配色从 Tabs 挪到了 TabBar：flet 1.1 的 Tabs 只是 TabController，"
            "没有 label_color 这类属性，挂在它上面的同名参数不会传到 Flutter。"
            "现在默认值走 PRIMARY / ON_SURFACE_VARIANT，明暗与主色自动跟随。"
        ),
    ],
    tags=("标签页", "页签", "选项卡", "tabs", "tab bar"),
)


if __name__ == "__main__":
    run(SPEC)
