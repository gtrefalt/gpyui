# Contributing to gpyui

gpyui exposes actual GPUI Kit components to Python. Rust owns windows, rendering,
native state and text editing; Python owns layout composition, application state
and callbacks. Read the [architecture](https://gtrefalt.github.io/gpyui/architecture/)
and [component coverage](https://gtrefalt.github.io/gpyui/component-coverage/)
before extending the API.

## Set up a source checkout

Install Python 3.12+, [uv](https://docs.astral.sh/uv/), and
[Rust through rustup](https://rustup.rs/). The repository pins its Rust toolchain
in `rust-toolchain.toml`. Install your platform's native build prerequisites
from the [source installation guide](https://gtrefalt.github.io/gpyui/guide/install/#build-from-source).

```bash
git clone https://github.com/gtrefalt/gpyui.git
cd gpyui
uv sync --locked
uv run python examples/hello.py
```

The first build compiles GPUI and Kit and can take several minutes. Native
examples require a functioning desktop display and graphics driver. In the
managed workspace with locally extracted libraries, source
`scripts/workspace-env.sh` before building or running.

## Development commands

[Just](https://github.com/casey/just) provides development commands;
[Lefthook](https://github.com/evilmartians/lefthook) runs Ruff and ty checks in Git
hooks. Tool versions are pinned in `uv.lock`.

```bash
uv tool install rust-just==1.58.0
just hooks
just check
just test
just rust-check
```

`just hooks` installs development tools into `.venv-tools` and Git hooks.
`just check` runs Ruff lint and format checks, ty, Justfile formatting and hook
configuration validation. `just format` applies safe Ruff fixes and formatting.
`just test` uses the native development environment in `.venv`; `just rust-check`
runs Rust formatting and Clippy. Use `just --list` for all commands.

For real native interaction tests on Linux, install Xvfb and xdotool, then run:

```bash
just test-native
```

Native tests cover text editing, button activation, Python updates, async binding,
shutdown, component rendering and overlays. Logs, screenshots and snapshots go
to the gitignored `artifacts/` directory. See the
[validation notes](https://gtrefalt.github.io/gpyui/validation/) for coverage and limits.

## Documentation

```bash
just docs-check
just docs-serve
```

Documentation tools run in `.venv-docs` and do not require compiling Rust.
See [documentation development](https://gtrefalt.github.io/gpyui/contributing-docs/)
for generated component references, native screenshot capture and GitHub Pages.
Keep animations in the documentation; the package README uses a static PNG.

## Pull requests

Describe the resulting user-facing behavior, supported properties and events,
and relevant verification. Check wrappers against the pinned upstream sources,
update the component catalog when the API changes, and keep implemented support
distinct from planned capabilities. Add tests for meaningful behavior or
regressions and run the checks appropriate to your change.

gpyui's code is licensed under [MIT](LICENSE). Preserve third-party license
notices; dependencies retain their own licenses.
