"""Launch a real window and verify queued updates, native input state and shutdown."""

import asyncio
import json
import threading
from pathlib import Path

from gpyui import Application, Button, Column, Label, State, TextInput

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
    observed.update(state)
    await asyncio.sleep(0.3)
    app.close()


app = Application(title="gpyui installed wheel smoke test", on_start=started)
with app, Column():
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
print("Native window, batched updates, text input state, asyncio and shutdown verified.")
