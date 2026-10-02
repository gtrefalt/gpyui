# Install and first app

gpyui currently builds from the repository. Use Python **3.12+**,
[uv](https://docs.astral.sh/uv/) and the pinned Rust toolchain from
`rust-toolchain.toml`. A working native display/GPU stack is required to open a
window. Linux/X11 is the validated target.

## Build from source

On Debian-based Linux, install the native build prerequisites:

```bash
sudo apt-get install build-essential pkg-config libclang-dev libfontconfig-dev \
  libfreetype-dev libx11-dev libx11-xcb-dev libxcb1-dev libxcb-xkb-dev \
  libxkbcommon-dev libxkbcommon-x11-dev libwayland-dev libvulkan-dev \
  mesa-vulkan-drivers
git clone https://github.com/gtrefalt/gpyui
cd gpyui
uv sync --locked
```

The first build compiles the pinned GPUI Kit dependencies and can take several
minutes. macOS/Windows, Wayland and portable wheels have not been validated.

## First window

Create `hello.py` in the checkout:

```python
from gpyui import Application, Button, Column, Label, TextInput

app = Application(title="Hello", width=480, height=300)
with app, Column():
    Label("Name")
    name = TextInput(placeholder="Enter your name")
    greeting = Label("Enter a name and choose Greet")

    def greet():
        greeting.text = f"Hello, {name.value or 'world'}!"

    Button("Greet", variant="primary", on_click=greet)
app.run()
```

```bash
uv run python hello.py
```

`run()` blocks the main thread until the native window closes. The native button
queues a callback onto gpyui's Python asyncio worker. Assigning `greeting.text`
submits an update to Rust; Python never renders the label.

## Try the examples

```bash
uv run python examples/hello.py
uv run python examples/async_binding.py
uv run python examples/gallery.py
uv run python examples/workspace.py --theme dark
uv run python examples/component_preview.py Checkbox
```

For this cloud workspace's locally extracted libraries/toolchain, source
`scripts/workspace-env.sh` before building or running. On a normal desktop,
install native packages using your platform's package manager.

Continue with [composition](layout.md), [state binding](state.md) or the
[component catalog](../components/index.md).
