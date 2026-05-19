import flet as ft


@ft.control("TextField")
class TextField(ft.BaseControl):
    def __init__(
        self,
        value: str = "",
        label: str | None = None,
        hint_text: str | None = None,
        width=None,
        password: bool = False,
        on_change=None,
        on_submit=None,
    ):
        super().__init__()
        self.value = value
        self.label = label
        self.hint_text = hint_text
        self.password = password
        self.width = width
        self.on_change = on_change
        self.on_submit = on_submit

    def build(self):
        return ft.TextField(
            value=self.value,
            label=self.label,
            hint_text=self.hint_text,
            password=self.password,
            on_change=self.on_change,
            on_submit=self.on_submit,
            width=self.width,
        )


def main(page: ft.Page):
    page.title = "TextField Demo"
    page.add(
        TextField(
            label="输入内容",
            hint_text="按回车提交",
            width=320,
            on_submit=lambda e: page.add(
                ft.Text(f"提交内容：{e.control.value}", color="green")
            ),
        )
    )


if __name__ == "__main__":
    ft.run(main)
