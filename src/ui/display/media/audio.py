"""音频 (Audio / AudioPlayer) —— 声音的两种放法。

* :class:`Audio` 是 ``flet_audio.Audio`` 的薄封装，一个 **服务**：不进控件树、
  渲染零像素，只管加载源、播放、跳转。要把它接到自己的按钮上时用它。
* :class:`AudioPlayer` 是它的一张卡片外壳：播放 / 暂停、进度与时长、音量、
  状态文案，开箱即用。

两者共用同一套播放能力，区别只在「谁画界面」：``Audio`` 把界面留给你，
``AudioPlayer`` 替你把最常见的几件控件画好。

依赖：``flet-audio``
"""

from __future__ import annotations

from dataclasses import dataclass

import flet as ft
import flet_audio as fa

from ui.core.doc import Api, Example, Spec, info, run, tip, warn
from ui.core.i18n import t, use_t
from ui.core.tokens import FONT_SIZE, FONT_WEIGHT, ICON_SIZE, RADIUS, SPACE

__all__ = ["SPECS", "Audio", "AudioPlayer"]

#: 播放键图标本体尺寸。IconButton 自带 padding，命中区约 48，够手指也够鼠标。
PLAY_ICON = 34
#: 进度条 / 音量条的高度：Slider 的可视轨只有 4px，留 26 给滑块的光晕
SLIDER_H = 26
#: 音量条宽度。再宽就会和中间那列抢位置，窄卡片里先被压的是它右边的空白
VOLUME_W = 84
#: 低于这个宽度就收起音量块：播放键 48 + 进度条 + 读秒，再塞 100px 音量就只剩一条缝
COMPACT_W = 360
CARD_RADIUS = RADIUS["lg"]
CARD_PAD = SPACE["3"]


@ft.control
class Audio(fa.Audio):
    """音频控件，继承自 :class:`flet_audio.Audio`。

    Args:
        src: 音频地址（本地文件路径或 URL）。
        autoplay: 是否自动播放，默认 False。
        volume: 音量（0~1），默认 0.8。
        loop: 是否循环播放，默认 False；为 True 时释放策略设为 ``LOOP``。
        playback_rate: 播放倍速，默认 1.0。
    """

    volume: float = 0.8
    loop: bool = False

    def init(self):
        if self.loop:
            self.release_mode = fa.ReleaseMode.LOOP


@ft.observable
@dataclass
class _PlayerState:
    """卡片上看得见的那几个数。

    全部写在这里、由 ``@ft.component`` 重绘，而不是去改 ``IconButton.icon``：
    声明式树里的控件是冻结的，回调里赋值会抛 ``Frozen controls cannot be
    updated``（真机踩到）。
    """

    playing: bool = False
    started: bool = False  # 至少播过一次：没播过显示「未播放」而不是「已暂停」
    position: int = 0  # 毫秒
    duration: int = 0  # 毫秒；0 表示还不知道
    volume: float = 0.8


def _clock(ms: int) -> str:
    """毫秒 → ``03:07``；真超过一小时才多出小时那一段。"""
    seconds = max(0, int(ms)) // 1000
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


