"""2
Container:

"""

import flet as ft


@ft.control
class Container(ft.InteractiveViewer):
    pan_enabled: bool = False
    scale_enabled: bool = False
