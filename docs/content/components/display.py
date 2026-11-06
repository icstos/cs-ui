"""数据展示：列表项、代码编辑器、代码视图、树、描述列表、数值动画、热力图。"""

from __future__ import annotations

import datetime as dt

import flet as ft
import flet_code_editor as fce

from docs import kit
from docs.blocks import Doc, demo, h2, note, p, ul
from docs.content.components._shared import panel
from ui import (
    Button,
    Calendar,
    Carousel,
    CodeEditor,
    CodeView,
    Column,
    Descriptions,
    DescriptionsItem,
    Heatmap,
    HeatmapItem,
    ListTile,
    NumberAnimation,
    Text,
    Tree,
    TreeNode,
    format_date,
    use_t,
)

_EDITOR_CODE = '''def greet(name: str) -> str:
    """一个可以就地编辑的代码块。"""
    return f"Hello, {name}!"


print(greet("cs-ui"))'''

_VIEW_CODE = """from ui import CodeView, Container, Text

CodeView(
    component=Container(Text("上面的实时组件")),
    code="Container(Text('上面的实时组件'))",
)"""

_SAMPLE = '''class LRUCache[K, V]:
    """带容量上限的最近最少使用缓存。"""

    def __init__(self, capacity: int) -> None:
        self._capacity = capacity
        self._data: dict[K, V] = {}

    def get(self, key: K) -> V | None:
        if key not in self._data:
            return None
        self._data[key] = self._data.pop(key)   # 命中后移到队尾
        return self._data[key]
'''


@ft.component
def _list_tiles() -> ft.Control:
    tr = use_t()
    people = (
        ("Shawn Chen", "shawn@cstos.com", ft.Colors.PRIMARY, "SC"),
        ("Avery Lin", "avery@example.com", ft.Colors.TERTIARY, "AL"),
        ("Riley Wu", "riley@example.com", ft.Colors.SECONDARY, "RW"),
    )
    return panel(
        *[
            ListTile(
                leading=ft.CircleAvatar(
                    content=ft.Text(initials, size=12, weight=ft.FontWeight.W_700),
                    bgcolor=ft.Colors.with_opacity(0.18, color),
                    color=color,
                    radius=18,
                ),
                title=Text(name, size=13.5, weight=ft.FontWeight.W_600),
                subtitle=Text(email, size=11.5, color=kit.MUTED),
                trailing=ft.IconButton(
                    icon=ft.Icons.MORE_HORIZ,
                    icon_size=17,
                    icon_color=kit.MUTED,
                    tooltip=tr("cat.display.tile.more"),
                ),
            )
            for name, email, color, initials in people
        ],
    )


@ft.component
def _editor() -> ft.Control:
    return ft.Container(
        border_radius=10,
        border=ft.Border.all(1, kit.BORDER),
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        content=CodeEditor(
            value=_EDITOR_CODE,
            language=fce.CodeLanguage.PYTHON,
            code_theme=fce.CodeTheme.ATOM_ONE_LIGHT,
            height=190,
            padding=10,
        ),
    )


@ft.component
def _code_view() -> ft.Control:
    tr = use_t()
    return CodeView(
        component=kit.surface(
            padding=16,
            content=Column(
                spacing=6,
                controls=[
                    Text(tr("cat.display.view.preview"), size=13),
                    Text(tr("cat.display.view.hint"), size=11.5, color=kit.MUTED),
                ],
            ),
        ),
        code=_VIEW_CODE,
    )


_TREE_CODE = """tree = Tree(
    data=[
        TreeNode("src", icon=ft.Icons.FOLDER_OPEN, trailing="6", children=[
            TreeNode("ui", children=[TreeNode("tree.py"), TreeNode("layout.py")]),
            TreeNode("app.py"),
        ]),
        TreeNode("README.md", icon=ft.Icons.ARTICLE),
    ],
    show_checkbox=True,   # 父子联动，半选自动推导
    show_lines=True,      # 层级引导线
    height=252,           # 给高度 => 内部滚动 + 按需构建行
)

tree.filter("py")                     # 只留命中节点和它的祖先，命中处高亮
tree.get_checked_keys(leaf_only=True) # 提交时通常只要叶子
tree.set_checked_keys(["0/ui"])       # 代码里改勾选，自动向下级联
"""

