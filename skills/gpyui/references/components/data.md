# Data

Generated Python API reference from the repository (manifest version 0.5.0).
Includes unreleased contracts; check [release status and coverage](../coverage.md) against your installed version.

## List

Compose selectable native ListItems.

### Runnable example

```python
import gpyui as ui

control = ui.List(["Recent files", "Shared with me", "Archive"], value=1)

app = ui.Application(ui.Column([control]), title="List", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `items` | `[]` | list[str] | Assignment |
| `value` | `0` | nonnegative int | Assignment |
| `disabled` | `false` | bool | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

- `on_change(event)`: Runs after native value and Python mirror/bound State change.

Handlers can take zero arguments or one `Event`, and can be synchronous or async. They run on the owned Python asyncio loop. See [events and asyncio](../state-and-events.md).

`bind_value(State(...))` binds both ways without echoing native edits back through setters. `unbind()` disposes the subscription. See [state binding](../state-and-events.md).

### Contract and limits

This wrapper renders every ListItem. It does not expose virtual ListState/delegate, scroll-to-item or async search. value is a positional index, not a stable item ID.

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L753) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](../coverage.md)

## Table

Native virtualized table with stable row keys, sorting and filtering.

### Runnable example

```python
import gpyui as ui

control = ui.Table(
    columns=["Name", "Language", "Status"],
    rows=[["gpyui", "Python", "Ready"], ["GPUI Kit", "Rust", "Native"]],
    column_width=185,
).style(height=160, full_width=True)

app = ui.Application(ui.Column([control]), title="Table", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `columns` | `[]` | list[str | TableColumn] | Constructor only |
| `rows` | `[]` | list[list[str]] or list[TableRow] | Assignment; preserves keyed selection |
| `value` | `0` | source row index; zero for an empty table | Assignment |
| `selected_key` | `null` | str or None when empty | Assign an existing row key |
| `row_keys` | `[]` | list[str]; derived from rows | Read only; replaced with rows |
| `column_width` | `125` | fallback width for string columns, minimum 24 pixels | Constructor only |
| `sortable` | `false` | bool; enables header sort buttons | Constructor only |
| `sort_column` | `-1` | source column index; -1 clears sorting | Assignment or sort() |
| `sort_descending` | `false` | bool | Assignment or sort() |
| `filter` | `""` | case-insensitive substring in any cell | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

- `on_change(event)`: Runs after native value and Python mirror/bound State change.
- `on_sort(event)`: Receives {column, descending} after native header sorting and Python mirrors update.

Handlers can take zero arguments or one `Event`, and can be synchronous or async. They run on the owned Python asyncio loop. See [events and asyncio](../state-and-events.md).

`bind_value(State(...))` binds both ways without echoing native edits back through setters. `unbind()` disposes the subscription. See [state binding](../state-and-events.md).

### Contract and limits

Columns accept strings or TableColumn(title, width=125, sort_type='text' or 'number'). Rows accept string lists or TableRow(key, cells); use keyed rows throughout a dataset to preserve selected_key across replacement. value is a source row index, including when sorted or filtered. sortable enables header sorting; sort(column, descending=False) controls it programmatically and filter performs case-insensitive substring matching. Hidden selected rows retain their domain selection. Custom cells and load-more remain unbound.

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L572) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/view.rs) · [Full coverage and remaining Kit APIs](../coverage.md)

## Tree

Native tree selection with stable item IDs.

### Runnable example

```python
import gpyui as ui

control = ui.Tree(
    [
        {"id": "src", "text": "Source", "children": [{"id": "src/main.py", "text": "main.py"}]},
        {"id": "docs", "text": "Documentation"},
    ],
    value="docs",
).style(height=160)

app = ui.Application(ui.Column([control]), title="Tree", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `items` | `[]` | list[tree item] | Constructor only |
| `value` | `""` | str | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

- `on_change(event)`: Runs after native value and Python mirror/bound State change.

Handlers can take zero arguments or one `Event`, and can be synchronous or async. They run on the owned Python asyncio loop. See [events and asyncio](../state-and-events.md).

`bind_value(State(...))` binds both ways without echoing native edits back through setters. `unbind()` disposes the subscription. See [state binding](../state-and-events.md).

### Contract and limits

Item IDs must be unique. value is an item ID or an empty string. Items are fixed; at most 10,000 items and 32 levels.

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L937) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](../coverage.md)

## DescriptionList

Native label/value presentation.

### Runnable example

```python
import gpyui as ui

control = ui.DescriptionList([["Language", "Python"], ["Renderer", "GPUI"], ["Components", "GPUI Kit"]])

app = ui.Application(ui.Column([control]), title="DescriptionList", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `items` | `[]` | list[list[str]] | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

This wrapper exposes no Python activation/change handler. Update its mutable properties by assignment from a running callback. Native behavior remains in Rust.

### Contract and limits

Each item is a two-string label/value pair.

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L479) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](../coverage.md)
