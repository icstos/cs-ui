"""视频 (Video) —— 一段视频，或者一整条播放列表。

对 ``flet_video.Video`` 的轻量封装：把单条 URL / 本地路径规范化成
``playlist=[VideoMedia(...)]``，再统一圆角与尺寸默认值。播放、进度、全屏这些
交互全部由底层播放器自己提供 —— 这一层只决定「放在哪儿、多大、几集连不连播」。

用法::

    Video(src="D:/media/demo.mp4", height=320)
    Video(playlist=build_playlist(["ep1.mp4", "ep2.mp4"]), loop=True)

依赖：``flet-video``
"""

from __future__ import annotations

from dataclasses import field

import flet as ft
import flet_video as fv

from ui.core.doc import Api, Example, Spec, info, run, tip, warn
from ui.core.tokens import FONT_SIZE, FONT_WEIGHT, ICON_SIZE, RADIUS, SPACE

__all__ = ["SPEC", "Video", "VideoMedia", "build_playlist"]

VideoMedia = fv.VideoMedia

#: 播放器默认高度：16:9 的片子放在 960 宽的正文里，320 刚好一屏能看全
DEFAULT_HEIGHT = 320


def build_playlist(sources: str | list[str], **kwargs) -> list[fv.VideoMedia]:
    """把 1~N 个地址转换为 ``VideoMedia`` 列表。

    Args:
        sources: 单个地址或地址列表。
        **kwargs: 透传给 :class:`flet_video.VideoMedia` 的参数。
    """
    if isinstance(sources, str):
        sources = [sources]
    return [fv.VideoMedia(resource=s, **kwargs) for s in sources]


