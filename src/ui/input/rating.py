import flet as ft
from collections.abc import Callable


@ft.control
class Rating(ft.Row):
    value: int | None = None
    elements: int = 5
    readonly: bool = False
    disabled: bool = False
    on_change: Callable | None = None

    def init(self):
        self.value = self.value - 1 if self.value is not None else self.value
        self.on_change = self.on_change or (lambda x: None)
        self.row_elements: list[ft.IconButton] = []
        self.references: list[ft.Ref] = []
        self._add_elements()
        self.controls = self.row_elements  # type: ignore
        self.spacing = 0

    def _add_elements(self):
        for i in range(0, self.elements):
            element_ref = ft.Ref[ft.IconButton]()
            self.references.append(element_ref)
            is_selected = True if self.value is not None and i <= self.value else False
            self.row_elements.append(
                ft.IconButton(
                    icon=ft.Icons.STAR_BORDER,
                    ref=element_ref,
                    icon_color=ft.Colors.GREY,
                    selected_icon=ft.Icons.STAR,
                    selected_icon_color=ft.Colors.GREY
                    if self.disabled
                    else ft.Colors.BLUE,
                    data=i,
                    selected=is_selected,
                    disabled=self.disabled,
                    on_click=self._select,
                )
            )

    def _reset(self, e):
        if self.readonly:
            return
        for i in range(self.elements - 1, -1, -1):
            ref: ft.Ref[ft.IconButton] = self.references[i]
            ref.current.selected = False
            self.value = None
        self.update()

    def _select(self, e):
        if self.readonly:
            return

        if self.value is not None and e.control.data == self.value:
            self._reset(e)
        else:
            for i in range(self.elements - 1, -1, -1):
                if e.control.data >= i:
                    ref: ft.Ref[ft.IconButton] = self.references[i]
                    ref.current.selected = True
                else:
                    ref: ft.Ref[ft.IconButton] = self.references[i]
                    ref.current.selected = False
            self.value = e.control.data
        self._on_change(self.value)
        self.update()

    def _on_change(self, e) -> None:
        if e is not None:
            self.on_change(e + 1)
        else:
            self.on_change(0)


def main(page: ft.Page):
    def handle_change(value):
        print("Selected rating:", value)

    page.add(Rating(on_change=handle_change))


if __name__ == "__main__":
    ft.run(main)
