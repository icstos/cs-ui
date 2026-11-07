"""版本判定纯逻辑断言（不启窗口）。

覆盖：版本串解析（含预发布 / 垃圾输入）、受支持范围判定、跨系列硬失败与
同系列补丁版降级为警告、依赖上界生成。

真机上的观感与启动耗时属于渲染期，交给 smoke_test 与探针。

用法::

    python scripts/_version_logic.py
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ui import version as v

_passes = 0
_fails = 0


def check(name: str, got: object, want: object) -> None:
    global _fails, _passes
    if got == want:
        _passes += 1
        print(f"PASS  {name}")
    else:
        _fails += 1
        print(f"FAIL  {name}: got={got!r} want={want!r}")


def gate(text: str) -> tuple[str, str]:
    """把守卫跑一遍，返回 (结论, 完整提示语)。

    结论取值：``ok`` / ``warn`` / ``error``。返回**完整**文本而不是首行 ——
    "照着做"的安装命令在第二行，只比首行会漏掉它。
    """
    original = v.FLET_VERSION
    v.FLET_VERSION = text
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            try:
                v.require_flet()
            except ImportError as exc:
                return "error", str(exc)
            if caught:
                return "warn", str(caught[0].message)
            return "ok", ""
    finally:
        v.FLET_VERSION = original


print("=== 版本串解析 ===")
check("常规三段", v._parse("1.1.2"), (1, 1, 2))
check("缺补丁位补 0", v._parse("1.2"), (1, 2, 0))
check("预发布取前面三段", v._parse("1.2.0rc1"), (1, 2, 0))
check("带本地标记", v._parse("1.1.2+local"), (1, 1, 2))
check("垃圾输入", v._parse("garbage"), None)
check("空输入", v._parse(""), None)

print()
print("=== 依赖上界 ===")
check("1.1 -> 1.2", v._next_minor("1.1"), "1.2")
check("2.9 -> 2.10", v._next_minor("2.9"), "2.10")
check("坏输入不抛", v._next_minor("x"), "x.999")

print()
print("=== 守卫：本系列 ===")
check("当前受支持版本放行", gate(v.FLET_MIN)[0], "ok")
check("更高补丁版放行", gate("1.1.9")[0], "ok")
check("低于下限只警告", gate("1.1.0")[0], "warn")
check("警告里带上限数字", "1.1.2" in gate("1.1.0")[1], True)

print()
print("=== 守卫：跨系列 ===")
verdict, msg = gate("1.2.0")
check("1.2 硬失败", verdict, "error")
check("错误里说清受支持范围", "1.1.x" in msg, True)
check("错误里给升级命令", "pip install" in msg, True)
check("2.0 同样硬失败", gate("2.0.0")[0], "error")

print()
print("=== 守卫：缺失 ===")
check("空版本串按未安装处理", gate("")[0], "error")
check("垃圾版本串按未安装处理", gate("garbage")[0], "error")

print()
print("=== 元数据一致性 ===")
check(
    "FLET_MIN 与 FLET_SERIES 不矛盾",
    v._parse(v.FLET_MIN)[:2],
    tuple(map(int, v.FLET_SERIES.split("."))),
)
check("包版本非空", bool(v.__version__), True)
check("运行时 flet 版本被识别", v._parse(v.FLET_VERSION) is not None, True)

print()
print("==============================================")
print(f"{_passes} passed, {_fails} failed")
raise SystemExit(1 if _fails else 0)
