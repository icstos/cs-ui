import flet as ft

from cs_ui.core import BaseControl


@ft.control("Loading")
class Loading(BaseControl):
    def __init__(self, text="加载中...", color="#1f6feb", size="normal"):
        super().__init__()
        self.text = text
        self.color = color
        self.size = size

    def build(self):
        size_map = {
            "small": 20,
            "normal": 32,
            "large": 48,
        }
        
        return ft.ProgressRing(
            color=self.color,
            stroke_width=4,
            width=size_map.get(self.size, 32),
            height=size_map.get(self.size, 32),
        )