"""表单组件：输入、选择、日期、滑块、取色与搜索。"""

from __future__ import annotations

import datetime as dt

import flet as ft

from docs import kit
from docs.blocks import Doc, code, demo, h2, note, p, tip, ul
from ui import (
    Cascader,
    Checkbox,
    CheckboxGroup,
    ColorPicker,
    Column,
    DateInput,
    DateTimeInput,
    Input,
    LayoutType,
    Message,
    MultiSelect,
    NumberInput,
    Radio,
    RangeSlider,
    Rating,
    Row,
    SearchBar,
    SegmentedButton,
    SelectBox,
    Slider,
    Switch,
    Transfer,
    TransferItem,
    use_t,
)

#: 演示输入框的统一尺寸：标签窄一点，两列才排得下。
_BOX = {"label_width": 72, "width": 200}

_INPUT_CODE = '''Input(label="Name", value="Shawn", width=260)
Input(label="Folder", value="", data_type="dir", width=260)'''

_NUMBER_CODE = '''NumberInput(label="Quantity", value=12, min=1, max=99)
NumberInput(label="Tax rate", value=0.13, step=0.01, precision=2, suffix="%",
            controls_position="right")
NumberInput(label="Price", value=199.9, step=0.1, precision=2, prefix="¥")'''

_DATE_CODE = '''DateInput(label="Date", value=date(2026, 9, 26))
DateInput(label="Week", type="week", value=date(2026, 9, 26))
DateInput(label="Month", type="month", value=date(2026, 9, 1))
DateInput(label="Year", type="year", value=date(2026, 1, 1))
DateInput(label="Dates", type="dates", value=[date(2026, 9, 3), date(2026, 9, 8)])
DateInput(label="Range", type="daterange",
          value=(date(2026, 9, 1), date(2026, 9, 20)))
DateInput(label="Months", type="monthrange",
          value=(date(2026, 3, 1), date(2026, 9, 1)))
DateTimeInput(label="Meeting", value=datetime(2026, 3, 18, 9, 30), minute_step=5)'''

_STABLE_CODE = '''# 在 @ft.component 里固定实例：父组件重绘不会重建，输入不丢
name = ft.use_ref(lambda: Input(label="Name", width=260)).current'''


@ft.component
def _inputs() -> ft.Control:
    tr = use_t()
    # 标签 72 / 输入框 200：一屏能稳稳排两列，不用横向滚动。
    name = kit.use_stable(
        lambda: Input(
            label=tr("demo.field.name"), value="Shawn", **_BOX
        )
    )
    folder = kit.use_stable(
        lambda: Input(label=tr("demo.field.folder"), value="", data_type="dir", **_BOX)
    )
    return ft.Row(
        spacing=18,
        wrap=True,
        run_spacing=14,
        vertical_alignment=ft.CrossAxisAlignment.START,
        controls=[name.ui(), folder.ui()],
    )


@ft.component
def _numbers() -> ft.Control:
    tr = use_t()
    qty = kit.use_stable(
        lambda: NumberInput(
            label=tr("demo.field.qty"), value=12, min=1, max=99, **_BOX
        )
    )
    rate = kit.use_stable(
        lambda: NumberInput(
            label=tr("demo.field.rate"),
            value=0.13,
            step=0.01,
            precision=2,
            suffix="%",
            controls_position="right",
            **_BOX,
        )
    )
    budget = kit.use_stable(
        lambda: NumberInput(
            label=tr("demo.field.budget"),
            value=199.9,
            step=0.1,
            precision=2,
            prefix="¥",
            **_BOX,
        )
    )
    return ft.Row(
        spacing=18,
        wrap=True,
        run_spacing=14,
        vertical_alignment=ft.CrossAxisAlignment.START,
        controls=[qty.ui(), rate.ui(), budget.ui()],
    )


@ft.component
def _choices() -> ft.Control:
    tr = use_t()
    agree = kit.use_stable(
        lambda: Checkbox(label=tr("demo.field.agree"), is_required=True)
    )
    hobbies = kit.use_stable(
        lambda: CheckboxGroup(
            label=tr("demo.field.hobbies"),
            options=tr.list("demo.hobbies"),
            is_required=True,
        )
    )
    notify = kit.use_stable(lambda: Switch(label=tr("demo.field.notify"), value=True))
    compact = kit.use_stable(lambda: Switch(label=tr("demo.field.compact")))
    plan = kit.use_stable(
        lambda: Radio(
            label=tr("demo.field.plan"),
            options=tr.list("demo.plans"),
            value=tr.list("demo.plans")[0],
            radio_layout_type=LayoutType.HORIZONTAL,
        )
    )
    return ft.Row(
        spacing=28,
        wrap=True,
        run_spacing=18,
        vertical_alignment=ft.CrossAxisAlignment.START,
        controls=[
            Column(spacing=10, width=282, controls=[agree.ui(), hobbies.ui()]),
            Column(spacing=10, width=200, controls=[notify.ui(), compact.ui()]),
            plan.ui(),
        ],
    )


