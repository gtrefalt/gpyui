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
The 0.6.0 `macos` preset uses Kit’s exact macOS Classic Light/Dark file
at [the pinned revision](https://github.com/longbridge/gpui-kit/blob/c1bda59e67f46266991a230ae94f749af496af2a/themes/macos-classic.json), including
36 color entries per mode and the highlight section through Kit’s unchanged schema.
It uses Kit’s default 16 px system font, 6/8 px radius and normal control sizing;
shadows are False. No compact frames, green switch override or SF font substitution
is added. Window decorations remain platform-owned. Pinned Kit ignores dotted
editor highlight keys and `comment.doc`; gpyui matches that parser behavior.
Windows keeps 14 px text, 32 px frames, larger checkbox/switch sizing, accent thumbs
and underlined focus, with installed Segoe/Open-font/Kit fallbacks. No proprietary
fonts are bundled. Windows and shadcn are inspired styles. App spacing is Python-owned.

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
or `None` for preset family selection and Kit fallbacks. `shadow` is a Boolean override or None for preset defaults: Classic False, others True.

Accepted theme color tokens:

- `background`, `foreground`, `muted`, `muted_foreground`, `secondary`,
  `secondary_foreground`, `accent`, `accent_foreground`.
- `primary`, `primary_foreground`, `primary_hover`, `primary_active`.
- `danger`, `danger_foreground`, `success`, `warning`, `info`.
- `border`, `input` (input border), `ring`, `selection`, `caret`.
- `button`, `button_hover`, `button_active`, `popover`, `sidebar`.
- `control_background` (TextInput/TextArea/Select), `switch` (off), `switch_thumb`,
  `switch_checked` (on), `slider` (fill), `slider_thumb`.

Override `switch_checked` independently from primary actions. Windows on-track
and slider thumb follow primary overrides; Classic uses Kit color fallbacks. Fields
retain the original Kit input state and focus handle across theme changes.

Overriding primary derives hover/active/ring/caret unless explicitly overridden,
and selection uses its color at 20% opacity. Override readable foreground/surface
pairs. `.colors` contains immutable **explicit overrides**, not the resolved palette.
`.customize(colors={...})` merges overrides into a new theme; explicit colors
carry across mode changes, so define separate light/dark brands where appropriate.

Runtime assignments must happen on the callback loop (or through `app.call_soon`
from another thread). `app.batch()` coalesces assignments; it is not rollback.
`app.theme` represents the requested theme. `await app.theme_snapshot()` flushes
and reads applied native name/mode, radius, typography, shadow and colors, plus
the Base projection. It also includes Kit’s `config`, applied `highlight` and full
`resolved_colors` (RGBA hex). Classic uses its upstream name in snapshots. Like `snapshot()`, it does not wait for GPU presentation.
Closing the window fails pending snapshots and cancels tracked callbacks.

Per-control `.style()` remains the limited semantic-token/pixel vocabulary in
[styling](styling.md). Hex overrides belong in `Theme`, not `.style()`.
Explicit control sizes/radii/fonts keep precedence over inherited theme settings.
