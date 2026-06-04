"""CS UI Chart 组件综合测试示例"""

import math
import os
import sys
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import flet as ft
from ui.chart.line_chart import LineChart


def main(page: ft.Page):
    page.title = "CS UI Chart 图表组件"
    page.bgcolor = "#f8fafc"
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 20

    # 准备测试数据
    large_data = [
        (i, 10 + 5 * math.sin(i * 0.3) + 3 * math.cos(i * 0.7)) for i in range(50)
    ]

    page.add(
        ft.Text(
            "CS UI Chart 图表组件", size=28, weight=ft.FontWeight.BOLD, color="#1f2937"
        ),
        ft.Text("支持多种数据格式，自动配色，交互式提示", size=14, color="#6b7280"),
        ft.Divider(),
        # 1. 简单数值列表
        ft.Text("1. 数值列表 → 自动生成 X 轴索引", size=16, weight=ft.FontWeight.BOLD),
        ft.Text("data=[1, 3, 2, 5, 4, 6, 8]", size=12, color="#6b7280"),
        LineChart(data=[1, 3, 2, 5, 4, 6, 8], height=250, show_points=True),
        ft.Divider(),
        # 2. 单条折线 (字典列表)
        ft.Text("2. 字典列表", size=16, weight=ft.FontWeight.BOLD),
        ft.Text(
            "data=[{'x':1,'y':3}, {'x':2,'y':5}, {'x':3,'y':2}]",
            size=12,
            color="#6b7280",
        ),
        LineChart(
            data=[
                {"x": 1, "y": 3},
                {"x": 2, "y": 5},
                {"x": 3, "y": 2},
                {"x": 4, "y": 7},
                {"x": 5, "y": 4},
            ],
            x="x",
            y="y",
            height=250,
            color="#10b981",
        ),
        ft.Divider(),
        # 3. 多条折线 (列字典)
        ft.Text("3. 多条折线 (列字典)", size=16, weight=ft.FontWeight.BOLD),
        ft.Text(
            "data={'月份':[1,2,3,4,5], '销量A':[3,5,2,7,4], '销量B':[4,6,3,8,5]}",
            size=12,
            color="#6b7280",
        ),
        LineChart(
            data={
                "月份": [1, 2, 3, 4, 5],
                "销量A": [3, 5, 2, 7, 4],
                "销量B": [4, 6, 3, 8, 5],
            },
            x="月份",
            y=["销量A", "销量B"],
            height=280,
            curved=True,
            show_points=True,
        ),
        ft.Divider(),
        # 4. 元组列表
        ft.Text("4. 元组列表", size=16, weight=ft.FontWeight.BOLD),
        ft.Text("data=[(1,3), (2,5), (3,2), (4,7), (5,4)]", size=12, color="#6b7280"),
        LineChart(
            data=[(1, 3), (2, 5), (3, 2), (4, 7), (5, 4)],
            height=250,
            color="#8b5cf6",
            show_points=True,
        ),
        ft.Divider(),
        # 5. 自定义样式
        ft.Text("5. 无网格、无提示、粗线条", size=16, weight=ft.FontWeight.BOLD),
        LineChart(
            data=[(1, 2), (2, 5), (3, 3), (4, 8), (5, 6)],
            height=220,
            color="#ef4444",
            show_grid=False,
            tooltip=False,
            stroke_width=3.0,
        ),
        ft.Divider(),
        # 6. 多条折线 - 字典列表
        ft.Text("6. 多条折线 (字典列表)", size=16, weight=ft.FontWeight.BOLD),
        LineChart(
            data=[
                {"月份": 1, "销售额": 10, "利润": 3},
                {"月份": 2, "销售额": 15, "利润": 5},
                {"月份": 3, "销售额": 12, "利润": 4},
                {"月份": 4, "销售额": 20, "利润": 8},
                {"月份": 5, "销售额": 18, "利润": 7},
            ],
            x="月份",
            y=["销售额", "利润"],
            height=280,
            show_points=True,
        ),
        ft.Divider(),
        # 7. 大量数据
        ft.Text("7. 大量数据 (50个点，平滑曲线)", size=16, weight=ft.FontWeight.BOLD),
        LineChart(
            data=large_data, height=280, curved=True, show_points=False, color="#06b6d4"
        ),
        ft.Divider(),
        # 8. 自定义配色
        ft.Text("8. 自定义配色方案", size=16, weight=ft.FontWeight.BOLD),
        LineChart(
            data={
                "x": [1, 2, 3, 4, 5],
                "系列A": [3, 5, 2, 7, 4],
                "系列B": [4, 6, 3, 8, 5],
                "系列C": [2, 4, 6, 3, 7],
            },
            x="x",
            y=["系列A", "系列B", "系列C"],
            height=280,
            color=["#1f6feb", "#f59e0b", "#ec4899"],
            show_points=True,
        ),
    )


if __name__ == "__main__":
    ft.run(main)
