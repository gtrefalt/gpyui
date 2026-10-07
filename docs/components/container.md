# Container

A composable GPUI layout surface.

![Native Container preview](../screenshots/components/container.png?v=c4b11a4bbd6e)

A real Linux/X11 native capture in light appearance. The same control also supports the initial dark theme.

## Runnable example

```python
import gpyui as ui

control = ui.Container([ui.Label("A themed surface"), ui.Label("Compose children in Python.")]).style(
    padding=20, gap=12, background="muted", radius=12
)

app = ui.Application(ui.Column([control]), title="Container", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

## Properties

This control has no component-specific constructor properties.

Accepts `children=[...]`, a `with` block, and runtime `add`, `insert`, `remove`, `clear`, `set_children` or assignment to `children`. Each child has one parent. Reuse existing instances to preserve native state; see [runtime composition](../guide/layout.md#runtime-children-and-visibility).

Construct explicit child lists outside a composition context, as in the example. Inside a `with` block, construct the parent first and then its children.

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](../reference/core.md).

## Events and state

This wrapper exposes no Python activation/change handler. Update its mutable properties by assignment from a running callback. Native behavior remains in Rust.

All controls accept [pixel layout and semantic theme styling](../guide/styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L305) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](../component-coverage.md)
