import flet as ft

def main(page: ft.Page):
    page.title = "Test"
    page.add(ft.Text("Hello World", size=30))
    page.add(ft.Button("Click me"))

ft.run(main)