@ft.component
def _player_body(
    audio: Audio, state: _PlayerState, title: str, subtitle: str
) -> ft.Control:
    """卡片内容。``audio`` 只读，界面完全由 ``state`` 决定。"""
    use_t()  # 状态文案随语言切换
    ready = bool(audio.src)
    #: 窄卡片把音量整块收掉：它是唯一固定宽度的大块，留着会把进度条挤成一个点。
    #: 初值给 False，量到宽度后由 on_size_change 纠正一次。
    compact, set_compact = ft.use_state(False)

    def measure(e: ft.ControlEvent) -> None:
        narrow = float(e.width or 0) < COMPACT_W
        if narrow != compact:
            set_compact(narrow)

    async def toggle(_e: ft.ControlEvent) -> None:
        """先切图标再等播放器：``play()`` 要跨进程往返，等回来再改有半秒空窗。"""
        if not ready:
            return
        state.playing = not state.playing
        state.started = True
        if state.playing:
            await audio.play()
        else:
            await audio.pause()

    async def seek(e: ft.ControlEvent) -> None:
        """松手才跳转。拖动过程中只改读秒，不打断解码。"""
        if not state.duration:
            return
        position = int(float(e.control.value))
        state.position = position
        await audio.seek(ft.Duration.from_unit(milliseconds=position))

    def set_volume(e: ft.ControlEvent) -> None:
        value = round(float(e.control.value), 2)
        state.volume = value
        audio.volume = value
        audio.update()

    if state.playing:
        status = t("ui.audio.playing")
    elif state.started:
        status = t("ui.audio.paused")
    else:
        status = t("ui.audio.idle")

    position = min(max(0, state.position), max(0, state.duration))
    head = ft.Row(
        spacing=SPACE["2"],
        controls=[
            ft.Text(
                title,
                size=FONT_SIZE["body"],
                weight=FONT_WEIGHT["semibold"],
                max_lines=1,
                overflow=ft.TextOverflow.ELLIPSIS,
                expand=True,
            ),
            ft.Text(
                status,
                size=FONT_SIZE["caption"],
                color=ft.Colors.ON_SURFACE_VARIANT,
                no_wrap=True,
            ),
        ],
    )

    # 没有源时整条进度是「死」的：可拖却拖不出声音，比禁用它更让人困惑。
    scale = max(1, state.duration)
    track = ft.Slider(
        min=0,
        max=scale,
        value=position,
        expand=True,
        height=SLIDER_H,
        disabled=not (ready and state.duration),
        on_change_end=seek,
    )
    clock = ft.Text(
        f"{_clock(position)} / {_clock(state.duration)}",
        size=FONT_SIZE["caption"],
        color=ft.Colors.ON_SURFACE_VARIANT,
        no_wrap=True,
    )

    lines: list[ft.Control] = [
        head,
        ft.Row(
            spacing=SPACE["2"],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[track, clock],
        ),
        *(
            [
                ft.Text(
                    subtitle,
                    size=FONT_SIZE["caption"],
                    color=ft.Colors.ON_SURFACE_VARIANT,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                )
            ]
            if subtitle
            else []
        ),
    ]

    volume = ft.Row(
        spacing=SPACE["0"],
        tight=True,
        controls=[
            ft.Icon(
                ft.Icons.VOLUME_UP_ROUNDED,
                size=ICON_SIZE["md"],
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
            ft.Slider(
                min=0,
                max=1,
                divisions=10,
                value=state.volume,
                width=VOLUME_W,
                height=SLIDER_H,
                on_change=set_volume,
            ),
        ],
    )

    return ft.Container(
        # 量一次宽度决定收不收音量：Flet 没有断点，只能自己听 on_size_change
        on_size_change=measure,
        content=ft.Row(
            spacing=SPACE["2"],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.IconButton(
                    icon=(
                        ft.Icons.PAUSE_CIRCLE_FILLED
                        if state.playing
                        else ft.Icons.PLAY_CIRCLE_FILLED
                    ),
                    icon_size=PLAY_ICON,
                    # 角色色而不是写死的蓝：换主色、切深色时不用改这一行
                    icon_color=ft.Colors.PRIMARY,
                    disabled=not ready,
                    tooltip=t("ui.audio.toggle") if ready else None,
                    on_click=toggle,
                ),
                ft.Column(
                    expand=True,
                    tight=True,
                    spacing=0,
                    controls=lines,
                ),
                *([] if compact else [volume]),
            ],
        ),
    )


