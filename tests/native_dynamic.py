"""Native fixture: background tree edits while actual keyboard editing continues."""

import asyncio
import json
import sys
import threading
from pathlib import Path

from gpyui import Application, Button, Column, Editor, Label, Row, State, TextArea, TextInput

directory = Path(sys.argv[1])
kind = sys.argv[2]
value = State("123")
changes = []
clicks = []


def write(name, data):
    target = directory / f"{name}.json"
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(data))
    temporary.replace(target)


def edited(event):
    changes.append(event.value)
    write("edit", {"value": field.value, "state": value.value, "changes": changes})


def activated():
    clicks.append(field.value)
    write("click", {"values": clicks})


async def started():
    write("ready", {"field": field.id, "left": left.id, "right": right.id})
    while True:
        command = directory / "command.json"
        if command.exists():
            data = json.loads(command.read_text())
            command.unlink()
            action = data["action"]
            with app.batch():
                if action == "insert":
                    left.insert(0, Label("Inserted sibling"))
                elif action == "reorder":
                    left.children = list(reversed(left.children))
                elif action == "move":
                    left.remove(field)
                    right.add(field)
                elif action == "hide":
                    field.visible = False
                elif action == "show":
                    field.visible = True
                elif action == "hide_parent":
                    right.visible = False
                elif action == "show_parent":
                    right.visible = True
                elif action == "detach":
                    right.remove(field)
                elif action == "reattach":
                    right.add(field)
                elif action == "dispose":
                    field.dispose()
                elif action == "add_button":
                    right.add(Button("Dynamic action", on_click=activated))
                elif action == "replace":
                    right.children = [Label("Replacement page")]
                elif action == "snapshot":
                    pass
                else:
                    raise ValueError(action)
            write(
                data["name"], {"snapshot": await app.snapshot(), "value": field.value, "state": value.value}
            )
        await asyncio.sleep(0.03)


app = Application(title=f"gpyui dynamic {kind}", width=650, height=400, on_start=started)
with app, Row().style(gap=24, full_width=True, align="start"):
    with Column().style(width=260, gap=12) as left:
        Label("Name")
        cls = {"input": TextInput, "textarea": TextArea, "editor": Editor}[kind]
        field = cls("123", on_change=edited).bind_value(value).style(width=260)
        if kind != "input":
            field.style(height=90)
    with Column().style(width=260, gap=12) as right:
        Label("Target")
app.run()
write(
    "closed",
    {"errors": [str(error) for error in app.errors], "threads": [t.name for t in threading.enumerate()]},
)
