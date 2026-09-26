"""颜色选择器 (ColorPicker)。

参考 Element Plus ``el-color-picker`` / Ant Design ``ColorPicker`` / Figma 的取色面板，
按桌面端的直觉做了三处收敛：

- **面板即所见**：左侧一块 **SV 取色区**（横向 白 → 纯色相、纵向 透明 → 黑），
  右侧一整条**色相条**，下沿一条**透明度条**（棋盘格衬底）。三处都能点、都能拖，
  **即改即生效**，没有"待提交"状态 —— 中途关掉也不会丢操作；
- **三种记法同屏可编辑**：``#RRGGBB`` 十六进制输入框 + ``R / G / B``（点右侧按钮切
  ``H / S / L``）+ ``A``（0~100%）四个数值框，彼此实时联动。数值框边打字边生效，
  失焦 / 回车即归一（越界自动夹回）；敲非法内容回车时框体转红边并还原；
- **原 / 新对比**：面板左侧并排两块色 —— 左半是**打开面板那一刻**的原色（点它还原），
  右半是当前色。这是 Photoshop / Figma 的老规矩，也是"改坏了怎么回去"的出口。

再往下是 **预设色板**（默认 12 × 4，取自 Ant Design 的公开调色板：
灰阶 / 主色 / 浅色 / 深色）与页脚（``还原`` / ``清除`` / ``完成``）。

.. important::
    :attr:`ColorPicker.value` 是 **flet 原生色串**，可以直接喂给任意 flet 控件：

    * 不透明 → ``"#RRGGBB"``
    * 带透明度 → ``ft.Colors.with_opacity()`` 的产物 ``"#RRGGBB,0.8"``

    这是唯一能安全回灌进 flet 的写法。**不要**拿 ``#RRGGBBAA`` 去当 ``bgcolor``：
    flet / Flutter 的颜色串是 ``#AARRGGBB``，8 位会被读成"透明度在前"，颜色整个错掉。

    需要 CSS 顺序的 8 位十六进制（``#RRGGBBAA``）时读 :attr:`ColorPicker.hex8`；
    面板里的输入框显示的也是它。程序侧传进来的 8 位十六进制按 ``hex_alpha``
    解释（默认 ``"last"`` = CSS 顺序）。

.. note::
    ``value`` 无法解析时（比如 ``ft.Colors.PRIMARY`` 这类**主题角色** —— 它由
    Flutter 在运行时从主题解析，Python 侧拿不到 RGB）不会报错：折叠态的色块照常
    显示原值，面板以中性色起步；用户一旦在面板里动一下，值就被换成具体的十六进制。
    ``ft.Colors`` 里的 **Material 基础色名**（``red`` / ``teal`` / ``grey`` …）与
    ``transparent`` 是可以解析的。

.. note::
    面板挂在**页面浮层**（``page.overlay``）上，折叠态的高度就是整个组件占用布局的
    高度。浮层需要 ``page.render`` 这条根视图路径；``page.render_views``
    （``Router(manage_views=True)`` 视图栈）下会被视图盖住，此时自动降级为流内展开。
    见 :func:`ui.core.float_layer.overlay_usable`。

用法::

    c = ColorPicker(label="主题色", value="#1F6FEB", on_change=lambda v: print(v))
    ...
    container = c.ui()
"""

from __future__ import annotations

import math
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass

import flet as ft
from flet import canvas as fcanvas

from ui.core.float_layer import use_float_layer
from ui.core.styles import outline_input
from ui.input.input import Label
from ui.input.panel_field import (
    DISABLED_FG,
    FIELD_HEIGHT,
    FIELD_RADIUS,
    FIELD_WIDTH,
    HOVER_BG,
    LABEL_SIZE,
    SMALL_SIZE,
    PanelField,
    _truthy,
    panel_shell,
    place_panel,
)

__all__ = ["ColorPicker", "DEFAULT_PRESETS"]

# ---------------------------------------------------------------------------
# 面板尺寸
# ---------------------------------------------------------------------------
PANEL_W = 300  # 面板总宽
PANEL_PAD = 12  # 面板内边距
PANEL_BORDER = 1  # 面板描边
INNER_W = PANEL_W - PANEL_PAD * 2 - PANEL_BORDER * 2  # 面板内容宽 = 274

STRIP_W = 16  # 色相条宽
STRIP_GAP = 10  # 色相条与 SV 取色区的水平间距
ALPHA_H = 16  # 透明度条高
ALPHA_GAP = 10  # 透明度条与 SV 取色区的垂直间距
SV_H = 146  # SV 取色区高
SV_W = INNER_W - STRIP_W - STRIP_GAP  # SV 取色区宽 = 248

RADIUS = 6  # 取色区 / 色条圆角
CHIP_RADIUS = 4  # 小色块圆角
CURSOR = 14  # SV 光标直径
THUMB = 4  # 色条滑块厚度

ROW_GAP = 10  # 面板内的主要行距
ROW_H = 32  # 十六进制行 / 数值行高
COMPARE_W = 84  # 原 / 新对比块宽
FMT_W = 46  # 数值记法切换按钮宽
FOOTER_H = 34  # 页脚高

PRESET_COLS = 12  # 预设色板默认列数
PRESET_GAP = 4  # 预设色块间距

#: 十六进制输入框放行的字符（其余一律被 InputFilter 挡在门外）。
_HEX_ALLOWED = r"[0-9a-fA-F#x,\.]"

#: 默认色：面板在"当前没有值"时从它起步。
DEFAULT_COLOR = "#1F6FEB"

#: 连 ``default`` 都解析不了时的最后兜底（中性蓝）。
_FALLBACK = (31, 111, 235, 255)

#: 色相条渐变：7 个等距锚点绕色环一圈（0° → 360° 回到红）。
_HUE_STOPS = (
    "#FF0000",
    "#FFFF00",
    "#00FF00",
    "#00FFFF",
    "#0000FF",
    "#FF00FF",
    "#FF0000",
)

#: 六个色相扇区里 ``(r, g, b)`` 各自取 ``(c, x, 0)`` 中的哪一个：
#: ``0`` = c、``1`` = x、``2`` = 0。索引 = ``int(h // 60) % 6``。
#: HSV 与 HSL 的扇区划分完全相同，只是 c / x / m 的算法不同，所以共用这张表。
_HUE_PLAN = (
    (0, 1, 2),  #   0°~ 60°  红 → 黄   (c, x, 0)
    (1, 0, 2),  #  60°~120°  黄 → 绿   (x, c, 0)
    (2, 0, 1),  # 120°~180°  绿 → 青   (0, c, x)
    (2, 1, 0),  # 180°~240°  青 → 蓝   (0, x, c)
    (1, 2, 0),  # 240°~300°  蓝 → 品红 (x, 0, c)
    (0, 2, 1),  # 300°~360°  品红 → 红 (c, 0, x)
)

#: 数值三件套的记法顺序（点右上角按钮往后走一格，循环）。
_FORMATS = ("rgb", "hsl")

#: ``hex_alpha`` 的合法取值：``"last"`` = CSS ``#RRGGBBAA``；
#: ``"first"`` = flet / Flutter ``#AARRGGBB``。
_HEX_ORDERS = ("last", "first")

