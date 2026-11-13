"""文件选择 —— 选文件、选目录、另存为的原生对话框入口。

分两类，按"谁来发起选择"划界：

**声明式三件套** :class:`FilePicker` / :class:`DirPicker` / :class:`FileSaver`
是「按钮 + 结果回显」的薄壳：选择由用户在界面上点出来，结果落在 ``value`` 里。
分成三个类而不是一个 ``mode="file|dir|save"``，是因为返回值的形状不同
（文件列表 / 目录 / 目标文件），合并只会让类型分支与空值判断糊在一起。

**命令式服务** :class:`FileDialog` 则面向"选择由视图模型发起"的场景：没有常驻
按钮、不参与渲染，``await`` 一次拿一个结果。MVVM 里视图模型不认识控件，只能发出
"请用户挑一个目录"的请求，由视图层代为 ``await``，结果再回喂给视图模型。

用法::

    picker = FilePicker(allowed_extensions=["pdf", "docx"])
    Column([picker.ui()])
    print([f.path for f in picker.value])   # 取消时保留上一次的选择
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import flet as ft

from ui.core.doc import Api, Example, Spec, info, run, tip, warn
from ui.core.i18n import use_t
from ui.core.tokens import FONT_SIZE, RADIUS, SPACE

__all__ = [
    "SPECS",
    "DirPicker",
    "FileDialog",
    "FileDialogError",
    "FilePicker",
    "FileSaver",
    "get_human_file_size",
    "get_size",
]

_log = logging.getLogger(__name__)

_MUTED = ft.Colors.ON_SURFACE_VARIANT


def get_size(file_path):
    return round(os.stat(file_path).st_size, 2)


def get_human_file_size(file_size: float) -> str:
    """字节数转「2.30 MB」这种人类可读串，单位按 1024 进位。"""
    if file_size < 1024:
        return f"{file_size:.2f} byte"
    elif file_size < 1024 * 1024:
        return f"{file_size / 1024:.2f} KB"
    elif file_size < 1024 * 1024 * 1024:
        return f"{file_size / (1024 * 1024):.2f} MB"
    else:
        return f"{file_size / (1024 * 1024 * 1024):.2f} GB"


def _as_picked(items: Sequence[Any]) -> list[ft.FilePickerFile]:
    """把初始值统一成 ``FilePickerFile`` 列表。

    ``value`` 允许传 ``Path`` / ``str`` / ``FilePickerFile`` 三种：来自配置的
    多半是路径，来自上一次选择的已经是 FilePickerFile。转换必须落在**一份新列表**
    上：边遍历副本边往原列表追加，会让 value 里同时躺着 Path 和转换后的对象；
    文件不存在时 ``stat()`` 还会直接抛异常，整块控件渲染不出来。
    """
    files: list[ft.FilePickerFile] = []
    for item in items:
        if isinstance(item, ft.FilePickerFile):
            files.append(item)
            continue
        path = Path(str(item)).expanduser()
        try:
            size = path.stat().st_size
        except OSError:
            # 记录里的文件可能已经被删掉：照旧显示，大小按 0 记，不让列表整块消失
            _log.debug("初始文件不可读，按 0 字节处理：%s", path)
            size = 0
        files.append(
            ft.FilePickerFile(
                id=len(files),
                name=path.name or str(path),
                path=str(path.absolute()),
                size=size,
            )
        )
    return files


def _file_rows(picker: FilePicker) -> list[ft.Control]:
    """已选文件列表的每一行：图标 / 文件名 / 大小 / 移除。"""

    def remove(file: ft.FilePickerFile):
        # 按对象身份删，而不是按文件名：不同目录下的同名文件不该一起消失
        picker.value = [f for f in picker.value if f is not file]
        picker.notify()
        if picker.on_change:
            picker.on_change(picker.value)

    return [
        ft.Row(
            key=f"{file.id}-{file.name}",
            spacing=SPACE["2"],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            tooltip=file.path,
            controls=[
                ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, size=18, color=_MUTED),
                ft.Text(
                    file.name,
                    size=FONT_SIZE["body"],
                    no_wrap=True,
                    overflow=ft.TextOverflow.ELLIPSIS,
                    expand=1,
                ),
                ft.Text(
                    get_human_file_size(file.size),
                    size=FONT_SIZE["small"],
                    color=_MUTED,
                    no_wrap=True,
                ),
                ft.IconButton(
                    icon=ft.Icons.CLOSE,
                    icon_size=16,
                    icon_color=_MUTED,
                    # 默认 48 的点击区会把一行撑得很空，收到 32 与行高齐平
                    width=32,
                    height=32,
                    on_click=lambda _e, f=file: remove(f),
                ),
            ],
        )
        for file in picker.value
    ]


def _path_text(value: Path | None) -> ft.Control:
    """结果回显行：按钮定宽、路径吃弹性，长路径单行省略而不是把按钮挤出去。"""
    return ft.Container(
        expand=1,
        content=ft.Text(
            str(value) if value else "",
            size=FONT_SIZE["body"],
            color=_MUTED,
            no_wrap=True,
            overflow=ft.TextOverflow.ELLIPSIS,
            tooltip=str(value) if value else None,
        ),
    )


@ft.observable
@dataclass
class FilePicker:
    """选文件：按钮 + 已选文件列表。

    Attributes:
        value: 已选文件，元素是 :class:`flet.FilePickerFile`（名称 / 大小 /
            绝对路径）；构造时也接受 ``Path`` 或 ``str``。
        allowed_extensions: 只允许的扩展名，不带点（``["pdf", "docx"]``）。
        allow_multiple: 一次是否可选多个；``False`` 时新选择覆盖旧的。
        on_change: 选择或移除文件后回调，参数是当前的 ``value``。
        dialog_title: 系统对话框标题；留空用系统默认。
        initial_directory: 打开时定位到的目录；留空用系统上次的位置。
    """

    value: list = field(default_factory=list)
    allowed_extensions: list = field(default_factory=list)
    allow_multiple: bool = True
    on_change: Callable | None = None
    # 以下三个是后加的可选参数，排在 on_change 之后：按位置写的旧调用不受影响
    dialog_title: str = ""
    initial_directory: str = ""

    def __post_init__(self):
        self.value = _as_picked(self.value or [])

    @ft.component
    def ui(self):
        tr = use_t()
        # 服务在构造时就注册到当前 page；每次重绘都 new 一个会攒下一串再也用不到
        # 的 FilePicker，所以一个组件实例只建一次。
        v_file_picker = ft.use_memo(ft.FilePicker, [])

        async def handle_files_pick(e):
            result = await v_file_picker.pick_files(
                dialog_title=self.dialog_title or None,
                initial_directory=self.initial_directory or None,
                allow_multiple=self.allow_multiple,
                allowed_extensions=list(self.allowed_extensions) or None,
                # 扩展名过滤只在 CUSTOM 下生效：只传 allowed_extensions 的话，
                # 对话框里仍然能看到全部文件。
                file_type=(
                    ft.FilePickerFileType.CUSTOM
                    if self.allowed_extensions
                    else ft.FilePickerFileType.ANY
                ),
            )
            # 取消时 flet 返回空列表而不是 None：此时保留上一次的选择，
            # 否则点「取消」反而把已经选好的文件清空了。
            if result:
                self.value = result
                self.notify()
                if self.on_change:
                    self.on_change(self.value)

        rows = _file_rows(self)
        return ft.Column(
            spacing=SPACE["2"],
            controls=[
                ft.Button(
                    content=ft.Text(tr("ui.file.choose")),
                    icon=ft.Icons.INSERT_DRIVE_FILE_OUTLINED,
                    on_click=handle_files_pick,
                ),
                # 没有文件时连框都不出现：空列表配一圈描边只是噪声
                *(
                    [
                        ft.Container(
                            padding=ft.Padding.symmetric(
                                horizontal=SPACE["2"], vertical=SPACE["1"]
                            ),
                            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                            border_radius=RADIUS["lg"],
                            content=ft.Column(spacing=0, tight=True, controls=rows),
                        )
                    ]
                    if rows
                    else []
                ),
            ],
        )


@ft.observable
@dataclass
class DirPicker:
    """选目录：按钮 + 绝对路径回显。

    Attributes:
        value: 已选目录；``None`` 表示还没选。
        on_change: 选择成功后回调，参数是 :class:`pathlib.Path`。
        dialog_title: 系统对话框标题；留空用系统默认。
        initial_directory: 打开时定位到的目录；留空用系统上次的位置。
    """

    value: Path | None = None
    on_change: Callable | None = None
    # 后加的可选参数排在 on_change 之后，按位置写的旧调用不受影响
    dialog_title: str = ""
    initial_directory: str = ""

    @ft.component
    def ui(self):
        tr = use_t()
        v_file_picker = ft.use_memo(ft.FilePicker, [])

        async def handle_dir_picker(e):
            selected_dir = await v_file_picker.get_directory_path(
                dialog_title=self.dialog_title or None,
                initial_directory=self.initial_directory or None,
            )
            if selected_dir:
                self.value = Path(selected_dir)
                self.notify()
                if self.on_change:
                    self.on_change(self.value)

        return ft.Row(
            spacing=SPACE["2"],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Button(
                    content=ft.Text(tr("ui.file.choose_dir")),
                    icon=ft.Icons.FOLDER_OPEN,
                    on_click=handle_dir_picker,
                ),
                _path_text(self.value),
            ],
        )


@ft.observable
@dataclass
class FileSaver:
    """另存为：先选目标路径，再由调用方写入内容。

    Attributes:
        value: 目标路径；``None`` 表示还没选。
        on_change: 选好路径后回调，参数是 :class:`pathlib.Path`。
        file_name: 对话框里的默认文件名（含后缀）；留空则由用户手写。
        dialog_title: 系统对话框标题；留空用系统默认。
        initial_directory: 打开时定位到的目录；留空用系统上次的位置。
    """

    value: Path | None = None
    on_change: Callable | None = None
    # 后加的可选参数排在 on_change 之后，按位置写的旧调用不受影响
    file_name: str = ""
    dialog_title: str = ""
    initial_directory: str = ""

    @ft.component
    def ui(self):
        tr = use_t()
        v_file_picker = ft.use_memo(ft.FilePicker, [])

        async def handle_save_file(e):
            selected_path = await v_file_picker.save_file(
                dialog_title=self.dialog_title or None,
                file_name=self.file_name or None,
                initial_directory=self.initial_directory or None,
            )
            if selected_path:
                self.value = Path(selected_path)
                self.notify()
                if self.on_change:
                    self.on_change(self.value)

        return ft.Row(
            spacing=SPACE["2"],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Button(
                    content=ft.Text(tr("ui.file.save")),
                    icon=ft.Icons.SAVE,
                    on_click=handle_save_file,
                ),
                _path_text(self.value),
            ],
        )

    def save_file(self, data: str | bytes):
        """把内容写进已选路径。``str`` 按 UTF-8 文本写，``bytes`` 按二进制写。

        没有目标路径时直接返回 —— 「另存为」还没选位置，写到哪里无从谈起。
        这里不吞写入异常：磁盘满、没权限要原样抛给调用方，界面才好提示。
        """
        if not self.value:
            _log.debug("FileSaver 还没有目标路径，忽略本次写入")
            return
        if isinstance(data, str):
            with open(self.value, "w", encoding="utf-8") as f:
                f.write(data)
        elif isinstance(data, bytes):
            with open(self.value, "wb") as f:
                f.write(data)
        else:
            _log.warning(
                "FileSaver.save_file 只接受 str / bytes，收到 %s",
                type(data).__name__,
            )


# ---------------------------------------------------------------------------
# 命令式服务：选择由视图模型发起时用（无控件、await 直接拿结果）
# ---------------------------------------------------------------------------


class FileDialogError(RuntimeError):
    """对话框不可用或调用失败。

    存在的意义是**把"失败"与"用户取消"分开**：取消是正常结果（返回 ``None``
    或空列表），调用方一般什么都不做；而"平台不支持目录框""服务没挂到页面上"
    必须让用户看见，不能和取消长成同一个返回值。
    """


class FileDialog:
    """命令式文件对话框：``await`` 拿结果，不参与渲染。

    声明式三件套解决"界面上放一个按钮"；但 MVVM 里选择往往由**视图模型**发起
    —— 它只发一条"请用户挑个目录"的请求，根本不知道控件长什么样。这时在视图层
    持有一个 :class:`FileDialog`，代替视图模型 ``await``，再把结果回喂回去。

    构造即注册：内部持有的 flet 服务会在 ``__init__`` 里挂到当前页，所以**必须在
    页面上下文里构造**（组件渲染期 ``use_ref(FileDialog)`` 最省事），并且**一个
    会话只建一份** —— 每帧 new 一个会攒下一串再也用不到的对话框服务。

    用法::

        dialog = use_ref(FileDialog).current      # 渲染期构造 = 注册到当前页

        folder = await dialog.pick_directory(title="选择导出目录")
        if folder is None:
            return                                # 用户取消，不是错误

        saved = await dialog.save_file(
            file_name="提交明细.csv", extensions=["csv"], data=csv_text
        )

    与声明式组件的分工：界面上要常驻一个「选择」按钮 + 结果回显 → 用
    :class:`FilePicker` / :class:`DirPicker` / :class:`FileSaver`；选择是一次性的、
    由业务流程触发 → 用本类。
    """

    def __init__(self) -> None:
        # Service 的 __post_init__ 会读当前页自动注册；不在页面上下文里构造时
        # 只构造不注册，第一次调用会在 _attached() 处给出一句人话。
        self._picker = ft.FilePicker()

    # ------------------------------------------------------------------ 入口
    async def pick_directory(
        self,
        *,
        title: str = "",
        initial: str | Path | None = None,
    ) -> Path | None:
        """选一个目录。用户取消返回 ``None``。

        Args:
            title: 对话框标题；留空用系统默认。
            initial: 打开时定位到的目录；留空用系统上次的位置。

        Raises:
            FileDialogError: 平台不支持（网页/移动端没有系统目录框）或调用失败。
        """
        self._attached()
        try:
            found = await self._picker.get_directory_path(
                dialog_title=title or None,
                initial_directory=_as_text(initial),
            )
        except Exception as exc:  # noqa: BLE001 —— 统一收敛成一种可捕获的失败
            raise FileDialogError(f"打开目录对话框失败：{exc}") from exc
        return Path(found) if found else None

    async def pick_files(
        self,
        *,
        title: str = "",
        initial: str | Path | None = None,
        extensions: Sequence[str] = (),
        multiple: bool = True,
    ) -> list[Path]:
        """选若干个文件。用户取消返回空列表。

        Args:
            title: 对话框标题；留空用系统默认。
            initial: 打开时定位到的目录；留空用系统上次的位置。
            extensions: 只允许的后缀，带不带点都行（``["csv", ".xlsx"]``）；
                留空则不过滤。
            multiple: 是否允许多选。

        Raises:
            FileDialogError: 平台不支持或调用失败。
        """
        self._attached()
        try:
            picked = await self._picker.pick_files(
                dialog_title=title or None,
                initial_directory=_as_text(initial),
                # 只传 allowed_extensions 时对话框仍会列出全部文件，必须切 CUSTOM
                file_type=_file_type(extensions),
                allowed_extensions=_extensions(extensions),
                allow_multiple=multiple,
            )
        except Exception as exc:  # noqa: BLE001
            raise FileDialogError(f"打开文件对话框失败：{exc}") from exc
        # 取消时 flet 返回 None（历史版本是空列表），两种都当"没选"
        return [Path(item.path) for item in picked or [] if item.path]

    async def save_file(
        self,
        *,
        file_name: str = "",
        title: str = "",
        initial: str | Path | None = None,
        extensions: Sequence[str] = (),
        data: str | bytes | None = None,
    ) -> Path | None:
        """另存为。用户取消返回 ``None``。

        给了 ``data`` 就由 flet 顺手写入（``str`` 按 UTF-8 编码）；不给则只拿到
        目标路径，写不写、写什么由调用方决定 —— 桌面端两种都支持。

        Args:
            file_name: 对话框里预填的文件名（含后缀）。
            title: 对话框标题；留空用系统默认。
            initial: 打开时定位到的目录；留空用系统上次的位置。
            extensions: 只允许的后缀；留空则不过滤。
            data: 要写入的内容。

        Raises:
            FileDialogError: 平台不支持或调用失败。
        """
        self._attached()
        try:
            saved = await self._picker.save_file(
                dialog_title=title or None,
                file_name=file_name or None,
                initial_directory=_as_text(initial),
                file_type=_file_type(extensions),
                allowed_extensions=_extensions(extensions),
                src_bytes=_payload(data),
            )
        except Exception as exc:  # noqa: BLE001
            raise FileDialogError(f"打开保存对话框失败：{exc}") from exc
        return Path(saved) if saved else None

    # ------------------------------------------------------------------ 内部
    def _attached(self) -> None:
        """服务没挂到页面上时给一句能照做的错误，而不是 flet 的原始异常。"""
        try:
            self._picker.page
        except RuntimeError as exc:
            raise FileDialogError(
                "对话框服务没有挂到页面上：请在页面上下文里构造 FileDialog"
                "（例如组件渲染期的 use_ref(FileDialog)）"
            ) from exc


def _as_text(path: str | Path | None) -> str | None:
    return str(path) if path else None


def _payload(data: str | bytes | None) -> bytes | None:
    """``str`` 统一按 UTF-8 编码；``None`` 表示"只要路径，不写内容"。"""
    return data.encode("utf-8") if isinstance(data, str) else data


def _extensions(extensions: Sequence[str]) -> list[str] | None:
    """去点、去空、转小写、去重；空列表转 ``None``（flet 认 ``None`` 为"不过滤"）。"""
    cleaned = list(
        dict.fromkeys(e.strip().lower().lstrip(".") for e in extensions if e.strip())
    )
    return cleaned or None


def _file_type(extensions: Sequence[str]) -> ft.FilePickerFileType:
    return (
        ft.FilePickerFileType.CUSTOM
        if _extensions(extensions)
        else ft.FilePickerFileType.ANY
    )


# ---------------------------------------------------------------------------
# 示例：全部用假数据回放「已经选过」的状态，渲染期不弹系统对话框
# ---------------------------------------------------------------------------
_DEMO_FILES = [
    ft.FilePickerFile(
        id=0,
        name="2026-Q3-经营分析.pdf",
        path="C:/Users/demo/Downloads/2026-Q3-经营分析.pdf",
        size=2_411_724,
    ),
    ft.FilePickerFile(
        id=1,
        name="门店清单.xlsx",
        path="C:/Users/demo/Downloads/门店清单.xlsx",
        size=38_912,
    ),
]

_DEMO_DIR = Path("C:/Users/demo/Documents/exports/2026-Q3")
_DEMO_LONG_DIR = Path(
    "C:/Users/demo/Documents/客户交付/2026-Q3/上海-华东区/导出的结果汇总"
)


@ft.component
def _echo(picker: FilePicker) -> ft.Control:
    """把 value 读出来：选完的结果只是一份状态，取数据是调用方的事。"""
    if not picker.value:
        text = "value：空（未选择）"
    else:
        total = sum(file.size or 0 for file in picker.value)
        text = (
            f"value：{len(picker.value)} 个文件 · "
            f"{get_human_file_size(total)} · 点行尾的 × 可移除"
        )
    return ft.Text(text, size=FONT_SIZE["small"], color=_MUTED)


@ft.component
def _dir_echo(picker: DirPicker) -> ft.Control:
    return ft.Text(
        f"value：{picker.value or 'None（未选择）'}",
        size=FONT_SIZE["small"],
        color=_MUTED,
    )


@ft.component
def _save_echo(picker: FileSaver) -> ft.Control:
    return ft.Text(
        f"value：{picker.value or 'None（未选择）'}",
        size=FONT_SIZE["small"],
        color=_MUTED,
    )


@ft.component
def _basic() -> ft.Control:
    picker = ft.use_memo(lambda: FilePicker(value=_DEMO_FILES), [])
    return ft.Column(spacing=SPACE["3"], controls=[picker.ui(), _echo(picker)])


@ft.component
def _filtered() -> ft.Control:
    """单选 + 后缀过滤：对话框里只剩 PDF / Word。"""
    picker = ft.use_memo(
        lambda: FilePicker(
            value=[_DEMO_FILES[0]],
            allow_multiple=False,
            allowed_extensions=["pdf", "docx"],
        ),
        [],
    )
    return ft.Column(
        spacing=SPACE["3"],
        controls=[picker.ui(), _echo(picker)],
    )


@ft.component
def _empty() -> ft.Control:
    picker = ft.use_memo(FilePicker, [])
    return ft.Column(spacing=SPACE["3"], controls=[picker.ui(), _echo(picker)])


@ft.component
def _dir_basic() -> ft.Control:
    picker = ft.use_memo(lambda: DirPicker(value=_DEMO_DIR), [])
    return ft.Column(spacing=SPACE["3"], controls=[picker.ui(), _dir_echo(picker)])


@ft.component
def _dir_empty() -> ft.Control:
    picker = ft.use_memo(DirPicker, [])
    return ft.Column(spacing=SPACE["3"], controls=[picker.ui(), _dir_echo(picker)])


@ft.component
def _dir_narrow() -> ft.Control:
    """420px 容器：路径先被压成省略号，按钮始终完整。"""
    picker = ft.use_memo(lambda: DirPicker(value=_DEMO_LONG_DIR), [])
    return ft.Column(
        spacing=SPACE["3"],
        controls=[
            ft.Container(width=420, content=picker.ui()),
            _dir_echo(picker),
        ],
    )


@ft.component
def _save_basic() -> ft.Control:
    picker = ft.use_memo(
        lambda: FileSaver(
            value=Path("C:/Users/demo/Documents/订单明细.xlsx"),
            file_name="订单明细.xlsx",
        ),
        [],
    )
    return ft.Column(spacing=SPACE["3"], controls=[picker.ui(), _save_echo(picker)])


@ft.component
def _save_guard() -> ft.Control:
    """没选路径时 save_file 是空操作：按钮点了也不会写出半个文件。"""
    picker = ft.use_memo(FileSaver, [])
    result, set_result = ft.use_state("")

    def try_write(_):
        picker.save_file("demo")
        set_result(
            "未选择路径 → save_file 直接返回，磁盘上什么都没发生"
            if not picker.value
            else f"已写入 {picker.value}"
        )

    return ft.Column(
        spacing=SPACE["3"],
        controls=[
            picker.ui(),
            ft.Row(
                spacing=SPACE["3"],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Button(
                        content=ft.Text("试写一次"),
                        on_click=try_write,
                    ),
                    ft.Text(result, size=FONT_SIZE["small"], color=_MUTED),
                ],
            ),
        ],
    )


@ft.component
def _dialog_demo() -> ft.Control:
    """按钮只负责"发起请求"，结果由 ``await`` 拿到后写进状态。"""
    # 渲染期构造即注册到当前页；一个组件实例只建一份
    dialog = ft.use_memo(FileDialog, [])
    result, set_result = ft.use_state("还没选")

    def choose(_e):
        async def run():
            try:
                folder = await dialog.pick_directory(title="选择导出目录")
            except FileDialogError as exc:
                set_result(f"失败：{exc}")
                return
            set_result(f"已选择：{folder}" if folder else "已取消")

        ft.context.page.run_task(run)

    return ft.Column(
        spacing=SPACE["3"],
        controls=[
            ft.Button(
                content=ft.Text("选择导出目录"),
                icon=ft.Icons.FOLDER_OPEN,
                on_click=choose,
            ),
            ft.Text(
                result,
                size=FONT_SIZE["small"],
                color=_MUTED,
                no_wrap=True,
                overflow=ft.TextOverflow.ELLIPSIS,
            ),
        ],
    )


@ft.component
def _dialog_save_demo() -> ft.Control:
    """另存为：一次 await 同时完成"选路径"与"写内容"（桌面端）。"""
    dialog = ft.use_memo(FileDialog, [])
    result, set_result = ft.use_state("还没保存")
    csv_text = "项目,变更\ncs-ui,3\n"

    def save(_e):
        async def run():
            try:
                saved = await dialog.save_file(
                    file_name="变更明细.csv",
                    title="导出变更明细",
                    extensions=["csv"],
                    data=csv_text,
                )
            except FileDialogError as exc:
                set_result(f"失败：{exc}")
                return
            set_result(f"已写入：{saved}" if saved else "已取消")

        ft.context.page.run_task(run)

    return ft.Column(
        spacing=SPACE["3"],
        controls=[
            ft.Button(
                content=ft.Text("另存为 CSV"),
                icon=ft.Icons.SAVE_OUTLINED,
                on_click=save,
            ),
            ft.Text(
                result,
                size=FONT_SIZE["small"],
                color=_MUTED,
                no_wrap=True,
                overflow=ft.TextOverflow.ELLIPSIS,
            ),
        ],
    )


_FILE_CODE = """picker = FilePicker(
    allowed_extensions=["pdf", "docx"],   # 非空时自动切到 CUSTOM 过滤
    allow_multiple=False,
)
Column([picker.ui()])

