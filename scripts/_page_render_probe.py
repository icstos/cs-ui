"""单独渲染 examples/demo.py 里的某个页面组件，捕获渲染期异常。

用法：
    python scripts/_page_render_probe.py GeneralPage HomePage FormPage ...

每个组件在独立子进程里渲染，互不干扰。
"""

from __future__ import annotations

import asyncio
import os
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import flet as ft  # noqa: E402

PAGE = sys.argv[1]


def main(page: ft.Page) -> None:
    async def scenario() -> None:
        status = "OK"
        detail = ""
        try:
            import examples.demo as demo

            target = getattr(demo, PAGE)
            demo._configure_page(page)
            if getattr(target, "_is_component", False) or hasattr(target, "__wrapped__"):
                page.render(target)
            else:
                page.render(target)
            page.update()
            await asyncio.sleep(0.55)
        except BaseException as e:  # noqa: BLE001
            status = "FAIL"
            detail = "".join(
                traceback.format_exception(type(e), e, e.__traceback__)
            )
        finally:
            print(f"@@RESULT@@ {PAGE} {status}")
            if detail:
                print(detail)
            sys.stdout.flush()
            try:
                await page.window.close()
            except Exception:
                pass
            os._exit(0)

    page.run_task(scenario)


if __name__ == "__main__":
    ft.run(main, view=ft.AppView.FLET_APP_HIDDEN)
