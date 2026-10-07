# Window options and macOS Classic source evidence

Originally implemented against Kit 0.7.0 / GPUI 0.3.7. The current source
references follow Kit 0.7.1 at `c1bda59e67f46266991a230ae94f749af496af2a`
and GPUI 0.3.8; see [validation](../validation.md) for upgrade acceptance checks.
This milestone follows 0.5.0 and is included in 0.6.1.

## Verified native contracts

- [Kit open_window](https://github.com/longbridge/gpui-kit/blob/c1bda59e67f46266991a230ae94f749af496af2a/crates/kit/src/lib.rs)
  forwards GPUI WindowOptions and wraps the Python root view with Kit’s native Root.
- GPUI `platform.rs` WindowOptions/WindowBounds: initial windowed/maximized/fullscreen
  bounds, minimum size, user resize/movement/minimize flags and system title bar.
- GPUI `window.rs`: `resize`, `set_window_title`, `activate_window`,
  `minimize_window`, `zoom_window`, `toggle_fullscreen`, `viewport_size`,
  `bounds`, capability/state queries, and native bounds observers.
- `gpui-pre-macos 0.3.8/src/window.rs` uses the resize/minimize flags in NSWindow
  styles and movement/minimums in native setters. `gpui-pre-windows` uses window
  style flags, minimum size and guarded hit testing.
- `gpui-pre-linux 0.3.8/src/linux/x11/window.rs` publishes minimum hints and a
  GPU texture maximum, without using `is_resizable` to fix native maximum size.
  Wayland sets minimum size and leaves placement to the compositor. GPUI guards
  its own `start_window_resize`; the pinned Linux backends do not enforce movement
  or minimization flags in desktop decorations.
- [`macos-classic.json`](https://github.com/longbridge/gpui-kit/blob/c1bda59e67f46266991a230ae94f749af496af2a/themes/macos-classic.json)
  defines Classic Light/Dark, 36 colors each, syntax highlighting and shadow=False.
  It does not specify custom typography or radius. Kit defaults are system font,
  16 px body, 13 px mono, 6/8 px radius and standard component geometry.
- [Kit ThemeConfig schema](https://github.com/longbridge/gpui-kit/blob/c1bda59e67f46266991a230ae94f749af496af2a/crates/component/src/theme/schema.rs)
  resets omitted colors through mode defaults but leaves omitted scalar values
  unchanged. [Highlight parser](https://github.com/longbridge/gpui-kit/blob/c1bda59e67f46266991a230ae94f749af496af2a/crates/component/src/highlighter/registry.rs)
  consumes known syntax styles. Some dotted source editor keys and `comment.doc`
  are ignored by this pinned parser; gpyui uses identical parser behavior.

GPUI sources are the locked published crates, also available on
[docs.rs](https://docs.rs/gpui-pre/0.3.8/gpui/struct.WindowOptions.html).

## Implementation

1. Validate finite size/minimums, flags, position and initial state before startup.
   Keep creation options immutable. Title assignment and explicit `resize()`
   represent requested values; `window_snapshot()` reads actual native state.
2. Translate creation options to actual GPUI WindowOptions. Keep window actions
   on the existing ordered bridge queue; the Python callback loop does not own
   platform objects. Flush controls first and validate before enqueueing actions.
3. Retain a native WindowState outside the control tree. A bounds observer
   restores fixed content dimensions after external resize, except fullscreen.
   This closes the Linux flag gap without patching dependencies or remounting
   controls. Desktop transitions remain asynchronous; describe platform limits.
4. Vendor the Classic file unchanged and compile it into Rust with `include_str!`.
   Apply its complete config through Kit’s parser and Theme::update, then optional
   explicit Python overrides. Fill omitted scalars from Kit defaults to prevent
   custom-theme values leaking across switches. Remove the approximate Mac
   palette, compact control wrappers, green switch substitution and font matching.
   Reset default highlighting when switching to a theme with no highlight config.
5. Update native previews, public references, README and app-building skills.
   Release these changes in 0.6.1; only a new version tag builds release wheels.

## Acceptance

- Python tests: invalid options, smaller windows with explicit minimums, immutable
  creation options/requested size, prestart title/resize, ordered runtime actions,
  wrong-thread/closed rejection, queue-failure atomicity and snapshot cleanup.
- Real X11 tests: inspect minimum hints, resize both fixed and resizable windows
  externally, change title/programmatic size, then type at the same native caret
  and undo. Verify shutdown joins the owned Python loop.
- Native theme tests: compare every Classic source color against the applied
  config/resolved color, verify parsed/applied syntax styles and scalar defaults,
  switch modes/presets/custom overrides, and exercise real caret, selection,
  undo, focus traversal, button, checkbox, switch and selection behavior.
- Refresh Classic Light/Dark PNGs from real native rendering. Run Ruff, ty,
  Clippy, Python/native suites, installed-wheel smoke, skills and strict docs.

Native geometry/Classic interaction checks run on Linux/X11 here. macOS/Windows
native smoke checks exercise title and programmatic size in the next tagged wheel
workflow. Fullscreen, maximization, minimization and activation require a desktop
manager; bare Xvfb does not validate those transitions. Custom title bars, maximum
size, always-on-top, live creation flag changes and multiple windows remain future work.
