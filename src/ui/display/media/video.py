"""视频播放器 (Video)。

对 ``flet_video.Video`` 的轻量封装：把单条 URL / 本地路径规范化成
``playlist=[VideoMedia(...)]``，并提供统一的圆角与尺寸默认值。

依赖：``flet-video``
"""

from __future__ import annotations

from dataclasses import field

import flet as ft
import flet_video as fv

__all__ = ["Video", "VideoMedia", "build_playlist"]

VideoMedia = fv.VideoMedia


def build_playlist(
    sources: str | list[str], **kwargs
) -> list[fv.VideoMedia]:
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
        playlist: 多集播放列表（与 ``src`` 二选一）。
        title: 播放器标题。
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
    height: int | float = field(default=320, kw_only=True)
    border_radius: int = field(default=8, kw_only=True)

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


@ft.component
def App():
    """Video 组件运行示例。"""
    bee = "https://flutter.github.io/assets-for-api-docs/assets/videos/bee.mp4"
    butterfly = (
        "https://flutter.github.io/assets-for-api-docs/assets/videos/butterfly.mp4"
    )
    return ft.Column(
        controls=[
            ft.Text("Video 视频播放器", size=20, weight=ft.FontWeight.BOLD),
            ft.Text("基于 flet-video，支持单源与播放列表", size=13, color="#6b7280"),
            ft.Divider(),
            ft.Text("1. 单视频源", size=14, weight=ft.FontWeight.W_600),
            Video(src=bee, title="bee.mp4", height=260),
            ft.Divider(),
            ft.Text("2. 播放列表", size=14, weight=ft.FontWeight.W_600),
            Video(
                playlist=build_playlist([bee, butterfly]),
                title="示例播放列表",
                height=260,
                autoplay=False,
            ),
        ]
    )


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
