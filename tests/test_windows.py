"""Window options validate independently of native startup and preserve lifecycle rules."""

import asyncio
import json

import pytest
from test_dynamic import mounted

from gpyui import Application, ApplicationClosedError


@pytest.mark.parametrize(
    "options",
    [
        {"resizable": 1},
        {"movable": None},
        {"minimizable": "yes"},
        {"width": True},
        {"height": float("nan")},
        {"min_width": 0},
        {"min_height": float("inf")},
        {"width": 400, "min_width": 500},
        {"position": [0, 0]},
        {"position": (float("nan"), 0)},
        {"window_state": "hidden"},
        {"resizable": False, "window_state": "maximized"},
    ],
)
def test_invalid_creation_options_fail_before_native_start(options):
    with pytest.raises((TypeError, ValueError)):
        Application(**options)


def test_small_fixed_window_and_prestart_title_size_changes():
    app = Application(
        width=200,
        height=100,
        min_width=100,
        min_height=80,
        resizable=False,
        movable=False,
        minimizable=False,
        position=(-20, 80),
    )
    assert not app.resizable and not app.movable and not app.minimizable
    assert app.position == (-20, 80)
    app.title = "Changed"
    app.resize(220, 120)
    assert (app.title, app.width, app.height) == ("Changed", 220, 120)
    with pytest.raises(AttributeError):
        app.width = 300  # ty: ignore[invalid-assignment] -- read-only requested size
    with pytest.raises(AttributeError):
        app.resizable = True  # ty: ignore[invalid-assignment]
    for method in (app.activate, app.minimize, app.toggle_maximized, app.toggle_fullscreen):
        with pytest.raises(ApplicationClosedError):
            method()


def test_runtime_window_commands_validation_thread_and_queue_failures():
    async def scenario():
        app = Application(resizable=False, minimizable=False)
        bridge = mounted(app)
        bridge.window_command = lambda action, value: bridge.calls.append((action, json.loads(value)))
        app.title = "Live title"
        app.resize(520, 320)
        app.activate()
        app.toggle_fullscreen()
        assert bridge.calls == [
            ("title", "Live title"),
            ("resize", [520, 320]),
            ("activate", None),
            ("toggle_fullscreen", None),
        ]
        with pytest.raises(ValueError):
            app.resize(100, 100)
        with pytest.raises(ValueError, match="fixed-size"):
            app.toggle_maximized()
        with pytest.raises(ValueError, match="minimizable"):
            app.minimize()
        with pytest.raises(RuntimeError, match="callback loop"):
            await asyncio.to_thread(app.resize, 600, 400)
        with pytest.raises(TypeError):
            app.title = 4  # ty: ignore[invalid-assignment]

        def fail(*_):
            raise RuntimeError("queue full")

        bridge.window_command = fail
        with pytest.raises(RuntimeError, match="queue full"):
            app.title = "Failed"
        with pytest.raises(RuntimeError, match="queue full"):
            app.resize(600, 400)
        assert (app.title, app.width, app.height) == ("Live title", 520, 320)
        app._phase = "closed"
        with pytest.raises(ApplicationClosedError):
            app.resize(600, 400)
        with pytest.raises(ApplicationClosedError):
            await app.window_snapshot()

    asyncio.run(scenario())


def test_window_snapshot_cleans_up_token_after_native_reply():
    async def scenario():
        app = Application()
        bridge = mounted(app)
        bridge.window_snapshot = lambda token: app._window_snapshots[token].set_result({"width": 480})
        assert await app.window_snapshot() == {"width": 480}
        assert app._window_snapshots == {}

    asyncio.run(scenario())


def test_bridge_rejects_invalid_window_json_before_display_start():
    Bridge = pytest.importorskip("gpyui._core").Bridge
    bridge = Bridge("[]")
    with pytest.raises(ValueError):
        bridge.run("Invalid", 480, 300, window_json='{"resizable": "yes"}')
    with pytest.raises(ValueError):
        bridge.run("Invalid", 480, 300, window_json='{"min_width": 600}')
    with pytest.raises(ValueError):
        bridge.window_command("resize", "[0, 50]")
    with pytest.raises(ValueError):
        bridge.window_command("missing", "null")
    bridge.finish()


def test_window_controls_example_constructs_with_fixed_policy():
    import runpy
    from pathlib import Path

    example = runpy.run_path(str(Path(__file__).resolve().parents[1] / "examples/window_controls.py"))
    app = example["build_app"]()
    assert app.resizable is False and app.theme.preset == "macos"
    assert (app.width, app.height) == (560, 360)
