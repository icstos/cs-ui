"""媒体播放控件套件 —— 可复算的配色 + 无状态控制件。

这个模块从「一个自己画控制栏的桌面播放器」里提炼出来，回答两件事：

1. **配色只有一条公式**。播放器要压在画面上，用通用表面色会跟视频抢注意力，
   于是各处手写 ``#0B1018`` 这类深蓝 —— 换品牌色时十几处一起改，且深浅两档
   永远对不上。:class:`MediaPalette` 把 ``build_scheme(brand, mode)`` 的 46 个
   M3 角色投影成播放器语汇（轨道 / 面板 / 已选 / 危险……），**只依赖品牌色和
   明暗档**，同参数必然得到同结果；``as_dict()`` 让 Agent 能直接读出整张表。
   :func:`desktop_controls` 再把同一张表下发给原生全屏控制条，Python 侧与
   Flutter 侧的蓝是同一个蓝。
2. **控制件是纯函数**。时间轴、音量、倍速、图标按钮都不持有状态：值从参数进，
   意图从回调出。于是它们可以脱离播放器单独测试、单独截图，也能被别的媒体
   应用直接复用。状态归调用方（视图模型 / ``use_state``），这里只负责画。

与 ``Video`` 的分工：``Video`` 是嵌在正文里的容器外壳，播放控制交给原生控件；
本模块给的是**自己接管交互**的播放器所需要的零件，并顺手把 ``flet_video``
的底层类型收在一个门面里，应用侧不必再直接依赖扩展包。

依赖：``flet-video``
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from functools import lru_cache

import flet as ft
import flet_video as fv

from ui.core.palette import build_scheme, tonal
from ui.core.theme import current_mode, theme_state
from ui.core.tokens import (
    FONT_SIZE,
    FONT_WEIGHT,
    ICON_SIZE,
    PRIMARY_SEEDS,
    SPACE,
)

__all__ = [
    "BAR_PADDING",
    "IconAction",
    "MaterialDesktopVideoControls",
    "MediaPalette",
    "NativeSlider",
    "NativeVideo",
    "PlaylistMode",
    "SpeedMenu",
    "TimeSlider",
    "VideoControlsMode",
    "VideoMedia",
    "VOLUME_SLIDER_WIDTH",
    "VolumeControl",
    "desktop_controls",
    "format_rate",
    "format_time",
]

# --------------------------------------------------------------------------- 原生能力门面
#: 带完整事件与 ``ref`` 的底层播放器。``ui.Video`` 是正文里的容器外壳，二者不要混用。
NativeVideo = fv.Video
#: 原生滑块。``ui.Slider`` 是 observable（要构造后调 ``.ui()``），而自己画控制栏
#: 的播放器需要「一个直接能放进控件树的 Control」，两者契约不同，故分开命名。
NativeSlider = ft.Slider
VideoMedia = fv.VideoMedia
PlaylistMode = fv.PlaylistMode
VideoControlsMode = fv.VideoControlsMode
MaterialDesktopVideoControls = fv.MaterialDesktopVideoControls

#: 音量滑块的轨道宽度。控制栏一行里既要有倍速、标题，又要留出主画面，
#: 80 是「能拖准 5% 又不吃掉标题」的折中；取自 4px 网格，不是手挑的数。
VOLUME_SLIDER_WIDTH = SPACE["10"] * 2

#: 控制条内边距：左右不对称是给滑块拇指留的余量，上下 4/2 贴着 4px 网格。
BAR_PADDING = ft.Padding.only(
    left=SPACE["2"], right=SPACE["2"], top=SPACE["1"], bottom=SPACE["1"]
)


# --------------------------------------------------------------------------- 配色
@dataclass(frozen=True, slots=True)
class MediaPalette:
    """播放器语义色表 —— 由品牌色与明暗档唯一决定。

    字段是**用途**不是色值：``track`` 是未填充轨道，``panel`` 是控制条底，
    ``active`` 是选中项，``darkest`` 是画面区黑底。任何一处想换颜色，都应改
    :meth:`derive` 的映射，而不是在组件里塞一个十六进制。

    ``as_dict()`` 是给检索 / 快照用的：整张表可以打印、可以断言、可以复算。
    """

    brand: str          # 品牌色本身（主按钮、进度、强调文字）
    primary: str
    hover: str          # 悬停：比主色亮一档
    track: str          # 未填充轨道 / 细边框
    border: str         # 面板描边
    divider: str        # 分割线
    panel: str          # 控制条 / 侧栏
    surface: str        # 页面底
    darkest: str        # 画面区黑底
    active: str         # 选中项底色
    text: str           # 主要文字
    muted: str          # 次要文字 / 图标
    danger: str         # 破坏性操作

    def as_dict(self) -> dict[str, str]:
        """整张色表的可序列化快照（供检索、测试与文档使用）。"""
        return asdict(self)

    @classmethod
    def derive(
        cls, brand: str = PRIMARY_SEEDS["blue"], *, mode: str = "dark"
    ) -> MediaPalette:
        """按品牌色与明暗档推导色表；同参数同结果，结果带缓存。

        Args:
            brand: 十六进制品牌色。
            mode: ``"dark"`` / ``"light"``，与 ``build_scheme`` 的档位一致。
        """
        return _derive(brand, mode)

    @classmethod
    def from_theme(cls) -> MediaPalette:
        """跟随当前应用主题（品牌色 + 明暗档）推导，换主色自动生效。"""
        return _derive(theme_state().primary, current_mode())


@lru_cache(maxsize=16)
def _derive(brand: str, mode: str) -> MediaPalette:
    """色表推导本体。

    只做两件事：把 ``build_scheme`` 的角色投影成播放器语汇，再从 ``tonal``
    色阶取一档作为悬停态。不读全局状态、不做 I/O —— 所以可缓存、可复算。
    """
    scheme = build_scheme(brand, mode)
    ramp = tonal(brand)
    return MediaPalette(
        brand=brand,
        primary=scheme["primary"],
        hover=ramp[300],
        track=scheme["outline_variant"],
        # 1px 线用表面梯度而不是 outline：M3 的 outline 在暗色下是亮灰（#797C7F），
        # 拉成一整条侧栏边框会盖过内容；表面梯度差一档刚好「看得见、不抢戏」。
        border=scheme["surface_container_high"],
        divider=scheme["surface_container"],
        panel=scheme["surface_container_low"],
        surface=scheme["surface"],
        darkest=scheme["surface_container_lowest"],
        active=scheme["primary_container"],
        text=scheme["on_surface"],
        muted=scheme["on_surface_variant"],
        danger=scheme["error"],
    )


def desktop_controls(palette: MediaPalette | None = None) -> MaterialDesktopVideoControls:
    """主题化的桌面全屏控制条。

    原生控制条的颜色参数要吃**具体色值**（Flutter 侧不解析角色名），所以这里
    把 :class:`MediaPalette` 的结果下发；与控制栏自绘部分同源，切到全屏时不会
    突然换一套蓝。交互参数固定：单击画面不切换播放、双击进/出全屏、挂载时不
    抢占画面 —— 控制栏由应用自己画。
    """
    p = palette or MediaPalette.from_theme()
    return MaterialDesktopVideoControls(
        seek_bar_position_color=p.primary,
        seek_bar_thumb_color=p.primary,
        seek_bar_color=p.track,
        seek_bar_hover_color=p.hover,
        volume_bar_active_color=p.primary,
        volume_bar_thumb_color=p.primary,
        volume_bar_color=p.track,
        button_bar_button_color=p.text,
        play_and_pause_on_tap=False,
        toggle_fullscreen_on_double_press=True,
        visible_on_mount=False,
    )


# --------------------------------------------------------------------------- 纯函数
def format_time(ms: int | float | None) -> str:
    """毫秒 → ``MM:SS`` / ``HH:MM:SS``；空值与负数一律读作 ``00:00``。"""
    if ms is None or ms <= 0:
        return "00:00"
    hours, remainder = divmod(int(ms) // 1000, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def format_rate(rate: float) -> str:
    """倍速 → ``1x`` / ``1.5x``（去掉无意义的尾零）。"""
    return f"{rate:g}x"


# --------------------------------------------------------------------------- 控制件
def IconAction(
    icon: ft.IconData | str,
    on_click: Callable | None = None,
    *,
    tooltip: str = "",
    disabled: bool = False,
    color: str | None = None,
    size: int = ICON_SIZE["md"],
    palette: MediaPalette | None = None,
) -> ft.IconButton:
    """紧凑图标按钮：控制栏里的最小交互单元。

    内边距走令牌、图标尺寸走图标刻度，所以一排按钮高度天然齐平；``tooltip``
    是唯一文案，避免为了说清一个图标再塞一行字压低信息密度。
    """
    p = palette or MediaPalette.from_theme()
    return ft.IconButton(
        icon=icon,
        icon_color=color or p.text,
        on_click=on_click,
        tooltip=tooltip,
        disabled=disabled,
        icon_size=size,
        style=ft.ButtonStyle(padding=ft.Padding.all(SPACE["1"])),
    )


def TimeSlider(
    position_ms: int,
    duration_ms: int,
    *,
    show_remaining: bool = False,
    label: str = "",
    disabled: bool = False,
    on_change_start: Callable | None = None,
    on_change: Callable | None = None,
    on_change_end: Callable | None = None,
    on_toggle_time: Callable | None = None,
    formatter: Callable[[int], str] = format_time,
    palette: MediaPalette | None = None,
) -> ft.Row:
    """时间轴：当前时间 + 进度滑块 + 总时长。

    左侧时间可点（``on_toggle_time``）在「已播 / 剩余」之间切换，负号只出现在
    剩余模式；拖动时的浮标文案由调用方给（``label``），组件不猜业务格式。
    三个滑块回调分别对应「开始拖 / 拖动预览 / 松手提交」，让视图模型能在拖动
    期间暂停位置轮询，避免画面回跳。
    """
    p = palette or MediaPalette.from_theme()
    maximum = max(duration_ms, 1)
    remaining = show_remaining and duration_ms > 0
    left_value = (
        f"-{formatter(max(0, duration_ms - position_ms))}"
        if remaining
        else formatter(position_ms)
    )
    left = ft.Text(left_value, color=p.muted, size=FONT_SIZE["caption"])
    if on_toggle_time is not None:
        left = ft.GestureDetector(content=left, on_tap=on_toggle_time)

    return ft.Row(
        controls=[
            left,
            ft.Slider(
                min=0,
                max=maximum,
                value=min(max(position_ms, 0), maximum),
                active_color=p.primary,
                inactive_color=p.track,
                thumb_color=p.primary,
                expand=True,
                label=label,
                disabled=disabled,
                on_change_start=on_change_start,
                on_change=on_change,
                on_change_end=on_change_end,
            ),
            ft.Text(formatter(duration_ms), color=p.muted, size=FONT_SIZE["caption"]),
        ],
        spacing=SPACE["1"],
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )


def VolumeControl(
    volume: float,
    muted: bool,
    *,
    on_change: Callable | None = None,
    on_toggle_mute: Callable | None = None,
    on_scroll: Callable | None = None,
    width: float = VOLUME_SLIDER_WIDTH,
    palette: MediaPalette | None = None,
) -> ft.Row:
    """音量组：图标按钮 + 短滑块，图标上滚滚轮也能调（``on_scroll``）。

    ``muted`` 时轨道归零但保留 ``volume`` 的值 —— 取消静音应回到原来的音量，
    而不是又从 0 开始拖。
    """
    p = palette or MediaPalette.from_theme()
    icon = ft.Icons.VOLUME_OFF if muted or volume <= 0 else ft.Icons.VOLUME_UP
    button = IconAction(
        icon, on_toggle_mute, tooltip="静音", color=p.muted, palette=p
    )
    if on_scroll is not None:
        button = ft.GestureDetector(content=button, on_scroll=on_scroll)
    return ft.Row(
        controls=[
            button,
            ft.Slider(
                min=0,
                max=100,
                value=0 if muted else volume,
                active_color=p.primary,
                inactive_color=p.track,
                thumb_color=p.primary,
                width=width,
                on_change=on_change,
            ),
        ],
        spacing=SPACE["0"],
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )


def SpeedMenu(
    rate: float,
    rates: Sequence[float],
    on_select: Callable[[float], None],
    *,
    formatter: Callable[[float], str] = format_rate,
    palette: MediaPalette | None = None,
) -> ft.PopupMenuButton:
    """倍速菜单：当前档打勾并高亮，选完即收起。

    档位由调用方给（不同业务对 0.25x~16x 的取舍不同），组件只负责把「当前值」
    显示成一行紧凑文案 —— 控制栏里不需要常驻 12 个按钮。
    """
    p = palette or MediaPalette.from_theme()
    items: list[ft.PopupMenuItem] = [
        ft.PopupMenuItem(
            content=ft.Text(
                formatter(value),
                color=p.primary if value == rate else p.text,
                size=FONT_SIZE["small"],
            ),
            icon=ft.Icons.CHECK if value == rate else None,
            on_click=lambda e, value=value: on_select(value),
        )
        for value in rates
    ]
    return ft.PopupMenuButton(
        # 纯数值（「1x」）看不出能点，跟一枚下拉箭头才符合交互直觉；
        # 箭头比文字弱一档，不跟当前倍速抢注意力。
        content=ft.Row(
            controls=[
                ft.Text(
                    formatter(rate),
                    color=p.primary,
                    size=FONT_SIZE["small"],
                    weight=FONT_WEIGHT["semibold"],
                ),
                ft.Icon(
                    ft.Icons.ARROW_DROP_DOWN,
                    size=ICON_SIZE["xs"],
                    color=p.muted,
                ),
            ],
            spacing=SPACE["0"],
        ),
        items=items,
        bgcolor=p.panel,
        menu_position=ft.PopupMenuPosition.UNDER,
    )