# 结果：元素带 name / size / path（取消时保留上一次的选择）
[f.path for f in picker.value]"""

_DIR_CODE = """picker = DirPicker(
    dialog_title="选择导出目录",
    initial_directory="D:/exports",
)
Column([picker.ui()])

# 选择成功后：
picker.value            # Path | None"""

_SAVE_CODE = """saver = FileSaver(file_name="订单明细.xlsx")
Column([saver.ui()])

# 用户选好路径之后（value 还是 None 时写入会被跳过）：
saver.save_file("订单号,金额\\nA-001,128.00")"""


_FILE_SPEC = Spec(
    name="FilePicker",
    summary="按钮加已选文件列表，把系统文件选择框的结果收成一份状态。",
    definition=(
        "选文件解决的是「内容在用户磁盘上」。它不读文件内容，只把用户选中的文件"
        "整理成 FilePickerFile（名称、大小、绝对路径）放进 value，并在每次选择或"
        "移除后回调。取消选择时保留上一次的结果 —— 用户点「取消」通常只是放弃这次"
        "改动，不是要把已经选好的文件清空。"
    ),
    anatomy=[
        (
            "选择按钮",
            "「选择文件」，点开系统对话框；allow_multiple 决定一次能选几个。",
        ),
        (
            "文件行",
            (
                "每个已选文件一行：类型图标、文件名、人类可读大小。文件名超长时单行"
                "省略，大小与移除按钮始终完整。"
            ),
        ),
        (
            "移除",
            "行尾的 × 按对象删掉这一条，不同目录下的同名文件不会一起消失。",
        ),
        (
            "外框",
            "有文件时才出现一圈发丝描边；没选时整块不占位，不留一个空框。",
        ),
        (
            "value",
            "已选文件的列表，顺序即选择顺序；on_change 收到的就是这个列表。",
        ),
    ],
    when=[
        "需要读取用户本地的文件内容：解析、上传、预览",
        "一次要选多个文件，并且希望就地看到文件名与大小",
        "只接受特定后缀：allowed_extensions 会切到 CUSTOM 过滤",
    ],
    avoid=[
        "选的是目录：用 DirPicker，文件对话框里点不中文件夹",
        "选图片并要缩略图：用 ImagePicker，它自带 150×150 预览",
        "要把内容写到用户挑的位置：用 FileSaver，选路径与写入一次完成",
    ],
    examples=[
        Example(
            "基础用法",
            _basic,
            hint="两个已选文件（假数据）；点行尾的 × 会从 value 移除，下方实时回读。",
            code=_FILE_CODE,
        ),
        Example(
            "单选与后缀过滤",
            _filtered,
            hint="allow_multiple=False 只留一个；allowed_extensions 非空时自动切到 CUSTOM。",
        ),
        Example(
            "空态",
            _empty,
            hint="还没选文件：只有按钮，没有空列表，也没有虚线框。",
        ),
    ],
    api=[
        Api("value", "list[FilePickerFile]", "[]", "已选文件；顺序即渲染顺序"),
        Api(
            "allowed_extensions",
            "list[str]",
            "[]",
            "只允许的扩展名（不带点）；非空时切到 CUSTOM 过滤",
        ),
        Api("allow_multiple", "bool", "True", "一次选多个；False 时新选择覆盖旧的"),
        Api(
            "on_change",
            "Callable[[list[FilePickerFile]], None] | None",
            "None",
            "选择或移除后回调，参数是当前 value",
        ),
        Api("dialog_title", "str", "''", "对话框标题；留空用系统默认"),
        Api("initial_directory", "str", "''", "打开时定位到的目录；留空用上次位置"),
        Api("ui()", "Control", "", "渲染按钮与已选列表"),
    ],
    notes=[
        tip(
            "allowed_extensions 只在 file_type=CUSTOM 时生效。组件在扩展名非空时自动"
            "切过去 —— 只传列表的话，对话框里其实还能看到全部文件。"
        ),
        warn(
            "取消选择时 flet 返回空列表而不是 None。组件只在结果非空时覆盖 value，"
            "否则点一次「取消」就会把已选文件清空。"
        ),
        info(
            "FilePicker 是 flet 的服务，构造即注册到当前 page；这里用 use_memo 只建"
            "一次，避免每次重绘都攒下一个再也用不到的服务。"
        ),
        info(
            "dialog_title / initial_directory 是三个选择器共有的可选参数，默认空串 —— "
            "组件把空串转成 None，等于沿用系统上次的位置。它们排在 on_change 之后，"
            "按位置写的旧调用不受影响。"
        ),
    ],
    tags=("文件", "选择文件", "file", "upload", "附件"),
)

