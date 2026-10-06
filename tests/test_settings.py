"""The acceptance app validates raw edits, saves asynchronously and retries."""

import asyncio
import json
import runpy
from pathlib import Path

SETTINGS = runpy.run_path(str(Path(__file__).resolve().parents[1] / "examples/settings.py"))


def test_settings_validation_failure_never_writes_or_reconstructs(tmp_path):
    async def scenario():
        destination = tmp_path / "settings.json"
        app, form, controls = SETTINGS["build_app"](destination, delay=0)
        editor = controls["name"]
        editor.value = "A"
        assert not await form.submit()
        assert form.errors == {"workspace_name": "Use at least three characters."}
        assert not destination.exists() and controls["attempts"]["count"] == 0
        assert controls["name"] is editor and editor.value == "A" and form in app.children[0].children

    asyncio.run(scenario())


def test_settings_simulated_io_failure_retry_and_conditional_payload(tmp_path):
    async def scenario():
        destination = tmp_path / "settings.json"
        _, form, controls = SETTINGS["build_app"](destination, fail_first_save=True, delay=0)
        assert not await form.submit()
        assert controls["retry"].visible and not controls["spinner"].visible
        assert not destination.exists() and "Demo save failure" in form.error
        controls["endpoint"].value = "Invalid, but disabled"
        controls["sync_state"].value = False
        assert not controls["endpoint_field"].visible and not controls["interval_field"].visible
        assert await form.submit() and not form.error and not controls["retry"].visible
        payload = json.loads(destination.read_text())
        assert payload == {
            "workspace_name": "Research workspace",
            "notifications": True,
            "sync_enabled": False,
        }
        assert controls["endpoint"].value == "Invalid, but disabled"
        controls["sync_state"].value = True
        assert not await form.submit() and form.errors["endpoint"] == "Enter a complete HTTPS URL."

    asyncio.run(scenario())


def test_settings_numeric_editing_string_and_domain_conversion(tmp_path):
    async def scenario():
        destination = tmp_path / "settings.json"
        _, form, controls = SETTINGS["build_app"](destination, delay=0)
        controls["interval"].value = "-"
        assert not await form.submit() and form.errors["interval"] == "Enter a whole number of seconds."
        assert controls["interval"].value == "-"
        controls["interval"].value = "45"
        assert await form.submit() and json.loads(destination.read_text())["interval"] == 45
        assert controls["interval"].value == "45" and not (tmp_path / "settings.json.tmp").exists()

    asyncio.run(scenario())
