"""图片选择 (ImagePicker) —— 点一下方块选图，就地 150×150 预览。

只做一件事：把「选哪张图」变成 ``value`` 里的一个路径，选完立刻在原地显示缩略图，
不必再单独摆一个 Image。文件不复制、不转码，``value`` 就是用户磁盘上的原路径。

用法::

    picker = ImagePicker(label="封面图", value="cover.png")
    Column([picker.ui()])
    print(picker.path)          # Path | None
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import flet as ft

from ui.core.doc import Api, Example, Spec, info, run, tip, warn
from ui.core.tokens import FONT_SIZE, ICON_SIZE, RADIUS, SPACE
from ui.input.input import Input

__all__ = ["ImagePicker"]

BOX = 150  # 预览方块边长：再大就压过同排的表单字段
#: 空预览框的占位图标：这是"空状态"，按刻度取 3xl（32）——
#: 它是整块控件唯一的可点区域，比正文图标大两档才撑得住 150px 的方框。
PLACEHOLDER_ICON_SIZE = ICON_SIZE["3xl"]
_MUTED = ft.Colors.ON_SURFACE_VARIANT


@ft.observable
@dataclass
class ImagePicker(Input):
    """图片表单控件：一个方块，点击选图，选完就地预览。

    Attributes:
        value: 已选图片的路径；``None`` 或文件不存在时显示空态图标。
        label: 说明文字。继承自 :class:`~ui.input.input.Label`，横向布局时在左侧。
        label_width: 标签占位宽度。
        is_vertical: 标签放到方块上方。
        is_required: 标签前加红色星号。
    """

    def _preview(self) -> ft.Control:
        """有路径且文件存在就显示图片，否则显示「加一张图」的空态图标。"""
        path = self.path
        exists = False
        if path is not None:
            try:
                exists = path.exists()
            except (OSError, ValueError):
                # 非法路径（空字符、过长的盘符）不该让整块控件崩掉
                exists = False
        if not exists:
            return ft.Icon(
                ft.Icons.ADD_PHOTO_ALTERNATE_OUTLINED,
                size=PLACEHOLDER_ICON_SIZE,
                color=_MUTED,
            )
        return ft.Image(
            src=str(path),
            width=BOX,
            height=BOX,
            fit=ft.BoxFit.COVER,
            border_radius=RADIUS["lg"],
            error_content=ft.Container(
                alignment=ft.Alignment.CENTER,
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                content=ft.Icon(
                    ft.Icons.BROKEN_IMAGE_OUTLINED,
                    size=PLACEHOLDER_ICON_SIZE,
                    color=_MUTED,
                ),
            ),
        )

    @ft.component
    def ui(self):
        # 服务在构造时就注册到当前 page，只建一次，避免每次重绘攒下废弃的实例
        file_picker = ft.use_memo(ft.FilePicker, [])

        async def on_click(_e):
            selected = await file_picker.pick_files(
                allow_multiple=False,
                file_type=ft.FilePickerFileType.IMAGE,
            )
            # 取消时 flet 返回空列表：保留上一次的图，不把预览清掉
            if not selected:
                return
            path = selected[0].path
            if path:
                self.value = path
                self.last_value = path
                # 不 notify 的话 value 变了但方块不会重绘，预览要等下一次整页刷新
                self.notify()

        box = ft.Container(
            width=BOX,
            height=BOX,
            border_radius=RADIUS["lg"],
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            alignment=ft.Alignment.CENTER,
            tooltip=str(self.value) if self.value else None,
            on_click=on_click,
            content=self._preview(),
        )

        label = self.v_label
        if label is None:
            return box
        if self.is_vertical:
            return ft.Column(
                spacing=self.spacing,
                horizontal_alignment=ft.CrossAxisAlignment.START,
                controls=[label, box],
            )
        return ft.Row(
            spacing=self.spacing,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[label, box],
        )


# ---------------------------------------------------------------------------
# 示例：用仓库里的示例图回放「已选择」，渲染期不弹系统对话框
# ---------------------------------------------------------------------------
_SAMPLE = Path(__file__).resolve().parents[1] / "data" / "images" / "logo.png"


@ft.component
def _echo(picker: ImagePicker) -> ft.Control:
    return ft.Text(
        f"value：{picker.value or 'None（未选择）'}",
        size=FONT_SIZE["small"],
        color=_MUTED,
    )


@ft.component
def _selected() -> ft.Control:
    picker = ft.use_memo(lambda: ImagePicker(label="封面图", value=str(_SAMPLE)), [])
    return ft.Column(spacing=SPACE["3"], controls=[picker.ui(), _echo(picker)])


@ft.component
def _empty() -> ft.Control:
    picker = ft.use_memo(lambda: ImagePicker(label="封面图"), [])
    return ft.Column(spacing=SPACE["3"], controls=[picker.ui(), _echo(picker)])


@ft.component
def _switch() -> ft.Control:
    """同一个控件在「未选择 / 已选择」之间切换，说明预览只取决于 value。"""
    picker = ft.use_memo(ImagePicker, [])

    def flip(_e):
        picker.value = None if picker.value else str(_SAMPLE)
        picker.notify()

    return ft.Column(
        spacing=SPACE["3"],
        controls=[
            picker.ui(),
            ft.Row(
                spacing=SPACE["3"],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Button(
                        content=ft.Text("切换选择前 / 选择后"),
                        on_click=flip,
                    ),
                    _echo(picker),
                ],
            ),
        ],
    )


_IMAGE_CODE = """picker = ImagePicker(label="封面图", value="cover.png")
Column([picker.ui()])

