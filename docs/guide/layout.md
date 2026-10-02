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
sharing or reparenting the same instance is rejected.

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

!!! note "Static topology"

    You can call `add(...)` before mounting. Once `run()` mounts the tree, change
    mutable properties rather than adding/removing controls. Dynamic topology
    and multiple windows remain future work.
