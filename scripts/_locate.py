"""按像素特征在截图里定位控件，输出可直接喂给探针的逻辑坐标。

为什么需要这个：**缩略图会骗人**。界面上看着在 (620, 1005) 的东西，
在 2240×1260 的原图里坐标完全不同。肉眼估坐标十有八九点空
（本次就连续点空 4 次，浪费了大量时间）。

用法::

    python scripts/_locate.py output/shot.png --rect 0.2,0.9,0.0,0.7 \\
        --target-blue --pad 4

或者直接当库用::

    from _locate import locate_blue_buttons
    for x0, y0, x1, y1 in locate_blue_buttons("output/shot.png"):
        print((x0 + x1) // 2, (y0 + y1) // 2)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image

#: 本机实测（scripts/_calib_host.py 标定）：图像 = 原点 + 逻辑 × DPR
DPR = 1.75
ORIGIN_X = 12.0
ORIGIN_Y = 52.0


def to_logical(img_x: float, img_y: float) -> tuple[int, int]:
    """图像坐标 → 探针要的客户区逻辑坐标。"""
    return (
        round((img_x - ORIGIN_X) / DPR),
        round((img_y - ORIGIN_Y) / DPR),
    )


def is_blue(p: tuple[int, int, int]) -> bool:
    r, g, b = p
    return b > 130 and b - r > 40 and b - g > 25


def is_gray_border(p: tuple[int, int, int]) -> bool:
    """浅灰描边（Paging 的其他按钮边框）。"""
    r, g, b = p
    return abs(r - g) < 14 and abs(g - b) < 14 and 195 < r < 238


def find_boxes(
    path: str | Path,
    predicate,
    y_range: tuple[int, int] | None = None,
    x_range: tuple[int, int] | None = None,
    gap: int = 10,
    min_w: int = 8,
    min_h: int = 8,
) -> list[tuple[int, int, int, int]]:
    """扫描满足 predicate 的像素，聚成矩形框。返回 [(x0,y0,x1,y1)]。"""
    img = Image.open(path).convert("RGB")
    w, h = img.size
    y0, y1 = y_range or (0, h)
    x0, x1 = x_range or (0, w)

    pts: list[tuple[int, int]] = []
    for y in range(y0, min(y1, h)):
        for x in range(x0, min(x1, w)):
            if predicate(img.getpixel((x, y))):
                pts.append((x, y))
    if not pts:
        return []

    # 先按行聚成段，再把段按 x 聚成框
    rows: dict[int, list[int]] = {}
    for x, y in pts:
        rows.setdefault(y, []).append(x)

    boxes: list[tuple[int, int, int, int]] = []
    open_box: list[int] | None = None  # [x0, x1, ytop, ybot]
    for y in sorted(rows):
        xs = sorted(rows[y])
        segs: list[list[int]] = []
        cur = [xs[0]]
        for x in xs[1:]:
            if x - cur[-1] <= gap:
                cur.append(x)
            else:
                segs.append(cur)
                cur = [x]
        segs.append(cur)

        cur_boxes: list[list[int]] = []
        for s in segs:
            sx0, sx1 = s[0], s[-1]
            if open_box is not None and abs(open_box[0] - sx0) <= gap:
                open_box[0] = min(open_box[0], sx0)
                open_box[1] = max(open_box[1], sx1)
                open_box[3] = y
            else:
                if open_box is not None:
                    cur_boxes.append(open_box)
                open_box = [sx0, sx1, y, y]
        if open_box is not None and open_box not in cur_boxes:
            cur_boxes.append(open_box)
        open_box = None

        for b in cur_boxes:
            if b[1] - b[0] >= min_w and b[3] - b[2] >= min_h:
                boxes.append((b[0], b[2], b[1], b[3]))
    return boxes


def locate_page_buttons(path: str | Path) -> list[tuple[int, int]]:
    """定位 Paging 的页码按钮，返回可直接点的逻辑坐标列表。

    先找**当前页**按钮的蓝色边框（整条分页器里唯一的蓝色），
    由此定出分页器行的 y；再在该行上按白色块（其他页码按钮的底色）等距外推。
    这样页面怎么滚动、窗口多高都不用重新估坐标。
    """
    img = Image.open(path).convert("RGB")
    w, h = img.size

    # ① 当前页按钮：蓝色边框，整图唯一
    blue_rows = [
        y
        for y in range(h)
        if sum(1 for x in range(0, int(w * 0.6), 2) if is_blue(img.getpixel((x, y)))) > 3
    ]
    if not blue_rows:
        return []
    segs: list[list[int]] = []
    cur = [blue_rows[0]]
    for y in blue_rows[1:]:
        if y - cur[-1] <= 5:
            cur.append(y)
        else:
            segs.append(cur)
            cur = [y]
    segs.append(cur)
    # 取最靠下的一段（分页器在页面下部；表格里不会有蓝色边框）
    bar = segs[-1]
    cy = (bar[0] + bar[-1]) // 2

    # ② 当前页按钮的左右边界 → 按钮宽 + 间距
    blue_cols = [
        x
        for x in range(int(w * 0.1), int(w * 0.6))
        if is_blue(img.getpixel((x, cy)))
    ]
    if not blue_cols:
        return []
    x0, x1 = min(blue_cols), max(blue_cols)
    cur_center = (x0 + x1) // 2

    # ③ 相邻白色块 = 其他页码按钮。取紧邻右侧那一段，算出中心间距
    white_cols = [
        x
        for x in range(x1, int(w * 0.6))
        if all(v > 248 for v in img.getpixel((x, cy)))
    ]
    pitch = 0
    if white_cols:
        segs2: list[list[int]] = []
        cur2 = [white_cols[0]]
        for x in white_cols[1:]:
            if x - cur2[-1] <= 4:
                cur2.append(x)
            else:
                segs2.append(cur2)
                cur2 = [x]
        segs2.append(cur2)
        segs2 = [g for g in segs2 if len(g) > 8]
        if segs2:
            pitch = (segs2[0][0] + segs2[0][-1]) // 2 - cur_center

    out = []
    # 当前页往前最多 5 个、往后最多 10 个，够覆盖省略号布局
    for k in range(-5, 11):
        if pitch == 0 and k != 0:
            continue
        ix = cur_center + k * pitch
        if 0 <= ix < w:
            out.append(to_logical(ix, cy))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--buttons", action="store_true", help="定位页码按钮")
    args = ap.parse_args()

    if args.buttons:
        pts = locate_page_buttons(args.image)
        print(f"找到 {len(pts)} 个候选按钮（逻辑坐标，索引 0 = 当前页）：")
        for i, (lx, ly) in enumerate(pts):
            print(f"  [{i:2d}] {lx},{ly}")
    else:
        boxes = find_boxes(args.image, is_blue)
        print(f"蓝色框 {len(boxes)} 个：{boxes[:20]}")


if __name__ == "__main__":
    sys.exit(main())
