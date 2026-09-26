"""页面级浮层 (floating layer)。

有些面板必须"悬挂"在页面之上：下拉框的选项面板、气泡提示、二级菜单。
它们不能占据布局空间，否则会把下方内容推下去。

.. note::
    在 flet 1.0.0 里，浮层**只有一条路可走**，两条看似可行的路都已实测排除：

    1. **``Stack(clip_behavior=NONE)`` 让面板溢出绘制** —— 画得出来，但**点不到**。
       Flutter 的 ``RenderBox.hitTest`` 会拒绝自身 ``size`` 之外的坐标，
       所以溢出的那部分永远收不到点击。
    2. **``page.overlay``** —— 唯一同时满足"不占布局"和"可交互"的层。
       但它**只在 ``page.render``（根视图）路径下渲染**；
       用 ``page.render_views``（Router 的 ``manage_views=True`` 视图栈）时，
       View 会把它整层盖住 —— 不报错、Python 侧 ``len(page.overlay)`` 正确、
       回调照常触发，但**零像素变化**。``page.show_dialog`` 同样如此。

    :func:`overlay_usable` 用来探测当前处于哪条路径，调用方可据此降级。

用法::

    from ui.core.float_layer import use_float_layer

    @ft.component
    def Widget(self):
        page = ft.context.page
        use_float_layer(
            page=page,
            visible=self.is_open,
            left=80,
            top=140,
            content=self._build_panel(),
            on_dismiss=self.close,
        )
        return self._build_field()
"""

from __future__ import annotations

from collections.abc import Callable

import flet as ft

__all__ = ["overlay_usable", "use_float_layer"]

#: 遮罩颜色：几乎全透明，但足以参与命中测试（拦截"点击外部"）。
BARRIER_COLOR = ft.Colors.with_opacity(0.01, ft.Colors.BLACK)


def overlay_usable(page: ft.Page) -> bool:
    """当前渲染路径下 ``page.overlay`` 是否真的会显示。

    ``page.render`` 把组件渲染进根视图，``page.views`` 保持为 ``[View]``；
    ``page.render_views`` 则把渲染结果整体赋给 ``page.views``，此时它是
    一个未展开的组件对象而不是列表 —— 浮层层被视图栈遮住。

    这个判断是**行为性**的（而非读取某个内部开关），但它只用来决定
    "用浮层还是退化成流内展开"，判错的最坏结果是多占一点高度，不会失效。
    """
    try:
        return isinstance(page.views, list)
    except Exception:  # noqa: BLE001 - 拿不到 views 时按不可用处理
        return False


def use_float_layer(
    *,
    page: ft.Page,
    visible: bool,
    left: float,
    content: ft.Control,
    top: float | None = None,
    bottom: float | None = None,
    on_dismiss: Callable[[], None] | None = None,
    hole: tuple[float, float, float, float] | None = None,
) -> None:
    """把 ``content`` 挂到页面浮层，并带一层全屏透明遮罩。

    必须在组件渲染期间调用（它是一个 hook 集合，依赖当前组件上下文）。

    Args:
        page: 目标页面。
        visible: 是否显示。``False`` 时浮层会被移除。
        left: 面板左边缘相对页面客户区的横坐标（逻辑像素）。
        content: 浮层内容。
        top: 面板**上**边缘的纵坐标（逻辑像素）。与 ``bottom`` 二选一。
        bottom: 面板**下**边缘到页面底部的距离（逻辑像素）。与 ``top`` 二选一。
            "向上翻转"的下拉面板用 ``bottom`` 定位更稳：面板实际高度不必预知，
            多高都自动贴着锚点，不会因为高度估算误差而离出一条缝。
        on_dismiss: 点击遮罩（面板外部）时触发，通常用于收起重置状态。
            为 ``None`` 时不加遮罩，浮层只作展示用。
        hole: 可选，遮罩上挖出的孔洞 ``(x, y, w, h)``。用来放行锚点控件自身
            （比如输入框）——否则遮罩会盖住它，它上面的按钮（Chip 的 ``×``）
            就永远点不到，点击只会变成"点外部关闭"。
    """
    if (top is None) == (bottom is None):
        raise ValueError("use_float_layer 需要 top / bottom 二选一")

    holder = ft.use_ref(lambda: {"node": None})

    def remove() -> bool:
        node = holder.current["node"]
        if node is None:
            return False
        try:
            if node in page.overlay:
                page.overlay.remove(node)
        except Exception:  # noqa: BLE001 - 页面已销毁等情况
            pass
        holder.current["node"] = None
        return True

    def sync() -> None:
        removed = remove()
        if not visible:
            if removed:
                page.update()
            return

        barrier: list[ft.Control] = []
        if on_dismiss is not None:
            barrier = _barrier_blocks(hole, on_dismiss)

        anchor = (
            {"top": top} if top is not None else {"bottom": bottom}
        )
        node = ft.Stack(
            left=0,
            top=0,
            right=0,
            bottom=0,
            clip_behavior=ft.ClipBehavior.NONE,
            controls=[
                *barrier,
                ft.Container(left=left, content=content, **anchor),
            ],
        )
        holder.current["node"] = node
        page.overlay.append(node)
        page.update()

    def drop() -> None:
        if remove():
            try:
                page.update()
            except Exception:  # noqa: BLE001 - 卸载途中页面可能已关闭
                pass

    ft.on_updated(sync)
    ft.on_unmounted(drop)


def _barrier_blocks(
    hole: tuple[float, float, float, float] | None,
    on_dismiss: Callable[[], None],
) -> list[ft.Control]:
    """遮罩矩形。给了 ``hole`` 就围出孔洞，否则整块铺满。"""

    def block(**bounds: float) -> ft.Control | None:
        # 只丢真正没有尺寸的块；left/top 为 0 是正常的位置，不是"零尺寸"。
        for key in ("width", "height"):
            if key in bounds and bounds[key] <= 0:
                return None
        return ft.Container(
            bgcolor=BARRIER_COLOR,
            on_click=lambda _e: on_dismiss(),
            **bounds,  # type: ignore[arg-type]
        )

    def keep(items: list[ft.Control | None]) -> list[ft.Control]:
        return [it for it in items if it is not None]

    if hole is None:
        return keep([block(left=0, top=0, right=0, bottom=0)])

    x, y, w, h = hole
    return keep(
        [
            block(left=0, top=0, right=0, height=y),  # 孔洞上方
            block(left=0, top=y + h, right=0, bottom=0),  # 孔洞下方
            block(left=0, top=y, width=x, height=h),  # 孔洞左侧
            block(left=x + w, top=y, right=0, height=h),  # 孔洞右侧
        ]
    )

