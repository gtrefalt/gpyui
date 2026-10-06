# Python styling contract

`control.style(**properties)` validates and merges styles, returns the same
control, and queues changes when mounted. Use semantic native styling; these
are the accepted properties, not examples of an unrestricted CSS surface.

| Properties | Values |
| --- | --- |
| width, height, min_width, min_height, padding, gap, radius, font_size | Finite nonnegative pixel numbers |
| flex | Finite nonnegative growth/shrink weight |
| full_width, full_height, border, bold | Boolean |
| align | `start`, `center`, `end`, `stretch` |
| justify | `start`, `center`, `end`, `between` |
| background, color | Semantic token below |

Color tokens: `background`, `foreground`, `muted`, `muted_foreground`, `primary`,
`primary_foreground`, `secondary`, `secondary_foreground`, `border`, `accent`,
`accent_foreground`, `danger`, `success`, `warning`, `info`, `transparent`.

```python
from gpyui import Column, Label

panel = Column(
    [
        Label("Project details").style(font_size=20, bold=True),
        Label("Choose a project to inspect its activity.").style(color="muted_foreground"),
    ]
).style(padding=16, gap=12, background="muted", radius=8, border=True)
```

Do not use raw hex, RGB values, CSS class names, margin, per-edge padding,
positioning, opacity, font families or Rust `.primary()` builders: those
styling APIs are not exposed. ColorPicker's hex **value** is a separate data
contract; it does not add raw hex colors to `.style()`.

Visibility is a control property: `control.visible = False`, not a style key.
Hidden controls consume no layout space and keep their native state.

Button `variant` is fixed at construction and accepts `primary`, `secondary`,
`outline`, `ghost`, `danger`. Its icon is also fixed. Other controls have their
own variant contracts: read the catalog, do not transfer Button variants to Tag
or Alert. Button has `disabled`, but not a Python `loading` property; combine a
disabled button with a status Label or supported Progress/Marker component.

Global `Theme` configuration supports hex palettes, fonts, radii and shadows,
plus macOS, Windows and shadcn-inspired presets and runtime switching. See
[native themes](themes.md). Hex values still do not belong in `.style()`.

Light is the default application theme. Keep surfaces readable with semantic
foreground/background pairs and show meaning in text as well as color. For a
new screen, apply the companion `gpyui-design-guides` skill's layout, hierarchy
and review guidance. Upstream Rust guides mention rem units and extra theme
roles; gpyui uses the pixel properties and tokens listed above.
