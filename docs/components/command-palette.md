# CommandPalette

Search and execute shared native commands.

![Native CommandPalette preview](../screenshots/components/command-palette.png?v=5d916acdbec2)

A real Linux/X11 native capture in light appearance. The same control also supports the initial dark theme.

## Runnable example

```python
import gpyui as ui

control = ui.CommandPalette(
    [
        ui.Command("Save document", lambda: None, shortcut="mod+s"),
        ui.Command("Open document", lambda: None, shortcut="mod+o"),
        ui.Command("Export report", lambda: None, enabled=False),
    ]
)

app = ui.Application(ui.Column([control]), title="CommandPalette", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

## Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `commands` | `[]` | Iterable[Command] | Assignment |
| `query` | `""` | str | Assignment |
| `placeholder` | `"Search commands…"` | str | Assignment |
| `searchable` | `true` | bool | Assignment |
| `filterable` | `true` | bool | Assignment |
| `loading` | `false` | bool | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](../reference/core.md).

## Events and state

- `on_query(event)`: Receives the current search query after its Python mirror changes.
- `on_cancel(event)`: Reports Escape after the query is empty; a hosting Dialog owns dismissal.

Handlers can take zero arguments or one `Event`, and can be synchronous or async. They run on the owned Python asyncio loop. See [events and asyncio](../guide/events.md).

`bind_value(State(...))` binds both ways without echoing native edits back through setters. `unbind()` disposes the subscription. See [state binding](../guide/state.md).

## Contract and limits

commands and query are mutable. Command enabled/checked state and shortcut hints remain shared with buttons and menus. on_query receives changed query strings; on_cancel reports Escape with an empty query. Compose inside Dialog for an overlay. External search can use filterable=False and loading; async providers must discard stale results themselves.

All controls accept [pixel layout and semantic theme styling](../guide/styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/commands.py#L252) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/view.rs) · [Full coverage and remaining Kit APIs](../component-coverage.md)
