# Label

A native text label.

![Native Label preview](../screenshots/components/label.png?v=4cd36b28ddd8)

A real Linux/X11 native capture in light appearance. The same control also supports the initial dark theme.

## Runnable example

```python
import gpyui as ui

control = ui.Label("Hello from Python").style(font_size=24, bold=True)

app = ui.Application(ui.Column([control]), title="Label", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

## Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `text` | `""` | str | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](../reference/core.md).

## Events and state

This wrapper exposes no Python activation/change handler. Update its mutable properties by assignment from a running callback. Native behavior remains in Rust.

`bind_text(State(...), transform)` provides one-way text binding.

All controls accept [pixel layout and semantic theme styling](../guide/styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/controls.py#L244) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/view.rs) · [Full coverage and remaining Kit APIs](../component-coverage.md)
