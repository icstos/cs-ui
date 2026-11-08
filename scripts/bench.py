"""性能基准 —— 让"高性能"成为可测量、可回归的属性，而不是形容词。

三条被测曲线，各自对应一类真实退化：

1. **冷启动**（``import``）：子进程里从零 ``import``，取多次的中位数。退化信号是
   "某个门面又开始 eagerly 导入兄弟模块"——历史上 ``ui.core`` 的 star-import 让
   每次组件导入多付 90~170ms。
2. **组件构建**（``render``）：把组件在**无页面**的渲染器里跑一遍 ``ui()``，量的是
   纯 Python 侧的控件树构建时间。退化信号是 O(n²) 查找、每行重复算同一份索引、
   或者往每行里塞了本可以共用的控件。
3. **热路径函数**（``micro``）：查找 / 格式化 / 翻译这类每次重绘都要跑的纯函数。

为什么不用 ``page.render()``
----------------------------
带页面跑一遍要起 flet 运行时、走 IPC、等 Flutter 排帧，测量对象里混进了大量与
本框架无关的噪声（实测首屏 0.57s 里 0.35s 是事件循环在等）。``@ft.component``
的实现被 flet 拆成了两段：``obj.ui()`` 只登记一个 ``Component`` 包装，
``Renderer(component).render(fn, *args)`` 才真正执行函数体。基准钻的就是第二段 ——
它跑的是**同一份代码**，但只含我们要优化的部分。

用法::

    python scripts/bench.py                      # 全部，人读
    python scripts/bench.py --sections render    # 只量构建
    python scripts/bench.py --json out.json      # 存档（可当基线）
    python scripts/bench.py --baseline out.json  # 与基线比对，超阈值即退出码 1

阈值默认 +25%：性能测量在共享 CI 上抖 5~10% 很正常，卡太紧会把噪声变成红灯，
反而让人习惯性忽略它。
"""

from __future__ import annotations

import argparse
import datetime as dt
import gc
import json
import math
import statistics
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import flet as ft

# 构建/展开组件的实现放在 scripts/_harness.py，示例冒烟 (smoke_examples.py) 共用。
from _harness import build as _build

#: 与基线比对时的容差（性能只会因为"改坏了"而变慢，小幅波动不拦）
TOLERANCE = 0.25

#: 回归判定的绝对下限（毫秒）。差值小于这个数一律不算 —— 在 0.02ms 上
#: 算百分比是没有意义的：一次调度抖动就能让它翻倍，红绿全看运气。
MIN_ABS_DELTA_MS = 0.5

#: 每个用例的重复次数（取中位数；中位数比均值抗偶发 GC / 调度抖动）
REPEAT = 9


# ---------------------------------------------------------------------------
# 采样工具
# ---------------------------------------------------------------------------
def _median_ms(fn: Callable[[], Any], repeat: int = REPEAT) -> float:
    """跑 ``repeat`` 次取中位数（毫秒）。

    测量期间**关掉循环 GC**。每个用例都会造出几千个短期控件对象，开着 GC 时
    什么时候回收取决于前面跑过什么 —— 同一段代码在"刚跑完 import 段"和"单独
    跑"两种情况下能差 30%（实测 6.7ms → 8.9ms），红绿全看调用顺序。关掉 GC
    再测、测完立刻回收，数字才只反映被测代码本身。
    """
    fn()  # 预热：第一次会带上懒导入 / 分支预测 / 缓存填充

    gc_was_enabled = gc.isenabled()
    gc.disable()
    try:
        samples: list[float] = []
        for _ in range(repeat):
            # 每轮开始前清一次：只关 GC 不回收的话，9 轮堆越攒越大，
            # 后面的样本会比前面的慢（calendar 实测 2.7ms → 4.1ms）。
            # gc.collect() 在 disabled 状态下仍然会执行，可以照常调用。
            gc.collect()
            start = time.perf_counter()
            fn()
            samples.append((time.perf_counter() - start) * 1000)
    finally:
        if gc_was_enabled:
            gc.enable()
        gc.collect()
    return round(statistics.median(samples), 3)


