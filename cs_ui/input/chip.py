import flet as ft


@ft.control
class Chip(ft.Chip):
    selected_color: ft.Colors = ft.Colors.GREEN
    selected: bool = False

    def init(self):
        if self.label and isinstance(self.label, str):
            self.label = ft.Text(self.label)
        self.on_click = self.on_click or self._on_click
        self.check_color = ft.Colors.WHITE

    def did_mount(self):
        self._update_color()

    def _on_click(self, e):
        self.selected = not self.selected
        self._update_color()
        self.update()

    def _update_color(self):
        if isinstance(self.label, ft.Text):
            if self.selected:
                self.label.color = ft.Colors.WHITE
            else:
                self.label.color = ft.Colors.BLACK

        self.update()


def main(page: ft.Page):
    page.add(
        Chip(label="Chip 1", selected=True), Chip(label="Chip 2"), Chip(label="Chip 3")
    )


if __name__ == "__main__":
    ft.run(main)
