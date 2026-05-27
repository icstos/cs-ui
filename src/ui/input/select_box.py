import flet as ft
from dataclasses import field
# from ui.core.constants import

ICON_SIZE = 18
TEXT_SIZE = 14
PADDING = 10
INPUT_HEIGHT = 36


@ft.control
class SelectBox(ft.Dropdown):
    options: list[ft.DropdownOption | str] = field(default_factory=list)
    dense: bool = True
    filled: bool = True
    editable: bool = True
    # animate_size: int = 5000

    def init(self):
        if len(self.options) > 0 and isinstance(self.options[0], str):
            self._options = [ft.DropdownOption(text=_) for _ in self.options]
            self.options = self._options
        self.content_padding = ft.Padding.only(left=PADDING)

        self.border_color = ft.Colors.GREY_400
        self.bgcolor = ft.Colors.WHITE
        self.border_width = 1
        self.border_radius = 6
        self.focused_border_color = ft.Colors.BLUE
        self.select_icon_enabled_color = ft.Colors.GREY_500
        self.padding = ft.Padding.all(0)
        self.options_fill_horizontally = True


def main(page: ft.Page):
    page.add(SelectBox(options=['Option 1', 'Option 2', 'Option 3']))


if __name__ == '__main__':
    ft.run(main)
