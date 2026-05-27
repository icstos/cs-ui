import flet as ft


@ft.control
class Image(ft.Container):
    src: str | bytes | None = None
    repeat: ft.ImageRepeat = ft.ImageRepeat.NO_REPEAT
    fit: ft.BoxFit | None = None

    def init(self):
        self.content = ft.Image(src=self.src, repeat=self.repeat, fit=self.fit)
        self.bgcolor = ft.Colors.GREY
        self.border_radius = ft.BorderRadius.all(5)
        self.alignment = ft.Alignment.CENTER
        self.on_hover = self.img_hover

    def img_hover(self, e):
        self.scale = 1.1 if e.data else 1.0

    def update_w_h(self, width: int, height: int):
        # 外部调用，更新图片显示的宽高
        self.width = width
        self.height = height


def main(page: ft.Page):
    page.add(
        Image(
            src="https://flet.dev/img/pages/home/flet-home.png", width=200, height=200
        )
    )


if __name__ == '__main__':
    ft.run(main)
