# Native window controls

`Application` owns one native GPUI window. Kit opens it using GPUI's
`WindowOptions`; the Python API now exposes the everyday options.
These additions are unreleased, following 0.5.0.

## Fixed size and minimum dimensions

```python
from gpyui import Application, Column, Label, TextInput, Theme

app = Application(
    title="Compact editor",
    width=520,
    height=320,
    resizable=False,
    theme=Theme("macos"),
)
with app, Column().style(gap=12):
    Label("Display name")
    TextInput("Sam Taylor")
app.run()
```

`width` and `height` set the requested content size in logical pixels.
`resizable=False` keeps that size during normal windowed use. Python can still
change it through `app.resize(width, height)`. For a resizable window, set
`min_width` and `min_height` to keep the interface usable. Defaults remain 240 ×
160; both can be reduced to values of at least 1 pixel for smaller utility windows.
Initial sizes and later `resize()` calls must meet those minimums.

The pinned Linux backend blocks GPUI resize gestures but does not supply fixed
maximum dimensions to the desktop. A Rust bounds observer therefore restores
fixed content dimensions after an external resize; a compositor may briefly
show an intermediate size. Fullscreen is exempt from the fixed-size guard.

## Creation options

| Option | Default | Behavior |
| --- | --- | --- |
| `resizable` | `True` | Allow user resizing; `False` fixes windowed content size |
| `min_width`, `min_height` | `240`, `160` | Finite logical pixels, at least 1 |
| `minimizable` | `True` | Native minimize capability; also guards `app.minimize()` |
| `movable` | `True` | Native user movement capability |
| `position` | `None` | Centered, or an `(x, y)` screen-coordinate tuple |
| `window_state` | `"normal"` | `normal`, `maximized` or `fullscreen` at startup |

These options are read-only after construction. A fixed window cannot start
maximized or use `toggle_maximized()`. Wayland owns placement and may ignore
`position`. GPUI's pinned Linux backends do not enforce native `movable` and
`minimizable` decorations; macOS and Windows consume those flags. Window actions
are requests to the desktop, so focus and state transitions depend on the
window manager or compositor. Custom title bars, always-on-top, maximum size,
multiple windows and live changes to creation flags are not yet exposed.

## Update a running window

```python
from gpyui import Application, Button, Column, Label

app = Application(title="Window controls", width=520, height=320)

def expand():
    app.title = "Expanded editor"
    app.resize(720, 480)

with app, Column().style(gap=12):
    Label("Try changing this window")
    Button("Expand", on_click=expand)
    Button("Fullscreen", on_click=app.toggle_fullscreen)
app.run()
```

`app.title` assignment and `resize()` work before startup and on the running
callback loop. `activate()`, `minimize()`, `toggle_maximized()` and
`toggle_fullscreen()` require a running application. They flush pending control
updates and enqueue native commands on the existing transport. Use
`app.call_soon(...)` from another thread. Title or size queue failures leave the
Python requested values unchanged. None of these operations rebuild the
control tree or replace editing entities.

`app.width` and `app.height` are read-only **requested** dimensions; a user resize
can change actual dimensions. `await app.window_snapshot()` returns native
`title`, content `width`/`height`, screen `x`/`y`, configured `resizable`,
`minimizable`, `movable`, minimum dimensions, and current `maximized`/`fullscreen`
flags. It fences native queue processing, not a later compositor event or GPU
presentation. Observe a later snapshot when waiting for a desktop transition.

See the [application reference](../reference/application.md),
[window example](https://github.com/gtrefalt/gpyui/blob/main/examples/window_controls.py)
and [source evidence and acceptance checks](../plans/window-options.md).
