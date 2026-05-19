import flet as ft


@ft.control("Slider")
class Slider(ft.BaseControl):
    def __init__(
        self,
        value: float = 0.0,
        min_value: float = 0.0,
        max_value: float = 1.0,
        divisions: int | None = None,
        label: str | None = None,
        width=None,
        on_change=None,
    ):
        super().__init__()
        self.value = value
        self.min_value = min_value
        self.max_value = max_value
        self.divisions = divisions
        self.label = label
        self.width = width
        self.on_change = on_change

    def build(self):
        return ft.Slider(
            value=self.value,
            min=self.min_value,
            max=self.max_value,
            divisions=self.divisions,
            label=self.label,
            on_change=self.on_change,
        )


def main(page: ft.Page):
    page.title = "Slider Demo"
    page.add(
        Slider(
            value=30,
            min_value=0,
            max_value=100,
            divisions=10,
            label="滑块值",
            width=320,
            on_change=lambda e: page.add(
                ft.Text(f"值：{e.control.value}", color="green")
            ),
        )
    )


if __name__ == "__main__":
    ft.run(main)
