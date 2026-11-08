"""示例冒烟 —— 把 71 个组件说明里的每一个示例都构建一遍。

和 ``smoke_test.py`` 互补：那个起真 flet 运行时、看的是"窗口里能不能画出来"，
慢（每个组件约 5s）；这个只跑 Python 侧的组件构建，全部 71 个组件约 10s，
适合每次改完框架立刻跑。

覆盖的是**文档里的真实用法** —— ``Spec.examples`` 里的每一个 ``view()``，
也就是 ``docs`` 页面上真正展示的那批控件。框架改动最容易踩的坑
（构造签名、状态字段、可选参数组合）基本都会在这里露出来。

用法::

    python scripts/smoke_examples.py                 # 全部
    python scripts/smoke_examples.py menu tree       # 只跑匹配的组件

退出码：0 = 全部构建成功；1 = 存在失败。
"""

from __future__ import annotations

import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from _harness import build

#: 这类异常不是"坏了"，是"没有页面就构造不出来"：示例里调了 ``ft.context.page``
#: （弹层、定时器、剪贴板都要它）。它们在 ``smoke_test.py`` 里带真窗口跑得到。
_NEEDS_PAGE = "not associated with any page"


def main() -> int:
    from ui.core.catalog import ENTRIES, load

    keywords = sys.argv[1:]
    entries = [
        item
        for item in ENTRIES.values()
        if not keywords
        or any(k.lower() in f"{item.key} {item.module} {item.name}".lower() for k in keywords)
    ]

    started = time.perf_counter()
    total = 0
    needs_page: list[str] = []
    fails: list[tuple[str, str]] = []
    for item in sorted(entries, key=lambda e: e.key):
        try:
            spec = load(item.key)
            examples = spec.examples
        except Exception:  # noqa: BLE001 - 连说明都取不到，单独记一笔
            fails.append((f"{item.key} (SPEC 加载)", traceback.format_exc(limit=3)))
            continue
        for example in examples:
            total += 1
            label = f"{item.key} / {example.title}"
            try:
                build(example.view)
            except RuntimeError as exc:
                if _NEEDS_PAGE in str(exc):
                    needs_page.append(label)
                else:
                    fails.append((label, traceback.format_exc(limit=6)))
            except Exception:  # noqa: BLE001
                fails.append((label, traceback.format_exc(limit=6)))

    elapsed = time.perf_counter() - started
    print(
        f"\n{len(entries)} 个组件、{total} 个示例："
        f"直接构建通过 {total - len(fails) - len(needs_page)}、"
        f"需要页面 {len(needs_page)}、失败 {len(fails)}，耗时 {elapsed:.1f}s"
    )
    if needs_page:
        print("需要页面的示例（无头构建不了，靠 smoke_test.py 覆盖）：")
        for label in needs_page:
            print(f"  ~ {label}")
    for label, err in fails:
        print(f"\n=== {label}\n{err}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