#: 级联演示数据：地名是专有名词，三语共用一份。
_CASCADER_OPTIONS = [
    {
        "label": "浙江",
        "children": [
            {"label": "杭州", "children": [
                {"label": "西湖区"}, {"label": "余杭区"},
            ]},
            {"label": "宁波", "children": [{"label": "海曙区"}]},
        ],
    },
    {
        "label": "江苏",
        "children": [
            {"label": "南京", "children": [{"label": "鼓楼区"}]},
            {"label": "苏州", "children": [{"label": "姑苏区"}]},
        ],
    },
    {"label": "北京", "children": [
        {"label": "朝阳区"}, {"label": "海淀区"},
    ]},
]

_CASCADE_CODE = '''Cascader(label="Region", options=_OPTIONS,
           value=["浙江", "杭州", "西湖区"])
Cascader(label="Cities", options=_OPTIONS, multiple=True,
         value=[["浙江", "杭州"]], collapse_tags=True)
Cascader(label="Search", options=_OPTIONS, filterable=True)
Cascader(label="Any level", options=_OPTIONS, check_strictly=True,
         value=["江苏"], show_all_levels=False)'''


@ft.component
def _cascader() -> ft.Control:
    basic = kit.use_stable(
        lambda: Cascader(
            label="地区",
            options=_CASCADER_OPTIONS,
            value=["浙江", "杭州", "西湖区"],
        )
    )
    multi = kit.use_stable(
        lambda: Cascader(
            label="多选",
            options=_CASCADER_OPTIONS,
            multiple=True,
            value=[["浙江", "杭州"], ["江苏", "南京"]],
            collapse_tags=True,
        )
    )
    search = kit.use_stable(
        lambda: Cascader(label="搜索", options=_CASCADER_OPTIONS, filterable=True)
    )
    strict = kit.use_stable(
        lambda: Cascader(
            label="任意级",
            options=_CASCADER_OPTIONS,
            check_strictly=True,
            value=["北京"],
            show_all_levels=False,
        )
    )
    return Column(spacing=14, controls=[basic.ui(), multi.ui(), search.ui(), strict.ui()])


@ft.component
def _selects() -> ft.Control:
    tr = use_t()
    city = kit.use_stable(
        lambda: SelectBox(
            label=tr("demo.field.city"),
            options=tr.list("demo.cities"),
            value=tr.list("demo.cities")[0],
        )
    )
    tags = kit.use_stable(
        lambda: MultiSelect(
            label=tr("demo.field.tags"),
            options=tr.list("demo.tags"),
            value=tr.list("demo.tags")[1:3],
        )
    )
    return Column(spacing=14, controls=[city.ui(), tags.ui()])


_TRANSFER_CODE = '''Transfer(
    data_source=[
        TransferItem("name", "姓名"),
        TransferItem("dept", "部门", description="一级 / 二级部门"),
        TransferItem("id", "证件号", disabled=True),   # 两侧都搬不动
    ],
    target_keys=["name"],        # 已选，恒按 data_source 排序
    titles=("可授权", "已授权"),
    on_change=lambda keys, direction, moved: print(keys, direction, moved),
)'''


def _transfer_items(tr) -> list[TransferItem]:
    """演示条目。``id`` 那条故意禁用：它搬不走，但照常显示、照常能被搜到。"""
    return [
        TransferItem("name", tr("cat.form.transfer.name")),
        TransferItem(
            "dept",
            tr("cat.form.transfer.dept"),
            description=tr("cat.form.transfer.dept_desc"),
        ),
        TransferItem(
            "email",
            tr("cat.form.transfer.email"),
            description=tr("cat.form.transfer.email_desc"),
        ),
        TransferItem("phone", tr("cat.form.transfer.phone")),
        TransferItem(
            "id",
            tr("cat.form.transfer.id"),
            description=tr("cat.form.transfer.id_desc"),
            disabled=True,
        ),
    ]


