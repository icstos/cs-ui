from dataclasses import dataclass
from typing import cast

import flet as ft


@dataclass
@ft.observable
class Form:
    name: str = ""

    def set_name(self, value):
        self.name = value

    async def submit(self, e: ft.Event[ft.Button]):
        e.page.show_dialog(
            ft.AlertDialog(
                title="Hello",
                content=ft.Text(f"Hello, {self.name}!"),
            )
        )

    async def reset(self):
        self.name = ""


@ft.component
def App():
    form, _ = ft.use_state(Form())

    return [
        input := ft.TextField(
            label="Your name",
            value=form.name,
            on_change=lambda e: form.set_name(e.control.value),
        ),
        ft.Row(
            cast(
                list[ft.Control],
                [
                    ft.FilledButton("Submit", on_click=form.submit),
                    ft.FilledTonalButton("Reset", on_click=form.reset),
                    ft.FilledTonalButton(
                        "print", on_click=lambda _: print(input.value)
                    ),
                ],
            )
        ),
    ]


ft.run(lambda page: page.render(App))
