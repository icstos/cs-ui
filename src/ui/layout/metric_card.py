"""指标卡 (MetricCard) —— 一个数字 + 它是什么 + 一个语义色图标。

为什么不是"Card 里塞几个 Text"
-----------------------------
仪表盘上一排指标卡，最容易出的问题不是不好看，而是**不齐**：
数值字号 24 / 26 / 28 各写一遍，图标块 28×28 与 30×30 并存，指标名有的 12
有的 13 —— 单看每张都行，排成一行就露馅。MetricCard 把这五件事固定死：

============  ==========================================================
图标块        30×30、RADIUS.md、``accent_soft`` 底 + ``accent_text`` 图标
数值          ``headline_lg``（24）+ bold —— 卡片里唯一的巨字
指标名        ``small``（12）+ ``ON_SURFACE_VARIANT``：可读但不抢数值
右上角提示    可选，``caption``（11）+ 语义色 —— 环比、占比、单位
卡片          16px 内边距 + 8px 圆角 + 1px 描边 + 一层极淡投影
============  ==========================================================

为什么三行而不是两行
--------------------
数值与指标名同行的写法（"24 个 / 项目"）在中文里宽度不可控：指标名一长就换行、
一换行两张卡的高度就对不上。竖排后三行各自一行，**任何文字长度下卡片高度都一致**。

用法::

    MetricCard(label="提交数", value="1,286", role="primary", icon=ft.Icons.COMMIT)
    MetricCard(label="净增行", value="+8,420", role="info", hint="较上周 +12%")
    ResponsiveRow([MetricCard(..., col={"xs": 6, "md": 3}) for ...])
"""

from __future__ import annotations

import flet as ft

from ui.core.doc import Api, Example, Spec, info, run, tip, warn
from ui.core.tokens import (
    FONT_SIZE,
    FONT_WEIGHT,
    ICON_SIZE,
    RADIUS,
    SPACE,
    accent_soft,
    accent_text,
    elevation,
)

__all__ = ["MetricCard"]

#: 图标块的边长。与 ``FONT_SIZE["display"]`` 不是一回事：它是个"印章"，
#: 小于 28 会显得飘，大于 32 会压过数值。
CHIP = 30

#: 可用语气（与 :class:`~ui.display.tag.Tag` 同一套角色名）
ROLES: tuple[str, ...] = (
    "primary",
    "secondary",
    "tertiary",
    "success",
    "warning",
    "danger",
    "info",
    "neutral",
)


@ft.control
class MetricCard(ft.Container):
    """一张指标卡。

    Args:
        label: 指标名（"提交数"、"活跃项目"）。
        value: 数值或已格式化的字符串（``"1,286"``、``"+8,420"``、``"12 %"``）。
            组件不做格式化 —— 千分位、正负号、单位都是业务口径。
        role: 语义语气，决定图标块的色相；未知值退回 ``primary``。
        icon: 图标。留空时按语气取默认图标（见 :data:`DEFAULT_ICONS`）。
        hint: 右上角的一行小字（环比、单位、"近 30 天"）。留空则不占位。
    """

    label: str = ""
    value: str = ""
    role: str = "primary"
    icon: ft.IconData | None = None
    hint: str = ""

    def init(self):
        role = self.role if self.role in ROLES else "primary"
        icon = self.icon if self.icon is not None else DEFAULT_ICONS.get(role)
        accent = accent_text(role)

        self.padding = SPACE["4"]
        self.border_radius = RADIUS["lg"]
        self.bgcolor = ft.Colors.SURFACE_CONTAINER_LOWEST
        self.border = ft.Border.all(1, ft.Colors.OUTLINE_VARIANT)
        # 一层极淡的投影：卡片"浮"在页面底上，但不到"卡片有立体感"的程度。
        self.shadow = elevation(1)

        head: list[ft.Control] = [
            ft.Container(
                width=CHIP,
                height=CHIP,
                border_radius=RADIUS["md"],
                bgcolor=accent_soft(role),
                alignment=ft.Alignment.CENTER,
                content=ft.Icon(icon, size=ICON_SIZE["md"], color=accent),
            )
        ]
        if self.hint:
            head.extend(
                [
                    ft.Container(expand=True),
                    ft.Text(
                        self.hint,
                        size=FONT_SIZE["caption"],
                        weight=FONT_WEIGHT["medium"],
                        color=accent,
                        no_wrap=True,
                    ),
                ]
            )

        self.content = ft.Column(
            spacing=SPACE["1"],
            tight=True,
            controls=[
                ft.Row(
                    spacing=SPACE["2"],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=head,
                ),
                ft.Text(
                    self.value,
                    size=FONT_SIZE["headline_lg"],
                    weight=FONT_WEIGHT["bold"],
                    color=ft.Colors.ON_SURFACE,
                    no_wrap=True,
                    style=ft.TextStyle(height=1.2),
                ),
                ft.Text(
                    self.label,
                    size=FONT_SIZE["small"],
                    color=ft.Colors.ON_SURFACE_VARIANT,
                    no_wrap=True,
                ),
            ],
        )