@ft.control
class Video(ft.Container):
    """视频播放器，继承自 :class:`flet.Container`。

    Args:
        src: 单个视频地址 / 本地路径。
        playlist: 多集播放列表（与 ``src`` 二选一，同时给时以列表为准）。
        title: 原生后端的窗口 / 进程名，不是画面上的标题。
        height: 播放器高度，默认 320。
        width: 播放器宽度，默认撑满。
        autoplay: 是否自动播放，默认 False。
        loop: 是否循环播放，默认 False。
        muted: 是否静音，默认 False。
        border_radius: 圆角，默认 8。
    """

    # 子类自定义字段一律 kw_only：否则 Video("a.mp4") 会把地址塞进 Container.content。
    src: str | None = field(default=None, kw_only=True)
    playlist: list[fv.VideoMedia] = field(default_factory=list, kw_only=True)
    title: str = field(default="Video", kw_only=True)
    autoplay: bool = field(default=False, kw_only=True)
    loop: bool = field(default=False, kw_only=True)
    muted: bool = field(default=False, kw_only=True)
    # height / border_radius 继承自 ft.Container 的 kw_only 字段，重新声明时
    # 必须显式 kw_only=True，否则会变成位置参数（详见 ui.input.button.Button）。
    height: float = field(default=DEFAULT_HEIGHT, kw_only=True)
    border_radius: int = field(default=RADIUS["lg"], kw_only=True)

    def init(self):
        media: list[fv.VideoMedia] = list(self.playlist or [])
        if not media and self.src:
            media = build_playlist(self.src)

        self.clip_behavior = ft.ClipBehavior.HARD_EDGE
        self.content = fv.Video(
            playlist=media,
            title=self.title,
            autoplay=self.autoplay,
            muted=self.muted,
            playlist_mode=fv.PlaylistMode.LOOP if self.loop else None,
            expand=True,
        )


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
@ft.component
def _empty_shell() -> ft.Control:
    return ft.Column(
        spacing=SPACE["2"],
        controls=[
            Video(height=240),
            ft.Text(
                "没有 src 也没有 playlist 时，这里就是播放器本来的空样子：一块黑底，"
                "没有画面，也没有可点的控制条。",
                size=FONT_SIZE["caption"],
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
        ],
    )


@ft.component
def _playlist_preview() -> ft.Control:
    """把播放列表摊开看：Video 收的就是这几个字段。"""
    media = build_playlist(
        ["ep-01.mp4", "ep-02.mp4", "ep-03.mp4"], extras={"season": "1"}
    )
    items: list[ft.Control] = []
    for index, item in enumerate(media, start=1):
        items.append(
            ft.Container(
                padding=ft.Padding.symmetric(
                    horizontal=SPACE["3"], vertical=SPACE["2"]
                ),
                border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                border_radius=ft.BorderRadius.all(RADIUS["md"]),
                content=ft.Row(
                    spacing=SPACE["2"],
                    controls=[
                        ft.Text(
                            f"{index:02d}",
                            size=FONT_SIZE["caption"],
                            color=ft.Colors.PRIMARY,
                            weight=FONT_WEIGHT["bold"],
                        ),
                        ft.Icon(
                            ft.Icons.MOVIE_OUTLINED,
                            size=ICON_SIZE["md"],
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        ft.Text(item.resource, size=FONT_SIZE["body"], expand=True),
                        ft.Text(
                            f"extras={item.extras}",
                            size=FONT_SIZE["caption"],
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                    ],
                ),
            )
        )

    return ft.Column(
        spacing=SPACE["2"],
        controls=[
            ft.Text(
                f"build_playlist(...) 得到 {len(media)} 项 VideoMedia：",
                size=FONT_SIZE["small"],
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
            *items,
            ft.Text(
                "原样交给 Video(playlist=...) 就是一条播放列表；loop=True 时播完回到第一项。",
                size=FONT_SIZE["caption"],
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
        ],
    )


_SRC_CODE = """from ui.display.media.video import Video

Video(
    src="D:/media/demo.mp4",   # 本地路径或 https 地址
    height=320,
    autoplay=False,
    muted=False,
)"""

_LIST_CODE = """from ui.display.media.video import Video, build_playlist

Video(
    playlist=build_playlist(["ep-01.mp4", "ep-02.mp4", "ep-03.mp4"]),
    title="课程回放",     # 原生后端的进程名，不出现在画面上
    loop=True,           # playlist_mode=LOOP：播完回到第一集
    height=320,
)"""

SPEC = Spec(
    name="Video",
    summary="把一段视频或一整条播放列表嵌进页面，播放控制交给播放器自己。",
    definition=(
        "Video 是 flet_video 的容器外壳：把单个地址规范成一项播放列表，再统一高度、圆角"
        "与溢出裁切。它不接管交互 —— 播放、进度、音量、全屏都由底层播放器提供，这一层"
        "只回答「放在哪儿、多大、几集连不连播」。正因为不管交互，它适合直接嵌在正文里，"
        "而不适合做需要自定义时间轴或弹幕的编辑器。"
    ),
    anatomy=[
        (
            "播放器本体",
            "flet_video 自带的控制条（播放、进度、音量、全屏）压在画面上，外壳不再叠第二套按钮。",
        ),
        (
            "尺寸与圆角",
            "height 默认 320、圆角 8，配 HARD_EDGE 裁切：视频不会从圆角外溢出来。",
        ),
        (
            "单源",
            "src 只收一个地址，init 时包成一项 playlist；与 playlist 同时给时列表优先。",
        ),
        (
            "播放列表",
            "playlist 是 VideoMedia 列表；loop=True 时设成 PlaylistMode.LOOP，播完自动回第一项。",
        ),
        (
            "起播行为",
            "autoplay / muted 原样透传。要自动播放又不想被系统拦，就把 muted 一起打开。",
        ),
        (
            "进程名",
            "title 是原生后端的窗口 / 进程名（系统音量合成器里能看到），画面上不显示。",
        ),
    ],
    when=[
        "教程、演示、产品介绍视频要嵌在正文里，一屏能看全",
        "多集内容按顺序连播，播完回到第一集（build_playlist + loop）",
        "希望播放控制保持浏览器 / 系统播放器的习惯，不想自己实现全屏与音量",
    ],
    avoid=[
        "只有声音：用 Audio 或 AudioPlayer，视频控件在黑框里放声音是浪费一块版面",
        "需要逐帧、自定义时间轴、弹幕：外壳只做容器，这些要接底层播放器的事件",
        "只想展示一张封面：用 Image，挂一个不播的播放器只是给页面加一块黑",
    ],
    examples=[
        Example(
            "基础用法",
            _empty_shell,
            hint="示例舞台没有视频素材，这里就是不给源时的原样：一块黑底，连控制条都不出现。",
            code=_SRC_CODE,
        ),
        Example(
            "播放列表",
            _playlist_preview,
            hint="build_playlist 的产物摊开看：每一项就是一个资源地址外加可选元数据。",
            code=_LIST_CODE,
        ),
    ],
    api=[
        Api("src", "str | None", "None", "单个视频地址或本地路径"),
        Api(
            "playlist",
            "list[VideoMedia]",
            "[]",
            "多集播放列表；与 src 同时给时以它为准",
        ),
        Api("title", "str", "Video", "原生后端的窗口 / 进程名，不出现在画面上"),
        Api("autoplay", "bool", "False", "挂载后自动播放"),
        Api("loop", "bool", "False", "播完回到第一项（PlaylistMode.LOOP）"),
        Api("muted", "bool", "False", "静音起播；自动播放配它更稳"),
        Api("height", "float", "320", "播放器高度"),
        Api("border_radius", "int", "8", "圆角；配合 HARD_EDGE 裁切画面"),
        Api(
            "build_playlist(sources, **kwargs)",
            "list[VideoMedia]",
            "—",
            "把 1~N 个地址转成播放列表，kwargs 透传给 VideoMedia",
        ),
        Api(
            "VideoMedia",
            "fv.VideoMedia",
            "—",
            "媒体项：resource 加可选的 http_headers / extras",
        ),
    ],
    notes=[
        tip(
            "src 与 playlist 同时给时 playlist 优先，src 被静默忽略 —— 二选一，别两份都写，"
            "否则排查「为什么换了地址没反应」要花很久。"
        ),
        info(
            "title 不是画面上的标题，而是原生后端给子窗口 / 进程起的名字，作用相当于系统"
            "音量合成器里的标签；要在画面上写字，得自己在外层叠一个 Text。"
        ),
        warn(
            "没有 src 也没有 playlist 时播放器没有内建空态：一块没有控制条的黑底。"
            "占位提示（「还没有视频」之类）要由调用方在外面画。"
        ),
    ],
    tags=("视频", "video", "播放器", "播放列表", "player"),
)


if __name__ == "__main__":
    run(SPEC)
