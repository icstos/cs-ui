"""媒体组件：音频、视频。

门面惰性（见 :mod:`ui._lazy`）：两者的后端各自独立（``flet_audio`` /
``flet_video``），用哪个付哪个的代价，别一次全付。
"""

from ui._lazy import lazy_exports

lazy_exports(
    globals(),
    {
        "Audio": ".audio",
        "AudioPlayer": ".audio",
        "Video": ".video",
        "VideoMedia": ".video",
        "build_playlist": ".video",
        # 自定义控制栏套件（配色可复算、控制件无状态）
        "BAR_PADDING": ".player",
        "IconAction": ".player",
        "MaterialDesktopVideoControls": ".player",
        "MediaPalette": ".player",
        "NativeSlider": ".player",
        "NativeVideo": ".player",
        "PlaylistMode": ".player",
        "SpeedMenu": ".player",
        "TimeSlider": ".player",
        "VideoControlsMode": ".player",
        "VOLUME_SLIDER_WIDTH": ".player",
        "VolumeControl": ".player",
        "desktop_controls": ".player",
        "format_rate": ".player",
        "format_time": ".player",
    },
    __name__,
)