_TREE_DATA = [
    TreeNode(
        "src",
        icon=ft.Icons.FOLDER_OPEN,
        trailing="6",
        children=[
            TreeNode(
                "ui",
                icon=ft.Icons.FOLDER,
                children=[
                    TreeNode("tree.py", icon=ft.Icons.DESCRIPTION),
                    TreeNode("input.py", icon=ft.Icons.DESCRIPTION),
                    TreeNode("layout.py", icon=ft.Icons.DESCRIPTION),
                ],
            ),
            TreeNode("app.py", icon=ft.Icons.DESCRIPTION),
            TreeNode("main.py", icon=ft.Icons.DESCRIPTION),
        ],
    ),
    TreeNode(
        "docs",
        icon=ft.Icons.FOLDER,
        children=[
            TreeNode("index.md", icon=ft.Icons.ARTICLE),
            TreeNode("guide.md", icon=ft.Icons.ARTICLE),
        ],
    ),
    TreeNode("README.md", icon=ft.Icons.ARTICLE),
]


@ft.component
def _tree() -> ft.Control:
    tr = use_t()
    # 实例要跨渲染稳定，否则每次重绘都会丢掉展开 / 勾选状态
    tree = kit.use_stable(
        lambda: Tree(
            data=_TREE_DATA,
            show_checkbox=True,
            show_lines=True,
            height=252,
            expanded={"0"},
        )
    )
    search = ft.Container(
        width=240,
        height=34,
        padding=ft.Padding.symmetric(horizontal=8),
        bgcolor=ft.Colors.SURFACE,
        border=ft.Border.all(1, kit.BORDER),
        border_radius=8,
        content=ft.TextField(
            hint_text=tr("demo.tree.search"),
            border=ft.InputBorder.NONE,
            dense=True,
            text_size=13,
            prefix_icon=ft.Icons.SEARCH,
            content_padding=ft.Padding.symmetric(vertical=6),
            on_change=lambda e: tree.filter(e.control.value),
        ),
    )
    return panel(search, tree.ui(), padding=12)


_DESCRIPTIONS_CODE = """Descriptions(
    title="用户信息",
    column=3,
    extra=Button("编辑"),
    items=[
        DescriptionsItem("用户名", "kooriookami", icon=ft.Icons.PERSON_OUTLINE),
        DescriptionsItem("手机号", "18100000000"),
        DescriptionsItem("居住地", "苏州市"),
        DescriptionsItem("备注", badge("学校")),
        DescriptionsItem("联系地址", "江苏省苏州市吴中区吴中大道 1188 号", span=2),
    ],
)"""


def _badge(text: str) -> ft.Control:
    """状态徽标：走主题色，明暗主题都读得清。"""
    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=8, vertical=2),
        bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.PRIMARY),
        border_radius=4,
        content=ft.Text(text, size=11.5, color=ft.Colors.PRIMARY),
    )


@ft.component
def _descriptions() -> ft.Control:
    tr = use_t()
    user = [
        DescriptionsItem(
            tr("cat.display.desc.name"), "kooriookami", icon=ft.Icons.PERSON_OUTLINE
        ),
        DescriptionsItem(tr("cat.display.desc.phone"), "18100000000"),
        DescriptionsItem(
            tr("cat.display.desc.city"), tr("cat.display.desc.city_value")
        ),
        DescriptionsItem(
            tr("cat.display.desc.note"), _badge(tr("cat.display.desc.school"))
        ),
        DescriptionsItem(
            tr("cat.display.desc.address"),
            tr("cat.display.desc.address_value"),
            span=2,
        ),
    ]
    order = [
        DescriptionsItem(tr("cat.display.desc.order_no"), "SO-2026-1104-0087"),
        DescriptionsItem(
            tr("cat.display.desc.customer"), tr("cat.display.desc.customer_value")
        ),
        DescriptionsItem(tr("cat.display.desc.placed_at"), "2026-11-04 09:12"),
        DescriptionsItem(tr("cat.display.desc.amount"), "¥ 12,480.00"),
        DescriptionsItem(
            tr("cat.display.desc.state"), _badge(tr("cat.display.desc.state_value"))
        ),
        DescriptionsItem(
            tr("cat.display.desc.ship_to"),
            tr("cat.display.desc.ship_to_value"),
            span=2,
        ),
    ]
    return Column(
        spacing=22,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        controls=[
            Descriptions(
                title=tr("cat.display.desc.h1"),
                extra=Button(tr("cat.display.desc.edit")),
                items=user,
                column=3,
            ),
            Descriptions(
                title=tr("cat.display.desc.h2"),
                items=user[:3],
                column=3,
                direction="vertical",
            ),
            Descriptions(
                title=tr("cat.display.desc.h3"),
                items=order,
                column=2,
                bordered=False,
                size="small",
            ),
        ],
    )


