"""Launch a real window and verify queued updates, native input state and shutdown."""

import asyncio
import json
import threading
from pathlib import Path

from gpyui import (
    Application,
    Button,
    Carousel,
    Column,
    Command,
    Dialog,
    DropdownMenu,
    Label,
    Menu,
    MenuSeparator,
    Sheet,
    State,
    TextInput,
)

message = State("Starting")
observed = {}


async def started():
    await asyncio.sleep(0.3)  # Allow the native window to present its first frames.
    initial = await app.snapshot()
    assert initial[label.id]["text"] == "Starting"
    with app.batch():
        field.value = "Wheel test"
        message.value = "Updated from Python"
        button.disabled = True
    state = await app.snapshot()
    assert state[field.id]["value"] == "Wheel test"
    assert state[label.id]["text"] == "Updated from Python"
    assert state[button.id]["disabled"] is True
    # Run these structural/state checks on every released platform and architecture.
    with app.batch():
        extra = TextInput("Dynamic native input")
        panel.insert(0, extra)
        panel.children = tuple(reversed(panel.children))
        field.visible = False
    state = await app.snapshot()
    assert state[extra.id]["value"] == "Dynamic native input"
    assert state[field.id]["displayed"] is False
    assert state[field.id]["value"] == "Wheel test"
    with app.batch():
        panel.remove(field)
        app.add(field)
        field.visible = True
    state = await app.snapshot()
    assert state[field.id]["attached"] is True and state[field.id]["displayed"] is True
    assert state[field.id]["value"] == "Wheel test"
    panel.clear()
    state = await app.snapshot()
    assert state[extra.id]["attached"] is False
    assert state[label.id]["text"] == "Updated from Python"
    panel.add(label)
    extra.dispose()
    state = await app.snapshot()
    assert extra.id not in state
    assert state[label.id]["displayed"] is True
    # Stateful container bounds and open overlay content also follow child updates.
    last = Label("Last page")
    carousel = Carousel(value=1, children=[Label("First page"), last])
    app.add(carousel)
    state = await app.snapshot()
    assert state[carousel.id]["value"] == 1
    last.visible = False
    state = await app.snapshot()
    assert state[carousel.id]["value"] == 0
    carousel.clear()
    assert (await app.snapshot())[carousel.id]["value"] == 0
    carousel.dispose()
    for cls in (Dialog, Sheet):
        overlay = cls("Dynamic content", children=[Label("Original")])
        app.add(overlay)
        overlay.open()
        await app.snapshot()
        await asyncio.sleep(0.1)
        replacement = Button("Added while open")
        overlay.children = [replacement]
        state = await app.snapshot()
        assert state[overlay.id]["children"] == [replacement.id]
        assert state[replacement.id]["displayed"] is True
        await asyncio.sleep(0.1)
        overlay.visible = False
        state = await app.snapshot()
        assert state[replacement.id]["displayed"] is False
        overlay.visible = True
        await app.snapshot()
        overlay.dispose()
        state = await app.snapshot()
        assert overlay.id not in state and replacement.id not in state
    # Shared commands and queued callbacks are exercised by installed wheels on
    # every release platform, including the macOS system application menu path.
    completed = asyncio.Event()
    calls = []

    async def save(event):
        assert event.sender is action and event.name == "command"
        calls.append(field.value)
        label.text = "Saved by command"
        completed.set()

    action = Command("Save", save, shortcut="mod+s")
    with app.batch():
        app.add_command(action)
        action_button = Button(command=action)
        dropdown = DropdownMenu("More", [action, MenuSeparator(), Menu("Nested", [action])])
        app.add(action_button, dropdown)
        field.context_menu([action], native=True)
        app.menus = [Menu("File", [action])]
    action.execute()
    await asyncio.wait_for(completed.wait(), 5)
    state = await app.snapshot()
    assert calls == ["Wheel test"] and state[label.id]["text"] == "Saved by command"
    with app.batch():
        action.enabled = False
        action.checked = True
        dropdown.items = [action]
    action.execute()  # Disabled commands do not queue another callback.
    state = await app.snapshot()
    assert state[action.id]["enabled"] is False and state[action.id]["checked"] is True
    assert state[action_button.id]["disabled"] is True
    assert len(calls) == 1
    action.enabled = True
    app.menus = []
    await app.snapshot()
    observed.update(state)
    await asyncio.sleep(0.3)
    app.close()


app = Application(title="gpyui installed wheel smoke test", on_start=started)
with app, Column() as panel:
    Label("Name")
    field = TextInput(placeholder="Enter a name")
    label = Label().bind_text(message)
    button = Button("Greet")

app.run()
assert observed, "The native startup callback did not finish"
assert not app.errors, app.errors
assert not any(t.name == "gpyui-asyncio" for t in threading.enumerate())
Path("artifacts").mkdir(exist_ok=True)
Path("artifacts/native-smoke.json").write_text(json.dumps(observed))
print(
    "Native window, dynamic children, visibility, retained input state, shared commands, menus, asyncio and shutdown verified."
)
