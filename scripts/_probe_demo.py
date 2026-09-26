"""CS UI Demo 真机 UI 探针（一次性驱动脚本）。

在一次执行内完成：启动 examples/demo.py → 定位窗口 → 抢前台 →
按给定逻辑坐标点击 → PrintWindow 截图存档。

用法::

    python scripts/_probe_demo.py --out /tmp/shot1.png
    python scripts/_probe_demo.py --click 300,420 --sleep 2.0 --out /tmp/shot2.png
    python scripts/_probe_demo.py --click 300,420 --click 500,700 --sleep 1.5 --out /tmp/shot3.png

需要"点击 → 滚动 → 再点击"这类有序交互时用 ``--do``（按给定顺序执行）::

    python scripts/_probe_demo.py --once \
        --do click:207,469 --do wheel:400,500,-14 \
        --do shot:before --do click:300,600 --do shot:after

坐标是**窗口客户区逻辑坐标**（flet 的 CSS 逻辑像素）。
"""

from __future__ import annotations

import argparse
import ctypes
import ctypes.wintypes as wt
import os
import subprocess
import sys
import threading
import time
from ctypes import c_int, c_uint, c_void_p
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
kernel32 = ctypes.windll.kernel32

user32.FindWindowW.restype = wt.HWND
user32.FindWindowW.argtypes = [wt.LPCWSTR, wt.LPCWSTR]
user32.GetWindowRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
user32.GetClientRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
user32.ClientToScreen.argtypes = [wt.HWND, ctypes.POINTER(wt.POINT)]
user32.SetWindowPos.argtypes = [wt.HWND, wt.HWND, c_int, c_int, c_int, c_int, c_uint]
user32.SetWindowPos.restype = wt.BOOL
user32.SetCursorPos.argtypes = [c_int, c_int]
user32.WindowFromPoint.restype = wt.HWND
user32.WindowFromPoint.argtypes = [wt.POINT]
user32.GetForegroundWindow.restype = wt.HWND
user32.GetWindowDC.restype = wt.HDC
user32.GetWindowDC.argtypes = [wt.HWND]
user32.ReleaseDC.argtypes = [wt.HWND, wt.HDC]
user32.PrintWindow.argtypes = [wt.HWND, wt.HDC, c_uint]
user32.PrintWindow.restype = wt.BOOL
user32.GetAncestor.argtypes = [wt.HWND, c_uint]
user32.GetAncestor.restype = wt.HWND
gdi32.CreateCompatibleDC.restype = wt.HDC
gdi32.CreateCompatibleDC.argtypes = [wt.HDC]
gdi32.CreateCompatibleBitmap.restype = wt.HBITMAP
gdi32.CreateCompatibleBitmap.argtypes = [wt.HDC, c_int, c_int]
gdi32.SelectObject.restype = wt.HGDIOBJ
gdi32.SelectObject.argtypes = [wt.HDC, wt.HGDIOBJ]
gdi32.DeleteObject.argtypes = [wt.HGDIOBJ]
gdi32.DeleteDC.argtypes = [wt.HDC]
gdi32.GetDIBits.restype = c_int
gdi32.GetDIBits.argtypes = [
    wt.HDC,
    wt.HBITMAP,
    c_uint,
    c_uint,
    c_void_p,
    c_void_p,
    c_uint,
]


TITLE = "CS UI Demo"
SWP_SHOWWINDOW = 0x0040
SWP_NOSIZE = 0x0001
HWND_TOP = 0


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wt.DWORD),
        ("biWidth", ctypes.c_long),
        ("biHeight", ctypes.c_long),
        ("biPlanes", wt.WORD),
        ("biBitCount", wt.WORD),
        ("biCompression", wt.DWORD),
        ("biSizeImage", wt.DWORD),
        ("biXPelsPerMeter", ctypes.c_long),
        ("biYPelsPerMeter", ctypes.c_long),
        ("biClrUsed", wt.DWORD),
        ("biClrImportant", wt.DWORD),
    ]


def find_window(title: str, timeout: float = 40.0) -> int:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        hwnd = user32.FindWindowW(None, title)
        if hwnd:
            return hwnd
        time.sleep(0.3)
    return 0


def window_geometry(hwnd: int):
    """返回 (left, top, width, height, client_origin_screen_x, client_origin_screen_y)."""
    wr = wt.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(wr))
    pt = wt.POINT(0, 0)
    user32.ClientToScreen(hwnd, ctypes.byref(pt))
    return wr.left, wr.top, wr.right - wr.left, wr.bottom - wr.top, pt.x, pt.y