_NUMBER_CODE = """NumberAnimation(
    end=1_286_400,
    duration=1100,        # 0 表示不要动画，直接落位
    precision=0,          # 保留几位小数
    separator=None,       # None 跟随语言；给字符串就照办，"" 关闭分组
    prefix="¥",           # 后缀用 suffix="%"
    easing="ease-out",    # linear / ease-in-out / 自定义 f(0~1)
    size=30,
    weight="semibold",    # 改 end 会从当前值接着滚，不从头重播
)"""


def _number_card(
    label: str, number: ft.Control, note: str, anim: NumberAnimation
) -> ft.Control:
    """一张 KPI 卡：点一下就把这串数字重播一遍。"""
    return ft.Container(
        width=190,
        padding=ft.Padding.symmetric(horizontal=16, vertical=14),
        border_radius=14,
        bgcolor=kit.SURFACE,
        border=ft.Border.all(1, kit.BORDER),
        ink=True,
        on_click=lambda _e: anim.play(),
        content=ft.Column(
            spacing=6,
            controls=[
                ft.Text(label, size=12, color=kit.MUTED),
                number,
                ft.Text(note, size=11, color=ft.Colors.OUTLINE),
            ],
        ),
    )


@ft.component
def _numbers() -> ft.Control:
    tr = use_t()
    amount = kit.use_stable(
        lambda: NumberAnimation(
            end=1_286_400,
            duration=1100,
            prefix="¥",
            size=30,
            weight=ft.FontWeight.W_600,
        )
    )
    rate = kit.use_stable(
        lambda: NumberAnimation(
            end=12.4,
            precision=1,
            suffix="%",
            separator="",
            duration=1300,
            size=30,
            weight=ft.FontWeight.W_600,
            color=ft.Colors.TERTIARY,
        )
    )
    online = kit.use_stable(
        lambda: NumberAnimation(
            end=8642,
            duration=900,
            easing="ease-in-out",
            size=30,
            weight=ft.FontWeight.W_600,
        )
    )
    return Column(
        spacing=12,
        horizontal_alignment=ft.CrossAxisAlignment.START,
        controls=[
            ft.Row(
                spacing=14,
                wrap=True,
                run_spacing=14,
                controls=[
                    _number_card(
                        tr("cat.display.num.amount"),
                        amount.ui(),
                        tr("cat.display.num.amount_note"),
                        amount,
                    ),
                    _number_card(
                        tr("cat.display.num.rate"),
                        rate.ui(),
                        tr("cat.display.num.rate_note"),
                        rate,
                    ),
                    _number_card(
                        tr("cat.display.num.online"),
                        online.ui(),
                        tr("cat.display.num.online_note"),
                        online,
                    ),
                ],
            ),
            Text(tr("cat.display.num.replay"), size=12, color=kit.MUTED),
        ],
    )


_HEATMAP_CODE = """Heatmap(
    data=[
        HeatmapItem(date(2026, 9, 26), 12),
        {"date": date(2026, 9, 27), "value": 3},
        (date(2026, 9, 28), 0),
    ],
    color_theme="green",   # 或显式给 active_colors=[...]
    size="medium",         # small / medium / large
    tooltip=True,          # 悬停气泡
    footer=my_stats_bar,   # 左下角自定义区域
)"""


