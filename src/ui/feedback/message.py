import flet as ft
from ui.core.constants import StyleType, FeedbackStyle
from dataclasses import field


@ft.control
class Message(ft.SnackBar):
    content: ft.StrOrControl = ''
    style_type: StyleType = field(default_factory=lambda: StyleType.DEFAULT)
    persist: bool = False
    show_close_icon: bool = True

    def init(self):
        self.set_theme(style_type=self.style_type)
        self.set_content(content=self.content)

    def set_theme(self, style_type):
        self.style = FeedbackStyle(*style_type.value)
        if style_type == StyleType.DEFAULT:
            self.bgcolor = ft.Colors.GREY_600
        else:
            self.bgcolor = self.style.color
        self.accent_color = self.style.color_accent
        self.icon = self.style.icon
        self.close_icon_color = ft.Colors.WHITE

    def set_content(self, content):
        if isinstance(content, str):
            self.content = ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Icon(self.icon, color=ft.Colors.WHITE),
                        bgcolor=self.bgcolor,
                    ),
                    ft.Text(content, color=ft.Colors.WHITE),
                ]
            )
        else:
            self.content = content

    def show(self, content: ft.StrOrControl | None = None, style_type=None, page=None):
        ft.context.page.pop_dialog()
        if style_type is not None:
            self.set_theme(style_type=style_type)
        if content is not None:
            self.set_content(content=content)
        ft.context.page.show_dialog(self)


@ft.component
def App():
    def click_default(e):
        Message(content='test').show()

    def click_primary(e):
        Message(content='test', style_type=StyleType.PRIMARY).show()

    def click_info(e):
        Message(content='test', style_type=StyleType.INFO).show()

    def click_success(e):
        Message(content='test', style_type=StyleType.SUCCESS).show()

    def click_error(e):
        Message(content='test', style_type=StyleType.ERROR).show()

    def click_warning(e):
        Message(content='test', style_type=StyleType.WARNING).show()

    return ft.Column(
        controls=[
            ft.Button(
                content=ft.Text(value='show default message'),
                on_click=click_default,
            ),
            ft.Button(
                content=ft.Text(value='show primary message'),
                on_click=click_primary,
            ),
            ft.Button(content=ft.Text(value='show info message'), on_click=click_info),
            ft.Button(
                content=ft.Text(value='show success message'),
                on_click=click_success,
            ),
            ft.Button(
                content=ft.Text(value='show error message'), on_click=click_error
            ),
            ft.Button(
                content=ft.Text(value='show warning message'),
                on_click=click_warning,
            ),
        ]
    )


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
