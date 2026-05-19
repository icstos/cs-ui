import flet as ft
from typing import Any


class BaseControl(ft.BaseControl):
    """
    自定义控件的基类，提供统一的 build 辅助方法
    """
    
    def _build_control(self, control: Any) -> Any:
        """
        递归构建控件，处理自定义控件和原生 Flet 控件
        """
        if hasattr(control, 'build') and callable(control.build):
            return control.build()
        return control

    def _build_controls(self, controls: list) -> list:
        """
        批量构建控件列表
        """
        return [self._build_control(control) for control in controls]
