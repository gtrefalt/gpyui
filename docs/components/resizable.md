# Resizable

Native draggable boundaries between panes.

![Native Resizable preview](../screenshots/components/resizable.png)

A real Linux/X11 native capture. The preview uses dark appearance; the same control supports the initial light theme.

## Runnable example

```python
import gpyui as ui

control = ui.Resizable(children=[ui.Label("Files"), ui.Label("Editor")]).style(height=150, full_width=True)

app = ui.Application(ui.Column([control]), title="Resizable", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

## Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `vertical` | `false` | bool | Constructor only |

Accepts `children=[...]`, a `with` block, and `add(...)` before mounting. Each child has one parent. The mounted topology is fixed.

Construct explicit child lists outside a composition context, as in the example. Inside a `with` block, construct the parent first and then its children.

## Events and state

- `on_resize(event)`: Reports native panel sizes after a resize.

Handlers can take zero arguments or one `Event`, and can be synchronous or async. They run on the owned Python asyncio loop. See [events and asyncio](../guide/events.md).

## Contract and limits

Axis is fixed after construction. on_resize receives native panel sizes.

All controls accept [pixel layout and semantic theme styling](../guide/styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L682) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](../component-coverage.md)
