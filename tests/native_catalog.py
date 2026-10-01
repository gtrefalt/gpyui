"""Native example fixture; observations use the public snapshot barrier."""

import asyncio
import json
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))

from gallery import create_gallery
from workspace import create_workspace

from gpyui import Application, Button, Column, Dialog, Label, Sheet

directory, mode, theme = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
directory.mkdir(parents=True, exist_ok=True)


def write(name, value):
    path = directory / f"{name}.json"
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2))
    temporary.replace(path)


async def started(event):
    await asyncio.sleep(0.2)
    write("ready", await event.sender.snapshot())
    while True:
        await asyncio.sleep(0.05)
        write("state", await event.sender.snapshot())


def error(exc):
    write("error", {"type": type(exc).__name__, "message": str(exc)})


if mode in {"workspace", "stream"}:
    app = create_workspace(theme, streaming=mode == "stream", on_start=started, on_error=error).app
elif mode == "gallery":
    app, _ = create_gallery(theme, on_start=started, on_error=error)
else:
    app = Application(title="gpyui · Overlay test", width=480, height=300, on_start=started, on_error=error)
    with app, Column():
        Label("Native overlays")
        Button("Open dialog", on_click=lambda: dialog.open())
        Button("Open sheet", on_click=lambda: sheet.open())
    with app:
        with Dialog("Native dialog") as dialog:
            Label("Python-composed contents")
            Button("Close", on_click=dialog.close)
        with Sheet("Native sheet") as sheet:
            Label("Python-composed contents")
            Button("Close", on_click=sheet.close)
app.run()
write(
    "closed",
    {
        "errors": [str(error) for error in app.errors],
        "threads": [thread.name for thread in threading.enumerate()],
    },
)
