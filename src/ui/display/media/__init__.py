"""媒体组件：音频。

门面惰性（见 :mod:`ui._lazy`）：后端是 ``flet_audio``，只有真正用到 ``Audio`` /
``AudioPlayer`` 时才加载，``import ui`` 不为它付代价。

**框架不提供视频**。视频播放器要接管时间轴、音量、全屏与播放列表状态，本质上
是一个应用而不是一个控件：放进通用组件库，等于替所有使用者选定一套交互，并让
每个装 cs-ui 的人都背上 ``flet-video``。需要播放器的项目自行封装 —— 参考
cs-video-player 的 ``components/media``（原生门面 + 无状态控制件 + 可复算色表）。
"""

from ui._lazy import lazy_exports

lazy_exports(
    globals(),
    {
        "Audio": ".audio",
        "AudioPlayer": ".audio",
    },
    __name__,
)
