import flet as ft


class ProgressBar(ft.ProgressBar):
    def __init__(self, progress: float = 0.0, **kwargs):
        v = min(progress / 100.0, 1.0) if progress > 1 else progress
        super().__init__(value=v, **kwargs)
