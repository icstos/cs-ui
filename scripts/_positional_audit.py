"""审计 src/ui 下 @ft.control 组件的位置参数顺序。

flet 1.0.0 的基类字段大多为 kw_only。子类若用裸注解重新声明同名字段
（如 ``height: int = 36``），dataclasses 会把它翻成 **位置参数**，且保留基类
中的字段位置 —— 于是第一个位置参数不再是 ``content``，``Button("文字")``
会把文字塞进 ``height``。

跑法：
    python scripts/_positional_audit.py
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import flet as ft  # noqa: E402
import ui  # noqa: E402


def positional(cls) -> list[str]:
    try:
        sig = inspect.signature(cls)
    except (TypeError, ValueError):
        return []
    return [
        n
        for n, p in sig.parameters.items()
        if p.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    ]


def base_positional(cls) -> list[str]:
    for base in cls.__mro__[1:]:
        if not getattr(base, "__module__", "").startswith("flet"):
            continue
        pos = positional(base)
        if pos:
            return pos
    return []


def iter_ui_classes():
    pkg_dir = Path(ui.__file__).parent
    for mod in pkgutil.walk_packages([str(pkg_dir)], prefix="ui."):
        if ".data" in mod.name:
            continue
        try:
            m = importlib.import_module(mod.name)
        except Exception as e:  # noqa: BLE001
            print(f"!! import failed {mod.name}: {type(e).__name__}: {e}")
            continue
        for name, obj in vars(m).items():
            if not inspect.isclass(obj):
                continue
            if obj.__module__ != mod.name:
                continue
            if not hasattr(obj, "__dataclass_fields__"):
                continue
            yield mod.name, name, obj


def main() -> None:
    bad = []
    checked = 0
    skipped_custom = 0
    for mod_name, name, cls in iter_ui_classes():
        # 手写 __init__ 的类，位置参数由作者显式控制，不受 dataclasses 重排影响。
        # dataclasses 生成的 __init__ 其 co_filename 为 "<string>"。
        if getattr(cls.__init__, "__code__", None) is None or (
            cls.__init__.__code__.co_filename != "<string>"
        ):
            skipped_custom += 1
            continue
        checked += 1
        base_pos = base_positional(cls)
        own_pos = positional(cls)
        inherited = set(base_pos)
        # 危险模式：某个「子类新增字段」出现在「继承字段」之前 ——
        # 说明它抢占了基类字段原有的位置。
        seen_new = False
        stolen_head: list[str] = []
        for p in own_pos:
            if p in inherited:
                if seen_new:
                    stolen_head.append(p)
            else:
                seen_new = True
        if stolen_head:
            bad.append((mod_name, name, base_pos, own_pos, stolen_head))

    print(
        f"检查了 {checked} 个「由 dataclass 生成 __init__」的组件"
        f"（跳过 {skipped_custom} 个自带 __init__ 的类）\n"
    )
    if not bad:
        print("OK：没有子类新增字段抢占继承字段的位置。")
        return
    print(f"!! {len(bad)} 个组件存在字段抢占位置：\n")
    for mod_name, name, base_pos, own_pos, stolen in sorted(
        bad, key=lambda x: (x[0], x[1])
    ):
        print(f"  {mod_name}.{name}")
        print(f"      位置参数: {own_pos}")
        print(f"      被顶到新增字段之后的继承字段: {stolen}")


if __name__ == "__main__":
    main()
