<!-- Generated from docs/guide/commands.md; run just docs-generate. -->

# Commands, menus and shortcuts

A `Command` shares one Python callback across buttons, nested menus and a keyboard
shortcut. Native actions enqueue events; callbacks run on gpyui's asyncio worker
with current native input values already mirrored into Python.

```python
from gpyui import Application, Button, Column, Command, DropdownMenu, Label, Menu, MenuSeparator, TextInput

name = TextInput("Ada")
status = Label("Ready")


def save(event):
    status.text = f"Saved {name.value} through {event.sender.label}"


save_command = Command("Save", save, shortcut="mod+s")
app = Application(
    Column(
        [
            name,
            Button(command=save_command, variant="primary"),
            DropdownMenu("More", [save_command, MenuSeparator(), Menu("Document", [save_command])]),
            status,
        ]
    ),
    title="Shared commands",
    width=560,
    height=360,
    menus=[Menu("File", [save_command])],
)
name.context_menu([save_command])
app.run()
```

## Command contract

`Command(label, on_execute, *, shortcut="", enabled=True, checked=False)` is an
application-owned model, not a layout control. `label` must be nonempty. Label
and shortcut are fixed at construction. IDs share the control ID space.

- `on_execute` accepts zero arguments or one `Event`, and can be synchronous or
  async. The event has `sender=command`, `name="command"` and `value=None`.
- Assign Boolean `enabled` and `checked` on the callback loop. Disabled commands
  cannot activate through buttons, menus, shortcuts or `execute()`.
- `bind_enabled(State[bool])` and `bind_checked(State[bool])` provide one-way
  bindings. `unbind()` removes these subscriptions; shutdown also unbinds them.
- `execute()` queues activation through Rust with current native input snapshots.
  It returns `None`, before the Python callback completes. Use an asyncio event
  or application state when another callback must await completion.
- Referencing a command from a control or menu registers it when mounted.
  `Application(commands=[...])` and `app.add_command(...)` register commands
  explicitly, including actions used only through shortcuts.

A command belongs to one running application and remains registered until window
close, even if all its buttons are disposed or menu entries removed. Changing a
layout therefore does not silently remove a shortcut. There is no command
unregister/dispose API yet; a window can retain at most 1,024 commands.

`Button(command=save_command)` uses the command label as its initial text and
combines its own `disabled` flag with the command's enabled state. An explicit
button text overrides that label. `command` and `on_click` are mutually exclusive.
Changing a button's local disabled flag does not disable the shared command.

## Command palette

`CommandPalette(commands, *, query="", placeholder="Search commands…",
searchable=True, filterable=True, loading=False, on_query=None, on_cancel=None)`
is available from 0.6.1, backed by Kit's retained `CommandState` and native
virtual command list. Use the same `Command` instances as buttons and menus:
enabled/checked state, callback execution and shortcut hints remain shared.

```python
from gpyui import Application, Button, Command, CommandPalette, Dialog, Label

status = Label("Ready")
save = Command("Save document", lambda: setattr(status, "text", "Saved"), shortcut="mod+s")
palette = CommandPalette([save])
dialog = Dialog("Commands", children=[palette])
app = Application(Button("Commands", on_click=dialog.open), status, dialog)
app.run()
```

Assign `commands` to replace results or `query` to replace search text. Commands
are unique, capped at 1,024 and automatically registered with the owning window.
Removing results leaves their commands registered, as with menus. Search is
local by default, and keyboard navigation skips disabled commands. Confirming an
item dispatches its shared command with current input values; it does not close
the dialog automatically. The command callback may close it when appropriate.

`on_query` receives `Event.value` after the query mirror changes. For external
search, use `filterable=False`, set `loading` while awaiting results, and assign
`commands` when ready. The application must cancel or discard stale async
results; no provider generation policy is built into this initial wrapper.
`on_cancel` reports Escape with an empty query. Escape first clears a nonempty
query; a hosting Dialog owns dismissal on the subsequent Escape. Its cancel
callback should record state rather than dismiss that dialog again.

## Shortcuts

Use `mod+s` for Save: `mod` becomes Command on macOS and Ctrl on Windows/Linux.
Modifiers are joined with `+`, for example `mod+shift+b`, `alt+enter` or `ctrl+k`.
Explicit `cmd`, `ctrl`, `alt` and `shift` are accepted. Unmodified shortcuts are
restricted to F1–F24 so ordinary typing remains available to native editors.
Only single keystrokes are supported; sequential chords are not yet exposed.

Shortcuts are scoped to this application window, not operating-system hotkeys.
Duplicate normalized shortcuts are rejected before registration. Native editing
contexts retain precedence over application bindings, so avoid assigning editing
shortcuts such as Undo, Copy or Paste to unrelated application commands.
`Kbd` remains a display control; `Command.shortcut` registers the action.

## Menu models and backends

`Menu(label, items)` is an immutable named menu/submenu. Items accept `Command`,
`Menu` and `MenuSeparator()`. They are copied into tuples; replace an owner's
items to change topology. Each menu supports at most 1,000 entries and eight
submenu levels. Empty menus are allowed.

| Surface | API | Native implementation |
| --- | --- | --- |
| Dropdown | `DropdownMenu(text, items)` | Kit Button and DropdownMenu/PopupMenu |
| Context menu | `control.context_menu(items)` | Kit ContextMenu and PopupMenu |
| OS context menu | `control.context_menu(items, native=True)` | Kit NativeMenu; drawn fallback on Linux |
| Application menu | `Application(menus=[Menu(...)])`, `app.menus = [...]` | macOS system menu bar; Kit AppMenuBar on Windows/Linux |

`DropdownMenu.text`, `items` and `disabled` are mutable. Application menu roots
must be `Menu` objects. `control.context_menu(None)` removes its assigned menu.
An assigned context menu takes precedence over the input's default editing menu;
leave it unset to retain the native Cut/Copy/Paste menu.

Drawn dropdown/context menus refresh their enabled/checked state and items while
open. Their popup entities retain identity and focus; rebuilding resets item
selection and closes expanded submenus. OS-native menus use a snapshot when opened, and the execution gate
still checks the command's latest enabled state. Application menu changes reload
the menu bar. Native editing entities are preserved throughout.

## Async actions and shared state

Disable the command before awaiting work to disable every entry point together.
Use persistent status text for errors and restore the command in `finally`.
Do blocking I/O with `asyncio.to_thread`. Closing the window cancels pending
callbacks; do not swallow `asyncio.CancelledError`.

The [notes example](https://gtrefalt.github.io/gpyui/examples/notes/) demonstrates async disk persistence,
Save from a button/menu/shortcut and a checked sidebar command. Hiding the sidebar
changes layout around the same retained editor.

OS-global hotkeys, user-editable keymaps and multiple windows
remain future work. See [coverage](coverage.md).
