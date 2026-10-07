# Text and buttons

Generated Python API reference from the repository (manifest version 0.6.1).
Follows the repository manifest; check [release status and coverage](../coverage.md) against your installed version.

## Label

A native text label.

### Runnable example

```python
import gpyui as ui

control = ui.Label("Hello from Python").style(font_size=24, bold=True)

app = ui.Application(ui.Column([control]), title="Label", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `text` | `""` | str | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

This wrapper exposes no Python activation/change handler. Update its mutable properties by assignment from a running callback. Native behavior remains in Rust.

`bind_text(State(...), transform)` provides one-way text binding.

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/controls.py#L247) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/view.rs) · [Full coverage and remaining Kit APIs](../coverage.md)

## Button

Native activation invokes Python callbacks.

### Runnable example

```python
import gpyui as ui

status = ui.Label("Choose Save")
control = ui.Button(
    "Save", variant="primary", icon="save", on_click=lambda: setattr(status, "text", "Saved from Python")
)

app = ui.Application(ui.Column([status, control]), title="Button", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `text` | `null` | str; defaults to command.label | Assignment |
| `command` | `null` | Command; mutually exclusive with on_click | Constructor only |
| `disabled` | `false` | bool | Assignment |
| `variant` | `"secondary"` | primary · secondary · outline · ghost · danger | Constructor only |
| `icon` | `""` | Lucide name | Constructor only |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

- `on_click(event)`: Native pointer or keyboard activation, with current input-value snapshots.

Handlers can take zero arguments or one `Event`, and can be synchronous or async. They run on the owned Python asyncio loop. See [events and asyncio](../state-and-events.md).

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/controls.py#L366) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/view.rs) · [Full coverage and remaining Kit APIs](../coverage.md)

## DropdownMenu

A Kit button with nested commands, checks and shortcut hints.

### Runnable example

```python
import gpyui as ui

save = ui.Command("Save", lambda: print("Save requested"), shortcut="mod+s")
sidebar = ui.Command("Show sidebar", lambda: print("Sidebar requested"), checked=True)
control = ui.DropdownMenu("Actions", [save, ui.MenuSeparator(), ui.Menu("View", [sidebar])])

app = ui.Application(ui.Column([control]), title="DropdownMenu", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `text` | Required | str | Assignment |
| `items` | Required | Iterable[Command | Menu | MenuSeparator] | Assignment |
| `disabled` | `false` | bool | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

Menu activation calls the selected `Command.on_execute` callback with current native input values. See [commands and menus](../commands-and-menus.md).

### Contract and limits

Items are Command, Menu or MenuSeparator models. Reassign items to update an open menu. Shared enabled/checked state and callbacks are owned by Command; see the commands guide.

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/commands.py#L202) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/view.rs) · [Full coverage and remaining Kit APIs](../coverage.md)

## CommandPalette

Search and execute shared native commands.

### Runnable example

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

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `commands` | `[]` | Iterable[Command] | Assignment |
| `query` | `""` | str | Assignment |
| `placeholder` | `"Search commands…"` | str | Assignment |
| `searchable` | `true` | bool | Assignment |
| `filterable` | `true` | bool | Assignment |
| `loading` | `false` | bool | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

- `on_query(event)`: Receives the current search query after its Python mirror changes.
- `on_cancel(event)`: Reports Escape after the query is empty; a hosting Dialog owns dismissal.

Handlers can take zero arguments or one `Event`, and can be synchronous or async. They run on the owned Python asyncio loop. See [events and asyncio](../state-and-events.md).

`bind_value(State(...))` binds both ways without echoing native edits back through setters. `unbind()` disposes the subscription. See [state binding](../state-and-events.md).

### Contract and limits

commands and query are mutable. Command enabled/checked state and shortcut hints remain shared with buttons and menus. on_query receives changed query strings; on_cancel reports Escape with an empty query. Compose inside Dialog for an overlay. External search can use filterable=False and loading; async providers must discard stale results themselves.

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/commands.py#L252) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/view.rs) · [Full coverage and remaining Kit APIs](../coverage.md)

## Link

A native link with optional Python activation.

### Runnable example

```python
import gpyui as ui

control = ui.Link("Explore GPUI Kit ↗", href="https://gpui-kit.com")

app = ui.Application(ui.Column([control]), title="Link", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `text` | `""` | str | Assignment |
| `href` | `""` | str | Assignment |
| `disabled` | `false` | bool | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

- `on_click(event)`: Native pointer or keyboard activation, with current input-value snapshots.

Handlers can take zero arguments or one `Event`, and can be synchronous or async. They run on the owned Python asyncio loop. See [events and asyncio](../state-and-events.md).

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L463) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](../coverage.md)

## Clipboard

Copy a string using the native clipboard.

### Runnable example

```python
import gpyui as ui

control = ui.Clipboard("Copied from gpyui")

app = ui.Application(ui.Column([control]), title="Clipboard", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `text` | `""` | str | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

This wrapper exposes no Python activation/change handler. Update its mutable properties by assignment from a running callback. Native behavior remains in Rust.

### Contract and limits

The native copy affordance owns clipboard behavior.

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L728) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](../coverage.md)

## Icon

Bundled Lucide icons rendered natively.

### Runnable example

```python
import gpyui as ui

control = ui.Icon("sparkles").style(width=32, height=32, color="primary")

app = ui.Application(ui.Column([control]), title="Icon", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `name` | `"check"` | str | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

This wrapper exposes no Python activation/change handler. Update its mutable properties by assignment from a running callback. Native behavior remains in Rust.

### Contract and limits

Use lowercase kebab-case Lucide names. Names must refer to bundled assets.

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L448) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](../coverage.md)

## Kbd

Display a parsed native keyboard shortcut.

### Runnable example

```python
import gpyui as ui

control = ui.Kbd("ctrl-shift-p")

app = ui.Application(ui.Column([control]), title="Kbd", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `key` | `"ctrl-k"` | str | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

This wrapper exposes no Python activation/change handler. Update its mutable properties by assignment from a running callback. Native behavior remains in Rust.

### Contract and limits

This displays a shortcut; it does not register a Python command handler.

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L511) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](../coverage.md)

## Separator

A native divider, optionally with a label.

### Runnable example

```python
import gpyui as ui

control = ui.Separator("Details").style(full_width=True)

app = ui.Application(ui.Column([control]), title="Separator", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `text` | `""` | str | Assignment |
| `vertical` | `false` | bool | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

This wrapper exposes no Python activation/change handler. Update its mutable properties by assignment from a running callback. Native behavior remains in Rust.

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L458) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](../coverage.md)