class AudioPlayer(ft.Container):
    """卡片式音频播放器：播放 / 暂停、进度与时长、音量、状态。

    Args:
        src: 音频地址。
        title: 标题文本。``None``（默认）取语言包里的「音频 / Audio」。
        subtitle: 次要说明文本。
        width: 卡片宽度，默认撑满容器。
    """

    def __init__(
        self,
        src: str = "",
        title: str | None = None,
        subtitle: str = "",
        width: float | None = None,
        **kwargs,
    ) -> None:
        super().__init__(width=width, **kwargs)

        self._audio = Audio(
            src=src,
            on_state_change=self._on_state_change,
            on_position_change=self._on_position_change,
            on_duration_change=self._on_duration_change,
        )
        self._state = _PlayerState(volume=float(self._audio.volume))

        # 注意（flet 1.0.0）：Audio 继承自 ft.Service 而不是 ft.Control，
        # 放进控件树会被 Flutter 判为 "Unknown control: Audio"。
        # Service 在构造时就会自行注册到 page 的服务注册表，因此这里只需
        # 用 self._audio 持有强引用（注册表按引用计数清理），不再挂进树里。
        self.content = _player_body(
            self._audio,
            self._state,
            title or t("ui.audio.title"),
            subtitle,
        )
        self.border = ft.Border.all(1, ft.Colors.OUTLINE_VARIANT)
        self.border_radius = ft.BorderRadius.all(CARD_RADIUS)
        self.padding = CARD_PAD

    @property
    def audio(self) -> Audio:
        """底层的 :class:`Audio` 服务：需要 ``seek`` / ``release`` 或读时长时用它。"""
        return self._audio

    # ------------------------------------------------------------------
    # 服务事件 → 状态
    # ------------------------------------------------------------------
    def _on_state_change(self, e: fa.AudioStateChangeEvent) -> None:
        """跟随播放器回报的状态，包括播完自动停下。"""
        self._state.playing = e.state == fa.AudioState.PLAYING
        if e.state == fa.AudioState.COMPLETED:
            # play() 默认从 0 开始，进度条也回到起点，否则"停在末尾 + 播放键"自相矛盾
            self._state.position = 0

    def _on_position_change(self, e: fa.AudioPositionChangeEvent) -> None:
        self._state.position = int(e.position)

    def _on_duration_change(self, e: fa.AudioDurationChangeEvent) -> None:
        if e.duration is not None:
            self._state.duration = e.duration.in_milliseconds


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
@ft.component
def _service_probe() -> ft.Control:
    """Audio 是服务：左边那块空白就是它渲染出来的全部。"""
    audio = ft.use_memo(lambda: Audio(src="", volume=0.6), [])
    volume, set_volume = ft.use_state(0.6)

    def change(e: ft.ControlEvent) -> None:
        value = round(float(e.control.value), 2)
        audio.volume = value  # 运行期改属性：直接写，服务对象立刻反映
        set_volume(value)

    placeholder = ft.Container(
        width=132,
        height=92,
        alignment=ft.Alignment.CENTER,
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        border_radius=ft.BorderRadius.all(CARD_RADIUS),
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=SPACE["1"],
            controls=[
                ft.Icon(
                    ft.Icons.GRAPHIC_EQ,
                    size=24,
                    color=ft.Colors.OUTLINE_VARIANT,
                ),
                ft.Text(
                    "渲染零像素",
                    size=FONT_SIZE["caption"],
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
            ],
        ),
    )

    return ft.Row(
        spacing=SPACE["4"],
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            placeholder,
            ft.Column(
                expand=True,
                spacing=SPACE["2"],
                controls=[
                    ft.Text(
                        "这个控件里的 audio 对象已经注册好了，界面上什么都没有 —— "
                        "它的价值全在你的按钮上。",
                        size=FONT_SIZE["small"],
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                    ft.Row(
                        spacing=SPACE["2"],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text(
                                "音量",
                                size=FONT_SIZE["small"],
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                            ft.Slider(
                                min=0,
                                max=1,
                                divisions=10,
                                value=volume,
                                width=180,
                                height=SLIDER_H,
                                on_change=change,
                            ),
                            ft.Text(
                                f"audio.volume = {volume:.1f}",
                                size=FONT_SIZE["small"],
                                no_wrap=True,
                            ),
                        ],
                    ),
                    ft.Text(
                        f"audio.release_mode = {audio.release_mode.value}",
                        size=FONT_SIZE["caption"],
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                ],
            ),
        ],
    )


@ft.component
def _loop_modes() -> ft.Control:
    """``loop=True`` 不是一条独立属性，它翻译成释放策略 ``LOOP``。"""
    plain = ft.use_memo(lambda: Audio(src="", loop=False), [])
    looped = ft.use_memo(lambda: Audio(src="", loop=True), [])

    def card(caption: str, mode: str) -> ft.Container:
        return ft.Container(
            expand=True,
            padding=SPACE["3"],
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=ft.BorderRadius.all(CARD_RADIUS),
            content=ft.Column(
                spacing=SPACE["1"],
                controls=[
                    ft.Text(
                        caption, size=FONT_SIZE["small"], weight=FONT_WEIGHT["medium"]
                    ),
                    ft.Text(
                        f"release_mode = {mode}",
                        size=FONT_SIZE["caption"],
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                    ft.Text(
                        "播完保留缓冲区，可立即重播"
                        if mode == "loop"
                        else "播完释放缓冲区",
                        size=FONT_SIZE["caption"],
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                ],
            ),
        )

    return ft.Column(
        spacing=SPACE["2"],
        controls=[
            ft.Row(
                spacing=SPACE["3"],
                controls=[
                    card("Audio(loop=False)", plain.release_mode.value),
                    card("Audio(loop=True)", looped.release_mode.value),
                ],
            ),
            ft.Text(
                "loop 只在构造时把 release_mode 置成 LOOP；运行期改 loop 不会生效，"
                "要改就写 release_mode。",
                size=FONT_SIZE["caption"],
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
        ],
    )


@ft.component
def _player_basic() -> ft.Control:
    return AudioPlayer(
        src="",
        title="示例音轨",
        subtitle="未给定 src · 这是没有素材时的控件骨架",
    )


@ft.component
def _player_compact() -> ft.Control:
    """窄到 320 时音量块整块收起，把宽度让给进度条。"""
    return ft.Column(
        spacing=SPACE["3"],
        controls=[
            AudioPlayer(
                src="",
                title="320px 宽的卡片",
                subtitle="窄于 360 时音量自动收起，进度条不被挤成一条缝",
                width=320,
            ),
            AudioPlayer(src="", title="撑满容器", subtitle="width 留空即跟随父级"),
        ],
    )


_SERVICE_CODE = """from ui.display.media.audio import Audio

# 事件回调写在构造参数里，随服务一起注册到客户端
audio = Audio(
    src="D:/media/intro.mp3",
    volume=0.6,
    on_state_change=lambda e: print(e.state),   # playing / paused / completed
)

Row([
    IconButton(ft.Icons.PLAY_ARROW, on_click=lambda e: e.page.run_task(audio.play)),
    IconButton(ft.Icons.PAUSE, on_click=lambda e: e.page.run_task(audio.pause)),
])

# Audio 是 Service，不进控件树；引用必须比播放活得久（模块级变量 / 页面属性都行）。"""

_PLAYER_CODE = """from ui.display.media.audio import AudioPlayer

AudioPlayer(
    src="D:/media/intro.mp3",     # 本地路径或 https 地址
    title="开场白",
    subtitle="2026-03 例会录音",
)

# 只需要播放能力就换用 Audio；卡片另有 audio 属性，
# 想自己 seek 或释放资源时用它拿到底层服务。"""

_AUDIO_SPEC = Spec(
    name="Audio",
    summary="把一段音频交给播放服务：能播、能停、能跳，但界面上不占一个像素。",
    definition=(
        "Audio 是 flet_audio 服务的薄封装，负责加载音频源、控制播放与音量，"
        "并向上抛状态、位置、时长三类事件。它刻意不画界面 —— 音频常常只是别的"
        "控件的一层能力（试听按钮、提示音、语音回放），把播放键和进度条画进来，"
        "调用方还得先把它拆掉。需要现成卡片时用 AudioPlayer。"
    ),
    anatomy=[
        (
            "音频源",
            "src 收本地路径或 URL；空串表示不加载，此时 play() 没有可播的东西。",
        ),
        (
            "播放控制",
            "play() / pause() / resume() 都是异步方法，跨进程往返，调用后要等状态事件回来才算数。",
        ),
        (
            "位置",
            "seek(position) 跳到指定时间；on_position_change 按毫秒回报当前位置，进度条就靠它。",
        ),
        (
            "音量与倍速",
            (
                "volume 取 0~1（默认 0.8，比 flet_audio 原生的 1.0 收一点），"
                "playback_rate 默认 1.0；运行期直接赋值即刻生效。"
            ),
        ),
        (
            "循环",
            "loop 只在构造时起作用：为 True 就把 release_mode 置成 LOOP，播完保留缓冲区。",
        ),
        (
            "事件",
            (
                "on_loaded / on_duration_change / on_state_change / "
                "on_position_change 四个钩子，全部由播放器线程回调。"
            ),
        ),
    ],
    when=[
        "页面里要出声，但界面元素是你自己画的（试听按钮、耳机图标、图表节点）",
        "一次要同时播放多条音频：每条一个实例，各自独立控制",
        "提示音、语音回放这类「播完就完」的短音频",
    ],
    avoid=[
        "需要播放键、进度、时长摆在那里：直接用 AudioPlayer，别自己拼",
        "有画面要放：音频控件放不出画面 —— 视频能力不在框架内，"
        "需要播放器请直接接 flet-video",
        "要波形、频谱、字幕同步：Audio 只给位置和时长，这些得自己算",
    ],
    examples=[
        Example(
            "服务，不是控件",
            _service_probe,
            hint="左边那块空白就是 Audio 渲染出来的全部；右边拖动滑块，读的是服务对象上的真实属性。",
            code=_SERVICE_CODE,
        ),
        Example(
            "循环与释放策略",
            _loop_modes,
            hint="loop=True 的真实效果是 release_mode=LOOP，而不是多出一条属性。",
        ),
    ],
    api=[
        Api("src", "str | None", "None", "音频源：本地路径或 URL；空串不加载"),
        Api("autoplay", "bool", "False", "挂载后自动播放"),
        Api("volume", "float", "0.8", "音量，取值 0~1"),
        Api("loop", "bool", "False", "循环播放；构造时翻译成 release_mode=LOOP"),
        Api("playback_rate", "float", "1.0", "播放倍速，1.0 为原速"),
        Api(
            "play(position)", "async", "0", "从指定位置开始播放；会重新加载已被释放的源"
        ),
        Api("pause()", "async", "", "暂停，之后可用 resume() 从断点继续"),
        Api("seek(position)", "async", "", "跳到指定位置，参数接受 ft.Duration"),
        Api("release()", "async", "", "释放底层播放器与缓冲；再播要重新加载"),
        Api(
            "on_state_change",
            "Callable[[AudioStateChangeEvent], None] | None",
            "None",
            "播放状态变化（playing / paused / completed / disposed）",
        ),
    ],
    notes=[
        tip(
            "Audio 继承 ft.Service，不是 ft.Control：放进 controls 会被 Flutter 判成 "
            "Unknown control。构造后要自己留一个强引用，引用一断服务就被回收、声音也停。"
        ),
        warn(
            "loop 只是构造期的开关。运行期对着正在播的实例写 audio.loop = True 不会生效，"
            "要循环就改 audio.release_mode = fa.ReleaseMode.LOOP。"
        ),
        info(
            "src 留空也能安全构造和渲染，只是没有可播的东西 —— 拿它当占位、等文件选好再赋值，"
            "不需要写额外的分支。"
        ),
    ],
    tags=("音频", "audio", "声音", "播放", "sound"),
)

_PLAYER_SPEC = Spec(
    name="AudioPlayer",
    summary="卡片式播放器：播放键、进度与时长、音量、状态，一行摆完。",
    definition=(
        "AudioPlayer 把 Audio 包成一张卡片，替你把最常见的几件控件摆好：左侧播放键、"
        "中间标题与可拖动的进度条、右侧音量。它不取音频也不缓存数据，src 给什么就放什么；"
        "所有显示都回读自底层服务，所以外部直接调 audio.pause() 时，卡片上的图标和文案也会跟着变。"
    ),
    anatomy=[
        (
            "播放键",
            "34px 圆形图标，主色，命中区约 48；没有 src 时禁用 —— 点了也没东西可播。",
        ),
        (
            "标题行",
            "标题左、状态右。标题单行省略，状态在「未播放 / 播放中 / 已暂停」之间切换。",
        ),
        (
            "进度条",
            "整行可拖的 Slider 加「00:12 / 03:45」。松手才 seek，拖动过程只更新读秒，不打断解码。",
        ),
        (
            "音量",
            (
                "喇叭图标加 10 档滑杆，拖动即写回 audio.volume；卡片窄于 360 时整块收起，"
                "把宽度让给进度条。"
            ),
        ),
        (
            "副标题",
            "可选的一行 caption 灰字，放来源、日期这类次要信息；超长同样省略。",
        ),
    ],
    when=[
        "列表或卡片里每行有一段音频，需要就地试听",
        "要看到进度并拖到某一段（会议录音、播客片段）",
        "设置页、帮助页里放一段说明音频，标题和副标题能把来龙去脉交代清楚",
    ],
    avoid=[
        "只是「响一下」的提示音：Audio 就够，一张卡片反而挡住了正文",
        "需要波形、频谱或字幕：卡片只有一条进度条，波形得自己按位置事件画",
        "完整播放器（播放列表、媒体键、后台播放）：那是独立窗口的活，不是卡片形态",
    ],
    examples=[
        Example(
            "基础用法",
            _player_basic,
            hint="没有素材时就是这样：控件全长出来了，只有播放键和进度条禁用。",
            code=_PLAYER_CODE,
        ),
        Example(
            "窄卡片与宽卡片",
            _player_compact,
            hint="320px 时音量块整块收起，进度条保住宽度；标题与副标题单行省略。",
        ),
    ],
    api=[
        Api("src", "str", "''", "音频地址：本地路径或 URL"),
        Api(
            "title", "str | None", "None", "卡片标题；留空取语言包里的「音频 / Audio」"
        ),
        Api("subtitle", "str", "''", "副标题，放来源、日期等次要信息"),
        Api("width", "float | None", "None", "卡片宽度，留空跟随父级"),
        Api(
            "audio",
            "Audio",
            "—",
            "只读属性：底层服务，要 seek / release 或读时长时拿它",
        ),
    ],
    notes=[
        tip(
            "卡片内容是 @ft.component，状态全写在 _PlayerState 上由重绘驱动。直接在回调里改 "
            "IconButton.icon 在声明式树里会抛 Frozen controls cannot be updated。"
        ),
        warn(
            "没有 src 时播放键和进度条都是禁用的：Audio.play() 对空源只会换来一次静默失败，"
            "让按钮可点等于骗用户。"
        ),
        info(
            "状态不靠按钮自己猜：on_state_change 回报什么就显示什么，播完会自动回到未播放，"
            '外部调 audio.pause() 也能同步。旧写法拿 str(e.state) 和 "playing" 比字符串，'
            "枚举转出来是 AudioState.PLAYING，永远不相等 —— 文案于是永远停在「未播放」。"
        ),
    ],
    tags=("音频播放器", "audio player", "播放", "试听"),
)


SPECS: dict[str, Spec] = {"audio": _AUDIO_SPEC, "audio_player": _PLAYER_SPEC}


if __name__ == "__main__":
    run(*SPECS.values())
