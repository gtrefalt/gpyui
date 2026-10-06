"""A light native settings editor with conditional fields, validation and retry.

uv run python settings.py
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from urllib.parse import urlparse

from gpyui import (
    Application,
    ApplicationClosedError,
    Button,
    Checkbox,
    Column,
    Field,
    Form,
    Label,
    NumberInput,
    Row,
    Separator,
    Spinner,
    State,
    Switch,
    TextInput,
)


def validate_name(value):
    return "Use at least three characters." if len(value.strip()) < 3 else None


def validate_endpoint(value):
    parsed = urlparse(value)
    return None if parsed.scheme == "https" and parsed.hostname else "Enter a complete HTTPS URL."


def validate_interval(value):
    try:
        interval = int(value)
    except ValueError:
        return "Enter a whole number of seconds."
    return None if 5 <= interval <= 3600 else "Choose between 5 and 3600 seconds."


def write_settings(path, values):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(values, indent=2) + "\n")
    temporary.replace(path)


def build_app(destination=Path("settings.json"), *, fail_first_save=False, delay=0.35, on_start=None):
    destination = Path(destination)
    sync = State(True)
    attempts = {"count": 0}
    app = Application(
        title="Workspace settings · gpyui", width=820, height=750, theme="light", on_start=on_start
    )

    async def save(values):
        attempts["count"] += 1
        status.text = "Saving settings…"
        spinner.visible = True
        retry.visible = False
        try:
            await asyncio.sleep(delay)
            if fail_first_save and attempts["count"] == 1:
                raise OSError("Demo save failure. Your edits are intact; retry saving.")
            payload = {**values, "workspace_name": values["workspace_name"].strip()}
            if "interval" in payload:
                payload["interval"] = int(payload["interval"])
            await asyncio.to_thread(write_settings, destination, payload)
            status.text = f"Saved to {destination.name}."
        except OSError:
            status.text = "Save failed. Retry when ready."
            retry.visible = True
            raise
        finally:
            # Native shutdown cancels the owned callback task before UI cleanup.
            try:
                spinner.visible = False
            except ApplicationClosedError:
                pass

    with app, Column().style(full_width=True, full_height=True, gap=14):
        Label("Workspace settings").style(font_size=26, bold=True)
        Label("Keep your preferences local. Required fields are marked with an asterisk.").style(
            color="muted_foreground"
        )
        Separator().style(full_width=True)
        with Form(on_submit=save, submit_label="Save settings", shortcut="mod+s", size="large") as form:
            with Field(
                "Workspace name",
                name="workspace_name",
                required=True,
                help="Shown in workspace menus.",
                validators=[validate_name],
            ) as name_field:
                name = TextInput("Research workspace").style(full_width=True)
            with Field(
                "Notifications",
                name="notifications",
                help="Changes take effect the next time you open this workspace.",
            ):
                notifications = Checkbox("Show desktop notifications", value=True)
            with Field(
                "Remote sync",
                name="sync_enabled",
                help="The demo stores preferences locally; it does not contact a server.",
            ):
                enabled = Switch("Enable remote sync").bind_value(sync)
            with Field(
                "Sync endpoint",
                name="endpoint",
                required=True,
                help="Use HTTPS, for example https://sync.example.com.",
                validators=[validate_endpoint],
            ) as endpoint_field:
                endpoint = TextInput("https://sync.example.com").style(full_width=True)
            with Field(
                "Sync interval",
                name="interval",
                required=True,
                help="Between 5 and 3600 seconds.",
                validators=[validate_interval],
            ) as interval_field:
                interval = NumberInput("30").style(width=180)
        Separator().style(full_width=True)
        with Row().style(full_width=True, gap=10, align="center"):
            save_button = Button(command=form.submit_command, variant="outline").style(bold=True)
            retry = Button("Retry save", command=form.submit_command, variant="outline")
            retry.visible = False
            spinner = Spinner()
            spinner.visible = False
            status = Label("Your changes are not saved yet.").style(color="muted_foreground", font_size=13)
        Label("Save with Ctrl+S or Command+S. Validation keeps text, selection and undo.").style(
            color="muted_foreground", font_size=12
        )

    def show_sync(value):
        endpoint_field.visible = value
        interval_field.visible = value

    unsubscribe_sync = sync.subscribe(show_sync)
    return (
        app,
        form,
        {
            "name": name,
            "name_field": name_field,
            "notifications": notifications,
            "sync": enabled,
            "sync_state": sync,
            "endpoint": endpoint,
            "endpoint_field": endpoint_field,
            "interval": interval,
            "interval_field": interval_field,
            "save": save_button,
            "retry": retry,
            "spinner": spinner,
            "status": status,
            "attempts": attempts,
            "unsubscribe_sync": unsubscribe_sync,
        },
    )


app, form, controls = build_app(fail_first_save=True)

if __name__ == "__main__":
    try:
        app.run()
    finally:
        controls["unsubscribe_sync"]()
