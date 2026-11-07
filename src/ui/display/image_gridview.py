"""图片网格视图 (ImageGridView)。

按页展示一批图片，支持「每页数量」切换与「缩略图尺寸」实时调整。

.. note::
   本组件早期版本是一个 ``@ft.control`` 控件，在 ``init()`` 中直接构造
   ``Pagination`` 组件。flet 1.0.0 的组件必须在渲染上下文中创建，
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

from ui.core.doc import Api, Example, Spec, info, run, tip, warn
from ui.core.i18n import t, use_t
from ui.display.image import Image
from ui.navigation.pagination import Pagination, PaginationState

__all__ = ["ImageGridView"]

MIN_IMG_SIZE = 80
MAX_IMG_SIZE = 320
DEFAULT_IMG_SIZE = 160
MUTED: ft.ColorValue = ft.Colors.ON_SURFACE_VARIANT


@ft.observable
@dataclass
class ImageGridView:
    """图片网格视图。

    Args:
        title: 标题文本。
        img_file_paths: 图片路径或 URL 列表。
        num_item_per_page: 每页图片数量，默认 10。
        img_size: 初始缩略图边长，默认 160。
        show_pagination: 是否显示分页控件，默认 True。
        show_size_slider: 是否显示缩略图尺寸滑块，默认 True。
        grid_height: 网格区域高度，默认 420。
    """

    title: str = ""
    img_file_paths: list[str | Path] = field(default_factory=list)
    num_item_per_page: int = 10
    img_size: int = DEFAULT_IMG_SIZE
    show_pagination: bool = True
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
    #
    # 本类是 `@ft.observable`，**给字段赋值本身就会通知订阅者重渲染**，
    # 不需要（也不能）再调 `self.notify()` —— flet 1.x 的 Control 上
    # 压根没有这个方法，旧代码里的 `self.notify()` 是 AttributeError。
    # ------------------------------------------------------------------

    def _set_page(self, page: str | int | None = None) -> None:
        try:
            value = int(page)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return
        self.current_page = value if 1 <= value <= self.num_pages else 1

    def _set_num_item_per_page(self, per_page: int | str) -> None:
        try:
            value = int(per_page)
        except (TypeError, ValueError):
            return
        if 1 <= value <= max(self.num_items, 1):
            self.num_item_per_page = value
        self.current_page = 1

    def _set_img_size(self, e: ft.ControlEvent) -> None:
        self.img_size = int(float(e.control.value))

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    @ft.component
    def ui(self) -> ft.Control:
        """构建图片网格视图。"""
        use_t()  # 订阅语言：尺寸滑块标签 + 分页量词都要跟着切
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

        if self.show_pagination and self.num_pages > 1:
            controls.append(
                Pagination(
                    PaginationState(
                        sum_data_nums=self.num_items,
                        data_per_page_nums=self.num_item_per_page,
                        current_page=self.current_page,
                        data_unit=t("ui.image.unit"),
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
                    ft.Text(
                        t("ui.image.size"),
                        size=12,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
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
        """单张图片卡片：缩略图 + 文件名。"""
        name = Path(str(path)).name
        return ft.Column(
            controls=[
                Image(
                    src=str(path),
                    width=self.img_size,
                    height=self.img_size,
                    fit=ft.BoxFit.COVER,
                    border_radius=6,
                    error_content=self._placeholder(name),
                ),
                ft.Text(
                    name,
                    size=11,
                    color=MUTED,
                    width=self.img_size,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            spacing=4,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _placeholder(self, name: str) -> ft.Control:
        """缩略图加载失败时的占位块。

        默认的破图图标在一面墙上重复十几次太吵；这里换成一块角色色底 + 文件后缀，
        远看仍是一格缩略图。离线、图挂掉、路径写错都走这一条。
        """
        suffix = Path(name).suffix.lstrip(".").upper() or "IMG"
        return ft.Container(
            width=self.img_size,
            height=self.img_size,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
            alignment=ft.Alignment.CENTER,
            content=ft.Column(
                spacing=4,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(ft.Icons.IMAGE_OUTLINED, size=20, color=MUTED),
                    ft.Text(suffix, size=10, color=MUTED),
                ],
            ),
        )


# ----------------------------------------------------------------------
# 示例
# ----------------------------------------------------------------------
#: 造样本用的文件名主干：拼出「相册/晨雾-01.jpg」这种路径。
_STEMS: tuple[str, ...] = (
    "晨雾",
    "海岸线",
    "夜航",
    "旧巷",
    "雪山",
    "集市",
    "稻田",
    "长桥",
    "沙丘",
    "灯塔",
    "雨林",
    "车站",
)


def _album(count: int, folder: str = "相册") -> list[str]:
    """生成一批**不存在的**本地路径。

    示例因此既不联网也不读盘：缩略图会走组件里的占位块，路径只用来做文件名标签。
    """
    return [
        f"{folder}/{_STEMS[i % len(_STEMS)]}-{i + 1:02d}"
        f".{'png' if i % 5 == 4 else 'jpg'}"
        for i in range(count)
    ]


@ft.component
def _basic() -> ft.Control:
    """18 张、每页 8 张：三页，底部分页条可以直接翻。"""
    grid = ft.use_memo(
        lambda: ImageGridView(
            title="2026 秋季采风",
            img_file_paths=_album(18),
            num_item_per_page=8,
            img_size=112,
            grid_height=320,
        ),
        [],
    )
    return grid.ui()


@ft.component
def _density() -> ft.Control:
    """12 张一页放完：分页条自动不出现，拖滑块把缩略图放大到 320。"""
    grid = ft.use_memo(
        lambda: ImageGridView(
            title="素材库 · 拖动右侧滑块改尺寸",
            img_file_paths=_album(12),
            num_item_per_page=12,
            img_size=96,
            grid_height=260,
        ),
        [],
    )
    return grid.ui()


@ft.component
def _wall() -> ft.Control:
    """没有标题也没有滑块：只剩一面紧凑的图墙，适合嵌进已有卡片。"""
    grid = ft.use_memo(
        lambda: ImageGridView(
            img_file_paths=_album(9, folder="导出"),
            num_item_per_page=9,
            img_size=88,
            show_size_slider=False,
            show_pagination=False,
            grid_height=248,
        ),
        [],
    )
    return grid.ui()


# ----------------------------------------------------------------------
# 示例源码（“查看代码”面板）
# ----------------------------------------------------------------------
_BASIC_CODE = """grid = ImageGridView(
    title="2026 秋季采风",
    img_file_paths=paths,            # list[str | Path]，顺序即展示顺序
    num_item_per_page=8,             # 每页 8 张，超过一页才出分页条
    img_size=112,                    # 缩略图边长，滑块可在 80–320 之间改
    grid_height=320,                 # 网格视口，超出由网格自己滚
)
Column([grid.ui()])"""

_DENSITY_CODE = """ImageGridView(
    title="素材库",
    img_file_paths=paths,
    num_item_per_page=12,            # 一页放完 → 分页条不出现
    img_size=96,                     # 滑块把 96 拖到 320 会实时重排
    show_size_slider=True,
    grid_height=260,
).ui()"""

_WALL_CODE = """ImageGridView(
    img_file_paths=paths,            # 不传 title，就没有标题行
    num_item_per_page=len(paths),    # 关分页时每页张数要 ≥ 总数，否则后面的图没有入口
    img_size=88,
    show_size_slider=False,
    show_pagination=False,
    grid_height=248,
).ui()"""


# ----------------------------------------------------------------------
# 组件说明
# ----------------------------------------------------------------------
SPEC = Spec(
    name="ImageGridView",
    summary="把一批图片铺成等高缩略图墙：标题、尺寸滑块、分页一次配齐。",
    definition=(
        "ImageGridView 是「相册墙」的成品件：上面一行标题与缩略图尺寸滑块，中间一块"
        "固定高度的正方缩略图网格，下面一条分页。它只解决「一批尺寸相同的图怎么排、"
        "一屏放多少」；上传、裁剪、点击预览都不在它的职责里 —— 那些应该在网格之外，"
        "按业务补一层可点容器或工具栏。"
    ),
    anatomy=[
        (
            "标题行",
            "左边标题、右边「缩略图尺寸」标签与滑块；标题为空且关掉滑块时整行不出现。",
        ),
        (
            "缩略图",
            "正方形、COVER 裁切、6px 圆角，边长由 img_size 决定（滑块范围 80–320）。",
        ),
        (
            "文件名",
            "缩略图下方 11px 一行，居中，超出宽度收省略号 —— 用来确认「这是哪一张」。",
        ),
        (
            "网格视口",
            (
                "SURFACE_CONTAINER_LOWEST 底 + 1px OUTLINE_VARIANT 描边，高度固定为 "
                "grid_height，行数超出由网格自己纵向滚动。"
            ),
        ),
        (
            "占位块",
            "图加载不出来时换成同尺寸的角色色块 + 文件后缀，整面墙不会变成一排破图。",
        ),
        (
            "分页条",
            "复用 Pagination：只有超过一页才出现，页码与每页张数都回写到组件状态。",
        ),
    ],
    when=[
        "相册、素材库、导出结果这类「一批尺寸相同的图」",
        "缩略图要在「看得清」与「一屏看更多」之间由用户自己权衡",
        "图多到需要分页，但每张图本身没有额外操作",
    ],
    avoid=[
        "图片有主次（首图大、其余小）：那是画廊或瀑布流，网格会把主图压成一样大",
        "每张图要悬停预览、点击放大、批量勾选：得自己在网格外包一层可点容器与工具栏",
        (
            "只想排一批卡片、不要分页与尺寸控制：直接用 GridView（或 Grid），"
            "少一层状态和一条分页条"
        ),
    ],
    examples=[
        Example(
            "相册分页",
            _basic,
            hint="18 张、每页 8 张共三页。缩略图是占位块 —— 示例路径不存在，正好演示加载失败的样子。",
            code=_BASIC_CODE,
        ),
        Example(
            "调整缩略图尺寸",
            _density,
            hint="拖右侧滑块：缩略图从 96 长到 320，网格会按新尺寸重排列数。",
            code=_DENSITY_CODE,
        ),
        Example(
            "紧凑图墙",
            _wall,
            hint="不传标题、关掉滑块与分页，只剩网格本身，适合嵌进已有卡片。",
            code=_WALL_CODE,
        ),
    ],
    api=[
        Api("title", "str", "''", "左上角标题；留空且关掉滑块时标题行整行不渲染"),
        Api(
            "img_file_paths", "list[str | Path]", "[]", "图片路径或 URL，顺序即展示顺序"
        ),
        Api("num_item_per_page", "int", "10", "每页张数；改动后回到第 1 页"),
        Api("img_size", "int", "160", "缩略图边长初值；滑块可在 80–320 之间调"),
        Api("show_pagination", "bool", "True", "是否带分页条（仍需超过一页才出现）"),
        Api("show_size_slider", "bool", "True", "是否显示缩略图尺寸滑块"),
        Api("grid_height", "int", "420", "网格视口高度；超出部分纵向滚动"),
        Api("current_page", "int", "1", "当前页码（1 起）；换页由分页条回写"),
        Api("page_items()", "() -> list[str | Path]", "—", "当前页应展示的那几张"),
        Api("ui()", "() -> Control", "—", "渲染成控件，放进页面时调它"),
    ],
    notes=[
        info(
            "每页张数有上限（不超过图片总数）：再大就没有下一页，分页条一消失，用户再也"
            "回不到 10 张一页。所以选一个超出的值会被忽略，只是页码回到第 1 页。"
        ),
        warn(
            "show_pagination=False 时组件仍按 num_item_per_page 切片。总数超过一页，剩下的图"
            "就没有任何入口 —— 关分页要把每页张数放到不小于总数。"
        ),
        tip(
            "缩略图加载失败走 Image 的 error_content，这里换成了角色色占位块 + 后缀名："
            "离线、图挂掉或路径写错时，整面墙仍是整齐的格子，而不是十几个破图图标。"
        ),
    ],
    tags=("图片网格", "相册", "缩略图", "gallery", "image grid"),
)


if __name__ == "__main__":
    run(SPEC)
