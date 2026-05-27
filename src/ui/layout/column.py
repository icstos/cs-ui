"""6
Column:

"""

import flet as ft


@ft.control
class Column(ft.Column):
    pass


def main(page: ft.Page):
    page.add(Column(controls=[ft.Text("Column control")]))


if __name__ == '__main__':
    ft.run(main)
