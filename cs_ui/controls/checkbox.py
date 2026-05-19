import flet as ft


@ft.control("Checkbox")
class Checkbox(ft.BaseControl):
    def __init__(
        self,
        label: str = "",
        value: bool = False,
        on_change=None,
        disabled: bool = False,
    ):
        super().__init__()
        self.label = label
        self.value = value
        self.on_change = on_change
        self.disabled = disabled

    def build(self):
        return ft.Checkbox(
            label=self.label,
            value=self.value,
            on_change=self.on_change,
            disabled=self.disabled,
        )


def main(page: ft.Page):
    page.title = "Checkbox Demo"
    page.add(
        Checkbox(
            label="示例复选框",
            on_change=lambda e: page.add(
                ft.Text(f"状态：{e.control.value}", color="green")
            ),
        )
    )


if __name__ == "__main__":
    ft.run(main)
