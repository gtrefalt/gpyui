# Setup and runtime

## Install for an application

Use CPython 3.12+ (Windows ARM64 is tested with 3.13+). On macOS 12+ and Windows:

```bash
uv init my-app
cd my-app
uv add gpyui
```

For an existing project, just run `uv add gpyui`. Linux prebuilt wheels live on
[GitHub Releases](https://github.com/gtrefalt/gpyui/releases), rather than PyPI.
Download the correct architecture (`linux_x86_64` or `linux_aarch64`) and use,
from your uv project:

```bash
uv add /path/to/gpyui-0.5.0-cp312-abi3-linux_x86_64.whl
```

Alternatively, use `pip install gpyui` or `pip install /path/to/wheel.whl` in a
virtual environment. A wheel needs no Rust compiler. Installing from PyPI on
Linux currently builds the source archive and needs Rust and native development
libraries; choose the prebuilt wheel when developing a Python app.

On Debian/Ubuntu, install runtime dependencies:

```bash
sudo apt-get install libxcb1 libxkbcommon0 libxkbcommon-x11-0 \
  libfontconfig1 libfreetype6 libvulkan1 mesa-vulkan-drivers fonts-dejavu-core
```

Run `uv run python app.py`, or `python app.py` with the pip environment active.
A graphical display and working Metal (macOS), DirectX (Windows), or Vulkan
(Linux) backend are required. Linux/X11 is validated; Wayland is not yet
validated. A missing display is not a Python composition error.

## Application contract

```python
from gpyui import Application, Column, Label

app = Application(
    Column([Label("Your workspace")]).style(padding=24),
    title="Workspace",
    width=800,
    height=540,
    theme="light",
)

if __name__ == "__main__":
    app.run()
```

`Application(*controls, title="gpyui", width=480, height=300, theme="light",
on_start=None, on_error=None)` accepts unparented roots. Size must be finite
and at least 240 × 160 pixels. Theme accepts `light`/`dark`, a preset name, or a
Theme object; light is the default. Assign `app.theme` from running callbacks to
switch without reconstructing controls. See [native themes](themes.md).

`run()` blocks the main thread until the window closes. One native application
may run per process, with one window. Python callbacks run on the separate,
owned asyncio worker; Rust releases the GIL while running the native loop.
Construct the initial tree before starting. `children` is a tuple supporting
assignment. Root and container mutations work on the running callback loop.
Removal and visibility retain native state; `dispose()` permanently releases
controls. See [dynamic composition](composition.md#dynamic-composition).

## Startup and shutdown

Pass a sync or async startup callback via `on_start`; it runs when the native
bridge is ready. A zero-argument callback is sufficient; a one-argument handler
receives an Event whose sender is the Application and name is `start`.
Long-running async startup work is tracked by the application. Window close
cancels tracked work, gathers tasks and joins the worker. If you create extra
child tasks yourself, cancel and await them in your startup coroutine's
`finally` block. Do not swallow `asyncio.CancelledError`.

Call `app.close()` from a running callback to flush updates and request native
shutdown. Do not call `run()` again after closing. For tests or multiple app
launches use separate processes. A permanently blocking synchronous callback
cannot be cooperatively cancelled.

Pass `on_error(exception)` to report unhandled callback failures in a useful
way. Exceptions are also available as `app.errors` (a tuple); without a handler
asyncio reports them. `ApplicationClosedError` describes use of runtime commands
before startup or after close. Queue overload is an explicit failure, not a
promise that unbounded updates will be accepted.

Full reference: [application](https://gtrefalt.github.io/gpyui/reference/application/)
and [release support](https://gtrefalt.github.io/gpyui/releases/).
