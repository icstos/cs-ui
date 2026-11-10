"""按钮 (Button) —— 主 / 次 / 文字三档强调，带图标与加载态。

三种变体共用同一套高度（36）与状态色，靠 ``style_type`` + ``plain`` 区分：

* 主按钮：主色实底 + 反白字，一屏只该有一个；
* 次按钮：``plain=True``，浅底 + 主色描边；
* 文字按钮：不传 ``style_type``（DEFAULT），没有可见边框。

用法::

    Button("保存", style_type=StyleType.PRIMARY)
    Button("取消", style_type=StyleType.PRIMARY, plain=True)
    Button("了解更多")
"""

from __future__ import annotations

import asyncio
from dataclasses import field

import flet as ft

from ui.core.constants import ButtonShape, StyleType
from ui.core.doc import Api, Example, Spec, info, run, tip, warn
from ui.core.tokens import (
    CONTROL_HEIGHT,
    FONT_SIZE,
    ICON_SIZE,
    RADIUS,
    STATE,
    disabled_layer,
    state_layer,
)
from ui.feedback._look import feedback_style

__all__ = ["Button"]

BORDER_RADIUS = RADIUS["md"]  # 6，与输入框一致
BUTTON_HEIGHT = CONTROL_HEIGHT["md"]  # 与输入框同高，一行表单里不会参差
#: 按钮内图标：比正文（14）大一档，与字排在一起时不会显得"缩"。
#: 不要再在模块里另开一个 ``ICON_SIZE`` —— 那会盖掉令牌名，让"图标该多大"
#: 又变成各处自说自话。
BTN_ICON_SIZE = ICON_SIZE["lg"]

#: 禁用态：统一用 on-surface 的两档透明度。写死 GREY_300 + 白字时，浅色主题下
#: 白字压在浅灰上几乎看不见；走角色透明度还能自动适配深色主题。
DISABLED_BG = disabled_layer("container")
DISABLED_FG = disabled_layer()
DISABLED_SIDE = disabled_layer("container")


def _merge_states(value, defaults: dict[ft.ControlState, str]):
    """把调用方显式指定的状态值叠加到默认状态表上。

    传单值时视作 DEFAULT/HOVERED/PRESSED 三态取同一个颜色（悬停反馈仍由
    overlay_color 提供），DISABLED 保留默认灰；传字典时逐键覆盖。
    这样调用方定制配色时不会因为预设色板被强制写回而出现「白底白字」。

    Args:
        value: 调用方给的状态值（None / 单值 / 状态字典）。
        defaults: 组件预设的状态表。

    Returns:
        合并后的状态表。
    """
    merged = dict(defaults)
    if value is None:
        return merged
    if isinstance(value, dict):
        merged.update(value)
        return merged
    merged[ft.ControlState.DEFAULT] = value
    merged[ft.ControlState.HOVERED] = value
    merged[ft.ControlState.PRESSED] = value
    return merged


