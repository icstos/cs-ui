import flet as ft
import datetime
from dataclasses import dataclass, field

from ui.input.input import Label

ICON_SIZE = 16
BORDER_RADIUS = 8
DEFAULT_FORM_HEIGHT = 36


def _is_leap_year(year: int) -> bool:
    """判断是否为闰年"""
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


def _get_days_in_month(year: int, month: int) -> int:
    """根据年月获取该月天数，自动处理闰年二月"""
    if month == 2:
        return 29 if _is_leap_year(year) else 28
    if month in (4, 6, 9, 11):
        return 30
    return 31


@ft.observable
@dataclass
class DateInput(Label):
    """基于 flet 的三下拉框日期选择器，遵循 Radio/Checkbox 的 observable 模式。

    自动处理闰年及每月天数，通过 value 属性获取当前日期。
    """

    value: datetime.date | None = None
    year_range: tuple[int, int] = (1900, 2100)

    def __post_init__(self):
        if self.value is None:
            self.value = datetime.date.today()

    def on_change(self, e):
        """由 UI 层的三个下拉框分别触发，通过 e.control 标识来源。"""
        # 此方法由 _on_year_change / _on_month_change / _on_day_change 手动调用
        pass

    @ft.component
    def ui(self):
        today = self.value if self.value else datetime.date.today()
        year, set_year = ft.use_state(today.year)
        month, set_month = ft.use_state(today.month)
        day, set_day = ft.use_state(today.day)

        min_year, max_year = self.year_range
        dd_padding = ft.padding.Padding(left=10, top=6, right=28, bottom=6)

        def _refresh_day_options(
            year_val: int, month_val: int
        ) -> list[ft.dropdown.Option]:
            days = _get_days_in_month(year_val, month_val)
            return [
                ft.dropdown.Option(key=str(d), text=f"{d:02d}")
                for d in range(1, days + 1)
            ]

        def _emit_change():
            self.value = datetime.date(year, month, day)
            self.notify()  # type: ignore[attr-defined]

        def _on_year_change(e):
            set_year(int(e.data))
            # 检查当月天数是否仍然有效
            new_year = int(e.data)
            max_day = _get_days_in_month(new_year, month)
            if day > max_day:
                set_day(max_day)
            self.value = datetime.date(new_year, month, min(day, max_day))
            self.notify()  # type: ignore[attr-defined]

        def _on_month_change(e):
            set_month(int(e.data))
            new_month = int(e.data)
            max_day = _get_days_in_month(year, new_month)
            if day > max_day:
                set_day(max_day)
            self.value = datetime.date(year, new_month, min(day, max_day))
            self.notify()  # type: ignore[attr-defined]

        def _on_day_change(e):
            set_day(int(e.data))
            self.value = datetime.date(year, month, int(e.data))
            self.notify()  # type: ignore[attr-defined]

        day_options = _refresh_day_options(year, month)
        # 如果当前 day 超出范围则修正
        actual_day = min(day, len(day_options))

        year_dd = ft.Dropdown(
            width=88,
            value=str(year),
            options=[
                ft.dropdown.Option(key=str(y), text=str(y))
                for y in range(min_year, max_year + 1)
            ],
            on_select=_on_year_change,
            border_radius=6,
            text_style=ft.TextStyle(size=13),
            content_padding=dd_padding,
        )

        month_dd = ft.Dropdown(
            width=76,
            value=str(month),
            options=[
                ft.dropdown.Option(key=str(m), text=f"{m:02d}") for m in range(1, 13)
            ],
            on_select=_on_month_change,
            border_radius=6,
            text_style=ft.TextStyle(size=13),
            content_padding=dd_padding,
        )

        day_dd = ft.Dropdown(
            width=76,
            value=str(actual_day),
            options=day_options,
            on_select=_on_day_change,
            border_radius=6,
            text_style=ft.TextStyle(size=13),
            content_padding=dd_padding,
        )

        v_ui = ft.Row(
            controls=[
                year_dd,
                ft.Text("年", size=13, color=ft.Colors.ON_SURFACE_VARIANT),
                month_dd,
                ft.Text("月", size=13, color=ft.Colors.ON_SURFACE_VARIANT),
                day_dd,
                ft.Text("日", size=13, color=ft.Colors.ON_SURFACE_VARIANT),
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=3,
        )

        if self.v_label is not None:
            if self.is_vertical:
                return ft.Column(
                    controls=[self.v_label, v_ui],
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                )
            else:
                return ft.Row(controls=[self.v_label, v_ui])
        else:
            return v_ui


@ft.component
def App():
    date_input = DateInput(
        label="选择日期",
        is_required=True,
    )

    date_input_vertical = DateInput(
        label="垂直布局",
        is_vertical=True,
        value=datetime.date(2025, 1, 15),
    )

    return ft.Column(
        controls=[
            date_input.ui(),
            ft.Divider(),
            date_input_vertical.ui(),
            ft.Divider(),
            ft.Button(
                content=ft.Text("打印值"),
                on_click=lambda _: print(
                    f"日期: {date_input.value}, 日期2: {date_input_vertical.value}"
                ),
            ),
        ]
    )


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
