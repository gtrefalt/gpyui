---
name: gpyui-design-guides
description: Design and review native Python desktop interfaces built with gpyui and GPUI Kit. Use before choosing layout, component hierarchy, spacing, semantic colors, density, form structure, data views, loading and error states, dialogs, or interface copy. Includes desktop design guidance adapted to the Python binding's actual styling and component limits. Pair with the gpyui skill for implementation, state, events and asyncio.
---

# Design gpyui interfaces

Read [the design guide](references/design-guides.md) before designing a screen.
For a new app or redesign, read the whole guide. For a small change, read
"Start with the task", the relevant section, and "Review before delivery".

Use the `gpyui` skill's component references when implementing the design.
This skill is self-contained design guidance; it does not require a checkout of
GPUI Kit. It describes gpyui 0.6.0 with Image, expanded window controls,
exact macOS Classic themes, keyed tables, richer inputs, MultiSelect and
CommandPalette, backed by Kit 0.7.1 / GPUI 0.3.8. Verify the installed API before
designing around these additions. Native themes, Form/Field validation, runtime
switching and the current one-window limit remain covered.

## Reading map

| Decision | Guide section |
| --- | --- |
| What the app should emphasize | Start with the task |
| Forms, panes, scrolling, density | Organize a native window |
| Spacing, type, colors and variants | Establish a visual language |
| Async work, errors and dangerous actions | Make state and consequences visible |
| Tables, charts and streaming dashboards | Design data views |
| Keyboard access, text and platform behavior | Preserve native interaction |
| Final review | Review before delivery |

## Defaults

- Default to light appearance unless the user specifies otherwise.
- Choose native Kit controls for their behavior; compose them around the task.
- Use Button for in-app commands, Link for external resources.
- Use Form/Field for labels, required indicators, help and inline validation.
  Keep actions reachable, show async saving/retry and retain editors on errors.
- Use semantic colors and supported pixel properties, with a consistent scale.
- Keep the primary action visible and concrete. Include empty, loading, failure
  and cancellation behavior when they apply to the workflow.
- Use runtime visibility and child updates to change screens while retaining
  editing controls. OS-global hotkeys, custom focus APIs and docking
  remain outside the Python surface.
- Table uses native virtualization and keyed TableRow models preserve domain selection;
  its value remains a source index when sorted/filtered. List renders all items.
  Tree selects stable IDs, Select/Combobox one string, and MultiSelect a string list.
  CommandPalette shares existing Commands. Check the installed version before use.

## Inspiration

These original Python-focused guides are inspired by
[GPUI Kit's design skill](https://github.com/longbridge/gpui-kit/tree/c1bda59e67f46266991a230ae94f749af496af2a/skills/gpui-kit-design-guides)
and [upstream design guidance](https://github.com/longbridge/gpui-kit/blob/c1bda59e67f46266991a230ae94f749af496af2a/website/docs/design-guides.md).
Upstream principles inform the design; the Python contract remains the authority
for implementable features.
