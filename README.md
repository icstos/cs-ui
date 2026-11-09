# CS UI

A Python UI framework built on [Flet](https://flet.dev/), providing a rich set of pre-styled, ready-to-use components with enhanced defaults and a clean package structure.

## Features

- **Batteries included** — `from ui import *` re-exports everything from Flet plus all CS UI components
- **Consistent interaction states** — hover / selected / disabled are three token-backed
  levels (`state_layer` / `selected_layer` / `disabled_layer`, 8% / 12% / 38%–12%): the same
  "glide over it" reads the same weight in menus, paging, calendars and transfer lists
- **Body text is 14px everywhere** — one token (`FONT_SIZE["body"]`) feeds all thirteen
  `text_theme` slots, so a bare `ft.Text`, `ListTile`, `TextField`, `Dropdown` and
  `DatePicker` all default to 14 instead of Flutter's own `bodyMedium`. Bumping flet
  can't silently drift it. Other steps: 11 / 12 / 16 / 20 / 24 / 28 / 36, at least 2px apart
- **Design tokens + Material 3 theming** — no raw color / radius / font-size literals inside
  components. A single brand color is turned into all 46 M3 roles by `ui.core.palette`
  (one set for light, one for dark; change the brand and the whole set changes) instead of
  being handed to Flutter's `tonalSpot`, which turns `#1F6FEB` into `#465D91` and strips half
  the chroma out of the brand blue. Light/dark and brand-color switching are **framework-level**
  operations, not per-widget recoloring
- **One palette, five layers** — surface / foreground / interaction / accent / data, each with a
  single means of expression. Buttons, messages, badges and log levels share one accent vocabulary
  (`accent_*`): a success button and a success toast are the same green, and a primary button's fill
  is M3's `PRIMARY`, following the seed. Chart series and heat-map scales are derived from the brand
  seed in OKLCH (equal lightness, evenly spaced hues) instead of eight hand-picked hex values
- **Colors are computed, not picked** — every hue unrolls into an 11-step scale (lightness on a
  logarithmic gradient, ~0.075 apart, matching human Weber-law perception) with a bell-shaped
  chroma envelope: the pale end stays pale *and* tinted, the deep end stays deep *without* turning
  muddy, and the hue never drifts by a degree. Foregrounds aren't sampled at a fixed step — the
  lightness is **solved against a contrast ratio** (bisection; body text ≥ 4.5:1, large headings
  ≥ 3:1), so `success` and `warning` — two hues whose lightness is worlds apart — land on paper at
  the same visual weight. Neutrals carry a 215° cool-blue cast plus a trace of the brand hue, so
  they read as slate rather than dead grey with three equal channels
- **Inheritance-based** — static components subclass Flet native controls (e.g., `Button(ft.Button)`, `Text(ft.Text)`)
- **Smart defaults** — components come with sensible styling defaults (colors, sizes, border-radius, etc.) for rapid prototyping
- **Categorized modules** — components organized by function: chart, display, feedback, input, layout, navigation
- **Declarative routing** — root-view routing via `ft.Router(routes, manage_views=False)` + `page.render`
- **Working page overlays** — under the root-view path, `page.overlay` / `page.show_dialog` actually
  render, so the `MultiSelect` dropdown, the `DateInput` calendar, and the `DateTimeInput`
  calendar-plus-time-wheel panel can truly float above the content (a collapsed field is all the layout height the widget takes; opening it never pushes
  the content below)
- **Two component paradigms** — static components subclass native Flet controls; interactive ones are
  `@ft.component` functions whose state is declared with hooks (`use_state` / `use_memo` / `use_effect`)
- **Charts** — Bar, Line, Area, and Scatter chart wrappers via `flet-charts`, with both numeric and categorical x-axes
- **One date picker, nine modes** — `DateInput` covers the whole Element-style family:
  `date` / `week` / `month` / `year`, the three multi-select flavours (`dates` / `months` / `years`),
  and `daterange` / `monthrange`. They all share one calendar: a cell's look is a single
  `DayMark` (filled dot, range band, today, disabled, out-of-month), so "pick many" and "pick a
  range" are not separate widgets — just different marks on the same grid. Click the title to
  zoom out a level (day → month → year) instead of paging twelve times. Ranges lay out two
  panels side by side, left early right late, and the connector band previews to wherever the
  pointer is after the first click. Values stay plain `datetime.date` (a month is its 1st, a
  year is Jan 1) — no extra type to learn
- **A year at a glance** — `Heatmap` lays dates out as one column per week, seven rows per week,
  and the deeper the colour the busier the day. The sequential ramp ships a light and a dark set
  (M3 roles can’t express “the third green”), while the empty-cell base colour stays a theme role,
  so light/dark needs no special case. The whole grid carries **one** gesture detector and maps the
  pointer to a cell by division; hover repaints only when the cell changes and the grid itself is
  built once — moving the mouse swaps a tooltip, not 371 cells
- **A month as a working surface** — `Calendar` is the full-panel counterpart to the date picker.
  Cells are large enough to hold a second line (`cell_content`), the title zooms out to twelve
  months instead of paging, and selection / today / hover live inside a 30px pill so a wide cell
  never turns into a block of colour. Clicking a greyed neighbouring day jumps to that month —
  the grid is always exactly 42 cells, so the panel never changes height when you page
- **Slides that slide** — `Carousel` puts N controls in one box and moves them one slot at a
  time, so the edge of the next slide stays visible and the user knows which way to flip. Arrows
  fade in on hover and are genuinely unclickable until then; dots switch from white-on-image to
  theme roles when they sit outside. Autoplay pauses while the pointer rests, width is measured
  after mount instead of being passed in, and looping wraps with a single instant step — cloning
  a slide is not possible when a control can only have one parent
- **Fields on a grid that lines up** — `Descriptions` lays a record out as a bordered grid by
  default: tinted label cells, hairline dividers, one rounded frame. `column` sets how many fields
  per row and `span` lets long values (addresses, notes) take two; if the last row runs short the
  final field absorbs the remainder instead of leaving a hole. Switch to `direction="vertical"`
  for label-above-value cards, or `bordered=False` to skip the frame and get a lightweight aligned
  layout. Column widths come from flex weights, so nothing is measured and resizing is free
- **Steps that show progress** — `Step` models a flow as a state machine: every step is
  `wait` / `process` / `finish` / `error`, derived from `active` or pinned per step. Connectors tint
  only the segments already walked, so progress reads from colour alone. Lay it out horizontally,
  as a vertical rail, or collapse it into a one-line `simple` strip that jumps on click. Click
  feedback is immediate — the component rebuilds itself in place, and `on_change(index)` keeps the
  caller in charge

## Requirements

- Python >= 3.12
- flet[all] >= 1.1.2, < 1.2
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
                                Text("Built on flet 1.1.2.", size=14, color="#6b7280"),
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
>    Floating `MultiSelect` panels, notifications and dialogs all silently break.
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
├── __init__.py              # re-exports all of flet + every CS UI component (711 names)
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
│   ├── format.py            #   locale-aware date / number formatting
│   ├── i18n.py              #   i18n: I18nProvider / LanguageSwitcher / use_t / t
│   ├── locales.py           #   bundled zh_CN / zh_TW / en_US dictionaries
│   ├── logger.py            #   logging
│   ├── styles.py            #   shared style helpers
│   ├── theme.py             #   ThemeProvider / ThemeSwitcher / use_theme
│   └── tokens.py            #   design tokens: SPACE / RADIUS / FONT_SIZE / semantic colors
├── data/                    # Static assets (fonts, images)
├── display/                 # Display components
│   ├── calendar.py          #   Calendar (month panel, year zoom, per-cell content)
│   ├── carousel.py          #   Carousel (slide strip, hover arrows, dots, autoplay)
│   ├── descriptions.py      #   Descriptions / DescriptionsItem
│   ├── heatmap.py           #   Heatmap / HeatmapItem (calendar heatmap)
│   ├── image.py             #   Image
│   ├── image_gridview.py    #   ImageGridView
│   ├── list_tile.py         #   ListTile
│   ├── log_container.py     #   LogContainer
│   ├── text.py              #   Text / Header_1..5 / Quote / Link / Code / Markdown / Json
│   ├── tree.py             #   Tree / TreeNode (expand / check / filter)
│   └── media/               #   Media
│       ├── audio.py         #     Audio / AudioPlayer
│       ├── pdf.py           #     Pdf
│       └── video.py         #     Video
├── feedback/                # Feedback & overlays
│   ├── _look.py             #   shared type → icon / accent mapping
│   ├── _overlay.py          #   overlay card stack (anchor, timing, grouping, hover-pause)
│   ├── alert_dialog.py      #   AlertDialog
│   ├── loading.py           #   Loading
│   ├── message.py           #   Message (top-centre receipt for user actions)
│   ├── notification.py      #   Notification (corner card with title, system-level)
│   └── progress_bar.py      #   ProgressBar
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
│   ├── number_input.py      #   NumberInput (step / precision / range / unit)
│   ├── cascader.py          #   Cascader / CascaderNode (multi-column cascading picker)
│   ├── radio.py             #   RadioGroup
│   ├── rating.py            #   Rating
│   ├── search_bar.py        #   SearchBar
│   ├── segmented_button.py  #   SegmentedButton
│   ├── select_box.py        #   SelectBox
│   ├── slider.py            #   Slider
│   ├── switch.py            #   Switch
│   └── transfer.py          #   Transfer / TransferItem (two-column shuttling)
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
│   ├── table.py             #   Table (with pagination)
│   ├── tabs.py              #   Tabs / Tab / TabBar / TabBarView
│   ├── step.py              #   Step / StepItem
│   └── view.py              #   View
├── navigation/              # Navigation
│   ├── app_bar.py           #   AppBar
│   ├── bread_crumb.py       #   BreadCrumb / Crumb
│   ├── menu.py              #   Menu / MenuItem / MenuGroup
│   └── pagination.py        #   Pagination / PaginationState
└── utils/                   # Utilities
    ├── code_editor.py       #   Code
    ├── code_view.py         #   CodeView
    └── componts.py          #   Helper components
```

## Component Overview

| Category | Components |
|----------|-----------|
| **Core** | ThemeProvider, ThemeSwitcher, `use_theme`, `theme_state` |
| **Chart** | BarChart, LineChart, AreaChart, ScatterChart |
| **Display** | Calendar, Carousel, Descriptions, Heatmap, Image, ImageGridView, ListTile, LogContainer, Tree, Text / Header_1..5 / Quote / Link / Code / Markdown / Json |
| **Display / Media** | Audio, AudioPlayer, Video, Pdf |
| **Feedback** | AlertDialog, Loading, Message, Notification, ProgressBar |
| **Input** | Button, Checkbox / CheckboxGroup, Chip, ColorPicker, DateInput, DateTimeInput, FilePicker / DirPicker, ImagePicker, Input, MultiSelect, NumberInput, RadioGroup, Rating, SearchBar, SegmentedButton, SelectBox, Slider, Switch, Transfer, Cascader |
| **Layout** | Card, Column, Container, Divider, Expander, GridView, ListView, PageLayout, Row, Stack, Step, Table, Tabs, View |
| **Navigation** | AppBar, BreadCrumb, Menu, Pagination |

**Two paradigms**:
- **Static components** (`Button` / `Table` / `Rating` / `Step` / charts …) subclass Flet controls and are ready to use.
- **Interactive components** (`Input` / `Checkbox` / `Switch` / `SelectBox` / `MultiSelect` / `Pdf` …) are
  `@ft.component` functions; their state is declared with hooks and the return value goes straight into the tree.

## Design Tokens and Theming

Components never contain raw color / radius / font-size literals — everything comes from
`ui.core.tokens`. Switching theme and brand color is therefore a **framework-level**
operation rather than per-widget recoloring.

### Apply a theme

Wrap the root view in `ThemeProvider`; `build` returns your router:

```python
import flet as ft
from ui import ThemeProvider

def App() -> ft.Control:
    return ThemeProvider(
        build=lambda: ft.Router(ROUTES, not_found=NotFoundPage, manage_views=False)
    )

def main(page: ft.Page):
    page.render(App)
```

`ThemeProvider` builds the subtree with `use_memo(build, [])` — **switching the theme does not
rebuild the widget tree**, so values already typed into a form survive the switch
(verified on a real device: after switching to dark, the `use_state` value is intact).

### Light/dark and brand color

```python
from ui import use_theme, ThemeSwitcher, PRIMARY_SEEDS

@ft.component
def TopBar() -> ft.Control:
    state = use_theme()                    # subscribe (must be called inside a component)
    ft.Button("toggle", on_click=lambda e: state.toggle_mode())
    ft.Button("recolor", on_click=lambda e: state.set_primary(PRIMARY_SEEDS["violet"]))
```

`ThemeSwitcher` is a ready-made top-bar control (brand palette + light/dark switch).
`ThemeState` exposes three distinct behaviors:

| Method | Behavior |
|--------|----------|
| `toggle_mode()` | always jump to the opposite of what is **currently visible** (for a ☀/🌙 button, so a click always shows a change) |
| `cycle_mode()` | `system → light → dark → system` (for a dropdown) |
| `set_mode(name)` | go straight to a mode; `"system"` follows the platform brightness |
| `set_primary(hex)` | swap the brand color: all 46 roles are recomputed and both light and dark are handed down |

### Tokens

**Theme-aware tokens** are `ft.Colors` role names resolved by Flutter at paint time, so a theme
switch costs **zero Python re-renders**:

```python
ft.Colors.PRIMARY, ft.Colors.SURFACE_CONTAINER_LOWEST, ft.Colors.ON_SURFACE_VARIANT
```

**Framework-resolved tokens** cover the semantic roles M3 does not ship (`ui.core.tokens`):

```python
from ui import (
    SPACE, RADIUS, FONT_SIZE, GAP, PAD, elevation, hairline,
    state_layer, selected_layer, disabled_layer, overlay,
)

SPACE["4"]                  # 16 — a 4pt scale: (0,1,2,3,4,5,6,8,10,12,16,20,24,32,40)
RADIUS["lg"]                # 8
FONT_SIZE["body"]           # 14 — the body baseline, also TextTheme.bodyMedium
                            #      other steps: 11 / 12 / 16 / 20 / 24 / 28 / 36
elevation(2)                # five shadow levels, tinted with the 'shadow' role so it follows light/dark
state_layer("hover")        # 'onsurface,0.08' — hover surface (M3 hover level)
selected_layer("normal")    # 'primary,0.12' — selected surface
disabled_layer()            # 'onsurface,0.38' — disabled text / icons
disabled_layer("container") # 'onsurface,0.12' — disabled control fill / border
hairline()                  # 1px divider
```

**Semantic colors come in three tiers** — one value cannot serve every use:

| Function | Use | Light | Dark |
|----------|-----|-------|------|
| `semantic("success")` | solid fill (badge background, status dot, progress segment) | `#007F5B` | `#38B98B` |
| `on_semantic("success")` | foreground on that fill | `#FFFFFF` | `#002014` |
| `semantic_text("success")` | text / icons / hairlines on the page | `#007F5B` | `#38B98B` |

Why: measured WCAG contrast, the hand-picked `#10B981` of earlier days is only **2.54:1** on
white and `#F59E0B` only **2.15:1** — white text on them is equally unreadable at 2.54 / 2.15.
These values are no longer hand-picked: `ui.core.palette` **solves each semantic color to the
same contrast target** (5.0:1 against white in light mode, 7.0:1 against the dark surface), so all
four fills land at the same visual weight (lightness spread < 0.02) and "info" never reads lighter
than "warning". In dark mode the foreground is **dark ink**, not white — `#F28948` under white is
2.0:1, under dark ink it is 7.0:1, and the dark page stops glaring.

**Available roles**: `success` / `warning` / `danger` / `info` / `neutral`.

**The accent quartet** is the entry point components should use. One accent has four
uses, and the four values cannot be the same:

| Function | Use |
|----------|-----|
| `accent_fill(role)` | solid fill (primary button, badge, progress segment) — deep enough to carry `on` |
| `accent_on(role)` | foreground on that fill (button label, badge icon) |
| `accent_text(role)` | text / icons sitting on a **surface** (outlined button, banner title) |
| `accent_soft(role)` | 12% tint for **small** areas (icon chips, count badges) |
| `accent_wash(role)` | 8% tint for **large** areas (dialog title band, full-width banner) |

`role` is `primary` / `secondary` / `tertiary` (M3 roles, resolved by Flutter at paint
time, so brand/theme switches cost no rebuild) or `success` / `warning` / `danger` /
`info` / `neutral` (framework semantic roles). Buttons, messages, notifications,
dialogs and log levels all go through this one vocabulary — a success button and a
success toast are literally the same green, and a primary button's fill is M3's
`PRIMARY` (it follows the seed instead of hard-coding `Colors.BLUE`). The tint comes in
two levels by **area**: at equal opacity, a larger patch reads heavier.

**Where the palette comes from.** `ui.core.palette` turns one brand color into all 46 M3 roles;
`build_theme(state, mode)` hands them down via `ft.ColorScheme(**build_scheme(...))`, one set per
mode, computed once at startup. It deliberately does not use `color_scheme_seed`, because Flutter's
`tonalSpot` maps the brand color onto tone 40 and drops its chroma — `#1F6FEB` comes back as
`#465D91`, half the blue gone. A design asset should not be edited like that.

```python
from ui.core.palette import build_scheme, tonal, neutral, semantic_scale

build_scheme("#1F6FEB", "light")   # all 46 roles in one call
tonal("#1F6FEB")[50]               # '#F4F8FF' — the 11-step scale (50…950)
tonal("#1F6FEB")[600]              # '#3271D7'
```

Three rules hold it up. Lightness is laid out on a **logarithmic gradient** across eleven steps
(~0.075 apart, matching Weber's law), so "one step lighter" means the same thing on every hue.
Chroma follows a **bell envelope** (0.10 at step 50 → 1.00 at 500 → 0.50 at 950): the pale end
stays pale *and* tinted, the deep end stays deep *without* going muddy. Foregrounds are
**solved against a contrast ratio** (16 bisection steps) rather than sampled at a fixed step —
yellow and blue at the same tone differ in relative luminance by 3×, so equal tone has never
meant equal readability.

Neutrals are not dead grey with three equal channels: a 215° cool-blue cast plus a trace of the
brand hue (what the `SURFACES` switch controls). Slate looks refined precisely because it leans
slightly, and the whole ramp re-harmonizes when the brand color changes.

**Color is layered, not a palette.** Five layers, one means of expression each — do not
borrow across layers:

| Layer | What to use | Resolved by |
|-------|-------------|-------------|
| Surface | `SURFACE` / `SURFACE_CONTAINER_LOWEST..HIGHEST` | Flutter |
| Foreground | `ON_SURFACE` / `ON_SURFACE_VARIANT` / `OUTLINE` / `OUTLINE_VARIANT` | Flutter |
| Interaction | `state_layer()` / `selected_layer()` / `disabled_layer()` | Flutter |
| Accent | `accent_fill/on/text/soft/wash()` (primary + five semantic roles) | mixed |
| Data | `chart_palette()`, heat-map scales (derived by `ui.core.color`) | Python |

Categorical chart colors are derived from the brand seed in **OKLCH**: series 1 shares the
brand hue, the whole table has equal lightness (so no series looks more important), and
hues are 45° apart (adjacent lines stay distinguishable). Change the seed and the charts
change with it — there is no second, hand-picked set of eight hex values. Heat maps work
the same way: four levels move only in lightness and the top level lands exactly on the
brand palette's anchor, so the hottest cell is the same green as a success badge.

### One important trap

In flet 1.x, **reading a field of an observable does not subscribe to it**. Subscription only
happens in three places: the component argument is an `Observable`, `use_state`, or `use_context`.

```python
state = theme_state()
mode = state.mode          # ❌ just a read; nothing re-renders
state = use_theme()        # ✅ use_context(theme_context); flet attaches the subscription
```

Relatedly, theme-aware role names and Python-computed colors have very different costs: role
names are resolved by Flutter (free on theme switch), whereas a hex computed by
`semantic("success")` only updates if the component itself subscribed to the theme.

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

### Import cost is lazy

`import ui` only loads `flet` itself (~0.2 s); components are imported from their
subpackage the first time they are touched. Eager star-imports were measured at
**1.4 s** for the same `import ui` — `ui.chart` alone drags in matplotlib + plotly
(~0.62 s) and `ft_init`'s 536 attribute reflections cost ~0.59 s.

```python
import ui              # ~0.2 s
ui.Container           # ~35 ms — imports ui.layout once
ui.BarChart            # imports ui.chart (matplotlib) only because it is used
```

`dir(ui)` still returns every name, so IDE completion and `from ui import *` behave
as before (the star-import deliberately pays for everything). The
name → subpackage table lives in `src/ui/_registry.py` and is generated:

```bash
python scripts/gen_ui_registry.py           # regenerate after adding components
python scripts/gen_ui_registry.py --check   # verify it hasn't drifted
```

### Run every regression in one command

Consistency does not survive "remember to run it", so all checks live behind one entry point:

```bash
python scripts/check_all.py                 # 27 checks / ~51 s (static gate + audit + logic + docs)
python scripts/check_all.py --stage fast    # static gate + token audit only (enough when restyling)
python scripts/check_all.py --stage visual  # real-window screenshots + grey-block detection (minutes)
```

| Check | What it protects |
|---|---|
| `ruff --select F821,F811,F841` | undefined names / redefinitions / unused locals (a missing token import surfaces here) |
| `audit_consistency.py` | raw colors, off-scale font / icon / radius, odd spacing, `OUTLINE` as text color, dark-hostile fills, Material's static palette names (`Colors.GREEN`, `RED_500`) |
| `_tokens_logic.py` | token contract: facade parity, monotonic scales, state-layer progression, safe fallbacks, single-source constants, interaction values, the accent quartet staying in sync with `SEMANTIC` |
| `_palette_logic.py` | palette contract: all 46 roles present, 11 steps at even lightness with a stable hue, 17 foreground/background pairs clearing their contrast target (across 8 seeds × 2 modes), structural ramp moving one way, four semantic fills at the same weight, bad seeds falling back instead of raising |
| `_color_logic.py` | color engine: OKLCH round-trip, equal-lightness series, hue spacing, monotonic scales, safe fallbacks |
| `_*_logic.py` | per-component logic (state derivation, clamping, callbacks) |
| `_doc_check.py` | SPEC / examples / API completeness for all 71 components |
| `gen_ui_registry.py --check` | `ui.__all__` vs registry drift |
| `build_docs_i18n.py --check` | site copy in sync across three languages |

## Examples

The component documentation site *is* the example library: all 71 components ship
runnable examples plus API notes, one route per page.

```bash
python docs/main.py
```

| Route | Contents |
|-------|----------|
| `/` | Home |
| `/docs/quickstart` `/docs/architecture` `/docs/theming` `/docs/i18n` | Guide articles |
| `/components` | Overview (general / layout / navigation / form / display / feedback / chart / media) |
| `/components/<group>/<component>` | One component: definition / composition / when to use / examples / API / notes |
| `/about` | About |

When you changed styling and want proof it actually rendered (a grey block means a
Flutter-side render failure; yellow stripes mean text outgrew its fixed-height box):

```bash
python scripts/_visual_check.py                      # 13 representative pages, light
python scripts/_visual_check.py --mode dark          # dark theme
python scripts/_visual_check.py --scroll 14 \
    --routes /components/layout/table                # scroll into the examples first
```

Additional test files:

- `examples/test_home.py` — minimal home page
- `examples/test_form.py` — form components
- `examples/test_feedback.py` — feedback (message, notification, dialog, loading, progress)
- `examples/test_chart.py` — chart components
- `examples/test_line_chart.py` — line chart
- `examples/test_button.py` — button variants
- `examples/test_minimal.py` / `test_simple.py` — minimal examples
- `examples/my_control.py` — custom control example

## MCP server (`ui-mcp`)

An MCP server that gives AI agents *version-accurate* knowledge of this component
library — same idea as [flet-mcp](https://flet.dev/docs/cookbook/flet-mcp/), but for
`ui`. The index is built by **runtime introspection** (`@ft.control` flattens the
constructor and `@ft.observable` creates proxy classes, so a static scan would miss
the real signatures) and shipped as JSON; the server never imports `ui`.

```bash
pip install -e ".[mcp]"
ui-mcp            # stdio server (default subcommand)
ui-mcp build      # rebuild the index after changing src/ui
ui-mcp check      # is the index older than the sources?
ui-mcp guide      # list the curated "gotchas" topics
```

Client config:

```json
{ "mcpServers": { "ui": { "command": "ui-mcp" } } }
```

12 tools in five groups (`UI_MCP_ENABLE_{API,ICONS,EXAMPLES,DOCS,GUIDE}`):
`get_api` (primary verifier, walks base classes), `list_components`,
`search_components` (Chinese + English), enum tools, `find_icon`,
`search_examples` / `get_example` (real demo code, with per-component call sites),
`search_docs` / `get_doc`, and `get_guidelines` — the paradigm rules that no API
lookup can tell you (frozen trees, `page.render`, `#AARRGGBB` colors, design tokens).

> Adding a component? Add one line to `src/ui_mcp/aliases.py` so Chinese queries find
> it, then run `ui-mcp build`.
