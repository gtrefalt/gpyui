# Overlays

Generated Python API reference from the repository (manifest version 0.5.0).
Includes unreleased contracts; check [release status and coverage](../coverage.md) against your installed version.

## Tooltip

Native tooltip attached to composed content.

### Runnable example

```python
import gpyui as ui

control = ui.Tooltip("Native help text", children=[ui.Button("Hover for help")])

app = ui.Application(ui.Column([control]), title="Tooltip", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `text` | `""` | str | Assignment |

Accepts `children=[...]`, a `with` block, and runtime `add`, `insert`, `remove`, `clear`, `set_children` or assignment to `children`. Each child has one parent. Reuse existing instances to preserve native state; see [runtime composition](../composition.md#dynamic-composition).

Construct explicit child lists outside a composition context, as in the example. Inside a `with` block, construct the parent first and then its children.

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

This wrapper exposes no Python activation/change handler. Update its mutable properties by assignment from a running callback. Native behavior remains in Rust.

### Contract and limits

Kit owns the hover lifecycle.

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L733) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](../coverage.md)

## Popover

Native popup with Python-composed contents.

### Runnable example

```python
import gpyui as ui

control = ui.Popover("Open details", children=[ui.Label("A native popup, composed in Python.")])

app = ui.Application(ui.Column([control]), title="Popover", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `text` | `"Details"` | str | Assignment |

Accepts `children=[...]`, a `with` block, and runtime `add`, `insert`, `remove`, `clear`, `set_children` or assignment to `children`. Each child has one parent. Reuse existing instances to preserve native state; see [runtime composition](../composition.md#dynamic-composition).

Construct explicit child lists outside a composition context, as in the example. Inside a `with` block, construct the parent first and then its children.

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

This wrapper exposes no Python activation/change handler. Update its mutable properties by assignment from a running callback. Native behavior remains in Rust.

### Contract and limits

Open/close lifecycle is native; controlled Python popup state is not exposed.

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L739) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](../coverage.md)

## HoverCard

Native hover preview content.

### Runnable example

```python
import gpyui as ui

control = ui.HoverCard("Hover for a preview", children=[ui.Label("A native preview card.")])

app = ui.Application(ui.Column([control]), title="HoverCard", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `text` | `"Details"` | str | Assignment |

Accepts `children=[...]`, a `with` block, and runtime `add`, `insert`, `remove`, `clear`, `set_children` or assignment to `children`. Each child has one parent. Reuse existing instances to preserve native state; see [runtime composition](../composition.md#dynamic-composition).

Construct explicit child lists outside a composition context, as in the example. Inside a `with` block, construct the parent first and then its children.

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

This wrapper exposes no Python activation/change handler. Update its mutable properties by assignment from a running callback. Native behavior remains in Rust.

### Contract and limits

Kit owns the hover lifecycle.

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L745) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](../coverage.md)

## Dialog

A native dialog containing Python controls.

### Runnable example

```python
import gpyui as ui

control = ui.Dialog(
    "Confirm changes", children=[ui.Label("Save this project?"), ui.Button("Save", variant="primary")]
)
open_button = ui.Button("Open dialog", on_click=control.open)

app = ui.Application(ui.Column([control, open_button]), title="Dialog", width=640, height=440)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `title` | `""` | str | Constructor only |
| `value` | `false` | bool | Assignment |

Accepts `children=[...]`, a `with` block, and runtime `add`, `insert`, `remove`, `clear`, `set_children` or assignment to `children`. Each child has one parent. Reuse existing instances to preserve native state; see [runtime composition](../composition.md#dynamic-composition).

Construct explicit child lists outside a composition context, as in the example. Inside a `with` block, construct the parent first and then its children.

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

- `on_change(event)`: Runs after native value and Python mirror/bound State change.

Handlers can take zero arguments or one `Event`, and can be synchronous or async. They run on the owned Python asyncio loop. See [events and asyncio](../state-and-events.md).

`bind_value(State(...))` binds both ways without echoing native edits back through setters. `unbind()` disposes the subscription. See [state binding](../state-and-events.md).

### Contract and limits

Use open()/close(), or assign value. One dialog per window; title is fixed.

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L872) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](../coverage.md)

## Sheet

A native side panel containing Python controls.

### Runnable example

```python
import gpyui as ui

control = ui.Sheet(
    "Project details",
    children=[
        ui.Label("Project: gpyui"),
        ui.TextInput("Ada Lovelace"),
        ui.Switch("Notifications", value=True),
    ],
)
open_button = ui.Button("Open sheet", on_click=control.open)

app = ui.Application(ui.Column([control, open_button]), title="Sheet", width=640, height=440)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `title` | `""` | str | Constructor only |
| `value` | `false` | bool | Assignment |

Accepts `children=[...]`, a `with` block, and runtime `add`, `insert`, `remove`, `clear`, `set_children` or assignment to `children`. Each child has one parent. Reuse existing instances to preserve native state; see [runtime composition](../composition.md#dynamic-composition).

Construct explicit child lists outside a composition context, as in the example. Inside a `with` block, construct the parent first and then its children.

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

- `on_change(event)`: Runs after native value and Python mirror/bound State change.

Handlers can take zero arguments or one `Event`, and can be synchronous or async. They run on the owned Python asyncio loop. See [events and asyncio](../state-and-events.md).

`bind_value(State(...))` binds both ways without echoing native edits back through setters. `unbind()` disposes the subscription. See [state binding](../state-and-events.md).

### Contract and limits

Use open()/close(), or assign value. One sheet per window; title is fixed.

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L886) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](../coverage.md)
