"""版本信息 —— 全仓唯一的版本事实源。

框架与 flet 之间是**紧耦合**的：组件直接实例化 ``ft.*`` 控件、直接读
``ColorScheme`` 角色，flet 一个小版本的行为变化（例如 1.1.0 把默认表面从
"带种子色偏的灰"换成中性灰、并引入带类型的 ``ScrollKey``）都会立刻体现在界面上。
所以版本不能散落在 pyproject / README / 文档站三处各写一遍 —— 那样必然漂移，
现实中已经漂过一次（``flet==1.1.0`` 与 ``__version__ = "0.0.5"`` 对不上
``pyproject`` 的 ``0.1.1``）。

本模块提供三个东西：

* :data:`__version__` / :data:`FLET_VERSION` —— **运行时实际**版本，给文档站页脚、
  "关于"页、日志用。读的是安装元数据，源码运行时也不会说谎。
* :data:`FLET_MIN` / :data:`FLET_SERIES` —— **受支持范围**，给依赖声明与版本守卫用。
* :func:`require_flet` —— 启动时的守卫，把"版本不对"变成一句能照着做的话，
  而不是若干层之后莫名其妙的 ``AttributeError``。

用法::

    from ui.version import FLET_VERSION, __version__

    print(f"cs-ui {__version__} on flet {FLET_VERSION}")
"""

from __future__ import annotations

import re
import warnings

__all__ = [
    "FLET_MIN",
    "FLET_SERIES",
    "FLET_VERSION",
    "__version__",  # noqa: F822 - 由模块级 __getattr__ 提供（惰性），不是字面量
    "flet_version",
    "require_flet",
    "ui_version",
]

#: 受支持的 flet 最低版本。
#:
#: 1.1.2 之前的两个补丁版各带去一个会咬到我们的问题：1.1.1 修了 Safari 下
#: 原始字节图片渲染空白（``Image(src=bytes)`` 是我们公开支持的形式），
#: 1.1.2 让 ``flet build`` / ``flet publish`` 只装 CLI 自己那一版 flet 扩展
#: （1.1.1 之前会装最新版，构建产物与开发环境能悄悄错开）。
FLET_MIN: str = "1.1.2"

#: 受支持的 flet 次版本系列（``major.minor``）。
#:
#: 只锁到次版本而不是 ``==1.1.2``：同一系列内的补丁版只修 bug、不加 API，
#: 允许自动前进；跨系列（1.2 / 2.0）必须回来重新验证一遍再放行。
FLET_SERIES: str = "1.1"

#: 源码目录直接运行（尚未 ``pip install``）时的兜底版本，与 pyproject 保持一致。
_FALLBACK_UI_VERSION: str = "0.2.0"

_VERSION_RE = re.compile(r"(\d+)\.(\d+)(?:\.(\d+))?")


def _parse(text: str) -> tuple[int, int, int] | None:
    """从任意版本串里取出 ``(major, minor, patch)``；解析不出返回 ``None``。

    刻意不用 ``packaging``：它是个真实依赖，而这里只需要"能比大小"。
    预发布/本地版本号（``1.2.0rc1``、``1.1.2+local``）也照前面三段取。
    """
    m = _VERSION_RE.search(str(text or ""))
    if not m:
        return None
    return int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)


def _dist_version(name: str) -> str:
    """读安装元数据里的版本。**函数内导入** —— 见 :func:`ui_version` 的说明。"""
    from importlib.metadata import version

    return version(name)


def ui_version() -> str:
    """cs-ui 自身的版本。

    优先读安装元数据（``pip install -e .`` 与打包产物都对）；从源码目录直接跑
    （没装过）时退回 :data:`_FALLBACK_UI_VERSION`。

    ``importlib.metadata`` 在这里**才**导入：它是 ``ui_version`` / ``flet_version``
    唯一需要它的地方，而模块级的 ``from importlib.metadata import ...`` 会连带加载
    ``email`` / ``zipfile`` / ``importlib.resources``（实测 36ms）。版本号不是启动
    关键路径，不该由它为整个框架的导入买单。
    """
    from importlib.metadata import PackageNotFoundError

    try:
        return _dist_version("cs-ui")
    except PackageNotFoundError:
        return _FALLBACK_UI_VERSION


