import flet as ft


@ft.control
class Expander(ft.ExpansionTile):
    title: ft.StrOrControl | ft.Container
    dense: bool | None = None
    affinity: ft.TileAffinity = ft.TileAffinity.PLATFORM
    bgcolor: ft.Colors = ft.Colors.BLUE_200
    collapsed_bgcolor: ft.Colors = ft.Colors.BLUE_100
    expanded_cross_axis_alignment: ft.CrossAxisAlignment = ft.CrossAxisAlignment.START

    def init(self):
        if isinstance(self.title, str):
            self.title = ft.Container(ft.Text(self.title), on_hover=self.handle_hover)
        if isinstance(self.subtitle, str):
            self.subtitle = ft.Container(ft.Text(self.subtitle))
        else:
            self.subtitle = ft.Container(self.subtitle)
        if self.controls is not None:
            self.controls = [
                ft.Container(
                    ft.Column(
                        controls=self.controls,
                        spacing=0,
                        alignment=ft.MainAxisAlignment.START,
                        horizontal_alignment=ft.CrossAxisAlignment.START,
                        expand=True,
                    ),
                    bgcolor=ft.Colors.WHITE,
                    expand=True,
                    alignment=ft.Alignment.TOP_LEFT,
                    padding=ft.Padding.only(left=16),
                )
            ]

    def handle_hover(self, e):
        # if isinstance(self.title, ft.Container):
        #     self.title.bgcolor = ft.Colors.BLUE_200 if e.data else ft.Colors.BLUE_100
        # if self.subtitle is not None and isinstance(self.subtitle, ft.Container):
        #     self.subtitle.bgcolor = ft.Colors.BLUE_200 if e.data else ft.Colors.BLUE_100
        self.bgcolor = ft.Colors.BLUE_300 if e.data else ft.Colors.BLUE_200


def main(page: ft.Page):
    page.add(
        Expander(
            title="Expander control",
            controls=[
                ft.Text("This is the content of the expander."),
                ft.Text("You can add any controls here."),
            ],
        )
    )


if __name__ == "__main__":
    ft.run(main)
