"""Settings editor driven through real native input and shared commands."""

import asyncio
import json
import runpy
import sys
import threading
from pathlib import Path

directory = Path(sys.argv[1])
build_app = runpy.run_path(str(Path(__file__).resolve().parents[1] / "examples/settings.py"))["build_app"]


def write(name, data):
    temporary = directory / f"{name}.tmp"
    temporary.write_text(json.dumps(data))
    temporary.replace(directory / f"{name}.json")


async def state():
    return {
        "snapshot": await app.snapshot(),
        "errors": form.errors,
        "error": form.error,
        "busy": form.busy,
        "attempts": controls["attempts"]["count"],
    }


async def start():
    write(
        "ready",
        {key: value.id for key, value in controls.items() if hasattr(value, "id")}
        | {"form": form.id, "command": form.submit_command.id},
    )
    while True:
        file = directory / "command.json"
        if file.exists():
            data = json.loads(file.read_text())
            file.unlink()
            action = data["action"]
            if action == "invalid":
                controls["endpoint"].value = "abcd"
            elif action == "valid":
                controls["endpoint"].value = "https://sync.example.com"
            elif action == "hide":
                controls["sync_state"].value = False
            elif action == "show":
                controls["sync_state"].value = True
            elif action == "save":
                form.submit_command.execute()
            elif action != "snapshot":
                raise ValueError(action)
            write(data["name"], await state())
        await asyncio.sleep(0.01)


app, form, controls = build_app(directory / "settings.json", fail_first_save=True, delay=0.7, on_start=start)
app.run()
controls["unsubscribe_sync"]()
write(
    "closed",
    {
        "errors": [str(error) for error in app.errors],
        "busy": form.busy,
        "threads": [thread.name for thread in threading.enumerate()],
    },
)