@ft.component
def _transfer() -> ft.Control:
    tr = use_t()
    page = ft.context.page

    # on_change 必须在**构造期**定下来，而 use_state 的 setter 要等渲染时才有，
    # 所以用一只可变盒子转手（同 Calendar 那节的理由）。
    hook: list = [None]

    def on_change(keys: list[str], direction: str, moved: list[str]) -> None:
        key = (
            "cat.form.transfer.moved"
            if direction == "right"
            else "cat.form.transfer.back"
        )
        Message.success(tr(key, n=len(moved)), page=page)
        if hook[0] is not None:
            hook[0](keys)

    widget = kit.use_stable(
        lambda: Transfer(
            titles=(
                tr("cat.form.transfer.src"),
                tr("cat.form.transfer.dst"),
            ),
            data_source=_transfer_items(tr),
            target_keys=["name", "phone"],
            height=260,
            on_change=on_change,
        )
    )
    picked, set_picked = ft.use_state(["name", "phone"])
    hook[0] = set_picked

    titles = {item.key: item.title for item in widget.data_source}
    summary = "、".join(titles.get(k, k) for k in picked) or tr(
        "cat.form.transfer.nothing"
    )
    return Column(
        spacing=14,
        horizontal_alignment=ft.CrossAxisAlignment.START,
        controls=[
            widget.ui(),
            ft.Text(
                tr("cat.form.transfer.current", keys=summary),
                size=12,
                color=kit.MUTED,
            ),
        ],
    )


@ft.component
def _transfer_plain() -> ft.Control:
    tr = use_t()
    widget = kit.use_stable(
        lambda: Transfer(
            titles=(
                tr("cat.form.transfer.src"),
                tr("cat.form.transfer.dst"),
            ),
            data_source=_transfer_items(tr)[:4],
            target_keys=[],
            show_search=False,
            show_select_all=False,
            one_way=True,
            height=248,
        )
    )
    return widget.ui()


def _pair(left: ft.Control, right: ft.Control) -> ft.Control:
    """两列并排：日期类输入框只有 220 宽，单列排下来太长。

    每个子项都套一层 ``tight=True`` 的 Row —— ``DateInput`` 的根是"标签 + 输入框"，
    默认会撑满可用宽度（主轴上取 max），不收紧就会变成"一项一行"。
    """

    def cell(control: ft.Control) -> ft.Control:
        return ft.Row(tight=True, controls=[control])

    return Row(spacing=20, run_spacing=14, wrap=True, controls=[cell(left), cell(right)])



@ft.component
def _dates() -> ft.Control:
    tr = use_t()

    def make(key: str, **kwargs):
        # 宽度从 kwargs 里取，别写死在构造函数上 —— 区间那两项要传 300，
        # 否则会撞成 "got multiple values for keyword argument 'width'"。
        w = kwargs.pop("width", 220)

        def build(k=key, kw=kwargs, width=w):
            return DateInput(
                label=tr(f"demo.field.{k}"), label_width=72, width=width, **kw
            )

        return kit.use_stable(build)

    single = make("date", value=dt.date(2026, 9, 26))
    week = make("week", type="week", value=dt.date(2026, 9, 26))
    month = make("month", type="month", value=dt.date(2026, 9, 1))
    year = make("year", type="year", value=dt.date(2026, 1, 1))
    dates = make("dates", type="dates", value=[dt.date(2026, 9, 3), dt.date(2026, 9, 8), dt.date(2026, 9, 15)])
    # 范围两端的文本接近 170px，220 的框会截断，单独给宽一点
    daterange = make(
        "daterange", type="daterange", width=300,
        value=(dt.date(2026, 9, 1), dt.date(2026, 9, 20)),
    )
    monthrange = make(
        "monthrange", type="monthrange", width=300,
        value=(dt.date(2026, 3, 1), dt.date(2026, 9, 1)),
    )
    meeting = kit.use_stable(
        lambda: DateTimeInput(
            label=tr("demo.field.meeting"),
            value=dt.datetime(2026, 3, 18, 9, 30),  # noqa: DTZ001 - 演示用本地时间
            with_seconds=False,
            minute_step=5,
        )
    )
    return Column(
        spacing=16,
        horizontal_alignment=ft.CrossAxisAlignment.START,
        controls=[
            _pair(single.ui(), week.ui()),
            _pair(month.ui(), year.ui()),
            _pair(dates.ui(), meeting.ui()),
            daterange.ui(),
            monthrange.ui(),
        ],
    )


