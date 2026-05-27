import flet as ft
import datetime
from collections.abc import Callable


def is_leap_year(year: int) -> bool:
    """判断是否为闰年"""
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


def get_days_in_month(year: int, month: int) -> int:
    """根据年月获取该月天数，自动处理闰年二月"""
    if month == 2:
        return 29 if is_leap_year(year) else 28
    if month in (4, 6, 9, 11):
        return 30
    return 31


class DateInput(ft.Container):
    """
    基于 Flet 的三下拉框日期选择器。
    - 年 / 月 / 日均使用 Dropdown
    - 自动处理闰年及每月天数
    - date 属性获取当前日期，on_change 回调通知变更
    """

    def __init__(
        self,
        on_change: Callable | None = None,
        initial_date: datetime.date | None = None,
        year_range: tuple[int, int] = (1900, 2100),
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.on_change_callback = on_change

        today = initial_date if initial_date else datetime.date.today()
        self.selected_year = today.year
        self.selected_month = today.month
        self.selected_day = today.day

        min_year, max_year = year_range
        dd_padding = ft.padding.Padding(left=10, top=6, right=28, bottom=6)

        self.year_dd = ft.Dropdown(
            width=88,
            value=str(self.selected_year),
            options=[
                ft.dropdown.Option(key=str(y), text=str(y))
                for y in range(min_year, max_year + 1)
            ],
            on_select=self._on_year_change,
            border_radius=6,
            text_style=ft.TextStyle(size=13),
            content_padding=dd_padding,
        )

        self.month_dd = ft.Dropdown(
            width=76,
            value=str(self.selected_month),
            options=[
                ft.dropdown.Option(key=str(m), text=f"{m:02d}") for m in range(1, 13)
            ],
            on_select=self._on_month_change,
            border_radius=6,
            text_style=ft.TextStyle(size=13),
            content_padding=dd_padding,
        )

        self.day_dd = ft.Dropdown(
            width=76,
            on_select=self._on_day_change,
            border_radius=6,
            text_style=ft.TextStyle(size=13),
            content_padding=dd_padding,
        )
        self._refresh_day_options()

        self.content = ft.Row(
            controls=[
                self.year_dd,
                ft.Text("年", size=13, color=ft.Colors.ON_SURFACE_VARIANT),
                self.month_dd,
                ft.Text("月", size=13, color=ft.Colors.ON_SURFACE_VARIANT),
                self.day_dd,
                ft.Text("日", size=13, color=ft.Colors.ON_SURFACE_VARIANT),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=3,
        )

        self.padding = ft.padding.Padding(left=16, top=12, right=16, bottom=12)
        self.border_radius = 12
        self.bgcolor = ft.Colors.SURFACE
        self.border = ft.border.Border(
            left=ft.border.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
            top=ft.border.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
            right=ft.border.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
            bottom=ft.border.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
        )

    # ── 内部方法 ──────────────────────────────────────────

    def _refresh_day_options(self):
        days = get_days_in_month(self.selected_year, self.selected_month)
        self.day_dd.options = [
            ft.dropdown.Option(key=str(d), text=f"{d:02d}") for d in range(1, days + 1)
        ]
        if self.selected_day > days:
            self.selected_day = days
        self.day_dd.value = str(self.selected_day)

    def _on_year_change(self, e):
        self.selected_year = int(self.year_dd.value)
        self._refresh_day_options()
        self.day_dd.update()
        self._emit_change()

    def _on_month_change(self, e):
        self.selected_month = int(self.month_dd.value)
        self._refresh_day_options()
        self.day_dd.update()
        self._emit_change()

    def _on_day_change(self, e):
        self.selected_day = int(self.day_dd.value)
        self._emit_change()

    def _emit_change(self):
        if self.on_change_callback:
            self.on_change_callback(self.date)

    # ── 公共接口 ──────────────────────────────────────────

    @property
    def date(self) -> datetime.date:
        return datetime.date(self.selected_year, self.selected_month, self.selected_day)


# ══════════════════════════════════════════════════════════════
#  示例应用
# ══════════════════════════════════════════════════════════════


def main(page: ft.Page):
    page.title = "日期选择器"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.padding = 32
    page.bgcolor = ft.Colors.SURFACE_CONTAINER_LOWEST

    output = ft.Text(size=15, color=ft.Colors.ON_SURFACE_VARIANT)

    picker = DateInput(
        on_change=lambda d: setattr(output, "value", f"📅 {d.strftime('%Y-%m-%d')}")
    )

    def on_confirm(_):
        output.value = f"📅 已选择: {picker.date.strftime('%Y-%m-%d')}"
        output.color = ft.Colors.PRIMARY
        output.size = 18
        output.weight = ft.FontWeight.BOLD
        page.update()

    page.add(
        ft.Text(
            "选择日期", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE
        ),
        ft.Divider(height=16, color=ft.Colors.TRANSPARENT),
        picker,
        ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
        ft.Button(
            "确认",
            on_click=on_confirm,
            icon=ft.Icons.CHECK,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=ft.padding.Padding(left=32, top=12, right=32, bottom=12),
            ),
        ),
        ft.Divider(height=16, color=ft.Colors.TRANSPARENT),
        output,
    )


if __name__ == "__main__":
    ft.run(main)
