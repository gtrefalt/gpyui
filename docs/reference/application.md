# Application

`Application` owns one native window and one Python asyncio worker loop.
Construct the initial tree before `run()`. Running callbacks can update children
and visibility while retaining native state.

```python
from gpyui import Application, Column, Label

app = Application(Column([Label("Hello")]), title="Project", width=640, height=360, theme="dark")
app.run()
```

## Constructor

| Argument | Default | Contract |
| --- | --- | --- |
| `*controls` | None | Unparented root controls |
| `title` | `"gpyui"` | Window title string |
| `width` | `480` | Finite width, at least 240 pixels |
| `height` | `300` | Finite height, at least 160 pixels |
| `theme` | `"light"` | Initial `light` or `dark` appearance |
| `commands` | `()` | Explicit Command registration, including shortcut-only actions |
| `menus` | `()` | Menu roots; macOS system bar or Kit in-window bar |
| `on_start` | `None` | Zero/one-argument sync/async tracked startup callback |
| `on_error` | `None` | Callback receiving an exception |

## Lifecycle

`run()` starts on the main thread outside an existing asyncio loop and blocks
until native close. A process may start the native application once. Native
window close cancels awaiting callback tasks and joins the Python worker.

`close()` flushes pending mutations and requests native shutdown from the callback
loop. `children` exposes a tuple of roots and supports assignment. `add`, `insert`,
`remove`, `clear` and `set_children` work before mounting and on the running
callback loop, using the same contracts as [containers](core.md).
`errors` exposes reported callback errors as a tuple.

## Updates

| Method | Contract |
| --- | --- |
| `update()` | Flush coalesced property and child updates from the callback loop |
| `batch()` | Context manager grouping synchronous assignments; no rollback |
| `await snapshot()` | Flush and wait for applied native state, indexed by integer control IDs |
| `call_soon(callback, *args)` | Thread-safe handoff of short synchronous work to the callback loop |

Snapshots include retained detached controls until disposal. Each node includes
`visible` (its own flag), `attached` (under an application root) and `displayed`
(attached and visible, including ancestors). Structural updates and explicit
property patches in one batch apply together. Existing native properties are
never replayed from a tree description.

The native snapshot barrier does not wait for GPU presentation. While the app
runs, mutate controls/State on the callback loop. External worker threads can
use `app.call_soon(lambda: setattr(label, "text", result))`.

## Commands and application menus

`commands` exposes a read-only tuple of registered commands. `add_command(*commands)`
registers additional actions before startup or on the callback loop. `menus`
exposes a tuple of Menu roots and supports replacement by assignment. Commands
referenced by controls are also discovered during mounting and runtime updates.
Snapshots include command entries with `type="command"`, `label`, `shortcut`
(normalized native spelling), `enabled` and `checked`.
See [commands and menus](../guide/commands.md) for ownership and execution.

## Native notifications

From a running callback:

```python
app.notify("Changes saved", title="Project", variant="success")
```

`message` and `title` are strings. `variant` accepts `info` (default), `success`,
`warning` or `danger`. The notification is a native Kit toast.

## Errors

`ApplicationClosedError` signals use before native start or after close.
Queue overload and invalid bridge updates are explicit exceptions. Callback
exceptions go to `on_error` or asyncio's exception handler and remain in `errors`.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/application.py) ·
[Native bridge](https://github.com/gtrefalt/gpyui/blob/main/src/bridge.rs) ·
[Events and asyncio](../guide/events.md)
