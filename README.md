# CS UI

[![Flet](https://img.shields.io/badge/Flet-1.1.2-blue)](https://flet.dev)
[![Python](https://img.shields.io/badge/Python-3.12%2B-green)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

A component library for [Flet](https://flet.dev/): 72 components, a computed palette, and a
typographic law.

## Features

- **Colors are computed, not picked** — one brand color expands into 46 M3 roles (a set for light,
  a set for dark) in `ui.core.palette`. It does not go through `color_scheme_seed`: Flutter's
  `tonalSpot` turns `#1F6FEB` into `#465D91` and strips half the chroma out of the brand blue.
- **Foregrounds are solved against contrast, not sampled by step** — 11 scale steps on a
  logarithmic lightness gradient; foreground lightness found by bisection (body ≥ 4.5:1,
  large headings ≥ 3:1). So `success` and `warning` — two hues worlds apart in lightness — land
  on paper at the same visual weight.
- **Typography is a law, not a pile of numbers** — the size (11 / 12 / 14 / 16 / 20 / 24 / 28 / 36)
  derives the other three: leading `φ − 0.018 × (size − 14)`, tracking as an optical correction in
  em, weight in four steps. Components never pass `height=` or `letter_spacing=`; the four travel
  together.
- **Spacing snaps to a 4px grid, leading does not** — `RHYTHM` (4 / 8 / 12 / 20 / 32 / 52, adjacent
  ratios 1.4–2.1, hugging φ) governs the space between blocks. Body leading is 22.65px; snapping it
  to 20 or 24 misses φ by a whole step.
- **Responsive repaints only on class change** — six breakpoints (0 / 576 / 768 / 992 / 1200 / 1400,
  identical to `ResponsiveRow`) collapse into compact / medium / expanded. The exact width lives in
  an immutable `Viewport` snapshot; updating it triggers no repaint, so dragging a window does not
  turn the UI into a slideshow.
- **One palette, five layers** — surface / foreground / interaction / accent / data, each with a
  single means of expression, never borrowed across layers. A success button and a success toast
  are the same green; chart series and heat-map scales are derived from the brand seed in OKLCH.
- **Two paradigms** — static components subclass native Flet controls (`Button(ft.Button)`);
  interactive ones are `@ft.component` functions using `use_state` / `use_memo` / `use_effect`.
- **i18n that is actually finished** — Simplified Chinese / Traditional Chinese / English, including
  the *components' own* strings (buttons, calendar, paging, color picker, players) and the formats
  for dates, numbers and list separators.

## Requirements

- Python >= 3.12
- flet[all] >= 1.1.2, < 1.2
- flet-code-editor / flet-charts / flet-video / flet-audio / flet-webview

## Install

```bash
uv pip install cs-ui          # or
pip install -e .              # from source, editable
```

## Quick start

```python
import flet as ft
from ui import Button, Checkbox, Column, Container, Input, Text


@ft.component
def HomePage() -> ft.Control:
    name = ft.use_ref(lambda: Input(label="Name", value="Shawn", width=260)).current
    agree = ft.use_ref(lambda: Checkbox(label="I have read the terms")).current

    return Container(
        expand=True,
        padding=24,
        content=Column(
            spacing=16,
            controls=[
                Text("CS UI", size=24, weight=ft.FontWeight.BOLD),
                name.ui(),
                agree.ui(),
                Button("Click me", on_click=lambda _: print("clicked!")),
            ],
        ),
    )


def main(page: ft.Page) -> None:
    page.title = "CS UI Demo"
    page.render(HomePage)


if __name__ == "__main__":
    ft.run(main)
```

### Three rules you must know

1. **Use `page.render` + `Router(manage_views=False)` for the root view, not `page.render_views`.**
   The view stack covers the entire page overlay: anything attached to `page.overlay` renders at zero
   pixels, `page.show_dialog` stops working, **and nothing raises** (`len(page.overlay)` is correct
   in Python, callbacks still fire).
2. **`ft.View` is not a regular control.** Put one inside a control tree and Flutter throws
   `Bad state: No element` repeatedly, leaving a grey page. Likewise `ft.AppBar` only mounts on
   `View.appbar`; draw a top bar with `Container` + `Row`.
3. **Interactive components must be built, then mounted with `.ui()`.** `Input` / `Checkbox` /
   `Switch` / `SelectBox` / `MultiSelect` are an `@ft.observable` data object plus an
   `@ft.component ui()`; dropping the object into a control tree yields a blank box.

If the host must keep the view stack (`manage_views=True`), `MultiSelect` degrades to an in-flow
panel (it takes layout height and pushes content down); `float_panel=False` turns that off explicitly.

## Module layout

| Package | Contents |
|---|---|
| `ui.core` | Base: `tokens`, `palette` (color engine), `typography`, `theme`, `i18n`, `format`, `responsive`, `doc` (documentation kit) |
| `ui.chart` | `BarChart` / `LineChart` / `AreaChart` / `ScatterChart` sharing one data parser and derived palette |
| `ui.display` | `Text` family (`Header_1..6` / `Quote` / `Link` / `Code` / `Markdown` / `Json`), `Calendar`, `Carousel`, `Heatmap`, `Descriptions`, `Tree`, `ListTile`, `Image`, `LogContainer` |
| `ui.display.media` | `Audio` / `AudioPlayer` / `Video` / `Pdf` |
| `ui.feedback` | `AlertDialog`, `Message` (receipt for an explicit action), `Notification` (system-level), `Loading`, `ProgressBar` |
| `ui.input` | Every form control: `Input`, `Checkbox`, `Radio`, `Switch`, `SelectBox`, `MultiSelect`, `Cascader`, `Transfer`, `Slider`, `Rating`, `Chip`, `ColorPicker`, `DateInput`, `DateTimeInput`, `FilePicker`, `ImagePicker`, `NumberInput`, `SearchBar`, `SegmentedButton`, `Button` |
| `ui.layout` | `PageLayout`, `Grid`, `Card`, `Column` / `Row` / `Stack` / `Container`, `Table` (with paging), `Tabs`, `Step`, `Expander`, `Divider` |
| `ui.navigation` | `AppBar`, `BreadCrumb`, `Menu`, `Pagination` |
| `ui.utils` | `CodeEditor`, `CodeView` (collapsible, copyable code display) |

To locate a specific component, function or token, `ui-mcp`'s `list_components` is faster than
walking the tree.

## Tokens and theming

Components contain no raw color / radius / font-size literals; everything comes from
`ui.core.tokens`. Changing the theme or the brand color is therefore a framework-level operation,
not per-widget recoloring.

### 1. Apply the theme

```python
import flet as ft
from ui import ThemeProvider, Router, Route

def App() -> ft.Control:
    return ThemeProvider(
        build=lambda: ft.Router(ROUTES, not_found=NotFoundPage, manage_views=False)
    )
```

`ThemeProvider` builds its subtree with `use_memo(build, [])`: switching themes does not rebuild the
control tree, so typed form content survives.

### 2. Light/dark and brand color

```python
from ui import theme_state, use_theme, ThemeSwitcher, PRIMARY_SEEDS

@ft.component
def TopBar() -> ft.Control:
    state = use_theme()                    # subscribe to the global theme (inside the component)
    ft.Button("Toggle", on_click=lambda e: state.toggle_mode())
    ft.Button("Recolor", on_click=lambda e: state.set_primary(PRIMARY_SEEDS["violet"]))
```

| Method | Behavior |
|---|---|
| `toggle_mode()` | Always switches to the mode opposite to **what is on screen** (the click is always visible) |
| `cycle_mode()` | `system → light → dark → system` |
| `set_mode(name)` | Jump straight to a mode; `"system"` follows the OS |
| `set_primary(hex)` | Recompute all 46 roles for the new hue; light and dark sets are shipped together |

### 3. Tokens

**Theme-aware tokens** (values are role names; Flutter resolves them at paint time, so switching
themes costs zero Python repaints):

```python
ft.Colors.PRIMARY, ft.Colors.SURFACE_CONTAINER_LOWEST, ft.Colors.ON_SURFACE_VARIANT
```

**Framework-resolved tokens** (semantics M3 does not have, from `ui.core.tokens`):

```python
from ui import SPACE, RADIUS, FONT_SIZE, elevation, hairline, state_layer, selected_layer, disabled_layer

SPACE["4"]                  # 16 —— 4pt steps (0,1,2,3,4,5,6,8,10,12,16,20,24,32,40)
RADIUS["lg"]                # 8
FONT_SIZE["body"]           # 14 —— other steps: 11 / 12 / 16 / 20 / 24 / 28 / 36
elevation(2)                # five shadow steps; the shadow color is the 'shadow' role
state_layer("hover")        # 'onsurface,0.08'
selected_layer("normal")    # 'primary,0.12'
disabled_layer()            # 'onsurface,0.38' —— disabled text / icons
disabled_layer("container") # 'onsurface,0.12' —— disabled fills and borders
hairline()                  # 1px divider
```

**Typography tokens** (`ui.core.typography`):

```python
from ui import typography as tp

tp.leading(14)              # 1.618 —— body gets φ, no hand-written height
tp.leading(36)              # 1.222 —— headings should be tight
tp.leading(11)              # 1.672 —— small text should breathe
tp.tracking(14)             # 0.0    —— tracked in em, optical correction within ±0.025
tp.tracking(36)             # -0.80  —— large text tightens (-0.022em)
tp.tracking(30)             # -0.62  —— off-scale sizes interpolate between neighbours
tp.role("body")             # Role(size=14, leading=1.618, tracking=0.0, weight=w400)
tp.text_style("title", color=..., weight=...)   # the only typesetting entry for components
tp.RHYTHM["section"]        # 32 — hair 4 / block 8 / paragraph 12 / group 20 / section 32 / page 52
tp.LEADING_PROSE            # 1.75 —— long-form body, one step looser than UI body
tp.LEADING_CODE             # 1.55
tp.cols("thirds")           # 2:1 on 12 columns (8 + 4)
tp.cols("golden")           # 7 + 5 (φ:1)
tp.cols("aside")            # 4 + 8 —— explanation left, demo right
```

**Semantic colors come in three steps** — one value must not serve all purposes.

| Function | Use | Light | Dark |
|---|---|---|---|
| `semantic("success")` | solid fill (badge, status dot, progress segment) | `#007F5B` | `#38B98B` |
| `on_semantic("success")` | foreground on that fill | `#FFFFFF` | `#002014` |
| `semantic_text("success")` | text / icons / hairlines on the page | `#007F5B` | `#38B98B` |

The hand-picked `#10B981` scored only **2.54:1** against white and `#F59E0B` only **2.15:1** — white
text on them was unreadable. Now `palette.semantic_scale` **solves every semantic color to the same
target contrast** (5.0:1 light, 7.0:1 dark), so all four roles land on the same visual weight
(lightness spread < 0.02). In dark mode the foreground is **deep ink**, not white — `#F28948` on
white is 2.0:1, on deep ink it is 7.0:1. Roles: `success` / `warning` / `danger` / `info` / `neutral`.

**The accent quartet** — one accent color, four legitimate uses, four different values.

| Function | Use |
|---|---|
| `accent_fill(role)` | solid fill (primary button, badge, progress segment) |
| `accent_on(role)` | foreground on that fill |
| `accent_text(role)` | text / icons on a **surface** color |
| `accent_soft(role)` | 12% wash, small area (icon base, count badge) |
| `accent_wash(role)` | 8% wash, large area (dialog header band, whole toast row) |

`role` is `primary` / `secondary` / `tertiary` (M3 roles, resolved by Flutter at runtime, so no
rebuild on theme change) or one of the five semantic roles. The wash comes in two steps because the
same opacity reads heavier over a larger area.

### 4. The palette

```python
from ui.core.palette import build_scheme, tonal

build_scheme("#1F6FEB", "light")   # all 46 roles in one call
tonal("#1F6FEB")[50]               # '#F4F8FF' —— 11 steps (50…950)
tonal("#1F6FEB")[600]              # '#3271D7'
```

Three rules hold it up: lightness on a **logarithmic gradient** across eleven steps (~0.075 apart,
matching Weber's law, so "one step paler" is the same paleness for any hue); chroma on a **bell
envelope** (0.10 at step 50 → 1.00 at 500 → 0.50 at 950, so the pale end stays pale *and* tinted);
foregrounds **solved by bisection against a contrast ratio** rather than sampled at a step — on the
same tone, yellow and blue differ threefold in relative luminance, and "equal tone" has never meant
"equally readable". Neutrals get a 215° cool-blue cast plus a trace of the brand hue: slate, not dead
grey.

**Five layers**, one means of expression each, never borrowed across:

| Layer | What to use | Resolved by |
|---|---|---|
| Surface | `SURFACE` / `SURFACE_CONTAINER_LOWEST..HIGHEST` | Flutter |
| Foreground | `ON_SURFACE` / `ON_SURFACE_VARIANT` / `OUTLINE` / `OUTLINE_VARIANT` | Flutter |
| Interaction | `state_layer()` / `selected_layer()` / `disabled_layer()` | Flutter |
| Accent | `accent_fill/on/text/soft/wash()` | mixed |
| Data | `chart_palette()`, heat-map scales (from `ui.core.color`) | Python |

Data-layer series colors are **derived in OKLCH**: first series shares the brand hue, all series have
equal lightness (so none "looks more important"), hues 45° apart. Change the brand and the charts
follow; the heat map's strongest step lands on the brand palette's anchor color.

### 5. One trap

In flet 1.x, **reading a field of an observable does not subscribe to it**. Subscription happens in
exactly three places: a component argument typed `Observable`, `use_state`, `use_context`.

```python
state = theme_state()
mode = state.mode          # ❌ read once, no repaint
state = use_theme()        # ✅ subscribes for you
```

Likewise, **role names and Python-computed hex values cost very different things**: a role name is
resolved by Flutter, so a theme switch costs Python nothing; `semantic("success")` only updates if
the component subscribes to the theme.

## Internationalization

### 1. Register strings

`zh-CN` / `zh-TW` / `en-US` are built in; you only supply your own strings:

```python
from ui import register_messages

register_messages("en-US", {
    "app": {"title": "My App"},
    "hello": "Hello, {name}",
    "files": {"one": "{n} file", "other": "{n} files"},
    "cities": ["Beijing", "Shanghai"],   # grouped: tr.list("cities")
})
register_messages("zh-CN", {
    "app.title": "我的应用",             # flat and nested are equivalent
    "hello": "你好，{name}",
    "files": {"one": "{n} 个文件", "other": "{n} 个文件"},
})
```

Keys are flattened into dot-strings (`"app.title"`) **when the table is installed**, so a lookup is
one `dict.get` — not a `split` plus a walk down the tree on every render.

### 2. Wire up a page

```python
@ft.component
def App():
    return I18nProvider(build=MainShell)     # next to ThemeProvider, at the root

@ft.component
def Toolbar():
    tr = use_t()                              # subscribes: repaints on language change
    return ft.Text(tr("app.title"))           # interpolation: tr("hello", name="Shawn")

t("app.title")                                # outside components (logs, menu building): no subscribe
```

`LanguageSwitcher()` is a ready-made top-bar language menu. **Use `use_t()`, not the global `t()`** —
same subscription trap as above: a bare `t()` reads once and never repaints. `I18nProvider` reuses
its subtree via `use_memo`, so switching languages does not clear form content either.

### 3. Fallbacks and missing keys

Lookup is `current language → base dialect → global fallback`, built in as `Traditional → Simplified
→ English`. A missing key **never raises** (a UI should not go blank over one untranslated line): the
key name is returned, one warning is logged, and `missing_keys()` lists the gaps. Turn on strict mode
in CI:

```python
from ui import configure, validate

configure(strict=True)        # missing key → KeyError
validate("zh-CN")             # {"zh_TW": ["a.b"], "en_US": []}
```

### 4. Format is copy too

"Not translated yet" is the easy i18n bug; **"translated, but the format is still Chinese"** is the
common one: `2026 年 9 月` in an English UI, `1,286` items, a calendar header hardcoded to
`一二三四五六日`. All of it comes from `ui.core.format`:

```python
from ui import format_number, format_date, calendar_title, weekday_names, first_weekday, format_list

format_number(1286)                    # 1,286
format_date(date(2026, 9, 26))         # 2026-09-26   /  09/26/2026
format_date(d, long=True)              # 2026年9月26日 /  September 26, 2026
calendar_title(2026, 9)                # 2026年9月     /  September 2026
weekday_names()                        # ('一','二',…,'日') / ('Mo','Tu',…)
first_weekday()                        # 0 = Monday for Chinese, 6 = Sunday for English
format_list(["A", "B", "C"])           # A、B、C       /  A, B, C
```

The calendar titles, month cells, weekday headers and first day of week in `DateInput` /
`DateTimeInput` / `CalendarPanel` all follow the language (`first_day_weekday=None` means "follow"),
and `Pagination` formats its total with thousands separators.

### 5. Add a language, persist the choice

```python
from ui import Language, load_catalogs, register_language

register_language(Language("ja", "日本語", "Japanese", fallback="en"))
load_catalogs("assets/i18n")     # fr.json / de.json … (_meta can self-register the language)
```

```json
{
  "_meta": {"native_name": "Français", "english_name": "French", "fallback": "en"},
  "messages": {"app": {"title": "Mon App"}}
}
```

Language tags may be written `zh-CN`, `zh_TW` or `en-US`: **region beats script** (`zh-Hant-HK →
zh_TW`), and lookups match loosely on language and script — register only `en` and both `en-US` and
`en-GB` resolve to it.

The chosen language is written to local config (`FLET_APP_STORAGE_DATA`, or
`%LOCALAPPDATA%\cs-ui` on Windows, `Application Support` on macOS, `$XDG_CONFIG_HOME` on Linux) and
**read back synchronously before the first frame**, so startup never flashes the default language. If
the user never chose, the system language wins. `MemoryStore()` is for tests; a custom store only
needs `read()` / `write()`.

## Imports

```python
from ui import Button, Card, Column, Container, Divider, Row, Text, TextField, ft
```

`ui.__all__` holds 780 names (everything public in flet + each package's `__all__` + submodule names +
`ft`).

**Imports are lazy**: `import ui` loads only `flet` itself (~0.2s); a component imports its package on
first access. A full star-import measured **1.4s** — `ui.chart` alone drags in matplotlib + plotly
(~0.62s), and 536 attribute reflections cost another ~0.59s.

```python
import ui              # ~0.2s
ui.Container           # ~35ms, pulls in ui.layout once
ui.BarChart            # imports ui.chart only if you actually chart
```

`dir(ui)` still returns the full name table, so IDE completion and `from ui import *` behave as
before. The name → package map lives in `src/ui/_registry.py` and is generated — **regenerate it
after changing components**:

```bash
python scripts/gen_ui_registry.py           # after adding / removing a component
python scripts/gen_ui_registry.py --check   # verify it matches the source
```

## Regression

Consistency cannot rely on "remember to run it", so every check lives behind one entry point:

```bash
python scripts/check_all.py                 # 31 checks / ~53s
python scripts/check_all.py --stage fast    # static gate + token audit only (enough for styling)
python scripts/check_all.py --stage visual  # real screenshots + grey-block detection (opens windows)
```

| Check | What it protects |
|---|---|
| `ruff --select F821,F811,F841,F401` | undefined names / duplicates / unused locals and imports |
| `audit_consistency.py` | raw colors, out-of-range sizes / icons / radii, odd padding, `OUTLINE` as text color, colors that break in dark mode, static color names |
| `_tokens_logic.py` | token contract: one facade, monotonic scales, state layers in order, accent quartet sourced from `SEMANTIC` |
| `_palette_logic.py` | palette contract: all 46 roles, 11 evenly spaced steps with no hue drift, 17 contrast pairs passing (8 seeds × 2 modes), equal weight across semantic colors |
| `_color_logic.py` | color engine: OKLCH round-trip, equal-lightness series, hue spacing, monotonic ramps |
| `_typography_logic.py` | the typographic law: leading formula, tracking on the scale equal to the step value, six heading levels monotonic — 86 assertions |
| `_responsive_logic.py` | breakpoints identical to `ResponsiveRow`, classes monotonic and boundary-closed-left, no repaint within a class, width limit takes `min()`, private fields never leak into the serialized tree |
| `_*_logic.py` | per-component pure logic (state derivation, value bounds, callbacks, frozen-tree degradation) |
| `_ui_mcp_logic.py` | MCP index contract: paradigm matches code, only base-module constants, same-name lookups resolvable, Chinese aliases never point at deleted symbols |
| `_doc_check.py` | SPEC / examples / API completeness for 72 components (examples are actually executed) |
| `gen_ui_registry.py --check` | `ui.__all__` and the registry do not drift |
| `build_docs_i18n.py --check` | the three site locales stay in sync |

**Assert rules, not color values**: an assertion pinned to `#047857` produces false alarms the moment
the hue changes; assert invariants such as "the lightness spread across four semantic colors < 0.3".

## Docs site and examples

The docs site is the example library: 72 components, each with runnable examples and an API table.

```bash
python docs/main.py
```

| Route | Contents |
|---|---|
| `/` | Home |
| `/docs/quickstart` `/docs/architecture` `/docs/theming` `/docs/i18n` `/docs/responsive` | Guides |
| `/components/<category>/<component>` | Definition / anatomy / when to use / examples / API / notes |
| `/about` | About |

After a styling change, confirm it actually painted (a grey block means Flutter failed to render; a
yellow hatch means text burst out of a fixed-height box):

```bash
python scripts/_visual_check.py                    # 13 representative pages, light
python scripts/_visual_check.py --mode dark        # dark
python scripts/_visual_check.py --scroll 14 --routes /components/layout/table
```

`examples/` holds minimal runnable hosts (`test_form.py` / `test_feedback.py` / `test_i18n.py` /
`test_chart.py` …); `scripts/ui_demo.py` is the older single-file full demo.

## MCP server (ui-mcp)

An API server for AI agents, same idea as [flet-mcp](https://flet.dev/docs/cookbook/flet-mcp/): a
model's memory of cs-ui is necessarily stale and partly invented, so let it **look things up** instead
of guess.

The index is **built by runtime introspection** (`@ft.control` flattens the constructor,
`@ft.observable` generates a proxy class — static scanning cannot see the real signature). Three JSON
files ship with the package; the server never imports `ui`:

| Artifact | Contents |
|---|---|
| `data/api.json` | 95 components, 28 data classes, 185 functions, 8 enums, 52 token constants, plus member tables for 45 inherited external classes |
| `data/examples.json` | `examples/` split by page + a real call snippet for every component |
| `data/docs.json` | README / TODO / project memory, split into searchable sections |

12 tools; `UI_MCP_ENABLE_{API,ICONS,EXAMPLES,DOCS,GUIDE}=0` disables a whole group:

| Tool | Purpose |
|---|---|
| `get_api(name, member=, query=, format=)` | Primary verifier. Components / data classes / functions / enums / token constants / external base classes |
| `list_components(category=, pattern=, kind=)` | Browse by category or paradigm (static / observable / function) |
| `search_components(query)` | Bilingual semantic search ("paging table" → Table, "spacing" → SPACE) |
| `get_enum` / `search_enum_members` / `enum_has_member` | Enum verification |
| `find_icon(query, family=)` | Find icons by concept (Material + Cupertino, Chinese mapping included) |
| `search_examples` / `get_example` | Find example pages, read real source |
| `search_docs` / `get_doc` | Search documentation sections |
| `get_guidelines(topic)` | **Hard-won rules**: frozen trees, the STRETCH trap, responsive, palette, tokens, verification scripts |

```bash
pip install -e ".[mcp]"      # fastmcp dependency
ui-mcp                        # stdio server (default subcommand)
ui-mcp build                  # rebuild the index after touching src/ui
ui-mcp check                  # is the index stale? (source mtime + ui/flet version drift)
ui-mcp guide responsive       # print the guidelines in a terminal
```

```json
{
  "mcpServers": {
    "ui": { "command": "ui-mcp" }
  }
}
```

A new component needs a line in `src/ui_mcp/aliases.py`, otherwise Chinese search will not find it.

## References

- <https://flet.dev/>
- <https://github.com/flet-dev/examples>
