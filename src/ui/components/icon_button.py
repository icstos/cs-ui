import flet as ft


@ft.component
def theme_toggle_button() -> ft.IconButton:

    is_dark, set_theme_mode = ft.use_state(False)
    if is_dark:
        ft.context.page.theme_mode = ft.ThemeMode.DARK
        return ft.IconButton(
            icon=ft.Icons.BRIGHTNESS_2,
            tooltip="Dark Mode",
            on_click=lambda: set_theme_mode(not is_dark),
        )
    else:
        ft.context.page.theme_mode = ft.ThemeMode.LIGHT
        return ft.IconButton(
            icon=ft.Icons.BRIGHTNESS_HIGH,
            tooltip="Light Mode",
            on_click=lambda: set_theme_mode(not is_dark),
        )


if __name__ == "__main__":
    ft.run(lambda page: page.render(theme_toggle_button))
