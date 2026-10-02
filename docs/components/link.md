# Link

A native link with optional Python activation.

![Native Link preview](../screenshots/components/link.png?v=a5d439863218)

A real Linux/X11 native capture in light appearance. The same control also supports the initial dark theme.

## Runnable example

```python
import gpyui as ui

control = ui.Link("Explore GPUI Kit ↗", href="https://gpui-kit.com")

app = ui.Application(ui.Column([control]), title="Link", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

## Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `text` | `""` | str | Assignment |
| `href` | `""` | str | Assignment |
| `disabled` | `false` | bool | Assignment |

## Events and state

- `on_click(event)`: Native pointer or keyboard activation, with current input-value snapshots.

Handlers can take zero arguments or one `Event`, and can be synchronous or async. They run on the owned Python asyncio loop. See [events and asyncio](../guide/events.md).

All controls accept [pixel layout and semantic theme styling](../guide/styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L406) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](../component-coverage.md)
