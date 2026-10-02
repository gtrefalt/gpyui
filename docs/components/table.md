# Table

Native retained table state with string rows.

![Native Table preview](../screenshots/components/table.png?v=9c4618ea2d84)

A real Linux/X11 native capture in light appearance. The same control also supports the initial dark theme.

## Runnable example

```python
import gpyui as ui

control = ui.Table(
    columns=["Name", "Language", "Status"],
    rows=[["gpyui", "Python", "Ready"], ["GPUI Kit", "Rust", "Native"]],
    column_width=185,
).style(height=160, full_width=True)

app = ui.Application(ui.Column([control]), title="Table", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

## Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `columns` | `[]` | list[str] | Constructor only |
| `rows` | `[]` | list[list[str]] | Assignment |
| `value` | `0` | nonnegative int | Assignment |
| `column_width` | `125` | finite number | Constructor only |

## Events and state

- `on_change(event)`: Runs after native value and Python mirror/bound State change.

Handlers can take zero arguments or one `Event`, and can be synchronous or async. They run on the owned Python asyncio loop. See [events and asyncio](../guide/events.md).

`bind_value(State(...))` binds both ways without echoing native edits back through setters. `unbind()` disposes the subscription. See [state binding](../guide/state.md).

## Contract and limits

Rows must match the column count. Columns and column_width are fixed. Reassign rows to refresh. value is the selected zero-based row index; native selection initially may be empty while the Python default is zero.

All controls accept [pixel layout and semantic theme styling](../guide/styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L476) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](../component-coverage.md)
