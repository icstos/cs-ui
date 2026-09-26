"""Toast 轻提示组件。

与 :class:`~ui.feedback.message.Message` 的区别：

- ``Message`` 是标准 SnackBar，位于底部、带关闭按钮，适合“需要用户注意”的通知；
- ``Toast`` 是浮动轻提示，带图标、自动消失、不打断操作，适合“操作结果回执”。

两者都复用 :class:`~ui.core.constants.StyleType` 语义色，保证视觉一致。

用法::

    Toast(content="保存成功", style_type=StyleType.SUCCESS).show()
    toast_success("保存成功", page=page)      # 便捷函数，推荐

.. warning::
   目标页面必须用**关键字**传：``.show(page=page)``。

   写成 ``.show(page)`` 不会报错，但 ``page`` 会被绑到第一个位置参数
   ``content`` 上，于是 SnackBar 的内容指向页面本身，与 ``page._dialogs``
   构成**环形引用**；flet 配置控件树时永不终止，最后在某个完全无关的位置
   （例如 ``Button.icon`` 的 ``isinstance``）抛出 ``RecursionError``。
   组件内部已用 :func:`~ui.core.snackbar.ensure_snackbar_content` 把它变成
   一条可读的 ``TypeError``。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import field

import flet as ft

from ui.core.constants import FeedbackStyle, StyleType
from ui.core.snackbar import ensure_snackbar_content

__all__ = ["Toast"]

ICON_SIZE = 18
TEXT_SIZE = 14


@ft.control
class Toast(ft.SnackBar):
    """浮动轻提示。

    Args:
        content: 提示文本或自定义控件（沿用 SnackBar 的字段名，便于互换使用）。
        style_type: 语义类型（DEFAULT / PRIMARY / INFO / SUCCESS / WARNING / ERROR）。
        duration: 自动消失时间（毫秒），默认 2000。
        icon_size: 图标尺寸，默认 18。
        width: 自定义宽度，默认自适应。
    """

    content: ft.StrOrControl = ""
    style_type: StyleType = field(default_factory=lambda: StyleType.INFO)
    duration: int = 2000
    icon_size: int = ICON_SIZE
    width: int | float | None = None

    def init(self):
        self.behavior = ft.SnackBarBehavior.FLOATING
        self.show_close_icon = False
        self.close_icon_color = ft.Colors.WHITE
        self.margin = ft.Margin.only(bottom=24)
        self._apply_theme(self.style_type)
        self._apply_content(self.content)

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _apply_theme(self, style_type: StyleType) -> None:
        """根据语义类型设置配色。"""
        style = FeedbackStyle(*style_type.value)
        self._style = style
        self.bgcolor = (
            ft.Colors.GREY_800 if style_type == StyleType.DEFAULT else style.color
        )

    def _apply_content(self, message: ft.StrOrControl) -> None:
        """根据内容类型构建 SnackBar 内容。"""
        # 拦住 content=ft.Page：它会与 page._dialogs 构成环形引用，
        # 配置控件树时永不终止，最终在随机位置抛 RecursionError。
        ensure_snackbar_content(message, where="Toast")
        if isinstance(message, str):
            self.content = ft.Row(
                controls=[
                    ft.Icon(
                        icon=self._style.icon,
                        color=ft.Colors.WHITE,
                        size=self.icon_size,
                    ),
                    ft.Text(message, color=ft.Colors.WHITE, size=TEXT_SIZE),
                ],
                spacing=8,
                tight=True,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        else:
            self.content = message

    # ------------------------------------------------------------------
    # 公开 API
    # ------------------------------------------------------------------

    def show(
        self,
        content: ft.StrOrControl | None = None,
        *,
        style_type: StyleType | None = None,
        duration: int | None = None,
        page: ft.Page | None = None,
    ) -> None:
        """显示提示。

        Args:
            content: 临时替换的提示内容（``str`` 或控件）。**不要**把 ``page``
                传在这里 —— 位置参数绑定的是 ``content``，写成 ``.show(page)``
                会让 SnackBar 的内容指向页面本身，与 ``page._dialogs`` 构成环形
                引用并抛 ``RecursionError``；目标页面请用 ``page=`` 传。
            style_type: 临时覆盖的语义类型。
            duration: 临时覆盖的自动消失时间。
            page: 目标页面，默认取当前上下文页。
        """
        page = page or ft.context.page
        if style_type is not None:
            self._apply_theme(style_type)
        if content is not None:
            self._apply_content(content)
        if duration is not None:
            self.duration = duration
        page.show_dialog(self)

    def close(self, page: ft.Page | None = None) -> None:
        """主动关闭提示。"""
        (page or ft.context.page).pop_dialog()


def toast(
    message: ft.StrOrControl,
    style_type: StyleType = StyleType.INFO,
    duration: int = 2000,
    page: ft.Page | None = None,
) -> Toast:
    """便捷函数：创建并立即显示一条 Toast。"""
    t = Toast(content=message, style_type=style_type, duration=duration)
    t.show(page=page)
    return t


def toast_success(
    message: ft.StrOrControl, page: ft.Page | None = None, duration: int = 2000
) -> Toast:
    """成功提示。"""
    return toast(message, StyleType.SUCCESS, duration, page)


def toast_error(
    message: ft.StrOrControl, page: ft.Page | None = None, duration: int = 3000
) -> Toast:
    """错误提示。"""
    return toast(message, StyleType.ERROR, duration, page)


def toast_warning(
    message: ft.StrOrControl, page: ft.Page | None = None, duration: int = 2600
) -> Toast:
    """警告提示。"""
    return toast(message, StyleType.WARNING, duration, page)


def toast_info(
    message: ft.StrOrControl, page: ft.Page | None = None, duration: int = 2000
) -> Toast:
    """信息提示。"""
    return toast(message, StyleType.INFO, duration, page)


# 保留 typing 提示，方便调用方复用回调签名
ToastHandler = Callable[[ft.ControlEvent], None]


@ft.component
def App():
    """Toast 组件运行示例。"""
    page = ft.context.page

    def make_show(style_type: StyleType, text: str):
        def _show(e):
            Toast(content=text, style_type=style_type).show(page=page)

        return _show

    return ft.Column(
        controls=[
            ft.Text("Toast 轻提示", size=20, weight=ft.FontWeight.BOLD),
            ft.Text("浮动显示、自动消失，适合操作结果回执", size=13, color="#6b7280"),
            ft.Divider(),
            ft.Row(
                wrap=True,
                spacing=12,
                controls=[
                    ft.Button(
                        "默认",
                        on_click=make_show(StyleType.DEFAULT, "这是一条默认提示"),
                    ),
                    ft.Button(
                        "成功",
                        on_click=make_show(StyleType.SUCCESS, "保存成功！"),
                    ),
                    ft.Button(
                        "警告",
                        on_click=make_show(StyleType.WARNING, "磁盘空间不足"),
                    ),
                    ft.Button(
                        "错误",
                        on_click=make_show(StyleType.ERROR, "请求失败，请重试"),
                    ),
                    ft.Button(
                        "信息",
                        on_click=make_show(StyleType.INFO, "已加载 12 条记录"),
                    ),
                ],
            ),
        ]
    )


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
