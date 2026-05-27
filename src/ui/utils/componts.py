import flet as ft
import asyncio


@ft.control
class DynamicWriteText(ft.Text):
    async def write(self, text):
        print('???')
        for i in range(len(text)):
            self.value = self.value[:-1] + text[i] + "_"
            await asyncio.sleep(0.1)
            await self.update()


def main(page: ft.Page):

    dynamic_write_text = DynamicWriteText()
    page.add(dynamic_write_text)
    page.add(
        ft.Button('test', on_click=lambda _: dynamic_write_text.write("Hello, World!"))
    )


if __name__ == "__main__":
    ft.run(main)