# ---------------------------------------------------------------------------
# 用例：数据规模贴近真实使用（侧边栏几十项、表格几百行、日历一年）
# ---------------------------------------------------------------------------
def _menu_items(top: int = 60, child: int = 4, groups: int = 10) -> list[Any]:
    from ui.navigation.menu import MenuGroup, MenuItem

    out: list[Any] = []
    step = top // groups
    for g in range(groups):
        out.append(
            MenuGroup(
                f"组{g}",
                [
                    MenuItem(
                        f"k{i}",
                        f"项目 {i}",
                        children=[
                            MenuItem(f"k{i}-{j}", f"子项 {j}") for j in range(child)
                        ],
                    )
                    for i in range(g * step, (g + 1) * step)
                ],
            )
        )
    return out


def _case_menu() -> Any:
    from ui.navigation.menu import Menu

    menu = Menu(items=_menu_items(), selected_key="k0-1")
    menu.expanded_keys = tuple(f"k{i}" for i in range(6))
    return menu


def _case_tree() -> Any:
    from ui.display.tree import Tree, TreeNode

    nodes = [
        TreeNode(f"节点{i}", children=[TreeNode(f"子{i}-{j}") for j in range(3)])
        for i in range(60)
    ]
    return Tree(data=nodes)


def _case_table() -> Any:
    from ui.layout.table import Table

    # 数据源在**计时之外**准备好：要量的是组件构建，不是 ft.DataTable 的构造。
    return Table(data_table=_table_data(), rows_per_page=10)


def _table_data() -> ft.DataTable:
    global _TABLE_DATA
    if _TABLE_DATA is None:
        head = [f"列{j}" for j in range(6)]
        _TABLE_DATA = ft.DataTable(
            columns=[ft.DataColumn(ft.Text(h)) for h in head],
            rows=[
                ft.DataRow([ft.DataCell(ft.Text(f"r{i}c{j}")) for j in range(6)])
                for i in range(200)
            ],
        )
    return _TABLE_DATA


_TABLE_DATA: ft.DataTable | None = None


def _case_descriptions() -> Any:
    from ui.display.descriptions import Descriptions, DescriptionsItem

    return Descriptions(
        items=[DescriptionsItem(f"字段{i}", f"值 {i}") for i in range(24)]
    )


def _case_pagination() -> Any:
    from ui.navigation.pagination import Pagination, PaginationState

    return Pagination(
        PaginationState(sum_data_nums=1286, data_per_page_nums=10, current_page=3)
    )


def _case_calendar() -> Any:
    from ui.display.calendar import Calendar

    return Calendar(value=dt.date(2026, 11, 7))


def _case_heatmap() -> Any:
    from ui.display.heatmap import Heatmap, HeatmapItem

    start = dt.date(2026, 1, 1)
    items = [
        HeatmapItem(start + dt.timedelta(days=i), (i * 7) % 11) for i in range(365)
    ]
    return Heatmap(items)


def _case_tree_expanded() -> Any:
    """全展开、无勾选框：给"每行成本"一个干净的分母。

    默认折叠时只渲染 60 个顶层行，拿它和全展开的用例比会得出"勾选框贵 5 倍"的
    错误结论 —— 差异主要来自行数。三个用例摆在一起才看得出哪个是真的。
    """
    from ui.display.tree import Tree, TreeNode

    nodes = [
        TreeNode(f"节点{i}", children=[TreeNode(f"子{i}-{j}") for j in range(3)])
        for i in range(60)
    ]
    return Tree(data=nodes, default_expand_all=True)


