# Native desktop design for gpyui

## Start with the task

Describe the object the user works with, the primary task, the information needed
to decide, and the next action. Build the window around that sequence. A notes
editor needs a document, editing surface and save feedback; it does not acquire
a dashboard merely because charts are available.

Keep the principal work area dominant. Put navigation and supporting details
near the content they explain. Distinguish persistent application state from
transient status. Plan initial, empty, loading, success and failure states before
writing callbacks. For a data operation, explain what is selected and what the
command will affect.

Use existing Kit controls first. Compose product-specific sections out of
Column, Row, GroupBox and other controls; do not draw an imitation checkbox or
text field in Python. Rust already owns its editing and interaction behavior.

## Organize a native window

Use a restrained desktop structure: title/toolbar, a primary work region, and
status where needed. A navigation pane or inspector is useful only when the
workflow needs it. Resizable can separate panes with native draggable boundaries;
it is not a general docking system.

Start with a practical window size such as 800 × 540, then check narrower and
shorter sizes. These are starting values, not requirements. Give the main region
`flex=1`; give compact side regions intentional widths. Apply `align="stretch"`
and `full_width=True` where containment requires them. Bound Scroll with a height
or a flexible region in a bounded parent. Important commands should remain
reachable when content grows.

Group related form fields with visible Label controls, not placeholders alone.
Use vertical labels by default; compose a Row when a short field genuinely fits
beside its label. Put help and validation text near the field. NumberInput holds
text, including incomplete edits; validate at submission, without destroying
native caret or undo behavior on each keystroke.

Prefer a small number of purposeful regions. Avoid a grid of identical bordered
cards, oversized blank gutters, nested cards and decorative banners that consume
the workspace. Dense data can be compact while forms retain comfortable spacing.
Use `visible` to switch between retained pages, or update a content container's
children. Preserve editing controls across moves and hide/show operations so
navigation does not lose a user's selection or undo history. Dispose permanently
discarded pages; detached pages otherwise retain native resources.

## Establish a visual language

Default to `Application(theme="light")`. If dark is requested, choose it at
startup; there is no bound runtime theme switch. Check the app in its intended
appearance, rather than assuming the documentation site's theme changes it.

Use a consistent pixel scale, for example 8 for related controls, 12–16 between
fields and 24 around a main form. Adjust based on density and window size. Apply
spacing to parents with `padding` and `gap`. A small number of text levels is
usually enough: title, section label, normal content and muted metadata.
Use `.style(font_size=20, bold=True)` sparingly for titles.

The exact styling surface is:

- Nonnegative pixel numbers: `width`, `height`, `min_width`, `min_height`,
  `padding`, `gap`, `radius`, `font_size`.
- Nonnegative weight: `flex`.
- Booleans: `full_width`, `full_height`, `border`, `bold`.
- Alignment: `align="start" | "center" | "end" | "stretch"`.
- Distribution: `justify="start" | "center" | "end" | "between"`.
- Semantic token strings for `background` and `color`: `background`,
  `foreground`, `muted`, `muted_foreground`, `primary`, `primary_foreground`,
  `secondary`, `secondary_foreground`, `border`, `accent`, `accent_foreground`,
  `danger`, `success`, `warning`, `info`, `transparent`.

Do not import CSS or Rust styling assumptions. There are no bound per-edge
padding, margin, raw hex palette, font-family, animation or positioning APIs.
Use matching semantic foreground/surface roles; check muted text and controls
against the actual native background. ColorPicker's value may contain hex data,
but `.style(color=...)` still requires a semantic token.

Use one primary Button per local task. Button variants are `primary`,
`secondary`, `outline`, `ghost`, `danger`, fixed at construction. For a Tag,
variants are `primary`, `secondary`, `success`, `warning`, `danger`, `info`;
Alert accepts `info`, `success`, `warning`, `danger`. Do not transfer variants
between components. Status colors should describe real status, with a text label
as well. Badge is for a useful count or short classification, not every caption.

