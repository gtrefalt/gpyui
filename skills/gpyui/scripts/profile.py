"""A state-bound form with asynchronous file I/O and recoverable failure."""

import asyncio
import json
from pathlib import Path

from gpyui import Application, ApplicationClosedError, Button, Column, Label, State, TextInput

name = State("")
status = State("Enter a display name, then save your profile.")
app = Application(title="Profile", width=540, height=360, theme="light")


def persist_profile(display_name: str) -> None:
    # This worker does I/O only; it never reads or mutates UI handles.
    Path("profile.json").write_text(json.dumps({"name": display_name}) + "\n", encoding="utf-8")


async def save_profile() -> None:
    display_name = name.value.strip()
    if not display_name:
        status.value = "Enter a display name before saving."
        return
    if save.disabled:
        return
    save.disabled = True
    status.value = "Saving profile…"
    try:
        await asyncio.to_thread(persist_profile, display_name)
        status.value = f"Saved profile for {display_name}."
    except OSError as error:
        status.value = f"Could not save profile: {error}"
    finally:
        try:
            save.disabled = False
        except ApplicationClosedError:
            # Window shutdown closes the bridge before cancelling callbacks.
            pass


with app, Column().style(padding=24, gap=12, align="stretch"):
    Label("Your profile").style(font_size=22, bold=True)
    Label("Display name")
    TextInput(placeholder="Ada Lovelace").bind_value(name)
    Label().bind_text(status).style(color="muted_foreground")
    save = Button("Save profile", variant="primary", on_click=save_profile)

if __name__ == "__main__":
    app.run()