def _heat_data() -> list[HeatmapItem]:
    """一年确定性的样例数据：工作日多、周末少、偶尔有高峰。

    不用随机数 —— 文档截图要每次跑出来都一模一样，否则回归时没法比对。
    """
    start = dt.date(2026, 1, 1)
    out: list[HeatmapItem] = []
    for i in range(365):
        day = start + dt.timedelta(days=i)
        seed = (day.toordinal() * 2654435761) % 97
        weekend = day.weekday() >= 5
        if (weekend and seed % 3) or seed < 9:
            out.append(HeatmapItem(day, 0))
        else:
            out.append(HeatmapItem(day, seed % 14 + (12 if seed % 23 == 0 else 0)))
    return out


@ft.component
def _heatmap() -> ft.Control:
    tr = use_t()
    data = _heat_data()

    def stats_text(hm: Heatmap) -> ft.Control:
        s = hm.stats()
        return ft.Text(
            tr(
                "cat.display.heat.stats",
                days=int(s["days"]),
                filled=int(s["filled"]),
                peak=int(s["peak"]),
                mean=f"{s['mean']:.1f}",
            ),
            size=11.5,
            color=kit.MUTED,
        )

    def build_main() -> Heatmap:
        # footer 在**构造期**赋值：此刻实例还没有订阅者，不会惊动重绘。
        # 若在渲染体里给已挂载实例的字段赋值，observable 会 notify → 重绘 →
        # 再赋值 → 无限循环（这里踩过一次）。
        hm = Heatmap(data=data, color_theme="green")
        hm.footer = stats_text(hm)
        return hm

    main = kit.use_stable(build_main)
    small = kit.use_stable(
        lambda: Heatmap(data=data, color_theme="blue", size="small", show_legend=False)
    )
    return Column(
        spacing=18,
        horizontal_alignment=ft.CrossAxisAlignment.START,
        controls=[
            main.ui(),
            Text(tr("cat.display.heat.sub"), size=12, color=kit.MUTED),
            small.ui(),
        ],
    )


_CALENDAR_CODE = """Calendar(
    value=date.today(),
    cell_height=68,           # 格子里要放内容就调高
    cell_content=marks,       # 每天返回一个控件，画在日期下方
    first_day_of_week=None,   # 跟随语言：中文周一、英文周日
    on_select=lambda day: print("选中", day),
)"""


def _cal_marks(day: dt.date) -> ft.Control | None:
    """确定性的"这天有几个日程"：文档截图每次都要一样，所以按日期算而非随机。"""
    seed = (day.toordinal() * 2654435761) % 89
    if seed % 3:
        return None
    return ft.Row(
        spacing=3,
        tight=True,
        controls=[
            ft.Container(width=5, height=5, border_radius=99, bgcolor=ft.Colors.PRIMARY)
            for _ in range(seed % 3 + 1)
        ],
    )


@ft.component
def _calendar() -> ft.Control:
    tr = use_t()
    # on_select 必须在**构造期**定下来，而 use_state 的 setter 要等渲染时才有，
    # 所以用一只可变盒子转手：lambda 到点击那一刻才读盒子里最新的函数。
    # （反过来，渲染期给已挂载实例的字段赋值 = 无限重绘，Heatmap 那节踩过。）
    hook: list = [None]
    cal = kit.use_stable(
        lambda: Calendar(
            # 本地时区的今天（`date.today()` 过不了 ruff 的 DTZ011，UTC 的今天
            # 在东八区凌晨会差一天 —— 日历高亮的必须是用户眼前这一天）
            value=dt.datetime.now(tz=dt.UTC).astimezone().date(),
            cell_height=68,
            cell_content=_cal_marks,
            on_select=lambda day: hook[0] and hook[0](day),
        )
    )
    picked, set_picked = ft.use_state(cal.selected)
    hook[0] = set_picked
    return Column(
        spacing=14,
        horizontal_alignment=ft.CrossAxisAlignment.START,
        controls=[
            cal.ui(),
            Text(
                tr(
                    "cat.display.cal.selected",
                    date=format_date(picked) if picked else "—",
                ),
                size=12,
                color=kit.MUTED,
            ),
        ],
    )


