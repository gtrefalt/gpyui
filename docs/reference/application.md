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
| `width` | `480` | Finite width, at least `min_width` pixels |
| `height` | `300` | Finite height, at least `min_height` pixels |
| `resizable` | `True` | False fixes windowed content dimensions |
| `min_width`, `min_height` | `240`, `160` | Finite minimum dimensions, at least 1 pixel |
| `minimizable`, `movable` | `True` | Native capability flags; platform support varies |
| `position` | `None` | Centered or `(x, y)` screen coordinates |
| `window_state` | `"normal"` | Initial normal, maximized or fullscreen state |
| `theme` | `"light"` | Theme object, preset name, or `light`/`dark` |
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
| `await theme_snapshot()` | Flush and read applied Kit/Base colors, typography, radius and shadow |
| `call_soon(callback, *args)` | Thread-safe handoff of short synchronous work to the callback loop |

Snapshots include retained detached controls until disposal. Each node includes
`visible` (its own flag), `attached` (under an application root) and `displayed`
(attached and visible, including ancestors). Structural updates and explicit
property patches in one batch apply together. Existing native properties are
never replayed from a tree description.

The native snapshot barrier does not wait for GPU presentation. While the app
runs, mutate controls/State on the callback loop. External worker threads can
use `app.call_soon(lambda: setattr(label, "text", result))`.

## Window

The 0.6.1 window additions expose GPUI's real window options. Assign
`app.title` or call `app.resize(width, height)` before startup or from the running
callback loop. `width` and `height` report the last requested size; other creation
options are read-only. Native operations `activate()`, `minimize()`,
`toggle_maximized()` and `toggle_fullscreen()` require the running callback loop.
They flush pending controls before enqueue. These operations retain all controls
and editing state. `await window_snapshot()` reads actual native content size,
position, configured capability flags/minimums and fullscreen/maximized flags.
Desktop transitions may complete after the snapshot command. See
[native window controls](../guide/windows.md) for complete platform contracts.

## Theme

`app.theme` returns the requested immutable `Theme`. Assign a preset string or
Theme before startup or from the running callback loop. Assignments coalesce in
`batch()`, refresh native theme state and retain editor identity, selection and
undo. Invalid descriptions fail before mutation. The applied native theme is
available through `await theme_snapshot()`; queue errors leave an update pending
for retry. See [native themes](../guide/themes.md) for presets and custom overrides.

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
