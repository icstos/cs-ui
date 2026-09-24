"""控件树配置深度探针 —— 定位 `RecursionError: maximum recursion depth exceeded`。

背景
----
flet 在把控件树交给 Flutter 之前，会从根控件开始**递归**配置整棵 dataclass 树
（`flet.controls.object_patch.DiffBuilder._configure_dataclass`，1.0.0 约 1593-1690 行），
逐层走 `dataclass 字段 → 列表元素 → 子控件`。所以：

- 正常控件树**极浅**（本仓库 demo 实测 16~24 层，递归上限 1000）；
- 一旦出现**环形引用**（A 的字段里有 B、B 又引用回 A），这个递归永不终止，
  最终在某个**完全无关的位置**炸出 `RecursionError`。

⚠️ 别去追 traceback 的最后一行。实测：报错会落在
`flet/controls/material/button.py:134` 的 `isinstance(ctrl.icon, IconData)` 上，
只因为那里是"栈刚好用尽时执行的下一个函数调用"（`EnumType.__instancecheck__`
需要新栈帧）。同一棵树换个规模，报错行就会换到别处。

本脚本给出真正的答案：**最大深度** + **环形引用的完整路径**。

用法::

    python scripts/_config_depth_probe.py --app examples/demo.py
    python scripts/_config_depth_probe.py --app scripts/_shot_page.py --page FormPage
    python scripts/_config_depth_probe.py --selftest      # 自检：造环给探针抓

判读::

    max_depth=24 limit=1000 无环形引用
        → 树是健康的；RecursionError 只可能来自环形引用或组件自我重渲染
    CYCLE! Column -> list(1) -> Column -> list(1) -> Column
        → 元凶就是它。按这个路径回代码里改（谁把谁塞进了谁）。

退出码：无环 0；发现环 1。适合当回归门禁。
"""

from __future__ import annotations

import argparse
import asyncio
import os
import runpy
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import flet as ft  # noqa: E402
from flet.controls import object_patch  # noqa: E402

LIMIT = sys.getrecursionlimit()

#: 超过该深度就提前提示（远低于递归上限，便于早发现苗头）
WARN_DEPTH = 64

REPORTED = False


class Tracker:
    """记录配置递归深度，并检测环形引用。"""

    def __init__(self) -> None:
        self.depth = 0
        self.max_depth = 0
        self.stack: list[tuple[str, int]] = []
        self.cycle: list[str] | None = None

    def enter(self, item) -> None:
        self.depth += 1
        self.max_depth = max(self.max_depth, self.depth)
        label = type(item).__name__
        if isinstance(item, (list, tuple, dict)):
            label = f"{label}({len(item)})"
        self.stack.append((label, id(item)))

        if self.cycle is None:
            # 只在**首次**发现重复时记录：那一刻的链路就是最短的那个环；
            # 之后再发现重复只会拿到同一个环的更长绕法。
            # 从近到远找，取最近的一个同 id 祖先。
            for i in range(len(self.stack) - 2, -1, -1):
                if self.stack[i][1] == id(item):
                    self.cycle = [f"{n}#{o}" for n, o in self.stack[i:]]
                    break

        if self.depth >= WARN_DEPTH and self.depth % WARN_DEPTH == 0:
            trail = " <- ".join(n for n, _ in self.stack[-4:-1])
            print(f"  ! depth={self.depth} 处于 {label}  (上游: {trail})")

    def leave(self) -> None:
        self.stack.pop()
        self.depth -= 1


TRACKER = Tracker()
_orig_configure = object_patch.DiffBuilder._configure_dataclass


def _patched(self, item, parent, frozen, configure_setattr_only=False):
    TRACKER.enter(item)
    try:
        yield from _orig_configure(self, item, parent, frozen, configure_setattr_only)
    finally:
        TRACKER.leave()


object_patch.DiffBuilder._configure_dataclass = _patched


def report() -> int:
    global REPORTED
    if REPORTED:
        return 1 if TRACKER.cycle else 0
    REPORTED = True
    print()
    if TRACKER.cycle:
        print("CYCLE! 检测到环形引用（配置递归不会终止）:")
        print("       " + " -> ".join(TRACKER.cycle))
        print(f"max_depth={TRACKER.max_depth} limit={LIMIT}")
        return 1
    print(f"@@CONFIG_DEPTH@@ max_depth={TRACKER.max_depth} limit={LIMIT} 无环形引用")
    return 0


# ----------------------------------------------------------------------
# 自检
# ----------------------------------------------------------------------


def selftest() -> None:
    """故意构造环形控件树，验证探针能识别出环。

    用**间接环**（A 含 B、B 含 A）：直接自引用会被 flet 自己的
    `ObjectPatchException: Parent is the same as item` 拦住，
    间接环能逃过那个守卫，一路递归到 `RecursionError` —— 即线上报的那个错的成因。
    """
    sys.setrecursionlimit(400)  # 让溢出早点发生，别等 1000
    print("[selftest] 构造 Column A -> Column B -> A 的间接环…")
    a = ft.Column()
    b = ft.Column(controls=[a])
    a.controls.append(b)

    @ft.component
    def Broken():
        return a

    async def scenario(page: ft.Page) -> None:
        try:
            page.render(Broken)
            page.update()
        except RecursionError:
            print("[selftest] 如期抛出 RecursionError（与线上症状一致）")
        sys.stdout.flush()
        os._exit(report())

    ft.run(lambda page: page.run_task(scenario, page), view=ft.AppView.FLET_APP_HIDDEN)


# ----------------------------------------------------------------------
# 探针
# ----------------------------------------------------------------------


def probe(app_path: str, page_name: str, wait: float) -> None:
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    if page_name:
        os.environ["CS_UI_SHOT_PAGE"] = page_name

    print(f"[probe] 运行 {app_path}，{wait}s 后自动出报告…")
    real_run = ft.run

    def run_and_watch(main, *args, **kwargs):
        def wrapped(page: ft.Page) -> None:
            main(page)

            async def watch() -> None:
                await asyncio.sleep(wait)
                code = report()
                sys.stdout.flush()
                try:
                    await page.window.close()
                except Exception:
                    pass
                os._exit(code)

            page.run_task(watch)

        return real_run(wrapped, *args, **kwargs)

    ft.run = run_and_watch  # type: ignore[assignment]
    try:
        runpy.run_path(app_path, run_name="__main__")
    except SystemExit:
        pass
    except BaseException:  # noqa: BLE001
        print("[probe] 宿主抛出异常，栈顶几帧：")
        traceback.print_exc()
    sys.stdout.flush()
    os._exit(report())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", help="被测宿主应用（如 examples/demo.py）")
    parser.add_argument("--page", help="传给宿主的页面名（CS_UI_SHOT_PAGE，可选）")
    parser.add_argument("--wait", type=float, default=8.0, help="启动后观察秒数，默认 8")
    parser.add_argument("--selftest", action="store_true", help="自检：造环给探针抓")
    args = parser.parse_args()

    if args.selftest:
        selftest()
        return
    if not args.app:
        parser.error("需要 --app <宿主应用> 或 --selftest")
    probe(args.app, args.page, args.wait)


if __name__ == "__main__":
    main()
