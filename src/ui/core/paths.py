"""平台目录 —— 配置 / 日志 / 缓存的落点，全框架共用的**零依赖**模块。

单独拆出来是为了打断循环：:mod:`ui.core.config` 要算日志目录，:mod:`ui.core.i18n`
要算配置目录，而 i18n 又依赖 config（拿 logger）。把「目录怎么算」放进这个不 import
任何 ``ui`` 模块的小文件，两边都只依赖它。

为什么不用"项目根 / 包目录"
--------------------------
``Path(__file__).parents[n]`` 只在源码树里成立。装成 wheel 之后同一个表达式指向
``site-packages``；冻结成 exe 之后指向解包出来的临时目录。往上写日志的最坏结果是
**导入即崩溃**（只读盘），最好结果是日志散落在没人找得到的地方。

所以默认落在用户可写目录（跟随平台惯例），并允许用 ``CS_UI_LOG_DIR`` 覆盖。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

__all__ = ["APP_DIR_NAME", "config_dir", "log_dir"]

#: 用户目录下的应用文件夹名（与 pyproject 的 ``cs-ui`` 一致）
APP_DIR_NAME = "cs-ui"


def config_dir() -> Path:
    """配置文件目录（跟随平台惯例）。

    ``FLET_APP_STORAGE_DATA`` 优先 —— flet 打包运行时会注入一个沙箱目录，
    在那种环境下 ``LOCALAPPDATA`` 往往不可写。
    """
    env = os.getenv("FLET_APP_STORAGE_DATA")
    if env:
        return Path(env)
    if sys.platform == "win32":
        base = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA")
        return Path(base or Path.home(), APP_DIR_NAME)
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_DIR_NAME
    return Path(os.getenv("XDG_CONFIG_HOME") or Path.home() / ".config") / APP_DIR_NAME


def log_dir() -> Path:
    """日志目录。``CS_UI_LOG_DIR`` 可覆盖（CI / 容器里指到挂载卷上）。"""
    override = os.getenv("CS_UI_LOG_DIR")
    if override:
        return Path(override)
    return Path(config_dir()) / "log"
