"""Real fixed/resizable window fixture with a retained native editor."""

import asyncio
import json
import sys
import threading
from pathlib import Path

from gpyui import Application, Column, Label, TextInput

directory = Path(sys.argv[1])
resizable = sys.argv[2] == "true"


def write(name, result):
    path = directory / f"{name}.tmp"
    path.write_text(json.dumps(result))
    path.replace(directory / f"{name}.json")


async def start():
    await asyncio.sleep(0.2)
    write("ready", {"field": field.id, "window": await app.window_snapshot()})
    while True:
        path = directory / "command.json"
        if path.exists():
            data = json.loads(path.read_text())
            path.unlink()
            if data["action"] == "resize":
                app.resize(data["width"], data["height"])
            elif data["action"] == "title":
                app.title = data["title"]
            elif data["action"] != "snapshot":
                raise ValueError(data["action"])
            await asyncio.sleep(0.06)  # Desktop bounds notifications arrive asynchronously.
            write(data["name"], {"window": await app.window_snapshot(), "nodes": await app.snapshot()})
        await asyncio.sleep(0.01)


app = Application(
    title="gpyui window regression",
    width=480,
    height=300,
    resizable=resizable,
    min_width=300,
    min_height=200,
    position=(100, 80),
    on_start=start,
)
with app, Column().style(gap=12):
    Label("Name").style(height=20)
    field = TextInput("123").style(width=300, height=32)
app.run()
write("closed", {"errors": [str(e) for e in app.errors], "threads": [t.name for t in threading.enumerate()]})
