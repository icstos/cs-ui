"""无页面构建工具 —— 基准与示例冒烟共用的一份实现。

为什么需要它
------------
``@ft.component`` 是**惰性**的：``obj.ui()`` 只是登记一个 ``Component`` 占位，
函数体要等 ``Renderer(component).render(fn, *args, **kwargs)`` 才真正执行。
所以"构建一棵组件树"在 Python 侧永远是两段：

1. 进 ``Renderer().with_context()`` —— 上下文必须在**登记之前**进入，否则
   ``@ft.component`` 函数一被调用就抛 "No current renderer is set"；
2. ``Renderer(node).render(node.fn, *node.args, **node.kwargs)`` 把函数体跑出来。

三种组件形态都要能测，因为框架里三种都真实存在：

* **observable 对象 + ``ui()``**（``Menu`` / ``Tree`` / ``Calendar``）
* **``@ft.component`` 函数**（``Table`` / ``Pagination``）
* **构造即完成的控件**（``Descriptions`` 继承 ``ft.Container``）

``expand`` 的用途是把**子组件**也展开成普通控件。真实渲染里子组件是逐个挂载
构建的；只渲染根组件量不到"整棵树到底建了多少控件"。基准要的是后者，否则
「拆成每行一个组件」这种改动会让数字凭空变小（行其实只是被推迟了）。
"""

from __future__ import annotations

import dataclasses
from collections.abc import Callable
from typing import Any

import flet as ft

__all__ = ["build", "child_fields", "expand"]

_CHILD_FIELDS: dict[type, tuple[str, ...]] = {}


def child_fields(cls: type) -> tuple[str, ...]:
    """这个控件类里"可能装子控件"的字段名（按类缓存）。

    逐个字段 ``getattr`` 太贵：``Container`` 有 60 多个字段，几百个控件就是几万次
    属性读，量到的会是基准自己的开销。按声明类型筛一遍并缓存，之后每个节点只读
    两三个字段。
    """
    cached = _CHILD_FIELDS.get(cls)
    if cached is None:
        names = []
        for f in dataclasses.fields(cls):
            text = f.type if isinstance(f.type, str) else str(f.type)
            if "Control" in text or "Component" in text or text.startswith("list"):
                names.append(f.name)
        cached = tuple(names)
        _CHILD_FIELDS[cls] = cached
    return cached


def expand(node: Any, depth: int = 0) -> Any:
    """把控件树里的子组件**就地展开**成普通控件，返回同一个（可能被替换的）节点。"""
    from flet.components.component import Component, Renderer

    if depth > 24:  # 防环（正常树远没有这么深）
        return node
    if isinstance(node, Component):
        with Renderer().with_context():
            built = Renderer(node).render(node.fn, *node.args, **node.kwargs)
        return expand(built, depth + 1)
    if isinstance(node, list):
        for i, item in enumerate(node):
            if isinstance(item, (Component, ft.Control, list)):
                node[i] = expand(item, depth + 1)
        return node
    if isinstance(node, ft.Control):
        for name in child_fields(type(node)):
            value = getattr(node, name, None)
            if isinstance(value, (list, Component, ft.Control)):
                replaced = expand(value, depth + 1)
                if replaced is not value:
                    setattr(node, name, replaced)
    return node


def build(factory: Callable[[], Any]) -> Any:
    """执行一个组件工厂，返回构建出的控件树。

    工厂本身也要在渲染器上下文里调用 —— ``@ft.component`` 函数**调用即登记**，
    在上下文外构造会直接抛 "No current renderer is set"。所以用例统一给工厂而不是
    已构造好的实例。
    """
    from flet.components.component import Component, Renderer

    with Renderer().with_context():
        target = factory()
        if isinstance(target, Component):
            node = target  # 组件函数已经自己登记好了
        elif hasattr(target, "ui"):
            node = target.ui()
        else:
            return expand(target)  # 构造即完成的控件
        tree = Renderer(node).render(node.fn, *node.args, **node.kwargs)
    return expand(tree)