def force_foreground(hwnd: int) -> bool:
    """用 AttachThreadInput 抢前台（skill 里最可靠的做法）。"""
    fg = user32.GetForegroundWindow()
    tgt_thread = user32.GetWindowThreadProcessId(fg, None)
    cur_thread = kernel32.GetCurrentThreadId()
    user32.AttachThreadInput(cur_thread, tgt_thread, True)
    try:
        user32.BringWindowToTop(hwnd)
        user32.SetForegroundWindow(hwnd)
        user32.SetActiveWindow(hwnd)
    finally:
        user32.AttachThreadInput(cur_thread, tgt_thread, False)
    return user32.GetForegroundWindow() == hwnd


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wt.LONG),
        ("dy", wt.LONG),
        ("mouseData", wt.DWORD),
        ("dwFlags", wt.DWORD),
        ("time", wt.DWORD),
        ("dwExtraInfo", c_void_p),
    ]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("pad", ctypes.c_byte * 32)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", wt.DWORD), ("u", _INPUTUNION)]


MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_WHEEL = 0x0800
WHEEL_DELTA = 120
INPUT_MOUSE = 0

user32.SendInput.argtypes = [c_uint, ctypes.POINTER(INPUT), c_int]
user32.SendInput.restype = c_uint


def _send_mouse(flags: int, dx: int = 0, dy: int = 0, data: int = 0) -> int:
    inp = INPUT()
    inp.type = INPUT_MOUSE
    inp.mi = MOUSEINPUT(dx, dy, data, flags, 0, None)
    assert ctypes.sizeof(INPUT) == 40, ctypes.sizeof(INPUT)
    return user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


def _belongs(hwnd: int, pt: wt.POINT) -> bool:
    """判断屏幕点是否落在本窗口（含 Flutter 的子窗口）内。"""
    hit = user32.WindowFromPoint(pt)
    if not hit:
        return False
    if hit == hwnd:
        return True
    root = user32.GetAncestor(hit, 2)  # GA_ROOT
    return root == hwnd


def _attach(hwnd: int):
    fg = user32.GetForegroundWindow()
    tgt_thread = user32.GetWindowThreadProcessId(fg, None)
    cur_thread = kernel32.GetCurrentThreadId()
    attached = tgt_thread != cur_thread
    if attached:
        user32.AttachThreadInput(cur_thread, tgt_thread, True)
    user32.BringWindowToTop(hwnd)
    user32.SetForegroundWindow(hwnd)
    user32.SetActiveWindow(hwnd)
    return attached, cur_thread, tgt_thread


def click(hwnd: int, lx: int, ly: int, repeat: int = 2) -> None:
    """在窗口客户区逻辑坐标 (lx, ly) 处注入真实鼠标点击（SendInput）。

    Args:
        repeat: 连点次数。默认 2 次（第一次可能只被用于激活窗口）；
            验证「切换类」交互（token 会被反转两次）时传 1。
    """
    dpi = user32.GetDpiForWindow(hwnd) / 96.0
    _l, _t, _w, _h, ox, oy = window_geometry(hwnd)
    sx, sy = ox + int(lx * dpi), oy + int(ly * dpi)

    attached, cur, tgt = _attach(hwnd)
    try:
        pt = wt.POINT(sx, sy)
        if not _belongs(hwnd, pt):
            print(f"  ! 目标点 ({sx},{sy}) 不属于本窗口，跳过")
            return
        user32.SetCursorPos(sx, sy)
        time.sleep(0.2)
        # 校验窗口没有被应用自己挪走
        _l, _t, _w, _h, ox, oy = window_geometry(hwnd)
        sx, sy = ox + int(lx * dpi), oy + int(ly * dpi)
        user32.SetCursorPos(sx, sy)
        time.sleep(0.2)

        for attempt in range(repeat):
            n1 = _send_mouse(MOUSEEVENTF_LEFTDOWN)
            time.sleep(0.06)
            n2 = _send_mouse(MOUSEEVENTF_LEFTUP)
            time.sleep(0.4)
            print(f"  click#{attempt} local=({lx},{ly}) screen=({sx},{sy}) "
                  f"dpi={dpi} injected={n1}/{n2}")
    finally:
        if attached:
            user32.AttachThreadInput(cur, tgt, False)


