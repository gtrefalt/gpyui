# Inputs

Generated Python API reference from the repository (manifest version 0.6.1).
Follows the repository manifest; check [release status and coverage](../coverage.md) against your installed version.

## TextInput

Native single-line text editing.

### Runnable example

```python
import gpyui as ui

control = ui.TextInput("Ada Lovelace", placeholder="Your name", on_change=lambda event: print(event.value))

app = ui.Application(ui.Column([control]), title="TextInput", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `value` | `""` | str | Assignment |
| `placeholder` | `""` | str | Assignment |
| `disabled` | `false` | bool | Assignment |
| `read_only` | `false` | bool | Assignment |
| `password` | `false` | bool | Assignment |
| `clearable` | `false` | bool | Assignment |
| `prefix` | `""` | str | Assignment |
| `suffix` | `""` | str | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

- `on_change(event)`: Runs after native value and Python mirror/bound State change.
- `on_submit(event)`: Receives the current text on Enter, with native input mirrors updated.
- `on_focus(event)`: Receives the current text when native focus is gained.
- `on_blur(event)`: Receives the current text when native focus is lost.

Handlers can take zero arguments or one `Event`, and can be synchronous or async. They run on the owned Python asyncio loop. See [events and asyncio](../state-and-events.md).

`bind_value(State(...))` binds both ways without echoing native edits back through setters. `unbind()` disposes the subscription. See [state binding](../state-and-events.md).

### Contract and limits

Programmatic value replacement clears native undo history; native edits are never echoed back through the setter. disabled, read_only, password, clearable and string prefix/suffix options are mutable. on_submit, on_focus and on_blur report native events; password only masks display, not values or snapshots.

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/controls.py#L265) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/view.rs) · [Full coverage and remaining Kit APIs](../coverage.md)

## TextArea

Native multiline editing.

### Runnable example

```python
import gpyui as ui

control = ui.TextArea("A native multiline field.\nFocus, caret and undo stay in Rust.").style(height=120)

app = ui.Application(ui.Column([control]), title="TextArea", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `value` | `""` | str | Assignment |
| `placeholder` | `""` | str | Assignment |
| `disabled` | `false` | bool | Assignment |
| `read_only` | `false` | bool | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

- `on_change(event)`: Runs after native value and Python mirror/bound State change.

Handlers can take zero arguments or one `Event`, and can be synchronous or async. They run on the owned Python asyncio loop. See [events and asyncio](../state-and-events.md).

`bind_value(State(...))` binds both ways without echoing native edits back through setters. `unbind()` disposes the subscription. See [state binding](../state-and-events.md).

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L783) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](../coverage.md)

## NumberInput

A native numeric editing buffer with step buttons.

### Runnable example

```python
import gpyui as ui

control = ui.NumberInput("42", placeholder="Quantity")

app = ui.Application(ui.Column([control]), title="NumberInput", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `value` | `""` | str | Assignment |
| `placeholder` | `""` | str | Assignment |
| `disabled` | `false` | bool | Assignment |
| `minimum` | `null` | finite number or None | Assignment |
| `maximum` | `null` | finite number or None | Assignment |
| `step` | `1` | finite number | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

- `on_change(event)`: Runs after native value and Python mirror/bound State change.

Handlers can take zero arguments or one `Event`, and can be synchronous or async. They run on the owned Python asyncio loop. See [events and asyncio](../state-and-events.md).

`bind_value(State(...))` binds both ways without echoing native edits back through setters. `unbind()` disposes the subscription. See [state binding](../state-and-events.md).

### Contract and limits

value is a string, including partially edited input. minimum/maximum accept finite numbers or None; step is positive and defaults to one. Native stepping and blur clamp completed numbers to the bounds; partial edits remain strings.

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L789) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](../coverage.md)

## OtpInput

Native one-time-code editing.

### Runnable example

```python
import gpyui as ui

control = ui.OtpInput("123", length=6)

app = ui.Application(ui.Column([control]), title="OtpInput", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `value` | `""` | str | Assignment |
| `length` | `6` | nonnegative int | Constructor only |
| `disabled` | `false` | bool | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

- `on_change(event)`: Runs after native value and Python mirror/bound State change.

Handlers can take zero arguments or one `Event`, and can be synchronous or async. They run on the owned Python asyncio loop. See [events and asyncio](../state-and-events.md).

`bind_value(State(...))` binds both ways without echoing native edits back through setters. `unbind()` disposes the subscription. See [state binding](../state-and-events.md).

### Contract and limits

Only ASCII digits are accepted, up to length. Length is fixed and must be between 1 and 32.

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L813) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](../coverage.md)

## Editor

A retained native editor buffer.

### Runnable example

```python
import gpyui as ui

control = ui.Editor("def greet(name):\n    return name.upper()\n").style(height=150)

app = ui.Application(ui.Column([control]), title="Editor", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `value` | `""` | str | Assignment |
| `placeholder` | `""` | str | Assignment |
| `disabled` | `false` | bool | Assignment |
| `read_only` | `false` | bool | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

- `on_change(event)`: Runs after native value and Python mirror/bound State change.

Handlers can take zero arguments or one `Event`, and can be synchronous or async. They run on the owned Python asyncio loop. See [events and asyncio](../state-and-events.md).

`bind_value(State(...))` binds both ways without echoing native edits back through setters. `unbind()` disposes the subscription. See [state binding](../state-and-events.md).

### Contract and limits

Basic editing is exposed; Python language-server and provider hooks remain future work.

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L899) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](../coverage.md)
