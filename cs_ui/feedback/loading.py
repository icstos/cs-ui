import flet as ft


_SIZE_MAP = {"small": 20, "normal": 32, "large": 48}


class Loading(ft.ProgressRing):
    def __init__(self, color: str = "#1f6feb", size_name: str = "normal", **kwargs):
        s = _SIZE_MAP.get(size_name, 32)
        super().__init__(color=color, width=s, height=s, stroke_width=4, **kwargs)
