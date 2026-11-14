"""展示类组件：文本、图片、日志、图表容器等。

门面惰性（见 :mod:`ui._lazy`）：本层组件众多，全部按访问时导入，
``import ui`` 不为其中任何一个付代价。

**本层不含媒体播放**：音频 / 视频要接管时间轴、设备与播放列表状态，本质上是
应用而不是控件。cs-ui 只提供界面构件，播放引擎由应用自己封装（参考
``cs-music-player`` 的 ``infra/audio``）。
"""

from ui._lazy import lazy_exports

lazy_exports(
    globals(),
    {
        "Calendar": ".calendar",
        "Carousel": ".carousel",
        "Descriptions": ".descriptions",
        "DescriptionsItem": ".descriptions",
        "Heatmap": ".heatmap",
        "HeatmapItem": ".heatmap",
        "Image": ".image",
        "Kbd": ".kbd",
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
        "Tag": ".tag",
    },
    __name__,
)
