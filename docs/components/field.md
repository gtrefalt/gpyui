# Field

Kit field labels, help, required indicators and retained inline error messages.

![Native Field preview](../screenshots/components/field.png?v=51b4a400659a)

A real Linux/X11 native capture in light appearance. The same control also supports the initial dark theme.

## Runnable example

```python
import gpyui as ui

control = ui.Field(
    "Email address",
    name="email",
    control=ui.TextInput("ada@"),
    required=True,
    help="Used only for account updates.",
    error="Enter a complete email address.",
)

app = ui.Application(ui.Column([control]), title="Field", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

## Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `label` | `""` | str | Assignment |
| `name` | `""` | str; nonempty unique name within a Form | Constructor only |
| `help` | `""` | str | Assignment |
| `required` | `false` | bool | Assignment |
| `error` | `""` | str | Assignment |
| `col_span` | `1` | integer 1–12 | Assignment |

Accepts `children=[...]`, a `with` block, and runtime `add`, `insert`, `remove`, `clear`, `set_children` or assignment to `children`. Each child has one parent. Reuse existing instances to preserve native state; see [runtime composition](../guide/layout.md#runtime-children-and-visibility).

Construct explicit child lists outside a composition context, as in the example. Inside a `with` block, construct the parent first and then its children.

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](../reference/core.md).

## Events and state

`control=` accepts a prebuilt value control; alternatively compose children with a `with` block. Validation requires exactly one bindable value control, including within nested layouts. `validators=` is a constructor-only iterable of sync/async callables taking one raw value. Return None/empty string for success or an error message. `control` and `validators` are read-only. See [forms and validation](../guide/forms.md) for the full validation/submission contract.

## Contract and limits

Python validators take one raw value and return None/empty string or an error message, synchronously or asynchronously. A validated field contains exactly one bindable value control, possibly inside child layouts. Field.error is rendered through Kit description_fn, not by replacing an editor.

All controls accept [pixel layout and semantic theme styling](../guide/styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/forms.py#L51) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](../component-coverage.md)