def _case_tree_checked() -> Any:
    """全展开 + 每行一个三态复选框。

    勾选框那套"方框 + 边框 + 圆角"很容易写成逐行新建值
    （``ft.Border.all`` 约 7µs、``BorderRadius.all`` 约 3µs），几百行就白扔
    好几毫秒 —— 这条曲线专门盯着它。
    """
    from ui.display.tree import Tree, TreeNode

    nodes = [
        TreeNode(f"节点{i}", children=[TreeNode(f"子{i}-{j}") for j in range(3)])
        for i in range(60)
    ]
    return Tree(data=nodes, show_checkbox=True, default_expand_all=True)


RENDER_CASES: dict[str, Callable[[], Any]] = {
    "menu 60 顶层 / 240 项 / 10 分组": _case_menu,
    "tree 60 顶层（折叠）": _case_tree,
    "tree 60×4（全展开）": _case_tree_expanded,
    "tree 60×4（全展开 + 勾选框）": _case_tree_checked,
    "table 200×6（分页 10 行）": _case_table,
    "descriptions 24 字段": _case_descriptions,
    "pagination 1286 项": _case_pagination,
    "calendar 月视图": _case_calendar,
    "heatmap 365 天": _case_heatmap,
}


# ---------------------------------------------------------------------------
# 三个 section
# ---------------------------------------------------------------------------
def section_import() -> dict[str, float]:
    """冷启动：每个用例一个全新解释器，取 5 次中位数。

    必须用子进程 —— 进程内的第二次 ``import`` 命中 ``sys.modules``，量到的是 0。

    关于 ``from ui.chart import BarChart`` 那 ~850ms：**这不是本框架的账**。
    ``flet_charts/__init__.py`` 会连锁导入 ``matplotlib_chart``（拖进 matplotlib，
    单这一条链就 ~540ms）与 ``plotly_chart``（~130ms）；而 Python 导入任何子模块
    前必先执行父包 ``__init__``，所以没法"只导一个柱状图"。我们这侧能做的只有
    「用到图表才付」—— ``ui/chart/__init__.py`` 是惰性门面，``import ui.chart``
    不碰 matplotlib，真正的账单落在第一次取具体图表类上。这条曲线留着当参照线 ——
    它受第三方包版本影响，超出容差时先怀疑 flet-charts 升级，而不是我们的代码。
    """
    cases = {
        "import flet（参照基准）": "import flet",
        "import ui": "import ui",
        "import ui.navigation.menu": "import ui.navigation.menu",
        "import ui.layout.table": "import ui.layout.table",
        "import ui.input.button": "import ui.input.button",
        "import ui.display.descriptions": "import ui.display.descriptions",
        "from ui.chart import BarChart": "from ui.chart import BarChart",
    }
    out: dict[str, float] = {}
    src_dir = ROOT / "src"
    for label, stmt in cases.items():
        code = (
            f"import sys,time;sys.path.insert(0, r'{src_dir}');"
            f"t=time.perf_counter();{stmt};print((time.perf_counter()-t)*1000)"
        )
        samples = []
        for _ in range(5):
            proc = subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True,
                text=True,
                cwd=str(ROOT),
                check=False,
            )
            if proc.returncode != 0:
                out[label] = float("nan")
                break
            samples.append(float(proc.stdout.strip()))
        if samples:
            out[label] = round(statistics.median(samples), 1)
    return out


def section_render() -> dict[str, float]:
    out: dict[str, float] = {}
    for label, factory in RENDER_CASES.items():
        try:
            out[label] = _median_ms(lambda f=factory: _build(f))
        except Exception as exc:  # noqa: BLE001 - 用例本身崩了不该掩盖其它数据
            print(f"  ! {label}: {type(exc).__name__}: {exc}", file=sys.stderr)
            out[label] = float("nan")
    return out


