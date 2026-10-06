"""Interactive theme regression fixture; each native application gets its own process."""

import asyncio
import json
import sys
import threading
from pathlib import Path

from gpyui import Application, Button, Checkbox, Column, Label, Select, Switch, TextArea, TextInput, Theme

directory = Path(sys.argv[1])
preset, mode = sys.argv[2:4]


def write(name, value):
    temporary = directory / f"{name}.tmp"
    temporary.write_text(json.dumps(value))
    temporary.replace(directory / f"{name}.json")


async def start():
    write(
        "ready",
        {
            "field": field.id,
            "area": area.id,
            "checkbox": checkbox.id,
            "switch": toggle.id,
            "select": select.id,
            "clicks": clicks.id,
            "theme": await app.theme_snapshot(),
        },
    )
    while True:
        path = directory / "command.json"
        if path.exists():
            data = json.loads(path.read_text())
            path.unlink()
            if data["action"] == "theme":
                app.theme = Theme(**data["theme"])
            elif data["action"] != "snapshot":
                raise ValueError(data["action"])
            write(data["name"], {"theme": await app.theme_snapshot(), "nodes": await app.snapshot()})
        await asyncio.sleep(0.01)


app = Application(
    title="gpyui theme regression", width=600, height=560, theme=Theme(preset, mode=mode), on_start=start
)
with app, Column().style(gap=12):
    Label("Name").style(height=20)
    field = TextInput("123").style(width=320, height=32)

    def clicked():
        clicks.text = "Clicked from Python"

    Button("Native primary", variant="primary", on_click=clicked).style(height=32)
    checkbox = Checkbox("Checkbox").style(height=32)
    toggle = Switch("Switch").style(height=32)
    select = Select(items=["One", "Two"], value="One").style(width=160, height=32)
    Label("Notes").style(height=20)
    area = TextArea("123").style(width=320, height=100)
    clicks = Label("Waiting")
app.run()
write(
    "closed",
    {"errors": [str(error) for error in app.errors], "threads": [t.name for t in threading.enumerate()]},
)
