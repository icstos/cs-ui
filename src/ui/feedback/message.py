import flet as ft
from ui.core.constants import StyleType, FeedbackStyle
from ui.core.snackbar import ensure_snackbar_content
from dataclasses import field


@ft.control
class Message(ft.SnackBar):
    content: ft.StrOrControl = ""
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
        # 拦住 content=ft.Page：它会与 page._dialogs 构成环形引用，
        # 配置控件树时永不终止，最终在随机位置抛 RecursionError。
        ensure_snackbar_content(content, where="Message")
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

    def show(
        self,
        content: ft.StrOrControl | None = None,
        *,
        style_type: StyleType | None = None,
        page: ft.Page | None = None,
    ) -> None:
        """显示消息，并先收起当前最上层的弹层。

        Args:
            content: 临时替换的提示内容（``str`` 或控件）。**不要**把 ``page``
                传在这个位置 —— ``content`` 才是第一个位置参数，写成
                ``.show(page)`` 会与 ``page._dialogs`` 构成环形引用并抛
                ``RecursionError``；目标页面请用 ``page=`` 传。
            style_type: 临时覆盖的语义类型。
            page: 目标页面，默认取当前上下文页。
        """
        # 注意：page 以前是"声明了但没用"的死参数，这里修好——否则
        # Message(...).show(page) 只能把页面错误地绑到 content 上。
        page = page or ft.context.page
        page.pop_dialog()
        if style_type is not None:
            self.set_theme(style_type=style_type)
        if content is not None:
            self.set_content(content=content)
        page.show_dialog(self)


@ft.component
def App():
    def click_default(e):
        Message(content="test").show()

    def click_primary(e):
        Message(content="test", style_type=StyleType.PRIMARY).show()

    def click_info(e):
        Message(content="test", style_type=StyleType.INFO).show()

    def click_success(e):
        Message(content="test", style_type=StyleType.SUCCESS).show()

    def click_error(e):
        Message(content="test", style_type=StyleType.ERROR).show()

    def click_warning(e):
        Message(content="test", style_type=StyleType.WARNING).show()

    return ft.Column(
        controls=[
            ft.Button(
                content=ft.Text(value="show default message"),
                on_click=click_default,
            ),
            ft.Button(
                content=ft.Text(value="show primary message"),
                on_click=click_primary,
            ),
            ft.Button(content=ft.Text(value="show info message"), on_click=click_info),
            ft.Button(
                content=ft.Text(value="show success message"),
                on_click=click_success,
            ),
            ft.Button(
                content=ft.Text(value="show error message"), on_click=click_error
            ),
            ft.Button(
                content=ft.Text(value="show warning message"),
                on_click=click_warning,
            ),
        ]
    )


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
