# Selection

Generated Python API reference for gpyui 0.4.0.

## Checkbox

An independent boolean choice.

### Runnable example

```python
import gpyui as ui

control = ui.Checkbox("Enable notifications", value=True)

app = ui.Application(ui.Column([control]), title="Checkbox", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `text` | `""` | str | Assignment |
| `value` | `false` | bool | Assignment |
| `disabled` | `false` | bool | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

- `on_change(event)`: Runs after native value and Python mirror/bound State change.

Handlers can take zero arguments or one `Event`, and can be synchronous or async. They run on the owned Python asyncio loop. See [events and asyncio](../state-and-events.md).

`bind_value(State(...))` binds both ways without echoing native edits back through setters. `unbind()` disposes the subscription. See [state binding](../state-and-events.md).

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L291) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](https://gtrefalt.github.io/gpyui/component-coverage/)

## Switch

A native boolean switch.

### Runnable example

```python
import gpyui as ui

control = ui.Switch("Auto-save", value=True)

app = ui.Application(ui.Column([control]), title="Switch", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `text` | `""` | str | Assignment |
| `value` | `false` | bool | Assignment |
| `disabled` | `false` | bool | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

- `on_change(event)`: Runs after native value and Python mirror/bound State change.

Handlers can take zero arguments or one `Event`, and can be synchronous or async. They run on the owned Python asyncio loop. See [events and asyncio](../state-and-events.md).

`bind_value(State(...))` binds both ways without echoing native edits back through setters. `unbind()` disposes the subscription. See [state binding](../state-and-events.md).

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L297) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](https://gtrefalt.github.io/gpyui/component-coverage/)

## Radio

A standalone native radio control.

### Runnable example

```python
import gpyui as ui

control = ui.Radio("Use system settings", value=True)

app = ui.Application(ui.Column([control]), title="Radio", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `text` | `""` | str | Assignment |
| `value` | `false` | bool | Assignment |
| `disabled` | `false` | bool | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

- `on_change(event)`: Runs after native value and Python mirror/bound State change.

Handlers can take zero arguments or one `Event`, and can be synchronous or async. They run on the owned Python asyncio loop. See [events and asyncio](../state-and-events.md).

`bind_value(State(...))` binds both ways without echoing native edits back through setters. `unbind()` disposes the subscription. See [state binding](../state-and-events.md).

### Contract and limits

Standalone radios do not enforce exclusivity. Use RadioGroup for a grouped choice.

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L301) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](https://gtrefalt.github.io/gpyui/component-coverage/)

## Toggle

A boolean button-like toggle.

### Runnable example

```python
import gpyui as ui

control = ui.Toggle("Pin to workspace", value=True)

app = ui.Application(ui.Column([control]), title="Toggle", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `text` | `""` | str | Assignment |
| `value` | `false` | bool | Assignment |
| `disabled` | `false` | bool | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

- `on_change(event)`: Runs after native value and Python mirror/bound State change.

Handlers can take zero arguments or one `Event`, and can be synchronous or async. They run on the owned Python asyncio loop. See [events and asyncio](../state-and-events.md).

`bind_value(State(...))` binds both ways without echoing native edits back through setters. `unbind()` disposes the subscription. See [state binding](../state-and-events.md).

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L305) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](https://gtrefalt.github.io/gpyui/component-coverage/)

## RadioGroup

An exclusive indexed native choice.

### Runnable example

```python
import gpyui as ui

control = ui.RadioGroup(["Small", "Medium", "Large"], value=1)

app = ui.Application(ui.Column([control]), title="RadioGroup", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `items` | `[]` | list[str] | Assignment |
| `value` | `0` | nonnegative int | Assignment |
| `disabled` | `false` | bool | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

- `on_change(event)`: Runs after native value and Python mirror/bound State change.

Handlers can take zero arguments or one `Event`, and can be synchronous or async. They run on the owned Python asyncio loop. See [events and asyncio](../state-and-events.md).

`bind_value(State(...))` binds both ways without echoing native edits back through setters. `unbind()` disposes the subscription. See [state binding](../state-and-events.md).

### Contract and limits

value is a zero-based item index.

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L309) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](https://gtrefalt.github.io/gpyui/component-coverage/)

## Select

A retained native single-selection dropdown.

### Runnable example

```python
import gpyui as ui

control = ui.Select(["Python", "Rust", "GPUI"], value="Python")

app = ui.Application(ui.Column([control]), title="Select", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `items` | `[]` | list[str] | Constructor only |
| `value` | `""` | str | Assignment |
| `placeholder` | `"Choose…"` | str | Assignment |
| `disabled` | `false` | bool | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

- `on_change(event)`: Runs after native value and Python mirror/bound State change.

Handlers can take zero arguments or one `Event`, and can be synchronous or async. They run on the owned Python asyncio loop. See [events and asyncio](../state-and-events.md).

`bind_value(State(...))` binds both ways without echoing native edits back through setters. `unbind()` disposes the subscription. See [state binding](../state-and-events.md).

### Contract and limits

value is a selected string or "". Items are fixed after construction.

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L360) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](https://gtrefalt.github.io/gpyui/component-coverage/)

## Combobox

Search within native string choices.

### Runnable example

```python
import gpyui as ui

control = ui.Combobox(["London", "New York", "Tokyo"], value="London")

app = ui.Application(ui.Column([control]), title="Combobox", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `items` | `[]` | list[str] | Constructor only |
| `value` | `""` | str | Assignment |
| `placeholder` | `"Choose…"` | str | Assignment |
| `disabled` | `false` | bool | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

- `on_change(event)`: Runs after native value and Python mirror/bound State change.

Handlers can take zero arguments or one `Event`, and can be synchronous or async. They run on the owned Python asyncio loop. See [events and asyncio](../state-and-events.md).

`bind_value(State(...))` binds both ways without echoing native edits back through setters. `unbind()` disposes the subscription. See [state binding](../state-and-events.md).

### Contract and limits

value is a selected string or "". Items are fixed after construction.

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L584) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](https://gtrefalt.github.io/gpyui/component-coverage/)

## Slider

A retained native scalar slider.

### Runnable example

```python
import gpyui as ui

control = ui.Slider(35, minimum=0, maximum=100, step=1)

app = ui.Application(ui.Column([control]), title="Slider", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `value` | `0` | finite number | Assignment |
| `minimum` | `0` | finite number | Constructor only |
| `maximum` | `100` | finite number | Constructor only |
| `step` | `1` | finite number | Constructor only |
| `disabled` | `false` | bool | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

- `on_change(event)`: Runs after native value and Python mirror/bound State change.
- `on_release(event)`: Reports the slider value when the native drag is released.

Handlers can take zero arguments or one `Event`, and can be synchronous or async. They run on the owned Python asyncio loop. See [events and asyncio](../state-and-events.md).

`bind_value(State(...))` binds both ways without echoing native edits back through setters. `unbind()` disposes the subscription. See [state binding](../state-and-events.md).

### Contract and limits

minimum < maximum, step > 0, and value must remain in range. Range and step are fixed. on_release reports the released value.

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L341) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](https://gtrefalt.github.io/gpyui/component-coverage/)

## Rating

Native zero-to-five rating.

### Runnable example

```python
import gpyui as ui

control = ui.Rating(4)

app = ui.Application(ui.Column([control]), title="Rating", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `value` | `0` | nonnegative int | Assignment |
| `disabled` | `false` | bool | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

- `on_change(event)`: Runs after native value and Python mirror/bound State change.

Handlers can take zero arguments or one `Event`, and can be synchronous or async. They run on the owned Python asyncio loop. See [events and asyncio](../state-and-events.md).

`bind_value(State(...))` binds both ways without echoing native edits back through setters. `unbind()` disposes the subscription. See [state binding](../state-and-events.md).

### Contract and limits

value is an integer from 0 through 5, not a navigation index.

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L331) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](https://gtrefalt.github.io/gpyui/component-coverage/)
