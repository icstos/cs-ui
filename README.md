# CS UI

A Python UI framework built on [Flet](https://flet.dev/), providing a rich set of pre-styled, ready-to-use components with enhanced defaults and a clean package structure.

## Features

- **Batteries included** — `from ui import *` re-exports everything from Flet plus all CS UI components
- **Inheritance-based** — all components directly subclass Flet native controls (e.g., `Button(ft.Button)`, `Text(ft.Text)`)
- **Smart defaults** — components come with sensible styling defaults (colors, sizes, border-radius, etc.) for rapid prototyping
- **Categorized modules** — components organized by function: chart, display, feedback, input, layout, navigation
- **Declarative routing** — root-view routing via `ft.Router(routes, manage_views=False)` + `page.render`
- **Working page overlays** — under the root-view path, `page.overlay` / `page.show_dialog` actually
  render, so the `MultiSelect` dropdown, the `DateInput` calendar, and the `DateTimeInput`
  calendar-plus-time-wheel panel can truly float above the content (a collapsed field is all the layout height the widget takes; opening it never pushes
  the content below)
- **Two component paradigms** — stateless controls subclass native Flet controls; stateful ones are `@ft.observable` objects with a `ui()` renderer
- **Charts** — Bar, Line, Area, and Scatter chart wrappers via `flet-charts`, with both numeric and categorical x-axes
- **Desktop-grade timeline** — `Timeline` supports three alignments (rail on the left / rail on the
  right / alternating around a centered rail); the timestamp can sit in its own column on the
  opposite side (the default, VS Code style), above the title, inline, or be hidden. Dots come with
  semantic colors, three variants (filled / outlined / plain) and three sizes; `done` turns into a
  check mark automatically and `pending` appends an "in progress" hollow ring. Rows are clickable
  end to end — hover highlight and click ripple are painted by Material's `ink`, so nothing is
  re-rendered from Python and long lists stay smooth

## Requirements

- Python >= 3.12
- flet[all] >= 1.0.0
- flet-code-editor
- flet-charts
- flet-video / flet-audio / flet-webview

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
from ui import (
    Button,
    Card,
    Checkbox,
    Column,
    Container,
    Divider,
    Input,
    Router,
    Route,
    Row,
    Text,
)


@ft.component
def HomePage() -> ft.Control:
    name = ft.use_ref(lambda: Input(label="Name", value="Shawn", width=260)).current
    agree = ft.use_ref(lambda: Checkbox(label="I have read the terms")).current

    # Pages return plain controls and draw their own top bar — see the notes below
    return Container(
        expand=True,
        content=Column(
            spacing=0,
            controls=[
                Container(
                    height=56,
                    bgcolor=ft.Colors.WHITE,
                    padding=ft.Padding.symmetric(horizontal=14),
                    content=Row(
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[Text("CS UI Demo", size=17, weight=ft.FontWeight.W_600)],
                    ),
                ),
                Card(
                    elevation=4,
                    content=Container(
                        padding=24,
                        border_radius=16,
                        content=Column(
                            controls=[
                                Text("CS UI declarative demo", size=24, weight=ft.FontWeight.BOLD),
                                Text("Built on flet 1.0.0.", size=14, color="#6b7280"),
                                Divider(),
                                name.ui(),
                                Row(
                                    spacing=20,
                                    controls=[agree.ui(), ft.Switch(label="A switch")],
                                ),
                                Button("Click me", on_click=lambda _: print("clicked!")),
                            ],
                            spacing=16,
                        ),
                    ),
                ),
            ],
        ),
    )


@ft.component
def App() -> ft.Control:
    return Router([Route(index=True, component=HomePage)], manage_views=False)


def main(page: ft.Page) -> None:
    page.title = "CS UI Demo"
    page.render(App)


if __name__ == "__main__":
    ft.run(main)
```

> **Render path: use `page.render` + `Router(manage_views=False)`, not `page.render_views`.**
>
> Two pitfalls we hit for real:
>
> 1. `page.render_views` (the view stack behind `Router(manage_views=True)`) **covers the entire page
>    overlay layer** — anything appended to `page.overlay` renders zero pixels, and `page.show_dialog`
>    is just as dead. It does **not** raise: `len(page.overlay)` is correct and callbacks still fire.
>    Floating `MultiSelect` panels, toasts and dialogs all silently break.
> 2. **`ft.View` cannot be used as an ordinary control.** Under the root-view path, putting a `View`
>    into the widget tree makes Flutter throw `Bad state: No element` on repeat and the whole page
>    turns into a grey box. Likewise `ft.AppBar` is an `AdaptiveControl`: it only fits `View.appbar`
>    and cannot go into `Column.controls` — draw the top bar with `Container` + `Row` instead.
>
> Migration notes: `ft.app(main)` → `ft.run(main)`; `page.add(...)` → `page.render(Component)`;
> `page.go(route)` → `page.navigate(route)`; hand-maintained `page.views` →
> `ft.Router(routes, manage_views=False)`. The bundled `ui.Button` takes its text as `content` (not `label`).
>
> Components come in two flavors: **stateless controls** (`Button` / `Table` / `Rating` …) subclass
> Flet controls and are usable immediately; **stateful components** (`Input` / `Checkbox` / `Switch` /
> `SelectBox` / `MultiSelect` …) are `@ft.observable` data objects that must be constructed and then
> rendered via `.ui()` — putting the object itself in the widget tree yields a blank or grey box.
>
> If the host app has to keep the view stack (`manage_views=True`), `MultiSelect` automatically
> degrades to **in-flow expansion** (the panel takes layout height and pushes content down); pass
> `float_panel=False` to opt out of the overlay explicitly.

## Package Structure

```
src/ui/
├── __init__.py              # re-exports all of flet + every CS UI component (617 names)
├── app.py                   # legacy-style App entry point
├── ft_init.py               # Flet initialization
├── theme.py                 # theme / palette
├── cli.py                   # CLI entry point
├── chart/                   # Charts (via flet-charts)
│   ├── _data.py             #   shared data parsing + palette (numeric / categorical axes)
│   ├── bar_chart.py         #   BarChart
│   ├── line_chart.py        #   LineChart
│   ├── rea_chart.py         #   AreaChart
│   └── scatter_chart.py     #   ScatterChart
├── components/              # Reusable generic controls
│   └── icon_button.py       #   IconButton
├── core/                    # Core utilities
│   ├── config.py            #   configuration
│   ├── constants.py         #   StyleType / FeedbackStyle / ButtonShape …
│   ├── float_layer.py       #   page overlay: overlay_usable / use_float_layer
│   ├── language.py          #   i18n
│   ├── logger.py            #   logging
│   ├── snackbar.py          #   content guard for SnackBar-based components
│   └── styles.py            #   shared style helpers
├── data/                    # Static assets (fonts, images)
├── display/                 # Display components
│   ├── echarts.py           #   ECharts (embedded WebView)
│   ├── image.py             #   Image
│   ├── image_gridview.py    #   ImageGridView
│   ├── list_tile.py         #   ListTile
│   ├── log_container.py     #   LogContainer
│   ├── text.py              #   Text / Header_1..5 / Quote / Link / Code / Markdown / Json
│   └── media/               #   Media
│       ├── audio.py         #     Audio / AudioPlayer
│       ├── pdf.py           #     Pdf
│       └── video.py         #     Video
├── feedback/                # Feedback & overlays
│   ├── alert_dialog.py      #   AlertDialog
│   ├── loading.py           #   Loading
│   ├── message.py           #   Message
│   ├── progress_bar.py      #   ProgressBar
│   └── toast.py             #   Toast / toast_success / toast_error …
├── input/                   # Form inputs
│   ├── button.py            #   Button
│   ├── checkbox.py          #   Checkbox / CheckboxGroup
│   ├── chip.py              #   Chip
│   ├── color_picker.py      #   ColorPicker
│   ├── date_input.py        #   DateInput
│   ├── datetime_input.py    #   DateTimeInput
│   ├── file_picker.py       #   FilePicker / DirPicker
│   ├── image_picker.py      #   ImagePicker
│   ├── input.py             #   Input (data_type: str/int/float/file/dir)
│   ├── multi_select.py      #   MultiSelect
│   ├── radio.py             #   RadioGroup
│   ├── rating.py            #   Rating
│   ├── search_bar.py        #   SearchBar
│   ├── segmented_button.py  #   SegmentedButton
│   ├── select_box.py        #   SelectBox
│   ├── slider.py            #   Slider
│   └── switch.py            #   Switch
├── layout/                  # Layout & containers
│   ├── card.py              #   Card
│   ├── column.py            #   Column
│   ├── container.py         #   Container
│   ├── divider.py           #   Divider
│   ├── expander.py          #   Expander
│   ├── grid_view.py         #   GridView
│   ├── list_view.py         #   ListView
│   ├── page.py              #   PageLayout
│   ├── row.py               #   Row
│   ├── stack.py             #   Stack
│   ├── table.py             #   Table (with paging)
│   ├── tabs.py              #   Tabs / Tab / TabBar / TabBarView
│   ├── time_line.py         #   Timeline / TimelineItem
│   └── view.py              #   View
├── navigation/              # Navigation
│   ├── app_bar.py           #   AppBar
│   ├── bread_crumb.py       #   BreadCrumb / Crumb
│   └── paging.py            #   Paging / PagingState
└── utils/                   # Utilities
    ├── code_editor.py       #   Code
    ├── code_view.py         #   CodeView
    └── componts.py          #   Helper components
```

## Component Overview

| Category | Components |
|----------|-----------|
| **Chart** | BarChart, LineChart, AreaChart, ScatterChart |
| **Display** | ECharts, Image, ImageGridView, ListTile, LogContainer, Text / Header_1..5 / Quote / Link / Code / Markdown / Json |
| **Display / Media** | Audio, AudioPlayer, Video, Pdf |
| **Feedback** | AlertDialog, Loading, Message, ProgressBar, Toast |
| **Input** | Button, Checkbox / CheckboxGroup, Chip, ColorPicker, DateInput, DateTimeInput, FilePicker / DirPicker, ImagePicker, Input, MultiSelect, RadioGroup, Rating, SearchBar, SegmentedButton, SelectBox, Slider, Switch |
| **Layout** | Card, Column, Container, Divider, Expander, GridView, ListView, PageLayout, Row, Stack, Table, Tabs, Timeline, View |
| **Navigation** | AppBar, BreadCrumb, Paging |

**Two paradigms**:
- **Stateless controls** (`Button` / `Table` / `ECharts` / `Rating` / `Timeline` / charts …) subclass Flet controls and are ready to use.
- **Stateful components** (`Input` / `Checkbox` / `Switch` / `SelectBox` / `MultiSelect` …) are `@ft.observable` data objects; construct them and render with `.ui()`.

## Importing

All components can be imported directly from `ui`:

```python
from ui import Button, Card, Column, Container, Divider, Row, Text, TextField
```

Since `ui` re-exports Flet, you can also access Flet types directly:

```python
from ui import ft  # the flet module

# or
from ui import Page, Colors, Icons, MainAxisAlignment, CrossAxisAlignment
```

## Examples

Run the demo to see every component in action (11 category pages plus a 404 page):

```bash
python examples/demo.py
```

| Route | Contents |
|-------|----------|
| `/` | Home navigation (enter each category) |
| `/general` | Text / buttons / icons / chips |
| `/layout` | Containers / lists / tables / timeline |
| `/navigation` | Breadcrumb / tabs / paging |
| `/form` | Inputs / selectors / slider / rating |
| `/upload` | Files / directories / save / images |
| `/feedback` | Toast / message / dialog / progress |
| `/display` | Logs / code / ECharts / images |
| `/charts` | Line / area / bar / scatter charts |
| `/media` | Audio / video / PDF |
| `/about` | Migration cheat-sheet and design notes |

Additional test files:

- `examples/test_home.py` — minimal home page
- `examples/test_form.py` — form components
- `examples/test_feedback.py` — feedback (dialog, snackbar, loading, progress)
- `examples/test_chart.py` — chart components
- `examples/test_line_chart.py` — line chart
- `examples/test_button.py` — button variants
- `examples/test_minimal.py` / `test_simple.py` — minimal examples
- `examples/my_control.py` — custom control example