def flet_version() -> str:
    """当前**已安装**的 flet 版本；没装返回空串。

    首选 ``flet.__version__`` —— 这是一次普通属性读取，**零成本**，而且此刻 flet
    必然已经在 ``sys.modules`` 里（``ui`` 的全部功能都建立在它之上）。

    历史写法走 ``importlib.metadata.version("flet")``，看起来"更权威"，实际代价是
    拖进整个 ``importlib.metadata`` 机制（连带 ``email.parser`` / ``zipfile``）——
    实测 ``import ui`` 130ms 里有 38ms 花在这里，为了一句版本号。只有拿不到
    ``flet.__version__``（极老的 flet、或被裁剪过的发行版）时才退回去问元数据。

    Returns:
        版本串（``"1.1.2"``）；两条路都失败返回空串 —— 交给 :func:`require_flet`
        去报，而不是在这里抛。
    """
    try:
        import flet as _flet

        return str(getattr(_flet, "__version__", "") or "")
    except Exception:  # noqa: BLE001, S110 - flet 未安装时 import 就会抛，走下面的兜底
        pass
    try:
        return _dist_version("flet")
    except Exception:  # noqa: BLE001 - 元数据里没有这个发行版
        return ""


#: 运行时实际 flet 版本（模块导入时取一次，够用；flet 不会在进程内变版本）。
FLET_VERSION: str = flet_version()


def __getattr__(name: str) -> str:
    """``__version__`` 惰性求值（PEP 562）。

    取自身的版本要走 ``importlib.metadata``，而**第一次**调用会连带加载整套元数据
    机制（约 37ms）。绝大多数进程从头到尾不显示版本号，没理由让每次启动都付这笔钱
    —— ``import ui`` 只做"能不能用"的判断（见 :func:`require_flet`），
    真正要版本号的人（关于页、CLI ``--version``）再触发。
    """
    if name == "__version__":
        value = ui_version()
        globals()["__version__"] = value  # 缓存：只算一次
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted({*globals(), "__version__"})


def _next_minor(series: str) -> str:
    """``"1.1"`` → ``"1.2"``（写依赖上界用，避免手写重复）。"""
    major, _, minor = series.partition(".")
    try:
        return f"{major}.{int(minor) + 1}"
    except ValueError:
        return f"{series}.999"


def require_flet(*, strict: bool = True) -> None:
    """校验 flet 版本，不合格就抛出**能照着做**的错误。

    Args:
        strict: ``True`` 时把跨系列（非 1.1.x）当作致命错误；``False`` 时只警告。
            工具脚本（例如批量生成文档）可以传 ``False``，避免因为环境里装了个
            更新的大版本就整批停下。

    Raises:
        ImportError: flet 未安装，或装的是未经验证的系列。

    版本在该系列内但低于 :data:`FLET_MIN` 时只发一次 :class:`UserWarning` ——
    1.1.0 / 1.1.1 上跑得起来，只是带着已知缺陷，不该拦死使用者。
    """
    found = _parse(FLET_VERSION)
    if found is None:
        raise ImportError(
            "cs-ui 需要 flet，但没有检测到已安装的 flet。"
            f"请先安装：pip install 'flet[all]>={FLET_MIN},<{_next_minor(FLET_SERIES)}'"
        )

    series = f"{found[0]}.{found[1]}"
    if series != FLET_SERIES:
        msg = (
            f"cs-ui 只验证过 flet {FLET_SERIES}.x（>= {FLET_MIN}），"
            f"当前装的是 {FLET_VERSION}。\n"
            f"请安装受支持的范围：pip install 'flet[all]>={FLET_MIN},"
            f"<{_next_minor(FLET_SERIES)}'"
        )
        if strict:
            raise ImportError(msg)
        warnings.warn(msg, UserWarning, stacklevel=2)
        return

    if found < _parse(FLET_MIN):
        warnings.warn(
            f"flet {FLET_VERSION} 低于受支持的 {FLET_MIN}，"
            "已知缺陷可能在图片解码、web 构建版本钉定上表现出来。"
            f"建议升级：pip install -U 'flet[all]>={FLET_MIN}'",
            UserWarning,
            stacklevel=2,
        )
