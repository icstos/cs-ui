"""按当前 Flet 平台选择系统字体族。"""

from __future__ import annotations

from typing import TypedDict

import flet as ft

__all__ = [
    "active_family",
    "apply_fonts",
    "body_font_fallback",
    "get_body_font_config",
    "get_monospace_font_config",
    "monospace_family",
    "monospace_font_fallback",
]


class FontConfig(TypedDict):
    font_family: str
    fallback: list[str]


_BODY_FONTS: dict[str, FontConfig] = {
    "windows": {
        "font_family": "Segoe UI",
        "fallback": ["Microsoft YaHei", "sans-serif"],
    },
    "macos": {
        "font_family": "Helvetica Neue",
        "fallback": ["PingFang SC", "sans-serif"],
    },
    "ios": {
        "font_family": "Helvetica Neue",
        "fallback": ["PingFang SC", "sans-serif"],
    },
    "android": {
        "font_family": "Roboto",
        "fallback": ["Source Han Sans CN", "sans-serif"],
    },
    "linux": {
        "font_family": "DejaVu Sans",
        "fallback": ["Noto Sans CJK SC", "sans-serif"],
    },
    "web": {
        "font_family": "system-ui",
        "fallback": [
            "-apple-system",
            "BlinkMacSystemFont",
            "Segoe UI",
            "Roboto",
            "Helvetica Neue",
            "Arial",
            "Microsoft YaHei",
            "sans-serif",
        ],
    },
}

_MONOSPACE_FONTS: dict[str, FontConfig] = {
    "windows": {
        "font_family": "Consolas",
        "fallback": ["Microsoft YaHei", "monospace"],
    },
    "macos": {"font_family": "Menlo", "fallback": ["PingFang SC", "monospace"]},
    "ios": {"font_family": "Menlo", "fallback": ["PingFang SC", "monospace"]},
    "android": {
        "font_family": "Droid Sans Mono",
        "fallback": ["Roboto Mono", "Source Han Sans CN", "monospace"],
    },
    "linux": {
        "font_family": "DejaVu Sans Mono",
        "fallback": ["Noto Sans CJK SC", "monospace"],
    },
    "web": {
        "font_family": "Consolas",
        "fallback": [
            "Menlo",
            "Monaco",
            "Courier New",
            "Microsoft YaHei",
            "monospace",
        ],
    },
}

_platform: ft.PagePlatform | str | None = None


def _platform_key(platform: ft.PagePlatform | str | None) -> str:
    value = getattr(platform, "value", platform)
    return str(value).lower() if value is not None else ""


def get_body_font_config(platform: ft.PagePlatform | str | None) -> FontConfig:
    """获取平台正文字体及中文、通用回退字体。"""
    config = _BODY_FONTS.get(
        _platform_key(platform),
        {"font_family": "sans-serif", "fallback": []},
    )
    return {
        "font_family": config["font_family"],
        "fallback": list(config["fallback"]),
    }


def get_monospace_font_config(
    platform: ft.PagePlatform | str | None,
) -> FontConfig:
    """获取平台等宽字体及中文、通用回退字体。"""
    config = _MONOSPACE_FONTS.get(
        _platform_key(platform),
        {"font_family": "monospace", "fallback": []},
    )
    return {
        "font_family": config["font_family"],
        "fallback": list(config["fallback"]),
    }


def body_font_fallback() -> list[str]:
    """获取当前平台正文字体回退族。"""
    return get_body_font_config(_platform)["fallback"]


def monospace_family() -> str:
    """获取当前平台的首选等宽字体族。"""
    return get_monospace_font_config(_platform)["font_family"]


def monospace_font_fallback() -> list[str]:
    """获取当前平台等宽字体回退族。"""
    return get_monospace_font_config(_platform)["fallback"]


def active_family() -> str:
    """获取当前正文字体族，优先使用应用显式设置的字体。"""
    from ui.core.theme import theme_state

    return (
        theme_state().font_family
        or get_body_font_config(_platform)["font_family"]
    )


def apply_fonts(page: ft.Page, family: str | None = None) -> str:
    """记录页面平台并返回正文字体族，不注册字体资源。

    保留旧函数名以兼容现有调用。系统字体由操作系统提供，因此本函数只记录当前
    平台；``family`` 可用于返回应用显式指定的字体。
    """
    global _platform
    _platform = (
        "web" if getattr(page, "web", False) else getattr(page, "platform", None)
    )
    if family:
        return family
    return active_family()
