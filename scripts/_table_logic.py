"""Table 分页逻辑单测（本项目范式：scripts/_<组件>_logic.py）。

Table 已从「命令式 ``@ft.control`` + ``self.update()``」重写为
「``@ft.component`` + ``use_state``」。这里断言纯逻辑部分：
切片、编号、页数、钳位、列注入。

这些全是**纯函数**，不需要 flet 运行时，因此可以在无头环境下断言。
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import flet as ft  # noqa: E402

from ui.layout.table import TableState  # noqa: E402

PASSED = 0


def check(label: str, got, want) -> None:
    global PASSED
    if got == want:
        PASSED += 1
        print(f"PASS  {label}: got={got!r}")
    else:
        print(f"FAIL  {label}: got={got!r} want={want!r}")
        raise SystemExit(1)


def check_no_raise(label: str, fn) -> None:
    """断言「调用不抛异常」（用于构造类这类无法用等值表达的条件）。"""
    global PASSED
    try:
        fn()
    except BaseException as e:  # noqa: BLE001
        print(f"FAIL  {label}: 抛了 {type(e).__name__}: {e}")
        raise SystemExit(1) from e
    PASSED += 1
    print(f"PASS  {label}: 无异常")


# ----------------------------------------------------------------------
# 构造各种形状的数据表
# ----------------------------------------------------------------------


def make_dt(n_rows: int, n_cols: int = 3) -> ft.DataTable:
    rows = [
        ft.DataRow(
            cells=[ft.DataCell(ft.Text(f"r{i}c{j}")) for j in range(n_cols)]
        )
        for i in range(n_rows)
    ]
    cols = [ft.DataColumn(ft.Text(f"c{j}")) for j in range(n_cols)]
    return ft.DataTable(columns=cols, rows=rows)


print("=== 基本分页 ===")
s = TableState(data_table=make_dt(25), rows_per_page=10)
check("总行数", s.num_rows, 25)
check("总页数（25/10 向上取整）", s.num_pages, 3)
check("第 1 页行数", len(s.build_rows(1)), 10)
check("第 3 页行数（余 5）", len(s.build_rows(3)), 5)
check("第 1 页首行全局下标", s.page_slice(1)[1], 0)
check("第 3 页首行全局下标", s.page_slice(3)[1], 20)

print()
print("=== 编号列 ===")
rows = s.build_rows(3)
check("第 3 页首行编号", rows[0].cells[0].content.value, "21")
check("第 3 页末行编号", rows[-1].cells[0].content.value, "25")
check("每行单元格数 = 3 + 编号列", len(rows[0].cells), 4)
cols = s.columns()
check("列数 = 3 + 编号列", len(cols), 4)
check("首列标题", cols[0].label.value, "编号")
check("原列被保留", [c.label.value for c in cols[1:]], ["c0", "c1", "c2"])

print()
print("=== with_number=False ===")
s2 = TableState(data_table=make_dt(7), rows_per_page=3, with_number=False)
rows2 = s2.build_rows(1)
check("不补编号列", len(rows2[0].cells), 3)
check("列数不注入", len(s2.columns()), 3)
check("首格是原始数据", rows2[0].cells[0].content.value, "r0c0")

print()
print("=== with_paged=False（单页铺满）===")
s3 = TableState(data_table=make_dt(12), rows_per_page=5, with_paged=False)
check("全部行都在第一页", len(s3.build_rows(1)), 12)
check("页数仍按 rows_per_page 算（供 Paging 用）", s3.num_pages, 3)
check("首行下标为 0", s3.page_slice(1)[1], 0)

print()
print("=== 页码钳位 ===")
s4 = TableState(data_table=make_dt(25), rows_per_page=10)
check("正常页", s4.clamp_page(2), 2)
check("小于 1 落到 1", s4.clamp_page(0), 1)
check("负数落到 1", s4.clamp_page(-5), 1)
check("超过总页落到 1", s4.clamp_page(99), 1)

print()
print("=== 边界：空表 / 整除 / rows_per_page<=0 ===")
# 注意：flet 1.0.4 的 DataTable.columns 是**必填**位置参数，所以"空表"
# 只能用「有列名、无数据行」来构造 —— 这也正是 Table 不给 data_table 时的兜底形状。
empty_dt = ft.DataTable(columns=[ft.DataColumn(ft.Text("列"))])
check_no_raise("空表构造 TableState", lambda: TableState(data_table=empty_dt, rows_per_page=10))
s_empty = TableState(data_table=make_dt(0), rows_per_page=10)
check("空表行数", s_empty.num_rows, 0)
check("空表页数至少 1", s_empty.num_pages, 1)
check("空表第一页无行", len(s_empty.build_rows(1)), 0)

s_exact = TableState(data_table=make_dt(20), rows_per_page=10)
check("整除时页数不多算", s_exact.num_pages, 2)
check("整除时末页满行", len(s_exact.build_rows(2)), 10)

s_zero = TableState(data_table=make_dt(20), rows_per_page=0)
check("rows_per_page=0 不除零崩溃", s_zero.num_pages, 1)

print()
print("=== 深拷贝：不污染调用方的数据 ===")
src = make_dt(5)
s5 = TableState(data_table=src, rows_per_page=5)
s5.build_rows(1)
check("源表列数未被插入编号列", len(src.columns), 3)
check("源表首行单元格数未被改", len(src.rows[0].cells), 3)
s5.build_rows(1)
check("重复调用不叠加编号列", len(src.rows[0].cells), 3)

print()
print("=== 确定性（纯函数，同输入同输出）===")
a = [c.content.value for c in s.build_rows(2)[0].cells]
b = [c.content.value for c in s.build_rows(2)[0].cells]
check("两次调用结果一致", a, b)

print()
print("=== PagingState 能吃下 TableState 的派生值 ===")
from ui.navigation.paging import PagingState  # noqa: E402

ps = PagingState(sum_data_nums=s4.num_rows, data_per_page_nums=s4.rows_per_page)
check("PagingState 算出的页数与 Table 一致", ps.sum_page_nums, s4.num_pages)

print()
print(f"RESULT: ALL PASS  (passed={PASSED})")
