import flet as ft


@ft.control("Switch")
class Switch(ft.BaseControl):
    def __init__(
        self, label: str = "", value: bool = False, on_change=None, active_color=None
    ):
        super().__init__()
        self.label = label
        self.value = value
        self.on_change = on_change
        self.active_color = active_color

    def build(self):
        return ft.Switch(
            label=self.label,
            value=self.value,
            on_change=self.on_change,
            active_color=self.active_color,
        )


def main(page: ft.Page):
    page.title = "Switch Demo"
    page.add(
        Switch(
            label="开关示例",
            value=False,
            on_change=lambda e: page.add(
                ft.Text(f"开关状态：{e.control.value}", color="green")
            ),
            active_color="#1f6feb",
        )
    )


if __name__ == "__main__":
    ft.run(main)
