"""音视频与 PDF 演示。"""

from __future__ import annotations

import flet as ft

from docs.demos._helpers import (
    MUTED,
    SAMPLE_AUDIO,
    SAMPLE_PDF,
    SAMPLE_VIDEO,
    SAMPLE_VIDEO_2,
    panel,
    use_stable,
)
from docs.kit import cell, demo_card, demo_grid, doc_page
from ui import (
    Audio,
    AudioPlayer,
    Pdf,
    Video,
    build_playlist,
    use_t,
)


@ft.component
def media_page() -> ft.Control:
    tr = use_t()

    # Audio 在 flet 1.x 中是 Service：构造即注册，不要塞进控件树。
    audio_service = use_stable(lambda: Audio(src=SAMPLE_AUDIO))

    audio = demo_card(
        title=tr("media.audio.title"),
        hint=tr("media.audio.hint"),
        icon=ft.Icons.GRAPHIC_EQ,
        stretch=True,
        body=[
            panel(
                ft.Row(
                    spacing=8,
                    controls=[
                        ft.Icon(ft.Icons.CHECK_CIRCLE, size=16, color=ft.Colors.PRIMARY),
                        ft.Text(
                            tr("media.audio.registered", src=audio_service.src),
                            size=12,
                            color=MUTED,
                        ),
                    ],
                )
            ),
            AudioPlayer(
                src=SAMPLE_AUDIO,
                title=tr("media.audio.track_title"),
                subtitle=tr("media.audio.track_subtitle"),
            ),
        ],
    )

    video = demo_card(
        title=tr("media.video.title"),
        hint=tr("media.video.hint"),
        icon=ft.Icons.VIDEO_LIBRARY_OUTLINED,
        stretch=True,
        body=[
            Video(src=SAMPLE_VIDEO, title="bee.mp4", height=260),
            Video(
                playlist=build_playlist([SAMPLE_VIDEO, SAMPLE_VIDEO_2]),
                title=tr("media.video.playlist"),
                height=260,
            ),
        ],
    )

    pdf = demo_card(
        title=tr("media.pdf.title"),
        hint=tr("media.pdf.hint"),
        icon=ft.Icons.PICTURE_AS_PDF,
        stretch=True,
        body=[Pdf(src=SAMPLE_PDF, title=tr("media.pdf.doc"), height=460)],
    )

    return doc_page(
        "media",
        [
            demo_grid(
                cell(audio, span=12),
                cell(video, span=12),
                cell(pdf, span=12),
            )
        ],
    )
