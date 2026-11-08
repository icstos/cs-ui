"""搜索框 (SearchBar) —— 关键字、建议列表与回车提交。

基于 Flutter 的 ``SearchBar``：折叠态是一行输入条，点开后在页面上展开一层
**搜索视图**，``options`` 逐条列在下方。选中一条会回填文本、收起视图，并回调
``on_select``；只敲字不选建议时，回车走 ``on_submit``。

.. note::
    打开的是 Flutter 的搜索视图（覆盖路由），不是下拉框。它适合全局搜索、命令
    面板这类「输入 + 建议」的入口，不适合塞进表格单元格或很窄的工具栏。

.. note::
    选中建议后组件调用 ``close_view(option)`` 回填文本 —— 不直接写 ``value``，
    因为 ``@ft.component`` 渲染出的控件是冻结的，赋值会抛
    ``Frozen controls cannot be updated``。

用法::

    bar = SearchBar(
        options=["Input", "SelectBox", "Cascader"],
        bar_hint_text="搜索组件",
        on_select=lambda text: print(text),
    )
    Column([bar])
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import field

import flet as ft

from ui.core.doc import Api, Example, Spec, info, run, tip, warn
from ui.core.i18n import t
from ui.core.tokens import FONT_SIZE

__all__ = ["SearchBar"]


@ft.control
class SearchBar(ft.SearchBar):
    """搜索框：输入关键字，从建议列表里选一条，或回车提交。

    Args:
        options: 建议项文本；打开搜索视图后按顺序列在下方。
        on_select: 选中一条建议后的回调，收到该条文本。
        on_click: 原始点击回调，收到 flet 事件；``e.control.data`` 是选项文本。
    """

    options: list[str] = field(default_factory=list)
    #: 两个回调都只给 Python 侧用，不注册成 Flutter 事件（SearchBar 没有
    #: click / select 这两个事件），所以标 skip 让它们保持普通字段。
    on_click: Callable | None = field(default=None, metadata={"skip": True})
    on_select: Callable[[str], None] | None = field(
        default=None, metadata={"skip": True}
    )

    def init(self):
        if self.bar_hint_text is None:
            # 没给占位文案时跟随语言：中文「搜索」、英文 "Search"。
            self.bar_hint_text = t("ui.common.search")
        self.controls.extend(
            ft.ListTile(title=ft.Text(option), data=option, on_click=self._pick)
            for option in self.options
        )

    def _pick(self, e: ft.ControlEvent) -> None:
        """点建议：回填文本、收起视图，再广播给调用方。"""
        option = str(e.control.data)
        # close_view 是运行时方法，不改 Python 侧的 value，冻结控件上也能用。
        # 控件还没挂到页面上时 self.page 会抛错（单元测试 / 预渲染），跳过即可。
        try:
            page = self.page
        except RuntimeError:
            page = None
        if page is not None:
            page.run_task(self.close_view, option)
        if self.on_select:
            self.on_select(option)
        if self.on_click:
            self.on_click(e)


# ---------------------------------------------------------------------------
# 独立运行：组件介绍 + 示例 + API
# ---------------------------------------------------------------------------
def _caption(text: str) -> ft.Control:
    return ft.Text(
        text,
        size=FONT_SIZE["small"],
        color=ft.Colors.ON_SURFACE_VARIANT,
        style=ft.TextStyle(height=1.6),
    )


@ft.component
def _basic() -> ft.Control:
    picked, set_picked = ft.use_state("")
    bar = SearchBar(
        value=picked,
        options=["Input", "SelectBox", "Cascader", "DateInput"],
        bar_hint_text="搜索组件",
        on_select=set_picked,
    )
    return ft.Column(
        spacing=10,
        controls=[
            bar,
            _caption(f"最近选中：{picked or '（还没选）'}"),
        ],
    )


@ft.component
def _submit() -> ft.Control:
    query, set_query = ft.use_state("")

    def handle_submit(e: ft.ControlEvent) -> None:
        set_query((e.control.value or "").strip())

    bar = SearchBar(
        options=["Input", "SelectBox", "Cascader"],
        bar_hint_text="输入后回车",
        on_submit=handle_submit,
    )
    return ft.Column(
        spacing=10,
        controls=[
            bar,
            _caption(f"上次提交：{query or '（还没回车）'}"),
        ],
    )


@ft.component
def _clear() -> ft.Control:
    picked, set_picked = ft.use_state("DateInput")
    version, set_version = ft.use_state(0)

    def reset(_event) -> None:
        # 改 state + 换 key：控件整体重建，框内文字才真正回到空。
        set_picked("")
        set_version(lambda n: n + 1)

    bar = SearchBar(
        key=f"search-{version}",
        value=picked,
        options=["Input", "SelectBox", "Cascader", "DateInput"],
        bar_hint_text="搜索组件",
        on_select=set_picked,
    )
    return ft.Column(
        spacing=10,
        controls=[
            bar,
            _caption(f"当前关键字：{picked or '（空）'}"),
            ft.Button("清空搜索框", on_click=reset),
        ],
    )


_BASIC_CODE = """picked, set_picked = ft.use_state("")

