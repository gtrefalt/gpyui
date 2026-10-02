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
captures the actual window in the native light theme, and verifies shutdown/error
state. The capture command explicitly selects light appearance so all catalog
previews match the site's default. PNGs go to
`docs/screenshots/components/`; native snapshots and logs go to `artifacts/`.
No native previews are synthesized as HTML or drawn in Python.

## CI and GitHub Pages

The documentation workflow verifies generated references, builds in strict mode,
checks built local links/assets/anchors,
without the native extension, and uploads a browsable `gpyui-docs` HTML artifact
on pull requests and main. Download and extract the artifact, then serve it with
`python -m http.server --directory site` (or the extracted directory).

The publication URL is <https://gtrefalt.github.io/gpyui/>. In
[Settings → Pages](https://github.com/gtrefalt/gpyui/settings/pages), select
**GitHub Actions** under **Build and deployment → Source**. No repository
variables or additional secrets are needed.

After enabling Pages, open the
[Documentation workflow](https://github.com/gtrefalt/gpyui/actions/workflows/docs.yml)
and select **Run workflow** on `main` for the first deployment. Subsequent
main-branch pushes publish the same verified site automatically. Pull requests
only build and upload their preview artifact. If Pages has not been enabled, the
build still runs and emits a setup warning, and deployment is skipped.
