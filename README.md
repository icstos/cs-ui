# cs_ui

A Python UI framework inspired by Flet. It provides a lightweight component system with a Flet-style API and clear package structure.

## Features

- `App` / `Page` wrapper to manage app lifecycle
- Base `Control` class for custom components
- Built-in controls: `Text`, `Button`, `TextField`, `Checkbox`, `Switch`, `Dropdown`, `RadioGroup`, `Slider`, `Tabs`, `IconButton`, `Image`, `ProgressBar`
- Layouts: `Column`, `Row`
- Container wrapper for composition
- `Card` container for panel-style grouping

## Example

```python
from ui import App, Button, Card, Checkbox, Column, Container, Image, ProgressBar, Row, Switch, Text, TextField


def main(page):
    card = Card(
        bgcolor="#ffffff",
        padding=24,
        border_radius=16,
        elevation=4,
    )
    card.add(
        Column(
            Text("CS UI 框架示例", size=24, weight="bold"),
            Text("基于 Flet 风格构建的组件体系。", size=14),
            TextField(
                label="输入内容",
                hint_text="按回车提交",
                width=320,
                on_submit=lambda e: page.add(Text(f"提交内容：{e.control.value}", color="green")),
            ),
            Row(
                Checkbox(label="我已阅读", on_change=lambda e: page.add(Text(f"勾选状态：{e.control.value}"))),
                Switch(label="开关示例", on_change=lambda e: page.add(Text(f"开关状态：{e.control.value}"))),
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
                spacing=20,
            ),
            spacing=16,
        )
    )
    page.add(card)


if __name__ == "__main__":
    App(title="CS UI Demo", on_start=main).run()
```

## Installation

Install `flet` in your environment before using this package:

```bash
pip install flet
```

To install this project in editable mode and import it as `ui` from the repository root:

```bash
pip install -e .
```

After installation you can import via:

```python
import ui
# or use the original package name if desired
import cs_ui
```

## Package structure

- `cs_ui/app.py` — application entry and page wrapper
- `cs_ui/core/control.py` — base control abstraction
- `cs_ui/controls` — button, text, input, checkbox, switch, dropdown, radio, slider, tabs, icon, image, progress components
- `cs_ui/containers` — container and card wrappers
- `cs_ui/layouts` — row and column layouts
- `examples/demo.py` — demo usage example