@ft.control
class Button(ft.Button):
    # 注意（flet 1.0.0）：基类的 height 是 kw_only 字段；子类若用裸注解重新声明，
    # dataclasses 会把它换成 kw_only=False 的新 Field，而位置仍沿用基类顺序 ——
    # 结果是 height 抢到第 0 个位置参数，Button("文字") 会把文字塞进 height。
    # 因此重新声明继承字段时必须显式 kw_only=True。
    height: int = field(default=BUTTON_HEIGHT, kw_only=True)

    style_type: StyleType = StyleType.DEFAULT
    shape: ButtonShape = ButtonShape.ROUND
    plain: bool = False  # 中心是否镂空
    is_primary: bool = False

    def init(self):
        if self.is_primary:
            self.style_type = StyleType.PRIMARY
        # 四色一次解析好：实底 / 实底前景 / 表面上的文字 / 淡底。
        # 唯一来源是 ui.feedback._look —— 与 Message / Notification / AlertDialog
        # 共用同一套语义色，于是"成功"按钮和"成功"提示条是同一个绿。
        self._style = feedback_style(self.style_type)
        self.style = self.style or ft.ButtonStyle(
            padding=ft.Padding.all(10), alignment=ft.Alignment.CENTER
        )
        accent = self._style.text
        if self.style_type == StyleType.DEFAULT:
            # 文字按钮：无填充、无描边，只在悬停时浮一层面色（M3 悬停档 8%）。
            # 白底 + 白边在浅色页面上像纯文字，在深色页面上是一块白砖。
            # DEFAULT + plain 仍是文字按钮 —— 白色描边在页面里本来就看不见。
            self.style.color = self.style.color or {
                ft.ControlState.DEFAULT: ft.Colors.ON_SURFACE,
                ft.ControlState.DISABLED: DISABLED_FG,
            }
            self.style.overlay_color = self.style.overlay_color or {
                ft.ControlState.DEFAULT: state_layer("hover")
            }
        elif self.plain:
            # 镂空：表面底 + 强调色描边与文字（而不是纯白底）——
            # 深色主题下纯白按钮会亮得像一个错误。
            self.style.bgcolor = self.style.bgcolor or {
                ft.ControlState.DEFAULT: ft.Colors.SURFACE
            }
            # 水波用强调色 8%：白底上的白色水波等于没有反馈
            self.style.overlay_color = self.style.overlay_color or {
                ft.ControlState.DEFAULT: state_layer("hover", role=accent)
            }
            # 悬停只加一层极淡的底色，**不动描边**：描边换成更浅的一档
            # （GREEN_100 之类的淡彩）时，线会在鼠标下变虚，像"禁用"。
            self.style.side = self.style.side or {
                ft.ControlState.DEFAULT: ft.BorderSide(1, accent),
                ft.ControlState.DISABLED: ft.BorderSide(1, DISABLED_SIDE),
            }
            self.style.color = self.style.color or {
                ft.ControlState.DEFAULT: accent,
                ft.ControlState.DISABLED: DISABLED_FG,
            }
            self.style.elevation = self.style.elevation or {
                ft.ControlState.DEFAULT: 0,
                ft.ControlState.PRESSED: 0,
                ft.ControlState.HOVERED: 0,
            }
        else:
            # 实心：实底 + 反白（或深墨）字。
            #
            # 悬停**不换底色**，而是压一层前景色：M3 对实心控件的做法就是
            # "底色不动，叠 8% 的前景色"。换成深一档的同色系（BLUE → BLUE_800）
            # 时，两档的跳变在深色主题下看不出来，反倒把"按下"和"悬停"画成了
            # 同一个颜色。
            self.style.color = self.style.color or {
                ft.ControlState.DEFAULT: self._style.on,
                ft.ControlState.DISABLED: DISABLED_FG,
            }
            self.style.bgcolor = _merge_states(
                self.style.bgcolor,
                {
                    ft.ControlState.DEFAULT: self._style.fill,
                    ft.ControlState.DISABLED: DISABLED_BG,
                },
            )
            self.style.overlay_color = self.style.overlay_color or {
                ft.ControlState.DEFAULT: ft.Colors.with_opacity(
                    STATE["hover"], self._style.on
                ),
                ft.ControlState.PRESSED: ft.Colors.with_opacity(
                    STATE["pressed"], self._style.on
                ),
            }
            self.style.elevation = self.style.elevation or {
                ft.ControlState.DEFAULT: 0,
                ft.ControlState.PRESSED: 0,
                ft.ControlState.HOVERED: 0,
            }
            self.style.side = self.style.side or {
                ft.ControlState.DISABLED: ft.BorderSide(1, DISABLED_SIDE),
            }

        if self.style is not None and self.style.shape is None:
            if self.shape == ButtonShape.RECTANGLE:
                self.style.shape = ft.ContinuousRectangleBorder()
            elif self.shape == ButtonShape.ROUND:
                self.style.shape = ft.RoundedRectangleBorder(radius=BORDER_RADIUS)
            elif self.shape == ButtonShape.CIRCLE:
                self.style.shape = ft.StadiumBorder()


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
def _caption(text: str) -> ft.Control:
    return ft.Text(text, size=FONT_SIZE["small"], color=ft.Colors.ON_SURFACE_VARIANT)


