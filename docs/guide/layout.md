# Compose layouts

Use [Column](../components/column.md) for vertical layout,
[Row](../components/row.md) for horizontal layout, and
[Container](../components/container.md) for a styled surface.
Application code stays in Python; these layouts become native GPUI elements.

## Context composition

```python
from gpyui import Application, Button, Column, GroupBox, Row, TextInput

app = Application(title="Project", width=640, height=360)
with app, Column().style(gap=16):
    with GroupBox("Project details"):
        name = TextInput("gpyui")
    with Row().style(gap=12):
        Button("Save", variant="primary")
        Button("Cancel")
app.run()
```

Construct a parent before its children within a `with` block. Each newly created
control attaches to the innermost active container. Composition contexts use
task-local stacks rather than an implicit process-global application.

## Explicit children

Construct explicit children outside a composition context:

```python
from gpyui import Application, Button, Column, Label, Row

actions = Row([Button("Save"), Button("Cancel")])
root = Column([Label("Project"), actions])
app = Application(root, title="Project", width=640, height=360)
app.run()
```

Avoid constructing an explicit child's list inside an existing context: those
children would already attach to the active parent. A control has one parent;
sharing the same instance is rejected. Remove it from its old parent before
adding it to a new parent in the same application.

## Flexible panes and scrolling

```python
from gpyui import Application, Column, Label, Row, Scroll

app = Application(title="Files", width=700, height=500)
with app, Row().style(full_width=True, full_height=True, gap=20, align="stretch"):
    with Column().style(width=180):
        Label("Navigation")
    with Scroll().style(flex=1):
        for index in range(50):
            Label(f"Item {index + 1}")
app.run()
```

Explicit dimensions use pixels and do not shrink. `flex=1` lets a pane take
available space and shrink within its parent. Give scrolling content a bounded
height or flexible viewport. [Resizable](../components/resizable.md) adds native
draggable boundaries when panes should resize interactively.

## Runtime children and visibility

From a running callback, application roots and containers support `add`, `insert`,
`remove`, `clear`, `set_children` and assignment to `children`. Reorder existing
instances to preserve their native identity, text, selection and undo history.

```python
from gpyui import Application, Button, Column, Label, TextInput

name = TextInput("Ada")
panel = Column([Label("Name"), name]).style(gap=12)


def change_layout():
    with app.batch():
        panel.insert(0, Label("Profile"))
        panel.children = tuple(reversed(panel.children))
        name.visible = not name.visible


app = Application(Column([panel, Button("Change layout", on_click=change_layout)]))
app.run()
```

`control.visible = False` removes its layout space and prevents interaction,
while retaining state and bindings. Hidden ancestors hide their descendants.
Removing a control detaches it without destroying it; add the same instance
again to restore it. Move with `old_parent.remove(control)` followed by
`new_parent.add(control)` inside `app.batch()` so the native update is atomic.

`control.dispose()` permanently releases its entire subtree, native state,
bindings and handlers. Disposed controls cannot be reused. Detached controls
remain owned by their application and count toward the 10,000-control limit;
dispose them when no longer needed. A mounted control cannot move to another app.

Compose new controls outside an active context, or create them within a `with`
block on their intended parent. Runtime mutations use the callback loop;
external threads hand work over with `app.call_soon()`. Multiple windows and
runtime theme switching remain future work.
