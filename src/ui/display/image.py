"""图片 (Image) —— 圆角、裁剪与加载失败占位。

在 :class:`flet.Image` 之上补两个默认值：

* ``fit=CONTAIN``：不指定时宁可留白，也不裁掉内容；
* 加载失败时的占位：没传 ``error_content`` 时自动补一个破损图标，
  免得图挂掉后整块高度塌成空白。

用法::

    Image(src="cover.png", width=200, height=140, fit=ft.BoxFit.COVER)
"""

from __future__ import annotations

from pathlib import Path

import flet as ft

from ui.core.doc import Api, Example, Spec, info, run, warn
from ui.core.tokens import ICON_SIZE

__all__ = ["Image", "ImgView"]


@ft.control
class Image(ft.Image):
    """图片控件。

    Args:
        src: 图片来源，支持 URL、本地资源路径、base64 与原始字节。
        fit: 裁剪方式，默认 CONTAIN（完整显示）。
        repeat: 容器大于图片时是否平铺。
        width: 显示宽度。
        height: 显示高度。
        border_radius: 圆角，直接裁在图像上。
        error_content: 加载失败时的占位；留空使用内置的破损图标。
        placeholder_src: 加载过程中的占位图。
    """

    repeat: ft.ImageRepeat = ft.ImageRepeat.NO_REPEAT
    fit: ft.BoxFit | None = ft.BoxFit.CONTAIN

    def init(self):
        super().init()
        if self.error_content is None:
            # 默认兜底：图片加载失败时至少留下一个「这里本该有图」的轮廓。
            # 走 surface_container_high + on_surface_variant，深色主题下不刺眼。
            self.error_content = ft.Container(
                alignment=ft.Alignment.CENTER,
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                content=ft.Icon(
                    ft.Icons.BROKEN_IMAGE_OUTLINED,
                    size=24,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
            )


@ft.control
class ImgView(ft.Column):
    img_path: str | Path | None = None
    repeat: ft.ImageRepeat = ft.ImageRepeat.NO_REPEAT
    fit: ft.BoxFit | None = ft.BoxFit.COVER

    def init(self):
        self.controls = [
            ft.Container(
                content=ft.Image(
                    src=str(self.img_path), repeat=self.repeat, fit=self.fit, scale=1.0
                ),
                ink=True,
                alignment=ft.Alignment.CENTER,
                width=150,
                height=150,
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,  # 占位底：明暗自适应
                border_radius=ft.BorderRadius.all(6),
            ),
            ft.Text(value=Path(self.img_path).name, size=12),
        ]
        self.spacing = 0


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
#: 240 × 150 的示意图（蓝天 / 地面 / 太阳），直接内嵌避免演示依赖网络。
#: 组件本身接受 URL，这里只是为了文档窗口离线也能看到效果。
_SAMPLE = (
    "iVBORw0KGgoAAAANSUhEUgAAAPAAAACWCAIAAABvmpKCAAACGUlEQVR42u3dsZHCMBBAUTVL"
    "HWQEtHMN0ANNUAEpzFxIAGZkpN3V8/wUkD0PJ1hLO/7dpDI1l0BAS0BLQEtAC2gJaAloCWgJ"
    "aAEtAS0BLQEtAS2gJaAloCWgJaD1dffrYUtAqwjlgKyBVi/lUKyB1j6Ug7AGWjtrnms6E+jH"
    "p2PAO9Ac3HQLa3S7wi0uO19OcxbTLezttvPo/Cyak5pu9Si/uNzlK0FzFtOtsOZ9b/NAA51b"
    "c23TwzQPNg30oqaBXlRzSdCDNY80DfSKpoFeWnMx0FM0DzMNNNBAAw000EADDTTQQAMNNNBA"
    "Aw000EADDTTQfikEGmigaQaaaaCB9jw00IuCtmPF03b2FNIMtF3fNNuxgvU6moGu4NvkJLu+"
    "65g2vQ5ooJk2OSmkaXDNtqtjGtlZpqecS9xxujSnNj3rRKLPh0Y5o+mJZ5Fg4DnNiVhPX/9a"
    "E/z1O9ZBVu4/VtTLOtSagVapgBbQEtAS0BLQAloCWgJaAloCWkBLQEtAS0BLQAtoCWgJaAlo"
    "CWgBLQEtAS0BLQEtoCWgJaAloCWgBbQEtAS0BLT0D/p0OUtlAlpAS0BLQEtAC2gJaAloCWgJ"
    "aAEtAS0BLQEtAS2gJaAloCWgJaAFtAS0BLQEtAS0gJaAloCWgJaAFtAS0BLQEtAS0AJaAloC"
    "WgJaQLsKAloCWgJaAlpAS0BLQEtAS0ALaAloCWgJaOltT/ooYZIPsQHuAAAAAElFTkSuQmCC"
)
_MISSING = "cover-not-found.png"


def _caption(text: str) -> ft.Control:
    return ft.Text(text, size=12, color=ft.Colors.ON_SURFACE_VARIANT)


def _tile(image: ft.Control, label: str) -> ft.Control:
    return ft.Column(
        spacing=8,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[image, _caption(label)],
    )


@ft.component
def _rounded() -> ft.Control:
    """同一张图三档圆角：直角、常规卡片圆角、胶囊。"""
    return ft.Row(
        spacing=20,
        wrap=True,
        controls=[
            _tile(
                Image(src=_SAMPLE, width=170, height=110, fit=ft.BoxFit.COVER),
                "border_radius=0",
            ),
            _tile(
                Image(
                    src=_SAMPLE,
                    width=170,
                    height=110,
                    fit=ft.BoxFit.COVER,
                    border_radius=12,
                ),
                "border_radius=12",
            ),
            _tile(
                Image(
                    src=_SAMPLE,
                    width=170,
                    height=110,
                    fit=ft.BoxFit.COVER,
                    border_radius=999,
                ),
                "border_radius=999（胶囊）",
            ),
        ],
    )


@ft.component
def _fits() -> ft.Control:
    """同一个 170×120 框里三种裁剪：完整、铺满、拉伸。"""
    return ft.Row(
        spacing=20,
        wrap=True,
        controls=[
            _tile(
                Image(src=_SAMPLE, width=170, height=120, border_radius=8),
                "CONTAIN：完整，留白",
            ),
            _tile(
                Image(
                    src=_SAMPLE,
                    width=170,
                    height=120,
                    fit=ft.BoxFit.COVER,
                    border_radius=8,
                ),
                "COVER：铺满，裁边",
            ),
            _tile(
                Image(
                    src=_SAMPLE,
                    width=170,
                    height=120,
                    fit=ft.BoxFit.FILL,
                    border_radius=8,
                ),
                "FILL：拉伸，会变形",
            ),
        ],
    )


@ft.component
def _broken() -> ft.Control:
    """加载失败：左边用内置占位，右边换成业务自己的说明。"""
    custom = ft.Container(
        alignment=ft.Alignment.CENTER,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
        content=ft.Column(
            spacing=4,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(
                    ft.Icons.IMAGE_NOT_SUPPORTED_OUTLINED,
                    size=ICON_SIZE["2xl"],
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
                _caption("图还没上传"),
            ],
        ),
    )
    return ft.Row(
        spacing=20,
        wrap=True,
        controls=[
            _tile(
                Image(src=_MISSING, width=170, height=110, border_radius=8),
                "默认占位",
            ),
            _tile(
                Image(
                    src=_MISSING,
                    width=170,
                    height=110,
                    border_radius=8,
                    error_content=custom,
                ),
                "自定义 error_content",
            ),
        ],
    )


_ROUNDED_CODE = """Image(src="cover.png", width=180, height=120, fit=ft.BoxFit.COVER)

# 圆角直接裁在图上，不用再包 Container：
Image(src="cover.png", width=180, height=120, fit=ft.BoxFit.COVER, border_radius=12)

# 头像那种胶囊：圆角给到比短边一半还大即可
Image(src="avatar.png", width=96, height=96, fit=ft.BoxFit.COVER, border_radius=999)"""


SPEC = Spec(
    name="Image",
    summary="显示一张图片：默认完整装入容器，圆角、裁剪与失败占位都在组件内收口。",
    definition=(
        "图片控件只做三件事：把图显示出来、按容器决定怎么裁、在图挂掉时给一个体面的"
        "占位。默认 fit=CONTAIN（完整显示、可能留白），需要铺满卡片时换成 COVER；"
        "圆角直接裁在图像上，不必再套一层 Container。"
    ),
    anatomy=[
        (
            "图像",
            "src 接受 URL、本地资源路径、base64 或原始 bytes，渲染前不需要预加载。",
        ),
        (
            "裁剪",
            "fit 决定图怎么放进给定宽高：CONTAIN 完整、COVER 铺满并裁边、FILL 拉伸变形。",
        ),
        ("圆角", "border_radius 裁的是图像本身；头像、封面图不用再包容器。"),
        (
            "失败占位",
            "加载失败时显示 error_content；不传时组件给一个破损图标，避免整块塌成空白。",
        ),
    ],
    when=[
        "封面图、头像、商品缩略图这类尺寸固定的位置",
        "图片比例与容器不一致，需要明确「留白还是裁切」",
        "图片来自网络，可能加载失败，需要占位兜底",
    ],
    avoid=[
        "一组图片需要网格排列：用 ImageGridView，省掉手写行列",
        "图片要点击放大：外面得包一层可点容器，Image 自己不管点击",
        "矢量图标：用 Icon，图片控件会按位图流程解码",
    ],
    examples=[
        Example(
            "圆角封面",
            _rounded,
            hint="同一张图三档圆角：直角、12px、胶囊。圆角是裁出来的，不是画上去的。",
            code=_ROUNDED_CODE,
        ),
        Example(
            "裁剪模式",
            _fits,
            hint="同一个 170×120 框：CONTAIN 留白、COVER 裁边、FILL 拉伸。",
        ),
        Example(
            "加载失败",
            _broken,
            hint="左边是内置占位，右边用 error_content 换成业务文案。",
        ),
    ],
    api=[
        Api("src", "str | bytes", "", "图片来源：URL、本地资源、base64 或原始字节"),
        Api(
            "fit",
            "BoxFit | None",
            "BoxFit.CONTAIN",
            "裁剪方式；默认完整显示，铺满用 COVER",
        ),
        Api("repeat", "ImageRepeat", "ImageRepeat.NO_REPEAT", "容器比图大时是否平铺"),
        Api("width", "int | float | None", "None", "显示宽度；不给就按图片原始尺寸"),
        Api("height", "int | float | None", "None", "显示高度；不给就按图片原始尺寸"),
        Api(
            "border_radius", "int | BorderRadius | None", "None", "圆角，直接裁在图像上"
        ),
        Api(
            "error_content",
            "Control | None",
            "None",
            "加载失败的占位；留空用内置破损图标",
        ),
        Api("placeholder_src", "str | bytes | None", "None", "加载过程中的占位图"),
    ],
    notes=[
        info(
            "fit 的默认值是 CONTAIN，与 flet 的 None 不同：不指定时宁可留白，也不裁掉"
            "内容 —— 裁切必须是显式决定。"
        ),
        warn(
            "src 是网络地址时，加载失败不会抛 Python 异常，只会走 error_content；"
            "外面包 try/except 拦不到任何东西。"
        ),
        info(
            "没有传 error_content 时组件自动补一个居中的破损图标占位。没有它，加载失败"
            "的图片会塌成 0 高，整行布局跟着跳。"
        ),
    ],
    tags=("图片", "image", "封面", "圆角", "裁剪"),
)


if __name__ == "__main__":
    run(SPEC)
