# Control, Event and State

## Control

A `Control` is a stable Python handle. Rust owns its native rendering/state.
Use concrete controls rather than constructing `Control` directly.

| API | Contract |
| --- | --- |
| `id` | Stable positive integer identifying the control |
| `style(**properties)` | Validate/merge native styles and return the same control |
| `update()` | Flush the owning application's pending changes, if mounted |
| `unbind()` | Remove this control's binding subscriptions |

Mutable component properties submit coalesced updates by assignment. Field tables
on the [component pages](../components/index.md) distinguish assignment from
constructor-only settings. Collections return copies.

Containers additionally expose `children`, `add(*controls)` and a context manager.
Every control has one parent; reparenting and cycles are rejected. Topology is
fixed after mounting.

## Event

`Event` is an immutable callback record:

| Field | Value |
| --- | --- |
| `sender` | The originating Control, or Application for startup |
| `name` | `start`, `click`, `change`, `release` or `resize` |
| `value` | Component-specific native value; absent for ordinary click/start |

```python
from gpyui import Slider

slider = Slider(35, on_change=lambda event: print(event.sender.id, event.name, event.value))
```

A handler can take zero arguments or require one `Event`; its signature is
validated before attachment. See [event ordering and asyncio](../guide/events.md).

## State

`State(value)` stores explicit observable state. Assigning an unequal `value`
notifies observers synchronously. `subscribe(callback)` returns an idempotent
unsubscribe function.

```python
from gpyui import Checkbox, Label, State

enabled = State(True)
checkbox = Checkbox("Enabled").bind_value(enabled)
label = Label().bind_text(enabled, lambda value: "On" if value else "Off")
```

`bind_value` is two-way on native value/change controls. `Label.bind_text` is
one-way, with `str` as the default transform. `unbind()` removes subscriptions;
app shutdown unbinds mounted controls. [State binding](../guide/state.md) explains
thread ownership and native editing history.

[Control/Event source](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/controls.py) ·
[State source](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/state.py)
