"""生成 ``src/ui/_registry.py``：组件名 → 所属子模块。

为什么需要这张表（改前先读）：``ui/__init__.py`` 不再 eager star-import 全部子包，
而是靠 PEP 562 的模块级 ``__getattr__`` 按需加载。名字一多（178 个）就无法手写，
也不该手写 —— 漏一个就是 ``from ui import X`` 静默失效。所以由本脚本从各子包
真实的 ``__all__`` 生成，并在 CI / 提交前用 ``--check`` 校验有没有漂移。

用法::

    python scripts/gen_ui_registry.py           # 重新生成
    python scripts/gen_ui_registry.py --check   # 只校验，不一致则退出码 1
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

#: 子包导入顺序 = 覆盖顺序（后者覆盖前者），与原先 ``__init__`` 里 star-import 的顺序一致
ORDER: tuple[str, ...] = (
    "chart",
    "core",
    "display",
    "feedback",
    "input",
    "layout",
    "navigation",
    "utils",
)

TARGET = ROOT / "src" / "ui" / "_registry.py"

HEADER = '''"""组件名 → 所属子模块（**自动生成，勿手改**）。

由 ``python scripts/gen_ui_registry.py`` 从各子包的 ``__all__`` 生成，
``python scripts/gen_ui_registry.py --check`` 校验是否与源码一致。

``ui/__init__.py`` 用它实现 PEP 562 懒加载：``import ui`` 只加载 flet 本身，
具体组件在第一次被访问时才导入所属子包（图表子包会拖进 matplotlib / plotly，
必须留在使用点之后）。
"""

from __future__ import annotations

#: 名字 → 子模块；``getattr(importlib.import_module(模块), 名字)`` 即为该导出
COMPONENT_MODULES: dict[str, str] = {
'''


def build() -> dict[str, str]:
    """按 ORDER 收集各子包的 ``__all__``（后者覆盖前者）。"""
    mapping: dict[str, str] = {}
    for sub in ORDER:
        module = importlib.import_module(f"ui.{sub}")
        names = getattr(module, "__all__", None)
        if not names:
            raise SystemExit(f"ui.{sub} 缺少 __all__，无法生成注册表")
        for name in names:
            mapping[name] = f"ui.{sub}"
    return mapping


def render(mapping: dict[str, str]) -> str:
    lines = [HEADER]
    for name in sorted(mapping):
        lines.append(f'    "{name}": "{mapping[name]}",\n')
    lines.append("}\n")
    return "".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="只校验，不写文件")
    args = parser.parse_args()

    text = render(build())
    if args.check:
        current = TARGET.read_text(encoding="utf-8") if TARGET.exists() else ""
        if current != text:
            print(f"{TARGET} 与源码不一致，请运行 python scripts/gen_ui_registry.py")
            return 1
        print(f"{TARGET} 已是最新（{len(build())} 个导出）")
        return 0

    TARGET.write_text(text, encoding="utf-8", newline="\n")
    print(f"已写入 {TARGET}（{len(build())} 个导出）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
