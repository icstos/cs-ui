"""探针：确认 I18nProvider 真的把语言同步到了 page.locale_configuration / page.rtl。"""

import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

import flet as ft  # noqa: E402
import examples.demo as demo  # noqa: E402


async def probe(page: ft.Page) -> None:
    page.render(demo.App)
    page.update()
    await asyncio.sleep(2.0)
    cfg = getattr(page, "locale_configuration", None)
    print("locale_configuration:", cfg, flush=True)
    if cfg is not None:
        cur = cfg.current_locale
        print(f"current: {cur.language_code}/{cur.script_code}/{cur.country_code}", flush=True)
        print(
            "supported:",
            [(item.language_code, item.country_code) for item in cfg.supported_locales],
            flush=True,
        )
    print("page.rtl:", page.rtl, flush=True)
    os._exit(0)


if __name__ == "__main__":
    ft.run(lambda page: page.run_task(probe, page), view=ft.AppView.FLET_APP_HIDDEN)