@ft.component
def _variants() -> ft.Control:
    """三种强调级别 + 图标：主、次、文字排在一起才看得出层级。"""
    return ft.Column(
        spacing=18,
        controls=[
            ft.Row(
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    Button("保存", style_type=StyleType.PRIMARY),
                    Button("取消", style_type=StyleType.PRIMARY, plain=True),
                    Button("了解更多"),
                ],
            ),
            ft.Row(
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    Button("新增", icon=ft.Icons.ADD, style_type=StyleType.PRIMARY),
                    Button(
                        "导入",
                        icon=ft.Icons.UPLOAD_FILE,
                        style_type=StyleType.PRIMARY,
                        plain=True,
                    ),
                ],
            ),
            _caption("实底只有一个；描边用于并列的次要动作；文字按钮不抢任何注意力。"),
        ],
    )


@ft.component
def _icons_sizes() -> ft.Control:
    """尺寸与图标位：高度变了，内边距要跟着收放，否则文字会被压扁。"""
    return ft.Column(
        spacing=16,
        controls=[
            _caption("28 / 36 / 44 三档，内边距同步调整"),
            ft.Row(
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    Button(
                        "小",
                        height=28,
                        style=ft.ButtonStyle(
                            padding=ft.Padding.symmetric(horizontal=10, vertical=2)
                        ),
                    ),
                    Button("中", height=36),
                    Button(
                        "大",
                        height=44,
                        style=ft.ButtonStyle(
                            padding=ft.Padding.symmetric(horizontal=16, vertical=8)
                        ),
                    ),
                ],
            ),
            _caption("图标在左（flet 只提供前导图标）；纯图标按钮记得给 tooltip"),
            ft.Row(
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    Button(
                        content=ft.Icon(ft.Icons.REFRESH, size=BTN_ICON_SIZE),
                        width=36,
                        height=36,
                        tooltip="刷新",
                        style=ft.ButtonStyle(padding=ft.Padding.all(0)),
                    ),
                    Button(
                        "下一步",
                        icon=ft.Icons.ARROW_FORWARD,
                        style_type=StyleType.PRIMARY,
                    ),
                ],
            ),
        ],
    )


@ft.component
def _states() -> ft.Control:
    """禁用与加载：加载中保留主色、摘掉点击；禁用才是真的变灰。"""
    loading, set_loading = ft.use_state(False)

    async def save(_event) -> None:
        if loading:
            return
        set_loading(True)
        await asyncio.sleep(1.2)
        set_loading(False)

    spinner = ft.Row(
        tight=True,
        spacing=8,
        alignment=ft.MainAxisAlignment.CENTER,
        controls=[
            ft.ProgressRing(width=14, height=14, stroke_width=2, color=ft.Colors.WHITE),
            ft.Text("保存中", size=FONT_SIZE["body"], color=ft.Colors.WHITE),
        ],
    )

    return ft.Column(
        spacing=16,
        controls=[
            ft.Row(
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    Button(
                        content=spinner if loading else "保存",
                        style_type=StyleType.PRIMARY,
                        # 加载中直接摘掉回调：用 disabled 会把主色压成灰色，
                        # 看起来像「不可用」，而不是「正在处理」。
                        on_click=None if loading else save,
                    ),
                    Button("禁用主按钮", style_type=StyleType.PRIMARY, disabled=True),
                    Button("禁用文字按钮", disabled=True),
                ],
            ),
            _caption("点「保存」看加载态；右边两个是禁用态，颜色随主题自动变灰。"),
        ],
    )


_VARIANTS_CODE = """Button("保存", style_type=StyleType.PRIMARY)           # 主：实底
Button("取消", style_type=StyleType.PRIMARY, plain=True)   # 次：描边
Button("了解更多")                                         # 文字：无边框

Button("新增", icon=ft.Icons.ADD, style_type=StyleType.PRIMARY)"""