bar = SearchBar(
    options=["Input", "SelectBox", "Cascader"],
    bar_hint_text="搜索组件",
    on_select=set_picked,          # 收到选中的纯文本
)
Column([bar, ft.Text(f"最近选中：{picked}")])"""

SPEC = Spec(
    name="SearchBar",
    summary="点开搜索视图，从建议里选一条，或回车提交关键字。",
    definition=(
        "搜索框把「输入关键字」和「从候选里挑一个」放在同一条路径上：折叠时是一行"
        "输入条，点开后展开一层搜索视图，建议列在下方，选中即回填并收起。它不负责"
        "取数据 —— 候选项由 options 给，真正的搜索请求挂在 on_change / on_submit 上。"
    ),
    anatomy=[
        (
            "输入条",
            "折叠态只占一行；点击后打开搜索视图，焦点直接落在输入框，不需要再点一次。",
        ),
        (
            "建议列表",
            "options 逐条生成 ListTile；点一条会回填文本、收起视图，并触发 on_select。",
        ),
        (
            "回车",
            "on_submit 在键盘回车时触发；读 e.control.value 拿完整关键字，没有候选也能提交。",
        ),
        (
            "清空",
            "搜索视图自带关闭按钮；受控场景改 value 并换一个 key 重建控件，框内文字才真正清空。",
        ),
        (
            "回调",
            "on_select 收纯文本；on_click 收原始事件（e.control.data 是选项），按需要选一个。",
        ),
    ],
    when=[
        "全局搜索、命令面板这类「输入 + 建议」的入口",
        "候选不多，用户需要边看边选（组件名、城市、标签）",
        "提交后要跳到结果页，选中建议只是先把关键字填好",
    ],
    avoid=[
        "只是录入一段文本、没有候选：用 Input，别为没有建议的字段打开搜索视图",
        "嵌在表格单元格或工具栏的窄搜索：SearchBar 会铺开一层视图，用 Input + 过滤列表更稳",
        "需要多选或分组建议：用 SelectBox / Transfer，SearchBar 的建议是平铺单列",
    ],
    examples=[
        Example(
            "建议列表",
            _basic,
            hint="点开输入条，从建议里选一条；on_select 收到文本，下面一行跟着更新。",
            code=_BASIC_CODE,
        ),
        Example(
            "回车提交",
            _submit,
            hint="不选建议也可以直接回车；on_submit 从 e.control.value 拿完整关键字。",
        ),
        Example(
            "清空",
            _clear,
            hint="「清空搜索框」改 state 并换 key 重建控件，框内文字回到空，不碰冻结的控件。",
        ),
    ],
    api=[
        Api("value", "str", "''", "框内文本；受控场景可用它回填选中项"),
        Api("options", "list[str]", "[]", "建议项文本；打开搜索视图后列在下方"),
        Api(
            "on_select",
            "Callable[[str], None] | None",
            "None",
            "选中建议后的回调，收到选项文本",
        ),
        Api(
            "on_click",
            "Callable | None",
            "None",
            "原始点击回调，收到 flet 事件（e.control.data 是选项）",
        ),
        Api(
            "on_change",
            "Callable | None",
            "None",
            "键入时回调；e.control.value 是当前文本",
        ),
        Api(
            "on_submit",
            "Callable | None",
            "None",
            "回车提交回调；e.control.value 是当前文本",
        ),
        Api(
            "bar_hint_text",
            "str | None",
            "None",
            "折叠态占位文案；None 取语言包的「搜索」",
        ),
        Api(
            "controls", "list[Control]", "[]", "建议列表控件；options 会按顺序自动生成"
        ),
        Api("disabled", "bool", "False", "禁用后不再打开搜索视图"),
        Api(
            "close_view",
            "async (str | None) -> None",
            "—",
            "收起搜索视图；传 text 可同时回填框内文字",
        ),
    ],
    notes=[
        info(
            "选中建议走 on_select（纯文本）；需要事件对象用 on_click。选中后组件会调用"
            " close_view(option) 回填并收起 —— 原来的实现只触发回调，框里不会出现选中文本。"
        ),
        tip(
            "不要在回调里直接改控件的 value：@ft.component 渲染出的控件是冻结的，赋值会抛"
            " Frozen controls cannot be updated。清空也一样，用 state 重建（见「清空」示例）。"
        ),
        warn(
            "打开的是 Flutter 的搜索视图（覆盖在页面上的一层路由），不是下拉框；容器很窄"
            "或候选很多时它会盖住整页，这种情况应该改用 Input 加一块过滤后的列表。"
        ),
    ],
    tags=("搜索", "搜索框", "search", "suggest", "input", "表单"),
)


if __name__ == "__main__":
    run(SPEC)
