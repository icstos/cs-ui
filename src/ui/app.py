import traceback
from importlib.util import module_from_spec, spec_from_file_location
from inspect import getmembers
from pathlib import Path

import flet as ft

from ui.core.config import logger
from ui.core.i18n import t, use_t
from ui.core.theme import apply_theme, theme_state
from ui.core.tokens import FONT_SIZE, RADIUS

FONT_DIR = Path(Path(__file__).parent, "data/fonts").resolve()
FONTS = {"AlibabaPuHuiTi": str(Path(FONT_DIR, "AlibabaPuHuiTi-3-55-Regular.otf"))}

@ft.component
def Home():
    return ft.Column(
        controls=[
            ft.Button(
                content="About", on_click=lambda _: ft.context.page.navigate("/about")
            ),
            ft.Text("Welcome home", size=FONT_SIZE["headline_lg"]),
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

    # 注意：这里返回普通控件而不是 ft.View。根视图模式（page.render +
    # Router(manage_views=False)）下，View 被当成普通控件渲染会让整页变灰块
    # （Flutter 抛 Bad state: No element）。而这正是为了让页面浮层
    # （page.overlay / show_dialog）可用的唯一路径，详见 ui.core.float_layer。
    return ft.Container(content=outlet, expand=True, padding=20)


@ft.component
def NotFoundView():
    use_t()  # 订阅语言：用户切语言时这一页也要跟着变
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("404", size=90),
                ft.Text(t("ui.app.not_found")),
                ft.Button(
                    t("ui.app.back_home"),
                    width=200,
                    height=40,
                    on_click=lambda _: ft.context.page.navigate("/"),
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.PRIMARY, color=ft.Colors.ON_PRIMARY
                    ),
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=ft.Colors.SURFACE_CONTAINER,
        padding=20,
        border_radius=RADIUS["lg"],
    )


def set_app():
    page = ft.context.page

    # page.scroll = ft.ScrollMode.AUTO
    # page.spacing = 0
    # page.padding = 0
    # page.scroll = ft.ScrollMode.AUTO

    # page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    # page.vertical_alignment = ft.MainAxisAlignment.START

    page.window.resizable = True  # 页面缩放
    # # page.on_resized = lambda _: on_page_resize(_, on_resize)
    # page.window_full_screen = True
    page.window.maximizable = True
    page.window.maximized = True

    # # page.window_always_on_top = True


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
        with_auto_routing=True,
        route_init="/",  # todo
        route_login="/login",  # todo
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

        self.with_auto_routing = with_auto_routing
        self.route = ft.Route(component=Template, outlet=True, children=[])

    @ft.component
    def _app(self):
        # page.vertical_alignment = ft.MainAxisAlignment.CENTER
        # page = ft.context.page
        page = ft.context.page
        page.title = self.name
        page.fonts = FONTS
        # 主题**不再在这里手搓一份**。手搓的那份少了 surfaces / 输入框 / 弹出菜单
        # 的主题，于是同一个应用里"框架按钮"和"flet 按钮"、"框架下拉"和
        # "flet 下拉"各是一套配色 —— 正是"组件与框架不和谐"的来源。
        # 全部交给 ui.core.theme：那里是主题的唯一事实源。apply_theme 会同时
        # 写下明暗两套主题 —— 只写 page.theme 的话，深色模式没有为深色准备的
        # 那棵树，Flutter 会把浅色色板硬套上去。
        st = theme_state()
        if not st.font_family:
            st.font_family = "AlibabaPuHuiTi"
        apply_theme(page, st)
        if self.with_auto_routing:
            self.auto_routing()
        # 用 manage_views=False + page.render（根视图）：
        # manage_views=True 的视图栈会盖住页面浮层（page.overlay / show_dialog
        # 都不渲染），MultiSelect 这类需要悬挂面板的组件会失效。
        # 相应地，页面组件必须返回普通控件而不是 ft.View。
        return ft.Router([self.route], not_found=NotFoundView, manage_views=False)

    def add_route(self, route: ft.Route | list[ft.Route]):
        if isinstance(route, ft.Route):
            route = [route]
        if self.route.children is not None:
            self.route.children.extend(route)
        else:
            print("Error: route.children is None")

    def auto_routing(self, file_dir: str | Path = "views"):
        routes = []
        # for file in file_dir.rglob('*.py[c]'):
        file_dir = Path(file_dir)
        for file in file_dir.rglob("*.py"):
            if file.name != "__init__.py":
                spec = spec_from_file_location(file.stem, file)
                if spec is not None:
                    module = module_from_spec(spec)
                    if spec.loader is not None:
                        spec.loader.exec_module(module)
                    for _, object_page in getmembers(module):
                        if isinstance(object_page, ft.Route):
                            routes.append(object_page)
        if len(routes) == 0:
            # raise ValueError(
            print(
                f"Warning: No instances of ft.Route found. Check the assigned path of the {file_dir.absolute()}"
            )
        self.add_route(routes)

    def run(self):
        try:
            ft.run(
                lambda page: page.render(self._app),
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
            )
        except Exception as e:
            error_message = f"Error: {e!s}\n\n message:\n{traceback.format_exc()}"
            try:
                logger.error(error_message)
            except Exception:
                pass


if __name__ == "__main__":
    app = App(name="CS-UI App")
    route = [
        ft.Route(index=True, component=Home),
        ft.Route(path="about", component=About),
        ft.Route(path="contact", component=Contact),
    ]
    app.add_route(route)
    app.run()