_DIR_SPEC = Spec(
    name="DirPicker",
    summary="只选目录：一行按钮加绝对路径回显，结果是一个 Path。",
    definition=(
        "选目录和选文件的分界线在对话框本身：目录框不返回文件，结果是一个绝对路径。"
        "组件把按钮与路径排成一行，路径过长时先省略路径、保住按钮。选完只回写 value，"
        "不替调用方遍历目录 —— 要读哪些文件是业务的事。"
    ),
    anatomy=[
        ("选择按钮", "「选择文件夹」，打开系统的目录对话框。"),
        (
            "路径回显",
            "一行等宽感的文字，显示 str(value)；超出宽度用省略号收尾，悬停可看全路径。",
        ),
        (
            "布局",
            "按钮定宽、路径 expand：窄容器里压缩的是路径，按钮永远完整可点。",
        ),
        ("value", "Path 或 None。没选时是 None，回显行留白而不是写「未选择」。"),
    ],
    when=[
        "导出或批量下载前，让用户挑一个落地目录",
        "要处理某个目录下的整批文件，需要一个根路径",
        "路径本身要展示给用户确认（「将保存到 …」）",
    ],
    avoid=[
        "要选单个文件：DirPicker 的对话框里选不中文件",
        "要选图片并预览：用 ImagePicker，它按图片类型过滤",
        "路径来自配置或上次记录：别再让用户点一次，直接读",
    ],
    examples=[
        Example(
            "基础用法",
            _dir_basic,
            hint="已经选好一个目录（假数据）；点按钮换一个，路径回显跟着更新。",
            code=_DIR_CODE,
        ),
        Example(
            "空态",
            _dir_empty,
            hint="还没选：只剩按钮，不占一行空白。",
        ),
        Example(
            "窄容器",
            _dir_narrow,
            hint="420px 宽：长路径被压成省略号，按钮没有被挤出容器。",
        ),
    ],
    api=[
        Api("value", "Path | None", "None", "已选目录；取消选择时保持不变"),
        Api(
            "on_change",
            "Callable[[Path], None] | None",
            "None",
            "选择成功后回调，参数是 Path",
        ),
        Api("dialog_title", "str", "''", "对话框标题；留空用系统默认"),
        Api("initial_directory", "str", "''", "打开时定位到的目录；留空用上次位置"),
        Api("ui()", "Control", "", "渲染按钮与路径行"),
    ],
    notes=[
        tip(
            "get_directory_path 在网页模式下不可用（flet 直接抛异常）。桌面端才是它的"
            "主场，网页里请换成上传或手填路径。"
        ),
        info(
            "路径用单行省略而不是换行：目录可能很深，换行会把按钮顶到看不见的位置。"
            "完整路径放在 tooltip 里。"
        ),
    ],
    tags=("目录", "文件夹", "directory", "folder", "路径"),
)

