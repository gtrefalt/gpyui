# Install and first app

Use **CPython 3.12+** and a working native display/graphics stack. Prebuilt wheels
are available for Linux, macOS and Windows on x64 and ARM64. A wheel installation
does not need Rust. See the [release matrix](../releases.md) for platform versions,
runtime libraries and test coverage.

## Install a wheel

On macOS 12+ and Windows, install from [PyPI](https://pypi.org/project/gpyui/):

```bash
uv init my-app
cd my-app
uv add gpyui
```

In an existing [uv](https://docs.astral.sh/uv/) project, use `uv add gpyui`.
Alternatively, use `pip install gpyui` in a virtual environment.
Windows ARM64 is tested with Python 3.13+.

On Linux, download the wheel matching your architecture from
[GitHub Releases](https://github.com/gtrefalt/gpyui/releases). The filenames end
in `linux_x86_64.whl` or `linux_aarch64.whl`. From your uv project, install the downloaded file:

```bash
uv add /path/to/gpyui-0.2.0-cp312-abi3-linux_x86_64.whl
```

Alternatively, use `pip install /path/to/wheel.whl` in a virtual environment.
PyPI currently provides a source archive for Linux; installing it compiles Rust.

For Debian/Ubuntu, install the desktop runtime libraries before opening a window:

```bash
sudo apt-get install libxcb1 libxkbcommon0 libxkbcommon-x11-0 \
  libfontconfig1 libfreetype6 libvulkan1 mesa-vulkan-drivers fonts-dejavu-core
```

## Build from source

Install [uv](https://docs.astral.sh/uv/) and
[Rust through rustup](https://rustup.rs/); the checkout pins the Rust toolchain
in `rust-toolchain.toml`. On macOS, install Xcode Command Line Tools. On Windows,
install Visual Studio Build Tools with the C++ desktop workload and Windows SDK.

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
minutes. Linux/X11 has native interaction tests; macOS and Windows wheels have
native window/state/lifecycle smoke tests. Wayland is not yet validated.

## First window

Create `hello.py` in your project:

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

With pip, activate your virtual environment and run `python hello.py`.

`run()` blocks the main thread until the native window closes. The native button
queues a callback onto gpyui's Python asyncio worker. Assigning `greeting.text`
submits an update to Rust; Python never renders the label.

## Try the examples

```bash
uv run python examples/hello.py
uv run python examples/async_binding.py
uv run python examples/gallery.py
uv run python examples/workspace.py --theme light
uv run python examples/component_preview.py Checkbox
```

For this cloud workspace's locally extracted libraries/toolchain, source
`scripts/workspace-env.sh` before building or running. On a normal desktop,
install native packages using your platform's package manager.

Continue with [composition](layout.md), [state binding](state.md) or the
[component catalog](../components/index.md).
