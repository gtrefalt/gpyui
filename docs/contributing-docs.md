# Documentation development

The site uses [Zensical](https://zensical.org/), pinned in the `docs` dependency
group and `uv.lock`. Its build needs Python 3.12 and uv; it does **not** need Rust,
a compiled gpyui extension, a display or native development libraries.

## Preview and build

Use a separate environment so documentation commands do not replace the native
development environment:

```bash
export UV_PROJECT_ENVIRONMENT=.venv-docs
uv sync --locked --only-group docs
uv run --locked --only-group docs python scripts/generate-docs.py --check
uv run --locked --only-group docs zensical serve
```

Open `http://localhost:8000`. To build static HTML:

```bash
uv run --locked --only-group docs zensical build --strict --clean
uv run --locked --only-group docs python scripts/check-docs-site.py
```

Output goes to the gitignored `site/` directory. `zensical.toml` configures
navigation, syntax highlighting, search, light/dark appearance and component cards.

## Keep the catalog in sync

The catalog generator reads the real Python fields, fixed properties and event
declarations, then constructs all specimens to validate them. The authoritative
sample descriptions, notes and code live in `examples/component_catalog.py`.

```bash
uv run --locked --only-group docs python scripts/generate-docs.py
uv run --locked --only-group docs python scripts/generate-docs.py --check
```

Commit generated component pages and `zensical.toml`. `--check` rejects stale
references, missing screenshots or a mismatch between documented controls and
the public catalog. All examples can construct their trees without loading Rust.

## Capture native components

Captures require the installed native extension and Linux/X11 tooling:

```bash
sudo apt-get install xvfb xdotool imagemagick
scripts/native-display.sh .venv/bin/python scripts/capture-components.py
scripts/native-display.sh .venv/bin/python scripts/capture-components.py Button Dialog
```

The helper uses a free Xvfb display when no display is present. Each specimen
starts in a fresh native process, opens hover/popover/dialog states where relevant,
captures the actual window, and verifies shutdown/error state. PNGs go to
`docs/screenshots/components/`; native snapshots and logs go to `artifacts/`.
No native previews are synthesized as HTML or drawn in Python.

## CI and GitHub Pages

The documentation workflow verifies generated references, builds in strict mode,
checks built local links/assets/anchors,
without the native extension, and uploads a browsable `gpyui-docs` HTML artifact
on pull requests and main. Download and extract the artifact, then serve it with
`python -m http.server --directory site` (or the extracted directory).

For optional publication at `https://gtrefalt.github.io/gpyui/`, select **GitHub
Actions** as the repository's Pages source and set repository variable
`PUBLISH_DOCS` to `true`. Main-branch pushes or a manual workflow run then deploy
the same built site. Pull requests only build and upload their preview artifact.
