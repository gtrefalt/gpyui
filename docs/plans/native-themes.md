# Native theme implementation plan

Verified against GPUI Kit revision
`3a142844d3661159964dce9e5512ca9a40286160` and GPUI `0.3.7`; no dependency update
is required for this milestone.

## Source evidence

- [ThemeConfig and Theme::apply_config](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/theme/schema.rs):
  mode, font families/sizes, integer radius, shadow, semantic colors and component
  color fallbacks. Primary colors flow into actual button hover/active colors;
  input borders, popovers, menus and other controls use the same configuration.
- [Theme::update](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/theme/mod.rs):
  reconcile legacy colors and background tokens, synchronize the Base theme and
  refresh windows. Direct `global_mut` edits bypass that synchronization. Applying
  semantic tokens alone leaves some legacy component palettes unchanged.
- [Root::render](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/root.rs):
  inherit current font family/size and update window rem size on render.
- [Monospace fallback](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/theme/mono_font.rs):
  resolve the platform default to an installed family; explicit families are
  application choices and must be installed.

## Implementation

1. Python owns an immutable `Theme` description with validated, copied overrides
   and macOS, Windows, shadcn Zinc/Blue and default light/dark presets. Keep
   component `.style()` colors semantic.
2. Validate startup JSON and runtime theme requests again in Rust before claiming
   the native loop or enqueueing a command. Translate accepted Python tokens to
   Kit's ThemeConfig keys, rejecting unknown keys and malformed hex colors.
3. Apply ThemeConfig through `Theme::update` on the GPUI foreground thread. Specify
   every scalar/default font so switching presets does not leak custom settings.
   Refresh rendering without remounting controls, modifying text values or
   entering Python from a native render callback.
4. Coalesce callback-loop assignments; preserve existing thread, queue-overload,
   close and cancellation contracts. Add an awaited native theme snapshot barrier
   exposing both Kit and Base values for debugging and regression evidence.
5. Document inspired styling and platform-owned decorations. Capture the same
   editable native preview in all four new presets and both modes.

## Acceptance gates

- Validate unknown colors, bad hex, bounds and fonts in Python and Rust; invalid
  commands consume no queue slots and invalid startup does not claim the loop.
- Verify live switching, default restoration, actual primary/hover/active tokens
  and Kit/Base agreement; preserve selected text, caret and undo in real native
  single-line and multiline editors with XTest input.
- Extend installed-wheel smoke tests across every released OS/architecture to
  apply all presets, read native tokens, render and retain edited values.
- Run Ruff, ty, skills/doc generation checks, Rust formatting/Clippy, all Python
  tests and the native interaction suite. Add the example and screenshots to the
  public documentation and bundle the theme contract into agent skills.

This milestone implements themes. Typed forms/validation, custom OS window
decorations, multiwindow, platform visual materials and full builder parity remain
separate work in the [coverage roadmap](../component-coverage.md).

## Platform treatment refinement after 0.4.0

The first captures exposed a gap: colors/radii alone left the actual controls
nearly identical. No upstream revision change is needed. Verified hooks at the
same pinned source are:

- [button/button.rs](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/button/button.rs): `Sizable` and `Styled` instance refinement reach the real
  button after variant styling. Apply 24/32 px heights, padding, font and radius;
  keep enabled/hover/active/keyboard handling in Kit.
- [input/input.rs](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/input/input.rs) and [input/textarea.rs](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/input/textarea.rs): appearance-free rendering keeps the
  original text state, context menu, accessibility and keyboard actions. Wrap
  that renderer in a Rust presentation frame with the original focus handle,
  full-height multiline containment and a halo / underline focus treatment.
- [select.rs](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/select.rs): `appearance(false)` removes the trigger frame while retaining
  selection/search/menu state; `Sizable` controls trigger and popup density.
- [sizing.rs](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/sizing.rs): custom Size does **not** provide arbitrary input height: it uses
  the six-rem-unit branch and scales text by 0.875 of the supplied pixel value.
  Use Small/Medium and explicit frame heights rather than treating Size as height.
- [checkbox.rs](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/checkbox.rs), [switch.rs](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/switch.rs): size enums change actual indicator/track geometry;
  Switch.color overrides checked color independently from primary. Track/thumb
  and slider colors have ThemeConfig keys in [theme/schema.rs](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/theme/schema.rs).
- GPUI's text system exposes installed family names, enabling preset preferences
  without bundling proprietary fonts or repeatedly trying missing families.

Expose the six additional colors in Python and native snapshots, retaining strict
validation on both sides. Store only renderer hints outside Kit's ThemeConfig;
reset those hints before every Kit refresh, including switching to default.
Verify actual editing across geometry changes and pointer/keyboard activation,
not just a serialized palette. Layout gaps stay explicit Python application choices.
