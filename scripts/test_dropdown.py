"""
bug from flet: https://github.com/flet-dev/flet/issues/6554
"""

import flet as ft


def main(page: ft.Page):
    page.add(
        ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Dropdown(),
                        ft.Dropdown(dense=True),
                        ft.Dropdown(dense=False),
                        ft.Dropdown(),
                    ]
                ),
                ft.Row(
                    controls=[
                        ft.Dropdown(height=24),
                        ft.Dropdown(height=36),
                        ft.Dropdown(height=48),
                        ft.Dropdown(height=96),
                    ]
                ),
                ft.Row(
                    controls=[
                        ft.Dropdown(
                            menu_height=24,
                            options=[
                                ft.DropdownOption("a", "Style 2A"),
                                ft.DropdownOption("b", "Style 2B"),
                                ft.DropdownOption("c", "Style 2C"),
                            ],
                        ),
                        ft.Dropdown(
                            menu_height=36,
                            options=[
                                ft.DropdownOption("a", "Style 2A"),
                                ft.DropdownOption("b", "Style 2B"),
                                ft.DropdownOption("c", "Style 2C"),
                            ],
                        ),
                        ft.Dropdown(
                            menu_height=48,
                            options=[
                                ft.DropdownOption("a", "Style 2A"),
                                ft.DropdownOption("b", "Style 2B"),
                                ft.DropdownOption("c", "Style 2C"),
                            ],
                        ),
                        ft.Dropdown(
                            menu_height=96,
                            options=[
                                ft.DropdownOption("a", "Style 2A"),
                                ft.DropdownOption("b", "Style 2B"),
                                ft.DropdownOption("c", "Style 2C"),
                            ],
                        ),
                        ft.Dropdown(
                            menu_height=200,
                            options=[
                                ft.DropdownOption("a", "Style 2A"),
                                ft.DropdownOption("b", "Style 2B"),
                                ft.DropdownOption("c", "Style 2C"),
                            ],
                        ),
                    ]
                ),
            ]
        )
    )


if __name__ == '__main__':
    ft.run(main)
