"""媒体组件：音频、视频、PDF 阅读器。

门面惰性（见 :mod:`ui._lazy`）：三者的后端各自独立（``flet_audio`` /
``flet_video`` / PDF.js），用哪个付哪个的代价，别一次全付。
"""

from ui._lazy import lazy_exports

lazy_exports(
    globals(),
    {
        "Audio": ".audio",
        "AudioPlayer": ".audio",
        "Pdf": ".pdf",
        "pdf_url": ".pdf",
        "Video": ".video",
        "VideoMedia": ".video",
        "build_playlist": ".video",
    },
    __name__,
)
