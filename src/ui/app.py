import flet as ft
from pathlib import Path

FONT_DIR = Path(Path(__file__).parent, 'data/fonts').resolve()
FONTS = {"AlibabaPuHuiTi": str(Path(FONT_DIR, "AlibabaPuHuiTi-3-55-Regular.otf"))}


@ft.component
def Home():
    return ft.Column(
        controls=[
            ft.Button(
                content="About", on_click=lambda _: ft.context.page.navigate("/about")
            ),
            ft.Text("你好，测试。Welcome home!", size=24),
        ]
    )


@ft.component
def About():
    return ft.Column(
        controls=[
            ft.Button(content="home", on_click=lambda _: ft.context.page.navigate("/")),
            ft.Text("About us", size=24),
        ]
    )


@ft.component
def Contact():
    return ft.Column(controls=[ft.Text("Contact page", size=24)])


@ft.component
def Template():
    outlet = ft.use_route_outlet()

    # page.bgcolor = ft.Colors.GREY_400

    # page.scroll = ft.ScrollMode.AUTO
    # page.spacing = 0
    # page.padding = 0
    # page.scroll = ft.ScrollMode.AUTO

    # page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    # page.vertical_alignment = ft.MainAxisAlignment.START

    # page.window.resizable = True  # 页面缩放
    # # # page.on_resized = lambda _: on_page_resize(_, on_resize)
    # # page.window_full_screen = True
    # page.window.maximizable = True
    # page.window.maximized = True

    # # page.window_always_on_top = True
    # # 最大化
    return ft.View(
        route="/", controls=[ft.Container(content=outlet, expand=True, padding=20)]
    )


@ft.component
def NotFoundView():
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("404", size=90),
                ft.Text("当前页未定义!"),
                ft.Button(
                    "回到首页",
                    width=200,
                    height=40,
                    on_click=lambda _: ft.context.page.navigate("/"),
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.RED_900, color=ft.Colors.WHITE
                    ),
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=ft.Colors.GREY_200,
        padding=20,
        border_radius=10,
    )


class App:
    def __init__(
        self,
        name: str = "CS-UI App",
        host: None | str = None,
        port: int = 0,
        view: None | ft.AppView = ft.AppView.FLET_APP,
        assets_dir: None | str = "assets",
        upload_dir: None | str = None,
        web_renderer: ft.WebRenderer = ft.WebRenderer.AUTO,
        route_url_strategy: ft.RouteUrlStrategy = ft.RouteUrlStrategy.PATH,
        no_cdn: None | bool = False,
        export_asgi_app: None | bool = False,
        target=None,
        route_init='/',  # todo
        route_login='/login',  # todo
    ):
        self.name = name
        self.host = host
        self.port = port
        self.view = view
        self.assets_dir = assets_dir
        self.upload_dir = upload_dir
        self.web_renderer = web_renderer
        self.route_url_strategy = route_url_strategy
        self.no_cdn = no_cdn
        self.export_asgi_app = export_asgi_app
        self.target = target

        self.route = ft.Route(component=Template, outlet=True, children=[])

    @ft.component
    def _app(self):
        # page.vertical_alignment = ft.MainAxisAlignment.CENTER
        # page.bgcolor = ft.Colors.GREY_400
        # page = ft.context.page
        page = ft.context.page
        page.fonts = FONTS
        page.theme_mode = ft.ThemeMode.LIGHT
        page.theme = ft.Theme(
            color_scheme_seed=ft.Colors.BLUE,  # 基于该颜色推导主题其他颜色
            # color_scheme=ft.ColorScheme(    # 从color_scheme_seed派生的material颜色方案
            # ),
            text_theme=ft.TextTheme(),  # 与卡片和画布颜色形成对比的文本样式
            primary_text_theme=ft.TextTheme(),  # 与主色调形成对比的文本主题
            scrollbar_theme=ft.ScrollbarTheme(
                thickness=4,
                radius=10,
                main_axis_margin=5,
                cross_axis_margin=-10,
                track_visibility=False,
                thumb_visibility=False,
                track_color={ft.ControlState.DEFAULT: ft.Colors.TRANSPARENT},
                thumb_color={
                    ft.ControlState.HOVERED: ft.Colors.TRANSPARENT,
                    ft.ControlState.DEFAULT: ft.Colors.TRANSPARENT,
                },
            ),
            # tabs_theme=ft.TabsTheme(),
            font_family="AlibabaPuHuiTi",  # 所有UI元素的基准字体
            use_material3=True,  # use material 2: this setting is mainly for the app-bar's elevation
            page_transitions=ft.PageTransitionsTheme(  # Removing animation on route change.
                android=ft.PageTransitionTheme.NONE,
                ios=ft.PageTransitionTheme.NONE,
                macos=ft.PageTransitionTheme.NONE,
                windows=ft.PageTransitionTheme.NONE,
                linux=ft.PageTransitionTheme.NONE,
            ),
        )
        return ft.Router([self.route], not_found=NotFoundView, manage_views=True)

    def add_route(self, route: ft.Route | list[ft.Route]):
        if isinstance(route, ft.Route):
            route = [route]
        if self.route.children is not None:
            self.route.children.extend(route)
        else:
            print("Error: route.children is None")

    def run(self):
        ft.run(
            lambda page: page.render_views(self._app),
            name=self.name,
            host=self.host,
            port=self.port,
            view=self.view,
            assets_dir=self.assets_dir,
            upload_dir=self.upload_dir,
            web_renderer=self.web_renderer,
            route_url_strategy=self.route_url_strategy,
            no_cdn=self.no_cdn,
            export_asgi_app=self.export_asgi_app,
            target=self.target,
        )


if __name__ == "__main__":
    app = App(name="CS-UI App")
    route = [
        ft.Route(index=True, component=Home),
        ft.Route(path="about", component=About),
        ft.Route(path="contact", component=Contact),
    ]
    app.add_route(route)
    app.run()
