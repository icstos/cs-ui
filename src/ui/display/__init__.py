"""展示类组件：文本、图片、媒体、日志、图表容器等。

门面惰性（见 :mod:`ui._lazy`）：``Text`` 与 ``Video`` 在同一层，但拿到 ``Text``
不该付出 ``flet_video`` / ``flet_audio`` 的加载代价。
"""

from ui._lazy import lazy_exports

lazy_exports(
    globals(),
    {
        "Audio": ".media.audio",
        "AudioPlayer": ".media.audio",
        "Pdf": ".media.pdf",
        "Video": ".media.video",
        "VideoMedia": ".media.video",
        "build_playlist": ".media.video",
        "Calendar": ".calendar",
        "Carousel": ".carousel",
        "Descriptions": ".descriptions",
        "DescriptionsItem": ".descriptions",
        "Heatmap": ".heatmap",
        "HeatmapItem": ".heatmap",
        "Image": ".image",
        "ImageGridView": ".image_gridview",
        "ListTile": ".list_tile",
        "LogContainer": ".log_container",
        "NumberAnimation": ".number_animation",
        "Code": ".text",
        "Header_1": ".text",
        "Header_2": ".text",
        "Header_3": ".text",
        "Header_4": ".text",
        "Header_5": ".text",
        "Json": ".text",
        "Link": ".text",
        "Markdown": ".text",
        "Quote": ".text",
        "SubTitle": ".text",
        "Text": ".text",
        "Title": ".text",
        "Tree": ".tree",
        "TreeNode": ".tree",
    },
    __name__,
)
