"""让有状态组件在语言切换时安全重建。"""

from __future__ import annotations

from collections.abc import Callable
from typing import cast

import flet as ft

from ui import use_i18n

#: 语言切换后需要从旧实例搬移的用户输入字段。
_CARRIED_FIELDS = ("value", "start_value", "end_value", "selected")


def use_stable[T](factory: Callable[[], T]) -> T:
    """返回跨渲染稳定的实例，并在语言变化时用新文案重建。

    ``ui`` 中交互式组件把标签、候选列表作为构造参数，实例被 ref 固定后
    切语言会停留在旧文案。这里在语言变化时重建实例，再以绕过 observable
    通知的方式搬移用户已填写的值，避免渲染期回环。
    """
    locale = use_i18n().locale
    box = cast(ft.Ref[T | None], ft.use_ref(None))
    stamp = cast(ft.Ref[str | None], ft.use_ref(None))

    if box.current is None or stamp.current != locale:
        previous = box.current
        instance = factory()
        box.current = instance
        stamp.current = locale
        if previous is not None:
            for field in _CARRIED_FIELDS:
                if hasattr(previous, field) and hasattr(instance, field):
                    object.__setattr__(instance, field, getattr(previous, field))
    return cast(T, box.current)
