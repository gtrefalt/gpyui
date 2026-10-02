# State and binding

`State(value)` is an explicit observable. Setters and native events propagate
changes with equality guards. gpyui does not poll arbitrary Python attributes.

## Two-way values and one-way text

```python
from gpyui import Application, Checkbox, Column, Label, State, TextInput

name = State("Ada")
enabled = State(True)
app = Application(title="Bindings", width=540, height=320)
with app, Column():
    TextInput().bind_value(name)
    Checkbox("Enable notifications").bind_value(enabled)
    Label().bind_text(name, lambda value: f"Hello, {value}!")
    Label().bind_text(enabled, lambda value: "Enabled" if value else "Disabled")
app.run()
```

`bind_value` exists on editable/selection controls that expose native change
events. A native edit first updates the Python value and bound State, then
invokes `on_change`. The update does not echo through the native setter, so caret,
selection and undo remain owned by Rust.

`Label.bind_text(state, transform)` binds in one direction. Its default transform
is `str`. `unbind()` removes a control's subscriptions; app shutdown unbinds
mounted controls.

## Observe state yourself

```python
from gpyui import State

count = State(0)
unsubscribe = count.subscribe(lambda value: print("Count:", value))
count.value = 1
unsubscribe()
```

The unsubscribe function is idempotent. Mutate bound state on the callback loop
while the app runs; use `app.call_soon(...)` to hand work over from other threads.

## Value types

| Controls | Value |
| --- | --- |
| TextInput, TextArea, NumberInput, OtpInput, Editor | String editing buffer |
| Checkbox, Switch, Radio, Toggle, Collapsible, Dialog, Sheet | Boolean |
| RadioGroup, tabs/navigation, Pagination, List, Table, Carousel | Zero-based index |
| Rating | Integer 0–5 |
| Slider | Scalar number in its configured range |
| Select, Combobox | Selected string or `""` |
| Tree | Stable item ID or `""` |
| Calendar, DatePicker | ISO single date or `""` |
| TimeField | Local `HH:MM:SS` string |
| ColorPicker | `#rrggbb` or `#rrggbbaa` |

Collections such as `Table.rows` and `LineChart.data` return copies. Reassign a
collection to submit an update: `table.rows = [*table.rows, new_row]`.
