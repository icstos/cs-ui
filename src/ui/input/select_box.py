"""下拉选择 (SelectBox) —— 单选、可输入筛选，值落在 value 上。

下拉解决的是「选项太多，摆不下」。收起时只占一行，展开才铺出候选列表；选项超过
七八个、或者标签长到一行放不下时，它比一排单选点更省地方。``editable`` 打开后
可以直接在框里打字筛选（按文本忽略大小写匹配），候选多时不用滚着找。

值只有一个 ``value``：``None`` 表示未选，空态显示占位文案；选中项回填进框里，
调用方读 ``value`` 就是最新结果，不需要解析事件对象。

用法::

    city = SelectBox(label="城市", options=["北京", "上海", "广州"], value="上海")
    Column([city.ui()])
    print(city.value)
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import flet as ft

from ui.core.doc import Api, Example, Spec, info, run, tip, warn
from ui.core.i18n import t
from ui.core.styles import INPUT_RADIUS, outline_input
from ui.core.tokens import CONTROL_HEIGHT, SPACE
from ui.input.input import Label

__all__ = ["SelectBox", "SelectOption"]

TEXT_SIZE = 14
PADDING = 10
#: 与输入框同高 —— 放在同一行表单里不能出现"台阶"。
#: 曾经写死 42，比 Input 的 36 高出一截。
INPUT_HEIGHT = CONTROL_HEIGHT["md"]
#: 默认宽度：下拉框不跟着最长选项撑开 —— 一个「中华人民共和国…」的选项
#: 会把整行表单顶出容器，而候选的完整文本在弹层里本来就能读到。
DEFAULT_WIDTH = 240


@ft.control
class SelectOption(ft.DropdownOption):
    """下拉选项：与 :class:`flet.DropdownOption` 同构，key 是值、text 是显示文本。"""


@ft.observable
@dataclass
class SelectBox(Label):
    """下拉选择：单选，可输入筛选，值落在 ``value`` 上。

    Args:
        value: 选中项的 key；``None`` 表示未选，框里显示 ``hint_text``。
        options: 候选；字符串的文本即 key，``SelectOption`` 可让值与显示文本分家。
        dense: 紧凑排布，一行表单里不额外撑高度。
        filled: 是否铺底色；默认描边 + 透明底，和输入框、多选下拉保持一致。
        editable: 允许在框里打字筛选；关闭后只能点选。
        hint_text: 未选时的占位文案；留空跟随界面语言（请选择 / Select…）。
        width: 输入框与弹层宽度；默认 240，避免长选项把一行撑开。
        disabled: 禁用：框和箭头一起降灰，不响应点击。
        on_change: 选中回调，入参是 flet 事件对象；表单校验常挂在这里。
    """

    value: str | None = None
    options: list[str | ft.DropdownOption] = field(default_factory=list)
    dense: bool = True
    filled: bool = False
    editable: bool = True
    hint_text: str | None = None
    width: int = DEFAULT_WIDTH
    disabled: bool = False
    on_change: Callable | None = None

    def _on_change(self, e):
        """把选中的 key 写回 ``value``；没选时归 ``None`` 而不是空串。"""
        self.value = getattr(e.control, "value", None) or None

    def _dropdown_options(self) -> list[ft.DropdownOption]:
        """把字符串 / 选项对象统一成 ``DropdownOption``。

        老的 ``ft.dropdownm2.Option`` 也算合法输入：两者字段同构，直接把 key 与
        text 搬过来，调用方不必为了换控件改一堆构造。
        """
        out: list[ft.DropdownOption] = []
        for option in self.options:
            if isinstance(option, ft.DropdownOption):
                out.append(option)
            elif isinstance(option, str):
                out.append(ft.DropdownOption(key=option, text=option))
            elif isinstance(option, ft.dropdownm2.Option):
                out.append(
                    ft.DropdownOption(
                        key=option.key or option.text,
                        text=option.text or option.key,
                    )
                )
            else:
                out.append(ft.DropdownOption(key=str(option), text=str(option)))
        return out

    @ft.component
    def ui(self):
        """渲染下拉框：一行输入区 + 可展开的候选列表。"""

        def _on_select(e):
            self._on_change(e)
            if self.on_change:
                self.on_change(e)
            self.notify()  # type: ignore[attr-defined]

        v_ui = ft.Dropdown(
            value=self.value,
            options=self._dropdown_options(),
            width=self.width,
            height=INPUT_HEIGHT,
            text_size=TEXT_SIZE,
            dense=self.dense,
            filled=self.filled,
            disabled=self.disabled,
            hint_text=self.hint_text or t("ui.common.placeholder"),
            # 可编辑与筛选是一件事的两半：只开 editable，输入不会过滤候选；
            # 只开 enable_filter，框根本没法聚焦输入。
            editable=self.editable,
            enable_filter=self.editable,
            # 42 高的框里留 10 的上下内边距，14px 文字才落在中线上
            content_padding=ft.Padding.symmetric(horizontal=PADDING, vertical=10),
            # 描边走角色色：以前的 GREY_200 定值在深色主题下是一块亮灰
            border=outline_input(
                INPUT_RADIUS, ft.Colors.OUTLINE_VARIANT, ft.Colors.PRIMARY
            ),
            on_select=_on_select,
        )

        if self.v_label is not None:
            if self.is_vertical:
                return ft.Column(
                    controls=[self.v_label, v_ui],
                    spacing=SPACE["1"],
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                )
            return ft.Row(
                controls=[self.v_label, v_ui],
                spacing=SPACE["2"],
                # 42 高的框要和标签中线对齐，否则标签浮在框顶
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        return v_ui


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
def _caption(text: str) -> ft.Control:
    return ft.Text(text, size=12, color=ft.Colors.ON_SURFACE_VARIANT)


@ft.component
def _basic() -> ft.Control:
    """直接打字就能筛：输入「杭」只剩杭州，回填的是选中项的 key。"""
    city, set_city = ft.use_state("上海")
    return ft.Column(
        spacing=12,
        controls=[
            SelectBox(
                label="城市",
                options=["北京", "上海", "广州", "深圳", "杭州", "成都"],
                value=city,
                width=220,
                on_change=lambda e: set_city(e.control.value),
            ).ui(),
            _caption(f"当前值：{city or '未选'}（可直接输入关键字筛选）"),
        ],
    )


@ft.component
def _many() -> ft.Control:
    """值与显示文本分开：框里读「华东 · 上海」，提交的是 sh。"""
    region, set_region = ft.use_state("sh")
    return ft.Column(
        spacing=12,
        controls=[
            SelectBox(
                label="常驻城市",
                options=[
                    SelectOption("bj", "华北 · 北京"),
                    SelectOption("sh", "华东 · 上海"),
                    SelectOption("gz", "华南 · 广州"),
                    SelectOption("sz", "华南 · 深圳"),
                    SelectOption("hz", "华东 · 杭州"),
                    SelectOption("cd", "西南 · 成都"),
                    SelectOption("wh", "华中 · 武汉"),
                    SelectOption("xa", "西北 · 西安"),
                    SelectOption("sy", "东北 · 沈阳"),
                    SelectOption("nj", "华东 · 南京"),
                    SelectOption("tj", "华北 · 天津"),
                    SelectOption("cq", "西南 · 重庆"),
                    SelectOption("cs", "华中 · 长沙"),
                    SelectOption("km", "西南 · 昆明"),
                    SelectOption("fz", "华东 · 福州"),
                    SelectOption("hf", "华东 · 合肥"),
                ],
                value=region,
                width=240,
                on_change=lambda e: set_region(e.control.value),
            ).ui(),
            _caption(f"提交的值：{region or '未选'}（显示文本不进 value）"),
        ],
    )


@ft.component
def _disabled_and_empty() -> ft.Control:
    """禁用只看不改；空态靠占位文案说清「还没选」，并给一个清空入口。"""
    project, set_project = ft.use_state(None)
    dept = SelectBox(
        label="所属部门",
        options=["研发中心", "设计中心", "市场部"],
        value="研发中心",
        disabled=True,
        width=220,
    )

    def clear(_e):
        set_project(None)

    return ft.Column(
        spacing=12,
        controls=[
            dept.ui(),
            SelectBox(
                label="负责项目",
                options=["数据中台", "客户门户", "计费系统"],
                value=project,
                width=220,
                on_change=lambda e: set_project(e.control.value),
            ).ui(),
            ft.Button(content="清空负责项目", on_click=clear),
            _caption(f"禁用项的值仍可读：{dept.value}；空态：{project or '未选'}"),
        ],
    )


_BASIC_CODE = """city = SelectBox(
    label="城市",
    options=["北京", "上海", "广州", "深圳", "杭州", "成都"],
    value="上海",
)
Column([city.ui(), Text(f"当前：{city.value}")])"""

_MANY_CODE = """SelectBox(
    label="常驻城市",
    options=[
        SelectOption("sh", "华东 · 上海"),   # key 提交，text 显示
        SelectOption("gz", "华南 · 广州"),
    ],
    value="sh",
).ui()"""


SPEC = Spec(
    name="SelectBox",
    summary="单选下拉：收起只占一行，展开才铺候选，还能直接打字筛选。",
    definition=(
        "下拉框把候选列表折进一行里，只在需要时展开 —— 选项超过七八个、或者标签长到"
        "一行放不下时，它比摊开的单选点省地方。值只有一个 ``value``：未选为 ``None``，"
        "选中后回填进框里。``editable`` 打开时可以直接在框内输入筛选，省掉在长列表里"
        "滚动查找的那几步。"
    ),
    anatomy=[
        ("输入区", "42px 高、6px 圆角、1px 描边；聚焦转主色，禁用整体降灰。"),
        ("选中值", "选中项回填进框里；未选时显示占位文案（默认跟随界面语言）。"),
        ("筛选输入", "editable 打开后可直接打字，候选按文本忽略大小写过滤。"),
        ("候选弹层", "点箭头或框展开，宽度与输入框同宽，超出屏幕高度时内部滚动。"),
        ("展开箭头", "固定在最右侧，禁用时一起变灰 —— 灰箭头已经在说「点不开」。"),
    ],
    when=[
        "选项超过七八个，摊开会把表单撑得很长",
        "选项文本较长（城市、部门、项目名），一行放不下几个",
        "候选多到需要输入关键字筛选（省份、物料、客户）",
    ],
    avoid=[
        "两三个短选项：用 Radio，多一次展开就多一次点击",
        "允许同时选多个：用 MultiSelect，单选下拉选第二个会替换第一个",
        "选项之间需要逐条比较说明：用 RadioCard，弹层里读不到那么多文字",
    ],
    examples=[
        Example(
            "基础下拉",
            _basic,
            hint="六个城市，输入「杭」即可筛出杭州；选中后 value 立刻回写。",
            code=_BASIC_CODE,
        ),
        Example(
            "大量选项",
            _many,
            hint="十六个候选，值与显示文本分开：框里读「华东 · 上海」，value 是 sh。",
            code=_MANY_CODE,
        ),
        Example(
            "禁用与空态",
            _disabled_and_empty,
            hint="禁用项保留选中值但点不开；空态显示占位文案，可用按钮清空。",
        ),
    ],
    api=[
        Api("value", "str | None", "None", "选中项的 key；None 表示未选，显示占位"),
        Api(
            "options",
            "list[str | ft.DropdownOption]",
            "[]",
            "候选；字符串的文本即 key，用 SelectOption 可分离值与文本",
        ),
        Api("editable", "bool", "True", "允许在框里打字筛选；关掉只能点选"),
        Api("hint_text", "str | None", "None", "未选时的占位文案；留空跟随界面语言"),
        Api("width", "int", "240", "输入框与弹层宽度，防止长选项撑破布局"),
        Api("dense", "bool", "True", "紧凑排布，避免一行表单被撑高"),
        Api("filled", "bool", "False", "是否铺底色；默认描边 + 透明底"),
        Api("disabled", "bool", "False", "禁用：框与箭头一起降灰，不响应点击"),
        Api(
            "on_change",
            "Callable | None",
            "None",
            "选中回调，入参是 flet 事件对象；校验与联动挂在这里",
        ),
    ],
    notes=[
        tip(
            "``editable`` 与筛选必须一起给：只开 editable，输入不会过滤候选；"
            "只开 enable_filter，框根本没法聚焦输入。底层也从 DropdownM2 换成了"
            " M3 的 Dropdown —— 旧控件没有筛选能力，``editable`` / ``dense`` 两个"
            "参数一直是空转的。"
        ),
        info(
            "``value`` 从控件属性读、并把空值归一成 ``None``：事件载荷是字符串，"
            "清空时给出空串，直接存下去会让「未选」和「值为空串的选项」分不开。"
        ),
        warn(
            "``value`` 必须是某个选项的 key。传了候选里没有的值，框里会是空的 ——"
            "Flutter 侧按 key 匹配，匹配不到就不显示。"
        ),
    ],
    tags=("下拉", "选择器", "select", "dropdown", "表单"),
)


if __name__ == "__main__":
    run(SPEC)
