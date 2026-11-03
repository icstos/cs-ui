"""媒体组件：音频、视频与 PDF。"""

from __future__ import annotations

import flet as ft

from docs import kit
from docs.blocks import Doc, demo, h2, note, p, ul
from ui import Audio, AudioPlayer, Pdf, Video, build_playlist, use_t

_SAMPLE_AUDIO = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
_SAMPLE_VIDEO = "https://flutter.github.io/assets-for-api-docs/assets/videos/bee.mp4"
_SAMPLE_VIDEO_2 = (
    "https://flutter.github.io/assets-for-api-docs/assets/videos/butterfly.mp4"
)
_SAMPLE_PDF = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"

_AUDIO_CODE = '''player = AudioPlayer(src="song.mp3", title="Night Drive")
# Audio 自身是 Service：构造即注册，不要塞进控件树
service = Audio(src="song.mp3")'''

_PDF_CODE = '''Pdf(src="manual.pdf", title="Manual", height=460)'''


@ft.component
def _audio() -> ft.Control:
    tr = use_t()
    kit.use_stable(lambda: Audio(src=_SAMPLE_AUDIO))
    return ft.Column(
        spacing=12,
        controls=[
            AudioPlayer(
                src=_SAMPLE_AUDIO,
                title=tr("cat.media.audio.track"),
                subtitle=tr("cat.media.audio.artist"),
            ),
            AudioPlayer(src=_SAMPLE_AUDIO, title=tr("cat.media.audio.track2")),
        ],
    )


@ft.component
def _video() -> ft.Control:
    tr = use_t()
    return ft.Column(
        spacing=14,
        controls=[
            Video(src=_SAMPLE_VIDEO, title="bee.mp4", height=260),
            Video(
                playlist=build_playlist([_SAMPLE_VIDEO, _SAMPLE_VIDEO_2]),
                title=tr("cat.media.video.playlist"),
                height=260,
            ),
        ],
    )


@ft.component
def _pdf() -> ft.Control:
    tr = use_t()
    return Pdf(src=_SAMPLE_PDF, title=tr("cat.media.pdf.doc"), height=440)


MEDIA: Doc = (
    p("cat.media.intro"),
    h2("cat.media.audio.title"),
    demo(_audio, hint_key="cat.media.audio.hint", code=_AUDIO_CODE),
    h2("cat.media.video.title"),
    demo(_video, hint_key="cat.media.video.hint", padded=False),
    h2("cat.media.pdf.title"),
    demo(_pdf, hint_key="cat.media.pdf.hint", code=_PDF_CODE, padded=False),
    ul("cat.media.note1", "cat.media.note2"),
    note("cat.media.tip", "cat.media.tip_title"),
)
