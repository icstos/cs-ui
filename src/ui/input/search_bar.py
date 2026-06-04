import flet as ft
from dataclasses import field
from collections.abc import Callable


@ft.control
class SearchBar(ft.SearchBar):
    options: list[str] = field(default_factory=list)
    on_click: Callable | None = None

    def init(self):
        for _ in self.options:
            self.controls.append(
                ft.ListTile(title=ft.Text(_), on_click=self.on_click, data=_)
            )


@ft.component
def App():

    return SearchBar(options=["Option 1", "Option 2", "Option 3"])


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
