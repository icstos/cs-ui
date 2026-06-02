from dataclasses import dataclass
from enum import Enum
import flet as ft
from ui.core.constants import LayoutType


@ft.control
class Radio(ft.RadioGroup):
    content: ft.Control | None = None
    options: list | None = None
    radio_layout_type: LayoutType = LayoutType.HORIZONTAL

    def init(self):
        self.update_options(self.options or [])

    def update_options(self, options: list[str | ft.Radio]):
        self._options = []
        for idx, _ in enumerate(options):
            if isinstance(_, str):
                self._options.append(
                    ft.Radio(
                        label=_,
                        value=_,
                        label_position=ft.LabelPosition.RIGHT,
                        active_color=ft.Colors.BLUE,
                    )
                )
            else:
                self._options.append(_)
        if self.radio_layout_type == LayoutType.HORIZONTAL:
            self.content = ft.Row(controls=self._options)
        else:
            self.content = ft.Column(controls=self._options, spacing=2, run_spacing=10)


@ft.component
def App():

    return Radio(
        options=["aa", "bb", "cc"], on_change=lambda e: print(f"Selected: {e.data}")
    )


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