#: 没传 icon 时按语气取的默认图标 —— 让"忘了给图标"也落在同一套语义上。
DEFAULT_ICONS: dict[str, ft.IconData] = {
    "primary": ft.Icons.INSIGHTS,
    "secondary": ft.Icons.LABEL_OUTLINE,
    "tertiary": ft.Icons.EXTENSION,
    "success": ft.Icons.CHECK_CIRCLE_OUTLINE,
    "warning": ft.Icons.WARNING_AMBER_ROUNDED,
    "danger": ft.Icons.ERROR_OUTLINE,
    "info": ft.Icons.INFO_OUTLINE,
    "neutral": ft.Icons.CIRCLE_OUTLINED,
}


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
@ft.component
def _row() -> ft.Control:
    """一排四张：图标块的色相是唯一的变量，其余完全对齐。"""
    return ft.ResponsiveRow(
        spacing=SPACE["4"],
        run_spacing=SPACE["4"],
        controls=[
            MetricCard(
                label="提交数",
                value="1,286",
                role="primary",
                icon=ft.Icons.COMMIT,
                col={"xs": 6, "md": 3},
            ),
            MetricCard(
                label="新增行",
                value="+24,830",
                role="success",
                icon=ft.Icons.ADD,
                col={"xs": 6, "md": 3},
            ),
            MetricCard(
                label="删除行",
                value="-9,214",
                role="danger",
                icon=ft.Icons.REMOVE,
                col={"xs": 6, "md": 3},
            ),
            MetricCard(label="活跃项目", value="8", role="neutral", col={"xs": 6, "md": 3}),
        ],
    )


@ft.component
def _with_hint() -> ft.Control:
    """带环比提示：小字只上色、不加图标，避免和数值抢注意力。"""
    return ft.Row(
        spacing=SPACE["4"],
        controls=[
            MetricCard(label="本周提交", value="142", role="info", hint="较上周 +12%"),
            MetricCard(label="平均耗时", value="3.4 s", role="warning", hint="近 30 天"),
        ],
    )


SPEC = Spec(
    name="MetricCard",
    summary="一个数字 + 它是什么 + 一个语义色图标，用于仪表盘首屏。",
    definition=(
        "指标卡把「数值」提到最高层级，再用一行小字说明这个数值是什么。"
        "它解决的不是「画一张卡」，而是「一排卡对齐」：数值字号、图标块尺寸、"
        "指标名的颜色与行距，只要有一处各写各的，整排卡就会高低参差。"
        "组件把这些固定死，只留数值、语气、图标、提示四个变量。"
    ),
    anatomy=[
        ("图标块", "30×30 + RADIUS.md + accent_soft 底；图标用 accent_text 同色。"),
        ("数值", "headline_lg（24）+ bold，卡片里唯一的巨字，永远 on-surface。"),
        ("指标名", "small（12）+ on-surface-variant：读得清但排在数值之下。"),
        ("提示", "可选，caption（11）+ 语义色，贴在右上角与图标块同一行。"),
        ("卡片", "16px 内边距、8px 圆角、1px 描边、elevation(1) 极淡投影。"),
    ],
    when=[
        "仪表盘 / 首页顶部的一排关键数字",
        "统计页的汇总区（提交数、增删行、活跃项目）",
        "详情页里三个以内的关键口径，需要并排比较",
    ],
    avoid=[
        "需要两行以上说明的内容：那是普通 Card，不是指标",
        "数字需要实时跳动的场景：配 NumberAnimation 使用，别在卡里自己写定时器",
        "一屏超过六张：读不过来，改用表格或分区",
    ],
    examples=[
        Example("一排四张", _row, hint="ResponsiveRow + col：窄屏两张一行，宽屏四张一行。"),
        Example("带提示", _with_hint, hint="hint 只在需要解释数值口径时才给。"),
    ],
    target=MetricCard,
    api=[
        Api("label", "str", "''", "指标名，显示在数值下方"),
        Api("value", "str", "''", "数值或已格式化的字符串；组件不做千分位/单位处理"),
        Api("role", "str", "'primary'", "语气：primary/secondary/tertiary/success/warning/danger/info/neutral"),
        Api("icon", "ft.IconData | None", "None", "图标；留空按 role 取 DEFAULT_ICONS"),
        Api("hint", "str", "''", "右上角小字（环比、单位、时间范围），留空不占位"),
        Api("col", "int | dict | None", "None", "Container 自带字段：在 ResponsiveRow 里的列宽"),
    ],
    notes=[
        info(
            "数值不做格式化：千分位、正负号、单位都是业务口径，框架猜一次就会错一次。"
            "需要时先用 core.format 的 format_number 处理好再传进来。"
        ),
        tip("同一排卡片的 role 不要超过三种：颜色一多，读者会以为颜色本身有含义。"),
        warn(
            "字段一律用关键字传（``label=`` / ``value=``）。flet 控件的位置参数会落到"
            "基类字段上（content / key），组件自己的字段仍是默认值 —— 结果是"
            "**一张空白卡，而且不报错**。"
        ),
    ],
    tags=("指标卡", "统计", "KPI", "dashboard", "metric", "卡片"),
)


if __name__ == "__main__":
    run(SPEC)