## Make state and consequences visible

A command should name the result: "Save profile", "Export report", "Delete
project". Keep validation errors actionable: name the field and how to fix it.
Use Label or Alert for durable error information and `app.notify()` for a brief
runtime confirmation. A notification cannot replace a persistent validation
message the user needs while correcting input.

For awaited work, disable the relevant Button, change the status text before
awaiting, and restore the button in `finally`. Button has no Python `loading`
property; pair it with status text or a supported progress control. Loading must
correspond to real pending work. Do not block the asyncio callback loop.
Distinguish a fresh value from a stale or disconnected stream.

Use Dialog for a focused confirmation and Sheet for contextual details. Both
accept prebuilt children, expose Boolean `value` and support `open()`/`close()`.
Show the affected object and consequence in a destructive confirmation, with
specific action text and an obvious cancel path. Do not use vague "OK" buttons
for deletion. Test actual native dismissal/focus behavior; custom focus and
keyboard bindings are not exposed in Python. Tooltip and HoverCard may provide
help but cannot be the only source of critical instructions.

Keep command actions as Button; reserve Link for external URLs or email.
`Kbd` only displays a shortcut, so do not label an action with a shortcut unless
that shortcut actually works. Initial menu and navigation wrappers expose
selection, not arbitrary nested command routing.

## Design data views

Choose Table when users compare aligned attributes, List for a flat choice,
Tree for stable hierarchy, and DescriptionList for a small detail inspector.
Use clear column names and units. Table column definitions and column_width are
fixed, and rows must match column count. List and Table report positional
selection; map that to domain identity before acting. Tree reports stable IDs
but its item topology is fixed. Do not promise sorting, custom cell editors,
virtualization or delegates merely because upstream Kit supports them.

Charts should answer a question. Put a concise title, units and a current summary
near the plot. Keep a usable table or text summary where exact values matter.
Line/Area/Bar/Pie data points are `[label, value]`; CandlestickChart points are
`[label, open, high, low, close]`. Python multi-series formatting and custom axes
are not exposed. Pie values must be nonnegative.

For a stream, bound retained history (for example 60 points), update at a useful
human rate and batch related synchronous property assignments. Reassign chart
data and table rows; modifying returned copies will not update the screen.
Label simulated data explicitly, as in the bundled dashboard recipe. Show stream
status and provide an applicable stop/close action. Avoid fake precision or
animated values unrelated to the user's task.

## Preserve native interaction

Use visible labels for inputs and legible command text. Do not require hover to
find the primary command or infer selected state only from color. Avoid icon-only
commands where an ordinary label fits. Verify pointer and keyboard activation,
Tab traversal, input editing, scrolling and overlay dismissal on a desktop.

Let the native library own caret, selection and undo. Do not recreate a field
from on_change or continually replace its text. Check error and loading states
as carefully as the initial screenshot. Accessibility and keyboard behavior
must be observed; construction validation alone does not certify either, and
custom accessibility metadata/focus APIs are not currently bound.

Use precise, short interface language and platform-appropriate terminology.
Keep labels and command strings centralized if the app needs localization.
The Python binding does not supply an application translation catalog.

## Review before delivery

- Is the user's primary task obvious from hierarchy and proximity?
- Are principal commands visible, concrete and appropriate to the selected object?
- Are fields labeled, partial edits preserved, and errors actionable?
- Do widths, flexible regions and bounded scrolling work at smaller window sizes?
- Are spacing, type levels, tokens and component variants consistent and supported?
- Are selected, disabled, empty, loading, failed and stale states understandable?
- Are async commands restored on failure/cancellation and background tasks stopped
  on window close?
- Are destructive actions scoped, explained and cancellable?
- Do actual mouse/keyboard, editing and overlays work in the native app?
- Does the implementation use available Python APIs without claiming unbound Kit
  capabilities? Is simulated data identified?

Deliver a real native screenshot when the app can be run. Describe what was
verified and any concrete binding gap that still affects the requested workflow.