def hover(hwnd: int, lx: int, ly: int) -> None:
    """把光标移到窗口客户区逻辑坐标 (lx, ly) 上，但不点击（验证 hover 态）。

    先落到旁边的空点再移入目标点，确保 Flutter 收到 mouse-move 事件。
    """
    dpi = user32.GetDpiForWindow(hwnd) / 96.0
    _l, _t, _w, _h, ox, oy = window_geometry(hwnd)
    sx, sy = ox + int(lx * dpi), oy + int(ly * dpi)

    force_foreground(hwnd)
    time.sleep(0.3)
    user32.SetCursorPos(sx + 40, sy + 40)
    time.sleep(0.25)
    user32.SetCursorPos(sx, sy)
    time.sleep(0.25)
    user32.SetCursorPos(sx + 2, sy + 1)
    time.sleep(0.6)
    print(f"  hover local=({lx},{ly}) screen=({sx},{sy}) dpi={dpi}")


def wheel(hwnd: int, lx: int, ly: int, notches: int) -> None:
    """把光标移到 (lx, ly) 后滚动鼠标滚轮（正数向上 / 负数向下）。

    用于把可滚动页面滚到目标控件处 —— 纯 SendInput 点击无法触达视口外的控件。
    """
    dpi = user32.GetDpiForWindow(hwnd) / 96.0
    _l, _t, _w, _h, ox, oy = window_geometry(hwnd)
    sx, sy = ox + int(lx * dpi), oy + int(ly * dpi)

    force_foreground(hwnd)
    time.sleep(0.3)
    user32.SetCursorPos(sx, sy)
    time.sleep(0.3)
    step = 1 if notches >= 0 else -1
    for _ in range(abs(notches)):
        _send_mouse(MOUSEEVENTF_WHEEL, 0, 0, step * WHEEL_DELTA)
        time.sleep(0.12)
    print(f"  wheel local=({lx},{ly}) notches={notches}")