def section_micro() -> dict[str, float]:
    """热路径纯函数 —— 每次重绘都会跑的那些。"""
    from ui.navigation.menu import (
        find_path,
        norm_selected,
        prune_expanded,
        visible_rows,
    )

    items = _menu_items()
    expanded = tuple(f"k{i}" for i in range(6))

    out: dict[str, float] = {}
    out["menu.find_path（命中叶子）"] = _median_ms(lambda: find_path(items, "k59-3"))
    out["menu.find_path（未命中）"] = _median_ms(lambda: find_path(items, "无此项"))
    out["menu.visible_rows（默认）"] = _median_ms(lambda: visible_rows(items, expanded))
    out["menu.prune_expanded"] = _median_ms(lambda: prune_expanded(items, expanded))
    out["menu.norm_selected"] = _median_ms(lambda: norm_selected(items, "k30-2"))
    return out


SECTIONS: dict[str, Callable[[], dict[str, float]]] = {
    "import": section_import,
    "render": section_render,
    "micro": section_micro,
}


# ---------------------------------------------------------------------------
# 输出
# ---------------------------------------------------------------------------
def _is_regression(value: float, base: float) -> bool:
    """判定一次测量是否算回归。

    **必须同时满足"相对超标"和"绝对可感"**。热路径那几支只有 0.01~0.08ms，
    在这个量级上跑一次多 20µs 就会显示 +60%，可它连一次函数调用的抖动都比
    这个差值大 —— 只看百分比，基准会在同代码上随机翻红，几次之后就没人信它了。
    """
    if not base or math.isnan(base) or math.isnan(value):
        return False
    if value - base < MIN_ABS_DELTA_MS:
        return False
    return value > base * (1 + TOLERANCE)


def _print_block(
    title: str, data: dict[str, float], baseline: dict[str, float]
) -> None:
    print(f"\n{title}")
    print("-" * 66)
    for label, value in data.items():
        base = baseline.get(label)
        if base and not math.isnan(base) and not math.isnan(value):
            ratio = value / base
            mark = "!!" if _is_regression(value, base) else "  "
            delta = f"{ratio - 1:+.0%}"
            print(f"{mark} {label:44s}{value:9.2f}ms{delta:>8s}")
        else:
            print(f"   {label:44s}{value:9.2f}ms")


def main() -> int:
    parser = argparse.ArgumentParser(description="cs-ui 性能基准")
    parser.add_argument(
        "--sections",
        default="import,render,micro",
        help="逗号分隔，可选 import / render / micro",
    )
    parser.add_argument("--json", default="", help="把结果写成 JSON（可作为基线）")
    parser.add_argument("--baseline", default="", help="与这份 JSON 比对")
    args = parser.parse_args()

    wanted = [s.strip() for s in args.sections.split(",") if s.strip()]
    unknown = [s for s in wanted if s not in SECTIONS]
    if unknown:
        parser.error(f"未知 section: {', '.join(unknown)}")

    baseline: dict[str, dict[str, float]] = {}
    if args.baseline:
        baseline = json.loads(Path(args.baseline).read_text(encoding="utf-8"))

    results: dict[str, dict[str, float]] = {}
    for name in wanted:
        print(f"采集中：{name} …", file=sys.stderr)
        results[name] = SECTIONS[name]()

    titles = {
        "import": "冷启动（子进程 median of 5）",
        "render": "组件构建（无页面渲染器 median of 9）",
        "micro": "热路径函数",
    }
    for name in wanted:
        _print_block(titles[name], results[name], baseline.get(name, {}))

    if args.json:
        Path(args.json).write_text(
            json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"\n已写入 {args.json}")

    # 回归判定：任一指标超出容差即失败（含绝对下限，见 _is_regression）
    regressions = [
        f"{section} / {label}: {value:.2f}ms vs {baseline[section][label]:.2f}ms"
        for section, block in results.items()
        for label, value in block.items()
        if _is_regression(value, baseline.get(section, {}).get(label, 0.0))
    ]
    if regressions:
        print("\n性能回归：")
        for line in regressions:
            print(f"  !! {line}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
