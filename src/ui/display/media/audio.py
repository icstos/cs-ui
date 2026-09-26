"""音频播放器 (Audio)。

对 ``flet_audio.Audio`` 的轻量封装，并提供一个卡片式播放器
:class:`AudioPlayer`（播放/暂停 + 音量 + 状态显示）。

依赖：``flet-audio``
"""

from __future__ import annotations

import flet as ft
import flet_audio as fa

__all__ = ["Audio", "AudioPlayer"]


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


class AudioPlayer(ft.Container):
    """卡片式音频播放器。

    Args:
        src: 音频地址。
        title: 标题文本。
        subtitle: 次要说明文本。
        width: 卡片宽度，默认撑满容器。
    """

    def __init__(
        self,
        src: str = "",
        title: str = "音频",
        subtitle: str = "",
        width: int | float | None = None,
        **kwargs,
    ) -> None:
        super().__init__(width=width, **kwargs)
        self._playing = False

        self._audio = Audio(src=src, on_state_change=self._on_state_change)
        self._status = ft.Text("未播放", size=12, color=ft.Colors.ON_SURFACE_VARIANT)
        self._play_btn = ft.IconButton(
            icon=ft.Icons.PLAY_CIRCLE_FILLED,
            icon_size=34,
            icon_color=ft.Colors.BLUE,
            tooltip="播放 / 暂停",
            on_click=self._toggle,
        )
        self._volume = ft.Slider(
            min=0,
            max=1,
            divisions=10,
            value=float(self._audio.volume),
            label="{value}",
            width=140,
            on_change=self._on_volume_change,
        )

        info = ft.Column(
            controls=[
                ft.Text(title, size=14, weight=ft.FontWeight.W_600),
                self._status,
                *(
                    [
                        ft.Text(
                            subtitle,
                            size=12,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        )
                    ]
                    if subtitle
                    else []
                ),
            ],
            spacing=2,
            expand=True,
        )

        # 注意（flet 1.0.0）：Audio 继承自 ft.Service 而不是 ft.Control，
        # 放进控件树会被 Flutter 判为 "Unknown control: Audio"。
        # Service 在构造时就会自行注册到 page 的服务注册表，因此这里只需
        # 用 self._audio 持有强引用（注册表按引用计数清理），不再挂进树里。
        self.content = ft.Row(
            controls=[self._play_btn, info, self._volume],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self.border = ft.Border.all(1, ft.Colors.OUTLINE_VARIANT)
        self.border_radius = ft.BorderRadius.all(8)
        self.padding = 12

    # ------------------------------------------------------------------
    # 事件处理
    # ------------------------------------------------------------------

    def _toggle(self, e: ft.ControlEvent) -> None:
        """播放 / 暂停。"""
        self._playing = not self._playing
        if self._playing:
            e.page.run_task(self._audio.play)
        else:
            e.page.run_task(self._audio.pause)
        self._sync_ui()

    def _on_state_change(self, e: fa.AudioStateChangeEvent) -> None:
        """跟随播放状态同步 UI（含播放结束）。"""
        playing = str(e.state) == fa.AudioState.PLAYING.value
        if playing != self._playing:
            self._playing = playing
            self._sync_ui()

    def _on_volume_change(self, e: ft.ControlEvent) -> None:
        """调整音量。"""
        self._audio.volume = float(e.control.value)
        self._audio.update()

    def _sync_ui(self) -> None:
        """刷新按钮图标与状态文本。"""
        self._play_btn.icon = (
            ft.Icons.PAUSE_CIRCLE_FILLED if self._playing else ft.Icons.PLAY_CIRCLE_FILLED
        )
        self._status.value = "播放中" if self._playing else "已暂停"
        self.update()


@ft.component
def App():
    """Audio 组件运行示例。"""
    src = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
    # Audio 是 ft.Service：构造即注册到 page，不要放进 controls
    audio = Audio(src=src)
    return ft.Column(
        controls=[
            ft.Text("Audio 音频播放器", size=20, weight=ft.FontWeight.BOLD),
            ft.Text("基于 flet-audio，提供播放/暂停与音量控制", size=13, color="#6b7280"),
            ft.Divider(),
            ft.Text(
                f"Audio 服务已注册 · src={audio.src}",
                size=12,
                color="#6b7280",
            ),
            ft.Divider(),
            AudioPlayer(src=src, title="示例音轨", subtitle="SoundHelix Song 1"),
        ]
    )


if __name__ == "__main__":
    ft.run(lambda page: page.render(App))
