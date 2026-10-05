"""The notes command persists the captured document and handles retry/cancellation."""

import asyncio
import sys
from pathlib import Path

import pytest
from test_dynamic import mounted

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))
from notes import build_app

from gpyui import Event


def test_notes_save_and_retained_sidebar(tmp_path):
    async def scenario():
        path = tmp_path / "notes.txt"
        app, ui = build_app(path)
        mounted(app)
        ui["editor"].value = "A real document\n"
        await ui["save"]._handler(Event(ui["save"], "command"))
        assert path.read_text() == "A real document\n"
        assert ui["status"].text == "Saved to notes.txt."
        assert ui["save"].enabled is True
        editor_id = ui["editor"].id
        ui["toggle"]._handler(Event(ui["toggle"], "command"))
        assert ui["sidebar"].visible is False and ui["toggle"].checked is False
        assert ui["editor"].id == editor_id and ui["editor"].value == "A real document\n"

    asyncio.run(scenario())


def test_notes_io_failure_is_visible_and_retry_remains_enabled(tmp_path):
    async def scenario():
        app, ui = build_app(tmp_path / "missing" / "notes.txt")
        mounted(app)
        await ui["save"]._handler(Event(ui["save"], "command"))
        assert "Could not save" in ui["status"].text and "retry" in ui["status"].text
        assert ui["save"].enabled is True

    asyncio.run(scenario())


def test_notes_save_preserves_cancellation_after_native_close(tmp_path, monkeypatch):
    async def scenario():
        app, ui = build_app(tmp_path / "notes.txt")
        mounted(app)
        entered = asyncio.Event()

        async def pending(*_, **__):
            entered.set()
            await asyncio.Future()

        monkeypatch.setattr(asyncio, "to_thread", pending)
        task = asyncio.create_task(ui["save"]._handler(Event(ui["save"], "command")))
        await entered.wait()
        assert ui["save"].enabled is False
        app._phase = "closed"
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(scenario())
