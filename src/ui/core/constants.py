from dataclasses import dataclass
from enum import Enum, unique

import flet as ft

from ui.core.tokens import CONTROL_HEIGHT

#: 表单控件（输入框 / 下拉 / 按钮）的统一高度。只有 tokens 一个来源：
#: 在 core 与组件里各写一遍 ``= 36``，改一处就漂一格。
DEFAULT_FORM_HEIGHT = CONTROL_HEIGHT["md"]


class RUN_MODE(Enum):
    DEV = "dev"
    TEST = "test"
    RELEASE = "release"


class SizeType(Enum):
    XS = "x_small"
    S = "small"
    M = "medium"
    L = "large"
    XL = "x_large"
    XXL = "xx_large"
    XXXL = "xxx_large"


class LayoutType(Enum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


class FormValueType(Enum):
    INT = "int"
    FLOAT = "float"
    STR = "str"
    FILE = "file"
    DIR = "dir"
    BOOL = "bool"


@dataclass(frozen=True)
class FeedbackStyle:
    """一个 :class:`StyleType` 解析后的整套视觉。

    四个色字段对应 :mod:`ui.core.tokens` 的「强调角色四联」
    （``accent_fill`` / ``accent_on`` / ``accent_text`` / ``accent_soft``），
    含义见那里的说明。

    **唯一的构造方是** :func:`ui.feedback._look.feedback_style` ——
    组件不要自己填这几个字段，否则又回到"每处各配一套色"的老路。
    字段里直接放 ``ft.Colors.GREEN`` / ``YELLOW_600`` 这类**不随主题变**的静态
    色板同样不行：同一个"成功"在消息条里是一个绿、在按钮里是另一个绿，深色主题
    下按钮的浅色描边还会亮得像贴了块白纸。
    """

    icon: ft.IconData
    role: str  # "primary" / "success" / …，可回传给 accent_* 系列再取色
    #: 下面四个是 ``ft.ColorValue`` 而不是 ``str``：``primary`` 这类角色拿到的是
    #: ``ft.Colors`` 枚举成员，语义角色拿到的是 ``"#RRGGBB"`` 字符串。flet 两者
    #: 都认，但把类型写窄成 ``str`` 会让人误以为"这里一定是十六进制"。
    fill: ft.ColorValue  # 实底
    on: ft.ColorValue  # 实底上的前景
    text: ft.ColorValue  # 压在表面色上的文字 / 图标
    soft: ft.ColorValue  # 12% 淡底


class ButtonShape(Enum):
    CIRCLE = "circle"
    RECTANGLE = "rectangle"
    ROUND = "round"


@unique
class StyleType(Enum):
    """视觉类型的**名字**。

    只回答"这是哪一类提示"，不携带任何色值或图标 —— 色值由
    :mod:`ui.core.tokens` 的语义角色决定，图标由 :mod:`ui.feedback._look` 决定。
    把颜色塞进枚举的代价是**它只能是死色**：枚举在 import 时就固化了，而主题
    可以在运行时切换（见 :mod:`ui.core.theme` 里那条"字典在 import 时就固化"
    的教训）。
    """

    DEFAULT = "default"
    PRIMARY = "primary"
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
