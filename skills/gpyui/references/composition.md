# Composition and component conventions

## Pick a control by its job

| Job | Python controls | Owner and contract |
| --- | --- | --- |
| Execute a command | Button | `on_click`; application owns operation |
| Edit text | TextInput, TextArea, Editor, NumberInput, OtpInput | Rust retains buffer/caret/undo; Python reads string `value` |
| Toggle a setting | Checkbox, Switch, Toggle | Boolean `value`, `on_change` |
| Choose one item | RadioGroup, Select, Combobox | RadioGroup index; Select/Combobox string |
| Navigate | Tabs, Sidebar, Breadcrumb, Stepper, Pagination | Index and `on_change`; application owns content behavior |
| Browse data | List, Table, Tree | List/Table selected index; Tree stable string ID |
| Compose geometry | Column, Row, Container, GroupBox, Scroll, Resizable | Children created before mount; Rust lays out and scrolls |
| Present a workflow overlay | Dialog, Sheet | Boolean `value`, `open()`, `close()`, `on_change` |
| Show feedback | Label, Alert, Tag, Progress, notification | Mutable text/status; `app.notify()` is runtime-only |
| Plot data | LineChart, AreaChart, BarChart, PieChart, CandlestickChart | Reassigned `data` collection; constructor contract per chart |

The window supports one native Dialog and one Sheet at a time. Their titles are
fixed; do not promise a stack of independent modal windows.

Read the exact family in [the catalog](components.md) for supported properties
and limits. The actual Python wrappers control what is available, even when the
Rust Kit component has additional builders.

## Context composition

```python
from gpyui import Application, Button, Column, Label, Row, TextInput

app = Application(title="Profile", width=560, height=360)
with app, Column().style(gap=16, padding=24, align="stretch"):
    Label("Profile").style(font_size=22, bold=True)
    Label("Display name")
    name = TextInput(placeholder="Ada Lovelace")
    with Row().style(gap=8):
        Button("Save profile", variant="primary")
        Button("Cancel", variant="outline")
```

A new control attaches to the innermost active container. `.style()` returns the
same control. Each control has one parent, and cycles/reparenting are rejected.
Do not add context-created children again or pass them to another parent.

## Explicit trees

```python
from gpyui import Application, Button, Column, Label, Row, TextInput

# Build this outside a `with app` or other composition context.
name = TextInput(placeholder="Ada Lovelace")
actions = Row([Button("Save profile", variant="primary"), Button("Cancel", variant="outline")])
app = Application(Column([Label("Display name"), name, actions]).style(gap=12, padding=24))
```

Both forms are supported. Build reusable application sections with functions
returning an unparented control (and any required handles/model). Call explicit
tree builders outside composition contexts, then pass their results as children.
Alternatively, write context-based helpers that attach controls to the active
parent; do not reattach their results. A caller's active context also applies
inside helper functions. Choose a consistent calling convention.

## Component constructor rules

`Label(text="")`, `TextInput(value="", *, placeholder="", on_change=None)` and
`Button(text, *, on_click=None, disabled=False, variant="secondary", icon="")`
have explicit signatures. `Column(children=())` accepts an iterable.

The other Kit controls accept at most one positional property: the first field
shown in their catalog table. Other fields and `on_<event>` handlers are keyword
arguments. Containers accept `children=[...]` or a `with` block. A container
without fields (Row, Container, Scroll, Toolbar, StatusBar, Bubble) also accepts
its children as the sole positional argument. Use `children=` for containers
with fields, such as `GroupBox("Settings", children=[...])` and Resizable.

Assign mutable properties directly: `label.text = "Saved"`,
`save.disabled = True`, `table.rows = new_rows`. Constructor-only fields cannot
change after construction, even before mount. In particular, Select/Combobox
choices and Tree items are fixed; plan the workflow around that limit.

## Sizing and scrolling

Use `.style(gap=12, padding=16)` on layout parents. Set `width` for a narrow
navigation pane and `flex=1` for work areas that grow and shrink. Use
`full_width=True`/`full_height=True` deliberately on bounding surfaces; align
children with `align="stretch"` where appropriate.

Scroll needs a bounded viewport: a fixed `height` or a flexible region in a
bounded parent. Do not put an expanding document in an unbounded Scroll and
expect overflow. Resizable exposes native draggable pane boundaries, not the
full Kit dock/tiles API.

Navigation controls do not own arbitrary content pages. The mounted tree is
static: no runtime child insertion/removal, generic visibility switch, route
stack or multi-window support. Update prebuilt fields and datasets. If a task
needs dynamic topology, implement that library capability before relying on it.
