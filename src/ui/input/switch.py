import flet as ft


@ft.control
class Switch(ft.Switch):
    pass


@ft.component
def App():

    return Switch()


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
