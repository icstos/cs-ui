import flet as ft
from dataclasses import dataclass
import asyncio


@ft.control
class SearchButton(ft.Button):
    content: ft.StrOrControl = "搜索"
    icon: ft.IconData = ft.Icons.SEARCH


def on_hovered_color(e):
    e.control.style.color = ft.Colors.BLUE if e.data == "true" else ft.Colors.BLACK
    e.control.update()


@ft.observable
@dataclass
class State:
    text: str = "Hello, World!"

    async def on_text_changed(self, text):
        for i in range(len(text)):
            self.text = self.text[:-1] + text[i] + "_"
            await asyncio.sleep(0.1)


@ft.component
def App():
    state, _ = ft.use_state(State())
    dynamic_write_text = ft.Text(state.text)

    async def on_click(e):
        await state.on_text_changed("Hello, Flet!")

    return ft.Column([dynamic_write_text, ft.Button('test', on_click=on_click)])


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
