# Component coverage and Python API

The goal remains full GPUI Kit access from Python. This pass adds 67 control
classes to the original four: **71 controls**, plus native notifications through
`Application.notify`. Layout helpers use GPUI directly; the themed component
wrappers construct actual Kit components. There are no placeholder classes for
unimplemented Kit families.

This is basic catalog coverage, not parity with every upstream builder method.
The inventory below is grounded in the pinned
[component crate](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/lib.rs).
Component links resolve to that same immutable revision. Examples are entirely
Python: [workspace](https://github.com/gtrefalt/gpyui/blob/main/examples/workspace.py) and [gallery](https://github.com/gtrefalt/gpyui/blob/main/examples/gallery.py).

## Available controls

Controls accept a positional value for their first property and keyword
arguments for the others. Container controls accept `children=[...]` and `with`
blocks. `Row`, `Container` and `Scroll` also accept a positional children list.
`Column` retains its original children-list constructor.

| Family | Python controls | Initial contract |
| --- | --- | --- |
| GPUI layout | `Column`, `Row`, `Container`, `Scroll` | Children, pixel layout, native vertical scrolling |
| [GroupBox](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/group_box.rs) | `GroupBox` | Title and children |
| [Toolbar](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/toolbar.rs), [StatusBar](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/status_bar.rs) | `Toolbar`, `StatusBar` | Python-composed native content |
| [Label](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/label.rs), [Button](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/button/button.rs) | `Label`, `Button` | Text; button disabled/click, constructor variant/icon |
| [Input](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/input/mod.rs) | `TextInput`, `TextArea`, `NumberInput`, `OtpInput`, `Editor` | Native editing, value/change, explicit two-way binding; newer inputs also accept disabled |
| [Checkbox](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/checkbox.rs), [Switch](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/switch.rs), [Radio](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/radio.rs), [Toggle](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/button/toggle.rs) | `Checkbox`, `Switch`, `Radio`, `Toggle`, `RadioGroup` | Boolean or index value, disabled, change/binding; standalone radios need Python grouping policy |
| [Slider](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/slider.rs), [Rating](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/rating.rs) | `Slider`, `Rating` | Scalar slider range/step, 0–5 rating, change/binding; slider release event |
| [Select](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/select.rs), [Combobox](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/combobox.rs) | `Select`, `Combobox` | String items, single selected value, disabled; native searchable combobox |
| [Tabs](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/tab/tab_bar.rs), [Sidebar](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/sidebar/mod.rs), [Breadcrumb](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/breadcrumb.rs), [Stepper](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/stepper/stepper.rs) | `Tabs`, `Sidebar`, `Breadcrumb`, `Stepper` | Labels, zero-based selection, disabled, change |
| [Pagination](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/pagination.rs), [Link](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/link.rs) | `Pagination`, `Link` | Zero-based page value translated to Kit's one-based page API; URL/click |
| [List](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/list/list_item.rs), [Table](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/table/data_table.rs), [Tree](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/tree.rs) | `List`, `Table`, `Tree` | ListItem composition; retained TableState/delegate and rows; retained TreeState with stable item IDs |
| [Charts](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/chart/mod.rs) | `LineChart`, `AreaChart`, `BarChart`, `PieChart`, `CandlestickChart` | Native plots and tooltips, assignable data; line domain follows data |
| [Calendar](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/time/calendar.rs), [DatePicker](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/time/date_picker.rs), [TimeField](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/time/time_field.rs), [ColorPicker](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/color_picker.rs) | `Calendar`, `DatePicker`, `TimeField`, `ColorPicker` | Native state and change/binding; single ISO dates, local time to seconds, hex RGB/RGBA colors |
| [Progress](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/progress/mod.rs), [Spinner](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/spinner.rs), [Skeleton](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/skeleton.rs), [Shimmer](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/shimmer.rs) | `Progress`, `ProgressCircle`, `Spinner`, `Skeleton`, `Shimmer` | Percentage/indeterminate progress and native animated feedback |
| [Tag](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/tag.rs), [Badge](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/badge.rs), [Avatar](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/avatar/avatar.rs), icons | `Tag`, `Badge`, `Avatar`, `Icon`, `Kbd`, `Separator` | Semantic tag variants, count badges, initials, bundled Lucide icons, keystrokes, separators |
| [Alert](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/alert.rs), [Empty](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/empty.rs), [DescriptionList](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/description_list.rs) | `Alert`, `Empty`, `DescriptionList` | Text/variants and label/value pairs |
| [Accordion](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/accordion.rs), [Collapsible](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/collapsible.rs), [Carousel](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/carousel/mod.rs), [Resizable](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/resizable.rs) | `Accordion`, `Collapsible`, `Carousel`, `Resizable` | Disclosure, native slide selection, native resize state and resize events |
| [Dialog](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/dialog/dialog.rs), [Sheet](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/sheet.rs), [Notification](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/notification.rs) | `Dialog`, `Sheet`, `app.notify(...)` | Python contents, queued native open/close, native dismissal mirrored to value; one dialog and one sheet per window |
| [Tooltip](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/tooltip.rs), [Popover](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/popover.rs), [HoverCard](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/hover_card.rs), [Clipboard](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/clipboard.rs) | `Tooltip`, `Popover`, `HoverCard`, `Clipboard` | Native hover/popup/copy behavior and Python-composed popup contents |
| [Message](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/message.rs), [Bubble](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/bubble.rs), [Marker](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/marker.rs), [Attachment](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/attachment.rs), [Text](https://github.com/longbridge/gpui-kit/blob/3a142844d3661159964dce9e5512ca9a40286160/crates/component/src/text/compat.rs) | `Message`, `Bubble`, `Marker`, `Attachment`, `Markdown`, `Html` | Native content presentation and rich text selection |

## Values, updates and constraints

`on_change(event)` receives `Event.value` after native state has changed and the
Python mirror/bound State has been updated. Zero-argument and async callbacks
retain the original contract. Kit controlled controls write their state in Rust
and notify immediately; their interaction does not wait for Python to redraw.
Entity-backed inputs retain focus, caret, editing buffers and undo history in Rust.

All input values are strings, including NumberInput's partially edited buffer.
NumberInput steps by one natively. Boolean controls use bool; navigation, rating,
pagination and table selections use zero-based indices; Tree uses stable string
item IDs. Select/Combobox use selected strings, with `""` for no selection. Date
controls use `YYYY-MM-DD` or `""`; time uses `HH:MM:SS`; colors use `#rrggbb` or
`#rrggbbaa`. A table starts at row zero when selected by interaction; empty tables
retain zero as the default Python value. List currently composes Kit ListItems;
the full virtual ListState/delegate API is not exposed.

Table rows are lists of strings matching its columns. Charts accept
`[[label, value], ...]`; candles accept `[label, open, high, low, close]` and
validate the OHLC bounds. Tree items have `id`, `text`, and optional `children`;
IDs must be unique, with a maximum of 10,000 items and 32 levels.

Properties are mutable through assignment unless explicitly fixed: Slider
range/step; Select/Combobox/Tree items; Table columns/column_width; OTP length;
Resizable axis; Dialog/Sheet title. Collections are copied when assigned/read.
Dynamic roots and container children, visibility and explicit subtree disposal
are supported. Reordering, moving, hiding and detaching preserve native control
identity and editing state. Accordion initially exposes one
open index and string item contents. Avatar initially exposes initials; Editor
exposes editing without Python LSP/provider hooks. Chart animation/hover and
resize geometry remain native. The initial theme is chosen when run starts.

`.style(...)` supports width, height, min_width, min_height, padding, gap, radius,
font_size, flex, full_width, full_height, border, bold, align and justify. Spacing
and dimensions are pixels. Background/color use semantic theme tokens:
background, foreground, muted, muted_foreground, primary, primary_foreground,
secondary, secondary_foreground, border, accent, accent_foreground, danger,
success, warning, info and transparent.

## Remaining catalog work

These are real gaps, not aliases to generic containers:

| Upstream area | Next implementation |
| --- | --- |
| `menu`, `native_menu`, `command` | Structured command/action protocol, menus, shortcut routing and command palette |
| `dock` | Stable panel identities, persistence, drag/detach behavior and multiwindow lifecycle |
| `form`, `setting`, `questionnaire` | Typed schemas, validation, conditional fields and submission lifecycle |
| `searchable_list`, virtual list | Python data model with native virtualization and queued async search; full List delegate |
| `message_scroller` | Native anchoring/follow behavior, streaming updates and history loading |
| `chart`, `plot` | Radar/Sankey, multiple series and lower-level plot composition |
| Existing families | Group variants, custom item renderers, images, input groups, date ranges, rich formatting, controlled popup lifecycle and complete builder options |
| `highlighter`, `history`, `theme` | Provider hooks, explicit undo/redo commands and runtime theme control; editing/history/theme already run natively |

Next acceptance gates should prove menu keyboard routing, virtualized data
updates and typed form submission with real windows before adding docking and
multiwindow. Full Kit parity requires these behaviors and wider platform testing;
the current source-backed wrappers are the reusable foundation.
