"""文档站使用的路径与版本信息。"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

DOCS_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = DOCS_ROOT.parent
UI_ROOT = PROJECT_ROOT / "src" / "ui"

FONT_FILE = UI_ROOT / "data" / "fonts" / "AlibabaPuHuiTi-3-55-Regular.otf"
FONT_FAMILY = "AlibabaPuHuiTi"
LOGO_FILE = UI_ROOT / "data" / "images" / "logo.png"

I18N_DIR = DOCS_ROOT / "i18n"
SITE_I18N_DIR = I18N_DIR / "site"


def _detect_version() -> str:
    """优先取已安装包的版本，源码运行时退回项目发布版本。"""
    try:
        return version("cs-ui")
    except PackageNotFoundError:
        return "0.1.1"


PACKAGE_VERSION = _detect_version()
