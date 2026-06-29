"""6
Column:

"""

import flet as ft


@ft.control
class Column(ft.Column):
    pass


@ft.component
def App():
    return Column(controls=[ft.Text("Column control")])


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
