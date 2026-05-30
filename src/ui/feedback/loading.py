import flet as ft


_SIZE_MAP = {"small": 20, "normal": 32, "large": 48}


@ft.control
class Loading(ft.ProgressRing):
    size_name: str = "normal"

    def init(self):
        size_value = _SIZE_MAP.get(self.size_name, 32)
        self.width = size_value
        self.height = size_value
        self.stroke_width = max(2, size_value / 10)
