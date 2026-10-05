# State, events and asyncio

## Bind explicit observable state

```python
from gpyui import Application, Checkbox, Column, Label, State, TextInput

name = State("Ada")
enabled = State(True)
app = Application(title="Bindings")
with app, Column().style(gap=12, padding=24):
    TextInput().bind_value(name)
    Label().bind_text(name, lambda value: f"Hello, {value}")
    Checkbox("Receive updates").bind_value(enabled)
```

`State.value = value` synchronously notifies subscribers only when unequal.
`state.subscribe(callback)` returns an idempotent unsubscribe function.
`bind_value` is two-way on controls exposing both `value` and `change`.
`Label.bind_text` is one-way, with `str` as its default transform.
`control.unbind()` removes bindings. Hiding or detaching retains them;
`control.dispose()` and application shutdown unbind retained controls.

Native changes update the Python mirror and bound State **before** `on_change`.
Do not echo native text back through `.value` to keep it synchronized: that
unnecessarily replaces the retained editing buffer and clears undo history.
Use programmatic replacement only when the application's intent is replacement.
While running, change controls and bound State on the callback loop. A State
observer also runs synchronously on the thread that changes it.

## Value types are component-specific

| Components | `value` |
| --- | --- |
| TextInput, TextArea, Editor, NumberInput, OtpInput | String; NumberInput can hold partial numeric edits |
| Checkbox, Switch, Radio, Toggle, Collapsible, Dialog, Sheet | Boolean |
| RadioGroup, Tabs, Sidebar, Breadcrumb, Stepper, List, Table, Accordion, Pagination, Carousel | Nonnegative zero-based index |
| Select, Combobox | Selected string, or empty string |
| Tree | Stable item ID, or empty string |
| Rating | Integer 0–5 |
| Slider | Number within fixed range |
| Calendar, DatePicker | ISO date string, or empty string |
| TimeField | Local `HH:MM:SS` string |
| ColorPicker | `#rrggbb` or `#rrggbbaa` string |

Standalone Radio controls do not enforce mutual exclusion. Use RadioGroup.
Map positional selection to application domain IDs yourself. Parse numeric text
at a validation/submission boundary and show a useful error for incomplete input.

## Callback signatures and ordering

Handlers can require zero arguments or one `Event`. They may be sync, async,
or return an awaitable. `Event` is immutable: `sender`, `name`, `value`.
Names are `click`, `change`, `release`, `resize`, and `start`. Click/start do
not ordinarily carry a value; resize carries native panel sizes. Register only
events listed for the control (`on_click`, `on_change`, etc.). There is no
universal `.on()` registration API.

Button click events include input-value snapshots in the native queue, so
reading a TextInput in a click callback sees the text associated with that
activation. Native events and Python callbacks are queued; keep handlers short.
Queued callbacks for hidden/detached controls are suppressed; events for disposed
controls are ignored. Already-running callback tasks still require normal
application cancellation/ownership handling.

## Async work

Disable an operation's button before awaiting I/O, show progress, and restore
it in `finally` while the window is open. During shutdown, the bridge closes
before callback cancellation: a final UI assignment can raise
`ApplicationClosedError`. Catch that specific error for cleanup as in the
profile recipe; preserve cancellation itself. Capture values at submission time if subsequent edits should
not affect the in-flight request. Use async client APIs or
`await asyncio.to_thread(blocking_function, ...)`; then update controls after
awaiting, when execution returns to the callback loop. Do not manipulate controls
inside the worker function.

For an external thread, submit a short synchronous function through
`app.call_soon(callback, *args)`. It is a handoff, not an async task scheduler;
calling it with an async function does not await the coroutine.

Use an async `on_start` coroutine for a stream, poller or startup request.
Keep histories bounded, throttle display updates and allow cancellation at awaits.
Do not invoke `asyncio.run()` inside a callback or keep your own native UI loop.
See [tested recipes](recipes.md).

## Batches and observation

Assignments are coalesced by `(control ID, property)` within a callback turn;
intermediate values may never be displayed. This is appropriate for UI state,
not an audit log or every-event data stream.

`with app.batch():` groups **synchronous** mutations on a running app. Do not
hold the batch across I/O awaits. It flushes on exit and provides no rollback.
`app.update()` explicitly flushes pending properties. Both require a running
callback context; do not use them to build an unmounted tree.

`await app.snapshot()` flushes and waits for applied native command state.
The result maps integer control IDs to native properties, including retained
detached nodes. `visible` is the node's own flag; `attached` means under a live
application root; `displayed` also accounts for hidden ancestors. Disposed IDs
are absent. Structural changes and property patches in one batch apply together.
It is
not a GPU presentation fence and does not prove that pixels have been displayed.

Collections are copied on assignment and read. Use `table.rows = new_rows` or
`chart.data = new_points`, not `table.rows.append(...)`. Collection length is
limited (typically 10,000); streaming recipes retain a much smaller history.
