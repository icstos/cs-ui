# CS UI

A Python UI framework built on [Flet](https://flet.dev/), providing a rich set of pre-styled, ready-to-use components with enhanced defaults and a clean package structure.

## Features

- **Batteries included** — `from ui import *` re-exports everything from Flet plus all CS UI components
- **Inheritance-based** — all components directly subclass Flet native controls (e.g., `Button(ft.Button)`, `Text(ft.Text)`)
- **Smart defaults** — components come with sensible styling defaults (colors, sizes, border-radius, etc.) for rapid prototyping
- **Categorized modules** — components organized by function: chart, display, feedback, input, layout, navigation
- **Route system** — built-in `App` class with auto-routing support
- **Charts** — Bar, Line, Area, and Scatter chart wrappers via `flet-charts`

## Requirements

- Python >= 3.13
- flet[all] >= 0.85.2
- flet-code-editor
- flet-charts

## Installation

```bash
uv pip install cs-ui
```

Or install from source in editable mode:

```bash
git clone https://github.com/icstos/cs-ui.git
cd cs-ui
pip install -e .
```

## Quick Start

```python
import flet as ft
from ui import App, Button, Card, Checkbox, Column, Container, Divider, Row, Switch, Text, TextField

def main(page: ft.Page):
    page.title = "CS UI Demo"
    page.bgcolor = "#f8fafc"

    card = Card(
        elevation=4,
        content=Container(
            padding=24,
            border_radius=16,
            content=Column(
                controls=[
                    Text("CS UI 框架示例", size=24, weight="bold"),
                    Text("基于 Flet 风格构建的组件体系。", size=14, color="#6b7280"),
                    Divider(),
                    TextField(
                        label="输入内容",
                        hint_text="按回车提交",
                        width=320,
                    ),
                    Row(
                        controls=[
                            Checkbox(label="我已阅读"),
                            Switch(label="开关示例"),
                        ],
                        spacing=20,
                    ),
                    Button(label="点我", on_click=lambda e: print("clicked!")),
                ],
                spacing=16,
            ),
        ),
    )
    page.add(card)

if __name__ == "__main__":
    ft.app(target=main)
```

## Package Structure

```
src/ui/
├── __init__.py          # re-exports from flet + all subpackages
├── app.py               # App class with routing
├── ft_init.py           # Flet initialization
├── chart/               # Charts
│   ├── bar_chart.py     #   BarChart
│   ├── line_chart.py    #   LineChart
│   ├── rea_chart.py     #   AreaChart
│   └── scatter_chart.py #   ScatterChart
├── core/                # Core utilities
│   ├── config.py
│   ├── constants.py
│   ├── form.py
│   └── language.py
├── data/                # Static assets (fonts, images)
├── display/             # Display components
│   ├── image.py         #   Image
│   ├── image_gridview.py#   ImageGridView
│   ├── list_tile.py     #   ListTile
│   ├── log_container.py #   LogContainer
│   └── text.py          #   Text
├── feedback/            # Feedback & overlays
│   ├── alert_dialog.py  #   AlertDialog
│   ├── loading.py       #   Loading
│   ├── message.py       #   Message
│   ├── progress_bar.py  #   ProgressBar
│   └── toast.py         #   SnackBar (toast)
├── input/               # Form inputs
│   ├── button.py            #   Button
│   ├── checkbox.py          #   Checkbox
│   ├── chip.py              #   Chip
│   ├── color_picker.py      #   ColorPicker
│   ├── date_input.py        #   DateInput
│   ├── datetime_input.py    #   DateTimeInput
│   ├── file_picker.py       #   FilePicker
│   ├── image_picker.py      #   ImagePicker
│   ├── input.py             #   TextField
│   ├── multi_select.py      #   MultiSelect
│   ├── radio.py             #   RadioGroup
│   ├── rating.py            #   Rating
│   ├── search_bar.py        #   SearchBar
│   ├── segmented_button.py  #   SegmentedButton
│   ├── select_box.py        #   Dropdown
│   └── slider.py            #   Slider
│   └── switch.py            #   Switch
├── layout/              # Layout & containers
│   ├── card.py          #   Card
│   ├── column.py        #   Column
│   ├── container.py     #   Container
│   ├── divider.py       #   Divider
│   ├── expander.py      #   Expander
│   ├── grid_view.py     #   GridView
│   ├── list_view.py     #   ListView
│   ├── page.py          #   Page
│   ├── row.py           #   Row
│   ├── stack.py         #   Stack
│   ├── table.py         #   Table
│   ├── tabs.py          #   Tabs
│   ├── time_line.py     #   Timeline
│   └── view.py          #   View
├── navigation/          # Navigation
│   ├── app_bar.py       #   AppBar
│   ├── bread_crumb.py   #   BreadCrumb
│   └── paging.py        #   NavigationBar
└── utils/               # Utilities
    ├── code_editor.py   #   CodeEditor
    ├── code_view.py     #   CodeView
    └── componts.py      #   Helper components
```

## Component Overview

| Category | Components |
|----------|-----------|
| **Chart** | BarChart, LineChart, AreaChart, ScatterChart |
| **Display** | Image, ImageGridView, ListTile, LogContainer, Text |
| **Feedback** | AlertDialog, Loading, Message, ProgressBar, SnackBar |
| **Input** | Button, Checkbox, Chip, ColorPicker, DateInput, DateTimeInput, FilePicker, ImagePicker, TextField, MultiSelect, RadioGroup, Rating, SearchBar, SegmentedButton, Dropdown, Slider, Switch |
| **Layout** | Card, Column, Container, Divider, Expander, GridView, ListView, Page, Row, Stack, Table, Tabs, Timeline, View |
| **Navigation** | AppBar, BreadCrumb, NavigationBar |

## Importing

All components can be imported directly from `ui`:

```python
from ui import App, Button, Card, Column, Container, Divider, Row, Text, TextField
```

Since `ui` re-exports Flet, you can also access Flet types directly:

```python
from ui import ft  # the flet module
# or
from ui import Page, Colors, Icons, MainAxisAlignment, CrossAxisAlignment
```

## Examples

Run the demo to see all components in action:

```bash
python examples/demo.py
```

Additional test files:

- `examples/test_home.py` — minimal home page
- `examples/test_form.py` — form components
- `examples/test_feedback.py` — feedback (dialog, snackbar, loading, progress)
- `examples/test_chart.py` — chart components
- `examples/test_line_chart.py` — line chart
- `examples/test_button.py` — button variants
- `examples/test_minimal.py` / `test_simple.py` — minimal examples
