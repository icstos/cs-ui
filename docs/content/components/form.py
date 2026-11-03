"""表单组件：输入、选择、日期、滑块、取色与搜索。"""

from __future__ import annotations

import datetime as dt

import flet as ft

from docs import kit
from docs.blocks import Doc, code, demo, h2, note, p, tip, ul
from ui import (
    Checkbox,
    CheckboxGroup,
    ColorPicker,
    Column,
    DateInput,
    DateTimeInput,
    Input,
    LayoutType,
    MultiSelect,
    Radio,
    RangeSlider,
    Rating,
    SearchBar,
    SegmentedButton,
    SelectBox,
    Slider,
    Switch,
    use_t,
)

#: 演示输入框的统一尺寸：标签窄一点，两列才排得下。
_BOX = {"label_width": 72, "width": 200}

_INPUT_CODE = '''Input(label="Name", value="Shawn", width=260)
Input(label="Age", value="30", data_type="int", width=260)
Input(label="Budget", value="199.9", data_type="float", width=260)'''

_DATE_CODE = '''DateInput(label="Birthday", value=date(1996, 5, 20))
DateTimeInput(
    label="Meeting",
    value=datetime(2026, 3, 18, 9, 30),
    minute_step=5,
)'''

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
    age = kit.use_stable(
        lambda: Input(
            label=tr("demo.field.age"), value="30", data_type="int", **_BOX
        )
    )
    budget = kit.use_stable(
        lambda: Input(
            label=tr("demo.field.budget"), value="199.9", data_type="float", **_BOX
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
        controls=[name.ui(), age.ui(), budget.ui(), folder.ui()],
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


@ft.component
def _dates() -> ft.Control:
    tr = use_t()
    birthday = kit.use_stable(
        lambda: DateInput(
            label=tr("demo.field.birthday"), value=dt.date(1996, 5, 20)
        )
    )
    meeting = kit.use_stable(
        lambda: DateTimeInput(
            label=tr("demo.field.meeting"),
            value=dt.datetime(2026, 3, 18, 9, 30),  # noqa: DTZ001 - 演示用本地时间
            with_seconds=False,
            minute_step=5,
        )
    )
    return Column(spacing=14, controls=[birthday.ui(), meeting.ui()])


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
    h2("cat.form.choice.title"),
    demo(_choices, hint_key="cat.form.choice.hint"),
    h2("cat.form.select.title"),
    demo(_selects, hint_key="cat.form.select.hint"),
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
