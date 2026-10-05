"""Real menu/shortcut actions with a shared asynchronous Python command."""

import asyncio
import json
import sys
import threading
from pathlib import Path

from gpyui import (
    Application,
    Button,
    Column,
    Command,
    DropdownMenu,
    Label,
    Menu,
    MenuSeparator,
    Row,
    State,
    TextInput,
)

path = Path(sys.argv[1])
mode = sys.argv[2] if len(sys.argv) > 2 else "kit"
value = State("123")
calls = []


def write(name, data):
    target = path / f"{name}.json"
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(data))
    temporary.replace(target)


async def save(event):
    assert event.sender is save_command and event.name == "command"
    calls.append(field.value)
    number = len(calls)
    save_command.enabled = False
    await asyncio.sleep(0.08)
    with app.batch():
        status.text = f"Saved {number}: {calls[-1]}"
        save_command.enabled = True
    write(
        f"save-{number}",
        {
            "value": calls[number - 1],
            "thread": threading.current_thread().name,
            "snapshot": await app.snapshot(),
        },
    )


def toggle():
    with app.batch():
        sidebar.visible = not sidebar.visible
        toggle_command.checked = sidebar.visible


async def start():
    write(
        "ready",
        {
            "field": field.id,
            "button": button.id,
            "save": save_command.id,
            "toggle": toggle_command.id,
            "sidebar": sidebar.id,
        },
    )
    while True:
        file = path / "command.json"
        if file.exists():
            data = json.loads(file.read_text())
            file.unlink()
            action = data["action"]
            with app.batch():
                if action == "disable":
                    save_command.enabled = False
                elif action == "enable":
                    save_command.enabled = True
                elif action == "execute":
                    save_command.execute()
                elif action == "replace":
                    dropdown.items = [toggle_command]
                elif action == "remove_menu":
                    field.context_menu(None)
                elif action == "add_command":
                    dynamic = Command(
                        "Dynamic action",
                        lambda: write("dynamic", {"value": field.value}),
                        shortcut="mod+shift+d",
                    )
                    app.add_command(dynamic)
                elif action == "snapshot":
                    pass
                else:
                    raise ValueError(action)
            write(data["name"], {"snapshot": await app.snapshot(), "calls": calls})
        await asyncio.sleep(0.02)


save_command = Command("Save", save, shortcut="mod+s")
toggle_command = Command("Sidebar", toggle, shortcut="mod+shift+b", checked=True)
app = Application(
    title=f"gpyui commands {mode}",
    width=720,
    height=450,
    menus=[Menu("File", [save_command, MenuSeparator(), Menu("View", [toggle_command])])],
    on_start=start,
)
with app, Column().style(gap=12):
    Label("Name")
    field = (
        TextInput("123")
        .bind_value(value)
        .style(width=320)
        .context_menu([save_command, Menu("View", [toggle_command])], native=mode == "native")
    )
    with Row().style(gap=12):
        button = Button(command=save_command)
        dropdown = DropdownMenu("More", [save_command, MenuSeparator(), Menu("View", [toggle_command])])
    status = Label("Ready")
    with Column() as sidebar:
        Label("Sidebar content")
app.run()
write(
    "closed",
    {"errors": [str(error) for error in app.errors], "threads": [t.name for t in threading.enumerate()]},
)
