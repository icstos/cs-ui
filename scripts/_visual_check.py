"""对各页面做真机截图 + 灰块检测。

背景：Python 侧 `page.render()` 不抛异常，并不代表 Flutter 侧渲染成功。
控件树里混入不可渲染的值（例如裸字符串）时，Flutter 会用 ErrorWidget 顶替，
在 release 构建里表现为一整块灰色（#BDBDBD 附近）——只有截图才能发现。

用法::

    python scripts/_visual_check.py
    python scripts/_visual_check.py --pages GeneralPage ChartsPage
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHOT_APP = ROOT / "scripts" / "_shot_page.py"
PROBE = ROOT / "scripts" / "_probe_demo.py"
OUT_DIR = ROOT / "output" / "_visual_check"

PAGES = [
    "HomePage",
    "GeneralPage",
    "LayoutPage",
    "NavigationPage",
    "FormPage",
    "UploadPage",
    "FeedbackPage",
    "DisplayPage",
    "ChartsPage",
    "MediaPage",
    "AboutPage",
    "NotFoundPage",
]


def is_grey_block(path: Path) -> tuple[bool, float]:
    """检测截图内容区是否被 ErrorWidget 灰块占据。"""
    from PIL import Image

    img = Image.open(path).convert("RGB")
    w, h = img.size
    # 只看内容区中部，避开标题栏与 AppBar
    box = img.crop((int(w * 0.08), int(h * 0.18), int(w * 0.92), int(h * 0.92)))
    pixels = list(box.getdata())
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", nargs="*", default=PAGES)
    parser.add_argument("--boot", type=float, default=7.0)
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    bad: list[str] = []

    for page in args.pages:
        shot = OUT_DIR / f"{page}.png"
        proc = subprocess.run(
            [
                sys.executable,
                "-u",
                str(PROBE),
                "--app",
                str(SHOT_APP),
                "--title",
                f"CS UI · {page}",
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
            env={**__import__("os").environ, "CS_UI_SHOT_PAGE": page},
        )
        if "shot ->" not in (proc.stdout or ""):
            print(f"!! {page}: 未截到图")
            print((proc.stdout or "")[-800:])
            bad.append(page)
            continue
        grey, ratio = is_grey_block(shot)
        flag = "GREY-BLOCK" if grey else "ok"
        print(f"{flag:11s} {page:16s} 灰占比={ratio:.3f}  -> {shot.name}")
        if grey:
            bad.append(page)

    print()
    if bad:
        print(f"!! {len(bad)} 个页面疑似渲染失败: {', '.join(bad)}")
        sys.exit(1)
    print("全部页面视觉检查通过。")


if __name__ == "__main__":
    main()
