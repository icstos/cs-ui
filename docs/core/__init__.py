"""文档站核心工具。"""

from __future__ import annotations

from docs.core.assets import (
    FONT_FAMILY,
    FONT_FILE,
    I18N_DIR,
    LOGO_FILE,
    PACKAGE_VERSION,
    SITE_I18N_DIR,
)
from docs.core.state import use_stable

__all__ = [
    "FONT_FAMILY",
    "FONT_FILE",
    "I18N_DIR",
    "LOGO_FILE",
    "PACKAGE_VERSION",
    "SITE_I18N_DIR",
    "use_stable",
]
