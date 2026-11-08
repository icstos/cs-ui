"""对各页面做真机截图 + 灰块检测。

背景：Python 侧 `page.render()` 不抛异常，并不代表 Flutter 侧渲染成功。
控件树里混入不可渲染的值（例如裸字符串）时，Flutter 会用 ErrorWidget 顶替，
在 release 构建里表现为一整块灰色（#BDBDBD 附近）——只有截图才能发现。

为什么用文档站而不是示例页
--------------------------
本脚本原先渲染 ``examples/demo.py`` 里的 ``HomePage`` / ``FormPage`` 等页面，
那套示例在"清理死文件"时随 ``demo.py`` 一起下线了，脚本却还在按老标题找窗口：
命令确实返回、也不报错，只是一张图都没截到。这种"绿着的失效"比没有检查更糟，
所以改成直接跑当前站点（``docs.main``），按路由取页。

路由覆盖原则：每个分类挑一页 + 本轮改动密集的组件页。整站 100+ 页全跑一遍是
分钟级开销，而灰块这类事故从来是"改到哪炸到哪"，取代表集足够。

用法::

    python scripts/_visual_check.py                       # 默认路由集
    python scripts/_visual_check.py --routes /components/form/rating
    python scripts/_visual_check.py --mode dark           # 暗色主题
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHOT_HOST = ROOT / "scripts" / "_shot_docs.py"
PROBE = ROOT / "scripts" / "_probe_demo.py"
OUT_DIR = ROOT / "output" / "_visual_check"

#: 探针按窗口标题找窗口，中文标点在命令行里容易失真 —— 统一用 ASCII。
WINDOW_TITLE = "CSUIDOCS"

#: (路由, 说明)。说明只用于报表，文件名取路由的 slug。
ROUTES: list[tuple[str, str]] = [
    ("/", "首页"),
    ("/components", "组件总览"),
    ("/docs/theming", "主题文章"),
    ("/components/general/button", "按钮（禁用 / 悬停两档）"),
    ("/components/form/rating", "评分（星标 24 / 可点 36）"),
    ("/components/form/transfer", "穿梭框（列头 / 悬停 / 勾选）"),
    ("/components/form/multi_select", "多选（选中 / 悬停 / 锁定）"),
    ("/components/form/checkbox", "复选框（禁用档）"),
    ("/components/navigation/menu", "菜单（选中 / 悬停 / 禁用）"),
    ("/components/navigation/pagination", "分页（箭头悬停 / 禁用）"),
    ("/components/navigation/bread_crumb", "面包屑（分隔符图标）"),
    ("/components/layout/table", "表格（行悬停 / 斑马纹）"),
    ("/components/display/calendar", "日历（单元格悬停）"),
]


def slug(route: str) -> str:
    """``/components/form/rating`` → ``components_form_rating``。"""
    parts = [p for p in route.strip("/").split("/") if p]
    return "_".join(parts) or "home"


def is_grey_block(path: Path) -> tuple[bool, float]:
    """检测截图内容区是否被 ErrorWidget 灰块占据。"""
    from PIL import Image

    img = Image.open(path).convert("RGB")
    w, h = img.size
    # 只看内容区中部，避开标题栏与侧栏（侧栏本身是块灰面，会拉高占比）
    box = img.crop((int(w * 0.2), int(h * 0.15), int(w * 0.95), int(h * 0.92)))
    # Pillow 14 起 getdata 弃用（换成 get_flattened_data），这里两种都认
    fetch = getattr(box, "get_flattened_data", None) or box.getdata
    pixels = list(fetch())
    if not pixels:
        return False, 0.0
    # ErrorWidget 的灰：R≈G≈B 且落在 0xB0~0xC8
    greyish = sum(
        1
        for r, g, b in pixels
        if abs(r - g) <= 6 and abs(g - b) <= 6 and 0xAC <= r <= 0xCC
    )
    ratio = greyish / len(pixels)
    return ratio > 0.55, ratio


def main() -> int:
    parser = argparse.ArgumentParser(description="文档站真机截图 + 灰块检测")
    parser.add_argument(
        "--routes",
        nargs="*",
        default=[route for route, _ in ROUTES],
        help="要截的路由（默认取内置代表集）",
    )
    parser.add_argument("--mode", choices=("light", "dark"), default="light")
    parser.add_argument("--boot", type=float, default=9.0, help="等首帧的秒数")
    args = parser.parse_args()

    notes = dict(ROUTES)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    bad: list[str] = []

    for route in args.routes:
        suffix = f"_{args.mode}" if args.mode == "dark" else ""
        shot = OUT_DIR / f"{slug(route)}{suffix}.png"
        probe = subprocess.run(
            [
                sys.executable,
                "-u",
                str(PROBE),
                "--app",
                str(SHOT_HOST),
                "--title",
                WINDOW_TITLE,
                "--boot",
                str(args.boot),
                "--out",
                str(shot),
            ],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env={
                **os.environ,
                "CS_UI_DOCS_ROUTE": route,
                "CS_UI_DOCS_TITLE": WINDOW_TITLE,
                "CS_UI_DOCS_MODE": args.mode,
            },
        )
        if "shot ->" not in (probe.stdout or ""):
            print(f"!! {route}: 未截到图")
            print((probe.stdout or "")[-600:])
            bad.append(route)
            continue
        grey, ratio = is_grey_block(shot)
        flag = "GREY-BLOCK" if grey else "ok"
        print(f"{flag:11s} {route:34s} 灰占比={ratio:.3f}  {notes.get(route, '')}  -> {shot.name}")
        if grey:
            bad.append(route)

    print()
    if bad:
        print(f"!! {len(bad)} 页疑似渲染失败: {', '.join(bad)}")
        return 1
    print(f"全部 {len(args.routes)} 页视觉检查通过（{args.mode}）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