#: 预设色板默认四行：灰阶 / 主色 / 浅色 / 深色。
#: 色值取自 Ant Design 公开调色板的 day-6 / day-4 / day-7。
DEFAULT_PRESETS: tuple[tuple[str, ...], ...] = (
    (
        "#FFFFFF", "#FAFAFA", "#F5F5F5", "#E8E8E8", "#D9D9D9", "#C0C0C0",
        "#A6A6A6", "#8C8C8C", "#737373", "#595959", "#262626", "#000000",
    ),
    (
        "#F5222D", "#FA541C", "#FA8C16", "#FAAD14", "#FADB14", "#A0D911",
        "#52C41A", "#13C2C2", "#1890FF", "#2F54EB", "#722ED1", "#EB2F96",
    ),
    (
        "#FF7875", "#FF9C6E", "#FFC069", "#FFD666", "#FFF566", "#D3F261",
        "#95DE64", "#5CDBD3", "#69C0FF", "#85A5FF", "#B37FEB", "#FF85C0",
    ),
    (
        "#CF1322", "#D4380D", "#D46B08", "#D48806", "#D4B106", "#7CB305",
        "#389E0D", "#08979C", "#096DD9", "#1D39C4", "#531DAB", "#C41D7F",
    ),
)

#: ``ft.Colors`` 里那批 **Material 基础色**的十六进制值。
#:
#: 键是"去掉下划线的小写名"：``ft.Colors.LIGHT_BLUE`` → ``'lightblue'``。
#: 只收基础色（对应 Flutter 的 ``Colors.<name>``）—— 带色阶的（``RED_500``）、
#: 强调色（``RED_ACCENT``）以及 ``PRIMARY`` 这类**主题角色**在 Python 侧拿不到
#: 具体数值，统一走"原值透传"的降级路径（见模块 docstring）。
_MATERIAL: dict[str, str] = {
    "red": "#F44336",
    "pink": "#E91E63",
    "purple": "#9C27B0",
    "deeppurple": "#673AB7",
    "indigo": "#3F51B5",
    "blue": "#2196F3",
    "lightblue": "#03A9F4",
    "cyan": "#00BCD4",
    "teal": "#009688",
    "green": "#4CAF50",
    "lightgreen": "#8BC34A",
    "lime": "#CDDC39",
    "yellow": "#FFEB3B",
    "amber": "#FFC107",
    "orange": "#FF9800",
    "deeporange": "#FF5722",
    "brown": "#795548",
    "grey": "#9E9E9E",
    "gray": "#9E9E9E",
    "bluegrey": "#607D8B",
    "bluegray": "#607D8B",
    "black": "#000000",
    "white": "#FFFFFF",
}

_RGB_FN = re.compile(r"rgba?\(([^)]*)\)")
_HEX_DIGITS = re.compile(r"[0-9a-fA-F]+")


# ---------------------------------------------------------------------------
# 纯函数工具
# ---------------------------------------------------------------------------
def _clamp(value: float, lo: float, hi: float) -> float:
    """把 ``value`` 夹进 ``[lo, hi]``。"""
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value


def _opt(value: object, allowed: Sequence[str], fallback: str) -> str:
    """枚举参数归一：不在 ``allowed`` 里就退回 ``fallback``。"""
    return value if value in allowed else fallback  # type: ignore[return-value]


