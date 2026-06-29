import flet as ft
from collections.abc import Callable
from ui.core.constants import StyleType, FeedbackStyle
from ui.input.button import Button
from dataclasses import field

# title的container的圆角弧度，需要与原生的AlertDialog的圆角弧度保持一致
BORDER_RADIUS = 12


@ft.control
class AlertDialog(ft.AlertDialog):
    title: ft.Control | str | None = None
    msg: ft.StrOrControl = ""
    on_yes_click: Callable | None = None
    on_no_click: Callable | None = None
    style_type: StyleType = field(default_factory=lambda: StyleType.DEFAULT)

    def init(self):
        self.style = FeedbackStyle(*self.style_type.value)

        self.title_padding = 0
        self.content_padding = 0
        self.actions_padding = ft.Padding.only(right=10, bottom=10)
        self.action_button_padding = ft.Padding.only(
            top=16, bottom=16, right=12, left=12
        )
        self.actions_overflow_button_spacing = 8
        self.inset_padding = 0
        if isinstance(self.title, str):
            self.build_title(self.title)
        if self.content is None:
            self.build_content()
        if len(self.actions) == 0:
            self.build_actions()

        self.actions_alignment = ft.MainAxisAlignment.END
        self.shape = ft.RoundedRectangleBorder(radius=BORDER_RADIUS)

    def build_title(self, title: str):
        self.title = ft.Container(
            ft.Row(
                [ft.Text(title, weight=ft.FontWeight.W_500)],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            bgcolor=ft.Colors.with_opacity(0.5, self.style.color),
            padding=ft.Padding.only(left=16, top=8, bottom=8),
            border_radius=ft.BorderRadius(
                top_left=BORDER_RADIUS,
                top_right=BORDER_RADIUS,
                bottom_left=0,
                bottom_right=0,
            ),
        )

    def build_content(self):
        if self.style is not None and self.msg is not None:
            icon_container = ft.Container(
                content=ft.IconButton(
                    width=30,
                    height=30,
                    icon_size=20,
                    icon=self.style.icon,
                    style=ft.ButtonStyle(
                        color={ft.ControlState.DEFAULT: ft.Colors.WHITE}, padding=0
                    ),
                ),
                bgcolor=self.style.color,
            )
            self.content = ft.Container(
                ft.Row(controls=[icon_container, ft.Text(value=self.msg)], wrap=True)
            )
            if self.style_type == StyleType.DEFAULT:
                icon_container.visible = False
        else:
            self.content = ft.Container(
                ft.Row(controls=[ft.Text(value=self.msg)], wrap=True)
            )
        self.content.padding = ft.Padding.only(left=16, top=12, bottom=12)

    def build_actions(self):
        self.actions = []

        if self.on_no_click is not None:
            self.actions.append(
                Button(content=ft.Text("取消"), height=28, on_click=self._on_no_click)
            )
        if self.on_yes_click is not None:
            self.actions.append(
                Button(
                    content=ft.Text("确认"),
                    height=28,
                    on_click=self._on_yes_click,
                    style_type=StyleType.PRIMARY,
                )
            )

        self.actions_alignment = ft.MainAxisAlignment.END
        self.content.border_radius = ft.BorderRadius(
            top_left=0,
            top_right=0,
            bottom_left=BORDER_RADIUS,
            bottom_right=BORDER_RADIUS,
        )

    def _on_yes_click(self, e):
        if self.on_yes_click is not None:
            self.on_yes_click(e)
        self.open = False
        e.page.update()

    def _on_no_click(self, e):
        if self.on_no_click is not None:
            self.on_no_click(e)
        self.open = False
        e.page.update()

    def show(self, page: ft.Page):
        page.show_dialog(self)

    def close(self, page: ft.Page):
        page.pop_dialog()


def show_alert_dialog(page: ft.Page, alert_dialog: ft.AlertDialog):
    alert_dialog.modal = True
    page.show_dialog(alert_dialog)


@ft.component
def App():
    page = ft.context.page
    default_dialog = AlertDialog(
        title="确认按钮",
        content=ft.Container(
            ft.Text("测试表单内容"),
            # height=400,
            # width=400,
            padding=ft.Padding.only(left=16, top=8, bottom=8),
        ),
        on_yes_click=lambda _: print("yes"),
        on_no_click=lambda _: print("no"),
    )
    primary_dialog = AlertDialog(
        title="primary 弹窗", msg="tessssst", style_type=StyleType.PRIMARY
    )
    success_dialog = AlertDialog(
        title="success 弹窗", msg="tessssst", style_type=StyleType.SUCCESS
    )
    warning_dialog = AlertDialog(
        title="warning 弹窗", msg="tessssst", style_type=StyleType.WARNING
    )
    error_dialog = AlertDialog(
        title="error 弹窗", msg="tessssst", style_type=StyleType.ERROR
    )
    info_dialog = AlertDialog(
        title="info 弹窗", msg="tessssst", style_type=StyleType.INFO
    )

    def test_default_dialog(e):
        default_dialog.show(e.page)

    def test_primary_dialog(e):
        primary_dialog.show(e.page)

    def test_success_dialog(e):
        success_dialog.show(e.page)

    def test_warning_dialog(e):
        warning_dialog.show(e.page)

    def test_error_dialog(e):
        error_dialog.show(e.page)

    def test_info_dialog(e):
        info_dialog.show(e.page)

    default_button = Button(
        content=ft.Text(value="确认按钮"), on_click=test_default_dialog
    )
    primary_button = Button(
        content=ft.Text(value="primary"), on_click=test_primary_dialog
    )
    success_button = Button(
        content=ft.Text(value="success"), on_click=test_success_dialog
    )
    warning_button = Button(
        content=ft.Text(value="warning"), on_click=test_warning_dialog
    )
    error_button = Button(content=ft.Text(value="error"), on_click=test_error_dialog)
    info_button = Button(content=ft.Text(value="info"), on_click=test_info_dialog)

    alert_dialog = AlertDialog(title="Alert", msg="This is an alert dialog")
    return ft.Column(
        controls=[
            Button(
                content="Click me", on_click=lambda e: page.show_dialog(alert_dialog)
            ),
            ft.IconButton(
                ft.Icons.DONE, icon_color=ft.Colors.WHITE, bgcolor=ft.Colors.GREEN
            ),
            default_button,
            primary_button,
            success_button,
            warning_button,
            error_button,
            info_button,
        ]
    )


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
