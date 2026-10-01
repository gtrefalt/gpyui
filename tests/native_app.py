"""Native fixture launched in its own process; all interactions come from X11."""

import asyncio
import json
import sys
import threading
import time
from pathlib import Path

from gpyui import Application, Button, Column, Label, State, TextInput

directory = Path(sys.argv[1])
mode = sys.argv[2]
message = State("Enter a name and choose Greet")
name_state = State("")
calls = 0
activation_values = []


def write(name, value):
    target = directory / f"{name}.json"
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(value))
    temporary.replace(target)


async def started():
    if mode == "history":
        field.value = "Ada"
    initial = await app.snapshot()
    write("ready", {"input": field.id, "label": greeting.id, "button": button.id, "initial": initial})
    if mode == "queued":
        # Deliberately pause Python dispatch while GPUI continues accepting input.
        time.sleep(0.75)


def error_handler(error):
    write("error", {"type": type(error).__name__, "message": str(error)})
    if mode == "error":
        app.close()


app = Application(title=f"gpyui native test {mode}", on_start=started, on_error=error_handler)


async def verify():
    global calls
    calls += 1
    snapshot = await app.snapshot()
    write(
        f"result-{calls}", {"snapshot": snapshot, "input_value": field.value, "state_value": name_state.value}
    )
    write(
        "result",
        {
            "snapshot": snapshot,
            "input_value": field.value,
            "state_value": name_state.value,
            "callback_thread": threading.current_thread().name,
        },
    )


def greet():
    if mode == "error":
        raise ValueError("callback failure test")
    if mode == "queued":
        activation_values.append(field.value)
        write(f"activation-{len(activation_values)}", {"value": field.value})
    # Repeated writes in a synchronous callback are deliberately coalesced.
    with app.batch():
        greeting.text = "intermediate"
        greeting.text = f"Hello, {field.value}!"
    return verify()  # A synchronous callback returning an awaitable is supported.


async def greet_async(event):
    assert event.sender is button and event.name == "click"
    button.disabled = True
    message.value = "Preparing greeting…"
    write("waiting", await app.snapshot())
    if mode == "cancel":
        try:
            await asyncio.sleep(60)
        finally:
            write("cancelled", {"thread": threading.current_thread().name})
        return
    await asyncio.sleep(0.15)
    message.value = f"Hello, {field.value}!"
    button.disabled = False
    await verify()


with app, Column():
    Label("Name")
    field = TextInput(placeholder="Enter your name").bind_value(name_state)
    greeting = Label().bind_text(message)
    button = Button("Greet", on_click=greet_async if mode in {"async", "cancel"} else greet)

app.run()
write(
    "closed",
    {"errors": [str(error) for error in app.errors], "threads": [t.name for t in threading.enumerate()]},
)
