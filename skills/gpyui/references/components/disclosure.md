# Disclosure

Generated Python API reference from the repository (manifest version 0.6.0).
Follows the repository manifest; check [release status and coverage](../coverage.md) against your installed version.

## Collapsible

Native disclosure for Python-composed content.

### Runnable example

```python
import gpyui as ui

control = ui.Collapsible(
    "More information", value=True, children=[ui.Label("Rust retains native component state.")]
)

app = ui.Application(ui.Column([control]), title="Collapsible", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `text` | `""` | str | Assignment |
| `value` | `false` | bool | Assignment |

Accepts `children=[...]`, a `with` block, and runtime `add`, `insert`, `remove`, `clear`, `set_children` or assignment to `children`. Each child has one parent. Reuse existing instances to preserve native state; see [runtime composition](../composition.md#dynamic-composition).

Construct explicit child lists outside a composition context, as in the example. Inside a `with` block, construct the parent first and then its children.

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

- `on_change(event)`: Runs after native value and Python mirror/bound State change.

Handlers can take zero arguments or one `Event`, and can be synchronous or async. They run on the owned Python asyncio loop. See [events and asyncio](../state-and-events.md).

`bind_value(State(...))` binds both ways without echoing native edits back through setters. `unbind()` disposes the subscription. See [state binding](../state-and-events.md).

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L516) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](../coverage.md)

## Accordion

Native disclosure among labeled items.

### Runnable example

```python
import gpyui as ui

control = ui.Accordion(
    [["About gpyui", "Compose native apps in Python."], ["Architecture", "Rust owns rendering and editing."]],
    value=0,
)

app = ui.Application(ui.Column([control]), title="Accordion", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `items` | `[]` | list[list[str]] | Assignment |
| `value` | `0` | nonnegative int | Assignment |
| `disabled` | `false` | bool | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

- `on_change(event)`: Runs after native value and Python mirror/bound State change.

Handlers can take zero arguments or one `Event`, and can be synchronous or async. They run on the owned Python asyncio loop. See [events and asyncio](../state-and-events.md).

`bind_value(State(...))` binds both ways without echoing native edits back through setters. `unbind()` disposes the subscription. See [state binding](../state-and-events.md).

### Contract and limits

The initial wrapper exposes one open index and string item contents.

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L523) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](../coverage.md)

## Carousel

Native slide selection.

### Runnable example

```python
import gpyui as ui

control = ui.Carousel(children=[ui.Label("First native slide"), ui.Label("Second native slide")]).style(
    height=150, full_width=True
)

app = ui.Application(ui.Column([control]), title="Carousel", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `value` | `0` | nonnegative int | Assignment |

Accepts `children=[...]`, a `with` block, and runtime `add`, `insert`, `remove`, `clear`, `set_children` or assignment to `children`. Each child has one parent. Reuse existing instances to preserve native state; see [runtime composition](../composition.md#dynamic-composition).

Construct explicit child lists outside a composition context, as in the example. Inside a `with` block, construct the parent first and then its children.

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

- `on_change(event)`: Runs after native value and Python mirror/bound State change.

Handlers can take zero arguments or one `Event`, and can be synchronous or async. They run on the owned Python asyncio loop. See [events and asyncio](../state-and-events.md).

`bind_value(State(...))` binds both ways without echoing native edits back through setters. `unbind()` disposes the subscription. See [state binding](../state-and-events.md).

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L865) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](../coverage.md)
