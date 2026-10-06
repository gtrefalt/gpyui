# Native theme presets and overrides

gpyui 0.4.0 exposes an immutable `Theme` and runtime `app.theme` assignment.
Keep rendering and editing native; do not reconstruct controls when switching.

```python
from gpyui import Application, Button, Column, Label, TextInput, Theme

app = Application(title="Appearance", theme=Theme("macos"))


def toggle():
    app.theme = app.theme.customize(mode="dark" if app.theme.mode == "light" else "light")


with app, Column().style(gap=12):
    Label("Display name")
    TextInput("Sam Taylor")
    Button("Toggle appearance", on_click=toggle)
app.run()
```

Presets: `default`, `macos`, `windows`, `shadcn-zinc`, `shadcn-blue`. Every preset
accepts `mode="light" | "dark"`; default light. `Application(theme="macos")` selects
the light preset; `theme="light" | "dark"` selects the Kit default.
macOS and Windows styles are inspired, cross-platform Kit themes, not AppKit or
WinUI controls. Native title bars/system menus remain platform-owned. The presets
use installed platform fonts; they do not bundle SF Pro/Segoe UI or expose Mica.

```python
from gpyui import Application, Button, Column, Label, Theme

brand = Theme(
    "shadcn-zinc",
    colors={"primary": "#7c3aed", "primary_foreground": "#ffffff"},
    radius=8,
    radius_lg=12,
    font_size=15,
    shadow=False,
)
app = Application(theme=brand)
with app, Column().style(gap=12):
    Label("Native brand colors")
    Button("Continue", variant="primary")
app.run()
```

Options: `colors` is a copied token-to-hex mapping (`#RRGGBB` or `#RRGGBBAA`);
`radius`/`radius_lg` are integers 0–64 pixels; `font_size`/`mono_font_size` are
finite numbers 8–48. Omitted radius/font size uses preset defaults; monospace
size defaults to 13. `font_family`/`mono_font_family` use installed families,
or `None` for Kit platform defaults/fallbacks. `shadow` is Boolean, default True.

Accepted theme color tokens:

- `background`, `foreground`, `muted`, `muted_foreground`, `secondary`,
  `secondary_foreground`, `accent`, `accent_foreground`.
- `primary`, `primary_foreground`, `primary_hover`, `primary_active`.
- `danger`, `danger_foreground`, `success`, `warning`, `info`.
- `border`, `input` (input border), `ring`, `selection`, `caret`.
- `button`, `button_hover`, `button_active`, `popover`, `sidebar`.

Overriding primary derives hover/active/ring/caret unless explicitly overridden,
and selection uses its color at 20% opacity. Override readable foreground/surface
pairs. `.colors` contains immutable **explicit overrides**, not the resolved palette.
`.customize(colors={...})` merges overrides into a new theme; explicit colors
carry across mode changes, so define separate light/dark brands where appropriate.

Runtime assignments must happen on the callback loop (or through `app.call_soon`
from another thread). `app.batch()` coalesces assignments; it is not rollback.
`app.theme` represents the requested theme. `await app.theme_snapshot()` flushes
and reads applied native name/mode, radius, typography, shadow and colors, plus
the Base projection. Like `snapshot()`, it does not wait for GPU presentation.
Closing the window fails pending snapshots and cancels tracked callbacks.

Per-control `.style()` remains the limited semantic-token/pixel vocabulary in
[styling](styling.md). Hex overrides belong in `Theme`, not `.style()`.
Explicit control sizes/radii/fonts keep precedence over inherited theme settings.
