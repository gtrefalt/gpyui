"""Bundled app recipes must handle real persistence failures and cancellation."""

import asyncio
import json
import runpy
from pathlib import Path

import pytest

RECIPE = Path(__file__).resolve().parents[1] / "skills/gpyui/scripts/profile.py"


@pytest.fixture
def profile():
    return runpy.run_path(str(RECIPE), run_name="skill_recipe")


def test_profile_requires_a_name_before_io(profile, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    asyncio.run(profile["save_profile"]())
    assert "Enter a display name" in profile["status"].value
    assert not (tmp_path / "profile.json").exists()
    assert profile["save"].disabled is False


def test_profile_saves_json_and_restores_command(profile, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    profile["name"].value = " Ada Lovelace "
    asyncio.run(profile["save_profile"]())
    assert json.loads((tmp_path / "profile.json").read_text()) == {"name": "Ada Lovelace"}
    assert profile["status"].value == "Saved profile for Ada Lovelace."
    assert profile["save"].disabled is False


def test_profile_reports_io_failure_and_allows_retry(profile, monkeypatch):
    def fail(_):
        raise OSError("Read-only location")

    monkeypatch.setitem(profile["save_profile"].__globals__, "persist_profile", fail)
    profile["name"].value = "Ada"
    asyncio.run(profile["save_profile"]())
    assert "Read-only location" in profile["status"].value
    assert profile["save"].disabled is False


@pytest.mark.parametrize("window_closed", [False, True])
def test_profile_preserves_cancellation_even_after_bridge_closes(profile, monkeypatch, window_closed):
    async def scenario():
        entered = asyncio.Event()

        async def pending_io(*_):
            entered.set()
            await asyncio.Future()

        monkeypatch.setattr(asyncio, "to_thread", pending_io)
        profile["name"].value = "Ada"
        task = asyncio.create_task(profile["save_profile"]())
        await entered.wait()
        assert profile["save"].disabled is True
        if window_closed:
            # Native shutdown closes the bridge before cancelling callbacks.
            profile["app"]._phase = "closed"
            profile["save"]._app = profile["app"]
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        if not window_closed:
            assert profile["save"].disabled is False

    asyncio.run(scenario())
