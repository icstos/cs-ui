"""长列表 (ListView) —— 一列可滚动的项，按视口按需构建。

ListView 和 Column 的差别不在长相，而在**构建方式**：Column 一次性把全部子项
放进控件树，ListView 只构建视口附近的那几项，所以 200 行和 2000 行一样跟手。
代价是它必须先知道自己有多高 —— 放进无界高度的父级（比如默认的 Column）会
渲染不出来，得给 height、expand，或让父级先有界。

用法::

    ListView(
        height=320,                     # 有界高度，滚动才有参照
        divider_thickness=1,
        padding=Padding.symmetric(horizontal=12, vertical=8),
        controls=[ListTile(...), ...],
    )
"""

from __future__ import annotations

import flet as ft

from ui.core.doc import Api, Example, Spec, info, run, tip, warn
from ui.core.tokens import FONT_SIZE, SPACE

__all__ = ["ListView"]

_MUTED = ft.Colors.ON_SURFACE_VARIANT


@ft.control
class ListView(ft.ListView):
    """可滚动的一列；长列表默认按需构建，滚到哪儿建到哪儿。

    默认把 ``clip_behavior`` 从 flet 的 ``HARD_EDGE`` 改成 ``ANTI_ALIAS``：列表项
    多为圆角卡片，滚到视口边缘时硬边裁剪会留下锯齿。
    """

    clip_behavior: ft.ClipBehavior = ft.ClipBehavior.ANTI_ALIAS


# ---------------------------------------------------------------------------
# 示例零件
# ---------------------------------------------------------------------------
def _caption(text: str) -> ft.Control:
    return ft.Text(text, size=FONT_SIZE["small"], color=_MUTED)


def _avatar(initial: str) -> ft.Control:
    return ft.CircleAvatar(
        radius=16,
        bgcolor=ft.Colors.SECONDARY_CONTAINER,
        content=ft.Text(
            initial,
            size=FONT_SIZE["body"],
            color=ft.Colors.ON_SECONDARY_CONTAINER,
        ),
    )


#: 基础示例的人员名单：(键, 头像字, 姓名, 副标题)
_PEOPLE: tuple[tuple[str, str, str, str], ...] = (
    ("lin", "林", "林一舟", "产品 · 今天 09:12"),
    ("zhao", "赵", "赵思远", "设计 · 今天 08:40"),
    ("chen", "陈", "陈可", "前端 · 昨天 18:20"),
    ("wang", "王", "王砚", "后端 · 昨天 16:05"),
    ("liu", "刘", "刘沐", "测试 · 周二 11:30"),
    ("sun", "孙", "孙泊", "运维 · 周二 09:00"),
)


# ---------------------------------------------------------------------------
# 示例
# ---------------------------------------------------------------------------
@ft.component
def _basic() -> ft.Control:
    """带头像与副标题的名单；点一行选中，选中态由 ListTile 自己画。"""
    picked, set_picked = ft.use_state("lin")

    def pick(key: str):
        def handler(_event: ft.Event[ft.ListTile]) -> None:
            set_picked(key)

        return handler

    return ListView(
        padding=ft.Padding.symmetric(vertical=SPACE["2"], horizontal=SPACE["2"]),
        controls=[
            ft.ListTile(
                leading=_avatar(initial),
                title=ft.Text(name, size=FONT_SIZE["subtitle"]),
                subtitle=ft.Text(sub, size=FONT_SIZE["small"], color=_MUTED),
                trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT, size=18, color=_MUTED),
                selected=key == picked,
                on_click=pick(key),
            )
            for key, initial, name, sub in _PEOPLE
        ],
    )


#: 设置项：(图标, 标题, 说明)
_SETTINGS: tuple[tuple[ft.IconData, str, str], ...] = (
    (ft.Icons.WIFI, "无线网络", "已连接 Office-5G"),
    (ft.Icons.BLUETOOTH, "蓝牙", "2 台设备已配对"),
    (ft.Icons.NOTIFICATIONS_OUTLINED, "通知", "仅接收提及与指派"),
    (ft.Icons.LOCK_OUTLINE, "隐私", "会话锁 5 分钟后生效"),
    (ft.Icons.CLOUD_OUTLINED, "同步", "上次同步 3 分钟前"),
)


@ft.component
def _divided() -> ft.Control:
    """分隔线 + 内边距：行与行之间的归属感来自那条 1px，而不是把行距拉大。"""
    return ListView(
        divider_thickness=1,
        padding=ft.Padding.symmetric(horizontal=SPACE["4"], vertical=SPACE["2"]),
        controls=[
            ft.ListTile(
                leading=ft.Icon(icon, size=20, color=ft.Colors.PRIMARY),
                title=ft.Text(title, size=FONT_SIZE["subtitle"]),
                subtitle=ft.Text(desc, size=FONT_SIZE["small"], color=_MUTED),
                trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT, size=18, color=_MUTED),
            )
            for icon, title, desc in _SETTINGS
        ],
    )


@ft.component
def _long() -> ft.Control:
    """200 项、固定行高 44：滚动时只构建视口附近的项，拖动不卡。"""
    return ListView(
        item_extent=44,
        padding=ft.Padding.symmetric(horizontal=SPACE["3"]),
        controls=[
            ft.Container(
                height=44,
                padding=ft.Padding.symmetric(horizontal=SPACE["2"]),
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(f"任务 #{index:03d}", size=FONT_SIZE["body"]),
                        ft.Text("已完成", size=FONT_SIZE["caption"], color=_MUTED),
                    ],
                ),
            )
            for index in range(1, 201)
        ],
    )


