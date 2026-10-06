---
name: gpyui
description: Build native desktop applications in Python with gpyui and Longbridge GPUI Kit components. Use when creating or changing a gpyui app, choosing controls, composing layouts, binding State, handling events or asyncio, updating tables and charts, opening dialogs, styling, or managing application lifecycle. Includes verified Python contracts for all 74 controls and runnable recipes. Use the gpyui-design-guides skill for visible interface design. Rust GPUI Kit APIs are not automatically available in Python.
---

# Build apps with gpyui

Use this skill for **Python application code**. Rust owns rendering, windows,
focus, text editing and retained Kit component state. Python owns composition,
application data and callbacks. Applications import `gpyui`; they do not manage
GPUI entities, contexts, initialization or native threads themselves.

These references describe **gpyui 0.5.0**. Read the installed version's API when
it differs; never invent an API by translating a Rust, web, Tkinter or Flet
example. If the request needs a missing binding, identify that gap and implement
it in the library before depending on it in application code.

## Workflow

1. Read [setup and runtime](references/runtime.md) before creating an app.
2. Read [composition and component conventions](references/composition.md),
   then the relevant family in the [component index](references/components.md).
   The family references include every constructor field, event, fixed property,
   contract limit and a complete runnable example.
3. Read [state, events and asyncio](references/state-and-events.md) before adding
   behavior or background work. Match the actual value type of each control.
4. Read [styling](references/styling.md) and use `gpyui-design-guides` when changing
   a visible screen. The companion skill is optional to install; the Python
   styling contract is bundled here.
5. Read [commands and menus](references/commands-and-menus.md) for reusable actions,
   shortcuts, context menus or an application menu bar.
   Read [native themes](references/themes.md) for macOS/Windows/shadcn presets,
   custom colors and runtime switching without replacing editors. The theme
   reference records the platform control refinements included in 0.5.0.
   Read [forms and validation](references/forms.md) for Field labels/help/errors,
   Python validators, conditional editors and shared async submission/retry.
6. Start from the [application recipes](references/recipes.md) rather than
   assembling unfamiliar API calls. Adapt them to the user's task.
7. Validate the tree and business logic without a native window, then run the
   app on a desktop. Verify real editing, selection, scrolling, loading, errors
   and shutdown. Construction checks do not prove native interaction.

## Rules for application code

- Install dependencies with `uv add` and launch with `uv run python app.py`.
  The alternative is `pip install` in a virtual environment; see platform setup.
- Build the initial tree before `app.run()`; update children on the callback loop. Use one composition method at a
  time: context-managed children, or explicit child lists built outside a
  context. A control has one parent.
- Call `app.run()` once, on the main thread, outside an existing asyncio loop.
  Callbacks run on the owned Python asyncio worker. Do not wrap `run()` in
  `asyncio.run()` or run the native window in a background thread.
- Use assignments for mutable properties, `State` for explicit bindings, and
  `app.call_soon()` to hand results back from external threads. Never poll
  arbitrary attributes or recreate native editing controls on every keystroke.
- Keep blocking work off the callback loop with `await asyncio.to_thread(...)`.
  Create tracked startup tasks through `on_start`; cancellation must propagate.
- Read `Event.value` for component changes. An index is not a domain ID, and
  `NumberInput.value` is an editing string, not a number.
- Use real Form/Field for validation. Share `form.submit_command` across actions;
  keep raw editor values intact and normalize the copied save payload. Hide Field
  for conditional omission, and preserve cancellation of validators/save callbacks.
- Reassign collections; changing a returned `rows`, `items` or `data` copy
  submits no update. Bound streaming history and update rate.
- Use semantic style colors and pixel dimensions. `.style()` accepts a limited
  vocabulary, not CSS. No `.pack()`, `.grid()`, `.classes()`,
  `.on(...)`, raw Rust builders or implicit reactive rendering.
- Keep scope honest: one native window. Theme presets and runtime switching are supported.
  Kbd displays a shortcut; Command.shortcut registers a window-scoped action. Navigation selects an index
  but does not own pages; implement page changes with visibility or child updates. Initial wrappers do not expose full Kit
  docking, custom table delegates, multi-series chart configuration or editor
  language-server hooks.

## Sources and inspiration

The split into technical and design skills, task-directed references, ownership
rules and complete recipes is inspired by
[GPUI Kit's skills at the pinned revision](https://github.com/longbridge/gpui-kit/tree/3a142844d3661159964dce9e5512ca9a40286160/skills).
The instructions here are written for gpyui's Python API, rather than copies of
upstream Rust guidance.

Authority: [Python controls](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/controls.py),
[component contracts](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py),
[application lifecycle](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/application.py),
[State](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/state.py) and
[native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs).
The bundled component references are generated from these Python contracts and
the same specimens as the public documentation.
