import os
import sys

# When running this example as a script (python examples/demo.py), the
# script's directory becomes sys.path[0] (examples/). Ensure the project
# root is on sys.path so `from cs_ui import ...` works.
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from cs_ui import (
    App,
    Button,
    Card,
    Checkbox,
    Column,
    Dropdown,
    IconButton,
    Image,
    ProgressBar,
    Row,
    Slider,
    Switch,
    Tabs,
    Text,
    TextField,
)


def main(page):
    card = Card(bgcolor="#ffffff", padding=24, border_radius=16, elevation=4)
    card.add(
        Column(
            Text("CS UI 框架示例", size=24, weight="bold"),
            Text("基于 Flet 风格构建的组件体系。", size=14, color="#333333"),
            TextField(
                label="输入内容",
                hint_text="按回车提交",
                width=320,
                on_submit=lambda e: page.add(
                    Text(f"提交内容：{e.control.value}", color="green")
                ),
            ),
            Dropdown(
                label="选择一项",
                options=["选项一", "选项二", "选项三"],
                value="选项一",
                width=320,
                on_change=lambda e: page.add(Text(f"下拉选择：{e.control.value}")),
            ),
            Slider(
                value=20,
                min_value=0,
                max_value=100,
                divisions=10,
                label="滑块值",
                width=320,
                on_change=lambda e: page.add(Text(f"滑块值：{e.control.value}")),
            ),
            Row(
                Checkbox(
                    label="我已阅读",
                    on_change=lambda e: page.add(Text(f"勾选状态：{e.control.value}")),
                ),
                Switch(
                    label="开关示例",
                    on_change=lambda e: page.add(Text(f"开关状态：{e.control.value}")),
                ),
                spacing=20,
            ),
            ProgressBar(value=60, width=320, color="#4caf50"),
            Row(
                Image(
                    src="https://via.placeholder.com/120",
                    width=120,
                    height=120,
                    border_radius=12,
                ),
                Button(
                    "点我",
                    on_click=lambda e: page.add(Text("按钮已点击!", color="green")),
                    width=120,
                ),
                IconButton(
                    icon="favorite",
                    tooltip="喜欢",
                    on_click=lambda e: page.add(Text("IconButton 点击", color="blue")),
                ),
                spacing=20,
            ),
            Tabs(
                tabs=["首页", "设置", "关于"],
                value="首页",
                on_change=lambda e: page.add(
                    Text(f"当前标签：{e.control.selected_index}")
                ),
                width=320,
            ),
            spacing=16,
        )
    )
    page.add(card)


if __name__ == "__main__":
    App(title="CS UI Demo", on_start=main).run()
