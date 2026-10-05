"""Command ownership, shared state and declarative menu contracts."""

import asyncio
from types import ModuleType
from unittest.mock import patch

import pytest
from test_dynamic import mounted

from gpyui import (
    Application,
    ApplicationClosedError,
    Button,
    Column,
    Command,
    DropdownMenu,
    Menu,
    MenuSeparator,
    State,
    TextInput,
)
from gpyui.commands import shortcut_key


def test_portable_shortcuts_and_duplicate_aliases():
    with patch("sys.platform", "linux"):
        assert shortcut_key("mod+shift+s") == "ctrl-shift-s"
        with pytest.raises(ValueError, match="duplicate"):
            shortcut_key("mod+ctrl+s")
    with patch("sys.platform", "darwin"):
        assert shortcut_key("mod+shift+s") == "cmd-shift-s"
        assert shortcut_key("ctrl+s") == "ctrl-s"
    for invalid in ["s", "ctrl+", "ctrl++s", "ctrl+ctrl+s", "super+s", "ctrl+s ctrl+x"]:
        with pytest.raises(ValueError):
            shortcut_key(invalid)
    assert shortcut_key("f12") == "f12"
    with pytest.raises(TypeError):
        shortcut_key(None)  # ty: ignore[invalid-argument-type] -- runtime validation


def test_button_uses_command_label_and_shared_enabled_state():
    command = Command("Save", lambda event: None, shortcut="mod+s")
    button = Button(command=command)
    assert button.text == "Save" and button.disabled is False
    assert button._spec()["command"] == command.id
    command.enabled = False
    assert button.disabled is True
    command.enabled = True
    button.disabled = True
    assert button.disabled is True and command.enabled is True
    with pytest.raises(TypeError, match="not both"):
        Button(command=command, on_click=lambda: None)
    with pytest.raises(TypeError, match="text or command"):
        Button()


def test_models_and_bindings_validate_without_a_native_window():
    enabled, checked = State(True), State(False)
    command = Command("Sidebar", lambda: None).bind_enabled(enabled).bind_checked(checked)
    enabled.value = False
    checked.value = True
    assert command.enabled is False and command.checked is True
    items = [command, MenuSeparator(), Menu("More", [command])]
    dropdown = DropdownMenu("Actions", items)
    items.clear()
    assert len(dropdown.items) == 3
    with pytest.raises(TypeError, match="menu items"):
        dropdown.items = ["Save"]  # ty: ignore[invalid-assignment] -- runtime validation
    with pytest.raises(TypeError, match="Menu roots"):
        Application(menus=[command])  # ty: ignore[invalid-argument-type] -- runtime validation
    command.unbind()
    enabled.value = True
    assert command.enabled is False


def test_runtime_discovery_batches_command_state_and_menu_changes():
    async def scenario():
        root = Column()
        app = Application(root)
        bridge = mounted(app)
        command = Command("Save", lambda: None, shortcut="mod+s")
        with app.batch():
            with root:
                button = Button(command=command)
                dropdown = DropdownMenu("More", [command])
            app.menus = [Menu("File", [command])]
            command.enabled = False
            button.context_menu([command])
        assert app.commands == (command,)
        assert command._app is app
        assert len(bridge.calls) == 1 and bridge.calls[0][0] == "reconcile"
        assert any(p["id"] == command.id and p["property"] == "enabled" for p in bridge.calls[0][3])
        assert dropdown.items == (command,)
        with app.batch():
            button.dispose()
            dropdown.dispose()
        # Registered commands are window-owned, independent of their consumers.
        assert app.commands == (command,)
        command.enabled = True
        app.update()
        assert bridge.calls[-1][0] == "submit"

    asyncio.run(scenario())


def test_duplicate_shortcuts_and_cross_application_registration_are_atomic():
    async def scenario():
        first = Command("Save", lambda: None, shortcut="mod+s")
        app = Application(commands=[first])
        mounted(app)
        with pytest.raises(ValueError, match="duplicate shortcut"):
            app.add_command(Command("Conflict", lambda: None, shortcut="mod+s"))
        assert app.commands == (first,)
        with pytest.raises(ValueError, match="one application"):
            Application(commands=[first])
        field = TextInput()
        with app.batch():
            app.add(field)
        with pytest.raises(ValueError, match="duplicate shortcut"):
            field.context_menu([Command("Conflict", lambda: None, shortcut="mod+s")])
        assert field._context_items is None
        with pytest.raises(RuntimeError, match="callback loop"):
            await asyncio.to_thread(setattr, first, "enabled", False)
        assert first.enabled is True

    asyncio.run(scenario())


def test_commands_reject_execution_outside_the_native_lifetime():
    command = Command("Save", lambda: None)
    with pytest.raises(ApplicationClosedError):
        command.execute()


def test_shortcut_conflicts_across_unmounted_roots_are_atomic():
    first = Column([Button(command=Command("Save", lambda: None, shortcut="mod+s"))])
    second = Column([Button(command=Command("Other", lambda: None, shortcut="mod+s"))])
    app = Application(first)
    with pytest.raises(ValueError, match="duplicate shortcut"):
        app.add(second)
    assert second._parent is None and app.children == (first,)


def test_failed_native_validation_leaves_commands_and_controls_unmounted():
    command = Command("Save", lambda: None, shortcut="mod+s")
    button = Button(command=command)
    app = Application(button)
    native = ModuleType("gpyui._core")

    def reject(*_):
        raise ValueError("invalid native configuration")

    native.Bridge = reject  # ty: ignore[unresolved-attribute] -- native module test double
    with patch.dict("sys.modules", {"gpyui._core": native}):
        with pytest.raises(ValueError, match="invalid native"):
            app.run()
    assert button._app is None and command._app is None and app.commands == ()
    button.text = "Still editable"
    assert button.text == "Still editable"
