import flet as ft
from pathlib import Path


@ft.control
class Image(ft.Image):
    # src: str | bytes | None = None
    repeat: ft.ImageRepeat = ft.ImageRepeat.NO_REPEAT
    fit: ft.BoxFit | None = ft.BoxFit.CONTAIN
    # img_width: int = 200
    # img_height: int = 200

    # def init(self):
    #     self.content = ft.Image(
    #         src=self.src, repeat=self.repeat, fit=self.fit, scale=1.0
    #     )
    #     self.bgcolor = ft.Colors.GREY
    #     self.border_radius = ft.BorderRadius.all(5)
    #     self.alignment = ft.Alignment.CENTER
    #     self.on_hover = self.img_hover

    # def img_hover(self, e):
    #     self.scale = 1.1 if e.data else 1.0

    # def update_w_h(self, width: int, height: int):
    #     # 外部调用，更新图片显示的宽高
    #     self.width = width
    #     self.height = height


@ft.component
class ImgView(ft.Column):
    img_path: str | Path
    repeat: ft.ImageRepeat = ft.ImageRepeat.NO_REPEAT
    fit: ft.BoxFit | None = ft.BoxFit.CONTAIN
    # img_width: int = 200
    # img_height: int = 200

    def init(self):
        self.controls = [
            ft.Container(
                content=ft.Image(
                    src=str(self.img_path), repeat=self.repeat, fit=self.fit, scale=1.0
                ),
                # on_click=self.on_click,
                ink=True,
                alignment=ft.Alignment.CENTER,
                width=150,
                height=150,
                bgcolor=ft.Colors.GREY_100,
                border_radius=ft.BorderRadius.all(6),
                # border_radius=10,
            ),
            ft.Text(value=Path(self.img_path).name, size=12),
        ]
        self.spacing = 0


@ft.component
def App():
    return ft.Column(
        [
            Image(
                src="https://flet.dev/img/pages/home/flet-home.png",
                width=200,
                height=200,
            )
        ]
    )


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
