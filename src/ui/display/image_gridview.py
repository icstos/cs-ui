import flet as ft
from pathlib import Path
from dataclasses import field
from ui.display.image import Image
from ui.navigation.paging import Paging


@ft.control
class ImageGridView(ft.Card):
    title: str | None = ''
    img_file_paths: list[str | Path] = field(default_factory=list)
    num_item_per_page: int = 10

    def init(self):
        self.num_items = len(self.img_file_paths)
        self.current_page = 1

        self.v_title = ft.Text(
            value=self.title,
            theme_style=ft.TextThemeStyle.HEADLINE_LARGE,
            weight='bold',
        )
        self.v_img_size = ft.Slider(
            min=100,
            max=500,
            divisions=10,
            label='{value}',
            value=200,
            width=200,
            on_change=self.change_img_size_slider,
        )
        self.layout_row1 = ft.Row(
            controls=[
                ft.Row(
                    [self.v_title], alignment=ft.MainAxisAlignment.START, expand=True
                ),
                ft.Row(
                    [ft.Text('图像大小:'), self.v_img_size],
                    alignment=ft.MainAxisAlignment.END,
                ),
            ]
        )
        self.v_paging = Paging(
            sum_data_nums=self.num_items,
            on_change_page=self.set_page,
            on_change_per_page_nums=self.set_num_item_per_page,
        )

        self.layout_row2 = ft.GridView(
            controls=self.build_items(),
            max_extent=200,
            padding=ft.Padding.only(left=30, top=30, right=30, bottom=150),
            spacing=80,
        )

        self.content = ft.Container(
            ft.Column(
                controls=[
                    self.layout_row1,
                    ft.Card(
                        ft.Container(content=self.layout_row2, bgcolor=ft.Colors.WHITE),
                        elevation=5,
                    ),
                    ft.Row([self.v_paging]),
                ],
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=10,
            bgcolor=ft.Colors.WHITE,
        )
        self.elevation = 5

    def change_img_size_slider(self, e):
        now_value = e.control.value
        self.layout_row2.max_extent = now_value
        self.layout_row2.spacing = now_value / 4
        for _ in self.layout_row2.controls:
            _: Image
            _.update_w_h(width=now_value, height=now_value)

    @property
    def num_pages(self):
        if self.num_item_per_page <= 0:
            return 1
        num_page, num_page_over = divmod(self.num_items, self.num_item_per_page)
        return num_page + (1 if num_page_over else 0)

    def set_num_item_per_page(self, new_row_per_page: str):
        try:
            value = int(new_row_per_page)
            if 1 <= value <= self.num_items:
                self.num_item_per_page = value
        except Exception:
            pass
        self.set_page(page=1)

    def set_page(self, page: str | int | None = None, delta: int = 0):
        if page is not None:
            try:
                page_int = int(page)
                self.current_page = page_int if 1 <= page_int <= self.num_pages else 1
            except ValueError:
                self.current_page = 1
        elif delta:
            self.current_page += delta
            if self.current_page < 1:
                self.current_page = 1
            elif self.current_page > self.num_pages:
                self.current_page = self.num_pages
        else:
            return
        self.layout_row2.controls = self.build_items()

    def build_items(self) -> list:

        index_start = (self.current_page - 1) * self.num_item_per_page
        index_end = self.current_page * self.num_item_per_page
        now_img_file_paths = self.img_file_paths[index_start:index_end]
        items = []
        for img_path in now_img_file_paths:
            items.append(Image(src=str(img_path)))
        return items


def main(page: ft.Page):
    page.scroll = ft.ScrollMode.AUTO

    file_paths = []
    file_dir = Path(r'src/ui/data/images')
    print(file_dir.absolute())
    for i in range(10):
        for file in file_dir.glob('*.png'):
            file_paths.append(str(file))
    print(f'ImageGridView: {len(file_paths)}')
    multi_img_show = ImageGridView(title='测试数据集', img_file_paths=file_paths)
    page.add(multi_img_show)


if __name__ == '__main__':
    ft.run(main)