def _hue_paint(h: float, c: float, x: float, m: float) -> tuple[int, int, int]:
    """按色相所在扇区把 ``(c, x, 0)`` 落到 r / g / b 上（HSV 与 HSL 共用）。"""
    plan = _HUE_PLAN[int((h % 360) // 60) % 6]
    vals = (c, x, 0.0)
    return (
        round((vals[plan[0]] + m) * 255),
        round((vals[plan[1]] + m) * 255),
        round((vals[plan[2]] + m) * 255),
    )


def rgb_to_hsv(r: int, g: int, b: int) -> tuple[float, float, float]:
    """``(r, g, b)`` 0~255 → ``(h 0~360, s 0~1, v 0~1)``。"""
    rf, gf, bf = r / 255, g / 255, b / 255
    mx, mn = max(rf, gf, bf), min(rf, gf, bf)
    d = mx - mn
    if d == 0:
        h = 0.0
    elif mx == rf:
        h = 60 * (((gf - bf) / d) % 6)
    elif mx == gf:
        h = 60 * ((bf - rf) / d + 2)
    else:
        h = 60 * ((rf - gf) / d + 4)
    return h % 360, (0.0 if mx == 0 else d / mx), mx


def hsv_to_rgb(h: float, s: float, v: float) -> tuple[int, int, int]:
    """``(h 0~360, s 0~1, v 0~1)`` → ``(r, g, b)`` 0~255。"""
    c = v * s
    x = c * (1 - abs((h % 360) / 60 % 2 - 1))
    return _hue_paint(h, c, x, v - c)


def rgb_to_hsl(r: int, g: int, b: int) -> tuple[float, float, float]:
    """``(r, g, b)`` 0~255 → ``(h 0~360, s 0~1, l 0~1)``。"""
    rf, gf, bf = r / 255, g / 255, b / 255
    mx, mn = max(rf, gf, bf), min(rf, gf, bf)
    d = mx - mn
    light = (mx + mn) / 2
    if d == 0:
        h = s = 0.0
    else:
        s = d / (2 - mx - mn) if light > 0.5 else d / (mx + mn)
        if mx == rf:
            h = 60 * (((gf - bf) / d) % 6)
        elif mx == gf:
            h = 60 * ((bf - rf) / d + 2)
        else:
            h = 60 * ((rf - gf) / d + 4)
    return h % 360, s, light


def hsl_to_rgb(h: float, s: float, l: float) -> tuple[int, int, int]:
    """``(h 0~360, s 0~1, l 0~1)`` → ``(r, g, b)`` 0~255。"""
    c = (1 - abs(2 * l - 1)) * s
    x = c * (1 - abs((h % 360) / 60 % 2 - 1))
    return _hue_paint(h, c, x, l - c / 2)


def hex6(r: int, g: int, b: int) -> str:
    """``(r, g, b)`` → ``"#RRGGBB"``（大写）。"""
    return f"#{r:02X}{g:02X}{b:02X}"


def hex8(r: int, g: int, b: int, a: int, order: str = "last") -> str:
    """``(r, g, b, a)`` → 8 位十六进制；``order`` 决定透明度在前还是在后。"""
    rgb, alpha = f"{r:02X}{g:02X}{b:02X}", f"{a:02X}"
    return f"#{alpha}{rgb}" if order == "first" else f"#{rgb}{alpha}"


def native_color(r: int, g: int, b: int, a: int = 255) -> str:
    """转成 **flet 原生色串**：不透明是 ``#RRGGBB``，带透明度是 ``#RRGGBB,0.8``。"""
    base = hex6(r, g, b)
    return base if a >= 255 else ft.Colors.with_opacity(round(a / 255, 3), base)


def parse_color(
    text: object, *, hex_alpha: str = "last"
) -> tuple[int, int, int, int] | None:
    """尽力把颜色串解析成 ``(r, g, b, a)``（分量 0~255），失败返回 ``None``。

    接受：``#RGB`` / ``#RGBA`` / ``#RRGGBB`` / 8 位十六进制（顺序由 ``hex_alpha``
    决定）、``rgb(31,111,235)`` / ``rgba(31,111,235,0.8)``（分量可带 ``%``）、
    ``ft.Colors.with_opacity`` 的产物 ``#RRGGBB,0.8``、``ft.Colors`` 里的
    Material 基础色名与 ``transparent``。
    """
    if text is None:
        return None
    if isinstance(text, ft.Colors):
        text = text.value  # 'red' / 'red500' / 'primary' …

    s = str(text).strip()
    if not s:
        return None
    low = s.lower()

    # rgb() / rgba()：串里本来就有逗号，必须排在"逗号分隔透明度"前面判。
    m = _RGB_FN.fullmatch(low)
    if m:
        parts = [p.strip() for p in m.group(1).split(",")]
        if len(parts) not in (3, 4):
            return None
        try:
            vals = [
                round(_clamp(float(p[:-1]), 0, 100) * 2.55)
                if p.endswith("%")
                else round(_clamp(float(p), 0, 255))
                for p in parts[:3]
            ]
            alpha = 255
            if len(parts) == 4:
                p = parts[3]
                if p.endswith("%"):
                    raw = _clamp(float(p[:-1]), 0, 100) / 100
                else:
                    raw = _clamp(float(p), 0, 1)
                alpha = round(raw * 255)
        except ValueError:
            return None
        return vals[0], vals[1], vals[2], alpha

    # ft.Colors.with_opacity 的产物："#RRGGBB,0.8" / "#RRGGBB,1.0"
    if "," in low:
        head, _, tail = low.rpartition(",")
        base = parse_color(head, hex_alpha=hex_alpha)
        if base is None:
            return None
        try:
            raw = float(tail)
        except ValueError:
            return None
        if raw > 1:  # 也认 0~255 的写法
            raw /= 255
        return base[0], base[1], base[2], round(_clamp(raw, 0.0, 1.0) * 255)

    if low == "transparent":
        return 0, 0, 0, 0
    named = _MATERIAL.get(low.replace("_", ""))
    if named:
        return int(named[1:3], 16), int(named[3:5], 16), int(named[5:7], 16), 255

    digits = low[1:] if low.startswith("#") else low
    if not _HEX_DIGITS.fullmatch(digits):
        return None
    if len(digits) == 3:
        return (
            int(digits[0] * 2, 16),
            int(digits[1] * 2, 16),
            int(digits[2] * 2, 16),
            255,
        )
    if len(digits) == 4:
        return (
            int(digits[0] * 2, 16),
            int(digits[1] * 2, 16),
            int(digits[2] * 2, 16),
            int(digits[3] * 2, 16),
        )
    if len(digits) == 6:
        return (
            int(digits[0:2], 16),
            int(digits[2:4], 16),
            int(digits[4:6], 16),
            255,
        )
    if len(digits) == 8:
        if hex_alpha == "first":  # flet / Flutter：透明在前
            return (
                int(digits[2:4], 16),
                int(digits[4:6], 16),
                int(digits[6:8], 16),
                int(digits[0:2], 16),
            )
        return (  # CSS：透明在后
            int(digits[0:2], 16),
            int(digits[2:4], 16),
            int(digits[4:6], 16),
            int(digits[6:8], 16),
        )
    return None


def _checker(w: float, h: float, tile: int = 8) -> ft.Control:
    """半透明色的衬底：棋盘格。

    用 ``canvas`` 逐格画方块，而不是贴一张图片 —— 否则要带一份 base64 资源，
    还得担心缩放插值把格子糊掉。
    """
    shapes: list[ft.Control] = [
        fcanvas.Rect(0, 0, w, h, paint=ft.Paint(color="#D9D9D9"))
    ]
    for row in range(math.ceil(h / tile)):
        for col in range(math.ceil(w / tile)):
            if (row + col) % 2:
                continue
            shapes.append(
                fcanvas.Rect(
                    col * tile,
                    row * tile,
                    min(tile, w - col * tile),
                    min(tile, h - row * tile),
                    paint=ft.Paint(color="#FFFFFF"),
                )
            )
    return fcanvas.Canvas(width=w, height=h, shapes=shapes)


# ---------------------------------------------------------------------------
# 组件
# ---------------------------------------------------------------------------
@ft.observable
@dataclass
class ColorPicker(PanelField, Label):
    """颜色选择器：色块输入框 + 悬浮取色面板。

    Args:
        value: 当前颜色，**flet 原生色串**（``"#RRGGBB"``，或
            ``ft.Colors.with_opacity()`` 的产物 ``"#RRGGBB,0.8"``）。
            ``None`` 表示未选择（显示 ``placeholder``）。
        default: 未选择时面板的起步色。
        placeholder: 未选择时的占位文本。
        width: 输入框宽度，默认 240。``show_value=False`` 时可调窄成纯色块按钮。
        height: 输入框高度，默认 40。
        show_value: 折叠态是否显示十六进制文本；``False`` 时只留色块与下拉箭头。
        allow_alpha: 是否允许透明度。关掉则透明度条与 ``A`` 框一并隐藏，值恒为不透明。
        hex_alpha: 8 位十六进制的顺序。``"last"``（默认）= CSS ``#RRGGBBAA``；
            ``"first"`` = flet / Flutter ``#AARRGGBB``。只影响 8 位写法 ——
            :attr:`value` 始终是 flet 原生色串。
        format: ``"rgb"``（默认）/ ``"hsl"`` —— 数值三件套的记法，面板里可随时切换。
        presets: 预设色板。``None`` 或空则整块隐藏；扁平列表按 ``preset_cols``
            折行，嵌套列表按行原样铺开。
        preset_cols: 扁平 ``presets`` 的列数，默认 12。
        clearable: 是否允许清空（框内 × 与页脚「清除」），默认 True。
        disabled: 是否禁用。
        is_open: 面板是否展开（运行期状态，可代码控制）。
        float_panel: 面板是否走页面浮层。``None``（默认）表示自动：浮层可用时
            悬挂，否则退化为流内展开。``True`` / ``False`` 强制指定。
        on_change: 颜色变化回调，接收最新的 flet 原生色串（清空时是 ``None``）。
            按值去重，同一个颜色只回调一次。
    """

    value: str | None = None
    default: str = DEFAULT_COLOR
    placeholder: str = "请选择颜色"
    width: int | float = FIELD_WIDTH
    height: int | float = FIELD_HEIGHT
    show_value: bool = True
    allow_alpha: bool = True
    hex_alpha: str = "last"
    format: str = "rgb"
    presets: Sequence[str] | Sequence[Sequence[str]] | None = DEFAULT_PRESETS
    preset_cols: int | None = None
    clearable: bool = True
    disabled: bool = False
    is_open: bool = False
    float_panel: bool | None = None
    on_change: Callable[[str | None], None] | None = None

    def __post_init__(self) -> None:
        # 运行期状态：下划线开头 => 不参与序列化，变更后靠 notify() 重绘。
        self._hover: str | None = None  # 当前悬停元素的 key
        self._anchor: tuple[float, float] | None = None  # 输入框左上角页面坐标
        self._field_w: float = float(self.width)  # 输入框实测宽（on_size_change 上报）
        self._field_h: float = float(self.height)
        self._invalid: bool = False  # 键入内容非法（框体转红边）
        self._editing: dict[str, str] = {}  # 正在键入的原文（key -> text）
        self._unsupported: str | None = None  # 解析不了的原值（主题角色等）
        self._emitted: str | None = self.value  # 上次广播出去的值
        self._orig: tuple[int, int, int, int] | None = None  # 展开面板那一刻的原色
        # 面板的**规范状态**是 h / s / v / a —— 拖动只改它们。
        # 若每次都从 rgb 反推 h / s / v，``s = 0``（灰）或 ``v = 0``（黑）时色相会丢，
        # 表现是"拖着拖着色相条自己跳走"。所以只在值被外部换掉时才反推一次。
        self._rgba: tuple[int, int, int, int] = _FALLBACK
        self._h, self._s, self._v = rgb_to_hsv(*_FALLBACK[:3])
        self._a: int = 255
        self._synced: bool = False  # 是否已经用 value / default 起步过
        self._sync_value()
        # 构造时就要求展开的（内联面板形态），原色当场记下来 —— 否则对比块
        # 左半会一直是"空"，用户根本没法还原。
        if self.is_open:
            self._orig = None if self._unsupported else self._rgba

    # ------------------------------------------------------------------
    # 参数归一
    # ------------------------------------------------------------------
    @property
    def _hex_alpha(self) -> str:
        """8 位十六进制的顺序（非法值退回 ``"last"``）。"""
        return _opt(self.hex_alpha, _HEX_ORDERS, "last")

    @property
    def _format(self) -> str:
        """数值三件套的记法（非法值退回 ``"rgb"``）。"""
        return _opt(self.format, _FORMATS, "rgb")

    # ------------------------------------------------------------------
    # 状态同步
    # ------------------------------------------------------------------
    def _adopt(self, rgba: tuple[int, int, int, int], *, force: bool = False) -> None:
        """把 ``(r, g, b, a)`` 收进面板状态；``force`` 时连 h / s / v 一起反推。

        ``allow_alpha=False`` 时透明度一律压成不透明 —— 值恒等于用户看到的样子。
        """
        if not self.allow_alpha:
            rgba = (rgba[0], rgba[1], rgba[2], 255)
        reseed = force or rgba != self._rgba
        self._rgba = rgba
        self._a = rgba[3]
        if reseed:
            self._h, self._s, self._v = rgb_to_hsv(*rgba[:3])

    def _sync_value(self) -> None:
        """把外部对 ``value`` 的改动同步进面板状态。

        - ``value`` 能解析 → 采纳它；
        - ``value`` 为空 → **保留**面板当前位置（``default`` 只在第一次同步时
          用来起步 —— 否则用户清空后再拖动，每帧都会被拉回默认色）；
        - 解析不了（主题角色等）→ 记下原值走"原值透传"，面板保持不动。
        """
        parsed = parse_color(self.value, hex_alpha=self._hex_alpha)
        if parsed is not None:
            self._unsupported = None
            self._adopt(parsed, force=not self._synced)
            self._synced = True
            return

        if self.value is not None:
            # 解析不了：色块把原值原样交给 Flutter（主题角色它能认），面板保持不动。
            # 非字符串 / 非色枚举的值先用 str() 兜住，免得 bgcolor 收到奇怪类型。
            self._unsupported = (
                self.value
                if isinstance(self.value, (str, ft.Colors))
                else str(self.value)
            )
            self._synced = True
            return

        self._unsupported = None
        if not self._synced:
            fallback = parse_color(self.default, hex_alpha=self._hex_alpha)
            self._adopt(fallback or _FALLBACK, force=True)
        self._synced = True

    def _emit(self) -> None:
        """广播变化（按值去重）。"""
        if self.value != self._emitted:
            self._emitted = self.value
            if self.on_change:
                self.on_change(self.value)

    def _mark(self, *, resync_hsv: bool) -> None:
        """把 ``_rgba`` 写回 ``value`` 并重绘；``resync_hsv`` 时反推 h / s / v。"""
        r, g, b, a = self._rgba
        self._a = a
        if resync_hsv:
            self._h, self._s, self._v = rgb_to_hsv(r, g, b)
        self._unsupported = None
        new = native_color(r, g, b, a if self.allow_alpha else 255)
        if new != self.value:
            self.value = new
        self._emit()
        self.notify()  # type: ignore[attr-defined]

    def _set_hsv(self, h: float, s: float, v: float, alpha: int | None = None) -> None:
        """由 h / s / v（+ 透明度）算出 rgb 并落地 —— 拖动取色区都走这条。"""
        self._h, self._s, self._v = h, s, v
        self._rgba = (*hsv_to_rgb(h, s, v), self._a if alpha is None else alpha)
        self._mark(resync_hsv=False)

    # ------------------------------------------------------------------
    # 公开操作
    # ------------------------------------------------------------------
    def open(self) -> None:
        """展开面板，并把当前色记为"原色"（供对比块还原）。"""
        if self.disabled or self.is_open:
            return
        self._orig = None if self._unsupported else self._rgba
        self._editing.clear()
        self._invalid = False
        self.is_open = True
        self.notify()  # type: ignore[attr-defined]

    def close(self) -> None:
        """收起面板（颜色已经落地，不存在"未提交"的改动）。"""
        if not self.is_open:
            return
        self.is_open = False
        self._hover = None
        self._editing.clear()
        self._invalid = False
        self.notify()  # type: ignore[attr-defined]

    def toggle_open(self) -> None:
        """展开 / 收起。"""
        self.close() if self.is_open else self.open()

    def clear(self) -> None:
        """清空已选颜色（面板的取色位置保留，再打开时接着上次的位置）。"""
        if self.value is None:
            return
        self.value = None
        self._unsupported = None
        self._editing.clear()
        self._invalid = False
        self._emit()
        self.notify()  # type: ignore[attr-defined]

    def revert(self) -> None:
        """还原成展开面板那一刻的颜色（点对比块左半）。"""
        if self._orig is None:
            self.clear()
            return
        self._rgba = self._orig
        self._mark(resync_hsv=True)

    def set_color(self, color: str) -> None:
        """以程序方式改颜色（等同赋 ``value`` 后刷新）。解析不了就原样透传。"""
        parsed = parse_color(color, hex_alpha=self._hex_alpha)
        if parsed is None:
            self.value = color
            self._unsupported = color
            self._synced = True
            self._emit()
            self.notify()  # type: ignore[attr-defined]
            return
        self._adopt(parsed, force=True)
        self._mark(resync_hsv=False)

    # ------------------------------------------------------------------
    # 只读属性
    # ------------------------------------------------------------------
    @property
    def rgb(self) -> tuple[int, int, int]:
        """当前颜色的 ``(r, g, b)``，分量 0~255。"""
        return self._rgba[0], self._rgba[1], self._rgba[2]

    @property
    def rgba(self) -> tuple[int, int, int, float]:
        """当前颜色的 ``(r, g, b, a)``，``a`` 归一化到 0~1。"""
        return self._rgba[0], self._rgba[1], self._rgba[2], self._rgba[3] / 255

    @property
    def hsv(self) -> tuple[float, float, float]:
        """当前颜色的 ``(h 0~360, s 0~1, v 0~1)``。

        色相按 ``[0, 360)`` 归一输出 —— 内部为了色相条滑块的位置会保留 ``360``
        （拖到底就是"整条走完"，滑块不该弹回顶端），但对外 ``360`` 与 ``0`` 等价。
        """
        return self._h % 360, self._s, self._v

    @property
    def hsl(self) -> tuple[float, float, float]:
        """当前颜色的 ``(h 0~360, s 0~1, l 0~1)``。"""
        return rgb_to_hsl(*self.rgb)

    @property
    def hex(self) -> str:
        """``"#RRGGBB"``（丢掉透明度）。"""
        return hex6(*self.rgb)

    @property
    def hex8(self) -> str:
        """含透明度的 8 位十六进制，顺序按 ``hex_alpha``。"""
        return hex8(*self._rgba, order=self._hex_alpha)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    @ft.component
    def ui(self) -> ft.Control:
        """构建颜色选择器 UI。"""
        page = ft.context.page
        self._sync_value()
        field = self._build_field(self._field_content(), self._trailing())
        floating = self._should_float(page)
        show_panel = self.is_open and not self.disabled
        # 面板只在展开时才构建 —— 一块面板有四百来个控件（渐变层、棋盘格、
        # 数值框、48 个预设色块），收起着还每帧造一遍纯属浪费。
        panel = self._build_panel() if show_panel else ft.Container()

        if floating:
            # 面板在浮层里，布局只占折叠态的高度。
            body: ft.Control = field
        elif show_panel:
            # 降级：面板流内展开，下方内容随之下移。
            body = ft.Column(controls=[field, panel], spacing=4)
        else:
            body = field

        left, top, bottom = place_panel(
            page, self._anchor, self._field_h, PANEL_W, self._panel_h()
        )
        # 无条件调用（hook 顺序必须稳定）；visible=False 时浮层自动移除。
        # hole 把输入框从遮罩里挖出来：展开后还要能点框内文字改十六进制。
        use_float_layer(
            page=page,
            visible=floating and show_panel,
            left=left,
            top=top,
            bottom=bottom,
            content=panel,
            on_dismiss=self.close,
            hole=self._hole(),
        )

        return self._with_label(body)

    # ---- 折叠态 ----

    def _trailing(self) -> ft.Control:
        """折叠态右端的下拉箭头（禁用时压灰）。"""
        return ft.Icon(
            ft.Icons.KEYBOARD_ARROW_DOWN,
            size=18,
            color=ft.Colors.OUTLINE if self.disabled else ft.Colors.ON_SURFACE_VARIANT,
        )

    def _field_content(self) -> ft.Control:
        """折叠态左端：色块（+ 十六进制文本）。"""
        controls: list[ft.Control] = [
            self._swatch(
                self._display_rgba(),
                raw=self._unsupported,
                w=22,
                h=22,
                radius=CHIP_RADIUS,
                border=True,
            )
        ]
        if self.show_value:
            controls.append(ft.Container(expand=True, content=self._hex_field()))
        return ft.Row(
            spacing=8,
            alignment=ft.MainAxisAlignment.CENTER
            if not self.show_value
            else ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=controls,
        )

    def _hex_field(self) -> ft.Control:
        """框内十六进制文本。收起态 ``ignore_pointers`` —— 让点击穿透到外层手势。"""
        return ft.TextField(
            value=self._editing.get("hex", self._hex_display()),
            border=ft.NoInputBorder(),
            filled=False,
            dense=True,
            text_size=SMALL_SIZE,
            color=self._fg,
            content_padding=ft.Padding.symmetric(vertical=6),
            hint_text=self.placeholder,
            hint_style=ft.TextStyle(size=SMALL_SIZE, color=ft.Colors.OUTLINE),
            input_filter=ft.InputFilter(allow=True, regex_string=_HEX_ALLOWED),
            read_only=self.disabled,
            # 关键：收起（或禁用）时不吃指针事件，否则外层 GestureDetector 拿不到点击。
            ignore_pointers=self.disabled or not self.is_open,
            on_change=None if self.disabled else self._on_hex_change,
            on_submit=None if self.disabled else self._on_hex_submit,
            on_blur=None if self.disabled else self._on_hex_blur,
        )

    def _raw_text(self) -> str:
        """"原值透传"时给输入框看的文本。

        原值本身要原样交给 Flutter 去解析（``bgcolor=ft.Colors.PRIMARY``），
        但 ``str(ft.Colors.PRIMARY)`` 是 ``"Colors.PRIMARY"`` —— 塞进输入框太丑，
        这里换成它真正带的值 ``"primary"``。
        """
        raw = self._unsupported
        return str(raw.value) if isinstance(raw, ft.Colors) else str(raw)

    def _display_rgba(self) -> tuple[int, int, int, int] | None:
        """折叠态色块该显示什么。没有值就是"空"（只画棋盘格）。

        面板自己在用的 ``_rgba`` 不能拿来当折叠态的显示 —— 用户清空之后它还停在
        上一次的位置，色块却应该回到"未选择"，否则跟空白的输入框自相矛盾。
        """
        return None if self.value is None else self._rgba

    def _hex_display(self) -> str:
        """折叠态该显示什么：原值透传 > 8 位（带透明度）> 6 位。"""
        if self._unsupported is not None:
            return self._raw_text()
        if self.value is None:
            return ""
        r, g, b, a = self._rgba
        if not self.allow_alpha or a >= 255:
            return hex6(r, g, b)
        return hex8(r, g, b, a, self._hex_alpha)

    def _on_hex_change(self, e: ft.ControlEvent) -> None:
        """键入过程中即时解析：合法就落地并广播，全程不打断输入。"""
        text = e.data or ""
        self._editing["hex"] = text
        self._invalid = False
        parsed = parse_color(text, hex_alpha=self._hex_alpha)
        if parsed is not None:
            self._rgba = parsed if self.allow_alpha else (*parsed[:3], 255)
            self._mark(resync_hsv=True)
            return
        self.notify()  # type: ignore[attr-defined]

    def _on_hex_submit(self, e: ft.ControlEvent) -> None:
        """回车提交：合法则落地，非法则标红（框体转红边，值不变）。"""
        text = e.data if e.data is not None else self._hex_display()
        self._editing.pop("hex", None)
        parsed = parse_color(text, hex_alpha=self._hex_alpha)
        if parsed is None:
            # 空串不算错 —— 只是"还没想好"，标红反而吓人。
            self._invalid = bool((text or "").strip())
            self.notify()  # type: ignore[attr-defined]
            return
        self._invalid = False
        self._rgba = parsed if self.allow_alpha else (*parsed[:3], 255)
        self._mark(resync_hsv=True)

    def _on_hex_blur(self, e: ft.ControlEvent) -> None:
        """失焦即放弃未提交的键入（回到格式化值）。"""
        if "hex" not in self._editing:
            return
        self._editing.pop("hex", None)
        self._invalid = False
        self.notify()  # type: ignore[attr-defined]

    # ---- 面板骨架 ----

    def _hue_h(self) -> int:
        """色相条高：允许透明度时贯穿"SV 区 + 间距 + 透明度条"。"""
        return SV_H + (ALPHA_GAP + ALPHA_H if self.allow_alpha else 0)

    def _preset_rows(self) -> list[list[str]]:
        """归一后的预设色板（以行为单位）。"""
        presets = self.presets
        if not presets:
            return []
        if isinstance(presets[0], (list, tuple)):
            return [[str(c) for c in row] for row in presets]  # type: ignore[union-attr]
        cols = self.preset_cols if self.preset_cols and self.preset_cols > 0 else PRESET_COLS
        flat = [str(c) for c in presets]
        return [flat[i : i + cols] for i in range(0, len(flat), cols)]

    @staticmethod
    def _preset_h(cols: int) -> int:
        """预设色块的边长：按列数把内容宽摊平，保持正方形。"""
        if cols < 1:
            return 0
        return max(8, int((INNER_W - (cols - 1) * PRESET_GAP) / cols))

    def _panel_h(self) -> float:
        """面板高度估算 —— ``place_panel`` 靠它决定"向下弹还是向上翻"。"""
        h = PANEL_PAD * 2 + PANEL_BORDER * 2
        h += self._hue_h()
        h += (ROW_GAP + ROW_H) * 2  # 十六进制行 + 数值行
        rows = self._preset_rows()
        if rows:
            h += ROW_GAP * 2 + 1
            h += sum(self._preset_h(len(r)) for r in rows)
            h += PRESET_GAP * (len(rows) - 1)
        h += ROW_GAP + 1 + FOOTER_H  # 分隔线 + 页脚
        return h

    def _build_panel(self) -> ft.Control:
        """取色面板：取色区 + 十六进制行 + 数值行 + 预设色板 + 页脚。"""
        sections: list[ft.Control] = [self._picker_block(), self._value_row()]
        if not self.disabled:
            sections.append(self._num_row())
        rows = self._preset_rows()
        if rows:
            sections += [self._divider(), self._preset_block(rows)]
        sections += [self._divider(), self._footer()]
        return panel_shell(
            width=PANEL_W,
            pad=PANEL_PAD,
            body=ft.Column(spacing=ROW_GAP, controls=sections),
        )

    # ---- 取色区 ----

    def _picker_block(self) -> ft.Control:
        """SV 取色区 + 右侧色相条；透明度条贴在取色区下沿。"""
        left: list[ft.Control] = [self._sv_square()]
        if self.allow_alpha:
            left += [ft.Container(height=ALPHA_GAP), self._alpha_strip()]
        return ft.Row(
            spacing=STRIP_GAP,
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                ft.Column(spacing=0, width=SV_W, controls=left),
                self._hue_strip(),
            ],
        )

    def _sv_square(self) -> ft.Control:
        """SV 取色区：横轴饱和度、纵轴明度。

        底色是"白 → 纯色相"的横向渐变，再叠一层"透明 → 黑"的纵向渐变 ——
        两层线性渐变正好覆盖整个 HSV 彩色平面，比插值出一张位图省得多。
        """
        pure = hex6(*hsv_to_rgb(self._h, 1.0, 1.0))
        x = _clamp(self._s * SV_W - CURSOR / 2, 0, SV_W - CURSOR)
        y = _clamp((1 - self._v) * SV_H - CURSOR / 2, 0, SV_H - CURSOR)
        cursor = ft.Container(
            left=x,
            top=y,
            width=CURSOR,
            height=CURSOR,
            border_radius=ft.BorderRadius.all(CURSOR / 2),
            bgcolor=hex6(*self.rgb),
            border=ft.Border.all(2, ft.Colors.WHITE),
            # 白色描边压在浅色区域上会看不见，所以再补一圈无偏移的黑色柔光。
            shadow=ft.BoxShadow(
                blur_radius=4,
                color=ft.Colors.with_opacity(0.55, ft.Colors.BLACK),
                offset=ft.Offset(0, 0),
            ),
        )
        return ft.Container(
            width=SV_W,
            height=SV_H,
            border_radius=ft.BorderRadius.all(RADIUS),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=ft.GestureDetector(
                on_tap_down=self._on_sv,
                on_pan_start=self._on_sv,
                on_pan_update=self._on_sv,
                mouse_cursor=ft.MouseCursor.PRECISE,
                content=ft.Stack(
                    width=SV_W,
                    height=SV_H,
                    controls=[
                        ft.Container(
                            width=SV_W,
                            height=SV_H,
                            gradient=ft.LinearGradient(
                                begin=ft.Alignment.CENTER_LEFT,
                                end=ft.Alignment.CENTER_RIGHT,
                                colors=[ft.Colors.WHITE, pure],
                            ),
                        ),
                        ft.Container(
                            width=SV_W,
                            height=SV_H,
                            gradient=ft.LinearGradient(
                                begin=ft.Alignment.TOP_CENTER,
                                end=ft.Alignment.BOTTOM_CENTER,
                                colors=[
                                    ft.Colors.with_opacity(0.0, ft.Colors.BLACK),
                                    ft.Colors.BLACK,
                                ],
                            ),
                        ),
                        cursor,
                        # 描边要画在渐变之上，所以放在最后。
                        ft.Container(
                            width=SV_W,
                            height=SV_H,
                            border_radius=ft.BorderRadius.all(RADIUS),
                            border=ft.Border.all(
                                1, ft.Colors.with_opacity(0.18, ft.Colors.ON_SURFACE)
                            ),
                        ),
                    ],
                ),
            ),
        )

    def _hue_strip(self) -> ft.Control:
        """色相条：整条竖向，0° 在上、360° 在下。"""
        h = self._hue_h()
        top = _clamp(self._h / 360 * h - THUMB / 2, 0, h - THUMB)
        return ft.Container(
            width=STRIP_W,
            height=h,
            border_radius=ft.BorderRadius.all(3),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=ft.GestureDetector(
                on_tap_down=self._on_hue,
                on_pan_start=self._on_hue,
                on_pan_update=self._on_hue,
                content=ft.Stack(
                    width=STRIP_W,
                    height=h,
                    controls=[
                        ft.Container(
                            width=STRIP_W,
                            height=h,
                            gradient=ft.LinearGradient(
                                begin=ft.Alignment.TOP_CENTER,
                                end=ft.Alignment.BOTTOM_CENTER,
                                colors=list(_HUE_STOPS),
                            ),
                        ),
                        # 滑块做成一条横线、不越出色条边界：跨出去的部分在 Stack 里
                        # 画得出来却点不到，反而破坏拖拽的手感。
                        ft.Container(
                            left=0,
                            right=0,
                            top=top,
                            height=THUMB,
                            bgcolor=ft.Colors.WHITE,
                            border=ft.Border.all(
                                1, ft.Colors.with_opacity(0.35, ft.Colors.BLACK)
                            ),
                            border_radius=ft.BorderRadius.all(2),
                        ),
                    ],
                ),
            ),
        )

    def _alpha_strip(self) -> ft.Control:
        """透明度条：棋盘格衬底 + "全透明 → 当前色"的横向渐变。"""
        r, g, b, a = self._rgba
        base = hex6(r, g, b)
        left = _clamp(a / 255 * SV_W - THUMB / 2, 0, SV_W - THUMB)
        return ft.Container(
            width=SV_W,
            height=ALPHA_H,
            border_radius=ft.BorderRadius.all(3),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=ft.GestureDetector(
                on_tap_down=self._on_alpha,
                on_pan_start=self._on_alpha,
                on_pan_update=self._on_alpha,
                content=ft.Stack(
                    width=SV_W,
                    height=ALPHA_H,
                    controls=[
                        _checker(SV_W, ALPHA_H),
                        ft.Container(
                            width=SV_W,
                            height=ALPHA_H,
                            gradient=ft.LinearGradient(
                                begin=ft.Alignment.CENTER_LEFT,
                                end=ft.Alignment.CENTER_RIGHT,
                                colors=[ft.Colors.with_opacity(0.0, base), base],
                            ),
                        ),
                        ft.Container(
                            top=0,
                            bottom=0,
                            left=left,
                            width=THUMB,
                            bgcolor=ft.Colors.WHITE,
                            border=ft.Border.all(
                                1, ft.Colors.with_opacity(0.35, ft.Colors.BLACK)
                            ),
                            border_radius=ft.BorderRadius.all(2),
                        ),
                    ],
                ),
            ),
        )

    # ---- 取色区交互 ----

    def _on_sv(self, e: ft.ControlEvent) -> None:
        """SV 取色区：点与拖走同一条路径（``local_position`` 就是区内坐标）。"""
        lp = getattr(e, "local_position", None)
        if lp is None:
            return
        self._set_hsv(
            self._h,
            _clamp(lp.x / SV_W, 0.0, 1.0),
            1 - _clamp(lp.y / SV_H, 0.0, 1.0),
        )

    def _on_hue(self, e: ft.ControlEvent) -> None:
        """色相条：纵向位置映射到 0~360°。"""
        lp = getattr(e, "local_position", None)
        if lp is None:
            return
        self._set_hsv(_clamp(lp.y / self._hue_h(), 0.0, 1.0) * 360, self._s, self._v)

    def _on_alpha(self, e: ft.ControlEvent) -> None:
        """透明度条：横向位置映射到 0~255。"""
        lp = getattr(e, "local_position", None)
        if lp is None:
            return
        self._a = round(_clamp(lp.x / SV_W, 0.0, 1.0) * 255)
        self._rgba = (*self.rgb, self._a)
        self._mark(resync_hsv=False)

    # ---- 原新对比 + 十六进制 + 记法切换 ----

    def _value_row(self) -> ft.Control:
        """一行：原 / 新对比块 + 十六进制输入框 + 数值记法切换。"""
        return ft.Row(
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                self._compare(),
                ft.Container(expand=True, height=ROW_H, content=self._hex_box()),
                self._format_button(),
            ],
        )

    def _hex_box(self) -> ft.Control:
        """面板里的十六进制输入框（带描边，便于看清输入区）。"""
        return ft.Container(
            height=ROW_H,
            border_radius=ft.BorderRadius.all(FIELD_RADIUS - 2),
            border=ft.Border.all(
                1, ft.Colors.ERROR if self._invalid else ft.Colors.OUTLINE_VARIANT
            ),
            padding=ft.Padding.symmetric(horizontal=10),
            alignment=ft.Alignment.CENTER_LEFT,
            content=ft.TextField(
                value=self._editing.get("hex", self._hex_display()),
                border=ft.NoInputBorder(),
                filled=False,
                dense=True,
                text_size=SMALL_SIZE,
                color=ft.Colors.ERROR if self._invalid else ft.Colors.ON_SURFACE,
                content_padding=ft.Padding.symmetric(vertical=6),
                hint_text="#RRGGBB",
                hint_style=ft.TextStyle(size=SMALL_SIZE, color=ft.Colors.OUTLINE),
                input_filter=ft.InputFilter(allow=True, regex_string=_HEX_ALLOWED),
                on_change=self._on_hex_change,
                on_submit=self._on_hex_submit,
                on_blur=self._on_hex_blur,
            ),
        )

    def _compare(self) -> ft.Control:
        """原 / 新对比：左半是展开面板时的原色，点它还原。"""
        half = COMPARE_W // 2
        return ft.Container(
            width=COMPARE_W,
            height=ROW_H,
            border_radius=ft.BorderRadius.all(FIELD_RADIUS - 2),
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=ft.Row(
                spacing=0,
                controls=[
                    ft.GestureDetector(
                        on_tap=lambda _e: self.revert(),
                        mouse_cursor=ft.MouseCursor.CLICK,
                        tooltip=ft.Tooltip(message="还原到打开面板时的颜色"),
                        content=self._swatch(self._orig, w=half, h=ROW_H, radius=0),
                    ),
                    ft.Container(width=1, height=ROW_H, bgcolor=ft.Colors.OUTLINE_VARIANT),
                    self._swatch(
                        self._rgba, raw=self._unsupported, w=half - 1, h=ROW_H, radius=0
                    ),
                ],
            ),
        )

    def _format_button(self) -> ft.Control:
        """数值三件套的记法切换：RGB ⇄ HSL。"""
        label = self._format.upper()
        return ft.Container(
            width=FMT_W,
            height=ROW_H,
            alignment=ft.Alignment.CENTER,
            border_radius=ft.BorderRadius.all(FIELD_RADIUS - 2),
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            bgcolor=HOVER_BG if self._hover == "fmt" else None,
            on_click=lambda _e: self._toggle_format(),
            on_hover=lambda e: self._hover_key("fmt", _truthy(e.data)),
            tooltip=ft.Tooltip(message=f"数值记法：{label}（点击切换）"),
            content=ft.Text(
                label,
                size=LABEL_SIZE,
                weight=ft.FontWeight.W_600,
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
        )

    def _toggle_format(self) -> None:
        """RGB → HSL → RGB …"""
        idx = _FORMATS.index(self._format)
        self.format = _FORMATS[(idx + 1) % len(_FORMATS)]
        self._editing.clear()
        self.notify()  # type: ignore[attr-defined]

    # ---- 数值三件套 ----

    def _num_specs(self) -> list[tuple[str, str, int, int]]:
        """``(key, 前缀, 当前值, 上界)`` —— 下界恒为 0，所以只带上界。"""
        r, g, b, a = self._rgba
        if self._format == "hsl":
            h, s, light = rgb_to_hsl(r, g, b)
            specs = [
                ("h", "H", round(h), 360),
                ("s", "S", round(s * 100), 100),
                ("l", "L", round(light * 100), 100),
            ]
        else:
            specs = [("r", "R", r, 255), ("g", "G", g, 255), ("b", "B", b, 255)]
        if self.allow_alpha:
            specs.append(("a", "A", round(a / 255 * 100), 100))
        return specs

    def _num_row(self) -> ft.Control:
        """R / G / B（或 H / S / L）+ A 四个数值框，实时联动。"""
        return ft.Row(
            spacing=6,
            controls=[self._num_field(*spec) for spec in self._num_specs()],
        )

    def _num_field(self, key: str, prefix: str, value: int, hi: int) -> ft.Control:
        """单个数值框：边打字边生效，失焦 / 回车即归一。"""
        return ft.Container(
            expand=True,
            height=ROW_H,
            content=ft.TextField(
                value=self._editing.get(key, str(value)),
                prefix=ft.Text(
                    prefix,
                    size=LABEL_SIZE,
                    weight=ft.FontWeight.W_600,
                    color=ft.Colors.OUTLINE,
                ),
                border=outline_input(
                    radius=FIELD_RADIUS - 2, color=ft.Colors.OUTLINE_VARIANT
                ),
                filled=False,
                dense=True,
                text_size=SMALL_SIZE,
                text_align=ft.TextAlign.CENTER,
                content_padding=ft.Padding.symmetric(horizontal=4, vertical=4),
                input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]"),
                tooltip=ft.Tooltip(message=f"{prefix}：0 ~ {hi}"),
                on_change=lambda e, k=key: self._on_num(k, e.data, commit=False),
                on_submit=lambda e, k=key: self._on_num(k, e.data, commit=True),
                on_blur=lambda e, k=key: self._on_num(k, e.data, commit=True),
            ),
        )

    def _on_num(self, key: str, text: str | None, *, commit: bool) -> None:
        """数值框的键入 / 提交。

        ``commit=False``（键入中）只把原文记下来，能解析就顺手应用 —— 一边打字
        一边就能看到颜色变，同时原文不会被重新格式化打断光标；
        ``commit=True``（回车 / 失焦）清掉暂存，越界值夹回边界并回填。
        """
        raw = (text or "").strip()
        if not commit:
            self._editing[key] = raw
            if raw.isdigit():
                self._apply_num(key, int(raw))
                return
            self.notify()  # type: ignore[attr-defined]
            return

        self._editing.pop(key, None)
        if raw.isdigit():
            self._apply_num(key, int(raw))
            return
        self.notify()  # type: ignore[attr-defined]

    def _apply_num(self, key: str, value: int) -> None:
        """把一个数值框的新值并进当前颜色。"""
        r, g, b, a = self._rgba
        if key == "a":
            self._rgba = (r, g, b, round(_clamp(value, 0, 100) / 100 * 255))
            self._mark(resync_hsv=False)
            return
        if key in ("r", "g", "b"):
            channel = {"r": r, "g": g, "b": b}
            channel[key] = round(_clamp(value, 0, 255))
            self._rgba = (channel["r"], channel["g"], channel["b"], a)
            self._mark(resync_hsv=True)
            return
        h, s, light = rgb_to_hsl(r, g, b)
        if key == "h":
            h = _clamp(value, 0, 360)
        elif key == "s":
            s = _clamp(value, 0, 100) / 100
        else:
            light = _clamp(value, 0, 100) / 100
        self._rgba = (*hsl_to_rgb(h, s, light), a)
        self._mark(resync_hsv=True)

    # ---- 预设色板 ----

    def _preset_block(self, rows: list[list[str]]) -> ft.Control:
        """预设色板：点一下即选中，悬停描一圈主色。"""
        return ft.Column(
            spacing=PRESET_GAP,
            controls=[self._preset_row(row) for row in rows],
        )

    def _preset_row(self, row: list[str]) -> ft.Control:
        """一行预设色块（等宽摊平，保持正方形）。"""
        height = self._preset_h(len(row))
        return ft.Row(
            spacing=PRESET_GAP,
            controls=[self._preset_swatch(color, height) for color in row],
        )

    def _preset_swatch(self, color: str, height: int) -> ft.Control:
        """单个预设色块。预设一律不透明，所以直接拿颜色当底色，不必铺棋盘格。"""
        rgba = parse_color(color, hex_alpha=self._hex_alpha) or (0, 0, 0, 255)
        hot = self._hover == f"p{color}"
        return ft.Container(
            expand=True,
            height=height,
            bgcolor=native_color(*rgba),
            border_radius=ft.BorderRadius.all(CHIP_RADIUS - 1),
            border=ft.Border.all(
                1,
                ft.Colors.PRIMARY
                if hot
                else ft.Colors.with_opacity(0.12, ft.Colors.ON_SURFACE),
            ),
            on_click=lambda _e, c=color: self._pick_preset(c),
            on_hover=lambda e, c=color: self._hover_key(f"p{c}", _truthy(e.data)),
            tooltip=ft.Tooltip(message=color),
        )

    def _pick_preset(self, color: str) -> None:
        """点预设色块：直接落地（透明度归 1，与 Element Plus / Ant Design 一致）。"""
        parsed = parse_color(color, hex_alpha=self._hex_alpha)
        if parsed is None:
            return
        self._editing.clear()
        self._invalid = False
        self._rgba = parsed if self.allow_alpha else (*parsed[:3], 255)
        self._mark(resync_hsv=True)

    # ---- 页脚 ----

    def _footer(self) -> ft.Control:
        """页脚：左「还原」，右「清除 / 完成」。"""
        controls: list[ft.Control] = [
            self._link_button(
                "revert", "还原", self.revert, enabled=self._orig is not None
            ),
            ft.Container(expand=True),
        ]
        if self.clearable:
            controls.append(
                self._link_button(
                    "clear", "清除", self.clear, enabled=self.value is not None
                )
            )
        controls.append(self._link_button("done", "完成", self.close))
        return ft.Container(
            height=FOOTER_H,
            padding=ft.Padding.only(left=2, right=2),
            content=ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=controls
            ),
        )

    # ---- 色块 ----

    @staticmethod
    def _swatch(
        rgba: tuple[int, int, int, int] | None,
        *,
        raw: str | None = None,
        w: float,
        h: float,
        radius: float = CHIP_RADIUS,
        border: bool = False,
    ) -> ft.Control:
        """固定尺寸的色块：棋盘格衬底 + 颜色层。

        ``raw`` 给了就把它当 flet 色值直接铺（解析不了的原值走这条，交给 Flutter
        自己解析）；``rgba`` 为 ``None`` 时只画棋盘格，表示"没有颜色"。
        """
        if raw is not None:
            inner: ft.Control = ft.Container(width=w, height=h, bgcolor=raw)
        else:
            layers: list[ft.Control] = [_checker(w, h)]
            if rgba is not None:
                layers.append(
                    ft.Container(width=w, height=h, bgcolor=native_color(*rgba))
                )
            inner = ft.Stack(width=w, height=h, controls=layers)
        return ft.Container(
            width=w,
            height=h,
            border_radius=ft.BorderRadius.all(radius),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.15, ft.Colors.ON_SURFACE))
            if border
            else None,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=inner,
        )


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
@ft.component
def App() -> ft.Control:
    """ColorPicker 组件运行示例。"""
    brand = ColorPicker(
        label="品牌色",
        value="#1F6FEB",
        on_change=lambda v: print(f"[ColorPicker] 品牌色 -> {v}"),
    )
    accent = ColorPicker(
        label="强调色",
        value="#10B981",
        allow_alpha=False,
        format="hsl",
        placeholder="选个强调色",
    )
    overlay = ColorPicker(
        label="叠加层",
        value="#7C3AEDB3",  # 8 位 + hex_alpha="last" => #7C3AED 的 70% 不透明
        default="#7C3AED",
        preset_cols=8,
    )
    compact = ColorPicker(value="#EF4444", show_value=False, width=64)
    no_preset = ColorPicker(label="无预设色板", value="#F59E0B", presets=None)
    frozen = ColorPicker(label="只读", value="#94A3B8", disabled=True, clearable=False)

    return ft.Column(
        controls=[
            ft.Text("ColorPicker 颜色选择器", size=20, weight=ft.FontWeight.BOLD),
            ft.Text(
                "点框体挂出取色面板（悬浮、不推下方内容）：左上下拖动改饱和/明度，"
                "右侧色相条、下沿透明度条都能拖；十六进制框与 R/G/B(/A) 数值框实时联动。",
                size=13,
                color="#6B7280",
            ),
            ft.Divider(),
            brand.ui(),
            ft.Divider(),
            accent.ui(),
            ft.Divider(),
            overlay.ui(),
            ft.Divider(),
            no_preset.ui(),
            ft.Divider(),
            frozen.ui(),
            ft.Divider(),
            ft.Text("折叠成纯色块按钮（show_value=False）", size=13, color="#6B7280"),
            ft.Row(controls=[compact.ui()]),
            ft.Divider(),
            ft.Button(
                content="打印当前值",
                on_click=lambda _: print(
                    f"{brand.value} / {accent.value} / {overlay.value} / "
                    f"{compact.value} / {no_preset.value} / {frozen.value}"
                ),
            ),
        ],
        spacing=14,
    )


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
