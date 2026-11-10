"""对各页面做真机截图 + 灰块 / 溢出检测。

两类事故只有截图能发现，Python 侧一律静默：

* **灰块** —— 控件树里混入不可渲染的值（例如裸字符串）时，Flutter 会用
  ErrorWidget 顶替，release 构建里表现为一整块灰色（``#BDBDBD`` 附近）。
* **溢出** —— 字号 / 行高 / 内边距一改大，内容就撑破固定高度的盒子，Flutter
  画黄黑斜纹。它不抛异常、不进日志，``page.render()`` 返回得干干净净。
  正文从 13 调到 14 这类改动，最典型的副作用就是这个。

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

#: 滚动前把光标放这里：正文栏中部（逻辑像素）。落在侧栏只会滚侧栏。
SCROLL_AT = (700, 430)

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


def normalize_route(route: str) -> str:
    """把被 shell 改写过的路由还原成 ``/components/form/rating``。

    Git Bash（MSYS）会把命令行里以 ``/`` 开头的参数当成 Unix 绝对路径，改写成
    ``C:/Program Files/Git/components/form/rating``。截图宿主认得出这种前缀、
    页面截得没错，但**报表和文件名会带着那串 Windows 路径**——于是同一页每次
    跑出来的 PNG 名字都不一样，翻历史截图时等于没有。这里先切回真路由。
    """
    if "/" in route and (":" in route or "\\" in route):
        heads = [route.find(p) for p in ("/components/", "/docs/", "/about")]
        heads = [i for i in heads if i >= 0]
        if heads:
            return route[min(heads) :]
    return route


def slug(route: str) -> str:
    """``/components/form/rating`` → ``components_form_rating``。"""
    parts = [p for p in route.strip("/").split("/") if p]
    return "_".join(parts) or "home"


def known_routes() -> set[str]:
    """站点里真实存在的路由。

    必须有这道前置检查：写错一个路由，站点会渲染 404 页 —— 而 404 页**又白又整齐**，
    灰占比 0.001、溢出 0，于是报表上是个漂亮的 ``ok``。查的是"页面渲染成功吗"，
    却答成了"这个不存在的页面渲染正常"，比没检查更危险。
    """
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from docs.site import PAGE_BY_ROUTE

    return set(PAGE_BY_ROUTE)


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


def overflow_pixels(path: Path) -> int:
    """数一数截图里的 Flutter 溢出提示（黄黑斜纹）有多少像素。

    Flutter 在 debug 模式下把"内容比盒子大"画成一抹纯黄 ``#FFFF00`` 的斜纹。
    它不抛异常、不进日志，Python 侧的 ``page.render()`` 也一无所知 —— 字号、
    行高、内边距任何一个改大一点，都可能让某一行悄悄溢出。这个提示色在浅色
    主题里几乎不可能自然出现（本框架的 warning 是 ``#B45309``，暗色是
    ``#FBBF24``，绿通道都够不到 0xE0），所以可以放心当硬信号。

    返回原始像素数而不是比例：溢出带往往只有几像素高、被拉得很长，用比例会
    被稀释到噪声水平。
    """
    from PIL import Image

    img = Image.open(path).convert("RGB")
    w, h = img.size
    box = img.crop((int(w * 0.2), int(h * 0.1), int(w * 0.98), int(h * 0.95)))
    fetch = getattr(box, "get_flattened_data", None) or box.getdata
    return sum(1 for r, g, b in fetch() if r >= 240 and g >= 225 and b <= 80)


def main() -> int:
    parser = argparse.ArgumentParser(description="文档站真机截图 + 灰块 / 溢出检测")
    parser.add_argument(
        "--routes",
        nargs="*",
        default=[route for route, _ in ROUTES],
        help="要截的路由（默认取内置代表集）",
    )
    parser.add_argument("--mode", choices=("light", "dark"), default="light")
    parser.add_argument("--boot", type=float, default=9.0, help="等首帧的秒数")
    parser.add_argument(
        "--scroll",
        type=int,
        default=0,
        metavar="N",
        help="截图前在内容区向下滚 N 格（负值向上）。不滚只能看到页面上半屏 —— "
        "定义与徽标在上面，真正会溢出的示例都在下面。",
    )
    args = parser.parse_args()

    notes = dict(ROUTES)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    bad: list[str] = []
    routes = known_routes()

    for raw in args.routes:
        route = normalize_route(raw)
        if route not in routes:
            print(f"!! {route}: 路由不存在（站点会渲染 404，截出来的图必然'通过'）")
            bad.append(route)
            continue
        suffix = f"_{args.mode}" if args.mode == "dark" else ""
        if args.scroll:
            suffix += f"_s{args.scroll}"
        shot = OUT_DIR / f"{slug(route)}{suffix}.png"
        wheel_cmd: list[str] = []
        if args.scroll:
            # 内容区中部：滚轮要落在可滚动的列表上，落在侧栏只会滚侧栏
            wheel_cmd = ["--wheel", f"{SCROLL_AT[0]},{SCROLL_AT[1]},{-args.scroll}"]
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
                *wheel_cmd,
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

        # 探针的动作顺序是"先截一张、再滚、再截一张"，第二张才叫 ``<out>_1.png``。
        # 要检的显然是滚过之后那张 —— 只认 ``<out>`` 的话，检查的会一直是页面顶部，
        # 真正会溢出的示例区域永远没进过视野。
        target = shot
        if args.scroll:
            scrolled = shot.with_name(f"{shot.stem}_1{shot.suffix}")
            if not scrolled.exists():
                print(f"!! {route}: 滚动后没截到图")
                bad.append(route)
                continue
            scrolled.replace(shot)
            target = shot

        grey, ratio = is_grey_block(target)
        spill = overflow_pixels(target)
        if grey:
            flag = "GREY-BLOCK"
        elif spill > 500:
            flag = "OVERFLOW"
        else:
            flag = "ok"
        print(
            f"{flag:11s} {route:34s} 灰占比={ratio:.3f} 溢出={spill:5d}  "
            f"{notes.get(route, '')}  -> {shot.name}"
        )
        if flag != "ok":
            bad.append(route)

    print()
    if bad:
        print(f"!! {len(bad)} 页疑似渲染失败或溢出: {', '.join(bad)}")
        return 1
    print(f"全部 {len(args.routes)} 页视觉检查通过（{args.mode}）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
