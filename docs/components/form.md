# Form

Native form layout with named fields, required indicators and Python validation.

![Native Form preview](../screenshots/components/form.png?v=2e30a5bf9543)

A real Linux/X11 native capture in light appearance. The same control also supports the initial dark theme.

## Runnable example

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

## Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `label_layout` | `"vertical"` | vertical · horizontal | Assignment |
| `columns` | `1` | integer 1–12 | Assignment |
| `label_width` | `140` | nonnegative pixel number | Assignment |
| `size` | `"medium"` | small · medium · large | Assignment |
| `error` | `""` | str | Assignment |

Accepts `children=[...]`, a `with` block, and runtime `add`, `insert`, `remove`, `clear`, `set_children` or assignment to `children`. Each child has one parent. Reuse existing instances to preserve native state; see [runtime composition](../guide/layout.md#runtime-children-and-visibility).

Construct explicit child lists outside a composition context, as in the example. Inside a `with` block, construct the parent first and then its children.

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](../reference/core.md).

## Events and state

`on_submit` accepts a sync/async callback with zero arguments or one copied values dict. `submit_label` and `shortcut` configure the immutable `submit_command`, shared with Button and menus. `await validate()` and `await submit()` return bool; `busy`, `errors` and `values()` expose Python state. See [forms and validation](../guide/forms.md) for hidden fields, stale async validation and retry.

## Contract and limits

Form accepts only uniquely named Field children. on_submit takes zero arguments or an active-values dict. Use submit_command for buttons, menus and shortcuts; see the forms guide for validation, async saving and retry.

All controls accept [pixel layout and semantic theme styling](../guide/styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/forms.py#L109) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](../component-coverage.md)
