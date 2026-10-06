"""Native fixture controlled on the Python callback loop; no event injection."""

import asyncio
import json
import sys
import threading
from pathlib import Path

from image_helpers import animated_gif, png

import gpyui as ui

directory = Path(sys.argv[1])
url = sys.argv[2]
events = []
pending = None


def write(name, data):
    file = directory / f"{name}.json"
    temporary = file.with_suffix(".tmp")
    temporary.write_text(json.dumps(data))
    temporary.replace(file)


async def loaded(event):
    events.append({"name": event.name, "value": event.value, "thread": threading.current_thread().name})
    await asyncio.sleep(0)


async def started():
    global pending
    write("ready", {"image": image.id, "editor": editor.id})
    while True:
        file = directory / "command.json"
        if file.exists():
            data = json.loads(file.read_text())
            file.unlink()
            action = data["action"]
            if action == "bytes":
                image.source = png((20, 90, 220))
            elif action == "gif":
                image.source = animated_gif()
            elif action == "asset":
                image.source = ui.ImageSource.asset("icons/inbox.svg")
            elif action == "url":
                image.source = url + data.get("path", "/image.png")
            elif action == "invalid":
                image.source = b"this is not an image"
            elif action == "file":
                image.source = directory / data.get("file", "sample.png")
            elif action == "empty":
                image.source = None
            elif action == "hide":
                image.visible = False
            elif action == "show":
                image.visible = True
            elif action == "move":
                panel.remove(image)
                panel.insert(1, image)
            elif action == "fit":
                image.fit = data["fit"]
                image.grayscale = data.get("grayscale", False)
            elif action == "dispose":
                image.dispose()
            elif action == "add_pending":
                pending = ui.Image(url + "/slow.png", on_load=loaded, on_error=loaded).style(
                    width=80, height=40
                )
                panel.add(pending)
            elif action == "dispose_pending":
                assert pending is not None
                pending.dispose()
            elif action != "snapshot":
                raise ValueError(action)
            write(data["name"], {"nodes": await app.snapshot(), "events": list(events)})
        await asyncio.sleep(0.01)


editor = ui.TextInput("Keep editing")
image = ui.Image(directory / "sample.png", on_load=loaded, on_error=loaded).style(
    width=300, height=180, radius=12, background="muted"
)
panel = ui.Column([editor, image, ui.Button("Retry image", on_click=image.reload)])
app = ui.Application(panel, title="gpyui image test", width=500, height=330, on_start=started)
app.run()
write(
    "closed",
    {"errors": [str(error) for error in app.errors], "threads": [t.name for t in threading.enumerate()]},
)
