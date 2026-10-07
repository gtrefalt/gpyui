# gpyui

[![PyPI](https://img.shields.io/pypi/v/gpyui.svg)](https://pypi.org/project/gpyui/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://pypi.org/project/gpyui/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/gtrefalt/gpyui/blob/main/LICENSE)
[![Documentation](https://img.shields.io/badge/docs-gpyui-teal.svg)](https://gtrefalt.github.io/gpyui/)

**Build native desktop applications in Python with GPUI Kit.**

gpyui is a Python UI toolkit for apps, tools and dashboards. Compose layouts,
bind state and handle events in Python, using Longbridge's
[GPUI Kit](https://github.com/longbridge/gpui-kit) components. The Rust backend,
powered by [GPUI](https://github.com/zed-industries/zed/tree/main/crates/gpui),
handles native windows, rendering and text editing.

[Documentation](https://gtrefalt.github.io/gpyui/) ·
[Component catalog](https://gtrefalt.github.io/gpyui/components/) ·
[Examples](https://github.com/gtrefalt/gpyui/tree/main/examples) ·
[Releases](https://github.com/gtrefalt/gpyui/releases)

![A native gpyui dashboard in light appearance, with a watchlist, price chart and paper-order controls](https://raw.githubusercontent.com/gtrefalt/gpyui/main/docs/screenshots/workspace-light.png)

A real native window built entirely through the Python API. The
[trading dashboard example](https://gtrefalt.github.io/gpyui/examples/trading/)
includes simulated quotes, streaming charts and async paper orders. See the
documentation for the animated walkthrough.

## Why gpyui?

- **Native components:** 77 Python controls spanning inputs, images, tables, charts,
  navigation, dialogs and feedback, backed by GPUI Kit.
- **Python composition:** build layouts with `Column`, `Row`, containers and
  context managers, or pass an explicit tree of controls.
- **State binding:** connect application state to text, inputs and selection
  controls with `State` and bindings.
- **Async events:** use regular functions or `async def` callbacks; property
  changes are queued and batched for native updates.
- **Shared commands:** use the same Python action from buttons, nested menus and
  platform-aware keyboard shortcuts and searchable CommandPalette.
- **Forms and validation:** Kit Form/Field labels, help and inline errors,
  sync/async Python validators and shared submission with retry. Failed validation
  preserves native text, caret, selection and undo.
- **Native themes:** macOS Classic, Windows/Fluent and shadcn
  light/dark presets,
  custom palettes and live switching that preserves editor state.
- **Images:** native files, URLs and encoded bytes, GIF/WebP animation,
  fit modes, loading/error callbacks and retry. See the
  [image guide](https://gtrefalt.github.io/gpyui/guide/images/); video streaming
  requires a separate native pipeline.

## Installation

Requires **CPython 3.12+**. On macOS 12+ and Windows, install from PyPI:

```bash
uv init my-app
cd my-app
uv add gpyui
```

In an existing uv project, just run `uv add gpyui`. Alternatively, use
`pip install gpyui` in a virtual environment. Native wheels are available for
Intel/x64 and ARM64; Windows ARM64 is tested with Python 3.13+.

On **Linux**, install the matching prebuilt wheel from
[GitHub Releases](https://github.com/gtrefalt/gpyui/releases). Linux wheels use
system X11, font and Vulkan libraries and are currently distributed separately
from PyPI. See the [installation guide](https://gtrefalt.github.io/gpyui/guide/install/)
for runtime dependencies and source builds. Installing a wheel requires no Rust
compiler.

## Your first app

Save this as `hello.py`:

```python
from gpyui import Application, Button, Column, Label, TextInput

app = Application(title="Hello, gpyui", width=480, height=300, theme="light")

with app, Column().style(gap=12, padding=24):
    name = TextInput(placeholder="Your name")
    greeting = Label("Enter a name and choose Greet")

    def greet():
        greeting.text = f"Hello, {name.value or 'world'}!"

    Button("Greet", variant="primary", on_click=greet)

app.run()
```

Run `uv run python hello.py` (or `python hello.py` with pip). Clicking the native
button runs your Python callback and updates the label. Explore
[layouts](https://gtrefalt.github.io/gpyui/guide/layout/),
[state binding](https://gtrefalt.github.io/gpyui/guide/state/) and
[async events](https://gtrefalt.github.io/gpyui/guide/events/) for larger apps.

## Documentation and examples

For a fixed-size window, use `Application(width=520, height=320, resizable=False)`.
The 0.6.1 window API also adds minimum dimensions, initial position/state,
live `app.title` and `app.resize(...)`, plus minimize, focus and fullscreen actions.
See [native window controls](https://gtrefalt.github.io/gpyui/guide/windows/) for
platform behavior and examples.

Choose a native preset with `Application(theme=Theme("macos"))` or
`Theme("windows", mode="dark")`. Customize colors, corner radii and typography;
switch a running app by assigning `app.theme`. The 0.6.1 macOS correction
uses Kit’s exact Classic Light/Dark configuration; Windows uses Fluent controls, larger
checkboxes and underlined text fields. These style real Kit controls, with
platform-owned window decorations. See [themes and native previews](https://gtrefalt.github.io/gpyui/guide/themes/)
and the [appearance example](https://github.com/gtrefalt/gpyui/blob/main/examples/appearance.py).

| GPUI Kit macOS Classic Light | Windows 11-inspired |
| --- | --- |
| ![GPUI Kit macOS Classic Light native controls](https://raw.githubusercontent.com/gtrefalt/gpyui/main/docs/screenshots/themes/macos-light.png) | ![Roomier Windows-style native controls](https://raw.githubusercontent.com/gtrefalt/gpyui/main/docs/screenshots/themes/windows-light.png) |


The [documentation](https://gtrefalt.github.io/gpyui/) includes a visual catalog
with real native previews, properties, events and runnable examples for every
control, plus guides for styling, application lifecycle and release builds.

Try the [trading dashboard](https://gtrefalt.github.io/gpyui/examples/trading/),
[notes editor](https://gtrefalt.github.io/gpyui/examples/notes/),
[settings editor](https://gtrefalt.github.io/gpyui/examples/settings/),
[component gallery](https://gtrefalt.github.io/gpyui/examples/gallery/) or
[async binding example](https://github.com/gtrefalt/gpyui/blob/main/examples/async_binding.py).

![A light native settings editor with conditional fields, validation and async saving](https://raw.githubusercontent.com/gtrefalt/gpyui/main/docs/screenshots/settings-light.png)

The settings editor validates Python values, keeps conditional editors intact,
and shares Save/Retry/keyboard submission through one async command. See
[forms and validation](https://gtrefalt.github.io/gpyui/guide/forms/) for usage.

## Agent skills

Give your coding agent the Python API, component contracts, async recipes and
native desktop design guidance:

```bash
npx skills add gtrefalt/gpyui --skill gpyui --skill gpyui-design-guides
```

Inspired by [GPUI Kit's skills](https://github.com/longbridge/gpui-kit/tree/main/skills),
these skills cover the Python bindings and their current limits. See
[installation and usage](https://gtrefalt.github.io/gpyui/agent-skills/), including
manual installation for Codex. Python dependencies use uv; the command above
installs agent instructions.

## Project status

gpyui is in early development, with 77 Python controls on `main`. This is basic
catalog coverage; many upstream builder options and specialized APIs remain
unbound. Version 0.6.1 includes Image, expanded window controls, exact macOS Classic
themes, richer tables/inputs, MultiSelect and CommandPalette. Its backend pins
GPUI Kit 0.7.1 and GPUI 0.3.8; 0.5.0 used Kit 0.7.0 / GPUI 0.3.7.
Diff/Speech have no Python bindings; optional Speech and GPUI Fast are not enabled.

Applications currently use one window with dynamic children and visibility.
Existing controls retain their native identity and editing state when moved or
hidden. Table uses Kit's native virtualized table; List currently composes all
items. Tables now support stable row keys, per-column widths/text-numeric sorting
and native filtering. Inputs add read-only/masked editing, numeric bounds and
mutable choices; MultiSelect and CommandPalette expose native selection/search.
The next priorities are native List virtualization, custom cells and async providers.
Docking and multiwindow follow. Settings/questionnaires,
MessageScroller, advanced editor providers and remaining chart APIs are also
unbound. See the
[coverage and roadmap](https://gtrefalt.github.io/gpyui/component-coverage/) for
supported features and planned work.

Release wheels are tested on Linux, macOS and Windows across x64 and ARM64.
Linux/X11 has native interaction tests; macOS and Windows have native window,
state and lifecycle smoke tests. See [release support](https://gtrefalt.github.io/gpyui/releases/)
for the platform and Python matrix.

## Contributing

Issues and pull requests are welcome. Start with the
[contributor guide](https://github.com/gtrefalt/gpyui/blob/main/CONTRIBUTING.md)
for source setup, Ruff, ty, Just and Lefthook, and the
[architecture](https://gtrefalt.github.io/gpyui/architecture/) for design decisions
and pinned upstream dependencies.

## License and acknowledgements

gpyui is available under the
[MIT License](https://github.com/gtrefalt/gpyui/blob/main/LICENSE).
[GPUI](https://www.gpui.rs/) and [GPUI Kit](https://gpui-kit.com/) make its native
backend possible. The Python API also draws on composition and event patterns
from [NiceGUI](https://github.com/zauberzeug/nicegui) and
[Flet](https://github.com/flet-dev/flet).

Dependencies retain their own licenses. Distributions include
[third-party notices](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/THIRD_PARTY_NOTICES.txt).
