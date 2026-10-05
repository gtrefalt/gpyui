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
GPUI Kit. It describes gpyui 0.2.0's Python capabilities, including the current
one-window and startup-theme limits.

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
- Use semantic colors and supported pixel properties, with a consistent scale.
- Keep the primary action visible and concrete. Include empty, loading, failure
  and cancellation behavior when they apply to the workflow.
- Use runtime visibility and child updates to change screens while retaining
  editing controls. Global keyboard shortcuts, custom focus APIs and docking
  remain outside the Python surface.

## Inspiration

These original Python-focused guides are inspired by
[GPUI Kit's design skill](https://github.com/longbridge/gpui-kit/tree/3a142844d3661159964dce9e5512ca9a40286160/skills/gpui-kit-design-guides)
and [upstream design guidance](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/website/docs/design-guides.md).
Upstream principles inform the design; the Python contract remains the authority
for implementable features.
