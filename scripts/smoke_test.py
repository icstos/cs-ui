"""无头渲染冒烟测试（flet 1.0.0）。

在 ``AppView.FLET_APP_HIDDEN`` 模式下真实启动 Flet 运行时，渲染指定组件，
（可选）依次访问所有路由，捕获组件构建期间的任何异常。

这在没有人工点击 GUI 的情况下，能可靠地发现「组件在 1.0.0 下渲染即崩溃」的问题。

用法::

    python scripts/smoke_test.py examples.demo              # 渲染 module 的 App
    python scripts/smoke_test.py examples.demo Home         # 指定组件名
    python scripts/smoke_test.py ui.input.rating main       # 传统 main(page) 入口
    python scripts/smoke_test.py examples.demo --routes /,/general,/form

退出码：0 = 全部渲染成功；1 = 存在异常。
"""

from __future__ import annotations

import argparse
import asyncio
import importlib
import os
import sys
import traceback
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import flet as ft  # noqa: E402

RESULT: dict[str, list[str]] = {"ok": [], "fail": []}


def _record(name: str, error: BaseException | None) -> None:
    if error is None:
        RESULT["ok"].append(name)
    else:
        RESULT["fail"].append(f"{name}: {type(error).__name__}: {error}")
        traceback.print_exception(type(error), error, error.__traceback__)


def _make_renderer(target, attr_name: str) -> Callable[[ft.Page], None]:
    """根据目标形态返回一个 ``render(page)`` 回调。

    - ``@ft.component`` 函数 → ``page.render(target)``
    - 传统 ``main(page)`` 入口 → 直接调用
    """
    if attr_name == "main":
        return lambda page: target(page)
    return lambda page: page.render(target)


async def _probe(
    page: ft.Page,
    render: Callable[[ft.Page], None],
    routes: list[str],
    settle: float,
) -> None:
    try:
        render(page)
        page.update()
        await asyncio.sleep(settle)
        _record("<root>", None)
    except Exception as e:  # noqa: BLE001
        _record("<root>", e)

    for route in routes:
        try:
            page.navigate(route)
            await asyncio.sleep(settle)
            _record(route, None)
        except Exception as e:  # noqa: BLE001
            _record(route, e)

    try:
        await page.window.close()
    except Exception:  # noqa: BLE001
        pass

    ok, fail = len(RESULT["ok"]), len(RESULT["fail"])
    print(f"\n{'=' * 60}", file=sys.stderr)
    print(f"SMOKE RESULT: ok={ok} fail={fail}", file=sys.stderr)
    for item in RESULT["fail"]:
        print(f"  FAIL  {item}", file=sys.stderr)
    for item in RESULT["ok"]:
        print(f"  ok    {item}", file=sys.stderr)
    print(f"{'=' * 60}\n", file=sys.stderr)
    sys.stderr.flush()
    os._exit(1 if fail else 0)


def main() -> None:
    parser = argparse.ArgumentParser(description="Flet headless smoke test")
    parser.add_argument("module", help="模块路径，如 examples.demo")
    parser.add_argument("attr", nargs="?", default="App", help="组件名，默认 App")
    parser.add_argument(
        "--routes",
        default="",
        help="渲染后依次访问的路由，逗号分隔，如 /,/general,/form",
    )
    parser.add_argument("--settle", type=float, default=0.8, help="每次渲染后等待秒数")
    args = parser.parse_args()

    module = importlib.import_module(args.module)
    target = getattr(module, args.attr)

    routes = [r.strip() for r in args.routes.split(",") if r.strip()]
    render = _make_renderer(target, args.attr)

    print(
        f"smoke: {args.module}.{args.attr}  routes={routes or '(none)'}",
        file=sys.stderr,
    )

    def _main(page: ft.Page) -> None:
        page.run_task(_probe, page, render, routes, args.settle)

    ft.run(_main, view=ft.AppView.FLET_APP_HIDDEN)


if __name__ == "__main__":
    main()
