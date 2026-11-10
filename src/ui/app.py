"""应用入口：把主题、响应式、路由三件「页面级、只做一次」的事合成一个对象。

``App.run()`` 就是 ``ft.run(lambda page: page.render(self._app))`` —— 唯一的要求是
根视图走 ``page.render`` + ``Router(manage_views=False)``（见 :mod:`ui.core.float_layer`：
视图栈会盖住 ``page.overlay``，浮层面板全部失灵）。
"""

import traceback
from importlib.util import module_from_spec, spec_from_file_location
from inspect import getmembers
from pathlib import Path

import flet as ft

from ui.core.config import logger
from ui.core.i18n import t, use_t
from ui.core.responsive import apply_responsive
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


class App:
    """应用骨架：起页面、铺主题、挂路由。

    Args:
        name: 窗口标题，同时作为 ``ft.run(name=...)`` 的值。
        host / port: Web 视图下的监听地址与端口。
        view: ``ft.AppView.FLET_APP``（桌面）等。
        assets_dir: 静态资源目录。
        upload_dir: 上传落盘目录。
        web_renderer / route_url_strategy / no_cdn / export_asgi_app: 原样透传给 ``ft.run``。
        with_auto_routing: 是否扫描 ``views/`` 目录自动收集 ``ft.Route``。
    """

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
        with_auto_routing: bool = True,
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
        page = ft.context.page
        page.title = self.name
        page.fonts = FONTS
        # 主题只有一个事实源：ui.core.theme。apply_theme 同时写下明暗两套 ——
        # 只写 page.theme 的话深色模式没有为深色准备的那棵树。
        st = theme_state()
        if not st.font_family:
            st.font_family = "AlibabaPuHuiTi"
        apply_theme(page, st)
        # 响应式与主题同一个位置：都是"页面级、框架级、只做一次"的事。
        # 宽度只在**跨档**时触发重绘，拖动窗口不会变成幻灯片。
        apply_responsive(page)
        if self.with_auto_routing:
            self.auto_routing()
        # manage_views=False + page.render（根视图）：视图栈会盖住页面浮层，
        # MultiSelect 这类需要悬挂面板的组件会失效。相应地，页面组件必须返回
        # 普通控件而不是 ft.View。
        return ft.Router([self.route], not_found=NotFoundView, manage_views=False)

    def add_route(self, route: ft.Route | list[ft.Route]):
        if isinstance(route, ft.Route):
            route = [route]
        if self.route.children is None:
            logger.error("route.children is None")
            return
        self.route.children.extend(route)

    def auto_routing(self, file_dir: str | Path = "views"):
        """扫描 ``file_dir`` 下所有模块，收集其中的 ``ft.Route`` 实例。"""
        routes = []
        file_dir = Path(file_dir)
        for file in file_dir.rglob("*.py"):
            if file.name == "__init__.py":
                continue
            spec = spec_from_file_location(file.stem, file)
            if spec is None:
                continue
            module = module_from_spec(spec)
            if spec.loader is not None:
                spec.loader.exec_module(module)
            routes.extend(
                obj for _, obj in getmembers(module) if isinstance(obj, ft.Route)
            )
        if not routes:
            logger.warning("No ft.Route found in %s", file_dir.resolve())
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
