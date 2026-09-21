"""逐个渲染 src/ui 下各组件的自带演示，捕获 flet 1.0.0 兼容性错误。

用法（单模块）：
    python scripts/_ui_audit.py ui.input.button
    python scripts/_ui_audit.py ui.input.rating --entry main

批量见 scripts/audit_ui.sh
"""

from __future__ import annotations

import argparse
import asyncio
import importlib
import os
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import flet as ft  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("module")
    parser.add_argument("--entry", default="App")
    args = parser.parse_args()

    mod = importlib.import_module(args.module)
    target = getattr(mod, args.entry)
    is_component = getattr(target, "__is_component__", False)

    def _main(page: ft.Page) -> None:
        async def scenario() -> None:
            status, detail = "OK", ""
            try:
                if callable(target) and not is_component and args.entry == "main":
                    target(page)
                    page.update()
                elif is_component:
                    page.render(target)
                    page.update()
                else:
                    page.add(target())
                    page.update()
                await asyncio.sleep(0.5)
            except BaseException as e:  # noqa: BLE001
                status = "FAIL"
                tb = traceback.format_exception(type(e), e, e.__traceback__)
                keep = [
                    ln
                    for ln in "".join(tb).splitlines()
                    if "site-packages" not in ln
                ]
                detail = "\n".join(keep[-14:])
            finally:
                print(f"@@{status}@@ {args.module}:{args.entry}")
                if detail:
                    print(detail)
                sys.stdout.flush()
                try:
                    await page.window.close()
                except Exception:
                    pass
                os._exit(0 if status == "OK" else 0)

        page.run_task(scenario)

    ft.run(_main, view=ft.AppView.FLET_APP_HIDDEN)


if __name__ == "__main__":
    main()
