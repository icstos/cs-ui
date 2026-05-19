import flet as ft
from typing import Any


def resolve_icon(icon: Any):
    """将字符串图标名解析为 Flet 图标对象"""
    if icon is None:
        return None
    if isinstance(icon, str):
        resolved = getattr(ft.Icons, icon.upper(), None)
        return resolved if resolved is not None else ft.Icon(icon)
    return icon
