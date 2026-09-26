"""单独渲染 examples/demo.py 里的某个页面组件，捕获渲染期异常。

用法：
    python scripts/_page_render_probe.py GeneralPage HomePage FormPage ...

可选：--find <正则> 在**渲染后**的控件树里搜索控件，用来断言
「某个组件确实被放进了这一页」（例如自定义组件渲染出的是一堆普通
`Container`/`Icon`，没法按类型断言）。

    python scripts/_page_render_probe.py FormPage --find 'ARROW_DROP_DOWN'
    python scripts/_page_render_probe.py FormPage --find '标签|Label'

每个组件在独立子进程里渲染，互不干扰。

.. warning::
    本探针用 ``AppView.FLET_APP_HIDDEN`` 跑，**看不到 Flutter 侧的渲染错误**。
    例如把 ``ft.View`` 当普通控件用（根视图模式下会整页变灰块、Flutter 抛
    ``Bad state: No element``），这里照样全 OK —— 因为窗口从未真正显示。
    凡是涉及「整页是否真的画出来了」「浮层有没有渲染」这类问题，
    必须用 :mod:`scripts._probe_demo` 起真机窗口截图验证。
"""

from __future__ import annotations

import asyncio
import os
import re
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import flet as ft  # noqa: E402

_ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
PAGE = _ARGS[0] if _ARGS else "HomePage"
FIND = None
if "--find" in sys.argv:
    FIND = sys.argv[sys.argv.index("--find") + 1]

#: 图标在 flet 1.0.0 里是整型码点，反查回名字才能按名字搜索
_ICON_NAMES: dict[int, str] = {}
try:
    for _name in dir(ft.Icons):
        if _name.startswith("_"):
            continue
        _val = getattr(ft.Icons, _name, None)
        if isinstance(_val, int) and _val not in _ICON_NAMES:
            _ICON_NAMES[_val] = _name
except Exception:  # noqa: BLE001
    pass

_WALK_FIELDS = (
    "_b",
    "controls",
    "content",
    "actions",
    "leading",
    "trailing",
    "appbar",
    "title",
    "subtitle",
    "label",
)


def walk(node, out=None, depth=0, seen=None):
    """收集控件树里的所有控件（按 id 去重，防环）。"""
    out = out if out is not None else []
    seen = seen if seen is not None else set()
    if node is None or depth > 40:
        return out
    if isinstance(node, (list, tuple)):
        for item in node:
            walk(item, out, depth + 1, seen)
        return out
    if not hasattr(node, "__class__"):
        return out
    if id(node) in seen:
        return out
    seen.add(id(node))
    out.append(node)
    for field in _WALK_FIELDS:
        walk(getattr(node, field, None), out, depth + 1, seen)
    ctrl = getattr(node, "control", None)  # Value 包装
    if ctrl is not None and ctrl is not node:
        walk(ctrl, out, depth + 1, seen)
    return out


def signature(control) -> str:
    """把控件压成一行可搜索的描述（类型 + 常见语义字段 + 图标名）。"""
    parts = [type(control).__name__]
    for attr in ("value", "label", "text", "hint_text", "data", "name"):
        val = getattr(control, attr, None)
        if isinstance(val, str) and val:
            parts.append(f"{attr}={val}")
    icon = getattr(control, "icon", None)
    if isinstance(icon, int):
        parts.append(f"icon={_ICON_NAMES.get(icon, icon)}")
    return " ".join(parts)


def main(page: ft.Page) -> None:
    async def scenario() -> None:
        status = "OK"
        detail = ""
        hits: list[str] = []
        try:
            import examples.demo as demo

            target = getattr(demo, PAGE)
            demo._configure_page(page)
            page.render(target)
            page.update()
            await asyncio.sleep(0.55)

            if FIND is not None:
                pattern = re.compile(FIND)
                for ctrl in walk(getattr(page, "views", None)):
                    sig = signature(ctrl)
                    if pattern.search(sig):
                        hits.append(sig)
        except BaseException as e:  # noqa: BLE001
            status = "FAIL"
            detail = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        finally:
            # --find 未命中同样按失败处理，所以必须在打印 RESULT 之前定状态
            if FIND is not None and status == "OK" and not hits:
                status = "FAIL"
            print(f"@@RESULT@@ {PAGE} {status}")
            if FIND is not None:
                print(f"@@FIND@@ {FIND!r} -> {len(hits)} 命中")
                for line in hits[:20]:
                    print("   ", line)
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
