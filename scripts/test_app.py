import ui


@ui.component
def Home():
    return ui.Column(
        controls=[
            ui.Button(
                content="About", on_click=lambda _: ui.context.page.navigate("/about")
            ),
            ui.Text("你好，测试。Welcome home!", size=24),
        ]
    )


if __name__ == "__main__":
    app = ui.App(name="cstos")

    route = ui.Route(index=True, component=Home)
    app.add_route(route)
    app.run()
