# Forms and validation

`Form` and `Field` render GPUI Kit's actual native components. Rust owns layout,
labels, descriptions and the retained editors. Python owns validation and saving.
This API is introduced in gpyui 0.5.0.

## Compose a form

```python
import asyncio
import json
from pathlib import Path
from gpyui import Application, Button, Column, Field, Form, Label, TextInput

app = Application(title="Profile", width=540, height=420, theme="light")

def check_name(value):
    return None if len(value.strip()) >= 3 else "Use at least three characters."

async def save(values):
    await asyncio.to_thread(
        Path("profile.json").write_text, json.dumps(values), encoding="utf-8"
    )
    status.text = "Profile saved."

with app, Column().style(full_width=True, gap=12):
    with Form(on_submit=save, submit_label="Save profile", shortcut="mod+s") as form:
        with Field("Display name", name="name", required=True,
                   help="Shown to your teammates.", validators=[check_name]):
            name = TextInput(placeholder="Ada Lovelace").style(full_width=True)
    Button(command=form.submit_command, variant="outline")
    status = Label("Not saved yet.")

app.run()
```

A Form accepts only Fields with nonempty unique names. Compose actions outside
the Form. Each validated Field contains exactly one value control, optionally
inside a nested layout. Use a `with` block as above, or prebuild controls outside
a composition context and pass `Field(control=editor)` and `Form(children=[...])`.
`Field.name`, `Field.validators` and `Field.control` are read-only; change the
child tree explicitly to replace an editor.

Kit supports `label_layout="vertical"` (default) or `"horizontal"`,
`columns=1..12`, a nonnegative pixel `label_width`, and `size="small"`,
`"medium"` or `"large"`. Fields support `col_span=1..12`. `label`, `help`,
`required`, `error` and visibility are mutable. Standalone Field layout is
supported, but automatic validation/submission belongs to its Form.

## Validate raw editing values

`validators=[...]` accepts sync or async callables taking one value. Validators
run sequentially in field order on the application's Python asyncio loop. Return
`None` or `""` for success, or a nonempty string to show an inline error. A
`ValueError` becomes its message. Other exceptions and invalid return types are
programming errors handled through the normal application error path.

Required validation runs first. `None`, `False`, whitespace-only strings and
empty lists fail; numeric zero is valid. A required checkbox therefore means it
must be checked. Only the first error per Field is shown. `await form.validate()`
returns a bool without saving; `await form.submit()` validates, then saves on
success. Both reject concurrent operations with `False`.

Values use each control's existing type: TextInput, TextArea and NumberInput
return editing strings, Boolean controls return bool, and selection controls
keep their documented contracts. Parse and normalize a copied submitted dict in
your save callback. Validation never writes normalized data back into an editor.

`form.values()` returns copied raw values for active fields. `form.errors`
returns their inline errors. `form.error` holds the summary/save error.
`form.clear_errors()` clears summaries and all Fields. Errors remain until a
validation attempt replaces them or your code clears them; there is no implicit
validation on every keystroke.

## Conditional fields and async safety

Set `field.visible = False` to omit a field from both validation and the submitted
dict. Hidden editors retain their contents and native state. Hiding an ancestor
or detaching the Form makes its fields inactive. A form with no active fields
returns False with a summary. Showing a field reuses its editor.

After awaited validation, the Form checks active field identity/order, editor
identity, required flags and raw values. If they changed, it discards validation
results and asks the user to try again. It does not save a stale snapshot or
apply stale errors. This is a comparison at completion, not a revision log:
changing a value and restoring it to the captured value is treated as unchanged.

Once saving begins, the callback owns a copied values dict. Users can continue
editing; successful saves never rewrite newer edits. Your app should say what
was saved if edits during a save matter to its workflow.

## Shared submission, errors and retry

`form.submit_command` is a real shared Command. Use it with Button, DropdownMenu,
context menus and application menus. `submit_label` and `shortcut` configure it
at construction. Activation uses current native input values. During validation
or saving, `form.busy` is True and the command is disabled, so every associated
action agrees and duplicate requests cannot start another save. The previous
enabled state is restored in `finally`, including cancellation.

`on_submit` accepts a sync/async callback taking zero arguments or one copied
dict. It runs only after valid input. Return values are ignored. Raise `OSError`
for an expected I/O failure: the message is shown in `form.error` and the user can
retry the same command. Raise `ValidationError({"field_name": "message"}, message)`
for expected submission/server validation. Names must identify active captured
fields. If input changed while saving, named errors are discarded and a summary
asks for review. Unexpected exceptions propagate to `Application.errors` and
`on_error`; cancellation propagates without becoming a validation message.

Do not block a sync validator or save callback. Await asynchronous clients or
use `asyncio.to_thread` for blocking I/O. Window shutdown cancels owned callbacks;
worker-thread I/O already started may still complete. Keep UI cleanup tolerant
of `ApplicationClosedError` and retain text controls on failure.

See the [settings editor](../examples/settings.md),
[Form reference](../components/form.md), [Field reference](../components/field.md)
and [source-grounded implementation notes](../plans/forms-validation.md).
