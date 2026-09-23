"""图片网格视图 (ImageGridView)。

按页展示一批图片，支持「每页数量」切换与「缩略图尺寸」实时调整。

.. note::
   本组件早期版本是一个 ``@ft.control`` 控件，在 ``init()`` 中直接构造
   ``Paging`` 组件。flet 1.0.0 的组件必须在渲染上下文中创建，
   因此这里改为与其他有状态组件一致的 **observable 状态 + ``ui()`` 组件** 模式。

用法::

    grid = ImageGridView(title="数据集", img_file_paths=[...])
    ...
    control = grid.ui()
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import flet as ft

from ui.display.image import Image
from ui.navigation.paging import Paging, PagingState

__all__ = ["ImageGridView"]

MIN_IMG_SIZE = 80
MAX_IMG_SIZE = 320
DEFAULT_IMG_SIZE = 160


@ft.observable
@dataclass
class ImageGridView:
    """图片网格视图。

    Args:
        title: 标题文本。
        img_file_paths: 图片路径或 URL 列表。
        num_item_per_page: 每页图片数量，默认 10。
        img_size: 初始缩略图边长，默认 160。
        show_paging: 是否显示分页控件，默认 True。
        show_size_slider: 是否显示缩略图尺寸滑块，默认 True。
        grid_height: 网格区域高度，默认 420。
    """

    title: str = ""
    img_file_paths: list[str | Path] = field(default_factory=list)
    num_item_per_page: int = 10
    img_size: int = DEFAULT_IMG_SIZE
    show_paging: bool = True
    show_size_slider: bool = True
    grid_height: int = 420

    # 内部状态
    current_page: int = 1

    # ------------------------------------------------------------------
    # 派生属性
    # ------------------------------------------------------------------

    @property
    def num_items(self) -> int:
        """图片总数。"""
        return len(self.img_file_paths)

    @property
    def num_pages(self) -> int:
        """总页数（至少为 1）。"""
        if self.num_item_per_page <= 0:
            return 1
        pages, rest = divmod(self.num_items, self.num_item_per_page)
        return max(1, pages + (1 if rest else 0))

    def page_items(self) -> list[str | Path]:
        """当前页应展示的图片。"""
        start = (self.current_page - 1) * self.num_item_per_page
        return self.img_file_paths[start : start + self.num_item_per_page]

    # ------------------------------------------------------------------
    # 状态变更
    # ------------------------------------------------------------------

    def _set_page(self, page: str | int | None = None) -> None:
        try:
            value = int(page)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return
        self.current_page = value if 1 <= value <= self.num_pages else 1
        self.notify()  # type: ignore[attr-defined]

    def _set_num_item_per_page(self, per_page: int | str) -> None:
        try:
            value = int(per_page)
        except (TypeError, ValueError):
            return
        if 1 <= value <= max(self.num_items, 1):
            self.num_item_per_page = value
        self.current_page = 1
        self.notify()  # type: ignore[attr-defined]

    def _set_img_size(self, e: ft.ControlEvent) -> None:
        self.img_size = int(float(e.control.value))
        self.notify()  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    @ft.component
    def ui(self) -> ft.Control:
        """构建图片网格视图。"""
        controls: list[ft.Control] = []

        if self.title or self.show_size_slider:
            controls.append(self._build_header())

        controls.append(
            ft.Container(
                content=ft.GridView(
                    controls=[self._build_tile(path) for path in self.page_items()],
                    max_extent=self.img_size,
                    spacing=max(8, self.img_size // 5),
                    run_spacing=max(8, self.img_size // 5),
                    expand=True,
                    padding=8,
                ),
                height=self.grid_height,
                bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
                border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                border_radius=ft.BorderRadius.all(8),
            )
        )

        if self.show_paging and self.num_pages > 1:
            controls.append(
                Paging(
                    PagingState(
                        sum_data_nums=self.num_items,
                        data_per_page_nums=self.num_item_per_page,
                        current_page=self.current_page,
                        data_unit="张",
                        on_change_page=self._set_page,
                        on_change_per_page_nums=self._set_num_item_per_page,
                    )
                )
            )

        return ft.Column(controls=controls, spacing=12)

    # ------------------------------------------------------------------
    # 内部构建
    # ------------------------------------------------------------------

    def _build_header(self) -> ft.Control:
        """标题 + 尺寸滑块。"""
        left: list[ft.Control] = []
        if self.title:
            left.append(
                ft.Text(self.title, size=16, weight=ft.FontWeight.BOLD, expand=True)
            )
        else:
            left.append(ft.Container(expand=True))

        right: list[ft.Control] = []
        if self.show_size_slider:
            right.extend(
                [
                    ft.Text("缩略图尺寸", size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                    ft.Slider(
                        min=MIN_IMG_SIZE,
                        max=MAX_IMG_SIZE,
                        divisions=(MAX_IMG_SIZE - MIN_IMG_SIZE) // 20,
                        value=self.img_size,
                        width=180,
                        label="{value}",
                        on_change=self._set_img_size,
                    ),
                ]
            )

        return ft.Row(
            controls=[*left, *right],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _build_tile(self, path: str | Path) -> ft.Control:
        """单张图片卡片。"""
        name = Path(str(path)).name
        return ft.Column(
            controls=[
                Image(
                    src=str(path),
                    width=self.img_size,
                    height=self.img_size,
                    fit=ft.BoxFit.COVER,
                    border_radius=6,
                ),
                ft.Text(
                    name,
                    size=11,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                    width=self.img_size,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            spacing=4,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )


# ----------------------------------------------------------------------
# 示例
# ----------------------------------------------------------------------


@ft.component
def App():
    """ImageGridView 组件运行示例。"""
    logo = Path(__file__).resolve().parents[1] / "data/images/logo.png"
    paths = [str(logo) for _ in range(23)]

    grid = ImageGridView(title="测试数据集", img_file_paths=paths, num_item_per_page=8)
    return ft.Column(controls=[grid.ui()], scroll=ft.ScrollMode.AUTO, expand=True)


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
