from enum import Enum, unique
from dataclasses import dataclass
import flet as ft

DEFAULT_FORM_HEIGHT = 36


class RUN_MODE(Enum):
    DEV = 'dev'
    TEST = 'test'
    RELEASE = 'release'


class SizeType(Enum):
    XS = 'x_small'
    S = 'small'
    M = 'medium'
    L = 'large'
    XL = 'x_large'
    XXL = 'xx_large'
    XXXL = 'xxx_large'


class LayoutType(Enum):
    HORIZONTAL = 'horizontal'
    VERTICAL = 'vertical'


class FormValueType(Enum):
    INT = "int"
    FLOAT = "float"
    STR = "str"
    FILE = "file"
    DIR = "dir"
    BOOL = "bool"


@dataclass
class FeedbackStyle:
    icon: ft.IconData
    color: str
    color_light: str
    color_accent: str


class ButtonShape(Enum):
    CIRCLE = 'circle'
    RECTANGLE = 'rectangle'
    ROUND = 'round'


@unique
class StyleType(Enum):
    DEFAULT = (ft.Icons.MESSAGE, ft.Colors.WHITE, ft.Colors.WHITE, ft.Colors.GREY_100)
    PRIMARY = (
        ft.Icons.MESSAGE,
        ft.Colors.BLUE,
        ft.Colors.BLUE_100,
        ft.Colors.BLUE_800,
    )
    INFO = (
        ft.Icons.INFO,
        ft.Colors.LIGHT_BLUE,
        ft.Colors.LIGHT_BLUE_100,
        ft.Colors.LIGHT_BLUE_800,
    )
    SUCCESS = (ft.Icons.DONE, ft.Colors.GREEN, ft.Colors.GREEN_100, ft.Colors.GREEN_800)
    WARNING = (
        ft.Icons.WARNING_ROUNDED,
        ft.Colors.YELLOW_600,
        ft.Colors.YELLOW_100,
        ft.Colors.YELLOW_900,
    )
    ERROR = (ft.Icons.CLOSE, ft.Colors.RED, ft.Colors.RED_100, ft.Colors.RED_800)
