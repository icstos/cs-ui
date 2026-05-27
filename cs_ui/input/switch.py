import flet as ft


@ft.control
class Switch(ft.Switch):
    pass


def main(page: ft.Page):
    page.add(Switch())


if __name__ == "__main__":
    ft.run(main)
