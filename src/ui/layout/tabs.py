"""9
Tabs:

"""

import flet as ft


@ft.control
class Tabs(ft.Tabs):
    label_color: ft.Colors = ft.Colors.BLUE
    indicator_color: ft.Colors = ft.Colors.BLUE
    unselected_label_color: ft.Colors = ft.Colors.GREY_500


@ft.control
class TabBar(ft.TabBar):
    pass


@ft.control
class Tab(ft.Tab):
    text: str | ft.Control = ''
    content: ft.Control | None = None

    def init(self):
        self.label = self.label or self.text


@ft.control
class TabBarView(ft.TabBarView):
    def init(self):
        self.height = self.height or 1000


def main(page: ft.Page):
    page.title = 'Tabs'
    page.add(
        Tabs(
            length=3,
            content=ft.Column(
                controls=[
                    TabBar(
                        tabs=[Tab(text='Tab 1'), Tab(text='Tab 2'), Tab(text='Tab 3')]
                    ),
                    TabBarView(
                        controls=[
                            ft.Text('Content of Tab 1'),
                            ft.Text('Content of Tab 2'),
                            ft.Text('Content of Tab 3'),
                        ],
                        height=800,
                    ),
                ]
            ),
        )
    )


if __name__ == '__main__':
    ft.run(main)