_SAVE_SPEC = Spec(
    name="FileSaver",
    summary="先选目标路径，再由调用方写入：另存为对话框的薄壳。",
    definition=(
        "另存为把「到哪里存」和「存什么」拆开：对话框只负责拿到一个用户确认过的路径，"
        "内容由调用方通过 save_file 写进去。这样生成报表、导出 CSV 都能复用同一个按钮，"
        "而不必让组件知道数据长什么样。file_name 给一个默认文件名，省掉用户手打的几步。"
    ),
    anatomy=[
        ("保存按钮", "「保存文件」，打开系统的另存为对话框。"),
        (
            "路径回显",
            "一行文字显示目标路径；长路径省略，悬停看全。",
        ),
        (
            "默认文件名",
            "file_name 预填在对话框的文件名输入框里（含后缀），用户仍可改。",
        ),
        (
            "写入",
            "save_file(data)：str 按 UTF-8 文本写、bytes 按二进制写；没选路径时什么都不做。",
        ),
    ],
    when=[
        "把生成的内容（报表、导出文件）交给用户挑位置保存",
        "需要用户在系统对话框里改文件名或换目录",
        "同一份数据要能存成多个文件：路径由用户决定",
    ],
    avoid=[
        "上传文件到服务端：用 FilePicker",
        "只是选一个目录、不写文件：用 DirPicker",
        "固定写到缓存或安装目录：直接 open，弹框只会打断流程",
    ],
    examples=[
        Example(
            "基础用法",
            _save_basic,
            hint="已有一个目标路径（假数据）；file_name 让对话框预填好文件名。",
            code=_SAVE_CODE,
        ),
        Example(
            "未选择时的空操作",
            _save_guard,
            hint="点「试写一次」：value 还是 None，save_file 直接返回，磁盘上什么都没发生。",
        ),
    ],
    api=[
        Api("value", "Path | None", "None", "目标路径；None 表示还没选"),
        Api(
            "on_change",
            "Callable[[Path], None] | None",
            "None",
            "选好路径后回调，参数是 Path",
        ),
        Api("file_name", "str", "''", "对话框里预填的文件名（含后缀）"),
        Api("dialog_title", "str", "''", "对话框标题；留空用系统默认"),
        Api("initial_directory", "str", "''", "打开时定位到的目录；留空用上次位置"),
        Api("save_file(data)", "None", "", "把 str / bytes 写进 value；无路径时跳过"),
        Api("ui()", "Control", "", "渲染按钮与路径行"),
    ],
    notes=[
        warn(
            "写入异常（磁盘满、无权限、目录不存在）不会被吞掉，会原样抛给调用方 —— "
            "按钮回调里记得 try/except 并给出提示，否则界面上看不出失败。"
        ),
        info(
            "网页与移动端调 save_file 需要 src_bytes，桌面端才允许先拿路径后写入。"
            "本组件走的是后者。"
        ),
    ],
    tags=("另存为", "保存", "save", "导出", "download"),
)


