"""ColorPicker 纯逻辑单测（不需要窗口）。

覆盖：HSV / HSL 数学往返、颜色串解析与格式化、``value`` 的 flet 原生形态、
参数归一、面板几何、行结构、三种记法（HEX / RGB / HSL）的联动、透明度、
预设色板归一、清空 / 还原 / 禁用、回调去重、原值透传降级。

用法::

    python scripts/_color_picker_logic.py
"""

from __future__ import annotations

import itertools
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import flet as ft  # noqa: E402

from ui.input.color_picker import (  # noqa: E402
    DEFAULT_PRESETS,
    INNER_W,
    PANEL_W,
    ColorPicker,
    hex6,
    hex8,
    hsl_to_rgb,
    hsv_to_rgb,
    native_color,
    parse_color,
    rgb_to_hsl,
    rgb_to_hsv,
)

_fails: list[str] = []
_passed = 0


def check(name: str, got: object, want: object) -> None:
    global _passed
    if got == want:
        _passed += 1
        print(f"PASS  {name}: got={got!r}")
    else:
        _fails.append(f"{name}: got={got!r} want={want!r}")
        print(f"FAIL  {name}: got={got!r} want={want!r}")


def close(name: str, got: float, want: float, tol: float = 1e-6) -> None:
    global _passed
    if abs(got - want) <= tol:
        _passed += 1
        print(f"PASS  {name}: got={got!r}")
    else:
        _fails.append(f"{name}: got={got!r} want={want!r}")
        print(f"FAIL  {name}: got={got!r} want={want!r} (tol={tol})")


def section(title: str) -> None:
    print(f"\n== {title} ==")


