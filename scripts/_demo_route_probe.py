"""对 examples/demo.py 做路由切换验证（无头）。

跑法：
    python scripts/_demo_route_probe.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import flet as ft  # noqa: E402

from examples.demo import App, ROUTES  # noqa: E402


def _flatten(node, out, depth=0):
    if node is None or depth > 30:
        return
    if isinstance(node, (list, tuple)):
        for item in node:
            _flatten(item, out, depth + 1)
        return
    out.append(node)
    inner = getattr(node, "_b", None)
    if inner is not None:
        _flatten(inner, out, depth + 1)


def current_view(page):
    flat = []
    _flatten(getattr(page, "views", None), flat)
    views = [c for c in flat if isinstance(c, ft.View)]
    return views[-1] if views else None


def collect(node, out=None, depth=0):
    """收集控件树中所有控件的类名。"""
    out = out if out is not None else []
    if node is None or depth > 40:
        return out
    if isinstance(node, (list, tuple)):
        for item in node:
            collect(item, out, depth + 1)
        return out
    out.append(node)
    for field in (
        "_b",
        "controls",
        "content",
        "actions",
        "leading",
        "trailing",
        "appbar",
        "title",
        "items",
        "destinations",
        "tabs",
        "segments",
        "options",
        "children",
        "views",
    ):
        try:
            child = getattr(node, field, None)
        except Exception:
            continue
        if child is None or isinstance(child, (str, bytes, int, float, bool, dict)):
            continue
        collect(child, out, depth + 1)
    return out


async def probe(page: ft.Page) -> None:
    results = []
    try:
        page.render(App)
        page.update()
        await asyncio.sleep(0.9)

        v = current_view(page)
        print(f"[init] route={page.route!r} view.route={getattr(v, 'route', None)!r}")
        results.append(("/", page.route))

        for r in ROUTES:
            path = "/" + (r.path or "")
            if r.index:
                path = "/"
            page.navigate(path)
            await asyncio.sleep(0.9)
            # 断言 page.route：manage_views=False 下 Router 只替换
            # views[0].controls，View.route 不随导航变化。
            got = page.route
            ok = "OK " if got == path else "BAD"
            print(f"[{ok}] navigate({path!r}) -> page.route={got!r}")
            results.append((path, got))

        # 404：manage_views=False 时 Router 不再把请求路径注入 View.route，
        # 改为断言 404 页面的文案确实渲染出来了。
        page.navigate("/definitely-not-a-route")
        await asyncio.sleep(0.9)
        v = current_view(page)
        blob = " ".join(
            str(getattr(c, "value", ""))
            for c in collect(v)
            if isinstance(getattr(c, "value", None), str)
        )
        hit = "页面不存在" in blob
        ok = "OK " if hit else "BAD"
        print(
            f"[{ok}] 404 -> view.route={getattr(v, 'route', None)!r} 文案命中={hit}"
        )
        results.append(
            ("/definitely-not-a-route", "/definitely-not-a-route" if hit else None)
        )

        bad = [p for p, g in results if g != p]
        print("\nSUMMARY: total=%d bad=%d" % (len(results), len(bad)))
        for p in bad:
            print("  BAD", p)

        # 各页关键控件（按**渲染后**的真实类型断言；
        # 注意 ui 中的 observable 组件（如 Input/MultiSelect）渲染出的是 ft.TextField 等原生控件）
        expect: dict[str, set[str]] = {
            "/general": {"Header_1", "Quote", "Link", "Chip"},
            "/layout": {"PageLayout", "Table", "Timeline", "Expander", "Card"},
            "/navigation": {"BreadCrumb", "Crumb", "Tab", "NavigationBarDestination"},
            # /form 页的下拉类控件来自 SelectBox（底层 ft.DropdownM2）；
            # DateTimeInput 自 2026-09 起改为「月历 + 时间轮盘」，不再用 ft.Dropdown。
            "/form": {
                "TextField",
                "Checkbox",
                "DropdownM2",
                "Radio",
                "Rating",
                "Segment",
            },
            "/feedback": {"ProgressBar", "Button"},
            "/display": {"CodeEditor", "Image", "ListTile"},
            "/charts": {"LineChart", "AreaChart", "BarChart", "ScatterChart"},
        }
        print()
        missing_total = 0
        for path, wanted in expect.items():
            page.navigate(path)
            await asyncio.sleep(0.9)
            names = {type(c).__name__ for c in collect(current_view(page))}
            miss = wanted - names
            missing_total += len(miss)
            flag = "OK " if not miss else "!! "
            print(f"[{flag}]{path} 命中={sorted(wanted & names)} 缺失={sorted(miss)}")
        print(f"\n控件归属断言: missing={missing_total}")
    except BaseException:  # noqa: BLE001
        import traceback

        traceback.print_exc()
    finally:
        try:
            await page.window.close()
        except Exception:
            pass
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(0)


def main(page: ft.Page) -> None:
    page.run_task(probe, page)


if __name__ == "__main__":
    ft.run(main, view=ft.AppView.FLET_APP_HIDDEN)
