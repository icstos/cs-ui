import flet as ft


@ft.control
class Chip(ft.Chip):
    text: ft.StrOrControl | None = None
    label: ft.StrOrControl | None = None
    selected_color: ft.Colors = ft.Colors.GREEN
    selected: bool = False

    def init(self):
        self.label = self.label or self.text
        if self.label and isinstance(self.label, str):
            if self.selected:
                self.label = ft.Text(self.label, color=ft.Colors.WHITE)
            else:
                self.label = ft.Text(self.label, color=ft.Colors.BLACK)

        self.on_click = self.on_click or self._on_click
        self.check_color = ft.Colors.WHITE

    def _on_click(self, e):
        self.selected = not self.selected
        self._update_color()

    def _update_color(self):
        if isinstance(self.label, ft.Text):
            if self.selected:
                self.label.color = ft.Colors.WHITE
            else:
                self.label.color = ft.Colors.BLACK


def main(page: ft.Page):
    page.add(
        Chip(label="Chip 1", selected=True), Chip(label="Chip 2"), Chip(label="Chip 3")
    )


if __name__ == "__main__":
    ft.run(main)