def raiser(fn, *args, **kwargs) -> str:
    """跑一次调用，返回异常类名；没抛就返回空串。"""
    try:
        fn(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001
        return type(exc).__name__
    return ""


def tap(x: float | None = None, y: float | None = None) -> ft.TapEvent:
    """造一个带 / 不带坐标的点击事件。

    flet 的事件类要求 ``name`` / ``control`` 两个必填位，其余字段才有默认值；
    这里补齐，免得测试被事件类的构造细节牵住。
    """
    kwargs: dict[str, object] = {}
    if x is not None and y is not None:
        kwargs["local_position"] = ft.Offset(x, y)
    return ft.TapEvent(name="tap", control=None, **kwargs)  # type: ignore[arg-type]


def text_event(data: str, name: str = "change") -> ft.ControlEvent:
    """造一个携带文本值的控件事件（TextField 的 on_change / on_submit / on_blur）。"""
    return ft.ControlEvent(name=name, control=None, data=data)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
section("HSV / HSL 数学：全色域往返必须零误差")

PROBES = (0, 1, 17, 85, 128, 200, 254, 255)
bad = [
    (r, g, b)
    for r, g, b in itertools.product(PROBES, repeat=3)
    if hsv_to_rgb(*rgb_to_hsv(r, g, b)) != (r, g, b)
]
check("HSV 往返失败组数", len(bad), 0)
bad = [
    (r, g, b)
    for r, g, b in itertools.product(PROBES, repeat=3)
    if hsl_to_rgb(*rgb_to_hsl(r, g, b)) != (r, g, b)
]
check("HSL 往返失败组数", len(bad), 0)

check("rgb_to_hsv 红", tuple(round(x, 4) for x in rgb_to_hsv(255, 0, 0)), (0.0, 1.0, 1.0))
check("rgb_to_hsv 绿", tuple(round(x, 4) for x in rgb_to_hsv(0, 255, 0)), (120.0, 1.0, 1.0))
check("rgb_to_hsv 蓝", tuple(round(x, 4) for x in rgb_to_hsv(0, 0, 255)), (240.0, 1.0, 1.0))
check("rgb_to_hsv 黑（色相归零、饱和归零）", rgb_to_hsv(0, 0, 0), (0.0, 0.0, 0.0))
check("rgb_to_hsv 白（饱和归零）", tuple(round(x, 4) for x in rgb_to_hsv(255, 255, 255)),
      (0.0, 0.0, 1.0))
check("hsv_to_rgb 六个扇区顶点", [hsv_to_rgb(h, 1.0, 1.0) for h in (0, 60, 120, 180, 240, 300)],
      [(255, 0, 0), (255, 255, 0), (0, 255, 0), (0, 255, 255), (0, 0, 255), (255, 0, 255)])
check("hsv_to_rgb 色相越界自动绕回", hsv_to_rgb(360, 1.0, 1.0), (255, 0, 0))
check("hsv_to_rgb 负色相自动绕回", hsv_to_rgb(-120, 1.0, 1.0), (0, 0, 255))
check("rgb_to_hsl 红", tuple(round(x, 4) for x in rgb_to_hsl(255, 0, 0)), (0.0, 1.0, 0.5))
check("rgb_to_hsl 灰（饱和归零）", tuple(round(x, 4) for x in rgb_to_hsl(128, 128, 128)),
      (0.0, 0.0, 0.502))
check("hsl_to_rgb 半亮红", hsl_to_rgb(0, 1.0, 0.5), (255, 0, 0))
check("hsl_to_rgb 全亮任意色相都是白", hsl_to_rgb(210, 1.0, 1.0), (255, 255, 255))


# ---------------------------------------------------------------------------
section("十六进制格式化")

check("hex6 补零并大写", hex6(31, 111, 235), "#1F6FEB")
check("hex6 全零", hex6(0, 0, 0), "#000000")
check("hex8 CSS 顺序（默认）", hex8(124, 58, 237, 179), "#7C3AEDB3")
check("hex8 flet 顺序", hex8(124, 58, 237, 179, order="first"), "#B37C3AED")
check("native_color 不透明不加后缀", native_color(31, 111, 235), "#1F6FEB")
check("native_color 全不透明也不加后缀", native_color(31, 111, 235, 255), "#1F6FEB")
# 透明度取 3 位小数（不是 with_opacity 原样的长浮点）：这样 value 出去再 parse
# 回来必定落在同一个 0~255 整数上，来回拖动不会因为浮点误差越漂越远。
check("native_color 半透明走 with_opacity 形态（透明度 3 位小数）",
      native_color(31, 111, 235, 128),
      ft.Colors.with_opacity(round(128 / 255, 3), "#1F6FEB"))
check("native_color 半透明的数值形态", native_color(31, 111, 235, 128), "#1F6FEB,0.502")
check("native_color 全透明", native_color(31, 111, 235, 0), "#1F6FEB,0.0")


# ---------------------------------------------------------------------------
section("颜色串解析")

check("6 位带 #", parse_color("#1F6FEB"), (31, 111, 235, 255))
check("6 位不带 #", parse_color("1F6FEB"), (31, 111, 235, 255))
check("小写", parse_color("#1f6feb"), (31, 111, 235, 255))
check("3 位短写逐位翻倍", parse_color("#f0a"), (255, 0, 170, 255))
check("4 位短写含透明度", parse_color("#f0a8"), (255, 0, 170, 136))
check("8 位默认按 CSS（透明在后）", parse_color("#7C3AEDB3"), (124, 58, 237, 179))
check("8 位 hex_alpha=first 按 flet（透明在前）",
      parse_color("#B37C3AED", hex_alpha="first"), (124, 58, 237, 179))
check("with_opacity 产物", parse_color("#1F6FEB,0.5"), (31, 111, 235, 128))
check("逗号后写 0~255 也认", parse_color("#1F6FEB,128"), (31, 111, 235, 128))
check("rgb() 函数式", parse_color("rgb(31, 111, 235)"), (31, 111, 235, 255))
check("rgba() 函数式", parse_color("rgba(31,111,235,0.8)"), (31, 111, 235, 204))
check("rgb() 带百分号", parse_color("rgb(100%, 0%, 0%)"), (255, 0, 0, 255))
check("rgba() 透明度越界夹回", parse_color("rgba(0,0,0,5)"), (0, 0, 0, 255))
check("rgb() 分量越界夹回", parse_color("rgb(300,-20,0)"), (255, 0, 0, 255))
check("rgb() 参数个数不对 -> None", parse_color("rgb(1,2)"), None)
check("Material 基础色名", parse_color("red"), (244, 67, 54, 255))
check("色名大小写不敏感", parse_color("TEAL"), (0, 150, 136, 255))
check("色名可带下划线", parse_color("light_blue"), (3, 169, 244, 255))
check("ft.Colors 枚举直接可用", parse_color(ft.Colors.PURPLE), (156, 39, 176, 255))
check("transparent 归一为全透明黑", parse_color("transparent"), (0, 0, 0, 0))
check("前后空白被裁掉", parse_color("  #1F6FEB  "), (31, 111, 235, 255))
check("空串 -> None", parse_color(""), None)
check("None -> None", parse_color(None), None)
check("纯字母 -> None", parse_color("zzz"), None)
check("位数不对的十六进制 -> None", parse_color("#12345"), None)
check("主题角色解析不了 -> None（走原值透传）", parse_color("primary"), None)
check("带色阶的 Material 名解析不了 -> None", parse_color("red500"), None)

# value 出去再回来必须稳定（alpha 量化到 1/255 后不应漂移）
drift: list[tuple[str, str]] = []
for a in range(256):
    out = native_color(31, 111, 235, a)
    back = parse_color(out)
    if back != (31, 111, 235, a) or native_color(*back) != out:  # type: ignore[misc]
        drift.append((out, repr(back)))
check("native_color -> parse_color 全 256 档透明度往返无漂移", drift, [])


# ---------------------------------------------------------------------------
section("构造与默认值")

plain = ColorPicker(value="#1F6FEB")
check("默认尺寸（与其它输入组件一致）", (plain.width, plain.height), (240, 40))
check("默认允许透明度", plain.allow_alpha, True)
check("默认记法 rgb", plain._format, "rgb")
check("默认显示十六进制文本", plain.show_value, True)
check("默认可清空", plain.clearable, True)
check("默认未展开 / 未禁用", (plain.is_open, plain.disabled), (False, False))
check("默认浮层自动", plain.float_panel, None)
check("默认色板是 4 行 12 列", [len(r) for r in plain._preset_rows()], [12, 12, 12, 12])
check("rgb 属性", plain.rgb, (31, 111, 235))
check("rgb 属性对应 hex", plain.hex, "#1F6FEB")
check("不透明时 hex8 也带 FF", plain.hex8, "#1F6FEBFF")
check("rgba 属性 a 归一化", plain.rgba, (31, 111, 235, 1.0))
close("hsv 由 value 反推", plain.hsv[0], rgb_to_hsv(31, 111, 235)[0], tol=1e-9)


section("参数归一（非法值必须退回默认，不能抛）")
check("mode 非法 -> 无影响；hex_alpha 非法退回 last",
      ColorPicker(value="#1F6FEB", hex_alpha="middle")._hex_alpha, "last")
check("hex_alpha 合法值 first 保留",
      ColorPicker(value="#1F6FEB", hex_alpha="first")._hex_alpha, "first")
check("format 非法退回 rgb", ColorPicker(value="#1F6FEB", format="cmyk")._format, "rgb")
check("format hsl 保留", ColorPicker(value="#1F6FEB", format="hsl")._format, "hsl")


section("value 归一（透明度 / 越界 / 8 位顺序 / 原值透传）")
check("allow_alpha=False 时透明度被压成不透明",
      ColorPicker(value="#1F6FEB80", allow_alpha=False).rgba, (31, 111, 235, 1.0))
check("allow_alpha=True 时保留透明度",
      ColorPicker(value="#1F6FEB80").rgba, (31, 111, 235, 128 / 255))
check("hex_alpha=first 时 8 位按 flet 读",
      ColorPicker(value="#B37C3AED", hex_alpha="first").rgb, (124, 58, 237))
check("value=None 时用 default 起步",
      ColorPicker(default="#10B981").rgb, (16, 185, 129))
check("value=None 且 default 也非法 -> 兜底色，不抛",
      ColorPicker(default="primary").rgb, (31, 111, 235))
check("value 是主题角色 -> 面板仍可构建、不抛",
      raiser(lambda: ColorPicker(value=ft.Colors.PRIMARY)._build_panel()), "")
unsupported = ColorPicker(value=ft.Colors.PRIMARY)
check("主题角色走原值透传（原值交给 Flutter 解析）",
      unsupported._unsupported, ft.Colors.PRIMARY)
check("主题角色的输入框文本用它的值名（不是 Colors.PRIMARY）",
      unsupported._hex_display(), "primary")
check("主题角色时 value 原样保留（可继续喂给 flet）",
      unsupported.value, ft.Colors.PRIMARY)


# ---------------------------------------------------------------------------
section("公开操作：展开 / 收起 / 清空 / 还原")

p = ColorPicker(value="#1F6FEB")
p.open()
check("open 后 is_open", p.is_open, True)
check("open 记下原色（供还原）", p._orig, (31, 111, 235, 255))
p._pick_preset("#EF4444")
check("换色后 value 跟着变", p.value, "#EF4444")
p.revert()
check("revert 回到打开时的原色", p.value, "#1F6FEB")
p.close()
check("close 后 is_open", p.is_open, False)
check("close 后悬停态清空", p._hover, None)
check("close 后键入暂存清空", p._editing, {})

p2 = ColorPicker(value="#1F6FEB")
p2.clear()
check("clear 后 value 为 None", p2.value, None)
check("clear 后 _rgba 保留（再打开接着上次的位置）", p2.rgb, (31, 111, 235))
check("clear 后索引取色位置不变", p2._s, rgb_to_hsv(31, 111, 235)[1])
p2.clear()
check("重复 clear 是空操作（不抛）", p2.value, None)

disabled = ColorPicker(value="#1F6FEB", disabled=True)
disabled.open()
check("disabled 时 open 无效", disabled.is_open, False)
check("disabled 时数值行整段不参与构建",
      len(disabled._build_panel().content.controls),
      len(ColorPicker(value="#1F6FEB")._build_panel().content.controls) - 1)


section("回调：按值去重、清空广播 None")
seen: list[object] = []
cb = ColorPicker(value="#1F6FEB", on_change=seen.append)
cb._pick_preset("#EF4444")
cb._pick_preset("#EF4444")  # 同色，不该再回调
check("重复设同一个颜色只回调一次", seen, ["#EF4444"])
cb.clear()
check("清空也广播（None）", seen, ["#EF4444", None])
cb._pick_preset("#1F6FEB")
check("清空后再设色照常广播", seen, ["#EF4444", None, "#1F6FEB"])

no_dedupe = ColorPicker(value="#1F6FEB", on_change=seen.append)
seen.clear()
no_dedupe._mark(resync_hsv=True)
check("值没变时不回调", seen, [])


# ---------------------------------------------------------------------------
section("三种记法：HEX / RGB / HSL 联动")

c = ColorPicker(value="#1F6FEB")
check("RGB 三个数值框的值", [s[2] for s in c._num_specs()][:3], [31, 111, 235])
check("RGB 上界", [s[3] for s in c._num_specs()][:3], [255, 255, 255])
check("allow_alpha 时多一个 A 框且值为 100", c._num_specs()[3], ("a", "A", 100, 100))

c._apply_num("r", 255)
check("改 R 生效", c.rgb, (255, 111, 235))
check("改 R 后色调跟随", round(c.hsv[0], 2), round(rgb_to_hsv(255, 111, 235)[0], 2))
c._apply_num("r", 999)
check("R 越界夹到 255", c.rgb[0], 255)
c._apply_num("g", -5)
check("G 越界夹到 0", c.rgb[1], 0)

hsl_picker = ColorPicker(value="#FF0000", format="hsl")
check("HSL 模式三个数值框", [s[2] for s in hsl_picker._num_specs()][:3], [0, 100, 50])
check("HSL 模式上界", [s[3] for s in hsl_picker._num_specs()][:3], [360, 100, 100])
hsl_picker._apply_num("h", 120)
check("改 H 得到绿", hsl_picker.rgb, (0, 255, 0))
hsl_picker._apply_num("s", 0)
check("饱和度归零得到灰", hsl_picker.rgb, (128, 128, 128))
check("改 H / S / L 后不再抛（_rgba 长度恒定）", len(hsl_picker._rgba), 4)

fmt = ColorPicker(value="#1F6FEB")
check("初始记法", fmt._format, "rgb")
fmt._toggle_format()
check("切换一次 -> hsl", fmt._format, "hsl")
fmt._toggle_format()
check("再切一次 -> 回到 rgb", fmt._format, "rgb")
check("切换记法不改颜色", fmt.value, "#1F6FEB")


section("透明度")
alpha = ColorPicker(value="#1F6FEB80")
check("A 框显示 50%（128/255）", alpha._num_specs()[3][2], 50)
alpha._apply_num("a", 100)
check("A 拉到 100% 后回到纯色（value 无后缀）", alpha.value, "#1F6FEB")
alpha._apply_num("a", 0)
check("A 拉到 0% -> 全透明", alpha.value, ft.Colors.with_opacity(0.0, "#1F6FEB"))
alpha._apply_num("a", 150)
check("A 越界夹到 100", alpha._num_specs()[3][2], 100)

no_alpha = ColorPicker(value="#1F6FEB", allow_alpha=False)
check("allow_alpha=False 时不画透明度条", no_alpha._hue_h(), 146)
check("allow_alpha=False 时色相条与 SV 区等高", no_alpha._hue_h(), 146)
check("allow_alpha=False 时数值框只有 3 个", len(no_alpha._num_specs()), 3)
check("allow_alpha=True 时色相条贯穿透明度条", plain._hue_h(), 146 + 10 + 16)

a = ColorPicker(value="#1F6FEB")
a._on_alpha(tap(0, 0))
check("点透明度条最左 -> 全透明", a.rgba[3], 0.0)
a._on_alpha(tap(9999, 0))
check("点透明度条最右 -> 不透明", a.rgba[3], 1.0)


section("取色区交互（点 / 拖同一路径）")
sv = ColorPicker(value="#1F6FEB")
sv._on_sv(tap(0, 0))
check("点左上角 -> 饱和 0 明度 1（白）", sv.rgb, (255, 255, 255))
sv._on_sv(tap(0, sv._hue_h() + 1000))
check("点左下角 -> 明度 0（黑）", sv.rgb, (0, 0, 0))
sv._on_hue(tap(0, 0))
check("色相条顶端 -> 0°（黑仍是黑，色相记住了）", round(sv.hsv[0], 6), 0.0)
sv._set_hsv(0.0, 1.0, 1.0)
sv._on_hue(tap(0, 60))
check("色相条 1/3 处（146+10+16=172 高）-> 约 125°",
      round(sv.hsv[0]), round(60 / 172 * 360))
sv._on_sv(tap())  # 事件没有 local_position 时不能抛
check("事件缺 local_position 时安全返回", sv.rgb, hsv_to_rgb(*sv.hsv))


# ---------------------------------------------------------------------------
section("HEX 输入框：键入 / 回车 / 失焦")

h = ColorPicker(value="#1F6FEB")
h._on_hex_change(text_event("#10B981", "change"))
check("键入合法值即时生效", h.rgb, (16, 185, 129))
check("键入合法值不算非法", h._invalid, False)
h._on_hex_change(text_event("#10", "change"))
check("键入半截：不生效也不算错", (h.rgb, h._invalid), ((16, 185, 129), False))
check("键入原文被暂存（重渲染不打断光标）", h._editing["hex"], "#10")
h._on_hex_submit(text_event("#zzz", "submit"))
check("回车非法 -> 标红", h._invalid, True)
check("回车非法 -> 值不变", h.rgb, (16, 185, 129))
h._on_hex_submit(text_event("", "submit"))
check("回车空串 -> 不标红", h._invalid, False)
h._on_hex_submit(text_event("red", "submit"))
check("回车合法 -> 落地", h.rgb, (244, 67, 54))
check("提交后暂存被清掉", "hex" in h._editing, False)
h._on_hex_change(text_event("#00", "change"))
h._on_hex_blur(text_event("#00", "blur"))
check("失焦放弃未提交的键入", ("hex" in h._editing, h._invalid), (False, False))
check("失焦后值保持上一个合法值", h.rgb, (244, 67, 54))
h._on_hex_blur(text_event("#00", "blur"))
check("没有暂存时失焦是空操作", h.rgb, (244, 67, 54))

n = ColorPicker(value="#1F6FEB")
n._on_hex_change(text_event("#1F6FEB80", "change"))
check("键入 8 位 -> 产生半透明", n.rgba, (31, 111, 235, 128 / 255))
check("8 位键入后 hex_display 回到 8 位（大写）", n._hex_display(), "#1F6FEB80")


section("数值框：键入 / 提交")
num = ColorPicker(value="#1F6FEB")
num._on_num("r", "", commit=False)
check("清空数值框只是暂存，不改颜色", (num._editing.get("r"), num.rgb[0]), ("", 31))
num._on_num("g", "0", commit=False)
check("边打字边生效", num.rgb[1], 0)
check("暂存原文保留", num._editing.get("g"), "0")
num._on_num("g", "12", commit=False)
check("继续打字继续生效", num.rgb[1], 12)
num._on_num("g", "12", commit=True)
check("提交后清掉暂存并回填", ("g" in num._editing, num.rgb[1]), (False, 12))
num._on_num("g", "abc", commit=False)
check("非法字符（理论上被 InputFilter 挡住）不崩", num.rgb[1], 12)
num._on_num("g", "", commit=True)
check("提交空串不改颜色", num.rgb[1], 12)


# ---------------------------------------------------------------------------
section("面板几何与行结构")

inner = INNER_W
check("SV 区宽 + 间距 + 色相条 = 内容宽", 248 + 10 + 16, inner)
check("面板总宽 = 内容宽 + 左右内边距 + 描边", inner + 12 * 2 + 1 * 2, PANEL_W)

sv_square = plain._sv_square()
check("SV 区是容器", isinstance(sv_square, ft.Container), True)
check("SV 区尺寸", (sv_square.width, sv_square.height), (248, 146))
check("SV 区里面是手势层", isinstance(sv_square.content, ft.GestureDetector), True)
stack = sv_square.content.content
check("SV 区是叠层（渐变 ×2 + 光标 + 描边）", len(stack.controls), 4)
check("第一层是白→纯色相横向渐变",
      stack.controls[0].gradient.begin, ft.Alignment.CENTER_LEFT)
check("第一层终点是右侧", stack.controls[0].gradient.end, ft.Alignment.CENTER_RIGHT)
check("第二层是透明→黑纵向渐变",
      stack.controls[1].gradient.begin, ft.Alignment.TOP_CENTER)
check("第三层是光标（有白描边）", stack.controls[2].border.top.color, ft.Colors.WHITE)
check("第四层是描边层（画在渐变之上）", stack.controls[3].border.top.width, 1)

alpha_bar = plain._alpha_strip()
check("透明度条尺寸", (alpha_bar.width, alpha_bar.height), (248, 16))
check("透明度条第一层是棋盘格画布", isinstance(alpha_bar.content.content.controls[0], type(
    plain._alpha_strip().content.content.controls[0])), True)
check("透明度条滑块不越界（top=0/bottom=0 拉伸）",
      alpha_bar.content.content.controls[2].top, 0)

hue = plain._hue_strip()
check("色相条尺寸（含透明度条高度）", (hue.width, hue.height), (16, 172))
check("色相条渐变 7 个锚点", len(hue.content.content.controls[0].gradient.colors), 7)
check("色相条滑块左右都贴边（不越出条外）",
      (hue.content.content.controls[1].left, hue.content.content.controls[1].right), (0, 0))

panel = plain._build_panel()
check("面板外壳有阴影", panel.shadow is not None, True)
check("面板宽度", panel.width, PANEL_W)
check("面板圆角与输入框一致", panel.border_radius.top_left, 8)
sections = panel.content.controls
check("面板顶层 7 段（取色区 / 值行 / 数值行 / 分隔线 / 色板 / 分隔线 / 页脚）",
      len(sections), 7)
check("第一段是取色区", isinstance(sections[0], ft.Row), True)
check("第二段是值行", isinstance(sections[1], ft.Row), True)
check("第三段是数值行", isinstance(sections[2], ft.Row), True)
check("面板高度估算 > 取色区高度", plain._panel_h() > 172, True)
check("关掉透明度后面板变矮", plain._panel_h() > ColorPicker(
    value="#1F6FEB", allow_alpha=False)._panel_h(), True)
check("presets=None 时少掉「分隔线 + 色板」两段",
      len(ColorPicker(value="#1F6FEB", presets=None)._build_panel().content.controls), 5)

value_row = plain._value_row()
check("值行 3 列（对比块 / 十六进制框 / 记法切换）", len(value_row.controls), 3)
compare = value_row.controls[0]
check("对比块宽 84", compare.width, 84)
check("对比块两半 + 1px 分隔", len(compare.content.controls), 3)
check("左半可点（还原）",
      isinstance(compare.content.controls[0], ft.GestureDetector), True)
check("记法切换按钮显示 RGB", value_row.controls[2].content.value, "RGB")
check("切成 HSL 后按钮文案跟着变",
      ColorPicker(value="#1F6FEB", format="hsl")._value_row().controls[2].content.value, "HSL")

num_row = plain._num_row()
check("数值行 4 列（带透明度）", len(num_row.controls), 4)
check("数值框都等宽伸展", [c.expand for c in num_row.controls], [True] * 4)
check("数值框前缀依次是 R/G/B/A",
      [c.content.prefix.value for c in num_row.controls], ["R", "G", "B", "A"])
check("无透明度时数值行 3 列",
      len(ColorPicker(value="#1F6FEB", allow_alpha=False)._num_row().controls), 3)


section("预设色板归一")
preset = ColorPicker(value="#1F6FEB")
rows = preset._preset_rows()
check("默认 4 行", len(rows), 4)
check("默认每行 12 个", {len(r) for r in rows}, {12})
check("默认色板首尾", (rows[0][0], rows[0][-1], rows[1][0]), ("#FFFFFF", "#000000", "#F5222D"))

flat = ColorPicker(value="#1F6FEB", presets=["#000000", "#111111", "#222222", "#333333", "#444444"],
                   preset_cols=3)
check("扁平列表按 preset_cols 折行", [len(r) for r in flat._preset_rows()], [3, 2])
check("扁平列表内容保持顺序",
      flat._preset_rows()[0], ["#000000", "#111111", "#222222"])
nested = ColorPicker(value="#1F6FEB", presets=[["#000000", "#111111"], ["#222222"]])
check("嵌套列表按行原样铺开", nested._preset_rows(), [["#000000", "#111111"], ["#222222"]])
check("presets=None -> 空", ColorPicker(value="#1F6FEB", presets=None)._preset_rows(), [])
check("presets=[] -> 空", ColorPicker(value="#1F6FEB", presets=[])._preset_rows(), [])
check("preset_cols 非法（0）退回默认 12 列",
      len(ColorPicker(value="#1F6FEB", presets=[f"#00000{i}" for i in range(24)],
                      preset_cols=0)._preset_rows()), 2)
check("色块高度按列数摊平（12 列）", preset._preset_h(12), (274 - 11 * 4) // 12)
check("色块高度按列数摊平（1 列 = 整宽）", preset._preset_h(1), 274)
check("列数 <= 0 时高度为 0", preset._preset_h(0), 0)
check("色块是等宽伸展的", ColorPicker(value="#1F6FEB")._preset_swatch(
    "#123456", 19).expand, True)


section("折叠态输入框")
field = plain._build_field(plain._field_content(), plain._trailing())
check("折叠态是手势盒（整框可点）", isinstance(field, ft.GestureDetector), True)
box = field.content
check("盒尺寸取 width / height", (box.width, box.height), (240, 40))
check("未展开时边框是常态色", box.border.top.color, ft.Colors.OUTLINE_VARIANT)
plain.is_open = True
check("展开时边框转主色",
      plain._build_field(plain._field_content(), plain._trailing()).content.border.top.color,
      ft.Colors.PRIMARY)
plain._invalid = True
check("非法时边框转错误色",
      plain._build_field(plain._field_content(), plain._trailing()).content.border.top.color,
      ft.Colors.ERROR)
plain.is_open = False
plain._invalid = False

check("有值时显示 ×",
      len(plain._build_field(plain._field_content(), plain._trailing()).content.content.controls),
      3)
empty = ColorPicker(value=None)
check("没值时没有 ×",
      len(empty._build_field(empty._field_content(), empty._trailing()).content.content.controls),
      2)
check("没值时色块只画棋盘格（无颜色层）",
      len(empty._field_content().controls[0].content.controls), 1)
check("没值时面板状态已由 default 起步（面板不至于一片黑）",
      empty.rgb, (31, 111, 235))
check("有值时色块画棋盘格 + 颜色层",
      len(plain._field_content().controls[0].content.controls), 2)
check("没值时框内文本为空", empty._hex_display(), "")
compact = ColorPicker(value="#EF4444", show_value=False)
check("show_value=False 时不放文本字段",
      [type(c).__name__ for c in compact._field_content().controls], ["Container"])
check("show_value=False 时色块居中",
      compact._field_content().alignment, ft.MainAxisAlignment.CENTER)
check("show_value=True 时色块靠左",
      plain._field_content().alignment, ft.MainAxisAlignment.START)


section("稳定性：反复构建与连续操作不抛")
stress = ColorPicker(value="#1F6FEB")
for i in range(60):
    stress._on_sv(tap(i * 4, i * 2))
    stress._on_hue(tap(0, i * 3))
    stress._on_alpha(tap(i * 4, 0))
    stress._build_panel()
    stress._build_field(stress._field_content(), stress._trailing())
check("连续 60 轮拖拽 + 构建后 _rgba 仍是 4 元组", len(stress._rgba), 4)
check("连续拖拽后 h / s / v 都在合法区间",
      (0 <= stress.hsv[0] < 360, 0 <= stress.hsv[1] <= 1, 0 <= stress.hsv[2] <= 1),
      (True, True, True))
check("连续拖拽后 value 仍是 flet 可用色串",
      parse_color(stress.value) is not None, True)

for bad_value in (None, "", "  ", "#zz", "primary", ft.Colors.ON_SURFACE, 123, 4.5):
    check(f"非法 value {bad_value!r} 不抛",
          raiser(lambda v=bad_value: ColorPicker(value=v)._build_panel()), "")


# ---------------------------------------------------------------------------
print(f"\nRESULT: {'ALL PASS' if not _fails else f'{len(_fails)} FAILED'}"
      f"  (passed={_passed})")
if _fails:
    for line in _fails:
        print("  -", line)
    sys.exit(1)
