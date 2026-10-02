# Events and asyncio

Native event handlers enqueue data; they do not call Python from the renderer.
Python callbacks run on one owned `gpyui-asyncio` worker loop. GPUI's native
event loop remains on the main thread, with the GIL released during native run.

## Async callbacks

```python
import asyncio
from gpyui import Application, Button, Column, Label

app = Application(title="Async callbacks", width=480, height=300)
with app, Column():
    status = Label("Ready")

    async def save():
        button.disabled = True
        status.text = "Saving…"
        await asyncio.sleep(0.5)
        status.text = "Saved"
        button.disabled = False
        app.notify("Changes saved", variant="success")

    button = Button("Save", on_click=save)
app.run()
```

Changes flush even while a coroutine awaits. Handlers can take zero arguments,
or require one `Event`. Synchronous handlers may also return an awaitable.
Keep synchronous work short; use `await asyncio.to_thread(...)` for blocking
operations and mutate controls after returning to the callback loop.

## Read the event

```python
from gpyui import Checkbox

checkbox = Checkbox("Enabled", on_change=lambda event: print(event.sender.id, event.value))
```

The mirror and binding are updated before `on_change`. Button activation includes
native input-value snapshots, so reading `name.value` sees the input at that
activation even if later edits are already queued.

## Batched updates and barriers

Property assignment coalesces by `(control ID, property)` per asyncio turn.
Inside a running callback:

```python
with app.batch():
    status.text = "Saved"
    button.disabled = False
snapshot = await app.snapshot()
print(snapshot[status.id]["text"])
```

`app.update()` flushes explicitly. `app.batch()` groups synchronous assignments;
it is not a rollback transaction. `snapshot()` is a native command barrier,
not a fence guaranteeing GPU presentation.

## Startup, errors and shutdown

Use `Application(on_start=callback)` for tracked background coroutines such as
the [simulated trading stream](../examples/trading.md). Native close cancels
awaiting callback tasks, gathers them, closes the loop and joins the worker.
An indefinitely blocking synchronous handler cannot be cooperatively cancelled.

Use `on_error(exception)` to report callback failures; exceptions remain in
`app.errors`. `app.close()` requests native shutdown from a callback.
Bounded queue overload is explicit rather than silently dropping events.

`run()` must start outside an existing main-thread asyncio loop and may be used
once per native process. See [Application](../reference/application.md).
