"""SnackBar 派生组件（``Toast`` / ``Message``）的 ``content`` 守卫。

为什么需要这一道
----------------
``Toast.show()`` 与 ``Message.show()`` 的签名是::

    show(self, content=None, *, style_type=None, duration=None, page=None)

``content`` 是第一个位置参数，于是 ``Toast(...).show(page)`` 不会报错 ——
``page`` 被**静默绑到 content 上**，紧接着 ``page.show_dialog(self)`` 让
``self.content`` 直接指向 Page。控件图变成::

    Page -> Dialogs -> Toast -> content=Page -> Dialogs -> ...

一个**直接环**。flet 配置控件树时（``DiffBuilder._configure_dataclass``）
对这个环永不终止，最后在某个**完全无关**的位置炸出::

    RecursionError: maximum recursion depth exceeded
    flet/controls/material/button.py:134 in <lambda>
        isinstance(ctrl.icon, IconData)

报错行是随机的 —— 那只是"栈刚好用尽时执行的下一个函数调用"（``EnumType``
的 ``__instancecheck__`` 恰好需要新栈帧）。照着 traceback 去查 `Button.icon`
查不出任何东西，真正的答案在控件图里的环。

为什么不靠 flet 自带的校验器
----------------------------
``SnackBar.content`` 挂的是 ``V.str_or_visible_control()``，但
``issubclass(ft.Page, ft.Control) is True`` —— Page 能通过这个校验，
环照样成立。所以必须显式拦住 ``ft.Page``。

排查手法
--------
``python scripts/_config_depth_probe.py --app <宿主>``
会打印出环的完整路径，例如::

    CYCLE! Toast -> Page -> Dialogs -> list(1) -> Toast
"""

from __future__ import annotations

from typing import Any

import flet as ft

__all__ = ["ensure_snackbar_content"]


def ensure_snackbar_content(value: Any, *, where: str) -> None:
    """挡住"把 Page 当成 SnackBar 内容"的写法。

    这是唯一会让 ``content`` 成环的取值，所以只拦 ``ft.Page``；
    其余 ``str`` / 任意 ``Control`` 都是合法内容。

    Args:
        value: 即将写入 ``content`` 的值。
        where: 出错时用来指明调用点，例如 ``"Toast.show()"``。

    Raises:
        TypeError: 当 ``value`` 是 ``ft.Page`` 时。
    """
    if isinstance(value, ft.Page):
        raise TypeError(
            f"{where} 的 content 收到了 ft.Page。\n"
            "  原因：content 是 show() 的第一个位置参数，写成 `.show(page)` 会把 "
            "page 绑到 content 上；page.show_dialog(self) 之后 content 指向 Page，"
            "与 page._dialogs 构成环形引用，最终抛 RecursionError（报错位置随机）。\n"
            "  改法：`.show(page=page)`，或直接用 toast_info(...) / toast_success(...) "
            "这类便捷函数。"
        )
