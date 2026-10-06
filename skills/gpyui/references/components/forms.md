# Forms

Generated Python API reference for gpyui 0.5.0.

## Form

Native form layout with named fields, required indicators and Python validation.

### Runnable example

```python
import gpyui as ui

control = ui.Form(
    on_submit=lambda values: print(values),
    children=[
        ui.Field(
            "Display name",
            name="name",
            control=ui.TextInput("Ada"),
            required=True,
            help="Shown to your teammates.",
        ),
        ui.Field(
            "Notifications", name="notifications", control=ui.Switch("Desktop notifications", value=True)
        ),
    ],
)
save = ui.Button(command=control.submit_command, variant="outline")

app = ui.Application(ui.Column([control, save]), title="Form", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `label_layout` | `"vertical"` | vertical · horizontal | Assignment |
| `columns` | `1` | integer 1–12 | Assignment |
| `label_width` | `140` | nonnegative pixel number | Assignment |
| `size` | `"medium"` | small · medium · large | Assignment |
| `error` | `""` | str | Assignment |

Accepts `children=[...]`, a `with` block, and runtime `add`, `insert`, `remove`, `clear`, `set_children` or assignment to `children`. Each child has one parent. Reuse existing instances to preserve native state; see [runtime composition](../composition.md#dynamic-composition).

Construct explicit child lists outside a composition context, as in the example. Inside a `with` block, construct the parent first and then its children.

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

`on_submit` accepts a sync/async callback with zero arguments or one copied values dict. `submit_label` and `shortcut` configure the immutable `submit_command`, shared with Button and menus. `await validate()` and `await submit()` return bool; `busy`, `errors` and `values()` expose Python state. See [forms and validation](../forms.md) for hidden fields, stale async validation and retry.

### Contract and limits

Form accepts only uniquely named Field children. on_submit takes zero arguments or an active-values dict. Use submit_command for buttons, menus and shortcuts; see the forms guide for validation, async saving and retry.

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/forms.py#L109) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](https://gtrefalt.github.io/gpyui/component-coverage/)

## Field

Kit field labels, help, required indicators and retained inline error messages.

### Runnable example

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

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `label` | `""` | str | Assignment |
| `name` | `""` | str; nonempty unique name within a Form | Constructor only |
| `help` | `""` | str | Assignment |
| `required` | `false` | bool | Assignment |
| `error` | `""` | str | Assignment |
| `col_span` | `1` | integer 1–12 | Assignment |

Accepts `children=[...]`, a `with` block, and runtime `add`, `insert`, `remove`, `clear`, `set_children` or assignment to `children`. Each child has one parent. Reuse existing instances to preserve native state; see [runtime composition](../composition.md#dynamic-composition).

Construct explicit child lists outside a composition context, as in the example. Inside a `with` block, construct the parent first and then its children.

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

`control=` accepts a prebuilt value control; alternatively compose children with a `with` block. Validation requires exactly one bindable value control, including within nested layouts. `validators=` is a constructor-only iterable of sync/async callables taking one raw value. Return None/empty string for success or an error message. `control` and `validators` are read-only. See [forms and validation](../forms.md) for the full validation/submission contract.

### Contract and limits

Python validators take one raw value and return None/empty string or an error message, synchronously or asynchronously. A validated field contains exactly one bindable value control, possibly inside child layouts. Field.error is rendered through Kit description_fn, not by replacing an editor.

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/forms.py#L51) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](https://gtrefalt.github.io/gpyui/component-coverage/)
