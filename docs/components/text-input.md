# TextInput

Native single-line text editing.

![Native TextInput preview](../screenshots/components/text-input.png?v=73c34bf5510e)

A real Linux/X11 native capture in light appearance. The same control also supports the initial dark theme.

## Runnable example

```python
import gpyui as ui

control = ui.TextInput("Ada Lovelace", placeholder="Your name", on_change=lambda event: print(event.value))

app = ui.Application(ui.Column([control]), title="TextInput", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

## Properties

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

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](../reference/core.md).

## Events and state

- `on_change(event)`: Runs after native value and Python mirror/bound State change.
- `on_submit(event)`: Receives the current text on Enter, with native input mirrors updated.
- `on_focus(event)`: Receives the current text when native focus is gained.
- `on_blur(event)`: Receives the current text when native focus is lost.

Handlers can take zero arguments or one `Event`, and can be synchronous or async. They run on the owned Python asyncio loop. See [events and asyncio](../guide/events.md).

`bind_value(State(...))` binds both ways without echoing native edits back through setters. `unbind()` disposes the subscription. See [state binding](../guide/state.md).

## Contract and limits

Programmatic value replacement clears native undo history; native edits are never echoed back through the setter. disabled, read_only, password, clearable and string prefix/suffix options are mutable. on_submit, on_focus and on_blur report native events; password only masks display, not values or snapshots.

All controls accept [pixel layout and semantic theme styling](../guide/styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/controls.py#L265) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/view.rs) · [Full coverage and remaining Kit APIs](../component-coverage.md)
