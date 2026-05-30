import flet as ft


@ft.control
class ProgressBar(ft.ProgressBar):
    progress: int | float | None = None
    color: str | None = None

    def init(self):
        if self.progress is not None:
            # 兼容百分比 (0-100) 和小数 (0.0-1.0) 两种模式
            if isinstance(self.progress, int) and self.progress > 1:
                self.value = self.progress / 100.0
            else:
                self.value = float(self.progress)
        if self.color is not None:
            self.bgcolor = ft.Colors.with_opacity(0.15, ft.Colors.GREY_700)
            self.color = ft.Colors.with_opacity(0.85, self.color)
