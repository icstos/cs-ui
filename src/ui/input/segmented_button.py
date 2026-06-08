import flet as ft


@ft.control
class Segment(ft.Segment):
    def init(self):
        if self.label is None:
            self.label = ft.Text(value=self.value)


@ft.control
class SegmentedButton(ft.SegmentedButton):
    segments: list[Segment] | None = None
    options: list[str | Segment] | None = None
    selected_icon: ft.Control = ft.Icon(icon=ft.Icons.CHECK, color=ft.Colors.WHITE)
    allow_multiple_selection: bool = True
    allow_empty_selection: bool = True

    def init(self):
        self.selected_icon = self.selected_icon or ft.Icon(
            icon=ft.Icons.CHECK, color=ft.Colors.WHITE
        )
        if self.options is not None:
            self.segments = [Segment(_) for _ in self.options]
        self.style = ft.ButtonStyle(
            color={ft.ControlState.SELECTED: ft.Colors.WHITE},
            bgcolor={
                ft.ControlState.DEFAULT: ft.Colors.WHITE,
                ft.ControlState.SELECTED: ft.Colors.BLUE,
            },
            shape={
                ft.ControlState.DEFAULT: ft.RoundedRectangleBorder(radius=6),
                ft.ControlState.SELECTED: ft.RoundedRectangleBorder(radius=6),
            },
            side={
                ft.ControlState.SELECTED: ft.BorderSide(color=ft.Colors.WHITE),
            },
        )


# def main(page: ft.Page):
#     tmp =
#     page.add(tmp)
#     print(tmp.allow_multiple_selection)
#     print(tmp.allow_empty_selection)


# if __name__ == "__main__":
#     ft.run(main)
@ft.component
def App():

    return SegmentedButton(
        options=["Option 1", "Option 2", "Option 3"],
        selected_icon=ft.Icon(icon=ft.Icons.CHECK, color=ft.Colors.WHITE),
    )


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
