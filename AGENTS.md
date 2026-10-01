# Project intent

The user's goal is a reusable Python UI toolkit exposing Longbridge's GPUI Kit
components, enabling complete native desktop apps written entirely in Python,
comparable in use to Tkinter and other Python UI libraries. The working name is
gpyui; package-name availability has not been checked.

Keep Rust behind the Python API. Rust owns native windows, rendering, component
state and text editing; Python authors own composition and application behavior.
Use actual GPUI Kit components and verify wrappers against the pinned upstream
sources. The column, label, text input and button are the first milestone, not
the final scope or a demo-specific backend.

Extend component coverage and Python access to layout, styling, events, state and
application lifecycle as the toolkit develops. Distinguish implemented support
from planned capabilities. See README.md and docs/architecture.md for the current
API, source evidence and constraints.
