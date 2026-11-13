"""FileDialog 纯逻辑断言（不启窗口、不弹任何对话框）。

覆盖：后缀归一（去点/去空/转小写/去重）、文件类型推导、初始目录与内容编码、
"服务没挂到页面上"时的错误分类 —— 这条最关键：**取消**与**失败**必须是两种
结果，不能都变成 ``None``。

真正的系统对话框需要人点，交给 ``scripts/_doc_check.py`` 的渲染自检与应用端
真机确认；这里守的是不依赖窗口的那部分。

用法::

    python scripts/_file_dialog_logic.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ui.input.file_picker import (
    FileDialog,
    FileDialogError,
    _as_text,
    _extensions,
    _file_type,
    _payload,
)

_fails = 0
_passes = 0


def check(name: str, got: object, want: object) -> None:
    global _fails, _passes
    if got == want:
        _passes += 1
        print(f"PASS  {name}")
    else:
        _fails += 1
        print(f"FAIL  {name}: got={got!r} want={want!r}")


def check_raises(name: str, func, exc_type: type[BaseException]) -> None:
    global _fails, _passes
    try:
        func()
    except exc_type as exc:
        _passes += 1
        print(f"PASS  {name}（{exc}）")
    except BaseException as exc:  # noqa: BLE001
        _fails += 1
        print(f"FAIL  {name}: 抛了 {type(exc).__name__}，期望 {exc_type.__name__}")
    else:
        _fails += 1
        print(f"FAIL  {name}: 没有抛异常")


def main() -> int:
    # ---- 后缀归一 -------------------------------------------------------
    check("空序列 → None", _extensions([]), None)
    check("全是空白 → None", _extensions(["", "  "]), None)
    check("去点转小写", _extensions([".CSV", "Xlsx"]), ["csv", "xlsx"])
    check("去重保序", _extensions(["csv", ".csv", "txt"]), ["csv", "txt"])

    # ---- 文件类型 -------------------------------------------------------
    check("无后缀 → ANY", _file_type([]).value, "any")
    check("全空白后缀 → ANY", _file_type(["  "]).value, "any")
    check("有后缀 → CUSTOM", _file_type(["csv"]).value, "custom")

    # ---- 初始目录与内容编码 ---------------------------------------------
    check("初始目录 None", _as_text(None), None)
    check("初始目录空串", _as_text(""), None)
    check("初始目录 Path", _as_text(Path("D:/exports")), str(Path("D:/exports")))
    check("内容是 str → UTF-8", _payload("项目,变更\n"), "项目,变更\n".encode())
    check("内容是 bytes 原样", _payload(b"\x00\x01"), b"\x00\x01")
    check("没内容 → None（只取路径）", _payload(None), None)

    # ---- 失败分类：没挂到页面上 ------------------------------------------
    dialog = FileDialog()  # 不在页面上下文里构造 → 只构造不注册

    async def call() -> None:
        await dialog.pick_directory(title="x")

    check_raises(
        "未挂到页面 → FileDialogError",
        lambda: asyncio.run(call()),
        FileDialogError,
    )

    print(f"\n{_passes} passed, {_fails} failed")
    return 1 if _fails else 0


if __name__ == "__main__":
    sys.exit(main())
