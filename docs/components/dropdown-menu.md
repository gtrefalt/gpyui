# DropdownMenu

A Kit button with nested commands, checks and shortcut hints.

![Native DropdownMenu preview](../screenshots/components/dropdown-menu.png?v=5441e8218e26)

A real Linux/X11 native capture in light appearance. The same control also supports the initial dark theme.

## Runnable example

```python
import gpyui as ui

save = ui.Command("Save", lambda: print("Save requested"), shortcut="mod+s")
sidebar = ui.Command("Show sidebar", lambda: print("Sidebar requested"), checked=True)
control = ui.DropdownMenu("Actions", [save, ui.MenuSeparator(), ui.Menu("View", [sidebar])])

app = ui.Application(ui.Column([control]), title="DropdownMenu", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

## Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `text` | Required | str | Assignment |
| `items` | Required | Iterable[Command | Menu | MenuSeparator] | Assignment |
| `disabled` | `false` | bool | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](../reference/core.md).

## Events and state

Menu activation calls the selected `Command.on_execute` callback with current native input values. See [commands and menus](../guide/commands.md).

## Contract and limits

Items are Command, Menu or MenuSeparator models. Reassign items to update an open menu. Shared enabled/checked state and callbacks are owned by Command; see the commands guide.

All controls accept [pixel layout and semantic theme styling](../guide/styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/commands.py#L201) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/view.rs) · [Full coverage and remaining Kit APIs](../component-coverage.md)
