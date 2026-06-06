"""2
Container:

"""

import flet as ft


@ft.control
class Container(ft.Container):
    pass
    # pan_enabled: bool = False
    # scale_enabled: bool = False


@ft.component
def App():
    container = Container(bgcolor=ft.Colors.RED, width=100, height=300, expand=True)

    return ft.Column(
        controls=[
            container,
            ft.Button('ee', on_click=lambda _: print(container.height)),
        ]
    )


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
