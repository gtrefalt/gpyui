# Native forms and Python validation

Available in gpyui 0.5.0. Confirm the installed version exports Form, Field and
ValidationError before using them.

Form/Field render actual Kit builders in Rust. Python validates and submits;
native input entities retain text, caret, selection and undo. Do not replace
editors or assign normalized text when validation fails.

```python
import asyncio
import json
from pathlib import Path
from gpyui import Application, Button, Column, Field, Form, Label, TextInput

app = Application(title="Profile", width=540, height=420, theme="light")


def check_name(value):
    return None if len(value.strip()) >= 3 else "Use at least three characters."


async def save(values):
    await asyncio.to_thread(Path("profile.json").write_text, json.dumps(values), encoding="utf-8")
    status.text = "Profile saved."


with app, Column().style(full_width=True, gap=12):
    with Form(on_submit=save, submit_label="Save profile", shortcut="mod+s") as form:
        with Field(
            "Display name",
            name="name",
            required=True,
            help="Shown to your teammates.",
            validators=[check_name],
        ):
            editor = TextInput(placeholder="Ada Lovelace").style(full_width=True)
    Button(command=form.submit_command, variant="outline")
    status = Label("Not saved yet.")

app.run()
```

Form accepts only directly nested Fields with nonempty unique immutable names.
Actions belong outside it. Each validated Field resolves exactly one bindable
value control, also within nested layouts. Prebuilt `control=` and `children=`
are alternatives to context composition; construct explicit children outside a
`with` block. Field validators are immutable callable tuples.

Form supports label_layout vertical/horizontal, columns 1–12, nonnegative pixel
label_width and small/medium/large size. Field supports mutable label, help,
required, error, col_span 1–12 and visible. The component family reference lists
exact constructor properties. Standalone Fields render without owning submit.

Validators take one copied raw value, run sequentially on the Python callback
loop, and may be async. None/empty string succeeds; a nonempty string or ValueError
becomes inline error. Required checking runs first: None, False, blank strings
and empty lists fail; numeric zero succeeds. NumberInput remains an editing
string; parse/normalize a copied payload in the save callback. Unexpected
exceptions and non-string validator results are programming errors.

`await form.validate()` validates only; `await form.submit()` validates and saves.
Both return bool and return False while busy. `form.values()` returns copied
active raw values, `form.errors` active inline errors, `form.error` a summary and
`form.clear_errors()` clears all errors. Errors persist until the next validation
or explicit clearing, not until the next keystroke.

Hide a Field to omit it from validation and values while retaining its editor.
Hidden ancestors and detached Forms also make fields inactive. No active fields
is an unsuccessful submission. After async validation, changes to active field
order/identity, editor identity, required or raw values discard the results and
prevent saving. This compares completion state with captured state, not revisions.

Reuse `form.submit_command` for buttons, menus and its configured shortcut.
Activation captures current native input values. busy disables the shared command
for validation and saving, rejects duplicate work and restores its prior enabled
state in finally. on_submit takes zero arguments or one copied raw-values dict;
it can be sync or async and its return value is ignored. Editing during saving
does not overwrite newer edits; feedback should identify the saved snapshot.

Raise OSError for expected save failure: the summary displays it and the same
command can retry. Raise `ValidationError({"name": "Already used."}, "Review the profile.")`
for named submit/server errors. Names must identify active captured fields;
discard named errors if edits changed while saving. Other exceptions follow
Application.errors/on_error. Cancellation must propagate. Never block the
callback loop; use async I/O or to_thread. Already-started worker I/O may finish
after cancellation; catch ApplicationClosedError when restoring UI on shutdown.

Limits: no typed schema engine, per-keystroke validation, custom focus API or
Python caret/undo setters. Use retained visible controls and explicit validation.

[Composition](composition.md) · [State and asyncio](state-and-events.md) ·
[Commands](commands-and-menus.md) · [Forms component contracts](components/forms.md)
