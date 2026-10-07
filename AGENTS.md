# Project intent

The user's goal is a reusable Python UI toolkit exposing Longbridge's GPUI Kit
components, enabling complete native desktop apps written entirely in Python,
comparable in use to Tkinter and other Python UI libraries. The package is
published on PyPI as gpyui and licensed under MIT.

Keep Rust behind the Python API. Rust owns native windows, rendering, component
state and text editing; Python authors own composition and application behavior.
Use actual GPUI Kit components and verify wrappers against the pinned upstream
sources. The column, label, text input and button are the first milestone, not
the final scope or a demo-specific backend.

Extend component coverage and Python access to layout, styling, events, state and
application lifecycle as the toolkit develops. Distinguish implemented support
from planned capabilities. See README.md and docs/architecture.md for the current
API, source evidence and constraints.

# Application-building skills

For Python application work, read `skills/gpyui/SKILL.md` and its task-specific
references. Before designing or changing visible UI, also read
`skills/gpyui-design-guides/SKILL.md` and the bundled design guide. These cover
the Python bindings; do not substitute upstream Rust APIs. See skills/README.md
for installation into application projects outside this checkout.

Keep generated skill component references in sync with the docs using
`just docs-generate`. Run `just skills-check` and `just docs-check` after changes
to skills or public component contracts. Docs/skills-only changes do not need
a version bump, native wheel build, or release tag.

Keep README status, documentation and both skills aligned when changing public
capabilities or the roadmap. `docs/component-coverage.md` is the shared coverage
source; generation bundles it as `skills/gpyui/references/coverage.md`. The command and
data/input guides also generate their bundled skill references; edit the docs
sources and regenerate rather than changing those generated skill files. State
which APIs are released versus only implemented on main, and distinguish gaps
against the pinned Kit revision from additions in newer upstream source.