def screenshot(hwnd: int, path: Path) -> None:
    """抓取窗口位图。

    注意：Flutter 的窗口用 ``PrintWindow`` 常常抓到**上一帧**（点击后立刻截图会
    看到点击前的画面）。这里连抓两次，丢掉第一次、采用第二次，规避该滞后。
    """
    from PIL import Image

    _l, _t, w, h, _ox, _oy = window_geometry(hwnd)
    hdc = user32.GetWindowDC(hwnd)
    memdc = gdi32.CreateCompatibleDC(hdc)
    bmp = gdi32.CreateCompatibleBitmap(hdc, w, h)
    gdi32.SelectObject(memdc, bmp)

    user32.PrintWindow(hwnd, memdc, 2)  # PW_RENDERFULLCONTENT（可能拿到旧帧）
    time.sleep(0.25)
    user32.PrintWindow(hwnd, memdc, 2)  # 再抓一次，拿到最新帧

    bmi = BITMAPINFOHEADER()
    bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.biWidth = w
    bmi.biHeight = -h
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(memdc, bmp, 0, h, buf, ctypes.byref(bmi), 0)

    img = Image.frombuffer("RGBA", (w, h), buf, "raw", "BGRA", 0, 1).convert("RGB")
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)
    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(memdc)
    user32.ReleaseDC(hwnd, hdc)
    print(f"  shot -> {path}  ({w}x{h})")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--click", action="append", default=[], help="逻辑坐标 x,y（可重复）")
    parser.add_argument(
        "--do",
        action="append",
        default=[],
        help="按给定顺序执行动作（可重复），给了它就不再使用 --click/--hover/--wheel。"
        "语法：click:x,y / wheel:x,y,notches / hover:x,y / shot:名字",
    )
    parser.add_argument(
        "--hover",
        action="append",
        default=[],
        help="逻辑坐标 x,y：只移动光标不点击（可重复），输出 <out>_hover<i>.png",
    )
    parser.add_argument(
        "--wheel",
        action="append",
        default=[],
        help="x,y,notches：把光标放到 (x,y) 后滚动 notches 格（负=向下），"
        "在 --click 之前依次执行",
    )
    parser.add_argument("--sleep", type=float, default=1.2, help="每次点击后等待秒数")
    parser.add_argument(
        "--once",
        action="store_true",
        help="每个 --click 只注入一次点击（默认连点两次；切换类交互必须用 --once）",
    )
    parser.add_argument("--boot", type=float, default=6.0, help="启动后等待秒数")
    parser.add_argument("--out", default=str(ROOT / "output/_probe/probe.png"))
    parser.add_argument("--app", default=str(ROOT / "examples" / "demo.py"))
    parser.add_argument("--title", default=TITLE)
    parser.add_argument("--keep", action="store_true", help="保留进程（调试用）")
    parser.add_argument(
        "--repaint",
        action="store_true",
        help="截图后改窗口尺寸再还原，强制整窗重绘，输出 <out>_repaint.png",
    )
    args = parser.parse_args()

    user32.SetProcessDPIAware()

    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    log = open(ROOT / "output/_probe_app.log", "w", encoding="utf-8", errors="replace")
    proc = subprocess.Popen(
        # -u：子进程 stdout 重定向到文件，不缓冲才能在 taskkill 前留下日志
        [sys.executable, "-u", args.app],
        cwd=str(ROOT),
        stdout=log,
        stderr=subprocess.STDOUT,
        env=env,
    )
    print(f"launcher pid={proc.pid}")

    def give_up() -> None:
        time.sleep(220)
        print("! 探针超时，强制退出")
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                       capture_output=True)
        os._exit(4)

    threading.Timer(220, lambda: None).start()

    try:
        hwnd = find_window(args.title, timeout=45)
        if not hwnd:
            print("! 未找到窗口")
            return
        print(f"hwnd={hwnd}")
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        # 只挪位置、不改尺寸：窗口尺寸由应用自己按逻辑像素设定
        user32.SetWindowPos(hwnd, c_void_p(HWND_TOP), 60, 60, 0, 0,
                            SWP_SHOWWINDOW | SWP_NOSIZE)
        time.sleep(1.0)
        print(f"geometry={window_geometry(hwnd)} fg_ok={force_foreground(hwnd)}")
        time.sleep(args.boot)
        print(f"fg_ok(after boot)={user32.GetForegroundWindow() == hwnd}")

        shot = Path(args.out)
        screenshot(hwnd, shot)

        if args.repaint:
            left, top, w, h, _, _ = window_geometry(hwnd)
            for delta in (-40, 0):
                user32.SetWindowPos(
                    hwnd, c_void_p(HWND_TOP), left, top,
                    w + delta, h + delta, SWP_SHOWWINDOW,
                )
                time.sleep(0.9)
            force_foreground(hwnd)
            time.sleep(args.boot / 2)
            screenshot(hwnd, shot.with_name(f"{shot.stem}_repaint.png"))

        actions: list[str] = list(args.do)
        if not actions:
            actions = (
                [f"hover:{s}" for s in args.hover]
                + [f"wheel:{s}" for s in args.wheel]
                + [f"click:{s}" for s in args.click]
            )

        for i, spec in enumerate(actions, start=1):
            kind, _, rest = spec.partition(":")
            kind = kind.strip().lower()
            if kind != "shot":
                force_foreground(hwnd)
                time.sleep(0.3)
            if kind == "hover":
                lx, ly = (int(v) for v in rest.split(","))
                hover(hwnd, lx, ly)
            elif kind == "wheel":
                lx, ly, n = (int(v) for v in rest.split(","))
                wheel(hwnd, lx, ly, n)
            elif kind == "click":
                lx, ly = (int(v) for v in rest.split(","))
                click(hwnd, lx, ly, repeat=1 if args.once else 2)
            elif kind == "shot":
                screenshot(hwnd, shot.with_name(f"{shot.stem}_{rest}.png"))
                continue
            else:
                print(f"  ! 未知动作 {spec!r}（支持 click:x,y / wheel:x,y,n / hover:x,y / shot:name）")
                continue
            time.sleep(args.sleep)
            force_foreground(hwnd)
            time.sleep(0.3)
            screenshot(hwnd, shot.with_name(f"{shot.stem}_{i}.png"))
    except BaseException:
        import traceback

        traceback.print_exc()
    finally:
        log.flush()
        if not args.keep:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                           capture_output=True)
        log.close()
        app_log = ROOT / "output/_probe_app.log"
        if app_log.exists():
            text = app_log.read_text(encoding="utf-8", errors="replace")
            print("---- app log tail ----")
            print("\n".join(text.strip().splitlines()[-25:]))
        # os._exit 不 flush，stdout 接管道时前面所有 print 都会丢
        sys.stdout.flush()
        os._exit(0)


if __name__ == "__main__":
    main()
