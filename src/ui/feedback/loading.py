import flet as ft


_SIZE_MAP = {"small": 20, "normal": 32, "large": 48}


@ft.control
class Loading(ft.ProgressRing):
    pass
