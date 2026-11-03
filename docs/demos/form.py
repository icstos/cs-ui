"""表单与输入组件演示。"""

from __future__ import annotations

import datetime as dt

import flet as ft

from docs.demos._helpers import MUTED, panel, use_stable
from docs.kit import cell, demo_card, demo_grid, doc_page
from ui import (
    Button,
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
    toast_info,
    use_t,
)


@ft.component
def form_page() -> ft.Control:
    tr = use_t()
    page = ft.context.page

    name = use_stable(
        lambda: Input(label=tr("form.input.name"), value="Shawn", width=260)
    )
    age = use_stable(
        lambda: Input(label=tr("form.input.age"), value="30", data_type="int", width=300)
    )
    amount = use_stable(
        lambda: Input(
            label=tr("form.input.amount"),
            value="199.9",
            data_type="float",
            width=300,
        )
    )
    project_dir = use_stable(
        lambda: Input(
            label=tr("form.input.dir"),
            value="",
            data_type="dir",
            width=300,
        )
    )
    agree = use_stable(
        lambda: Checkbox(label=tr("form.checkbox.agree"), is_required=True)
    )
    hobbies = use_stable(
        lambda: CheckboxGroup(
            label=tr("form.checkbox.hobbies"),
            options=tr.list("form.checkbox.options"),
            is_required=True,
        )
    )
    dark = use_stable(lambda: Switch(label=tr("form.switch.dark")))
    notify = use_stable(lambda: Switch(label=tr("form.switch.notify"), value=True))
    gender = use_stable(
        lambda: Radio(
            label=tr("form.radio.gender"),
            options=tr.list("form.radio.options"),
            value=tr.list("form.radio.options")[0],
            radio_layout_type=LayoutType.HORIZONTAL,
        )
    )
    city = use_stable(
        lambda: SelectBox(
            label=tr("form.select.city"),
            options=tr.list("form.select.cities"),
            value=tr.list("form.select.cities")[0],
        )
    )
    tags = use_stable(
        lambda: MultiSelect(
            label=tr("form.select.tags"),
            options=tr.list("form.select.tag_options"),
            value=tr.list("form.select.tag_options")[1:3],
        )
    )
    volume = use_stable(
        lambda: Slider(
            label=tr("form.slider.volume"),
            value=40,
            min=0,
            max=100,
            divisions=10,
            slider_label="{value}%",
        )
    )
    price_range = use_stable(
        lambda: RangeSlider(
            label=tr("form.slider.price"),
            start_value=1500,
            end_value=6500,
            min=0,
            max=10000,
            divisions=20,
            slider_label="{value}",
        )
    )
    pitch = use_stable(lambda: Rating(value=4, elements=5))
    align_mode = use_stable(
        lambda: SegmentedButton(
            options=tr.list("form.segmented.options"),
            selected=[tr.list("form.segmented.options")[1]],
            allow_multiple_selection=False,
            allow_empty_selection=False,
        )
    )
    birthday = use_stable(
        lambda: DateInput(
            label=tr("form.date.birthday"),
            value=dt.date(1996, 5, 20),
        )
    )
    meeting = use_stable(
        lambda: DateTimeInput(
            label=tr("form.date.meeting"),
            value=dt.datetime(2026, 3, 18, 9, 30),  # noqa: DTZ001 - 演示用本地时间
            with_seconds=False,
            minute_step=5,
        )
    )
    checkin = use_stable(
        lambda: DateTimeInput(
            label=tr("form.date.checkin"),
            value=dt.datetime(2026, 3, 18, 9, 30, 15),  # noqa: DTZ001 - 同上
            with_seconds=True,
            hour_step=1,
            second_step=5,
            clearable=False,
        )
    )
    search = use_stable(
        lambda: SearchBar(
            options=tr.list("form.select.cities"),
            bar_hint_text=tr("form.search.bar_hint"),
            view_hint_text=tr("form.search.view_hint"),
            on_click=lambda event: print(f"[SearchBar] {event.control.data}"),
        )
    )
    brand_color = use_stable(
        lambda: ColorPicker(label=tr("form.color.brand"), value="#1F6FEB")
    )
    overlay_color = use_stable(
        lambda: ColorPicker(
            label=tr("form.color.overlay"),
            value="#7C3AEDB3",
            default="#7C3AED",
            preset_cols=8,
        )
    )
    locked_color = use_stable(
        lambda: ColorPicker(
            label=tr("form.color.locked"),
            value="#94A3B8",
            disabled=True,
            clearable=False,
        )
    )

    def dump_values(_: ft.Event[Button]) -> None:
        stars = pitch.value + 1 if isinstance(pitch.value, int) else 0
        toast_info(
            tr(
                "form.dump",
                name=name.value,
                age=age.value,
                city=city.value,
                tags=tags.display_text,
                volume=volume.value,
                stars=stars,
                birthday=birthday.display_text or "—",
                meeting=meeting.display_text or "—",
                brand=brand_color.value,
            ),
            page=page,
        )

    inputs = demo_card(
        title=tr("form.input.title"),
        hint=tr("form.input.hint"),
        icon=ft.Icons.EDIT_OUTLINED,
        stretch=True,
        body=[
            Column(
                spacing=12,
                controls=[name.ui(), age.ui(), amount.ui(), project_dir.ui()],
            )
        ],
    )

    checks = demo_card(
        title=tr("form.checkbox.title"),
        hint=tr("form.checkbox.hint"),
        icon=ft.Icons.CHECK_BOX_OUTLINED,
        stretch=True,
        body=[Column(spacing=12, controls=[agree.ui(), hobbies.ui()])],
    )

    switches = demo_card(
        title=tr("form.switch.title"),
        hint=tr("form.switch.hint"),
        icon=ft.Icons.TOGGLE_ON_OUTLINED,
        stretch=True,
        body=[Column(spacing=12, controls=[dark.ui(), notify.ui()])],
    )

    radios = demo_card(
        title=tr("form.radio.title"),
        hint=tr("form.radio.hint"),
        icon=ft.Icons.RADIO_BUTTON_CHECKED,
        stretch=True,
        body=[gender.ui()],
    )

    selects = demo_card(
        title=tr("form.select.title"),
        hint=tr("form.select.hint"),
        icon=ft.Icons.LIST_ALT,
        stretch=True,
        body=[Column(spacing=12, controls=[city.ui(), tags.ui()])],
    )

    sliders = demo_card(
        title=tr("form.slider.title"),
        hint=tr("form.slider.hint"),
        icon=ft.Icons.TUNE,
        stretch=True,
        body=[Column(spacing=12, controls=[volume.ui(), price_range.ui()])],
    )

    ratings = demo_card(
        title=tr("form.rating.title"),
        hint=tr("form.rating.hint"),
        icon=ft.Icons.STAR_OUTLINE,
        stretch=True,
        body=[
            Column(
                spacing=16,
                controls=[
                    ft.Column(
                        spacing=4,
                        controls=[
                            ft.Text(
                                tr("form.rating.interactive"),
                                size=12,
                                color=MUTED,
                            ),
                            pitch,
                        ],
                    ),
                    ft.Column(
                        spacing=4,
                        controls=[
                            ft.Text(
                                tr("form.rating.readonly"),
                                size=12,
                                color=MUTED,
                            ),
                            Rating(value=3, readonly=True),
                        ],
                    ),
                    ft.Column(
                        spacing=4,
                        controls=[
                            ft.Text(
                                tr("form.rating.disabled"),
                                size=12,
                                color=MUTED,
                            ),
                            Rating(value=2, disabled=True),
                        ],
                    ),
                ],
            )
        ],
    )

    segmented = demo_card(
        title=tr("form.segmented.title"),
        hint=tr("form.segmented.hint"),
        icon=ft.Icons.VIEW_WEEK_OUTLINED,
        body=[align_mode],
    )

    dates = demo_card(
        title=tr("form.date.title"),
        hint=tr("form.date.hint"),
        icon=ft.Icons.CALENDAR_MONTH_OUTLINED,
        stretch=True,
        body=[Column(spacing=14, controls=[birthday.ui(), meeting.ui(), checkin.ui()])],
    )

    colors = demo_card(
        title=tr("form.color.title"),
        hint=tr("form.color.hint"),
        icon=ft.Icons.COLOR_LENS_OUTLINED,
        stretch=True,
        body=[
            Column(
                spacing=14,
                controls=[brand_color.ui(), overlay_color.ui(), locked_color.ui()],
            )
        ],
    )

    search_card = demo_card(
        title=tr("form.search.title"),
        hint=tr("form.search.hint"),
        icon=ft.Icons.SEARCH,
        stretch=True,
        body=[panel(search)],
    )

    return doc_page(
        "form",
        [
            demo_grid(
                cell(inputs, span=6),
                cell(checks, span=6),
                cell(switches, span=6),
                cell(radios, span=6),
                cell(selects, span=6),
                cell(sliders, span=6),
                cell(ratings, span=6),
                cell(segmented, span=6),
                cell(dates, span=6),
                cell(colors, span=6),
                cell(search_card, span=12),
            ),
        ],
        badges=[
            Button(
                tr("common.read_values"),
                is_primary=True,
                on_click=dump_values,
            )
        ],
    )
