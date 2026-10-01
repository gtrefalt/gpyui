# gpyui

A native Python UI library powered by GPUI and Longbridge's GPUI Kit, with a
PyO3/maturin extension. Rust owns windows, rendering, focus and text editing;
Python owns composition, application state and callbacks.

The goal is a reusable desktop UI toolkit: write complete applications in Python,
as you would with Tkinter, using GPUI Kit components through Python controls.
Application authors should not need to write Rust. The current column, label,
text input and button are the first milestone; broader component coverage and
application features will build on this foundation.

`gpyui` is a working name. Package-name availability has not been checked.

```python
from gpyui import Application, Button, Column, Label, TextInput

app = Application(title="Hello")
with app, Column():
    Label("Name")
    name = TextInput(placeholder="Enter your name")
    greeting = Label("Enter a name and choose Greet")
    Button("Greet", on_click=lambda: setattr(greeting, "text", f"Hello, {name.value or 'world'}!"))

app.run()
```

Explicit composition also works: `Application(Column([Label("Hello"), ...]))`.
See [examples/async_binding.py](examples/async_binding.py) for `State`, two-way
input binding and an async callback.

## Build and run

Python 3.12+ and the pinned Rust toolchain are required. Native Linux builds need
development packages for X11/XCB, xkbcommon, Wayland, fontconfig, FreeType and a
Vulkan driver. Typical Debian packages:

```bash
sudo apt-get install build-essential pkg-config libclang-dev libfontconfig-dev \
  libfreetype-dev libx11-dev libx11-xcb-dev libxcb1-dev libxcb-xkb-dev \
  libxkbcommon-dev libxkbcommon-x11-dev libwayland-dev libvulkan-dev \
  mesa-vulkan-drivers
uv sync --locked
uv run python examples/hello.py
uv run python examples/async_binding.py
```

The generated project started with `uv init --lib --build-backend maturin --vcs
git /workspace/glint`, then was renamed at the user's request. The initial
uv_build scaffold was preserved separately before reinitialization.

In **this cloud workspace**, the toolchain and Debian packages were installed
locally without root access. Use:

```bash
cd /workspace/gpyui
source scripts/workspace-env.sh
uv sync --locked
uv run python examples/hello.py  # requires an actual display
```

## Callback and update contract

* `run()` owns the main-thread native event loop and blocks until close. One
  native run per process, one window, static mounted tree in this milestone.
* Callbacks execute on the `gpyui-asyncio` worker thread. A callback may require
  zero arguments or one `Event`. Handlers with no required arguments are called
  without an event. Both async handlers and returned awaitables are supported.
* Keep synchronous handlers short. Use `await asyncio.to_thread(...)` for
  blocking work; marshal UI mutations back to the callback loop. `app.call_soon`
  provides this handoff for other threads. Existing main-thread asyncio loops
  cannot host `run()` yet.
* Property assignments automatically coalesce by control/property per asyncio
  turn. `with app.batch(): ...` groups synchronous assignments. `app.update()`
  flushes immediately; neither is a rollback transaction.
* `await app.snapshot()` flushes and returns applied native properties, indexed
  by control ID. This is a command barrier, not a GPU presentation fence.
* Rust edits update Python `TextInput.value` and any bound `State` before
  `on_change`. Button activation carries a current input snapshot, so a handler
  reading `name.value` sees the input at activation. Native edits never pass
  through Rust `set_value`, preserving native cursor/selection/undo.
* Assigning `TextInput.value` deliberately replaces the editing buffer and clears
  undo history, following upstream `InputState.set_value`. It emits no user
  change callback. `.value` elsewhere is an asynchronously received mirror;
  use a snapshot when authoritative native state is needed.
* `State` uses explicit observers and equality guards. `Label.bind_text(state)`
  binds one way; `TextInput.bind_value(state)` binds both ways. `unbind()` removes
  subscriptions. Mutate bound state on the callback loop while running.
* `app.close()` requests shutdown. Native window close cancels awaiting handlers,
  gathers tasks, closes the asyncio loop, joins its worker, and unbinds controls.
  Cooperative cancellation cannot terminate an indefinitely blocking sync handler.
* Callback exceptions go to `on_error(exception)` or asyncio's exception handler
  and remain available in `app.errors`. Queue overload is explicit, not silent.

## Validation

```bash
uv run pytest -q
cargo check --locked
cargo clippy --locked -- -D warnings
cargo fmt --check
uv run ruff check src/gpyui examples tests
uv run ruff format --check src/gpyui examples tests
```

For actual native-window interaction tests, install Xvfb, xdotool and optionally
ImageMagick, then run `scripts/test-native.sh`. The script uses a free virtual
display and the local Mesa driver in this workspace. It tests native text input,
pointer and keyboard button activation, Python label updates, async binding,
exceptions and close/cancellation. Logs, screenshots and native snapshots go to
`artifacts/` (gitignored). Tests otherwise skip explicitly when native testing
is not enabled.

Read [docs/architecture.md](docs/architecture.md) for the source-grounded
NiceGUI/Flet comparison, design decisions and implementation plan,
[docs/upstream-lock.json](docs/upstream-lock.json) for revisions, and
[docs/validation.md](docs/validation.md) for measured results and limits.

Linux/X11 is the initial test target. macOS, Windows, Wayland, multiwindow,
dynamic topology, large control sets and distributed wheels remain follow-on
work. This milestone does not claim a production-ready general UI framework.