# 选完图片路径写回 value（点取消时保持原值）：
picker.value        # str | None
picker.path         # Path | None，去掉首尾空白与引号"""


SPEC = Spec(
    name="ImagePicker",
    summary="点一下方块选一张本地图片，选完就地显示 150×150 预览。",
    definition=(
        "图片选择是「表单里只放一张图」时最省事的做法：一个方块既是空态占位，也是"
        "预览位，还是打开文件对话框的按钮。它只记路径、不复制文件，所以用户在系统里"
        "换掉那张图，界面上看到的也会跟着换。需要多张图时该用 ImageGridView。"
    ),
    anatomy=[
        (
            "预览块",
            "150×150 的圆角方块，图按 COVER 裁切铺满；尺寸固定，不跟随 width 参数。",
        ),
        (
            "空态",
            "value 为空、或路径指向的文件已经不存在时，显示一个「加一张图」的图标。",
        ),
        (
            "点击",
            "整块都可点，打开系统的图片类型对话框（file_type=IMAGE），单选。",
        ),
        (
            "标签",
            "继承自 Label：横向布局时在方块左侧右对齐，is_vertical 时在上方左对齐。",
        ),
        ("value", "选中的绝对路径；读取时用 path 拿到规整过的 Path 更省事。"),
    ],
    when=[
        "头像、封面、证书扫描件这类「只放一张」的表单字段",
        "提交前需要让用户确认选的是哪张图",
        "占位空间有限，希望空态和预览共用同一块位置",
    ],
    avoid=[
        "要选多张图：用 ImageGridView，方块逐个摆会撑爆表单",
        "只要文件不关心内容：用 FilePicker，省掉解码与预览",
        "图片来自网络地址：直接用 Image，本地路径检查会把 URL 判成空态",
    ],
    examples=[
        Example(
            "已选择",
            _selected,
            hint="预置一张仓库里的示例图：方块直接显示缩略图，标签在左侧。",
            code=_IMAGE_CODE,
        ),
        Example(
            "空态",
            _empty,
            hint="value 为空时是一个「加一张图」的方块；点它会打开图片对话框。",
        ),
        Example(
            "选择前 / 选择后",
            _switch,
            hint="同一个控件在两种状态之间切换：预览只取决于 value，与点击无关。",
        ),
    ],
    api=[
        Api(
            "value",
            "str | Path | None",
            "None",
            "已选图片路径；空或文件不存在时显示空态",
        ),
        Api("path", "Path | None", "—", "只读属性：value 去掉空白与引号后的 Path"),
        Api("label", "str | None", "None", "左侧或上方的说明文字"),
        Api("label_width", "int", "150", "标签占位宽度；横向布局时右对齐"),
        Api("is_vertical", "bool", "False", "标签放到方块上方，适合窄容器"),
        Api("is_required", "bool", "False", "标签前加红色星号"),
        Api("ui()", "Control", "", "渲染方块（以及标签）"),
    ],
    notes=[
        tip(
            "label 以前是静默失效的：ui() 直接返回方块，传了标签也不显示。现在按 Input "
            "的约定渲染在左侧或上方，和其它表单控件对齐。"
        ),
        warn(
            "value 只认本地路径。网络 URL 会先被 Path(...).exists() 判成不存在而退回"
            "空态，要显示远程图片请直接用 Image。"
        ),
        info(
            "选完图必须 notify()：以前只改 value 不通知，缩略图要等下一次整页重绘才刷新，"
            "看起来像「点了没反应」。"
        ),
    ],
    tags=("图片", "选图", "上传", "image", "avatar", "封面"),
)


if __name__ == "__main__":
    run(SPEC)
