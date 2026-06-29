import flet as ft
from dataclasses import field
import flet_code_editor as fce

Text = ft.Text


@ft.control
class Header_1(ft.Text):
    theme_style: ft.TextThemeStyle = ft.TextThemeStyle.DISPLAY_SMALL
    weight: ft.FontWeight = ft.FontWeight.BOLD


Title = Header_1
Header = Header_1


@ft.control
class Header_2(ft.Text):
    theme_style: ft.TextThemeStyle = ft.TextThemeStyle.HEADLINE_LARGE
    weight: ft.FontWeight = ft.FontWeight.BOLD


SubTitle = Header_2
SubHeader = Header_2


@ft.control
class Header_3(ft.Text):
    theme_style: ft.TextThemeStyle = ft.TextThemeStyle.HEADLINE_MEDIUM
    weight: ft.FontWeight = ft.FontWeight.W_500


@ft.control
class Header_4(ft.Text):
    theme_style: ft.TextThemeStyle = ft.TextThemeStyle.HEADLINE_SMALL
    weight: ft.FontWeight = ft.FontWeight.W_500


@ft.control
class Header_5(ft.Text):
    theme_style: ft.TextThemeStyle = ft.TextThemeStyle.TITLE_LARGE
    weight: ft.FontWeight = ft.FontWeight.W_500


@ft.control
class Quote(ft.Text):
    bgcolor: ft.Colors = ft.Colors.BLUE_300


@ft.control
class Link(ft.Text):
    color: ft.Colors = ft.Colors.BLUE
    style: ft.TextStyle = field(
        default_factory=lambda: ft.TextStyle(
            decoration=ft.TextDecoration.UNDERLINE, decoration_color=ft.Colors.BLUE
        )
    )
    link: str | None = None

    def on_tap(self, e: ft.TapEvent):
        if self.link:
            import webbrowser

            webbrowser.open(self.link)


@ft.control
class Code(fce.CodeEditor):
    language: fce.CodeLanguage = fce.CodeLanguage.PYTHON
    code_theme: fce.CodeTheme = fce.CodeTheme.ATOM_ONE_LIGHT
    read_only: bool = True


@ft.control
class Markdown(ft.Markdown):
    selectable: bool = True
    extension_set: ft.MarkdownExtensionSet = ft.MarkdownExtensionSet.GITHUB_WEB
    code_theme = ft.MarkdownCodeTheme.MONOKAI


@ft.control
class Json(fce.CodeEditor):
    language: fce.CodeLanguage = fce.CodeLanguage.JSON
    code_theme: fce.CodeTheme = fce.CodeTheme.ATOM_ONE_LIGHT
    read_only: bool = True
    line_numbers: bool = False


@ft.component
def App():
    return ft.Column(
        controls=[
            Header_1("Header 1"),
            Header_2("Header 2"),
            Header_3("Header 3"),
            Header_4("Header 4"),
            Header_5("Header 5"),
            Text("text"),
            Quote("Quote"),
            Link("Link", link="https://www.baidu.com/"),
            Markdown(
                "# Markdown\n## Markdown\n### Markdown\n#### Markdown\n##### Markdown\n###### Markdown\n- Markdown\n- Markdown\n- Markdown\n[Markdown](https://www.baidu.com/)"
            ),
            Json(
                value='{"name": "cs_ui", "version": "0.1.0", "description": "A UI library for Python."}'
            ),
            Code(
                value="""{"name": "cs_ui",
"version": "0.1.0",
"description": "A UI library for Python."}
                """,
                language=fce.CodeLanguage.JSON,
            ),
        ]
    )


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