@ft.component
def _sliders() -> ft.Control:
    tr = use_t()
    volume = kit.use_stable(
        lambda: Slider(
            label=tr("demo.field.volume"),
            value=40,
            min=0,
            max=100,
            divisions=10,
            slider_label="{value}%",
        )
    )
    price = kit.use_stable(
        lambda: RangeSlider(
            label=tr("demo.field.price"),
            start_value=1500,
            end_value=6500,
            min=0,
            max=10000,
            divisions=20,
            slider_label="{value}",
        )
    )
    return Column(spacing=14, controls=[volume.ui(), price.ui()])


@ft.component
def _rating() -> ft.Control:
    tr = use_t()
    score = kit.use_stable(lambda: Rating(value=4, elements=5))
    return ft.Row(
        spacing=26,
        wrap=True,
        run_spacing=14,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Column(
                spacing=4,
                controls=[
                    ft.Text(tr("demo.rating.editable"), size=11, color=kit.MUTED),
                    score,
                ],
            ),
            ft.Column(
                spacing=4,
                controls=[
                    ft.Text(tr("demo.rating.readonly"), size=11, color=kit.MUTED),
                    Rating(value=3, readonly=True),
                ],
            ),
            ft.Column(
                spacing=4,
                controls=[
                    ft.Text(tr("demo.rating.disabled"), size=11, color=kit.MUTED),
                    Rating(value=2, disabled=True),
                ],
            ),
        ],
    )


@ft.component
def _segmented() -> ft.Control:
    tr = use_t()
    options = tr.list("demo.views")
    mode = kit.use_stable(
        lambda: SegmentedButton(
            options=options,
            selected=[options[0]],
            allow_multiple_selection=False,
            allow_empty_selection=False,
        )
    )
    return mode


@ft.component
def _colors() -> ft.Control:
    tr = use_t()
    brand = kit.use_stable(
        lambda: ColorPicker(label=tr("demo.field.brand"), value="#1F6FEB")
    )
    overlay = kit.use_stable(
        lambda: ColorPicker(
            label=tr("demo.field.overlay"),
            value="#7C3AEDB3",
            default="#7C3AED",
            preset_cols=8,
        )
    )
    return Column(spacing=14, controls=[brand.ui(), overlay.ui()])


@ft.component
def _search() -> ft.Control:
    tr = use_t()
    page = ft.context.page
    bar = kit.use_stable(
        lambda: SearchBar(
            options=tr.list("demo.cities"),
            bar_hint_text=tr("demo.search.bar"),
            view_hint_text=tr("demo.search.view"),
            on_click=lambda event: page.launch_url("https://flet.dev"),
        )
    )
    return ft.Column(
        spacing=12,
        controls=[
            ft.Container(
                border_radius=10,
                bgcolor=ft.Colors.SURFACE,
                border=ft.Border.all(1, kit.BORDER),
                content=bar,
            ),
            ft.Text(tr("demo.search.hint"), size=11.5, color=kit.MUTED),
        ],
    )


FORM: Doc = (
    p("cat.form.intro"),
    h2("cat.form.input.title"),
    demo(_inputs, hint_key="cat.form.input.hint", code=_INPUT_CODE),
    h2("cat.form.number.title"),
    demo(_numbers, hint_key="cat.form.number.hint", code=_NUMBER_CODE),
    h2("cat.form.choice.title"),
    demo(_choices, hint_key="cat.form.choice.hint"),
    h2("cat.form.select.title"),
    demo(_selects, hint_key="cat.form.select.hint"),
    h2("cat.form.transfer.title"),
    demo(_transfer, hint_key="cat.form.transfer.hint", code=_TRANSFER_CODE),
    h2("cat.form.transfer.plain_title"),
    demo(_transfer_plain, hint_key="cat.form.transfer.plain_hint"),
    h2("cat.form.cascader.title"),
    demo(_cascader, hint_key="cat.form.cascader.hint", code=_CASCADE_CODE),
    h2("cat.form.date.title"),
    demo(_dates, hint_key="cat.form.date.hint", code=_DATE_CODE),
    h2("cat.form.slider.title"),
    demo(_sliders, hint_key="cat.form.slider.hint"),
    h2("cat.form.rating.title"),
    demo(_rating, hint_key="cat.form.rating.hint"),
    h2("cat.form.segment.title"),
    demo(_segmented, hint_key="cat.form.segment.hint"),
    h2("cat.form.color.title"),
    demo(_colors, hint_key="cat.form.color.hint"),
    h2("cat.form.search.title"),
    demo(_search, hint_key="cat.form.search.hint"),
    ul("cat.form.note1", "cat.form.note2", "cat.form.note3"),
    code(_STABLE_CODE, "form.py"),
    tip("cat.form.tip", "cat.form.tip_title"),
    note("cat.form.tip2", "cat.form.tip2_title"),
)