_BASIC_CODE = """ListView(
    height=320,                          # 有界高度：没有它列表渲染不出来
    padding=Padding.symmetric(vertical=8),
    controls=[
        ListTile(
            leading=CircleAvatar(content=Text("林")),
            title=Text("林一舟"),
            subtitle=Text("产品 · 今天 09:12"),
            on_click=lambda e: open_profile("lin"),
        ),
    ],
)"""

_LONG_CODE = """ListView(
    height=320,
    item_extent=44,                      # 固定行高：视口能算出要构建哪几项
    controls=[task_row(task) for task in tasks],   # 200 项也只在滚动时构建可见部分
)

# 放在已经有界的父级里时，改用 expand 占满剩余空间：
Column(expand=True, controls=[ListView(expand=True, controls=rows)])"""


SPEC = Spec(
    name="ListView",
    summary="一列可滚动的项：按视口构建、可加分隔线，长列表也不拖慢首屏。",
    definition=(
        "ListView 是「一屏装不下的一列」。它和 Column 的差别在构建方式：Column 会一次性"
        "把全部子项放进控件树，ListView 只构建视口附近的那几项，所以 200 项、2000 项的"
        "首屏开销与滚动流畅度都不随总数线性变差。代价是它必须知道自己有多高 —— 无界"
        "高度下它不是「不滚」，而是根本渲染不出来。"
    ),
    anatomy=[
        ("列表项", "controls 按顺序从上到下；每项可以是 ListTile，也可以是任意控件。"),
        (
            "滚动区",
            "视口高度来自父级约束（height / expand）。列表本身不会向外要高度。",
        ),
        (
            "分隔线",
            "divider_thickness > 0 时在相邻两项之间画 1px 线，配 padding 用才不会顶到边。",
        ),
        (
            "行高",
            "item_extent 给固定行高，视口能精确算出要构建哪几项，长列表滚动更稳。",
        ),
        (
            "按需构建",
            "build_controls_on_demand 默认开启，只为可见区域附近的项生成控件。",
        ),
    ],
    when=[
        "条目数量不确定或明显超过一屏：消息、日志、任务、搜索结果",
        "每行结构一致（头像 + 标题 + 副标题 + 右侧图标），适合用 ListTile 拼",
        "需要分隔线或统一内边距的一列内容",
    ],
    avoid=[
        "十几项且不用滚动：直接用 Column，少一层滚动容器",
        "内容要按列或网格铺开：用 GridView，ListView 只有一列",
        "行与行需要不同的间距、或要分组吸顶：改用多个小节 + 各自的 Column",
    ],
    examples=[
        Example(
            "基础列表",
            _basic,
            hint="头像 + 姓名 + 副标题；点一行选中，选中态由 ListTile 自己画。",
            code=_BASIC_CODE,
            padded=False,
            height=320,
        ),
        Example(
            "分隔线与内边距",
            _divided,
            hint="divider_thickness=1 配 16 的左右内边距，行与行分开但不显得松散。",
            padded=False,
            height=320,
        ),
        Example(
            "长列表滚动",
            _long,
            hint="200 项、行高固定 44：滚动时只构建视口附近的项，拖动不卡。",
            code=_LONG_CODE,
            padded=False,
            height=320,
        ),
    ],
    api=[
        Api("controls", "list[Control]", "", "列表项，按顺序从上到下"),
        Api("spacing", "int", "0", "相邻两项的间距；有分隔线时保持 0"),
        Api(
            "padding",
            "Padding | int | None",
            "None",
            "列表四周内边距；贴边列表留空，带分隔线时通常给 12-16",
        ),
        Api("divider_thickness", "int", "0", "项之间的分隔线粗细，0 表示不画"),
        Api(
            "item_extent",
            "Number | None",
            "None",
            "固定行高；设了才能按视口精确懒加载",
        ),
        Api("horizontal", "bool", "False", "改成横向滚动的一排"),
        Api(
            "build_controls_on_demand",
            "bool",
            "True",
            "只构建可见项；长列表不要关掉",
        ),
        Api("auto_scroll", "bool", "False", "追加内容后自动滚到底，日志常用"),
        Api(
            "clip_behavior",
            "ClipBehavior",
            "ANTI_ALIAS",
            "边界裁剪方式；默认已改为抗锯齿，圆角卡片不出锯齿",
        ),
    ],
    notes=[
        warn(
            "ListView 必须有有界高度：height、expand，或父级本身有界。放进默认的 Column "
            "（高度无界）里会渲染不出来 —— 不是空白就是直接报错，先查这一条。"
        ),
        tip(
            "长列表给 item_extent 固定行高：省掉逐项测量，滚动位置也更准；代价是每项"
            "真的必须一样高，行内换行会导致裁切。"
        ),
        info(
            "clip_behavior 的默认值从 flet 的 HARD_EDGE 改成了 ANTI_ALIAS。列表项多为"
            "圆角卡片，滚到视口边缘时硬边裁剪会留下明显锯齿。"
        ),
    ],
    tags=("列表", "list", "listview", "长列表", "滚动", "懒加载"),
)


if __name__ == "__main__":
    run(SPEC)
