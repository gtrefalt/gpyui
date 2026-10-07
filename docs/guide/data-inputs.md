# Tables and input controls

These additions are unreleased. The catalog follows `main`; released 0.5.0 has
the earlier string table and input contracts.

## Keyed tables

Use `TableRow` keys when rows represent domain objects. `Table.value` always
indexes the source rows, even when the native view is sorted or filtered.
`selected_key` reads that row's key; assign an existing key to select it.

```python
from gpyui import Application, Table, TableColumn, TableRow, TextInput

table = Table(
    columns=[TableColumn("Project", width=260), TableColumn("Open issues", sort_type="number")],
    rows=[TableRow("gpyui", ("gpyui", 10)), TableRow("kit", ("GPUI Kit", 2))],
    sortable=True,
)
table.sort(1)
search = TextInput(
    placeholder="Filter projects",
    clearable=True,
    on_change=lambda event: setattr(table, "filter", event.value),
)
app = Application(search, table.style(height=280), title="Projects")
app.run()
```

`TableColumn(title, width=125, sort_type="text")` is immutable. Columns and widths
are fixed after construction. Text sorting compares strings; numeric sorting
compares finite parsed numbers and places nonnumeric text after numbers in
ascending order. Equal values retain source order. `sortable=True` enables native
header sort buttons. `sort(column, descending=False)` selects a source column;
`sort(-1)` clears sorting. `on_sort` reports header changes as
`{"column": index, "descending": bool}` after Python mirrors are updated.

`filter` matches a case-insensitive substring in any cell. Sorting/filtering
operate on native view indices and leave `rows` in source order. A filtered-out
selected row retains its domain selection and has no visible highlight.

`TableRow(key, cells)` is immutable: keys are unique, nonempty strings; cells
accept strings and finite numbers, rendered as text. Reassign `rows` with keyed
rows to retain the selected key across reorder/replacement. If its key disappears,
selection falls back to the first source row. Empty tables keep `value=0` and
`selected_key=None`. A dataset must use keyed rows throughout, or string-cell
lists throughout. Legacy string rows receive positional keys, so applications
using them must handle domain identity themselves.

Rows must match the column count; at most 10,000 rows are supported. The table
uses retained native `TableState` and virtualized `DataTable`. Custom cell
controls/editors, multiple selection, async delegates and load-more are not yet
exposed. Reassigning data changes neither control identity nor source column
configuration.

## Editing options

`TextInput` exposes mutable `disabled`, `read_only`, `password`, `clearable`,
`prefix` and `suffix`. Adornments are strings. `read_only` allows focus and text
selection but blocks edits; `disabled` also blocks ordinary interaction.
`password` masks display while Python values, bindings, events and native
snapshots still contain the original text. `clearable` uses Kit's native clear
button. Changing these options retains the editing entity and undo history.

`on_submit`, `on_focus` and `on_blur` receive the current text as `Event.value`.
Callbacks run on the asyncio worker, with input mirrors updated first.
Programmatic `value` replacement resets native undo without emitting change.
`TextArea` and `Editor` also expose `read_only` alongside `disabled`.

`NumberInput(value, minimum=None, maximum=None, step=1)` retains a string buffer,
including partial edits such as `"-"` and `"4."`. Bounds and step are mutable:
finite bounds require `minimum <= maximum`, and step must be positive. Native
step buttons and blur clamp completed numbers to the configured bounds. It does
not reject out-of-range text while typing; forms can validate completed input.

## Mutable choices and multiple selection

`Select` and `Combobox` accept unique, nonempty string items. Assign `items` to
replace choices in the existing native entity. A still-available selection is
retained; otherwise it becomes `""`. The option list and selection travel in one
validated batch, including updates to a bound `State`.

```python
from gpyui import Application, MultiSelect, State

selected = State(["Python", "Rust"])
languages = MultiSelect(["Python", "Rust", "GPUI"]).bind_value(selected)
app = Application(languages, title="Languages")
app.run()
```

`MultiSelect` uses Kit's searchable combobox in multiple mode. Its `value` is a
list of unique selected strings, with `[]` for none. Reassigning items retains
only values present in the new options. Selection events and binding updates
carry the complete list. Items and values are copied on assignment/read.
Typed item metadata, groups, disabled items, custom rows and managed async
providers remain future work.

For shared actions and search, see [the command palette](commands.md#command-palette).