SPEC = Spec(
    name="Button",
    summary="触发一个动作：主、次、文字三档强调级别，可带图标与加载态。",
    definition=(
        "按钮是界面上最小的承诺：点下去就会发生一件事。它本身不承载状态，也不解释"
        "后果 —— 这件事有多重要，决定了它该用实底、描边还是纯文字。"
        "同一屏里实底按钮只该有一个，否则「主」就不成立了。"
    ),
    anatomy=[
        (
            "填充与描边",
            "主按钮是主色实底 + 反白字；次按钮是浅底 + 主色描边；文字按钮没有可见边框。",
        ),
        (
            "文字与图标",
            "图标只能放在左侧，flet 只提供前导图标；需要尾部箭头时用 content 自己拼一行。",
        ),
        ("高度", "默认 36，与输入框、下拉框同高；28 / 44 两档要同时收放内边距。"),
        (
            "状态",
            (
                "实心按钮悬停时**底色不动**，盖一层 8% 的前景色，按下 12% —— "
                "这是 M3 对实心控件的做法，也是唯一能同时保证「有反馈」与「字始终"
                "读得出来」的做法（换一档底色就会在某一档上把反差压到 3:1 以下）。"
                "禁用态用 on-surface 的 12% / 38% 两档透明度。"
            ),
        ),
        (
            "加载态",
            "转圈 + 「保存中」，期间不响应点击，但保留主色 —— 它是在处理，不是不可用。",
        ),
    ],
    when=[
        "提交表单、确认弹窗里的「确定 / 取消」",
        "工具栏上的单个动作：新增、刷新、导出",
        "空状态里引导用户完成第一步",
    ],
    avoid=[
        "页面跳转：用链接或列表项，按钮会让人以为要提交什么",
        "一屏并列五六个同等重要的操作：收进菜单，别让主次失效",
        "开关型状态：用 Switch / Checkbox，按钮说不清「现在是开还是关」",
    ],
    examples=[
        Example(
            "三种变体",
            _variants,
            hint="实底、描边、文字排在一起：主按钮只有一个，其余自觉退后。",
            code=_VARIANTS_CODE,
        ),
        Example(
            "图标与尺寸",
            _icons_sizes,
            hint="前导图标补语义；三档高度要连内边距一起改，否则文字会被裁。",
        ),
        Example(
            "禁用与加载",
            _states,
            hint="点「保存」看加载态：转圈期间摘掉 on_click，按钮仍是主色。",
        ),
    ],
    api=[
        Api("content", "str | Control | None", "None", "按钮内容：文字或自定义控件"),
        Api("icon", "IconData | Control | None", "None", "前导图标，显示在文字左侧"),
        Api("icon_color", "ColorValue | None", "None", "图标颜色，默认跟随文字颜色"),
        Api(
            "style_type",
            "StyleType",
            "StyleType.DEFAULT",
            "语义色板：DEFAULT / PRIMARY / SUCCESS …",
        ),
        Api("plain", "bool", "False", "次按钮：浅底 + 描边，中心镂空"),
        Api("is_primary", "bool", "False", "快捷开关，等价于 style_type=PRIMARY"),
        Api("shape", "ButtonShape", "ButtonShape.ROUND", "圆角 / 直角 / 胶囊三种外形"),
        Api("height", "int", "36", "按钮高度；与输入框同高，改小要同步收内边距"),
        Api(
            "style",
            "ButtonStyle | None",
            "None",
            "整体覆盖样式；只传 padding 时其余默认仍生效",
        ),
        Api(
            "on_click", "Callable | None", "None", "点击回调；加载中可传 None 暂时摘掉"
        ),
    ],
    notes=[
        tip(
            "height 是关键字参数。子类重声明继承字段时漏掉 kw_only=True，它会抢到"
            '第 0 个位置参数，Button("文字") 就把文字塞进高度里了。'
        ),
        info(
            "不传 style_type 得到的是文字按钮（DEFAULT）：没有可见边框，只靠文字"
            "与留白表达。plain=True 只对有色 style_type 有意义 —— 要描边请写成"
            "style_type=StyleType.PRIMARY, plain=True。"
        ),
        warn(
            "组件没有 loading 参数。别用 disabled 做加载态 —— 那会把主色压成灰色，"
            "用户读到的是「不可用」。正确做法是把 content 换成转圈并摘掉 on_click。"
        ),
    ],
    tags=("按钮", "button", "操作", "提交", "主按钮"),
)


if __name__ == "__main__":
    run(SPEC)
