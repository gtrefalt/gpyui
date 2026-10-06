# Button

Native activation invokes Python callbacks.

![Native Button preview](../screenshots/components/button.png?v=48327355dc73)

A real Linux/X11 native capture in light appearance. The same control also supports the initial dark theme.

## Runnable example

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

## Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `text` | `null` | str; defaults to command.label | Assignment |
| `command` | `null` | Command; mutually exclusive with on_click | Constructor only |
| `disabled` | `false` | bool | Assignment |
| `variant` | `"secondary"` | primary · secondary · outline · ghost · danger | Constructor only |
| `icon` | `""` | Lucide name | Constructor only |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](../reference/core.md).

## Events and state

- `on_click(event)`: Native pointer or keyboard activation, with current input-value snapshots.

Handlers can take zero arguments or one `Event`, and can be synchronous or async. They run on the owned Python asyncio loop. See [events and asyncio](../guide/events.md).

All controls accept [pixel layout and semantic theme styling](../guide/styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/controls.py#L317) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/view.rs) · [Full coverage and remaining Kit APIs](../component-coverage.md)
