# Forms and validation implementation

Implemented against GPUI 0.3.7 and Kit revision
`3a142844d3661159964dce9e5512ca9a40286160`. Cargo pins remain unchanged.
This milestone follows dynamic children, commands and themes; it is included in 0.5.0.

## Upstream evidence

| Source at the pinned Kit revision | Binding decision |
| --- | --- |
| [Form](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/form/form.rs) accepts typed `Vec<Field>`, supplies layout/size props, label width, columns and footer | Build actual Kit Fields inside actual Kit Form in Rust; validate direct named Field children before mounting or reconciliation. Apply grid/span styles to those builders. |
| [Field](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/form/field.rs) supplies label, required marker, description/description_fn, children and column span | Expose these as Python metadata. Render help plus error using description_fn and semantic muted/danger text. Form summary uses its footer. |
| Form/Field have no validation engine, submit callback, schema coercion or error setter | Keep Python validation policy explicit. Do not claim those mechanisms are upstream Kit features. |
| [Input](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/input/state.rs) retains native editing state through the Base input engine | Reuse existing native input entities and focus handles. Failure changes Field/Form metadata, never editor values. |
| [Base input keyboard bindings](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/base/src/input/base/state.rs) own caret, selection, grouped history and OS-specific undo/redo | Verify editing via real keyboard events; use Ctrl+Y for native Linux redo rather than imposing a Python undo policy. |

The existing [NiceGUI/Flet source comparison](../architecture.md#implementation-evidence-and-adopted-patterns)
continues to guide Python composition and callback ownership. Form submission
extends the existing Command/asyncio bridge rather than adding another lifecycle
or rendering layer.

## Implementation sequence and result

1. Add Python Form/Field contracts and Rust schema validation. Enforce unique
   immutable Field names and direct Field children atomically; support standalone
   Fields, grid columns, label layouts, sizes, help and inline error descriptions.
2. Run sequential sync/async Python validators over copied raw values. Required
   checking precedes validators. Compare active fields, editors and values after
   awaited work; discard stale results. Preserve numeric editing strings.
3. Own one shared submit Command per Form. Capture native values at activation,
   guard concurrent submissions and restore enabled state after success, failure
   or cancellation. Support copied save payloads, expected named ValidationError
   and OSError retry messages, with programming errors routed normally.
4. Build the light settings acceptance app: conditional retained fields,
   validated URL/name/interval, async atomic local saving, deliberate one-time
   failure and retry. Verify text/caret/selection/history and cancellation in a
   real native window; include Form/Field in installed-wheel smoke checks.
5. Publish the guide, component references, native PNGs and both app-building
   skills. Release wheels continue to build only on a new version tag.

## Scope and next milestones

Validation occurs on explicit validate/submit; it is not a schema framework or
per-keystroke observer. There is no automatic coercion, focus-first-invalid API,
field accessibility association, arbitrary label/description widget builders,
or Kit setting/questionnaire schema wrapper. Native keyboard interaction is
verified on Linux/X11; installed-wheel smoke tests cover other platforms when
the next release builds. An in-flight worker-thread file write cannot be undone
by cancelling its awaiting task.

Next: richer List/Table models with stable domain selection across updates,
sorting and filtering; then a command palette backed by existing Commands.
Docking and multiple windows follow those acceptance gates.