_DIALOG_CODE = """dialog = use_ref(FileDialog).current   # 渲染期构造 = 注册到当前页

folder = await dialog.pick_directory(title="选择导出目录")
if folder is None:                      # 取消，不是错误
    return

saved = await dialog.save_file(
    file_name="提交明细.csv", extensions=["csv"], data=csv_text
)"""


_DIALOG_SPEC = Spec(
    name="FileDialog",
    summary="命令式对话框：await 一次拿结果，不渲染任何控件。",
    definition=(
        "选目录、选文件、另存为这三个动作在两种界面结构里发起方不同。声明式组件里"
        "是用户点按钮，控件自己拿着结果；而 MVVM 里是视图模型说「请用户挑个目录」，"
        "它只认识数据，不认识控件。FileDialog 把同一个系统对话框包成可 await 的"
        "服务：视图层持有实例并代为调用，结果（一个 Path 或 None）再回喂给视图模型。"
        "它不参与渲染，也不产生任何控件。"
    ),
    anatomy=[
        (
            "服务实例",
            "构造即注册到当前页；一个会话一份，别每帧 new。",
        ),
        (
            "pick_directory",
            "选一个目录，返回 Path；用户取消返回 None。",
        ),
        (
            "pick_files",
            "选若干文件，返回 Path 列表；取消返回空列表；extensions 控制后缀过滤。",
        ),
        (
            "save_file",
            "另存为，返回目标 Path；给了 data 就顺手写入，不给则只拿路径。",
        ),
        (
            "FileDialogError",
            "平台不支持或调用失败时抛这一个异常 —— 与「取消」严格区分。",
        ),
    ],
    when=[
        "MVVM / 状态驱动：选择由视图模型发起，界面上没有常驻按钮",
        "要按顺序编程：选完立刻拿结果继续下一步，而不是等 on_change 回调",
        "同一个应用里有好几处要用目录框，不想每处都摆一套按钮与回显",
    ],
    avoid=[
        "界面上要一直显示已选路径：用 DirPicker / FileSaver，状态自带回显",
        "选择结果要进表单校验：用声明式组件，value 就是表单字段",
        "上传文件到服务端：用 FilePicker 加 upload，本类只管选路径",
    ],
    examples=[
        Example(
            "命令式选目录",
            _dialog_demo,
            hint="点按钮才真正弹框；返回值写进下方文字，取消与失败分开显示。",
            code=_DIALOG_CODE,
        ),
        Example(
            "一次完成另存为",
            _dialog_save_demo,
            hint="save_file 带 data：选完路径就直接写入，不用再 open 一次。",
        ),
    ],
    api=[
        Api(
            "pick_directory(title, initial)",
            "Path | None",
            "",
            "选一个目录；取消返回 None",
        ),
        Api(
            "pick_files(title, initial, extensions, multiple)",
            "list[Path]",
            "[]",
            "选文件；取消返回空列表",
        ),
        Api(
            "save_file(file_name, title, initial, extensions, data)",
            "Path | None",
            "",
            "另存为；给 data 则一并写入",
        ),
        Api("FileDialogError", "Exception", "", "平台不支持或调用失败时抛出"),
        Api("", "", "", "构造必须在页面上下文里，否则调用时抛 FileDialogError"),
    ],
    notes=[
        info(
            "构造即注册：内部持有的 flet 服务在 __init__ 里就挂到当前页，"
            "所以要在渲染期构造（use_ref / use_memo），别在 async 任务里 new。"
        ),
        warn(
            "取消与失败必须分开处理：取消返回 None / []，失败抛 FileDialogError。"
            "把两者都当成 None，会让「对话框没弹出来」变成静默失败。"
        ),
        tip(
            "extensions 只在 file_type=CUSTOM 下才过滤，本类在 extensions 非空时"
            "自动切过去，调用方只传后缀即可（带不带点都行）。"
        ),
        info(
            "网页与移动端没有系统目录框，flet 直接抛异常 —— 本类会把它包成"
            "FileDialogError。桌面端才是它的主场。"
        ),
    ],
    tags=("对话框", "选目录", "另存为", "dialog", "directory", "save"),
)


SPECS: dict[str, Spec] = {
    "file_picker": _FILE_SPEC,
    "dir_picker": _DIR_SPEC,
    "file_saver": _SAVE_SPEC,
    "file_dialog": _DIALOG_SPEC,
}


if __name__ == "__main__":
    run(*SPECS.values())
