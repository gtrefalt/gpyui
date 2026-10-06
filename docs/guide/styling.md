# Style and theme

`.style(...)` returns the same control, making composition fluent. Styles apply
to the native GPUI tree; they are not CSS. The supported vocabulary is deliberately
smaller than GPUI's full builder API.

```python
from gpyui import Application, Column, Label, Tag

app = Application(title="Appearance", width=540, height=320, theme="dark")
with app, Column().style(padding=20, gap=16, background="muted", radius=12):
    Label("Project overview").style(font_size=24, bold=True)
    Label("Native theme colors").style(color="muted_foreground")
    Tag("Ready", variant="success")
app.run()
```

## Supported properties

| Property | Meaning |
| --- | --- |
| `width`, `height`, `min_width`, `min_height` | Nonnegative pixel dimensions |
| `padding`, `gap`, `radius`, `font_size` | Nonnegative pixel values |
| `flex` | Nonnegative flexible sizing value |
| `full_width`, `full_height` | Fill parent dimension |
| `border`, `bold` | Boolean border/font weight |
| `align` | `start`, `center`, `end`, `stretch` |
| `justify` | `start`, `center`, `end`, `between` |
| `background`, `color` | Semantic theme token |

Layout styles apply to the layout node, so alignment and gaps affect its children.
Leaf styles wrap the actual Kit component and inherit typography/colors. Native
components can retain their own themed internal appearance.

## Semantic tokens

`background`, `foreground`, `muted`, `muted_foreground`, `primary`,
`primary_foreground`, `secondary`, `secondary_foreground`, `border`, `accent`,
`accent_foreground`, `danger`, `success`, `warning`, `info`, `transparent`, `popover`, `sidebar`.

These resolve through Kit's current native theme. Arbitrary CSS, hex style colors
and arbitrary builder properties are not accepted by `.style(...)`.
[ColorPicker](../components/color-picker.md) values use hex color strings as a
separate component-specific contract.

## Appearance

Choose `Application(theme="light")` or `Application(theme="dark")`, or use
`Theme("macos")`, `Theme("windows")`, `Theme("shadcn-zinc")` or `Theme("shadcn-blue")`.
Each preset supports light/dark and custom colors, corner radii and typography.
Assign `app.theme` from a running callback to switch without replacing editors.
See [native theme presets](themes.md) for real previews and the complete contract.
The documentation site's appearance toggle changes the website; native previews
remain their captured appearance.