_CAROUSEL_CODE = """Carousel(
    slides=[
        Container(expand=True, gradient=..., content=Text("1")),  # 每张自己撑满
        Container(expand=True, gradient=..., content=Text("2")),
        Container(expand=True, gradient=..., content=Text("3")),
    ],
    height=230,            # 宽度不用给：挂载后自己量，跟着父容器变
    autoplay=True,         # 自动播放
    autoplay_speed=4500,   # 指针停上来就暂停，读完再走
    loop=True,
    on_change=lambda old, new: print(old, "->", new),
)"""

#: 每张的渐变：三色一组，深浅错开，缩略图里也一眼能分辨
_CAR_PALETTE: tuple[tuple[str, str], ...] = (
    ("#1F6FEB", "#4F46E5"),
    ("#0D9488", "#16A34A"),
    ("#EA580C", "#DC2626"),
)


def _car_slide(i: int) -> ft.Control:
    start, end = _CAR_PALETTE[i % len(_CAR_PALETTE)]
    return ft.Container(
        expand=True,
        alignment=ft.Alignment.CENTER,
        gradient=ft.LinearGradient(
            begin=ft.Alignment.TOP_LEFT,
            end=ft.Alignment.BOTTOM_RIGHT,
            colors=[start, end],
        ),
        content=ft.Text(
            str(i + 1), size=48, color=ft.Colors.WHITE, weight=ft.FontWeight.W_500
        ),
    )


@ft.component
def _carousel() -> ft.Control:
    tr = use_t()
    # 同日历那节：on_change 要在构造期定下来，用可变盒子转手到 set_state。
    # 直接给已挂载的实例赋字段 = notify → 重绘 → 再赋值，会转不停。
    hook: list = [None]
    box = kit.use_stable(
        lambda: Carousel(
            slides=[_car_slide(i) for i in range(len(_CAR_PALETTE))],
            height=230,
            autoplay=True,
            autoplay_speed=4500,
            loop=True,
            on_change=lambda old, new: hook[0] and hook[0](new),
        )
    )
    cur, set_cur = ft.use_state(box.current)
    hook[0] = set_cur
    return Column(
        spacing=14,
        horizontal_alignment=ft.CrossAxisAlignment.START,
        controls=[
            box.ui(),
            Text(
                tr(
                    "cat.display.carousel.current",
                    n=cur + 1,
                    total=len(_CAR_PALETTE),
                ),
                size=12,
                color=kit.MUTED,
            ),
        ],
    )


DISPLAY: Doc = (
    p("cat.display.intro"),
    h2("cat.display.tile.title"),
    demo(_list_tiles, hint_key="cat.display.tile.hint", padded=False),
    h2("cat.display.editor.title"),
    demo(_editor, hint_key="cat.display.editor.hint", padded=False),
    h2("cat.display.view.title"),
    demo(_code_view, hint_key="cat.display.view.hint", code=_SAMPLE),
    h2("cat.display.tree.title"),
    demo(_tree, hint_key="cat.display.tree.hint", code=_TREE_CODE, padded=False),
    h2("cat.display.desc.title"),
    demo(_descriptions, hint_key="cat.display.desc.hint", code=_DESCRIPTIONS_CODE),
    h2("cat.display.num.title"),
    demo(_numbers, hint_key="cat.display.num.hint", code=_NUMBER_CODE),
    h2("cat.display.heat.title"),
    demo(_heatmap, hint_key="cat.display.heat.hint", code=_HEATMAP_CODE, padded=False),
    h2("cat.display.cal.title"),
    demo(_calendar, hint_key="cat.display.cal.hint", code=_CALENDAR_CODE),
    h2("cat.display.carousel.title"),
    demo(_carousel, hint_key="cat.display.carousel.hint", code=_CAROUSEL_CODE),
    ul("cat.display.note1", "cat.display.note2", "cat.display.note3"),
    note("cat.display.tip", "cat.display.tip_title"),
)
